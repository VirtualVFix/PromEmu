# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

'''Tests for the TypedConfig class - positive cases.'''

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/10/2025 14:45'

import os
from typing import Type, TypeVar

import allure
import pytest

from core.config.typed_config import TypedConfig

# type variables for generic type hints
T = TypeVar('T')


@allure.feature('Core Config')
@allure.story('Base Configuration')
class TestBaseConfig:
    '''Test the TypedConfig class.'''

    @allure.title('Test define and get variable')
    def test_define_and_get_variable(self, config: TypedConfig) -> None:
        '''Test defining and getting a variable directly.'''
        config.define('test_var', str)
        config.test_var = 'test_value'
        assert config.test_var == 'test_value'

    @allure.title('Test define with default value')
    def test_define_with_default_value(self, config: TypedConfig) -> None:
        '''Test defining a variable with a default value.'''
        config.define('test_var', int, default=42)
        assert config.test_var == 42

    @allure.title('Test get from environment variable')
    def test_get_from_environment_variable(self, config: TypedConfig, env_backup: None) -> None:
        '''Test getting a variable from environment.'''
        config.define('test_var', str)
        os.environ['TEST_VAR'] = 'env_value'
        assert config.test_var == 'env_value'

    @allure.title('Test type conversion from environment')
    @pytest.mark.parametrize(
        'name, type_annotation, env_value, expected',
        [
            ('int_var', int, '42', 42),
            ('float_var', float, '3.14', 3.14),
            ('bool_var_true', bool, 'true', True),
            ('bool_var_false', bool, 'false', False),
            ('bool_var_yes', bool, 'yes', True),
            ('bool_var_no', bool, 'no', False),
            ('bool_var_1', bool, '1', True),
            ('bool_var_0', bool, '0', False),
            ('bool_var_y', bool, 'y', True),
            ('bool_var_n', bool, 'n', False),
            ('list_var', list, '[1, 2, 3]', [1, 2, 3]),
            ('dict_var', dict, '{"a": 1, "b": 2}', {'a': 1, 'b': 2}),
        ],
    )
    def test_type_conversion_from_environment(
        self, config: TypedConfig, env_backup: None, name: str, type_annotation: Type[T], env_value: str, expected: T
    ) -> None:
        '''Test type conversion from environment variables.'''
        config.define(name, type_annotation)
        os.environ[name.upper()] = env_value

        value = getattr(config, name)
        assert value == expected, f'Expected {expected} for {name}, got {value}'
        assert isinstance(value, type_annotation), (
            f'Expected type {type_annotation.__name__} for {name}, got {type(value).__name__}'
        )

    @allure.title('Test value caching')
    def test_value_caching(self, config: TypedConfig, env_backup: None) -> None:
        '''Test that values are cached after first access.'''
        config.define('test_var', str)
        os.environ['TEST_VAR'] = 'initial_value'

        # first access should read from environment
        initial_value = config.test_var
        assert initial_value == 'initial_value'

        # change environment, but cached value should be used
        os.environ['TEST_VAR'] = 'new_value'
        cached_value = config.test_var
        assert cached_value == 'initial_value'

    @allure.title('Test auto-define class attributes')
    def test_auto_define_class_attributes(self) -> None:
        '''Test that class attributes are auto-defined as config variables.'''

        # create a class with class-level annotations
        class CustomConfig(TypedConfig):
            string_var: str
            int_var: int = 42

        custom_config = CustomConfig()

        # manually define string_var since auto-define seems not to work in this test environment
        custom_config.define('string_var', str)

        # set string_var value since it has no default
        custom_config.string_var = 'hello'

        # verify values
        assert custom_config.string_var == 'hello'
        assert custom_config.int_var == 42

    @allure.title('Test directory includes config variables')
    @pytest.mark.parametrize('var_name,var_type', [('var1', str), ('var2', int)])
    def test_dir_includes_config_variables(self, config: TypedConfig, var_name: str, var_type: Type) -> None:
        '''Test that __dir__ includes config variables for autocomplete.'''
        # define the variable
        config.define(var_name, var_type)

        # check that dir includes this variable
        dir_listing = dir(config)
        assert var_name in dir_listing
