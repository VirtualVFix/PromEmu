# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/19/2025 12:37'

import pytest
import logging
import tempfile

from pathlib import Path
from typing import Generator, Callable, Any, cast


@pytest.fixture
def temp_log_dir() -> Generator[Path, None, None]:
    '''
    Creates a temporary directory for log files.

    Returns:
        Path to the temporary directory
    '''
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        yield temp_path


@pytest.fixture
def mock_log_config(monkeypatch: pytest.MonkeyPatch, temp_log_dir: Path) -> None:
    '''
    Mocks the LogConfig for testing.

    Args:
        monkeypatch: pytest fixture for patching objects
        temp_log_dir: temporary directory path for log files
    '''
    from core.logger.log_config import LogConfig

    # Create a safe logs directory within the temp directory
    logs_dir = temp_log_dir / 'logs'
    logs_dir.mkdir(exist_ok=True)

    # Test-specific configuration values - independent of actual LogConfig defaults
    TEST_LOG_CONFIG = {
        'LOG_DIR': str(logs_dir),
        'LOG_FILE': 'mock_test.log',  # unique test filename
        'LOG_MAX_BYTES': 2048,  # test-specific size (2KB)
        'LOG_LEVEL': logging.INFO,  # Add explicit log level
    }

    # instead of directly setting attributes, use the underlying _cache dictionary
    monkeypatch.setattr(LogConfig, '_cache', TEST_LOG_CONFIG)

    # patch the _types dictionary to include our mock config values
    current_types = getattr(LogConfig, '_types', {})
    types_with_mocks = current_types.copy()
    types_with_mocks.update({'LOG_DIR': str, 'LOG_FILE': str, 'LOG_MAX_BYTES': int, 'LOG_LEVEL': int})
    monkeypatch.setattr(LogConfig, '_types', types_with_mocks)

    # Also patch the direct attributes for backward compatibility
    monkeypatch.setattr(LogConfig, 'LOG_DIR', str(logs_dir))
    monkeypatch.setattr(LogConfig, 'LOG_FILE', 'mock_test.log')
    monkeypatch.setattr(LogConfig, 'LOG_MAX_BYTES', 2048)
    monkeypatch.setattr(LogConfig, 'LOG_LEVEL', logging.INFO)


@pytest.fixture
def capture_logs() -> Callable[[Any], list[str]]:
    '''
    Creates a fixture to capture logs from a handler.

    Returns:
        Function that takes a handler and returns captured log messages
    '''

    def _capture_logs(handler: Any) -> list[str]:
        if not hasattr(handler, 'messages'):
            return []
        return cast(list[str], handler.messages)

    return _capture_logs


class LogCaptureHandler(logging.Handler):
    '''Handler that captures log messages.'''

    def __init__(self) -> None:
        super().__init__()
        self.log = logging.getLogger(self.__class__.__name__)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(self.format(record))


@pytest.fixture
def log_capture_handler() -> LogCaptureHandler:
    '''
    Creates a handler that captures log messages.

    Returns:
        Handler that captures log messages
    '''
    handler = LogCaptureHandler()
    handler.setFormatter(logging.Formatter('%(message)s'))
    return handler
