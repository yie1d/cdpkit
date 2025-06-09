from .base import CustomException


class GeneratorNameNotFound(CustomException):
    ERROR_INFO = 'Generator name not found, must run generate_code.'
