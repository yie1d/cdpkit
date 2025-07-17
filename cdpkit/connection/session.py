import asyncio
import inspect
import json
import re
from collections.abc import AsyncIterable, Callable
from contextlib import suppress
from typing import Any

import aiohttp
import websockets
from pydantic import BaseModel, PrivateAttr
from websockets.asyncio.client import ClientConnection
from websockets.protocol import State

from cdpkit.connection.manager import CommandsManager, EventsManager
from cdpkit.exception import (
    CallbackParameterError,
    CommandExecutionError,
    CommandExecutionTimeout,
    InvalidResponse,
    NetworkError,
    WebSocketConnectionClosed,
)
from cdpkit.logger import logger
from cdpkit.protocol import RESULT_TYPE, CDPEvent, CDPMethod, Target


class CDPSession(BaseModel):
    ws_endpoint: str
    target_id: Target.TargetID

    _receive_task: asyncio.Task | None = PrivateAttr(default=None)
    _ws_connection: ClientConnection | None = PrivateAttr(default=None)
    _commands_manager: CommandsManager = PrivateAttr(default=CommandsManager())
    _events_manager: EventsManager = PrivateAttr(default=EventsManager())

    async def _parse_ws_address(self) -> str:
        if self.target_id == 'browser':
            return await self.get_browser_ws_address()
        else:
            return f'ws://{self.ws_endpoint}/devtools/page/{self.target_id}'

    async def get_browser_ws_address(self) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://{self.ws_endpoint}/json/version') as resp:
                    data = await resp.json()
                    return data['webSocketDebuggerUrl']
        except (aiohttp.ClientError, KeyError) as exc:
            raise NetworkError(f'Failed to get websocket address: {exc}')
        except KeyError as exc:
            raise InvalidResponse(f'Failed to get browser ws address: {exc}')

    async def _ensure_active_connection(self) -> None:
        if self._ws_connection is None or self._ws_connection.state is State.CLOSED:
            await self.establish_new_connection()

    async def establish_new_connection(self) -> None:
        ws_address = await self._parse_ws_address()
        logger.debug(f'ws_address: {ws_address}')

        self._ws_connection = await websockets.connect(
            ws_address,
            max_size=1024 * 1024 * 10  # 10MB
        )
        logger.info(f'start get page events: {ws_address}')
        self._receive_task = asyncio.create_task(self._receive_events())

    async def ping(self) -> bool:
        await self._ensure_active_connection()

        with suppress():
            await self._ws_connection.ping()
            return True
        return False

    async def execute(self, cdp_method: CDPMethod[RESULT_TYPE], timeout: int = 3) -> RESULT_TYPE:
        await self._ensure_active_connection()

        _id, future = self._commands_manager.create_command_future()
        command = cdp_method.command
        command['id'] = _id
        logger.info(f'execute command: {command}')

        try:
            await self._ws_connection.send(json.dumps(command))
            response: str = await asyncio.wait_for(future, timeout)
            resp_json = json.loads(response)
            if 'error' in resp_json:
                raise CommandExecutionError(f'Command {command} execution failed: {resp_json["error"]}')
            return await cdp_method.parse_response(json.dumps(resp_json['result']))
        except TimeoutError:
            self._commands_manager.remove_pending_command(_id)
            raise CommandExecutionTimeout()
        except websockets.ConnectionClosed:
            await self.close()
            raise WebSocketConnectionClosed()

    async def close(self) -> None:
        await self.clear_callbacks()

        if self._ws_connection:
            with suppress(websockets.ConnectionClosed):
                await self._ws_connection.close()

        self._ws_connection = None

        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()

        logger.info('Connection resources cleaned up')

    async def _incoming_messages(self) -> AsyncIterable[websockets.Data]:
        while self._ws_connection.state is not State.CLOSED:
            yield await self._ws_connection.recv()

    async def _receive_events(self) -> None:
        try:
            async for raw_message in self._incoming_messages():
                await self._process_single_message(raw_message)
        except websockets.ConnectionClosed as exc:
            logger.info(f'Connection closed gracefully: {exc}')
        except Exception as exc:
            logger.error(f'Unexpected error in event loop: {exc}')
            raise exc

    async def _process_single_message(self, raw_message: str) -> None:
        message = await self._parse_message(raw_message)
        if message is None:
            return

        if await self._is_command_response(message):
            await self._handle_command_message(message)
        else:
            await self._handle_event_message(message)

    @staticmethod
    async def _is_command_response(message: dict[str, Any]) -> bool:
        return isinstance(message.get('id'), int)

    @staticmethod
    async def _parse_message(raw_message: str) -> dict[str, Any] | None:
        try:
            return json.loads(raw_message)
        except json.JSONDecodeError as exc:
            logger.warning(f'Failed to parse raw message: {raw_message[:200]}, {exc}')
            return None

    async def _handle_command_message(self, message: dict[str, Any]) -> None:
        logger.info(f'Processing command response: {message["id"]}')

        self._commands_manager.resolve_command(message)

    async def _handle_event_message(self, message: dict[str, Any]) -> None:
        logger.info(f'Processing event message: {message}')

        if 'method' in message:
            await self._events_manager.process_event(message)
        else:
            logger.warning('unknown event')

    def __str__(self) -> str:
        return f'CDPSession(ws_endpoint={self.ws_endpoint}, target_id={self.target_id})'

    def __repr__(self) -> str:
        return self.__str__()

    async def register_callback(self, event: type[CDPEvent], callback: Callable, temporary: bool = False) -> int:
        return await self._events_manager.register_callback(
            event=event,
            callback=callback,
            temporary=temporary
        )

    async def remove_callback(self, callback_id: int) -> bool:
        return await self._events_manager.remove_callback(callback_id)

    async def clear_callbacks(self):
        await self._events_manager.clear_callbacks()


class CDPSessionManager(BaseModel):
    ws_endpoint: str

    _connection_session: dict[str, CDPSession] = PrivateAttr(default_factory=dict)

    async def remove_session(self, target_id: Target.TargetID = 'browser') -> None:
        if target_id in self._connection_session:
            await self._connection_session[target_id].close()
            del self._connection_session[target_id]

    async def get_session(self, target_id: Target.TargetID = 'browser') -> CDPSession:
        if target_id not in self._connection_session:
            cdp_session = CDPSession(
                ws_endpoint=self.ws_endpoint,
                target_id=target_id,
            )
            self._connection_session[target_id] = cdp_session
        else:
            cdp_session = self._connection_session[target_id]

        return cdp_session

    def __str__(self):
        return f'CDPSessionManager(ws_endpoint={self.ws_endpoint})'

    def __repr__(self) -> str:
        return str(self)


class CDPSessionExecutor(BaseModel):
    session: CDPSession | None = None
    session_manager: CDPSessionManager | None = None

    async def on(self, event: type[CDPEvent], callback: callable, temporary: bool = False) -> int:
        """

        Examples:
            async def _on_target_created(event_data: Target.TargetCreated):
                ...

            await session.on(event=TargetCreated, callback=_on_target_created)
        """
        sig = inspect.signature(callback)
        if 'event_data' in sig.parameters:
            # raise CallbackParameterError('Required parameter "event_data" not found in callback function')
            event_data_type = sig.parameters["event_data"].annotation

            event_name = re.sub(
                    r'(?<=\.)([a-z])',
                    lambda m: m.group(1).upper(),
                    event.EVENT_NAME
                )
            if isinstance(event_data_type, str):
                if not (event_data_type == event_name):
                    raise CallbackParameterError(
                        f"Parameter 'event_data' type mismatch. "
                        f"Expected {event_name}, but got {event_data_type}."
                    )
            elif not issubclass(event_data_type, event):
                raise CallbackParameterError(
                    f"Parameter 'event_data' type mismatch. "
                    f"Expected {event_name}, but got {event_data_type.__name__}."
                )
        return await self.session.register_callback(
            event, callback, temporary
        )

    async def execute_method(self, cdp_method: CDPMethod[RESULT_TYPE], timeout: int = 60) -> RESULT_TYPE:
        return await self.session.execute(
            cdp_method,
            timeout
        )
