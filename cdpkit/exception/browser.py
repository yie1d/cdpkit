from .base import CustomException


class ExecutableNotFoundError(CustomException):
    ERROR_INFO = 'Executable path not found, please check the settings.'


class NoSuchElement(CustomException):
    ERROR_INFO = 'No such element.'


class PageNotFoundError(CustomException):
    ERROR_INFO = 'Page not found.'
