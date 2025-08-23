# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/08/2025 00:00'

from typing import Type, TypeVar, Callable

T = TypeVar('T')


def EnvVariablePrefix(prefix: str = '') -> Callable[[Type[T]], Type[T]]:
    '''
    Decorator for TypedConfig classes to add prefix for all environment variables check.

    Args:
        prefix: The prefix to add to environment variable names.
                If empty string, no prefix will be added.

    Returns:
        Decorated class with environment variable prefix functionality.

    Usage:
        .. code-block:: python

            @EnvVariablePrefix('APP_')
            class MyConfig(TypedConfig):
                database_url: str = 'default'
                port: int = 8080


            # This will look for APP_DATABASE_URL and APP_PORT environment variables
    '''

    def decorator(cls: Type[T]) -> Type[T]:
        # store the original prefix in the class
        setattr(cls, '_env_prefix', prefix if prefix else '')
        return cls

    return decorator
