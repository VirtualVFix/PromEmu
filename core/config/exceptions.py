#!/usr/bin/env python3
# encoding: utf-8

# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/10/2025 14:45'


class ConfigError(Exception):
    '''Base exception for configuration errors'''


class ConfigTypeError(ConfigError, TypeError):
    '''Raised when a configuration value doesn't match its type annotation'''


class ConfigValueError(ConfigError, ValueError):
    '''Raised when a configuration value is missing or uninitalized'''
