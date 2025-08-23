# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/14/2025 00:00'

'''
Positive tests for scenarios module - basic scenario functionality.
'''

from typing import Any, Dict
from unittest.mock import MagicMock

import allure
import pytest

from core.emulation.scenarios import Scenarios


@allure.feature('Emulation')
@allure.story('Scenarios')
class TestBasicScenarios:
    '''Tests for basic scenario functions.'''

    @allure.title('Test do_nothing scenario returns current value')
    def test_do_nothing_returns_current_value(self, create_metric_context: Any) -> None:
        '''Test that do_nothing scenario returns the current metric value unchanged.'''
        # given a metric context with a specific value
        mock_metric = MagicMock()
        mock_metric.value = 75.0
        context = create_metric_context(mock_metric=mock_metric)

        # when do_nothing scenario is called
        result = Scenarios.do_nothing(context)

        # then it should return the current value
        assert result == 75.0

    @allure.title('Test do_nothing scenario with different values')
    @pytest.mark.parametrize('metric_value', [0.0, 100.0, 50.5, -10.0, 999.99])
    def test_do_nothing_with_different_values(self, create_metric_context: Any, metric_value: float) -> None:
        '''Test do_nothing scenario with various metric values.'''
        # given a metric context with a specific value
        mock_metric = MagicMock()
        mock_metric.value = metric_value
        context = create_metric_context(mock_metric=mock_metric)

        # when do_nothing is called
        result = Scenarios.do_nothing(context)

        # then it should return exactly that value
        assert result == metric_value
        assert isinstance(result, float)

    @allure.title('Test random_in_range with default metric range')
    def test_random_in_range_default_range(self, create_metric_context: Any, mock_random: Dict[str, MagicMock]) -> None:
        '''Test random_in_range uses metric's configured range by default.'''
        # given a metric context with a specific range (10.0, 90.0)
        mock_random['uniform'].return_value = 42.0

        # Create a mock metric with custom value range
        mock_metric = MagicMock()
        mock_metric.value = 50.0
        mock_metric.config = MagicMock()
        mock_metric.config.value_range = (10.0, 90.0)

        context = create_metric_context(mock_metric=mock_metric)

        # when random_in_range is called without value_range parameter
        result = Scenarios.random_in_range(context)

        # then it should use the metric's range
        mock_random['uniform'].assert_called_once_with(10.0, 90.0)
        assert result == 42.0

    @allure.title('Test random_in_range with custom range')
    def test_random_in_range_custom_range(self, create_metric_context: Any, mock_random: Dict[str, MagicMock]) -> None:
        '''Test random_in_range with a custom value range.'''
        # given a custom range and mock random value
        custom_range = (5.0, 25.0)
        mock_random['uniform'].return_value = 15.0
        context = create_metric_context()

        # when random_in_range is called with custom range
        result = Scenarios.random_in_range(context, value_range=custom_range)

        # then it should use the custom range
        mock_random['uniform'].assert_called_once_with(5.0, 25.0)
        assert result == 15.0

    @allure.title('Test random_in_range with different range parameters')
    @pytest.mark.parametrize(
        'range_min, range_max, expected_random',
        [(0.0, 1.0, 0.5), (100.0, 200.0, 150.0), (-50.0, 50.0, 0.0), (99.9, 100.0, 99.95)],
    )
    def test_random_in_range_parametrized(
        self,
        create_metric_context: Any,
        mock_random: Dict[str, MagicMock],
        range_min: float,
        range_max: float,
        expected_random: float,
    ) -> None:
        '''Test random_in_range with various range parameters.'''
        # given different ranges and expected random values
        mock_random['uniform'].return_value = expected_random
        context = create_metric_context()

        # when random_in_range is called
        result = Scenarios.random_in_range(context, value_range=(range_min, range_max))

        # then it should use the correct range and return the expected value
        mock_random['uniform'].assert_called_once_with(range_min, range_max)
        assert result == expected_random

    @allure.title('Test time_duration scenario initialization')
    def test_time_duration_initialization(self, create_metric_context: Any, mock_time: MagicMock) -> None:
        '''Test time_duration initializes uptime_start on first call.'''
        # given a fresh metric context and fixed time
        mock_time.return_value = 1000.0
        context = create_metric_context()

        # when time_duration is called for the first time
        result = Scenarios.time_duration(context)

        # then it should initialize uptime_start and return 0
        expected_start_time = context.storage.get('uptime_start')
        assert expected_start_time == 1000.0
        assert result == 0.0

    @allure.title('Test time_duration calculates elapsed time')
    def test_time_duration_elapsed_time(self, create_metric_context: Any, mock_time: MagicMock) -> None:
        '''Test time_duration calculates correct elapsed time.'''
        # given a metric context with uptime_start already set
        start_time = 1000.0
        context = create_metric_context()
        context.storage.set('uptime_start', start_time)
        mock_time.return_value = 1045.5  # current time (45.5 seconds later)

        # when time_duration is called
        result = Scenarios.time_duration(context)

        # then it should calculate correct elapsed time
        assert result == 45.5

    @allure.title('Test time_duration with multiple calls')
    def test_time_duration_multiple_calls(self, create_metric_context: Any, mock_time: MagicMock) -> None:
        '''Test time_duration consistency across multiple calls.'''
        # given different time values for sequential calls
        start_time = 1000.0
        context = create_metric_context()
        context.storage.set('uptime_start', start_time)

        time_values = [1010.0, 1025.0, 1060.0]
        expected_results = [10.0, 25.0, 60.0]

        for time_val, expected in zip(time_values, expected_results):
            # when time_duration is called at different times
            mock_time.return_value = time_val
            result = Scenarios.time_duration(context)

            # then it should return correct elapsed time
            assert result == expected

    @allure.title('Test variety_selection initialization')
    def test_variety_selection_initialization(
        self, create_metric_context: Any, variety_values_and_weights: Dict[str, Any]
    ) -> None:
        '''Test variety_selection initializes with first value on first call.'''
        # given values and weights
        values = variety_values_and_weights['values']
        weights = variety_values_and_weights['varieties']
        context = create_metric_context()

        # when variety_selection is called for first time
        result = Scenarios.variety_selection(context, values=values, varieties=weights, change_probability=0.0)

        # then it should return the first value
        assert result == values[0]

    @allure.title('Test variety_selection maintains value with zero probability')
    def test_variety_selection_no_change(
        self, create_metric_context: Any, variety_values_and_weights: Dict[str, Any]
    ) -> None:
        '''Test variety_selection maintains current value with zero change probability.'''
        # given values, weights, and zero change probability
        values = variety_values_and_weights['values']
        weights = variety_values_and_weights['varieties']
        context = create_metric_context()

        # setup the context to return index 1 (second value)
        context.storage.set('variety_index', 1)

        # when variety_selection is called with change_probability=0.0
        result = Scenarios.variety_selection(context, values=values, varieties=weights, change_probability=0.0)

        # then it should return the value at stored index (second value)
        assert result == values[1]  # 50.0

    @allure.title('Test variety_selection with forced change')
    def test_variety_selection_forced_change(
        self, create_metric_context: Any, variety_values_and_weights: Dict[str, Any], mock_random: Dict[str, MagicMock]
    ) -> None:
        '''Test variety_selection changes value with certainty.'''
        # given values, weights, and certain change
        values = variety_values_and_weights['values']
        weights = variety_values_and_weights['varieties']
        context = create_metric_context()
        context.storage.set('variety_index', 0)  # start at first value

        # mock random to trigger change and select specific value
        mock_random['random'].return_value = 0.5  # trigger change (> 0.0 probability)
        mock_random['uniform'].return_value = 0.3  # select second value (cumulative: 0.2 + 0.5 = 0.7)

        # when variety_selection is called with change_probability=1.0
        result = Scenarios.variety_selection(context, values=values, varieties=weights, change_probability=1.0)

        # then it should change to selected value
        # based on cumulative weights: [0.2, 0.7, 1.0], random 0.3 should select index 1
        expected_value = values[1]  # second value
        assert result == expected_value
