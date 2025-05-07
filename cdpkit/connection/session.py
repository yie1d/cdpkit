import asyncio
import functools
import json
from collections.abc import AsyncIterable
from typing import Any

import aiohttp
import websockets

from cdpkit.connection.handler import CDPCommandsHandler, CDPEventsHandler
from cdpkit.logger import logger


def async_ensure_connection(func):
    @functools.wraps(func)
    async def wrapper(self: 'CDPSession', *args, **kwargs):
        await self._ensure_active_connection()
        return await func(self, *args, **kwargs)
    return wrapper


class CDPSession:
    def __init__(self, ws_address: str):
        logger.info(f'ws_address: {ws_address}')
        self._ws_address = ws_address

        self._receive_task: asyncio.Task | None = None
        self._ws_connection: websockets.ClientConnection | None = None
        self._command_handler = CDPCommandsHandler()
        self._event_handler = CDPEventsHandler()

    async def _ensure_active_connection(self) -> None:
        if self._ws_connection is None:
            await self.establish_new_connection()

    @property
    def ws_connection(self) -> websockets.ClientConnection:
        if self._ws_connection is None:
            raise Exception("Websocket connection was not established")
        return self._ws_connection

    async def establish_new_connection(self) -> None:
        self._ws_connection = await websockets.connect(
            self._ws_address,
            max_size=1024 * 1024 * 10  # 10MB
        )
        logger.info(f'start get page events: {self._ws_address}')
        self._receive_task = asyncio.create_task(self._receive_events())

    @async_ensure_connection
    async def ping(self) -> bool:
        try:
            await self.ws_connection.ping()
            return True
        except Exception as exc:
            logger.warning(f'Failed to ping: {exc}')
            return False

    @async_ensure_connection
    async def execute_command(self, command: dict[str, Any], timeout: int = 10) -> str:
        _id, future = self._command_handler.create_command_future()
        command['id'] = _id

        try:
            await self.ws_connection.send(json.dumps(command))
            response: str = await asyncio.wait_for(future, timeout)
            return response
        except TimeoutError as exc:
            self._command_handler.remove_pending_command(_id)
            raise exc
        except websockets.ConnectionClosed as exc:
            await self._cleanup()
            raise exc

    async def _cleanup(self) -> None:
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
            await self._event_handler.process_event(message)
        else:
            logger.warning('unknown event')

    def __str__(self) -> str:
        return f'CDPSession(address={self._ws_address})'

    def __repr__(self) -> str:
        return str(self)


class CDPSessionManager:
    def __init__(
        self,
        connection_port: int
    ):
        self._connection_port = connection_port
        self._connection_session = {}

    async def _parse_ws_address(self, page_id: str) -> str:
        if page_id == 'browser':
            return await self.get_browser_ws_address()
        else:
            return f'ws://localhost:{self._connection_port}/devtools/page/{page_id}'

    async def get_browser_ws_address(self) -> str:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f'http://localhost:{self._connection_port}/json/version') as resp:
                    data = await resp.json()
                    return data['webSocketDebuggerUrl']
        except aiohttp.ClientError as err:
            raise Exception(f'Failed to get websocket address: {err}')
        except KeyError as err:
            raise Exception(f'Failed to get websocket address: {err}')

    async def get_session(self, page_id: str = 'browser') -> CDPSession:
        if page_id not in self._connection_session:
            ws_address = await self._parse_ws_address(page_id)
            cdp_session = CDPSession(ws_address)
            await cdp_session.establish_new_connection()
            self._connection_session[page_id] = cdp_session
        else:
            cdp_session = self._connection_session[page_id]

        return cdp_session

    def __str__(self):
        return f'CDPSessionManager(port={self._connection_port})'

    def __repr__(self) -> str:
        return str(self)
