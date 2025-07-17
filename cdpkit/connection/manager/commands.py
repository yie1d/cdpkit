import asyncio
import json
from typing import Any

from pydantic import BaseModel, PrivateAttr

from cdpkit.logger import logger


class CommandsManager(BaseModel):
    _pending_commands: dict[int, asyncio.Future] = PrivateAttr(default_factory=dict)
    _command_id: int = PrivateAttr(default=0)

    def create_command_future(self) -> tuple[int, asyncio.Future]:
        self._command_id += 1
        future = asyncio.Future()
        self._pending_commands[self._command_id] = future
        return self._command_id, future

    def remove_pending_command(self, response_id: int):
        if response_id in self._pending_commands:
            del self._pending_commands[response_id]

    def resolve_command(self, message: dict[str, Any]):
        response_id = message.get('id')
        if response_id in self._pending_commands:
            self._pending_commands[response_id].set_result(json.dumps(message))
            del self._pending_commands[response_id]
        else:
            logger.warning(f'No pending message can be resolve for id {response_id}')
