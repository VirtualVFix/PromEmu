# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/14/2025 14:43'

'''
Negative tests for utils module - error conditions and edge cases.
'''

import re
from typing import Any

import allure
import pytest

from core.emulation import utils
from core.emulation.metrics import MetricConfig, MetricContext


@allure.feature('Utils')
@allure.story('Size Conversion Error Handling')
class TestSizeToBytesErrors:
    '''Tests for utils.size_to_bytes function error conditions.'''

    @allure.title('Test empty and None input validation')
    @pytest.mark.parametrize('invalid_input', ['', None])
    def test_empty_and_none_input(self, invalid_input: Any) -> None:
        '''Test that empty strings and None raise ValueError.'''
        with pytest.raises(ValueError, match='Size must be a non-empty string'):
            utils.size_to_bytes(invalid_input)

    @allure.title('Test non-string input type validation')
    @pytest.mark.parametrize('invalid_input', [123, 123.45, ['1kb'], {'size': '1kb'}, True, False])
    def test_non_string_input_types(self, invalid_input: Any) -> None:
        '''Test that non-string inputs raise ValueError.'''
        with pytest.raises(ValueError, match='Size must be a non-empty string'):
            utils.size_to_bytes(invalid_input)

    @pytest.mark.parametrize(
        'invalid_format',
        [
            'kb',  # missing number
            '1',  # missing unit
            'abc',  # no number at all
            '1.2.3kb',  # invalid number format
            'kb1',  # unit before number
            '1 2 kb',  # multiple numbers
            '1kb2',  # extra characters after unit
            '-1kb',  # negative number
            '+1kb',  # explicit positive sign
            '1e3kb',  # scientific notation
        ],
    )
    @allure.title('Test invalid format string validation')
    def test_invalid_format_strings(self, invalid_format: str) -> None:
        '''Test that invalid format strings raise ValueError.'''
        with pytest.raises(ValueError, match=r'Invalid size format: <.*>. Expected format like'):
            utils.size_to_bytes(invalid_format)

    @pytest.mark.parametrize(
        'unit_with_extra',
        [
            '1kbyte2'  # extra characters in unit - actually gets "Invalid size format"
        ],
    )
    @allure.title('Test units with extra characters validation')
    def test_units_with_extra_characters(self, unit_with_extra: str) -> None:
        '''Test that units with extra characters raise ValueError.'''
        with pytest.raises(ValueError, match=r'Invalid size format: <.*>. Expected format like'):
            utils.size_to_bytes(unit_with_extra)

    @pytest.mark.parametrize(
        'invalid_format_with_numbers',
        [
            '1mb3',  # numbers in unit - gets "Invalid size format"
            '1gb4',  # numbers in unit - gets "Invalid size format"
        ],
    )
    @allure.title('Test invalid format with numbers in unit validation')
    def test_invalid_format_with_numbers_in_unit(self, invalid_format_with_numbers: str) -> None:
        '''Test that units with numbers raise ValueError for invalid format.'''
        with pytest.raises(ValueError, match=r'Invalid size format: <.*>. Expected format like'):
            utils.size_to_bytes(invalid_format_with_numbers)

    @pytest.mark.parametrize(
        'unsupported_unit',
        [
            '1xyz',
            '1unit',
            '1byt',  # typo in byte
            '1zb',  # non-existent unit
            '1eb',  # exabyte not supported
            '1yb',  # yottabyte not supported
        ],
    )
    @allure.title('Test unsupported units validation')
    def test_unsupported_units(self, unsupported_unit: str) -> None:
        '''Test that unsupported units raise ValueError.'''
        with pytest.raises(ValueError, match=r'Unsupported unit: <.*>. Supported units:'):
            utils.size_to_bytes(unsupported_unit)

    @allure.title('Test invalid number format validation')
    @pytest.mark.parametrize('invalid_number', ['abckb', 'infkb', 'nankb', '1.2.3kb', '1..2kb', '.kb', 'kb.'])
    def test_invalid_number_formats(self, invalid_number: str) -> None:
        '''Test that invalid number formats raise ValueError.'''
        with pytest.raises(ValueError):
            utils.size_to_bytes(invalid_number)

    @allure.title('Test whitespace-only input validation')
    @pytest.mark.parametrize('whitespace_input', ['   ', '\t\t', '\n\n', '  \t  \n  '])
    def test_whitespace_only_input(self, whitespace_input: str) -> None:
        '''Test that whitespace-only strings raise ValueError.'''
        with pytest.raises(ValueError, match=re.compile(r'Invalid size format: <.*>.*Expected format like', re.DOTALL)):
            utils.size_to_bytes(whitespace_input)

    @pytest.mark.parametrize(
        'special_input', ['1@kb', '1#mb', '1$gb', '1%tb', '1&pb', '1*kb', '1(kb)', '1[kb]', '1{kb}']
    )
    @allure.title('Test special characters in input validation')
    def test_special_characters_in_input(self, special_input: str) -> None:
        '''Test that inputs with special characters raise ValueError.'''
        with pytest.raises(ValueError):
            utils.size_to_bytes(special_input)


@allure.feature('Utils')
@allure.story('Percentage Calculation Error Handling')
class TestCalcPercentUsageErrors:
    '''Tests for utils.calc_percent_usage function error conditions.'''

    @allure.title('Test invalid range where min equals max')
    @pytest.mark.parametrize('min_max_value', [0.0, 50.0, 100.0, -10.0])
    def test_invalid_range_min_equals_max(self, min_max_value: float) -> None:
        '''Test that ranges where min equals max raise ValueError.'''
        config = MetricConfig(name='test', value_range=(min_max_value, min_max_value))
        context = MetricContext(data=config, value=50.0)
        with pytest.raises(ValueError, match=r'Invalid target metric range: min <.*> must be less than max <.*>'):
            utils.calc_percent_usage(context)

    @allure.title('Test invalid range where min is greater than max')
    @pytest.mark.parametrize('min_val, max_val', [(100.0, 0.0), (50.0, 25.0), (0.0, -10.0), (10.0, 5.0), (-5.0, -10.0)])
    def test_invalid_range_min_greater_than_max(self, min_val: float, max_val: float) -> None:
        '''Test that ranges where min > max raise ValueError.'''
        config = MetricConfig(name='test', value_range=(min_val, max_val))
        context = MetricContext(data=config, value=50.0)
        with pytest.raises(ValueError, match=r'Invalid target metric range: min <.*> must be less than max <.*>'):
            utils.calc_percent_usage(context)

    @pytest.mark.parametrize(
        'extreme_value',
        [
            float('inf'),
            float('-inf'),
            1e308,  # very large number
            -1e308,  # very large negative number
        ],
    )
    @allure.title('Test extreme source values handling')
    def test_extreme_source_values(self, extreme_value: float) -> None:
        '''Test that extreme source values are handled properly (clamped).'''
        config = MetricConfig(name='test', value_range=(0.0, 100.0))
        context = MetricContext(data=config, value=extreme_value)
        # these should not raise exceptions but should clamp to range
        result = utils.calc_percent_usage(context)
        assert isinstance(result, float)
        assert 0.0 <= result <= 100.0

    @allure.title('Test NaN source value handling')
    def test_nan_source_value(self) -> None:
        '''Test behavior with NaN source value.'''
        config = MetricConfig(name='test', value_range=(0.0, 100.0))
        context = MetricContext(data=config, value=float('nan'))
        # NaN comparisons always return False, so it should be treated as out of range
        result = utils.calc_percent_usage(context)
        # NaN behavior in min/max operations is implementation-dependent
        # but the function should not crash
        assert isinstance(result, float)

    @allure.title('Test zero range edge case handling')
    def test_zero_range_edge_case(self) -> None:
        '''Test behavior when range is effectively zero due to floating point precision.'''
        # use values that are very close but not exactly equal
        min_val = 1.0000000000000001
        max_val = 1.0000000000000002
        config = MetricConfig(name='test', value_range=(min_val, max_val))

        # this might cause division by very small number but should not crash
        context = MetricContext(data=config, value=1.0000000000000001)
        result = utils.calc_percent_usage(context)
        assert isinstance(result, float)

    @allure.title('Test invalid metric config types handling')
    def test_invalid_metric_config_types(self) -> None:
        '''Test that invalid metric config raises appropriate errors.'''
        # test with None config
        with pytest.raises(AttributeError):
            context = MetricContext(data=None, value=50.0)  # type: ignore[arg-type]
            utils.calc_percent_usage(context)

    @allure.title('Test metric config with invalid value range type')
    def test_metric_config_invalid_value_range_type(self) -> None:
        '''Test metric config with malformed value_range.'''
        # create config with invalid range structure
        config = MetricConfig(name='test')
        # manually set invalid range (this would normally be caught by dataclass validation)
        config.__dict__['value_range'] = [0.0, 100.0]  # list instead of tuple

        # should still work as long as it's iterable with 2 elements
        context = MetricContext(data=config, value=50.0)
        result = utils.calc_percent_usage(context)
        assert result == 50.0

    @allure.title('Test very large value ranges handling')
    def test_very_large_ranges(self) -> None:
        '''Test percentage calculation with very large value ranges.'''
        config = MetricConfig(name='test', value_range=(0.0, 1e15))
        context = MetricContext(data=config, value=5e14)
        result = utils.calc_percent_usage(context)
        expected = 50.0
        assert result == pytest.approx(expected, rel=1e-9)

    @allure.title('Test very small ranges precision handling')
    def test_very_small_ranges_precision(self) -> None:
        '''Test percentage calculation with ranges that might cause precision issues.'''
        config = MetricConfig(name='test', value_range=(1e-15, 2e-15))
        context = MetricContext(data=config, value=1.5e-15)
        result = utils.calc_percent_usage(context)
        expected = 50.0
        # allow for some floating point precision issues
        assert result == pytest.approx(expected, rel=1e-10)
