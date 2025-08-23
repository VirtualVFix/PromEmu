# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/12/2025 19:18'

'''Utility functions for Prometheus metrics core.'''

import re
from typing import Optional

from .metrics import MetricContext


# define unit multipliers
# fmt: off
BYTE_UNITS = {
    'b': 1, 'byte': 1, 'bytes': 1,
    'kb': 1024, 'kbyte': 1024, 'kbytes': 1024, 'kilobyte': 1024, 'kilobytes': 1024,
    'mb': 1024**2, 'mbyte': 1024**2, 'mbytes': 1024**2, 'megabyte': 1024**2, 'megabytes': 1024**2,
    'gb': 1024**3, 'gbyte': 1024**3, 'gbytes': 1024**3, 'gigabyte': 1024**3, 'gigabytes': 1024**3,
    'tb': 1024**4, 'tbyte': 1024**4, 'tbytes': 1024**4, 'terabyte': 1024**4, 'terabytes': 1024**4,
    'pb': 1024**5, 'pbyte': 1024**5, 'pbytes': 1024**5, 'petabyte': 1024**5, 'petabytes': 1024**5,
}

BIT_UNITS = {
    'bit': 1, 'bits': 1,
    'kbit': 1024, 'kbits': 1024, 'kilobit': 1024, 'kilobits': 1024,
    'mbit': 1024**2, 'mbits': 1024**2, 'megabit': 1024**2, 'megabits': 1024**2,
    'gbit': 1024**3, 'gbits': 1024**3, 'gigabit': 1024**3, 'gigabits': 1024**3,
    'tbit': 1024**4, 'tbits': 1024**4, 'terabit': 1024**4, 'terabits': 1024**4,
    'pbit': 1024**5, 'pbits': 1024**5, 'petabit': 1024**5, 'petabits': 1024**5,
}
# fmt: on


def size_to_bytes(size: str) -> int:
    '''Convert size string to bytes or bits.'''
    if not size or not isinstance(size, str):
        raise ValueError('Size must be a non-empty string')

    # normalize to lowercase for matching
    size_lower = size.lower().strip()

    # extract number and unit using regex
    match = re.match(r'^(\d+(?:\.\d+)?)\s*([a-z]+)$', size_lower)
    if not match:
        raise ValueError(f'Invalid size format: <{size}>. Expected format like "100KB" or "1.5Mbit"')

    number_str, unit = match.groups()
    try:
        number = float(number_str)
    except ValueError:
        raise ValueError(f'Invalid number in size: <{number_str}>')

    # check which unit type it is
    if unit in BYTE_UNITS:
        multiplier = BYTE_UNITS[unit]
    elif unit in BIT_UNITS:
        multiplier = BIT_UNITS[unit]
    else:
        raise ValueError(f'Unsupported unit: <{unit}>. Supported units: bytes, bits and their prefixes (k, m, g, t, p)')

    return int(number * multiplier)


def calc_percent_usage(source_metric_context: MetricContext) -> Optional[float]:
    '''Calculate usage percentage based on source_value and source metric configuration.'''
    if source_metric_context.value is None:
        return None

    min_value, max_value = source_metric_context.data.value_range

    if min_value >= max_value:
        raise ValueError(f'Invalid target metric range: min <{min_value}> must be less than max <{max_value}>')

    # clamp source value to target range
    clamped_value = max(min_value, min(max_value, source_metric_context.value))

    # calculate percentage
    range_size = max_value - min_value
    usage_ratio = (clamped_value - min_value) / range_size

    return float(usage_ratio * 100.0)
