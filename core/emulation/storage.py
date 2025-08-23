# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/17/2025 14:24'
__version__ = '0.1.0'

from typing import Any, Dict


class StateStorage:
    '''State for scenario.'''

    def __init__(self) -> None:
        self._state: Dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        '''Set state for scenario.'''
        self._state[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        '''Get state for scenario.'''
        return self._state.get(key, default)

    def clean(self) -> None:
        '''Clean state for scenario.'''
        self._state.clear()
