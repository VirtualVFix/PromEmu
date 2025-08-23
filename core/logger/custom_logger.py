# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/18/2025 17:54'
__version__ = '0.1.0'

import logging
from pathlib import Path
from typing import Any, Generator
from typing_extensions import override

BLANK_LOGGER_FORMAT = '%(message)s'


class CustomLogger(logging.Logger):
    '''
    Custom logger class to handle logging with additional features.

    Features:
        - Blank line printing
        - Colorized logging messages
        - Other loggers propagation
    '''

    def __init__(self, name: str, level: int = logging.NOTSET) -> None:
        logger_name = Path(name).stem  # remove extension in case of used __file__ as logger name
        super().__init__(logger_name, level)

    def __prepare(
        self, msg: object, *args: Any, level: int
    ) -> Generator[tuple[str | object, logging.Logger, tuple[Any]]]:
        '''Prepare loggers and format message'''
        # prepare loggers
        logger_list = [self] + [x for x in args if isinstance(x, logging.Logger)]
        arguments = tuple(x for x in args if x and not isinstance(x, logging.Logger))
        for logger in logger_list:
            if isinstance(logger, logging.Logger):
                if self.isEnabledFor(level):
                    yield msg, logger, arguments

    def blank(self, *loggers: logging.Logger, lines: int = 1, level: int = logging.INFO) -> None:
        '''
        Print empty line to all logger handlers via change handlers formatter.

        Args:
            *loggers (logging.Logger): Additional loggers to repeat action
            lines (int): Lines counter
            level (int): Logger level
        '''
        logger_list = [self] + [x for x in loggers if isinstance(x, logging.Logger)]
        for logger in logger_list:
            formats = []
            for x in logger.handlers:
                formats.append(x.formatter)
                x.formatter = logging.Formatter(fmt=BLANK_LOGGER_FORMAT)

            for i in range(lines):
                logger.log(level, '')

            for i, x in enumerate(logger.handlers):
                x.formatter = formats[i]

    @override
    def info(self, msg: object, *args: Any, **kwargs: Any) -> None:
        '''
        Print message to current and additional loggers.

        Args:
            msg: Logger message
            *args: Additional loggers to message propagation or format args
            **kwargs: Additional arguments for logger

        Usage:

        .. code-block:: python

            from core import getLogger

            logger = getLogger(__file__)
            logger2 = getLogger('custom')
            logger3 = getLogger('custom2', 'custom.log')

            logger.info("some message", logger2, logger3)
            logger.error("some error", logger3)
        '''
        for message, logger, arguments in self.__prepare(msg, *args, level=logging.INFO):
            logger._log(logging.INFO, message, arguments, **kwargs)

    @override
    def debug(self, msg: object, *args: Any, **kwargs: Any) -> None:
        for message, logger, arguments in self.__prepare(msg, *args, level=logging.DEBUG):
            logger._log(logging.DEBUG, message, arguments, **kwargs)

    @override
    def warning(self, msg: object, *args: Any, **kwargs: Any) -> None:
        for message, logger, arguments in self.__prepare(msg, *args, level=logging.WARNING):
            logger._log(logging.WARNING, message, arguments, **kwargs)

    @override
    def error(self, msg: object, *args: Any, **kwargs: Any) -> None:
        for message, logger, arguments in self.__prepare(msg, *args, level=logging.ERROR):
            logger._log(logging.ERROR, message, arguments, **kwargs)

    @override
    def critical(self, msg: object, *args: Any, **kwargs: Any) -> None:
        for message, logger, arguments in self.__prepare(msg, *args, level=logging.CRITICAL):
            logger._log(logging.CRITICAL, message, arguments, **kwargs)

    @override
    def exception(self, msg: object, *args: Any, **kwargs: Any) -> None:
        if 'exc_info' not in kwargs:
            kwargs['exc_info'] = True
        for message, logger, arguments in self.__prepare(msg, *args, level=logging.ERROR):
            logger._log(logging.ERROR, message, arguments, **kwargs)
