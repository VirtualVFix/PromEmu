# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/19/2025 12:37'

'''
Tests for the Unbuffered class from the logger module.
'''

import io
import logging
import pytest

import allure
from core.logger.unbuffered import Unbuffered


@allure.feature('Logger')
@allure.story('Unbuffered')
class TestUnbuffered:
    '''Tests for the Unbuffered class'''

    @allure.title('Test Unbuffered writes to stream')
    def test_unbuffered_writes_to_stream(self) -> None:
        '''Test that Unbuffered writes to the wrapped stream'''
        # given a stream and a logger
        stream = io.StringIO()
        logger = logging.getLogger('test_unbuffered')
        logger.handlers.clear()
        logger.setLevel(logging.INFO)

        # and an Unbuffered wrapper
        unbuffered = Unbuffered(stream, logger)

        # when we write to the unbuffered stream
        test_message = 'Test message for unbuffered'
        unbuffered.write(test_message)

        # then it should write to the wrapped stream
        assert stream.getvalue() == test_message

    @allure.title('Test Unbuffered logs to logger')
    def test_unbuffered_logs_to_logger(self) -> None:
        '''Test that Unbuffered logs to the provided logger'''
        # given a stream and a logger with a custom handler
        stream = io.StringIO()
        logger = logging.getLogger('test_unbuffered_log')
        logger.handlers.clear()
        logger.setLevel(logging.INFO)

        log_messages = []

        class TestHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                log_messages.append(record.getMessage())

        logger.addHandler(TestHandler())

        # and an Unbuffered wrapper
        unbuffered = Unbuffered(stream, logger)

        # when we write to the unbuffered stream
        test_message = 'Test message for unbuffered logger'
        unbuffered.write(test_message)

        # then it should log to the logger
        assert test_message in log_messages

    @allure.title('Test Unbuffered with different log levels')
    @pytest.mark.parametrize('level', [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL])
    def test_unbuffered_with_different_levels(self, level: int) -> None:
        '''Test that Unbuffered logs at the specified level'''
        # given a stream and a logger
        stream = io.StringIO()
        logger = logging.getLogger(f'test_unbuffered_level_{level}')
        logger.handlers.clear()
        logger.setLevel(logging.DEBUG)  # Set to lowest level to capture all

        # and a record of the log level used
        logged_level = None

        class LevelCheckHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                nonlocal logged_level
                logged_level = record.levelno

        logger.addHandler(LevelCheckHandler())

        # and an Unbuffered wrapper with a specific level
        unbuffered = Unbuffered(stream, logger, level=level)

        # when we write to the unbuffered stream
        unbuffered.write('Test message')

        # then it should log at the specified level
        assert logged_level == level

    @allure.title('Test Unbuffered attribute delegation')
    def test_unbuffered_attribute_delegation(self) -> None:
        '''Test that Unbuffered delegates unknown attributes to the wrapped stream'''
        # given a stream with a custom attribute and a logger
        stream = io.StringIO()
        stream.custom_attribute = 'test_value'  # type: ignore
        logger = logging.getLogger('test_unbuffered_delegation')

        # and an Unbuffered wrapper
        unbuffered = Unbuffered(stream, logger)

        # when we access an attribute on the unbuffered stream
        # then it should delegate to the wrapped stream
        assert unbuffered.custom_attribute == 'test_value'

    @allure.title('Test Unbuffered skips logging newline')
    def test_unbuffered_skips_logging_newline(self) -> None:
        '''Test that Unbuffered doesn't log newline characters'''
        # given a stream and a logger
        stream = io.StringIO()
        logger = logging.getLogger('test_unbuffered_newline')
        logger.handlers.clear()

        log_messages = []

        class TestHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                log_messages.append(record.getMessage())

        logger.addHandler(TestHandler())

        # and an Unbuffered wrapper
        unbuffered = Unbuffered(stream, logger)

        # when we write a newline to the unbuffered stream
        unbuffered.write('\n')

        # then it should not log anything
        assert not log_messages
