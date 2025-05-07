import inspect
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from cdpkit.connection.session import CDPSession
from cdpkit.logger import logger

__all__ = [
    'CDPObject',
    'InputModel',
    'OutputModel',
    'CDPEvent',
    'CDPMethod',
    'JSON_DICT'
]

RESULT_TYPE = TypeVar('RESULT_TYPE')
JSON_DICT = dict[str, Any]


class CDPObject(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra='forbid'
    )


class InputModel(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra='ignore'
    )


class OutputModel(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra='ignore'
    )


class CDPEvent(BaseModel):
    model_config = ConfigDict(
        strict=True,
        extra='forbid'
    )


class CDPMethod(Generic[RESULT_TYPE]):
    INPUT_VALIDATOR: InputModel | None = None
    OUTPUT_VALIDATOR: OutputModel | None = None

    def __init__(self, /, *_, **kwargs):
        if self.INPUT_VALIDATOR is None:
            self._params = kwargs
        else:
            input_model = self.INPUT_VALIDATOR.model_validate(kwargs)
            self._params = input_model.model_dump(exclude_none=True)
        self._command: JSON_DICT | None = None

    @property
    def command(self):
        if self._command is None:
            # /fake/dir/cdpkit/Target/methods.py -> Target
            domain_name = Path(inspect.getfile(self.__class__)).parent.name
            # ActivateTarget -> activateTarget
            method_name = self.__class__.__name__
            method_name = f'{method_name[0].lower()}{method_name[1:]}'

            self._command = {
                'method': f'{domain_name}.{method_name}',
                'params': self._params,
            }
        return self._command

    async def execute_by(self, session: CDPSession) -> RESULT_TYPE:
        resp = await session.execute_command(self.command)
        return await self.parse_response(resp)

    async def parse_response(self, response: str) -> RESULT_TYPE:
        logger.info(f'Parsing response for command: {response}')
        if self.OUTPUT_VALIDATOR is None:
            return None
        else:
            return self.OUTPUT_VALIDATOR.model_validate_json(response)
