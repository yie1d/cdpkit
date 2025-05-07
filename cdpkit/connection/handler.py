import asyncio
from collections import defaultdict
from collections.abc import Callable

from cdpkit.exceptions import InvalidCallback
from cdpkit.logger import logger


class CDPCommandsHandler:
    def __init__(self):
        self._pending_commands: dict[int, asyncio.Future] = {}
        self._command_id: int = 0

    def create_command_future(self) -> tuple[int, asyncio.Future]:
        self._command_id += 1
        future = asyncio.Future()
        self._pending_commands[self._command_id] = future
        return self._command_id, future

    def remove_pending_command(self, response_id: int):
        if response_id in self._pending_commands:
            del self._pending_commands[response_id]

    def resolve_command(self, response_id: int, result: str):
        if response_id in self._pending_commands:
            self._pending_commands[response_id].set_result(result)
            del self._pending_commands[response_id]
        else:
            logger.warning(f'No pending message can be resolve for id {response_id}')


class CDPEventsHandler:
    def __init__(self):
        # 用于记录挂起的callback_id及对应的callback_info
        self._pending_events: dict[int, dict] = {}
        self._callback_id = 0

        # 用于记录event对应的callback_id
        self._events_callbacks: dict[str, list[int]] = defaultdict(list)

    def register_callback(
        self, event_name: str, callback: Callable, temporary: bool = False
    ) -> int:
        if not callable(callback):
            logger.error('Callback must be callable function.')
            raise InvalidCallback()

        self._callback_id += 1
        self._pending_events[self._callback_id] = {
            'event': event_name,
            'callback': callback,
            'temporary': temporary
        }
        self._events_callbacks[event_name].append(self._callback_id)

        return self._callback_id

    def remove_callback(self, callback_id: int) -> bool:
        if callback_id not in self._pending_events:
            logger.warning(f'No pending message can be resolved for id {callback_id}')
            return False

        callback_info = self._pending_events[callback_id]
        self._events_callbacks[callback_info['event']].remove(callback_id)
        del self._pending_events[callback_id]

        return True

    def clear_callbacks(self):
        self._pending_events.clear()
        self._events_callbacks.clear()

    async def process_event(self, event_data: dict):
        event_name = event_data.get('method')
        logger.debug(f'Processing event: {event_name}')

        await self._trigger_callbacks(event_name, event_data)

    async def _trigger_callbacks(self, event_name: str, event_data: dict):
        if event_name not in self._events_callbacks:
            return

        callbacks_to_remove = []

        for callback_id in self._events_callbacks[event_name]:
            callback_info = self._pending_events[callback_id]
            if callback_info['temporary']:
                callbacks_to_remove.append(callback_id)

            callback_func = callback_info['callback']

            try:
                if asyncio.iscoroutinefunction(callback_func):
                    await callback_func(event_data)
                else:
                    callback_func(event_data)
            except Exception as exc:
                logger.error(f'Error processing callback {event_name} {event_data}: {exc}')

        for callback_id in callbacks_to_remove:
            self.remove_callback(callback_id)
