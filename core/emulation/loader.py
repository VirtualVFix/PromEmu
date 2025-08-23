# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '09/08/2025 00:00'

import inspect
import importlib
from pathlib import Path
from typing import Any, List, Optional

from .mixer import MixerConfig
from app_config import AppConfig
from core.logger import getLogger
from configs.base import BaseEmulatorConfig

log = getLogger(__file__)

SKIP_CONFIGS = ['base']
DEFAULT_CONFIG_CLASS_SUFFIX = 'Config'
DEFAULT_MODULES_PREFIX = 'configs'


class ConfigLoadError(Exception):
    '''Exception raised when configuration loading fails.'''

    def __init__(self, message: str):
        super().__init__(message)


def _validate_config_file(config_name: str, configs_dir: Path) -> Path:
    '''
    Validate that config file exists and return the config file path.

    Args:
        config_name: Name of the config file (without .py extension)
        configs_dir: Path to the folder containing the config files

    Returns:
        Path: The validated config file path

    Raises:
        ConfigLoadError: If config file doesn't exist
    '''
    config_file = Path(f'{config_name if config_name.endswith(".py") else config_name + ".py"}')
    if str(config_file.stem) in SKIP_CONFIGS:
        raise ConfigLoadError(f'Config <{config_name}> cannot be used as config!')
    config_path = configs_dir / config_file
    if not config_path.exists():
        available_configs = [f.stem for f in configs_dir.glob('*.py') if not f.name.startswith('_')]
        raise ConfigLoadError(
            f'Config file "{config_file}" not found in configs directory. Available configs: {available_configs}'
        )
    return config_file


def _import_config_module(config_file: Path) -> Any:
    '''
    Import config module and return it.

    Args:
        config_file: Path to the config file

    Returns:
        Any: The imported module

    Raises:
        ConfigLoadError: If import fails
    '''
    try:
        module_name = f'{DEFAULT_MODULES_PREFIX}.{config_file.stem}'
        config_module = importlib.import_module(module_name)
        log.info(f'Imported module: <{module_name}>')
        return config_module
    except ImportError as e:
        module_name = f'configs.{config_file.stem}'
        raise ConfigLoadError(f'Failed to import config module "{module_name}": {str(e)}') from e


def _find_config_classes(config_module: Any, config_file: Path) -> List[tuple[str, Any]]:
    '''
    Find classes that inherit from BaseEmulatorConfig in the config module.

    Args:
        config_module: The imported config module
        config_file: Path to the config file (for error messages)

    Returns:
        List of tuples containing (class_name, class_object)

    Raises:
        ConfigLoadError: If no valid config classes found
    '''
    config_classes = []
    for name, obj in inspect.getmembers(config_module):
        if inspect.isclass(obj) and issubclass(obj, BaseEmulatorConfig) and obj != BaseEmulatorConfig:
            config_classes.append((name, obj))

    if not config_classes:
        available_classes = [
            name for name, obj in inspect.getmembers(config_module, inspect.isclass) if obj != BaseEmulatorConfig
        ]
        raise ConfigLoadError(
            f'No classes inheriting from BaseEmulatorConfig found in <{config_file}>. '
            f'Available classes: {available_classes}'
        )

    return config_classes


def _select_config_class(config_classes: List[tuple[str, Any]], class_name: Optional[str], config_file: Path) -> Any:
    '''
    Select the appropriate config class to instantiate.

    Args:
        config_classes: List of available config classes
        class_name: Specific class name to use, or None for auto-detection
        config_file: Path to the config file (for error messages)

    Returns:
        Any: The selected class object

    Raises:
        ConfigLoadError: If specified class not found
    '''
    if class_name:
        target_class = None
        for name, cls in config_classes:
            if name == class_name:
                target_class = cls
                break

        if not target_class:
            available_classes = [name for name, _ in config_classes]
            raise ConfigLoadError(
                f'Class <{class_name}> not found in <{config_file}>. '
                f'Available BaseEmulatorConfig classes: {available_classes}'
            )
        return target_class
    else:
        # auto-detect: prefer class ending with 'Config', otherwise use first class
        for name, cls in config_classes:
            if name.endswith(DEFAULT_CONFIG_CLASS_SUFFIX):
                return cls

        # use first available class
        target_class = config_classes[0][1]
        log.info(f'Auto-selected class <{config_classes[0][0]}> from <{config_file}>')
        return target_class


def _instantiate_and_build_config(target_class: Any, **kwargs: Any) -> MixerConfig:
    '''Instantiate the config class and call its build method.

    Args:
        target_class: The class to instantiate
        **kwargs: Additional arguments to pass to the build method

    Returns:
        MixerConfig: The built configuration instance

    Raises:
        ConfigLoadError: If instantiation or build fails
    '''
    try:
        # instantiate the config class
        config_instance = target_class()
        log.info(f'Instantiated class: <{target_class.__name__}>')
    except Exception as e:
        raise ConfigLoadError(f'Error instantiating config class <{target_class.__name__}>: {str(e)}') from e

    # validate the instance
    if not isinstance(config_instance, BaseEmulatorConfig):
        raise ConfigLoadError(f'Class <{target_class.__name__}> instance is not a BaseEmulatorConfig subclass')

    try:
        # call the build method
        mixer_config = config_instance.build(**kwargs)
        log.info(f'Called build method on <{target_class.__name__}>')
    except Exception as e:
        raise ConfigLoadError(f'Error calling build method on <{target_class.__name__}>: {str(e)}') from e

    # validate the returned instance
    if not isinstance(mixer_config, MixerConfig):
        raise ConfigLoadError(
            f'Build method of <{target_class.__name__}> returned {type(mixer_config).__name__} '
            f'instead of {type(MixerConfig).__name__}'
        )

    return mixer_config


def _validate_mixer_config(mixer_config: MixerConfig) -> None:
    '''Validate the built mixer configuration instance.

    Args:
        mixer_config: The configuration to validate

    Raises:
        ConfigLoadError: If configuration is invalid
    '''
    if not hasattr(mixer_config, 'hosts') or not mixer_config.hosts:
        raise ConfigLoadError('Invalid MixerConfig: no hosts defined')


def load_config(
    config_name: str, class_name: Optional[str] = None, configs_dir: Path = AppConfig.CONFIGS_DIR, **kwargs: Any
) -> MixerConfig:
    '''Load configuration from a config file in the emulation/configs folder.

    Args:
        config_name: Name of the config file (without .py extension)
        class_name: Specific class name to use. If None, will auto-detect
        configs_dir: Path to the folder containing the config files
        **kwargs: Additional arguments to pass to the build method

    Returns:
        MixerConfig: The built configuration instance

    Raises:
        ConfigLoadError: If loading fails for any reason
    '''
    try:
        # validate config file exists
        config_file = _validate_config_file(config_name, configs_dir)
        # import the config module
        config_module = _import_config_module(config_file)
        # find classes that inherit from BaseEmulatorConfig
        config_classes = _find_config_classes(config_module, config_file)
        # select the class to instantiate
        target_class = _select_config_class(config_classes, class_name, config_file)
        # instantiate the class and call build method
        mixer_config = _instantiate_and_build_config(target_class, **kwargs)
        # validate the mixer config
        _validate_mixer_config(mixer_config)

        log.info(
            f'Successfully loaded config from <{config_file}> using class <{target_class.__name__}> '
            f'with <{len(mixer_config.hosts)}> hosts'
        )
        return mixer_config

    except Exception as e:
        if isinstance(e, ConfigLoadError):
            raise
        raise ConfigLoadError(f'Unexpected error loading config from "{config_name}": {str(e)}') from e


def list_available_configs(configs_dir: Path = AppConfig.CONFIGS_DIR) -> List[str]:
    '''
    List all available configuration files in the configs directory.

    Args:
        configs_dir: Path to the configs directory (default: AppConfig.CONFIGS_DIR)

    Returns:
        List of config file names (without .py extension)
    '''
    if not configs_dir.exists():
        return []

    return [f.stem for f in configs_dir.glob('*.py') if not f.name.startswith('__') if f.stem not in SKIP_CONFIGS]


def get_config_classes(config_name: str, configs_dir: Path = AppConfig.CONFIGS_DIR) -> List[str]:
    '''Get list of classes that inherit from BaseEmulatorConfig from a config file.

    Args:
        config_name: Name of the config file (without .py extension)
        configs_dir: Path to the configs directory

    Returns:
        List of class names

    Raises:
        ConfigLoadError: If config file doesn't exist or can't be imported
    '''
    # validate config file exists
    config_file = _validate_config_file(config_name, configs_dir)
    # import the config module
    config_module = _import_config_module(config_file)
    # find classes that inherit from BaseEmulatorConfig
    config_classes = _find_config_classes(config_module, config_file)
    return [name for name, _ in config_classes]
