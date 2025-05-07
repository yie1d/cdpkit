class BaseCustomException(Exception):
    ERROR_INFO = ''

    def __init__(self, error_info: str | None = None):
        if error_info is None:
            super().__init__(self.ERROR_INFO)
        else:
            super().__init__(error_info)


class GeneratorNameNotFound(BaseCustomException):
    ERROR_INFO = 'Generator name not found, must run generate_code.'


class InvalidCallback(BaseCustomException):
    ERROR_INFO = 'Invalid callback, must be callable.'