# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/19/2025 12:37'

'''
Positive tests for get_logger module.
'''

import logging
from typing import cast
from pathlib import Path

import allure
import pytest

from ..conftest import LogCaptureHandler
from core.logger.get_logger import getLogger


@allure.feature('Logger')
@allure.story('GetLogger')
class TestGetLogger:
    '''Tests for the getLogger function'''

    @allure.title('Test getLogger creates a logger with correct name')
    def test_get_logger_name(self) -> None:
        '''Test that getLogger creates a logger with the correct name'''
        # when we create a logger with a path
        logger = getLogger('/path/to/module.py')

        # then the logger name should be the stem of the path
        assert logger.name == 'module'

        # and when we create a logger with just a name
        logger = getLogger('test_logger')

        # then the logger name should be the name we provided
        assert logger.name == 'test_logger'

    @allure.title('Test getLogger with stream handler')
    def test_get_logger_with_stream_handler(self) -> None:
        '''Test that getLogger creates a logger with a stream handler when propagate is True'''
        # when we create a logger with propagate=True
        logger = getLogger('test_logger', propagate=True)

        # then it should have a stream handler
        has_stream_handler = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
        assert has_stream_handler
        assert logger.propagate is True

    @allure.title('Test getLogger with file handler')
    def test_get_logger_with_file_handler(self, mock_log_config: None, temp_log_dir: Path) -> None:
        '''Test that getLogger creates a logger with a file handler when a file is specified'''
        # given a log config with a temporary directory

        # when we create a logger with a file
        logger = getLogger('test_logger', file='test_file.log')

        # then it should have a file handler
        from core.logger.handlers.file_handler_with_compress import FileHandlerWithCompress

        file_handlers = [h for h in logger.handlers if isinstance(h, FileHandlerWithCompress)]
        assert len(file_handlers) > 0

        # get the actual path from the handler
        actual_file_path = Path(file_handlers[0].baseFilename)
        assert actual_file_path.exists()

    @allure.title('Test getLogger with custom level')
    def test_get_logger_with_custom_level(self) -> None:
        '''Test that getLogger creates a logger with the specified level'''
        # when we create a logger with a custom level
        logger = getLogger('test_logger', level=logging.DEBUG)

        # then the logger should have the specified level
        assert logger.level == logging.DEBUG

        # when we create a logger with another level
        logger = getLogger('test_logger', level=logging.ERROR)

        # then the logger should have the new level
        assert logger.level == logging.ERROR

    @allure.title('Test getLogger adds handlers correctly')
    @pytest.mark.parametrize(
        'file_name,propagate,expected_handlers',
        [
            (None, True, 1),  # Only stream handler
            ('test.log', True, 2),  # Stream and file handler
            ('test.log', False, 1),  # Only file handler
        ],
    )
    def test_get_logger_handlers(
        self, mock_log_config: None, file_name: str, propagate: bool, expected_handlers: int
    ) -> None:
        '''Test that getLogger adds the correct handlers based on parameters'''
        # given a log config with a temporary directory

        # when we create a logger with the specified parameters
        logger = getLogger('test_logger', file=file_name, propagate=propagate)

        # then it should have the expected number of handlers
        assert len(logger.handlers) == expected_handlers

        # and the propagate flag should be set correctly
        assert logger.propagate is propagate

    @allure.title('Test getLogger writes to log file')
    def test_get_logger_writes_to_file(self, mock_log_config: None, temp_log_dir: Path) -> None:
        '''Test that getLogger's log messages are written to the log file'''
        # given a logger with a file handler
        log_file = 'write_test.log'
        logger = getLogger('test_logger', file=log_file)

        # when we log a message
        test_message = 'This is a test message'
        logger.info(test_message)

        # then the message should be written to the log file
        from core.logger.handlers.file_handler_with_compress import FileHandlerWithCompress

        file_handlers = [h for h in logger.handlers if isinstance(h, FileHandlerWithCompress)]
        assert len(file_handlers) > 0

        # get the actual path from the handler
        actual_file_path = Path(file_handlers[0].baseFilename)
        assert actual_file_path.exists()

        with open(actual_file_path, 'r') as f:
            log_content = f.read()
            assert test_message in log_content

    @allure.title('Test getLogger correctly formats messages')
    def test_get_logger_formatting(self, log_capture_handler: logging.Handler) -> None:
        '''Test that getLogger's log messages are correctly formatted'''
        # given a logger with a custom handler
        logger = getLogger('test_logger')
        logger.handlers.clear()
        logger.addHandler(log_capture_handler)

        # when we log messages with different levels
        test_message = 'Test message'
        logger.info(test_message)
        logger.error('Error: ' + test_message)

        # then the messages should be captured
        handler = cast(LogCaptureHandler, log_capture_handler)
        assert len(handler.messages) == 2
        assert test_message in handler.messages[0]
        assert 'Error: ' + test_message in handler.messages[1]

    @allure.title('Test logger propagate options work correctly')
    def test_logger_propagate_options(self, log_capture_handler: logging.Handler) -> None:
        '''Test that logger propagate options control message propagation correctly'''
        # given a root logger with a capture handler
        root_logger = logging.getLogger()
        root_logger.handlers.clear()
        root_logger.addHandler(log_capture_handler)
        root_logger.setLevel(logging.DEBUG)

        # when we create a logger with propagate=True
        logger_propagate = getLogger('test_logger_propagate', propagate=True)
        logger_propagate.setLevel(logging.DEBUG)

        # and a logger with propagate=False
        logger_no_propagate = getLogger('test_logger_no_propagate', propagate=False, file='test.log')
        logger_no_propagate.setLevel(logging.DEBUG)

        # then the propagate logger should propagate messages to root
        test_message_1 = 'Message from propagate logger'
        logger_propagate.info(test_message_1)

        # and the no-propagate logger should not propagate messages to root
        test_message_2 = 'Message from no-propagate logger'
        logger_no_propagate.info(test_message_2)

        # then only the propagate logger's message should appear in root handler
        handler = cast(LogCaptureHandler, log_capture_handler)
        captured_messages = ' '.join(handler.messages)
        assert test_message_1 in captured_messages
        assert test_message_2 not in captured_messages

        # verify propagate flags are set correctly
        assert logger_propagate.propagate is True
        assert logger_no_propagate.propagate is False

    @allure.title('Test multiple loggers do not duplicate messages')
    def test_multiple_loggers_no_duplication(self, log_capture_handler: logging.Handler) -> None:
        '''Test that multiple loggers with same name do not duplicate messages'''
        # given a capture handler
        handler = cast(LogCaptureHandler, log_capture_handler)

        # when we create multiple loggers with the same name
        logger1 = getLogger('same_logger_name')
        logger2 = getLogger('same_logger_name')

        # they should be the same instance (Python logging behavior)
        assert logger1 is logger2

        # clear handlers and add our capture handler
        logger1.handlers.clear()
        logger1.addHandler(log_capture_handler)
        logger1.propagate = False  # prevent root logger interference

        # when we log a message through either logger reference
        test_message = 'Test message for duplication check'
        logger1.info(test_message)
        logger2.info(test_message)

        # then we should see exactly 2 messages (not 4 due to duplication)
        assert len(handler.messages) == 2
        assert all(test_message in msg for msg in handler.messages)

        # when we create loggers with different names
        handler.messages.clear()
        logger3 = getLogger('different_logger_1')
        logger4 = getLogger('different_logger_2')

        # they should be different instances
        assert logger3 is not logger4

        # clear handlers and add capture handlers
        logger3.handlers.clear()
        logger4.handlers.clear()
        logger3.addHandler(log_capture_handler)
        logger4.addHandler(log_capture_handler)
        logger3.propagate = False
        logger4.propagate = False

        # when each logs a message
        logger3.info('Message from logger 3')
        logger4.info('Message from logger 4')

        # then we should see exactly 2 distinct messages
        assert len(handler.messages) == 2
        assert 'Message from logger 3' in handler.messages[0]
        assert 'Message from logger 4' in handler.messages[1]

    @allure.title('Test logger captures regular print messages')
    def test_logger_captures_print_messages(self, log_capture_handler: logging.Handler) -> None:
        '''Test that the logger system can capture regular print() statements'''
        import sys
        from core.logger.unbuffered import Unbuffered

        # given a capture handler and logger setup
        handler = cast(LogCaptureHandler, log_capture_handler)

        # create a logger for stdout capture
        stdout_logger = getLogger('test_stdout', propagate=False)
        stdout_logger.handlers.clear()
        stdout_logger.addHandler(log_capture_handler)
        stdout_logger.setLevel(logging.INFO)

        # save the original stdout
        original_stdout = sys.stdout

        try:
            # when we replace stdout with an Unbuffered wrapper that logs to our logger
            sys.stdout = Unbuffered(sys.stdout, logger=stdout_logger, level=logging.INFO)

            # and we use regular print statements
            print('Test message from print()')
            print('Another test message')
            print('Third message with special chars: àáâã')

            # then the messages should be captured by the logger
            assert len(handler.messages) == 3
            assert 'Test message from print()' in handler.messages[0]
            assert 'Another test message' in handler.messages[1]
            assert 'Third message with special chars: àáâã' in handler.messages[2]

            # when we print without newline (using end parameter)
            handler.messages.clear()
            print('Message without newline', end='')

            # it should still be captured (but may capture multiple calls)
            # Note: print() with end='' may still make multiple write() calls
            assert len(handler.messages) >= 1
            captured_content = ''.join(handler.messages)
            assert 'Message without newline' in captured_content

            # when we print an empty line
            handler.messages.clear()
            print('')  # This creates just a newline

            # it should not log the newline (Unbuffered skips newlines)
            # but may log empty strings from the print mechanism
            logged_content = [msg for msg in handler.messages if msg != '\n']
            # we don't care if empty strings are logged, just that newlines aren't
            assert '\n' not in handler.messages

        finally:
            # restore original stdout
            sys.stdout = original_stdout

    @allure.title('Test logger captures print with different data types')
    def test_logger_captures_print_different_types(self, log_capture_handler: logging.Handler) -> None:
        '''Test that the logger captures print statements with different data types'''
        import sys
        from core.logger.unbuffered import Unbuffered

        # given a capture handler and logger setup
        handler = cast(LogCaptureHandler, log_capture_handler)

        # create a logger for stdout capture
        stdout_logger = getLogger('test_stdout_types', propagate=False)
        stdout_logger.handlers.clear()
        stdout_logger.addHandler(log_capture_handler)
        stdout_logger.setLevel(logging.INFO)

        # save the original stdout
        original_stdout = sys.stdout

        try:
            # when we replace stdout with an Unbuffered wrapper
            sys.stdout = Unbuffered(sys.stdout, logger=stdout_logger, level=logging.INFO)

            # and we print different data types
            print(42)  # integer
            print(3.14159)  # float
            print(True)  # boolean
            print(['list', 'with', 'items'])  # list
            print({'key': 'value', 'number': 123})  # dictionary

            # then all should be captured as strings
            assert len(handler.messages) == 5
            assert '42' in handler.messages[0]
            assert '3.14159' in handler.messages[1]
            assert 'True' in handler.messages[2]
            assert 'list' in handler.messages[3] and 'with' in handler.messages[3]
            assert 'key' in handler.messages[4] and 'value' in handler.messages[4]

        finally:
            # restore original stdout
            sys.stdout = original_stdout
