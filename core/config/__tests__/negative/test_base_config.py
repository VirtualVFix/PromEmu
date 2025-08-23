# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

'''Tests for the TypedConfig class - negative cases.'''

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/10/2025 14:45'

import os
from typing import Type, TypeVar

import allure
import pytest

from core.config.exceptions import ConfigError, ConfigTypeError, ConfigValueError
from core.config.typed_config import TypedConfig

# type variables for generic type hints
T = TypeVar('T')


@allure.feature('Core Config')
@allure.story('Base Configuration Error Handling')
class TestBaseConfigErrors:
    '''Test error cases for the TypedConfig class.'''

    @allure.title('Test error on define with invalid default value')
    def test_error_on_define_with_invalid_default_value(self, config: TypedConfig) -> None:
        '''Test that defining a variable with an invalid default value raises ConfigTypeError.'''
        with pytest.raises(ConfigTypeError) as excinfo:
            config.define('test_var', int, default='not_an_int')

        assert 'Default value for <test_var> must be of type int' in str(excinfo.value)

    @allure.title('Test error on define with underscore name')
    def test_error_on_define_with_underscore_name(self, config: TypedConfig) -> None:
        '''Test that defining a variable with name starting with underscore raises ConfigError.'''
        with pytest.raises(ConfigError) as excinfo:
            config.define('_test_var', str)

        assert 'Configuration variable names cannot start with underscore' in str(excinfo.value)

    @allure.title('Test error on get undefined variable')
    def test_error_on_get_undefined_variable(self, config: TypedConfig) -> None:
        '''Test that getting an undefined variable raises ConfigValueError.'''
        with pytest.raises(ConfigValueError) as excinfo:
            _ = config.undefined_var

        assert 'Configuration variable <undefined_var> is not defined' in str(excinfo.value)

    @allure.title('Test error on set undefined variable')
    def test_error_on_set_undefined_variable(self, config: TypedConfig) -> None:
        '''Test that setting an undefined variable raises ConfigValueError.'''
        with pytest.raises(ConfigValueError) as excinfo:
            config.undefined_var = 'value'

        assert 'Configuration variable' in str(excinfo.value)
        assert 'is not defined' in str(excinfo.value)

    @allure.title('Test error on set with wrong type')
    def test_error_on_set_with_wrong_type(self, config: TypedConfig) -> None:
        '''Test that setting a variable with wrong type raises ConfigTypeError.'''
        config.define('test_var', int)

        with pytest.raises(ConfigTypeError) as excinfo:
            config.test_var = 'not_an_int'

        assert 'Value for <test_var> must be of type int' in str(excinfo.value)

    @allure.title('Test error on get missing environment variable')
    def test_error_on_get_missing_environment_variable(self, config: TypedConfig, env_backup: None) -> None:
        '''Test that getting a missing environment variable raises ConfigValueError.'''
        config.define('test_var', str)

        # ensure the environment variable doesn't exist
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']

        with pytest.raises(ConfigValueError) as excinfo:
            _ = config.test_var

        assert 'Configuration variable <test_var> is not initialized' in str(excinfo.value)
        assert 'no environment variable <TEST_VAR>' in str(excinfo.value)

    @allure.title('Test error on environment value with wrong type')
    @pytest.mark.parametrize(
        'name, type_annotation, env_value, expected_error',
        [
            ('int_var', int, 'not_an_int', 'Cannot convert variable <INT_VAR=not_an_int> to int'),
            ('float_var', float, 'not_a_float', 'Cannot convert variable <FLOAT_VAR=not_a_float> to float'),
            ('bool_var', bool, 'not_a_bool', 'Cannot convert variable <BOOL_VAR=not_a_bool> to bool'),
            ('list_var', list, 'not_a_list', 'Cannot convert variable <LIST_VAR=not_a_list> to list'),
            ('dict_var', dict, 'not_a_dict', 'Cannot convert variable <DICT_VAR=not_a_dict> to dict'),
        ],
    )
    def test_error_on_environment_value_with_wrong_type(
        self,
        config: TypedConfig,
        env_backup: None,
        name: str,
        type_annotation: Type[T],
        env_value: str,
        expected_error: str,
    ) -> None:
        '''Test that getting an environment variable with wrong type raises ConfigTypeError.'''
        config.define(name, type_annotation)
        os.environ[name.upper()] = env_value

        with pytest.raises(ConfigTypeError) as excinfo:
            _ = getattr(config, name)

        error_message = str(excinfo.value)
        assert expected_error in error_message, f"Expected '{expected_error}' in '{error_message}'"
