# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/08/2025 00:00'

import os
import pytest
import allure

from core.config import TypedConfig, EnvVariablePrefix
from core.config.exceptions import ConfigValueError


@allure.feature('Core Config')
@allure.story('Environment Variable Prefix Error Handling')
class TestEnvVariablePrefixNegative:
    '''Negative tests for EnvVariablePrefix decorator.'''

    @allure.title('Test env prefix decorator missing required env variable')
    def test_env_prefix_missing_required_variable(self) -> None:
        '''Test that ConfigValueError is raised when required env variable is missing.'''

        @EnvVariablePrefix('MISSING_')
        class TestConfig(TypedConfig):
            def __init__(self) -> None:
                super().__init__()
                self.define('required_field', str)

        config = TestConfig()

        # ensure env variable is not set
        os.environ.pop('MISSING_REQUIRED_FIELD', None)

        with pytest.raises(ConfigValueError, match='Configuration variable <required_field> is not initialized'):
            _ = config.required_field

    @allure.title('Test env prefix decorator with wrong env variable name')
    def test_env_prefix_wrong_env_variable_name(self) -> None:
        '''Test that default value is used when wrong env variable name is set.'''

        @EnvVariablePrefix('APP_')
        class TestConfig(TypedConfig):
            timeout: int = 30

        config = TestConfig()

        # set wrong env variable name (without prefix)
        os.environ['TIMEOUT'] = '60'
        # correct name would be APP_TIMEOUT
        os.environ.pop('APP_TIMEOUT', None)

        try:
            # should use default value since APP_TIMEOUT is not set
            assert config.timeout == 30
        finally:
            # cleanup
            os.environ.pop('TIMEOUT', None)

    @allure.title('Test env prefix decorator with invalid type conversion')
    def test_env_prefix_invalid_type_conversion(self) -> None:
        '''Test that error is raised when env variable cannot be converted to expected type.'''

        @EnvVariablePrefix('TEST_')
        class TestConfig(TypedConfig):
            port: int = 8080

        config = TestConfig()

        # set invalid value for int type
        os.environ['TEST_PORT'] = 'invalid_number'

        try:
            with pytest.raises(Exception):  # should raise type conversion error
                _ = config.port
        finally:
            # cleanup
            os.environ.pop('TEST_PORT', None)

    @allure.title('Test env prefix decorator with invalid json')
    @allure.title('Test env prefix with invalid prefix type')
    def test_env_prefix_with_invalid_prefix_type(self) -> None:
        '''Test that error is raised when env variable contains invalid JSON.'''

        @EnvVariablePrefix('CONFIG_')
        class TestConfig(TypedConfig):
            settings: dict = {}

        config = TestConfig()

        # set invalid JSON
        os.environ['CONFIG_SETTINGS'] = '{"invalid": json}'

        try:
            with pytest.raises(Exception):  # should raise JSON parsing error
                _ = config.settings
        finally:
            # cleanup
            os.environ.pop('CONFIG_SETTINGS', None)

    @allure.title('Test env prefix decorator with wrong json type')
    def test_env_prefix_wrong_json_type(self) -> None:
        '''Test that error is raised when JSON type doesn\'t match expected type.'''

        @EnvVariablePrefix('APP_')
        class TestConfig(TypedConfig):
            items: list = []

        config = TestConfig()

        # set dict JSON for list field
        os.environ['APP_ITEMS'] = '{"key": "value"}'

        try:
            with pytest.raises(Exception):  # should raise type mismatch error
                _ = config.items
        finally:
            # cleanup
            os.environ.pop('APP_ITEMS', None)

    @allure.title('Test env prefix decorator without TypedConfig inheritance')
    @allure.title('Test env prefix with None prefix')
    def test_env_prefix_with_none_prefix(self) -> None:
        '''Test that decorator works but doesn\'t affect non-TypedConfig classes.'''

        @EnvVariablePrefix('TEST_')
        class RegularClass:
            def __init__(self) -> None:
                self.value = 'default'

        obj = RegularClass()

        # decorator should not affect regular classes
        assert obj.value == 'default'
        assert hasattr(obj.__class__, '_env_prefix')
        assert getattr(obj.__class__, '_env_prefix') == 'TEST_'
