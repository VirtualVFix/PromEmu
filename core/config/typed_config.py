# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/10/2025 14:45'

import os
import json
import logging
from typing import Any, Dict, Optional, Type, List, get_origin

from .exceptions import ConfigError, ConfigTypeError, ConfigValueError

# supported types for configuration variables
SUPPORTED_ENV_TYPES: tuple[type, ...] = (int, float, str, bool, list, dict)


class TypedConfig:
    '''
    Typed configuration class for defining and managing application settings.
    This class allows you to define configuration variables with type annotations,
    set default values, and retrieve them from environment variables.

    Note:
        Call super before get any class attributes when inheriting from TypedConfig.

    Usage:
        .. code-block:: python

            from max.core import TypedConfig


            class MyConfig(TypedConfig):
                some_static_variable: str
                other_static_variable = 'default_value'


            config = MyConfig()

            # define typed configuration variables
            config.define('database_url', str)
            config.define('max_connections', int, default=10)

            # set values directly
            config.database_url = 'postgresql://user:pass@localhost/mydb'
            # or using set method
            config.set('database_url', 'postgresql://user:pass@localhost/mydb')

            # or use environment variables (DATABASE_URL)
            # access values (raises exception if not set)
            db_url = config.database_url
            # or using get method
            db_url = config.get('database_url')
            some_static_variable = config.some_static_variable
    '''

    def __init__(self) -> None:
        self._log = logging.getLogger(self.__class__.__name__)
        self._init: Dict[str, Any] = {}
        self._cache: Dict[str, Any] = {}
        self._types: Dict[str, Type[Any]] = {}
        self._env_prefix = getattr(self.__class__, '_env_prefix', '')

        # gather annotations from all base classes
        all_annotations: Dict[str, Any] = {}
        for cls in reversed(self.__class__.__mro__):
            if hasattr(cls, '__annotations__'):
                all_annotations.update(cls.__annotations__)

        # gather class attributes from all base classes
        all_class_attrs: Dict[str, Any] = {}
        for cls in reversed(self.__class__.__mro__):
            for name, value in cls.__dict__.items():
                if not name.startswith('_') and name and not callable(value):
                    all_class_attrs[name] = value

        # auto define all static variables with annotations
        for name, value in all_class_attrs.items():
            type_annotation = all_annotations[name] if name in all_annotations else type(value)
            self.define(name=name, type_annotation=type_annotation, default=value)

    def __get_base_type(self, type_annotation: Any) -> Optional[Any]:
        '''
        Get the base type for a generic type annotation.

        Args:
            type_annotation: The type annotation to inspect

        Returns:
            The base type if found, otherwise None
        '''
        origin_type = get_origin(type_annotation)
        # handle generic types (like dict[int, str] or list[str])
        if origin_type is not None:
            if origin_type is dict:
                return dict
            elif origin_type is list:
                return list
            else:
                return origin_type
        return type_annotation

    def define(self, name: str, type_annotation: Any, default: Optional[Any] = None) -> None:
        '''
        Define a configuration variable with type annotation.

        Args:
            name: Name of the configuration variable
            type_annotation: Type of the configuration variable
            default: Optional default value

        Raises:
            ConfigTypeError: If the default value doesn't match the type annotation
            ConfigError: If the name starts with underscore
        '''
        if name.startswith('_'):
            raise ConfigError(f'Configuration variable names cannot start with underscore: {name}')

        # handle generic types (like dict[int, str] or list[str])
        base_type = self.__get_base_type(type_annotation)
        if not isinstance(base_type, type):
            base_type = type(type_annotation)
        if not isinstance(base_type, type):
            raise ConfigTypeError(f'Type annotation for <{name}> must be a type, got {type(base_type).__name__}')
        if base_type in (list, dict) and default is not None and not isinstance(default, (list, dict)):
            raise ConfigTypeError(f'Default value for <{name}> must be a list or dict, got {type(default).__name__}')

        # store original type
        self._types[name] = type_annotation

        # set default
        if default is not None:
            if base_type is not None:
                if not isinstance(default, base_type):
                    raise ConfigTypeError(f'Default value for <{name}> must be of type {base_type.__name__}')
            else:
                if not isinstance(default, type_annotation):
                    raise ConfigTypeError(f'Default value for <{name}> must be of type {type_annotation}')

            # set default value
            self._init[name] = default

    def __getattribute__(self, name: str) -> Any:
        '''
        Get attribute value from config. If attribute wasn't set directly,
        try to get it from environment variable with the same name in uppercase.
        Values are cached after first access.

        Args:
            name: Name of the configuration variable

        Returns:
            Value of the configuration variable

        Raises:
            ConfigValueError: If the variable is not defined or initialized
            ConfigTypeError: If the value from doesn't match the type annotation
        '''
        if name.startswith('_') or callable(getattr(self.__class__, name, None)):
            return super().__getattribute__(name)

        if name not in self._types:
            raise ConfigValueError(f'Configuration variable <{name}> is not defined. Use define("{name}", type) first.')

        # check cache
        if name in self._cache:
            return self._cache[name]

        # check type is supported for environment
        base_type = self.__get_base_type(self._types[name])
        type_name = getattr(base_type, '__name__', str(base_type))
        if base_type is None or base_type not in SUPPORTED_ENV_TYPES:
            # use init value for unsupported types in environment
            if name in self._init:
                init_value = self._init[name]
                self._cache[name] = init_value
                return init_value
            raise ConfigValueError(
                f'Configuration variable <{name}/{type_name}> is not initialized! '
                f'Unsupported type for environment variable: ({type_name}); Supported types: {SUPPORTED_ENV_TYPES}'
            )

        # check variable in environment
        env_var_name = name.upper()
        if self._env_prefix:
            env_var_name = f'{self._env_prefix.rstrip("_").upper()}_{env_var_name}'
        env_value = os.environ.get(env_var_name, None)
        if env_value is None:
            if name in self._init:
                init_value = self._init[name]
                self._cache[name] = init_value
                return init_value
            else:
                raise ConfigValueError(
                    f'Configuration variable <{name}> is not initialized and no environment '
                    f'variable <{env_var_name}> found'
                )

        # convert type
        try:
            base_type = self.__get_base_type(self._types[name])
            if isinstance(base_type, type) and issubclass(base_type, bool):
                # handle bool values from string
                if isinstance(env_value, str):
                    if env_value.lower() in ('true', 'yes', '1', 'y'):
                        typed_value = True
                    elif env_value.lower() in ('false', 'no', '0', 'n'):
                        typed_value = False
                    else:
                        raise ValueError(f'Cannot convert <{env_value}> to <{type_name}>')
                else:
                    typed_value = bool(env_value)
            elif isinstance(base_type, type) and (base_type in (list, dict) or issubclass(base_type, (list, dict))):
                # JSON structures
                if isinstance(env_value, (dict, list)):
                    typed_value = env_value
                else:
                    try:
                        typed_value = json.loads(env_value)
                        if not isinstance(typed_value, base_type):
                            raise ValueError(f'JSON value is not a {base_type.__name__}')
                    except json.JSONDecodeError as e:
                        raise ValueError(f'Invalid JSON: {str(e)}')
            else:
                # use the base type for conversion
                if isinstance(base_type, type):
                    typed_value = base_type(env_value)
                else:
                    type_annotation = self._types[name]
                    typed_value = type_annotation(env_value)

            # cache value
            self._cache[name] = typed_value
            self._log.debug(f'Variable <{name}/{type_name}> loaded from environment: {env_var_name}={typed_value}')
            return typed_value
        except ValueError as exc:
            self._log.error(f'Type conversion error for <{name}>: {str(exc)}')
            type_name = getattr(self._types[name], '__name__', str(self._types[name]))
            raise ConfigTypeError(f'Cannot convert variable <{env_var_name}={env_value}> to {type_name}') from exc

    def __setattr__(self, name: str, value: Any) -> None:
        '''
        Set attribute value to config and cache it.

        Args:
            name: Name of the configuration variable
            value: Value to set

        Raises:
            ConfigValueError: If the variable is not defined
            ConfigTypeError: If the value doesn't match the type annotation
        '''
        if name.startswith('_'):
            super().__setattr__(name, value)
            return

        # check if the name is a method of the class
        if callable(getattr(self.__class__, name, None)):
            super().__setattr__(name, value)
            return

        # check types
        if name not in self._types:
            raise ConfigValueError(f'Configuration variable <{name}> is not defined. Use define("{name}", type) first.')
        base_type = self.__get_base_type(self._types[name])
        type_name = getattr(base_type, '__name__', str(base_type))

        if base_type is not None and not isinstance(value, base_type):
            raise ConfigTypeError(f'Value for <{name}> must be of type {type_name}, got {type(value).__name__}')

        # cache the value
        self._cache[name] = value

    def __dir__(self) -> List[str]:
        '''Return list of attributes for autocomplete.'''
        base_attrs = super().__dir__()
        config_attrs = list(self._types.keys())
        return list(set(base_attrs).union(config_attrs))

    def get(self, name: str) -> Any:
        '''
        Get a configuration variable value.
        This is an alternative to accessing the attribute directly.

        Args:
            name: Name of the configuration variable

        Returns:
            Value of the configuration variable

        Raises:
            ConfigValueError: If the variable is not defined or initialized
        '''
        if name not in self._types:
            raise ConfigValueError(f'Configuration variable <{name}> is not defined. Use define("{name}", type) first.')

        return self.__getattribute__(name)

    def set(self, name: str, value: Any) -> None:
        '''
        Set a configuration variable value.
        This is an alternative to setting the attribute directly.

        Args:
            name: Name of the configuration variable
            value: Value to set

        Raises:
            ConfigValueError: If the variable is not defined
            ConfigTypeError: If the value doesn't match the type annotation
        '''
        if name not in self._types:
            raise ConfigValueError(f'Configuration variable <{name}> is not defined. Use define("{name}", type) first.')

        # check type
        base_type = self.__get_base_type(self._types[name])
        type_name = getattr(base_type, '__name__', str(base_type))

        if base_type is not None and not isinstance(value, base_type):
            raise ConfigTypeError(f'Value for <{name}> must be of type {type_name}, got {type(value).__name__}')

        # cache the value
        self._cache[name] = value
