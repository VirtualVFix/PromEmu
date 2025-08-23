# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/19/2025 12:35'

'''
Negative tests for get_logger module.
'''

import logging

import allure
import pytest

from core.logger.get_logger import getLogger


@allure.feature('Core Logger')
@allure.story('GetLogger Error Handling')
class TestGetLoggerNegative:
    '''Error cases in the getLogger function'''

    @allure.title('Test getLogger raises ValueError with propagate=False and file=None')
    def test_get_logger_propagate_false_no_file(self) -> None:
        '''Verify ValueError is raised when propagate=False without file'''
        with pytest.raises(ValueError) as excinfo:
            getLogger('test_logger', file=None, propagate=False)

        assert 'You must set file name if propagate is False!' in str(excinfo.value)

    @allure.title('Test getLogger with invalid file path')
    def test_get_logger_invalid_file_path(self, mock_log_config: None) -> None:
        '''Check handling of invalid log directory paths'''
        # the mock_log_config fixture should provide a safe temp directory
        # this test verifies that the logger can be created even when
        # working with a controlled test environment

        test_log_file = 'test_invalid_path.log'

        # should create logger in the mocked temp directory
        logger = getLogger('test_logger', file=test_log_file)

        assert isinstance(logger, logging.Logger)
        assert len(logger.handlers) > 0

    @allure.title('Test getLogger with invalid level')
    def test_get_logger_with_invalid_level_type(self) -> None:
        '''Verify ValueError is raised with invalid logging level'''
        with pytest.raises(ValueError) as excinfo:
            getLogger('test_logger', level='NOT_A_LEVEL')  # type: ignore

        assert 'Unknown level' in str(excinfo.value)

    @allure.title('Test getLogger with multiple file handlers for same file')
    def test_get_logger_multiple_handlers_same_file(self, mock_log_config: None) -> None:
        '''Check no duplicate handlers are added for the same file'''
        # create first logger
        logger = getLogger('test_logger', file='same_file.log')
        initial_handlers_count = len(logger.handlers)

        # get another logger with same name and file
        logger2 = getLogger('test_logger', file='same_file.log')

        # no new handlers should be added
        assert len(logger2.handlers) == initial_handlers_count
        assert logger.name == logger2.name

    @allure.title('Test getLogger with very long name')
    def test_get_logger_very_long_name(self) -> None:
        '''Verify handling of very long logger names'''
        very_long_name = 'a' * 1000
        logger = getLogger(very_long_name)

        assert logger.name == very_long_name
        logger.info('Test message with very long logger name')
