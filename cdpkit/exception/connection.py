from .base import CustomException


class InvalidCallback(CustomException):
    ERROR_INFO = 'Invalid callback, must be callable.'


class CallbackParameterError(CustomException):
    ERROR_INFO = 'Callback parameter error.'


class NetworkError(CustomException):
    ERROR_INFO = 'Network error.'


class InvalidResponse(CustomException):
    ERROR_INFO = 'The response received is invalid.'


class CommandExecutionTimeout(CustomException):
    ERROR_INFO = 'The command execution timed out.'


class WebSocketConnectionClosed(CustomException):
    ERROR_INFO = 'The WebSocket connection is closed'
