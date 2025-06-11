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
