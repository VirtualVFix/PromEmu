# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/19/2025 12:36'

'''
Tests for integration between getLogger and CustomLogger functionality.
'''

import logging
import pytest
from typing import cast

import allure
from core.logger.get_logger import getLogger
from core.logger.custom_logger import CustomLogger
from ..conftest import LogCaptureHandler


@allure.feature('Logger')
@allure.story('CustomLoggerIntegration')
class TestCustomLoggerIntegration:
    '''Tests for integration between getLogger and CustomLogger functionality'''

    @allure.title('Test getLogger returns CustomLogger instance')
    def test_get_logger_returns_custom_logger(self) -> None:
        '''Test that getLogger returns an instance of CustomLogger'''
        # when we create a logger
        logger = getLogger('test_logger')

        # then it should be an instance of CustomLogger
        assert isinstance(logger, CustomLogger)

    @allure.title('Test blank method works correctly')
    def test_blank_method(self, log_capture_handler: logging.Handler) -> None:
        '''Test that the blank method of CustomLogger works correctly'''
        # given a logger with a custom handler
        logger = getLogger('test_logger')
        logger.handlers.clear()
        logger.addHandler(log_capture_handler)

        # when we call the blank method
        logger.blank()
        logger.info('Test message')
        logger.blank(lines=2)

        # then the handler should have captured the blank lines and the message
        handler = cast(LogCaptureHandler, log_capture_handler)
        assert handler.messages[0] == ''
        assert 'Test message' in handler.messages[1]
        assert handler.messages[2] == ''
        assert handler.messages[3] == ''

    @allure.title('Test custom logging methods')
    @pytest.mark.parametrize(
        'log_method,log_level',
        [
            ('debug', logging.DEBUG),
            ('info', logging.INFO),
            ('warning', logging.WARNING),
            ('error', logging.ERROR),
            ('critical', logging.CRITICAL),
        ],
    )
    def test_custom_logging_methods(
        self, log_capture_handler: logging.Handler, log_method: str, log_level: int
    ) -> None:
        '''Test that the custom logging methods work correctly'''
        # given a logger with a custom handler and appropriate level
        logger = getLogger('test_logger', level=logging.DEBUG)
        logger.handlers.clear()
        logger.addHandler(log_capture_handler)

        # when we call the logging method
        test_message = f'Test {log_method} message'
        getattr(logger, log_method)(test_message)

        # then the handler should have captured the message
        handler = cast(LogCaptureHandler, log_capture_handler)
        assert test_message in handler.messages[0]

    @allure.title('Test logger propagation to additional loggers')
    def test_logger_propagation(self) -> None:
        '''Test that messages propagate to additional loggers'''
        # given two loggers
        logger1 = getLogger('logger1')
        logger2 = getLogger('logger2')

        # and custom handlers for capturing messages
        class TestHandler(logging.Handler):
            def __init__(self) -> None:
                super().__init__()
                self.messages: list[str] = []

            def emit(self, record: logging.LogRecord) -> None:
                self.messages.append(record.getMessage())

        handler1 = TestHandler()
        handler2 = TestHandler()

        logger1.handlers.clear()
        logger2.handlers.clear()
        logger1.addHandler(handler1)
        logger2.addHandler(handler2)

        # when we log a message to logger1 and include logger2
        test_message = 'This message should propagate'
        logger1.info(test_message, logger2)

        # then both handlers should have captured the message
        assert test_message in handler1.messages[0]
        assert test_message in handler2.messages[0]

    @allure.title('Test exception logging')
    def test_exception_logging(self, log_capture_handler: logging.Handler) -> None:
        '''Test that exception logging works correctly'''
        # given a logger with a custom handler
        logger = getLogger('test_logger')
        logger.handlers.clear()
        logger.addHandler(log_capture_handler)

        # when we log an exception
        try:
            raise ValueError('Test exception')
        except ValueError:
            logger.exception('An error occurred')

        # then the handler should have captured the exception message
        handler = cast(LogCaptureHandler, log_capture_handler)
        assert 'An error occurred' in handler.messages[0]
