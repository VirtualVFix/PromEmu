# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/11/2025 16:15'
__version__ = '0.1.0'

import logging
from pathlib import Path

from core.logger import LogConfig
from core.config import TypedConfig, EnvVariablePrefix


APP_NAME = 'Prometheus Metrics Emulator (PromEmu)'
APP_VERSION = '1.0.0'


@EnvVariablePrefix('PME_')
class EmulatorAppConfiguration(TypedConfig):
    '''Emulator configuration class.'''

    DEBUG_MODE: bool = False  # enable debug mode

    CONFIGS_DIR: Path = Path(__file__).parent / 'configs'
    PUSHGATEWAY_URL: str = 'http://localhost:9091'
    PUSHGATEWAY_PUSH_INTERVAL: float = 15.0
    PUSHGATEWAY_CLEANUP_ON_START: bool = True
    PUSHGATEWAY_CLEANUP_ON_FINISH: bool = True

    # show detailed hosts status
    SHOW_STATUS_INTERVAL_SEC: int = 30
    SHOW_HOSTS_STATUS: bool = True
    SHOW_METRICS_STATUS: bool = False

    def __init__(self) -> None:
        super().__init__()  # call super first
        if self.DEBUG_MODE:
            LogConfig.set_loggers_level(logging.DEBUG)


if 'app_config' in __name__:
    AppConfig = EmulatorAppConfiguration()
