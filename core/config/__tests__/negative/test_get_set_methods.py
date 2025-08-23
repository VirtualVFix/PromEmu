# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

'''Tests for TypedConfig get/set methods - negative cases.'''

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/20/2025 14:30'

import os
from typing import Type, TypeVar, Any

import allure
import pytest

from core.config.exceptions import ConfigTypeError, ConfigValueError
from core.config.typed_config import TypedConfig

# type variables for generic type hints
T = TypeVar('T')


@allure.feature('Core Config')
@allure.story('Get Set Methods Error Handling')
class TestGetSetMethodsErrors:
    '''Test error cases for get and set methods of TypedConfig.'''

    @allure.title('Test get method error on undefined variable')
    def test_get_error_on_undefined_variable(self, config: TypedConfig) -> None:
        '''Test that get() raises ConfigValueError for undefined variables.'''
        with pytest.raises(ConfigValueError) as excinfo:
            config.get('undefined_var')

        assert 'Configuration variable <undefined_var> is not defined' in str(excinfo.value)

    @allure.title('Test set method error on undefined variable')
    def test_set_error_on_undefined_variable(self, config: TypedConfig) -> None:
        '''Test that set() raises ConfigValueError for undefined variables.'''
        with pytest.raises(ConfigValueError) as excinfo:
            config.set('undefined_var', 'value')

        assert 'Configuration variable <undefined_var> is not defined' in str(excinfo.value)

    @allure.title('Test set method error on wrong type')
    @pytest.mark.parametrize(
        'name, type_annotation, invalid_value, expected_error',
        [
            ('int_var', int, 'not_an_int', 'Value for <int_var> must be of type int'),
            ('float_var', float, 'not_a_float', 'Value for <float_var> must be of type float'),
            ('bool_var', bool, 'not_a_bool_obj', 'Value for <bool_var> must be of type bool'),
            ('list_var', list, 'not_a_list', 'Value for <list_var> must be of type list'),
            ('dict_var', dict, 'not_a_dict', 'Value for <dict_var> must be of type dict'),
        ],
    )
    def test_set_error_on_wrong_type(
        self, config: TypedConfig, name: str, type_annotation: Type[Any], invalid_value: Any, expected_error: str
    ) -> None:
        '''Test that set() raises ConfigTypeError when setting value with wrong type.'''
        config.define(name, type_annotation)

        with pytest.raises(ConfigTypeError) as excinfo:
            config.set(name, invalid_value)

        error_message = str(excinfo.value)
        assert expected_error in error_message, f"Expected '{expected_error}' in '{error_message}'"

    @allure.title('Test get method error on missing environment variable')
    def test_get_error_on_missing_environment_variable(self, config: TypedConfig, env_backup: None) -> None:
        '''Test that get() raises ConfigValueError for missing environment variables.'''
        config.define('test_var', str)

        # Ensure the environment variable doesn't exist
        if 'TEST_VAR' in os.environ:
            del os.environ['TEST_VAR']

        with pytest.raises(ConfigValueError) as excinfo:
            config.get('test_var')

        assert 'Configuration variable <test_var> is not initialized' in str(excinfo.value)
        assert 'no environment variable <TEST_VAR>' in str(excinfo.value)
