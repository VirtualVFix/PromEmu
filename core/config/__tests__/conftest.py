# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/10/2025 14:45'

import os
import logging
from typing import Generator

import pytest

from core.config.typed_config import TypedConfig


@pytest.fixture
def config() -> TypedConfig:
    '''Fixture to provide a fresh TypedConfig instance for each test.'''
    return TypedConfig()


@pytest.fixture
def env_backup() -> Generator:
    '''Fixture to save and restore environment variables.'''
    original_env = os.environ.copy()
    yield
    # restore original environment variables after each test
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def disable_logging() -> Generator:
    '''Temporarily disable logging during tests.'''
    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]
    original_levels = {logger: logger.level for logger in loggers}
    for logger in loggers:
        logger.setLevel(logging.CRITICAL)
    yield
    # restore original log levels
    for logger, level in original_levels.items():
        logger.setLevel(level)
