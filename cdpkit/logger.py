import sys
from enum import IntEnum

from loguru import logger as _loguru_logger

__all__ = [
    'logger'
]


class LogLevel(IntEnum):
    """Log level enumeration class, inherits from IntEnum"""
    TRACE: int = 5
    DEBUG: int = 10
    INFO: int = 20
    SUCCESS: int = 25
    WARNING: int = 30
    ERROR: int = 40
    CRITICAL: int = 50


def set_logger(
    print_level: str | LogLevel = LogLevel.SUCCESS,
):
    """Configure and return a logger instance

    Args:
        print_level (str | LogLevel, optional):
            Log level to use. Defaults to LogLevel.INFO.

    Returns:
        loguru._logger.Logger: Configured logger instance.

    """
    _format = '{time:YYYY-MM-DD HH:mm:ss.SSS} |<lvl>{level:8}</>| {name:8} : {module}:{line:4} | - <lvl>{message}</>'

    if isinstance(print_level, str):
        try:
            print_level = LogLevel[print_level]
        except KeyError:
            raise KeyError(f'Invalid log level {print_level}')

    _loguru_logger.configure(
        handlers=[
            {
                'sink': sys.stdout,
                'format': _format,
                'colorize': True,
                'level': print_level.value,
                'enqueue': True
            }
        ]
    )
    return _loguru_logger


logger = set_logger(LogLevel.TRACE)
