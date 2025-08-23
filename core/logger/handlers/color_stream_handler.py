# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/25/2025 19:15'
__version__ = '0.1.0'

import logging
from io import TextIOWrapper
from typing import Any, Optional
from typing_extensions import override

from ..log_config import LogConfig, ELogColor


class ColorStreamHandler(logging.StreamHandler):
    def __init__(self, stream: Optional[TextIOWrapper] = None) -> None:
        super().__init__(stream)

    @override
    def emit(self, record: Any) -> None:
        '''Override the emit method to handle color formatting.'''
        try:
            message = self.format(record)
            if LogConfig.LOG_USE_COLOR:
                color = LogConfig.LOG_COLOR_MAP.get(record.levelno, ELogColor.WHITE.value)
                # no color before first space in formatted message
                space = message.find(' ')
                message = f'{message[:space]}{color}{message[space:]}{ELogColor.RESET.value}'
            stream = self.stream
            stream.write(message + self.terminator)
            self.flush()
        except RecursionError:
            raise
        except Exception:
            self.handleError(record)
