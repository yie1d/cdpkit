class BaseCustomException(Exception):
    """
    Base custom exception class

    The base class for all custom exceptions, supporting default or custom error messages
    """
    ERROR_INFO = ''

    def __init__(self, error_info: str | None = None):
        """
        Initialize the exception instance

        Args:
            error_info (str | None, optional):
                Custom error message. If None, use the default value from the class attribute ERROR_INFO
                Default: None
        """
        if error_info is None:
            super().__init__(self.ERROR_INFO)
        else:
            super().__init__(error_info)


class GeneratorNameNotFound(BaseCustomException):
    ERROR_INFO = 'Generator name not found, must run generate_code.'


class InvalidCallback(BaseCustomException):
    ERROR_INFO = 'Invalid callback, must be callable.'


class ExecutableNotFoundError(BaseCustomException):
    ERROR_INFO = 'Executable path not found, please check the settings.'


class PageNotFoundError(BaseCustomException):
    ERROR_INFO = 'Page not found.'


class CallbackParameterError(BaseCustomException):
    ERROR_INFO = 'Callback parameter error.'
