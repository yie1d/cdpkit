class CustomException(Exception):
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
            error_info = self.ERROR_INFO
        super().__init__(error_info)
