from .base import CustomException


class ExecutableNotFoundError(CustomException):
    ERROR_INFO = 'Executable path not found, please check the settings.'


class NoSuchElement(CustomException):
    ERROR_INFO = 'No such element.'


class TabNotFoundError(CustomException):
    ERROR_INFO = 'Tab not found.'


class BrowserLaunchError(CustomException):
    ERROR_INFO = 'Browser launch error.'


class NoValidTabError(CustomException):
    ERROR_INFO = 'No valid tab available.'


class ElementNotFileInput(CustomException):
    ERROR_INFO = 'Element is not a file input.'


class ArgumentAlreadyExistsInOptions(CustomException):
    ERROR_INFO = 'Argument already exists in options.'


class ParamsMustSpecified(CustomException):
    ERROR_INFO = 'Params must specified.'


class ScriptRunError(CustomException):
    ERROR_INFO = 'Script run error.'
