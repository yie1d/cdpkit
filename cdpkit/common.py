import inspect
from typing import Any, TypeVar, Generic
from pathlib import Path
from pydantic import BaseModel, ConfigDict, TypeAdapter

RESULT_TYPE = TypeVar('RESULT_TYPE')

"""
***************************************************
                    Base Pydantic Models
***************************************************
"""


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


"""
***************************************************
                    Common Types
***************************************************
"""
JSON_DICT = dict[str, Any]

"""
***************************************************
                    Methods
***************************************************
"""


class CDPMethod(Generic[RESULT_TYPE]):
    INPUT_VALIDATOR: InputModel | None = None
    OUTPUT_VALIDATOR: OutputModel | None = None

    def __init__(self, *_, **kwargs):
        if self.INPUT_VALIDATOR is None:
            self._params = kwargs
        else:
            input_model = self.INPUT_VALIDATOR.model_validate(kwargs)
            self._params = input_model.model_dump(exclude_none=True)
        self._command: JSON_DICT | None = None

    @property
    def command(self):
        if self._command is None:
            # /fake/dir/cdpkit/Target.py -> Target
            domain_name = Path(inspect.getfile(self.__class__)).stem
            # ActivateTarget -> activateTarget
            method_name = self.__class__.__name__
            method_name = f'{method_name[0].lower()}{method_name[1:]}'

            self._command = {
                'method': f'{domain_name}.{method_name}',
                'params': self._params,
            }
        return self._command

    async def parse_response(self, response: JSON_DICT) -> RESULT_TYPE:
        if self.OUTPUT_VALIDATOR is None:
            return None
        else:
            return self.OUTPUT_VALIDATOR.model_validate(response).field
