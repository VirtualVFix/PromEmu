# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/19/2025 12:36'

'''
Negative tests for log_config module.
'''

import allure
import pytest
import logging

from core.logger.log_config import LoggingConfiguration


@allure.feature('Logger')
@allure.story('LoggingConfiguration')
class TestLoggingConfigurationNegative:
    '''Tests for error cases in the LoggingConfiguration class'''

    @allure.title('Test LoggingConfiguration with nonexistent attributes')
    def test_nonexistent_attribute(self) -> None:
        '''Test that accessing a nonexistent attribute raises ConfigValueError'''
        # when we try to access a nonexistent attribute
        # then it should raise a ConfigValueError
        from core.config.exceptions import ConfigValueError

        with pytest.raises(ConfigValueError) as excinfo:
            LoggingConfiguration().NONEXISTENT_ATTRIBUTE

        # and the error message should indicate the variable is not defined
        assert 'is not defined' in str(excinfo.value)

    @allure.title('Test set_loggers_level with invalid level type')
    def test_set_loggers_level_invalid_type(self) -> None:
        '''Test that set_loggers_level with non-integer level is handled appropriately'''
        # when we call set_loggers_level with a string
        # it should raise a ConfigTypeError due to type checking
        instance = LoggingConfiguration()

        # using a non-integer level should raise a ConfigTypeError
        from core.config.exceptions import ConfigTypeError

        with pytest.raises(ConfigTypeError):
            instance.set_loggers_level('NOT_A_LEVEL')  # type: ignore

    @allure.title('Test LoggingConfiguration with modified properties after init')
    def test_modified_properties_after_init(self) -> None:
        '''Test that modifying properties after initialization raises ConfigTypeError with invalid type'''

        # create a new subclass with a modified property of wrong type
        # this should fail during class definition due to type annotation mismatch
        from core.config.exceptions import ConfigTypeError

        with pytest.raises(ConfigTypeError):

            class ModifiedConfig(LoggingConfiguration):  # type: ignore
                LOG_LEVEL = 'ERROR'  # type: ignore[assignment]

            # when we try to create an instance it should fail
            ModifiedConfig()

    @allure.title('Test LoggingConfiguration without required attributes')
    def test_missing_required_attributes(self) -> None:
        '''Test that a subclass without the LOG_LEVEL attribute will use the parent's value'''

        # create a new subclass without a required attribute
        class MinimalConfig(LoggingConfiguration):
            pass

        # when we create an instance and access the attribute
        instance = MinimalConfig()

        # then it should have the parent class's default value (logging.INFO = 20)
        assert instance.LOG_LEVEL == logging.INFO
