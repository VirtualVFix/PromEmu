# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

'''Tests for TypedConfig environment variable priority.'''

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/20/2025 14:30'

import os
from typing import Type, TypeVar, Any

import allure
import pytest

from core.config.typed_config import TypedConfig

# type variables for generic type hints
T = TypeVar('T')


@allure.epic('Core')
@allure.feature('Core Config')
@allure.story('Environment Variable Priority')
class TestEnvPriority:
    '''Test environment variable priority in TypedConfig.'''

    @allure.title('Test environment variable priority over default')
    @pytest.mark.parametrize(
        'name, type_annotation, default_value, env_value',
        [
            ('str_var', str, 'default', 'environment'),
            ('int_var', int, 10, '20'),
            ('float_var', float, 1.5, '2.5'),
            ('bool_var', bool, False, 'true'),
            ('list_var', list, [1, 2], '[3, 4, 5]'),
            ('dict_var', dict, {'a': 1}, '{"b": 2, "c": 3}'),
        ],
    )
    def test_env_variable_priority_over_default(
        self,
        config: TypedConfig,
        env_backup: None,
        name: str,
        type_annotation: Type[Any],
        default_value: Any,
        env_value: str,
    ) -> None:
        '''Test that environment variable values take precedence over default values.'''
        # define variable with default value
        config.define(name, type_annotation, default=default_value)

        # set environment variable
        os.environ[name.upper()] = env_value

        # access the variable - should get environment value, not default
        value = getattr(config, name)

        # expected value depends on the type
        if type_annotation is int:
            expected = int(env_value)
        elif type_annotation is float:
            expected = float(env_value)  # type: ignore
        elif type_annotation is bool:
            expected = env_value.lower() in ('true', 'yes', '1', 'y')
        elif type_annotation in (list, dict):
            import json

            expected = json.loads(env_value)
        else:
            expected = env_value  # type: ignore

        assert value == expected

    @allure.story('Environment Priority')
    @allure.title('Environment variable has higher priority than direct assignment')
    def test_env_priority_over_direct_assignment(self, config: TypedConfig, env_backup: None) -> None:
        '''Test that environment variable values take precedence over directly assigned values.'''
        # define variable
        config.define('test_var', str)

        # set directly first
        config.test_var = 'direct_value'
        assert config.test_var == 'direct_value'

        # set environment variable
        os.environ['TEST_VAR'] = 'env_value'

        # when accessing again, the cached value should be returned (not the env value)
        assert config.test_var == 'direct_value'

        # create a new config instance to test fresh access
        new_config = TypedConfig()
        new_config.define('test_var', str)

        # this should read from environment
        assert new_config.test_var == 'env_value'

    @allure.story('Environment Priority')
    @allure.title('Environment variables override class default values')
    def test_env_priority_over_class_defaults(self, env_backup: None) -> None:
        '''Test that environment variables override class default values.'''

        # define a class with default values
        class CustomConfig(TypedConfig):
            str_var: str = 'default'
            int_var: int = 42

        # set environment variables
        os.environ['STR_VAR'] = 'env_string'
        os.environ['INT_VAR'] = '84'

        # create instance
        config = CustomConfig()

        # check that environment values are used
        assert config.str_var == 'env_string'
        assert config.int_var == 84
