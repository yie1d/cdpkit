import inspect
from pathlib import Path
from typing import Any, TypeVar

from pydantic import BaseModel, ConfigDict

from cdpkit.logger import logger

__all__ = [
    'CDPObject',
    'InputModel',
    'OutputModel',
    'CDPEvent',
    'CDPMethod',
    'JSON_DICT',
    'RESULT_TYPE'
]

RESULT_TYPE = TypeVar('RESULT_TYPE')
JSON_DICT = dict[str, Any]


class CDPObject(BaseModel):
    """
    Base class for CDP objects

    The base class for all CDP-related objects, configured in strict mode to forbid extra fields.
    """
    model_config = ConfigDict(
        strict=True,
        extra='forbid'
    )


class InputModel(BaseModel):
    """
    Base class for input models

    The base class for input models used to validate input data, configured in strict mode to ignore extra fields.
    """
    model_config = ConfigDict(
        strict=True,
        extra='ignore'
    )


class OutputModel(BaseModel):
    """
    Base class for output models

    The base class for output models used to validate output data, configured in strict mode to ignore extra fields.
    """
    model_config = ConfigDict(
        strict=True,
        extra='ignore'
    )


class CDPEvent(BaseModel):
    """
    Base class for CDP events

    The base class for all CDP events, configured in strict mode to forbid extra fields.
    """
    model_config = ConfigDict(
        strict=True,
        extra='forbid'
    )


class CDPMethod[RESULT_TYPE]:
    """
    CDP method class

    Represents a method in the CDP protocol, containing input and output validators and command generation logic.

    Attributes:
        INPUT_VALIDATOR (InputModel | None): Input validator model
        OUTPUT_VALIDATOR (OutputModel | None): Output validator model
    """
    INPUT_VALIDATOR: InputModel | None = None
    OUTPUT_VALIDATOR: OutputModel | None = None

    def __init__(self, *_, **kwargs):
        """
        Initialize a CDP method instance

        Args:
            /: Indicates a parameter separator, and parameters after it can only be passed by keyword.
            **kwargs: Keyword arguments used to initialize the method's parameters.
        """
        if self.INPUT_VALIDATOR is None:
            self._params = kwargs
        else:
            input_model = self.INPUT_VALIDATOR.model_validate(kwargs)
            self._params = input_model.model_dump(exclude_none=True)
        self._command: JSON_DICT | None = None

    @property
    def command(self):
        """
        Get the command dictionary of the CDP method

        Returns:
            JSON_DICT: A dictionary containing the method name and parameters.
        """
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

    async def parse_response(self, response: str) -> RESULT_TYPE:
        """
        Parse the response of the CDP method

        Args:
            response (str): The response string.

        Returns:
            RESULT_TYPE: The parsed response result.
        """
        logger.info(f'Parsing response for command: {response}')
        if self.OUTPUT_VALIDATOR is None:
            return None
        else:
            return self.OUTPUT_VALIDATOR.model_validate_json(response)
