# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/18/2025 11:37'
__version__ = '0.1.0'

import logging
from enum import Enum
from core.config import TypedConfig, EnvVariablePrefix


class ELogColor(Enum):
    '''Enumeration for ANSI color codes.'''

    WHITE = '\033[0;37m'
    GREEN = '\033[0;32m'
    BLUE = '\033[34;5;111m'
    RED = '\033[38;5;196m'
    YELLOW = '\033[38;5;190m'
    GREY = '\033[38;5;242m'
    BOLD_RED = '\033[38;5;196;1m'
    RESET = '\033[0m'


@EnvVariablePrefix('MAX_')
class LoggingConfiguration(TypedConfig):
    '''Logger configuration class.'''

    LOG_LEVEL: int = logging.INFO  # default log level

    #: log file format
    LOG_FILE_FORMAT: str = '%(asctime)s %(threadName)s/%(levelname)s/%(name)s: %(message)s'
    LOG_FILE_DATE_FORMAT: str = '%m-%d %H:%M:%S.%f'

    #: console log format
    LOG_CONSOLE_FORMAT: str = '%(asctime)s %(levelname)s/%(name)s: %(message)s'
    LOG_CONSOLE_DATE_FORMAT: str = '%H:%M:%S'

    LOG_FILE: str = 'app.log'  # log file name
    LOG_DIR: str = '/var/logs/max'  # log directory

    LOG_MAX_BYTES: int = 1024 * 1024 * 5  # 5 MB
    LOG_BACKUP_EXPIRED_TIME_SEC: int = 60 * 60 * 24 * 7  # 7 days
    LOG_BACKUP_NAME_FORMAT: str = '%Y-%m-%d_%H-%M-%S'  # backup file name format

    #: log colors
    LOG_USE_COLOR: bool = True  # use color in console output
    LOG_COLOR_MAP: dict[int, str] = {
        logging.DEBUG: ELogColor.GREY.value,
        logging.INFO: ELogColor.WHITE.value,
        logging.WARNING: ELogColor.YELLOW.value,
        logging.ERROR: ELogColor.RED.value,
        logging.CRITICAL: ELogColor.BOLD_RED.value,
    }

    def __init__(self) -> None:
        super().__init__()  # call super first
        self.set_loggers_level(self.LOG_LEVEL)

    def set_loggers_level_by_level_name(self, level_name: str) -> None:
        '''Set all exists loggers level to required.'''
        level_map = logging.getLevelNamesMapping()  # type: ignore
        if level_name in level_map:
            level = level_map[level_name]
            self.set_loggers_level(level)
        else:
            raise ValueError(f'Invalid log level: {level_name}')

    def set_loggers_level(self, level: int) -> None:
        self.LOG_LEVEL = level
        logging.root.setLevel(level)
        for logger in logging.Logger.manager.loggerDict.values():
            if isinstance(logger, logging.Logger):
                logger.setLevel(level)


if 'log_config' in __name__:
    LogConfig = LoggingConfiguration()
