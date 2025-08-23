# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

'''Tests for TypedConfig get/set methods.'''

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/20/2025 14:30'

import os
from typing import Type, TypeVar, Any

import allure
import pytest

from core.config.typed_config import TypedConfig

# type variables for generic type hints
T = TypeVar('T')


@allure.feature('Core Config')
@allure.story('Get Set Methods')
class TestGetSetMethods:
    '''
    Test get and set methods of TypedConfig.
    '''

    @allure.title('Test get method returns correct value')
    @pytest.mark.parametrize(
        'name,value,type_annotation',
        [
            ('str_var', 'str value', str),
            ('int_var', 42, int),
            ('float_var', 3.14, float),
            ('bool_var', True, bool),
            ('list_var', [1, 2, 3], list),
            ('dict_var', {'a': 1, 'b': 2}, dict),
        ],
    )
    def test_get_method_returns_defined_variables(
        self, config: TypedConfig, name: str, value: Any, type_annotation: Type[Any]
    ) -> None:
        '''
        Test that get() returns values for defined variables.
        '''
        # define and set the variable
        config.define(name, type_annotation)
        setattr(config, name, value)

        # test get method
        retrieved_value = config.get(name)
        assert retrieved_value == value
        assert isinstance(retrieved_value, type_annotation)

    @allure.title('Test get method with type conversion')
    def test_get_method_reads_from_environment(self, config: TypedConfig, env_backup: None) -> None:
        '''
        Test that get() reads values from environment variables.
        '''
        config.define('env_var', str)
        os.environ['ENV_VAR'] = 'environment value'

        # test get method reads from environment
        assert config.get('env_var') == 'environment value'

    @allure.title('Test set method updates value correctly')
    @pytest.mark.parametrize(
        'name, type_annotation, initial_value, new_value',
        [
            ('str_var', str, 'initial', 'updated'),
            ('int_var', int, 10, 20),
            ('float_var', float, 1.5, 2.5),
            ('bool_var', bool, False, True),
            ('list_var', list, [1, 2], [3, 4, 5]),
            ('dict_var', dict, {'a': 1}, {'b': 2, 'c': 3}),
        ],
    )
    def test_set_method_updates_variables(
        self, config: TypedConfig, name: str, type_annotation: Type[T], initial_value: T, new_value: T
    ) -> None:
        '''
        Test that set() correctly updates values.
        '''
        # define and set initial value
        config.define(name, type_annotation)
        setattr(config, name, initial_value)
        assert getattr(config, name) == initial_value

        # update using set method
        config.set(name, new_value)

        # verify update worked
        assert getattr(config, name) == new_value

    @allure.title('Test set method with type validation')
    def test_set_method_caches_values(self, config: TypedConfig, env_backup: None) -> None:
        '''
        Test that set() caches values correctly.
        '''
        # define variable
        config.define('test_var', str)

        # set environment variable
        os.environ['TEST_VAR'] = 'env_value'

        # first access should get env value
        assert config.get('test_var') == 'env_value'

        # set new value with set method
        config.set('test_var', 'new_value')

        # next access should get cached value, not env value
        assert config.get('test_var') == 'new_value'

    @allure.story('Error Handling')
    @allure.title('Get method error on undefined variable')
    def test_get_error_on_undefined_variable(self, config: TypedConfig) -> None:
        '''
        Test that get() raises error for undefined variables.
        '''
        from core.config.exceptions import ConfigValueError

        with pytest.raises(ConfigValueError) as excinfo:
            config.get('undefined_var')

        assert 'Configuration variable <undefined_var> is not defined' in str(excinfo.value)

    @allure.story('Error Handling')
    @allure.title('Set method error on undefined variable')
    def test_set_error_on_undefined_variable(self, config: TypedConfig) -> None:
        '''
        Test that set() raises error for undefined variables.
        '''
        from core.config.exceptions import ConfigValueError

        with pytest.raises(ConfigValueError) as excinfo:
            config.set('undefined_var', 'value')

        assert 'Configuration variable <undefined_var> is not defined' in str(excinfo.value)

    @allure.story('Error Handling')
    @allure.title('Set method error on wrong type')
    def test_set_error_on_wrong_type(self, config: TypedConfig) -> None:
        '''
        Test that set() raises error when setting wrong type.
        '''
        from core.config.exceptions import ConfigTypeError

        config.define('int_var', int)

        with pytest.raises(ConfigTypeError) as excinfo:
            config.set('int_var', 'not_an_int')

        assert 'Value for <int_var> must be of type int' in str(excinfo.value)

    @allure.story('Method Equivalence')
    @allure.title('Get method is equivalent to attribute access')
    def test_get_method_equivalent_to_attribute_access(self, config: TypedConfig) -> None:
        '''
        Test that get() is equivalent to attribute access.
        '''
        config.define('test_var', str, default='test_value')

        assert config.get('test_var') == config.test_var

    @allure.story('Method Equivalence')
    @allure.title('Set method is equivalent to attribute assignment')
    def test_set_method_equivalent_to_attribute_assignment(self, config: TypedConfig) -> None:
        '''
        Test that set() is equivalent to attribute assignment.
        '''
        config.define('test_var', str)

        # set with set method
        config.set('test_var', 'method_value')
        assert config.test_var == 'method_value'

        # set with attribute assignment
        config.test_var = 'attribute_value'
        assert config.get('test_var') == 'attribute_value'
