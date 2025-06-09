from .base import CustomException


class InvalidCallback(CustomException):
    ERROR_INFO = 'Invalid callback, must be callable.'


class CallbackParameterError(CustomException):
    ERROR_INFO = 'Callback parameter error.'