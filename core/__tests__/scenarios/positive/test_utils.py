# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/14/2025 14:43'

'''
Positive tests for utils module - utility functions.
'''

import allure
import pytest

from core.emulation import utils
from core.emulation.metrics import MetricConfig, MetricContext


@allure.feature('Utils')
@allure.story('Size Conversion')
class TestSizeToBytes:
    '''Tests for size_to_bytes function.'''

    @pytest.mark.parametrize(
        'size_str, expected',
        [
            ('1b', 1),
            ('1byte', 1),
            ('1bytes', 1),
            ('2kb', 2048),
            ('1kbyte', 1024),
            ('3kbytes', 3072),
            ('1kilobyte', 1024),
            ('2kilobytes', 2048),
            ('1mb', 1024**2),
            ('2mbyte', 2 * 1024**2),
            ('1mbytes', 1024**2),
            ('1megabyte', 1024**2),
            ('2megabytes', 2 * 1024**2),
            ('1gb', 1024**3),
            ('2gbyte', 2 * 1024**3),
            ('1gbytes', 1024**3),
            ('1gigabyte', 1024**3),
            ('2gigabytes', 2 * 1024**3),
            ('1tb', 1024**4),
            ('2tbyte', 2 * 1024**4),
            ('1tbytes', 1024**4),
            ('1terabyte', 1024**4),
            ('2terabytes', 2 * 1024**4),
            ('1pb', 1024**5),
            ('2pbyte', 2 * 1024**5),
            ('1pbytes', 1024**5),
            ('1petabyte', 1024**5),
            ('2petabytes', 2 * 1024**5),
        ],
    )
    @allure.title('Test byte units conversion')
    def test_byte_units_conversion(self, size_str: str, expected: int) -> None:
        '''Test conversion of various byte units to bytes.'''
        result = utils.size_to_bytes(size_str)
        assert result == expected

    @pytest.mark.parametrize(
        'size_str, expected',
        [
            ('1bit', 1),
            ('1bits', 1),
            ('2kbit', 2048),
            ('1kbits', 1024),
            ('1kilobit', 1024),
            ('2kilobits', 2048),
            ('1mbit', 1024**2),
            ('2mbits', 2 * 1024**2),
            ('1megabit', 1024**2),
            ('2megabits', 2 * 1024**2),
            ('1gbit', 1024**3),
            ('2gbits', 2 * 1024**3),
            ('1gigabit', 1024**3),
            ('2gigabits', 2 * 1024**3),
            ('1tbit', 1024**4),
            ('2tbits', 2 * 1024**4),
            ('1terabit', 1024**4),
            ('2terabits', 2 * 1024**4),
            ('1pbit', 1024**5),
            ('2pbits', 2 * 1024**5),
            ('1petabit', 1024**5),
            ('2petabits', 2 * 1024**5),
        ],
    )
    @allure.title('Test bit units conversion')
    def test_bit_units_conversion(self, size_str: str, expected: int) -> None:
        '''Test conversion of various bit units to bits.'''
        result = utils.size_to_bytes(size_str)
        assert result == expected

    @pytest.mark.parametrize(
        'size_str, expected',
        [
            ('1.5kb', 1536),
            ('2.5mb', int(2.5 * 1024**2)),
            ('0.5gb', int(0.5 * 1024**3)),
            ('1.25tb', int(1.25 * 1024**4)),
            ('3.14mb', int(3.14 * 1024**2)),
            ('0.1kb', int(0.1 * 1024)),
        ],
    )
    @allure.title('Test decimal values conversion')
    def test_decimal_values_conversion(self, size_str: str, expected: int) -> None:
        '''Test conversion of decimal size values.'''
        result = utils.size_to_bytes(size_str)
        assert result == expected

    @pytest.mark.parametrize(
        'size_str, expected',
        [
            ('1KB', 1024),
            ('1Mb', 1024**2),
            ('1GB', 1024**3),
            ('1TB', 1024**4),
            ('1PB', 1024**5),
            ('1KBIT', 1024),
            ('1MBIT', 1024**2),
            ('1GBIT', 1024**3),
        ],
    )
    @allure.title('Test case insensitive conversion')
    def test_case_insensitive_conversion(self, size_str: str, expected: int) -> None:
        '''Test that size conversion is case insensitive.'''
        result = utils.size_to_bytes(size_str)
        assert result == expected

    @pytest.mark.parametrize(
        'size_str, expected',
        [('  1kb  ', 1024), ('1 kb', 1024), ('  1  kb  ', 1024), ('\t1mb\t', 1024**2), ('1\tgb', 1024**3)],
    )
    @allure.title('Test whitespace handling')
    def test_whitespace_handling(self, size_str: str, expected: int) -> None:
        '''Test that whitespace is properly handled in size strings.'''
        result = utils.size_to_bytes(size_str)
        assert result == expected


@allure.feature('Utils')
@allure.story('Percentage Calculation')
class TestCalcPercentUsage:
    '''Tests for calc_percent_usage function.'''

    @pytest.mark.parametrize(
        'source_value, min_val, max_val, expected',
        [
            (50.0, 0.0, 100.0, 50.0),
            (25.0, 0.0, 100.0, 25.0),
            (75.0, 0.0, 100.0, 75.0),
            (0.0, 0.0, 100.0, 0.0),
            (100.0, 0.0, 100.0, 100.0),
            (50.0, 0.0, 50.0, 100.0),
            (25.0, 0.0, 50.0, 50.0),
        ],
    )
    @allure.title('Test basic percentage calculation')
    def test_basic_percentage_calculation(
        self, source_value: float, min_val: float, max_val: float, expected: float
    ) -> None:
        '''Test basic percentage calculation with various ranges.'''
        config = MetricConfig(name='test', value_range=(min_val, max_val))
        context = MetricContext(data=config, value=source_value)
        result = utils.calc_percent_usage(context)
        assert result == pytest.approx(expected, rel=1e-9)

    @pytest.mark.parametrize(
        'source_value, min_val, max_val, expected',
        [
            (-10.0, 0.0, 100.0, 0.0),  # below min
            (150.0, 0.0, 100.0, 100.0),  # above max
            (-50.0, 10.0, 90.0, 0.0),  # below min with offset range
            (200.0, 10.0, 90.0, 100.0),  # above max with offset range
        ],
    )
    @allure.title('Test clamping values to range')
    def test_clamping_values_to_range(
        self, source_value: float, min_val: float, max_val: float, expected: float
    ) -> None:
        '''Test that values outside range are properly clamped.'''
        config = MetricConfig(name='test', value_range=(min_val, max_val))
        context = MetricContext(data=config, value=source_value)
        result = utils.calc_percent_usage(context)
        assert result == pytest.approx(expected, rel=1e-9)

    @pytest.mark.parametrize(
        'source_value, min_val, max_val, expected',
        [
            (30.0, 20.0, 40.0, 50.0),  # middle of range
            (20.0, 20.0, 40.0, 0.0),  # at minimum
            (40.0, 20.0, 40.0, 100.0),  # at maximum
            (35.0, 20.0, 40.0, 75.0),  # 3/4 of range
        ],
    )
    @allure.title('Test non-zero minimum ranges')
    def test_non_zero_minimum_ranges(
        self, source_value: float, min_val: float, max_val: float, expected: float
    ) -> None:
        '''Test percentage calculation with non-zero minimum values.'''
        config = MetricConfig(name='test', value_range=(min_val, max_val))
        context = MetricContext(data=config, value=source_value)
        result = utils.calc_percent_usage(context)
        assert result == pytest.approx(expected, rel=1e-9)

    @pytest.mark.parametrize(
        'source_value, min_val, max_val, expected',
        [
            (-50.0, -100.0, 0.0, 50.0),
            (-75.0, -100.0, 0.0, 25.0),
            (-100.0, -100.0, 0.0, 0.0),
            (0.0, -100.0, 0.0, 100.0),
            (-25.0, -50.0, 50.0, 25.0),
        ],
    )
    @allure.title('Test negative value ranges')
    def test_negative_value_ranges(self, source_value: float, min_val: float, max_val: float, expected: float) -> None:
        '''Test percentage calculation with negative value ranges.'''
        config = MetricConfig(name='test', value_range=(min_val, max_val))
        context = MetricContext(data=config, value=source_value)
        result = utils.calc_percent_usage(context)
        assert result == pytest.approx(expected, rel=1e-9)

    @allure.title('Test floating point precision')
    def test_floating_point_precision(self) -> None:
        '''Test that floating point calculations maintain precision.'''
        config = MetricConfig(name='test', value_range=(0.0, 1.0))
        context = MetricContext(data=config, value=0.333333)
        result = utils.calc_percent_usage(context)
        expected = 33.3333
        assert result == pytest.approx(expected, rel=1e-4)

    @allure.title('Test very small ranges')
    def test_very_small_ranges(self) -> None:
        '''Test percentage calculation with very small value ranges.'''
        config = MetricConfig(name='test', value_range=(0.001, 0.002))
        context = MetricContext(data=config, value=0.0015)
        result = utils.calc_percent_usage(context)
        expected = 50.0
        assert result == pytest.approx(expected, rel=1e-9)
