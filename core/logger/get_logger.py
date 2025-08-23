# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/10/2025 14:37'
__version__ = '0.1.0'

import sys
import logging
from pathlib import Path
from typing import Optional, cast

from .log_config import LogConfig
from .unbuffered import Unbuffered
from .custom_logger import CustomLogger
from .handlers import FileHandlerWithCompress, ColorStreamHandler

# register our custom logger class
logging.setLoggerClass(CustomLogger)


def getLogger(
    name: str, file: Optional[str] = LogConfig.LOG_FILE, propagate: bool = True, level: Optional[int] = None
) -> CustomLogger:
    '''
    Get logger with name.

    Args:
        name (str): Logger name. Recommended use `__file__` as logger name.
        file (str): Create file logger with file name.
        propagate (bool): If this evaluates to true, events logged to this logger will be passed to the handlers
            of higher level (ancestor) loggers, in addition to any handlers attached to this logger.
            Messages are passed directly to the ancestor loggers handlers - neither the level nor filters
            of the ancestor loggers in question are considered. If this evaluates to false, logging messages
            are not passed to the handlers of ancestor loggers. The constructor sets this attribute to True.
        level (int): Logger level. By default setups automatically according to Framework debug mode.

    Note:
        If you attach a handler to a logger and one or more of its ancestors,
        it may emit the same record multiple times. In general, you should not need to attach a handler
        to more than one logger - if you just attach it to the appropriate logger which is highest in the
        logger hierarchy, then it will see all events logged by all descendant loggers, provided that their
        propagate setting is left set to True. A common scenario is to attach handlers only to the root
        logger, and to let propagation take care of the rest.

    Returns:
        Logger with stream and/or file handler

    Example:

    .. code-block:: python

         from core import get_logger

         logger = get_logger(__file__)
         logger.info('text')
         logger.blank()
    '''
    if not propagate and file is None:
        raise ValueError('You must set file name if propagate is False!')

    # log path
    log_path = Path(LogConfig.LOG_DIR)
    if not log_path.exists():
        try:
            log_path.mkdir(parents=True, mode=0o655, exist_ok=True)
        except (OSError, PermissionError):
            # if can't create log directory, use current directory
            log_path = Path.cwd() / 'logs'
            try:
                log_path.mkdir(parents=True, mode=0o655, exist_ok=True)
            except (OSError, PermissionError):
                # if still can't create, just use current directory
                log_path = Path.cwd()

    # create logger
    level = level or LogConfig.LOG_LEVEL
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()

    # ensure we have the correct type (CustomLogger due to setLoggerClass above)
    assert isinstance(logger, CustomLogger), f'Expected CustomLogger, got {type(logger)}'

    # stream formatter
    stream_formatter = LogConfig.LOG_CONSOLE_FORMAT
    stream_date = LogConfig.LOG_CONSOLE_DATE_FORMAT

    # console logger
    if propagate:
        handler = ColorStreamHandler()
        formatter = logging.Formatter(stream_formatter, datefmt=stream_date)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = propagate

    # file logger
    if file is not None:
        log_name = file
        if not log_name.endswith('.log'):
            log_name += '.log'

        # create file handler
        log_file_path = log_path / log_name
        handler = FileHandlerWithCompress(str(log_file_path), maxBytes=LogConfig.LOG_MAX_BYTES, encoding='utf-8')  # type: ignore

        # file formatter
        formatter = logging.Formatter(LogConfig.LOG_FILE_FORMAT, datefmt=LogConfig.LOG_FILE_DATE_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = propagate
    return cast(CustomLogger, logger)


if 'get_logger' in __name__:
    # configure unbuffered output
    log_stdout = getLogger('stdout', propagate=False, level=logging.INFO)
    sys.stdout = Unbuffered(sys.stdout, logger=log_stdout, level=logging.INFO)
    # log_stderr = getLogger('stderr', propagate=False, level=logging.ERROR)
    # sys.stderr = Unbuffered(sys.stderr, logger=log_stderr, level=logging.ERROR)
