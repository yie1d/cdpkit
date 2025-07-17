import asyncio
import inspect
from collections import defaultdict
from collections.abc import Callable
from functools import partial

from pydantic import BaseModel, PrivateAttr

from cdpkit.exception import InvalidCallback
from cdpkit.logger import logger
from cdpkit.protocol import CDPEvent


class EventsManager(BaseModel):
    _pending_events: dict[int, dict] = PrivateAttr(default_factory=dict)
    _callback_id: int = PrivateAttr(default=0)

    _events_callbacks: dict[str, list[int]] = PrivateAttr(default=defaultdict(list))

    async def register_callback(
        self, event: type[CDPEvent], callback: Callable, temporary: bool = False
    ) -> int:
        if not callable(callback):
            logger.error('Callback must be callable function.')
            raise InvalidCallback()

        self._callback_id += 1
        self._pending_events[self._callback_id] = {
            'event': event.EVENT_NAME,
            'callback': callback,
            'callback_event': event,
            'temporary': temporary
        }
        self._events_callbacks[event.EVENT_NAME].append(self._callback_id)

        return self._callback_id

    async def remove_callback(self, callback_id: int) -> bool:
        if callback_id not in self._pending_events:
            logger.warning(f'No pending message can be resolved for id {callback_id}')
            return False

        callback_info = self._pending_events[callback_id]
        self._events_callbacks[callback_info['event']].remove(callback_id)
        del self._pending_events[callback_id]

        return True

    async def clear_callbacks(self):
        self._pending_events.clear()
        self._events_callbacks.clear()

    async def process_event(self, event_data: dict):
        event_name = event_data.get('method')
        logger.info(f'Processing event: {event_name}')

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

            sig = inspect.signature(callback_func)
            if 'event_data' in sig.parameters:
                event_data = callback_info['callback_event'].model_validate(event_data['params'])
                callback_func = partial(callback_func, event_data=event_data)

            try:
                if asyncio.iscoroutinefunction(callback_func):
                    await callback_func()
                else:
                    callback_func()
            except Exception as exc:
                logger.error(f'Error processing callback {event_name} {event_data}: {exc}')

        for callback_id in callbacks_to_remove:
            await self.remove_callback(callback_id)
