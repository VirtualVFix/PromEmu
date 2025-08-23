# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/11/2025 18:55'

'''
Tests for the ColorStreamHandler class.
'''

import allure
import logging
import unittest
from unittest.mock import patch, MagicMock

from core.logger.handlers.color_stream_handler import ColorStreamHandler


# Test constants for all mock configuration - completely independent of LogConfig
class TestLogConfig:
    '''Mock configuration for testing - independent of actual LogConfig values'''

    LOG_USE_COLOR_ENABLED = True
    LOG_USE_COLOR_DISABLED = False

    # Test color map - using our own test values
    TEST_COLOR_MAP = {
        logging.DEBUG: '\033[38;5;242m',  # grey
        logging.INFO: '\033[0;37m',  # white
        logging.WARNING: '\033[38;5;190m',  # yellow
        logging.ERROR: '\033[38;5;196m',  # red
        logging.CRITICAL: '\033[38;5;196;1m',  # bold red
    }

    # Test color values
    RESET_COLOR = '\033[0m'
    WHITE_COLOR = '\033[0;37m'
    RED_COLOR = '\033[38;5;196m'
    YELLOW_COLOR = '\033[38;5;190m'


class MockLogConfig:
    '''Mock LogConfig for testing'''

    def __init__(self, use_color: bool = True, color_map: dict | None = None):
        self.LOG_USE_COLOR = use_color
        self.LOG_COLOR_MAP = color_map or TestLogConfig.TEST_COLOR_MAP


class MockELogColor:
    '''Mock ELogColor for testing'''

    class WHITE:
        value = TestLogConfig.WHITE_COLOR

    class RESET:
        value = TestLogConfig.RESET_COLOR


@allure.feature('Logger')
@allure.story('ColorStreamHandler')
class TestColorStreamHandler(unittest.TestCase):
    '''Tests for the ColorStreamHandler class'''

    @allure.title('Test ColorStreamHandler applies colors correctly')
    def test_colorized_output(self) -> None:
        '''Test that ColorStreamHandler applies correct colors to log messages'''
        # Mock the entire module dependencies
        mock_log_config = MockLogConfig(use_color=TestLogConfig.LOG_USE_COLOR_ENABLED)
        mock_elogcolor = MockELogColor()

        with (
            patch('core.logger.handlers.color_stream_handler.LogConfig', mock_log_config),
            patch('core.logger.handlers.color_stream_handler.ELogColor', mock_elogcolor),
        ):
            # given a mock stream to capture output
            mock_stream = MagicMock()
            mock_stream.write = MagicMock()
            mock_stream.flush = MagicMock()

            handler = ColorStreamHandler()
            handler.stream = mock_stream  # set the stream directly
            formatter = logging.Formatter('%(levelname)s: %(message)s')
            handler.setFormatter(formatter)

            # when we emit different level messages
            test_message = 'Test message'

            # DEBUG level
            debug_record = logging.LogRecord(
                name='test', level=logging.DEBUG, pathname='', lineno=0, msg=test_message, args=(), exc_info=None
            )
            handler.emit(debug_record)

            # INFO level
            info_record = logging.LogRecord(
                name='test', level=logging.INFO, pathname='', lineno=0, msg=test_message, args=(), exc_info=None
            )
            handler.emit(info_record)

            # WARNING level
            warning_record = logging.LogRecord(
                name='test', level=logging.WARNING, pathname='', lineno=0, msg=test_message, args=(), exc_info=None
            )
            handler.emit(warning_record)

            # ERROR level
            error_record = logging.LogRecord(
                name='test', level=logging.ERROR, pathname='', lineno=0, msg=test_message, args=(), exc_info=None
            )
            handler.emit(error_record)

            # CRITICAL level
            critical_record = logging.LogRecord(
                name='test', level=logging.CRITICAL, pathname='', lineno=0, msg=test_message, args=(), exc_info=None
            )
            handler.emit(critical_record)

            # then the output should contain color codes
            # verify that write was called 5 times (once for each log level)
            assert mock_stream.write.call_count == 5

            # get all the written messages
            written_messages = [call.args[0] for call in mock_stream.write.call_args_list]
            combined_output = ''.join(written_messages)

            # verify each log level has its corresponding test color
            assert TestLogConfig.TEST_COLOR_MAP[logging.DEBUG] in combined_output  # DEBUG
            assert TestLogConfig.TEST_COLOR_MAP[logging.INFO] in combined_output  # INFO
            assert TestLogConfig.TEST_COLOR_MAP[logging.WARNING] in combined_output  # WARNING
            assert TestLogConfig.TEST_COLOR_MAP[logging.ERROR] in combined_output  # ERROR
            assert TestLogConfig.TEST_COLOR_MAP[logging.CRITICAL] in combined_output  # CRITICAL

            # verify reset codes are present
            reset_count = combined_output.count(TestLogConfig.RESET_COLOR)
            assert reset_count == 5  # One for each message

            # verify the test message appears in all outputs
            assert combined_output.count(test_message) == 5

    @allure.title('Test ColorStreamHandler with colors disabled')
    def test_no_colorization_when_disabled(self) -> None:
        '''Test that ColorStreamHandler doesn't apply colors when LOG_USE_COLOR is False'''
        # Mock configuration with colors disabled
        test_colors = {
            logging.WARNING: TestLogConfig.YELLOW_COLOR  # yellow
        }
        mock_log_config = MockLogConfig(use_color=TestLogConfig.LOG_USE_COLOR_DISABLED, color_map=test_colors)

        with patch('core.logger.handlers.color_stream_handler.LogConfig', mock_log_config):
            # and a mock stream to capture output
            mock_stream = MagicMock()
            mock_stream.write = MagicMock()
            mock_stream.flush = MagicMock()

            handler = ColorStreamHandler()
            handler.stream = mock_stream
            formatter = logging.Formatter('%(levelname)s: %(message)s')
            handler.setFormatter(formatter)

            # when we emit a log message
            test_message = 'Test message without color'
            record = logging.LogRecord(
                name='test', level=logging.WARNING, pathname='', lineno=0, msg=test_message, args=(), exc_info=None
            )
            handler.emit(record)

            # then the output should not contain any color codes
            mock_stream.write.assert_called_once()
            written_message = mock_stream.write.call_args[0][0]
            assert test_colors[logging.WARNING] not in written_message
            assert TestLogConfig.RESET_COLOR not in written_message
            assert test_message in written_message
            assert 'WARNING:' in written_message

    @allure.title('Test ColorStreamHandler color positioning')
    def test_color_positioning(self) -> None:
        '''Test that colors are applied after the first space in the formatted message'''
        # Mock configuration with test colors
        test_colors = {
            logging.ERROR: TestLogConfig.RED_COLOR  # red
        }
        mock_log_config = MockLogConfig(use_color=TestLogConfig.LOG_USE_COLOR_ENABLED, color_map=test_colors)
        mock_elogcolor = MockELogColor()

        with (
            patch('core.logger.handlers.color_stream_handler.LogConfig', mock_log_config),
            patch('core.logger.handlers.color_stream_handler.ELogColor', mock_elogcolor),
        ):
            # and a mock stream to capture output
            mock_stream = MagicMock()
            mock_stream.write = MagicMock()
            mock_stream.flush = MagicMock()

            handler = ColorStreamHandler()
            handler.stream = mock_stream
            formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
            handler.setFormatter(formatter)

            # when we emit a log message
            test_message = 'Test positioning'
            record = logging.LogRecord(
                name='test', level=logging.ERROR, pathname='', lineno=0, msg=test_message, args=(), exc_info=None
            )

            # get the original formatted message to understand positioning
            original_formatted = formatter.format(record)
            original_first_space = original_formatted.find(' ')

            handler.emit(record)

            # then the color should be applied at the first space position
            mock_stream.write.assert_called_once()
            output = mock_stream.write.call_args[0][0]

            # the ColorStreamHandler inserts color exactly at the first space position
            # so "2025-08-11 ERROR: message" becomes "2025-08-11{color} ERROR: message{reset}"
            color_start_index = output.find(test_colors[logging.ERROR])

            # color should appear at exactly the original first space position
            assert color_start_index == original_first_space
            assert TestLogConfig.RESET_COLOR in output
            assert test_message in output

    @allure.title('Test ColorStreamHandler handles unknown log levels')
    def test_unknown_log_level_defaults_to_white(self) -> None:
        '''Test that ColorStreamHandler uses white color for unknown log levels'''
        # mock configuration with some known colors but not the custom level
        test_colors = {
            logging.INFO: TestLogConfig.WHITE_COLOR,  # white
            logging.ERROR: TestLogConfig.RED_COLOR,  # red (for known levels)
        }
        mock_log_config = MockLogConfig(use_color=TestLogConfig.LOG_USE_COLOR_ENABLED, color_map=test_colors)
        mock_elogcolor = MockELogColor()

        with (
            patch('core.logger.handlers.color_stream_handler.LogConfig', mock_log_config),
            patch('core.logger.handlers.color_stream_handler.ELogColor', mock_elogcolor),
        ):
            # and a mock stream to capture output
            mock_stream = MagicMock()
            mock_stream.write = MagicMock()
            mock_stream.flush = MagicMock()

            handler = ColorStreamHandler()
            handler.stream = mock_stream
            formatter = logging.Formatter('%(levelname)s: %(message)s')
            handler.setFormatter(formatter)

            # when we emit a message with an unknown/custom log level
            custom_level = 25  # between INFO (20) and WARNING (30)
            test_message = 'Custom level message'
            record = logging.LogRecord(
                name='test', level=custom_level, pathname='', lineno=0, msg=test_message, args=(), exc_info=None
            )
            handler.emit(record)

            # then it should default to white color (fallback behavior)
            mock_stream.write.assert_called_once()
            output = mock_stream.write.call_args[0][0]

            # the color is applied AFTER the first space
            # so we expect: "Level\x1b[0;37m 25: Custom level message\x1b[0m\n"
            assert TestLogConfig.WHITE_COLOR in output
            assert TestLogConfig.RESET_COLOR in output
            assert test_message in output

    @allure.title('Test ColorStreamHandler handles exceptions gracefully')
    def test_exception_handling(self) -> None:
        '''Test that ColorStreamHandler handles exceptions gracefully during emit'''

        # given a handler with a broken stream
        class BrokenStream:
            def write(self, data: str) -> None:
                raise IOError('Stream is broken')

            def flush(self) -> None:
                pass

        broken_stream = BrokenStream()
        handler = ColorStreamHandler()
        handler.stream = broken_stream  # set broken stream directly
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)

        # when we emit a message and it raises an exception
        test_message = 'This will fail'
        record = logging.LogRecord(
            name='test', level=logging.INFO, pathname='', lineno=0, msg=test_message, args=(), exc_info=None
        )

        # then the handler should handle the error gracefully (not crash)
        # this tests the exception handling in the emit method
        with patch.object(handler, 'handleError') as mock_handle_error:
            handler.emit(record)
            mock_handle_error.assert_called_once_with(record)

    @allure.title('Test ColorStreamHandler message formatting integrity')
    def test_message_formatting_integrity(self) -> None:
        '''Test that ColorStreamHandler does not corrupt message content during colorization'''
        # mock color configuration
        test_colors = {logging.INFO: TestLogConfig.WHITE_COLOR, logging.ERROR: TestLogConfig.RED_COLOR}
        mock_log_config = MockLogConfig(use_color=TestLogConfig.LOG_USE_COLOR_ENABLED, color_map=test_colors)

        with patch('core.logger.handlers.color_stream_handler.LogConfig', mock_log_config):
            # and a mock stream to capture output
            mock_stream = MagicMock()
            mock_stream.write = MagicMock()
            mock_stream.flush = MagicMock()

            handler = ColorStreamHandler()
            handler.stream = mock_stream
            formatter = logging.Formatter('%(levelname)s: %(message)s')
            handler.setFormatter(formatter)

            # when we emit various types of potentially problematic messages
            test_cases = [
                ('Simple message', logging.INFO),
                ('Message with unicode: 你好世界 🌍', logging.ERROR),
                ('Message with special chars: @#$%^&*()[]{}|\\', logging.INFO),
                ('Message with ANSI-like text: \033[31mfake red\033[0m', logging.ERROR),
                ('Multi\nline\nmessage', logging.INFO),
                ('Message with tabs:\t\tindented', logging.ERROR),
            ]

            for message, level in test_cases:
                with self.subTest(message=message):
                    record = logging.LogRecord(
                        name='test', level=level, pathname='', lineno=0, msg=message, args=(), exc_info=None
                    )
                    handler.emit(record)

                    # then the message content should be preserved exactly
                    mock_stream.write.assert_called()
                    output = mock_stream.write.call_args[0][0]

                    # original message should be present in the output
                    assert message in output
                    # color codes should be added without corrupting original content
                    assert test_colors[level] in output
                    assert TestLogConfig.RESET_COLOR in output

                    mock_stream.reset_mock()
