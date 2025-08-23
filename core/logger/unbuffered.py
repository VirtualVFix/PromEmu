# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/18/2025 23:56'
__version__ = '0.1.0'

import logging
from typing import Any


class Unbuffered:
    '''Unbuffered stream wrapper for stdout and stderr.'''

    def __init__(self, stream: Any, logger: logging.Logger, level: int = logging.INFO) -> None:
        self.stream = stream
        self.log = logger
        self.level = level

    def write(self, data: str) -> None:
        self.stream.write(data)
        self.stream.flush()
        if self.log is not None and data != '\n':
            self.log.log(self.level, data)

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.stream, attr)
