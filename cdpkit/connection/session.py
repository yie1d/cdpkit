import asyncio
import inspect
import json
from collections.abc import AsyncIterable
from typing import Any

import aiohttp
import websockets

from cdpkit.connection.handler import CDPCommandsHandler, CDPEventsHandler
from cdpkit.exception import CallbackParameterError
from cdpkit.logger import logger
from cdpkit.protocol import RESULT_TYPE, CDPEvent, CDPMethod, Target


class CDPSession:
    def __init__(self, connection_port: int, target_id: Target.TargetID):
        self._connection_port = connection_port
        self._target_id = target_id

        self._receive_task: asyncio.Task | None = None
        self._ws_connection: websockets.ClientConnection | None = None
        self._command_handler = CDPCommandsHandler()
        self.event_handler = CDPEventsHandler()

    async def _parse_ws_address(self) -> str:
        if self._target_id == 'browser':
            return await self.get_browser_ws_address()
        else:
            return f'ws://localhost:{self._connection_port}/devtools/page/{self._target_id}'

    async def get_browser_ws_address(self) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://localhost:{self._connection_port}/json/version') as resp:
                    data = await resp.json()
                    return data['webSocketDebuggerUrl']
        except (aiohttp.ClientError, KeyError) as err:
            raise Exception(f'Failed to get websocket address: {err}')

    async def _ensure_active_connection(self) -> None:
        if self._ws_connection is None:
            await self.establish_new_connection()

    @property
    def ws_connection(self) -> websockets.ClientConnection:
        if self._ws_connection is None:
            raise Exception("Websocket connection was not established")
        return self._ws_connection

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

        try:
            await self.ws_connection.ping()
            return True
        except Exception as exc:
            logger.warning(f'Failed to ping: {exc}')
            return False

    async def execute(self, cdp_method: CDPMethod[RESULT_TYPE], timeout: int = 10) -> RESULT_TYPE:
        await self._ensure_active_connection()

        _id, future = self._command_handler.create_command_future()
        command = cdp_method.command
        command['id'] = _id

        try:
            await self.ws_connection.send(json.dumps(command))
            response: str = await asyncio.wait_for(future, timeout)
            return await cdp_method.parse_response(response)
        except TimeoutError as exc:
            self._command_handler.remove_pending_command(_id)
            raise exc
        except websockets.ConnectionClosed as exc:
            await self.close()
            raise exc

    async def close(self) -> None:
        if self._ws_connection:
            await self._ws_connection.close()
        self._ws_connection = None

        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()

        logger.info('Connection resources cleaned up')

    async def _incoming_messages(self) -> AsyncIterable[websockets.Data]:
        while True:
            yield await self.ws_connection.recv()

    async def _receive_events(self) -> None:
        try:
            async for raw_message in self._incoming_messages():
                await self._process_single_message(raw_message)
        except websockets.ConnectionClosed as exc:
            logger.info(f'Connection closed gracefully: {exc}')
        except Exception as exc:
            logger.error(f'Unexpected error in event loop: {exc}')
            raise

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
        logger.debug(f'Processing command response: {message["id"]}')
        if 'result' in message:
            self._command_handler.resolve_command(message['id'], json.dumps(message['result']))
        else:
            logger.error(f'Failed to resolve command response: {message}')

    async def _handle_event_message(self, message: dict[str, Any]) -> None:
        logger.info(f'Processing event message: {message}')

        if 'method' in message:
            await self.event_handler.process_event(message)
        else:
            logger.warning('unknown event')

    def __str__(self) -> str:
        return f'CDPSession(connection_port={self._connection_port}, target_id={self._target_id})'

    def __repr__(self) -> str:
        return str(self)


class CDPSessionManager:
    def __init__(
        self,
        connection_port: int
    ):
        self._connection_port = connection_port
        self._connection_session: dict[str, CDPSession] = {}

    async def remove_session(self, page_id: str = 'browser') -> None:
        if page_id in self._connection_session:
            await self._connection_session[page_id].close()
            del self._connection_session[page_id]

    def get_session(self, target_id: Target.TargetID = 'browser') -> CDPSession:
        if target_id not in self._connection_session:
            cdp_session = CDPSession(
                connection_port=self._connection_port,
                target_id=target_id,
            )
            self._connection_session[target_id] = cdp_session
        else:
            cdp_session = self._connection_session[target_id]

        return cdp_session

    def __str__(self):
        return f'CDPSessionManager(port={self._connection_port})'

    def __repr__(self) -> str:
        return str(self)


class CDPSessionExecutor:
    def __init__(
        self,
        session: CDPSession | None = None,
        session_manager: CDPSessionManager | None = None
    ) -> None:
        self._session = session
        self._session_manager = session_manager

    async def on(self, event: type[CDPEvent], callback: callable, temporary: bool = False) -> int:
        """

        Examples:
            async def _on_target_created(event_data: Target.TargetCreated):
                ...

            await session.on(event=TargetCreated, callback=_on_target_created)
        """
        sig = inspect.signature(callback)
        if 'event_data' not in sig.parameters:
            raise CallbackParameterError('Required parameter "event_data" not found in callback function')
        if issubclass(sig.parameters["event_data"].annotation, event) is False:
            raise CallbackParameterError(
                f"Parameter 'event_data' type mismatch. "
                f"Expected {event.__name__}, but got {sig.parameters['event_data'].annotation.__name__}."
            )
        return await self._session.event_handler.register_callback(
            event, callback, temporary
        )

    async def execute_method(self, cdp_method: CDPMethod[RESULT_TYPE], timeout: int = 60) -> RESULT_TYPE:
        return await self._session.execute(
            cdp_method,
            timeout
        )
