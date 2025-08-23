# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/19/2025 12:37'

'''
Positive tests for log_config module.
'''

import logging
import pytest

import allure
from core.logger.log_config import LogConfig, LoggingConfiguration, ELogColor


@allure.feature('Logger')
@allure.story('LoggingConfiguration')
class TestLoggingConfiguration:
    '''Tests for the LoggingConfiguration class'''

    @allure.title('Test LoggingConfiguration has expected properties')
    def test_properties(self) -> None:
        '''Test that LoggingConfiguration has expected properties'''
        # the LogConfig singleton should have all required properties
        assert hasattr(LogConfig, 'LOG_LEVEL')
        assert hasattr(LogConfig, 'LOG_FILE_FORMAT')
        assert hasattr(LogConfig, 'LOG_FILE_DATE_FORMAT')
        assert hasattr(LogConfig, 'LOG_CONSOLE_FORMAT')
        assert hasattr(LogConfig, 'LOG_CONSOLE_DATE_FORMAT')
        assert hasattr(LogConfig, 'LOG_FILE')
        assert hasattr(LogConfig, 'LOG_DIR')
        assert hasattr(LogConfig, 'LOG_MAX_BYTES')
        assert hasattr(LogConfig, 'LOG_BACKUP_EXPIRED_TIME_SEC')
        assert hasattr(LogConfig, 'LOG_BACKUP_NAME_FORMAT')
        assert hasattr(LogConfig, 'LOG_USE_COLOR')
        assert hasattr(LogConfig, 'LOG_COLOR_MAP')

    @allure.title('Test LoggingConfiguration set_loggers_level method')
    def test_set_loggers_level(self) -> None:
        '''Test that set_loggers_level changes the level of all loggers'''
        # given some existing loggers with different levels
        logger1 = logging.getLogger('test_logger1')
        logger1.setLevel(logging.DEBUG)

        logger2 = logging.getLogger('test_logger2')
        logger2.setLevel(logging.WARNING)

        # when we set all logger levels
        LogConfig.set_loggers_level(logging.ERROR)

        # then all loggers should have the new level
        assert logger1.level == logging.ERROR
        assert logger2.level == logging.ERROR

        # reset logger levels for other tests
        LogConfig.set_loggers_level(logging.INFO)

    @allure.title('Test LoggingConfiguration handles invalid log level')
    def test_invalid_log_level(self) -> None:
        '''Test that LoggingConfiguration handles invalid log levels appropriately'''

        # create a new subclass with invalid log level type
        # this should fail during class definition due to type annotation mismatch
        from core.config.exceptions import ConfigTypeError

        with pytest.raises(ConfigTypeError):

            class TestConfig(LoggingConfiguration):  # type: ignore
                LOG_LEVEL = 'INVALID_LEVEL'  # type: ignore[assignment]

            # when we try to create a new instance it should fail
            TestConfig()

    @allure.title('Test ELogColor enumeration')
    def test_elog_color_enum(self) -> None:
        '''Test that ELogColor enumeration has expected values'''
        # the ELogColor enum should have values for all log levels
        assert ELogColor.RESET.value == '\033[0m'

    @allure.title('Test log color mapping configured')
    def test_log_color_mapping(self) -> None:
        '''Test that log color mapping has entries for all standard log levels'''
        # the color map should have entries for all standard log levels
        assert logging.DEBUG in LogConfig.LOG_COLOR_MAP
        assert logging.INFO in LogConfig.LOG_COLOR_MAP
        assert logging.WARNING in LogConfig.LOG_COLOR_MAP
        assert logging.ERROR in LogConfig.LOG_COLOR_MAP
        assert logging.CRITICAL in LogConfig.LOG_COLOR_MAP

    @allure.title('Test multiple logger level changes via LogConfig function')
    def test_multiple_logger_level_changes(self) -> None:
        '''Test that LogConfig.set_loggers_level affects multiple existing loggers correctly'''
        # given multiple loggers with different initial levels
        logger_names = ['multi_test_logger_1', 'multi_test_logger_2', 'multi_test_logger_3']
        initial_levels = [logging.DEBUG, logging.INFO, logging.WARNING]
        loggers = []

        # create loggers with different initial levels
        for name, level in zip(logger_names, initial_levels):
            logger = logging.getLogger(name)
            logger.setLevel(level)
            loggers.append(logger)

        # verify initial levels are set correctly
        for logger, expected_level in zip(loggers, initial_levels):
            assert logger.level == expected_level

        # when we change all logger levels to ERROR via LogConfig
        LogConfig.set_loggers_level(logging.ERROR)

        # then all loggers should have the new level
        for logger in loggers:
            assert logger.level == logging.ERROR

        # when we change levels again to CRITICAL
        LogConfig.set_loggers_level(logging.CRITICAL)

        # then all loggers should have the CRITICAL level
        for logger in loggers:
            assert logger.level == logging.CRITICAL

        # verify that the LogConfig instance itself also reflects the change
        assert LogConfig.LOG_LEVEL == logging.CRITICAL

        # verify that root logger level is also updated
        assert logging.root.level == logging.CRITICAL

        # when we use set_loggers_level_by_level_name with valid level
        LogConfig.set_loggers_level_by_level_name('DEBUG')

        # then all loggers should have DEBUG level
        for logger in loggers:
            assert logger.level == logging.DEBUG
        assert LogConfig.LOG_LEVEL == logging.DEBUG

        # reset to INFO for other tests
        LogConfig.set_loggers_level(logging.INFO)
