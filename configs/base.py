from typing import Any
from abc import ABC, abstractmethod

from core.emulation.mixer import MixerConfig


class BaseEmulatorConfig(ABC):
    '''Base emulator configuration class.'''

    @abstractmethod
    def build(self, *args: Any, **kwargs: Any) -> MixerConfig:
        '''Build the configuration.'''
        raise NotImplementedError
