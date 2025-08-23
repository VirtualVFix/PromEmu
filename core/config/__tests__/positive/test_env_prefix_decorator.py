# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/08/2025 00:00'

import os
from typing import Any

import allure
import pytest

from core.config import TypedConfig, EnvVariablePrefix


@allure.feature('Core Config')
@allure.story('Environment Variable Prefix')
class TestEnvVariablePrefixPositive:
    '''Positive tests for EnvVariablePrefix decorator.'''

    @allure.title('Test env prefix decorator with simple prefix')
    def test_env_prefix_with_simple_prefix(self) -> None:
        '''Test that environment variables are correctly prefixed.'''

        @EnvVariablePrefix('TEST_')
        class TestConfig(TypedConfig):
            database_url: str = 'default'
            port: int = 8080

        config = TestConfig()

        # set environment variable with prefix
        os.environ['TEST_DATABASE_URL'] = 'postgresql://test'
        os.environ['TEST_PORT'] = '5432'

        try:
            assert config.database_url == 'postgresql://test'
            assert config.port == 5432
        finally:
            # cleanup
            os.environ.pop('TEST_DATABASE_URL', None)
            os.environ.pop('TEST_PORT', None)

    @allure.title('Test env prefix decorator with trailing underscore')
    def test_env_prefix_with_trailing_underscore(self) -> None:
        '''Test that trailing underscore in prefix is handled correctly.'''

        @EnvVariablePrefix('APP_')
        class TestConfig(TypedConfig):
            debug_mode: bool = False

        config = TestConfig()

        # set environment variable with prefix
        os.environ['APP_DEBUG_MODE'] = 'true'

        try:
            assert config.debug_mode is True
        finally:
            # cleanup
            os.environ.pop('APP_DEBUG_MODE', None)

    @allure.title('Test env prefix decorator with empty prefix')
    def test_env_prefix_with_empty_prefix(self) -> None:
        '''Test that empty prefix works like normal TypedConfig.'''

        @EnvVariablePrefix('')
        class TestConfig(TypedConfig):
            api_key: str = 'default_key'

        config = TestConfig()

        # set environment variable without prefix
        os.environ['API_KEY'] = 'secret_key'

        try:
            assert config.api_key == 'secret_key'
        finally:
            # cleanup
            os.environ.pop('API_KEY', None)

    @allure.title('Test env prefix decorator with no prefix parameter')
    def test_env_prefix_with_no_prefix_parameter(self) -> None:
        '''Test that decorator without prefix parameter works correctly.'''

        @EnvVariablePrefix()
        class TestConfig(TypedConfig):
            timeout: int = 30

        config = TestConfig()

        # set environment variable without prefix
        os.environ['TIMEOUT'] = '60'

        try:
            assert config.timeout == 60
        finally:
            # cleanup
            os.environ.pop('TIMEOUT', None)

    @allure.title('Test env prefix decorator with complex data types')
    @pytest.mark.parametrize(
        'prefix, var_name, value, expected',
        [
            ('CONFIG_', 'CONFIG_ITEMS', '["item1", "item2"]', ['item1', 'item2']),
            ('APP_', 'APP_SETTINGS', '{"key": "value"}', {'key': 'value'}),
            ('TEST_', 'TEST_ENABLED', 'false', False),
        ],
    )
    def test_env_prefix_with_complex_types(self, prefix: str, var_name: str, value: str, expected: Any) -> None:
        '''Test that complex data types work with prefix.'''

        @EnvVariablePrefix(prefix)
        class TestConfig(TypedConfig):
            items: list = []
            settings: dict = {}
            enabled: bool = True

        config = TestConfig()

        # set environment variable
        os.environ[var_name] = value

        try:
            if 'ITEMS' in var_name:
                assert config.items == expected
            elif 'SETTINGS' in var_name:
                assert config.settings == expected
            elif 'ENABLED' in var_name:
                assert config.enabled == expected
        finally:
            # cleanup
            os.environ.pop(var_name, None)

    @allure.title('Test env prefix decorator fallback to default values')
    def test_env_prefix_fallback_to_defaults(self) -> None:
        '''Test that default values are used when env vars are not set.'''

        @EnvVariablePrefix('MYAPP_')
        class TestConfig(TypedConfig):
            host: str = 'localhost'
            port: int = 3000
            debug: bool = False

        config = TestConfig()

        # ensure no env vars are set
        for var in ['MYAPP_HOST', 'MYAPP_PORT', 'MYAPP_DEBUG']:
            os.environ.pop(var, None)

        assert config.host == 'localhost'
        assert config.port == 3000
        assert config.debug is False
