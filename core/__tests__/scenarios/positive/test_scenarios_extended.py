# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/14/2025 18:40'

'''
Extended positive tests for scenarios module - comprehensive coverage of edge cases and mathematical correctness.
'''

import math
from typing import Any
from unittest.mock import MagicMock

import allure
import pytest

from core.emulation.scenarios import Scenarios


@allure.feature('Scenarios')
@allure.story('Extended Scenario Functions')
class TestScenariosExtended:
    '''Extended tests for scenario functions covering edge cases and mathematical correctness.'''

    @pytest.mark.parametrize(
        'period, amplitude, offset, phase_offset, elapsed_time, expected_result',
        [
            (100.0, 10.0, 50.0, 0.0, 0.0, 50.0),  # at start: sin(0) = 0
            (100.0, 10.0, 50.0, 0.0, 25.0, 60.0),  # quarter period: sin(π/2) = 1 -> 50 + 10*1 = 60
            (100.0, 10.0, 50.0, 0.0, 50.0, 50.0),  # half period: sin(π) = 0 -> 50 + 10*0 = 50
            (100.0, 10.0, 50.0, 0.0, 75.0, 40.0),  # three quarters: sin(3π/2) = -1 -> 50 + 10*(-1) = 40
            (100.0, 10.0, 50.0, math.pi / 2, 0.0, 60.0),  # phase offset π/2: sin(π/2) = 1 -> 50 + 10*1 = 60
            (200.0, 20.0, 100.0, 0.0, 50.0, 120.0),  # quarter of 200s period: sin(π/2) = 1 -> 100 + 20*1 = 120
        ],
    )
    @allure.title('Test sine wave mathematical correctness')
    def test_sine_wave_mathematical_correctness(
        self,
        create_metric_context: Any,
        mock_time: MagicMock,
        period: float,
        amplitude: float,
        offset: float,
        phase_offset: float,
        elapsed_time: float,
        expected_result: float,
    ) -> None:
        '''Test sine_wave produces mathematically correct values with various parameters.'''
        # given sine wave parameters and elapsed time
        start_time = 1000.0
        current_time = start_time + elapsed_time
        # mock time.time() to return current_time for elapsed calculation
        mock_time.return_value = current_time

        # Create context and set the sine_start_time in storage
        mock_metric = MagicMock()
        mock_metric.value = offset
        context = create_metric_context(mock_metric=mock_metric)
        context.storage.set('sine_start_time', start_time)

        # when sine_wave is called
        result = Scenarios.sine_wave(
            context, period=period, amplitude=amplitude, offset=offset, phase_offset=phase_offset
        )

        # then it should return mathematically correct value
        assert abs(result - expected_result) < 0.1, f'Expected {expected_result}, got {result}'  # type: ignore

    @pytest.mark.parametrize(
        'period, amplitude, offset',
        [
            (0.1, 1000.0, 0.0),  # very short period, large amplitude
            (10000.0, 0.001, 1000000.0),  # very long period, tiny amplitude, large offset
            (1.0, 0.0, 50.0),  # zero amplitude (constant)
        ],
    )
    @allure.title('Test sine wave extreme parameters')
    def test_sine_wave_extreme_parameters(
        self, create_metric_context: Any, mock_time: MagicMock, period: float, amplitude: float, offset: float
    ) -> None:
        '''Test sine_wave handles extreme parameter values correctly.'''
        # given extreme parameters
        mock_time.return_value = 1010.0
        mock_metric = MagicMock()
        mock_metric.value = offset
        context = create_metric_context(mock_metric=mock_metric)
        context.storage.set('sine_start_time', 1000.0)

        # when sine_wave is called with extreme parameters
        result = Scenarios.sine_wave(context, period=period, amplitude=amplitude, offset=offset)

        # then it should return a valid float value within expected range
        assert isinstance(result, float)
        assert offset - amplitude <= result <= offset + amplitude
