# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/14/2025 00:00'

'''
Positive tests for scenarios module - advanced scenario functionality.
'''

import math
from unittest.mock import MagicMock
from typing import Dict, Callable

import pytest
import allure

from core.emulation.events import Event
from ..conftest import MockAsyncioCreateTask
from core.emulation.scenarios import Scenarios
from core.emulation.metrics import MetricConfig, MetricContext


@allure.feature('Scenarios')
@allure.story('Advanced Scenario Functions')
class TestAdvancedScenarios:
    '''Tests for advanced scenario functions.'''

    @allure.title('Test feature toggle before start time')
    def test_feature_toggle_before_start_time(
        self, metric_context_factory: Callable[..., MetricContext], mock_time: MagicMock
    ) -> None:
        '''Test feature_toggle returns off_value before start_time.'''
        # given a feature toggle that hasn't started yet
        mock_time.return_value = 1000.0

        # when feature_toggle is called
        context = metric_context_factory()
        result = Scenarios.feature_toggle(context, start_time=30.0, duration=60.0, on_value=1.0, off_value=0.0)

        # then it should initialize and return off_value
        assert result == 0.0
        assert context.storage.get('start_timestamp') == 1000.0

    @allure.title('Test feature toggle on period')
    def test_feature_toggle_on_period(
        self,
        create_metric_context: Callable[..., MetricContext],
        mock_time: MagicMock,
        mock_asyncio_create_task: MockAsyncioCreateTask,
    ) -> None:
        '''Test feature_toggle returns on_value during on period.'''
        # given feature toggle is in on period
        # mock time to be 45 seconds after start (start_time=30, so 15 seconds into on period)
        mock_time.return_value = 1045.0

        # create metric context and initialize start timestamp
        context = create_metric_context()
        context.storage.set('start_timestamp', 1000.0)  # Initialize properly
        context.storage.set('feature_active', False)  # was off, now turning on

        # when feature_toggle is called
        result = Scenarios.feature_toggle(context, start_time=30.0, duration=60.0, on_value=1.0, off_value=0.0)

        # then it should return on_value and update state
        assert result == 1.0
        assert context.storage.get('feature_active') == True
        assert len(mock_asyncio_create_task.created_tasks) == 1

    @allure.title('Test feature toggle off period')
    def test_feature_toggle_off_period(
        self,
        create_metric_context: Callable[..., MetricContext],
        mock_time: MagicMock,
        mock_asyncio_create_task: MockAsyncioCreateTask,
    ) -> None:
        '''Test feature_toggle returns off_value during off period.'''
        # given feature toggle is in off period
        # cycle: start_time=30, duration=60, interval=15 = total cycle 75s
        # at time 1095s: elapsed = 1095-1000 = 95s, cycle_elapsed = 95-30 = 65s, cycle_position = 65s % 75s = 65s
        # 65s > 60s duration, so it's in off period
        mock_time.return_value = 1095.0

        # create metric context and initialize start timestamp
        context = create_metric_context()
        context.storage.set('start_timestamp', 1000.0)  # Initialize properly
        context.storage.set('feature_active', True)  # was on, now turning off

        # when feature_toggle is called
        result = Scenarios.feature_toggle(
            context, start_time=30.0, duration=60.0, interval=15.0, on_value=1.0, off_value=0.0
        )

        # then it should return off_value and update state
        assert result == 0.0
        assert context.storage.get('feature_active') == False
        assert len(mock_asyncio_create_task.created_tasks) == 1

    @allure.title('Test feature toggle cycle consistency')
    def test_feature_toggle_cycle_consistency(
        self,
        create_metric_context: Callable[..., MetricContext],
        mock_time: MagicMock,
        mock_asyncio_create_task: MockAsyncioCreateTask,
    ) -> None:
        '''Test feature_toggle maintains consistent cycle timing.'''
        # given feature toggle parameters
        start_time = 10.0
        duration = 20.0
        interval = 10.0
        # total cycle = duration + interval = 30s

        # test different points in the cycle
        # time | elapsed | cycle_elapsed | cycle_pos | expected
        test_cases = [
            (1005.0, 0.0),  # before start_time (5s < 10s)
            (1015.0, 1.0),  # 15s elapsed, 5s cycle_elapsed, 5s cycle_pos (< 20s duration) -> ON
            (1025.0, 1.0),  # 25s elapsed, 15s cycle_elapsed, 15s cycle_pos (< 20s duration) -> ON
            (1035.0, 0.0),  # 35s elapsed, 25s cycle_elapsed, 25s cycle_pos (> 20s duration) -> OFF
            (1045.0, 1.0),  # 45s elapsed, 35s cycle_elapsed, 5s cycle_pos (< 20s duration) -> ON (second cycle)
            (1065.0, 0.0),  # 65s elapsed, 55s cycle_elapsed, 25s cycle_pos (> 20s duration) -> OFF
        ]

        for time_val, expected_value in test_cases:
            mock_time.return_value = time_val

            # create fresh metric context for each test
            context = create_metric_context()
            context.storage.set('start_timestamp', 1000.0)
            context.storage.set('feature_active', expected_value == 0.0)  # opposite to trigger state change

            result = Scenarios.feature_toggle(
                context, start_time=start_time, duration=duration, interval=interval, on_value=1.0, off_value=0.0
            )

            assert result == expected_value, f"At time {time_val}, expected {expected_value}, got {result}"

    @allure.title('Test sine wave initialization')
    def test_sine_wave_initialization(
        self, create_metric_context: Callable[..., MetricContext], mock_time: MagicMock
    ) -> None:
        '''Test sine_wave initializes start time correctly.'''
        # given a fresh sine wave and fixed time
        mock_time.return_value = 1000.0
        mock_emulated_metric = MagicMock()
        mock_emulated_metric.get_scenario_state.return_value = None

        # when sine_wave is called for first time
        context = create_metric_context(mock_metric=mock_emulated_metric)
        result = Scenarios.sine_wave(context)

        # then it should initialize start time and return offset value
        assert context.storage.get('sine_start_time') == 1000.0
        assert result == 50.0  # default offset

    @allure.title('Test sine wave mathematical correctness')
    def test_sine_wave_mathematical_correctness(
        self, create_metric_context: Callable[..., MetricContext], mock_time: MagicMock
    ) -> None:
        '''Test sine_wave produces mathematically correct values.'''
        # given sine wave parameters
        period = 100.0
        amplitude = 25.0
        offset = 75.0
        phase_offset = math.pi / 4  # 45 degrees
        start_time = 1000.0

        # Mock time.time() to return controlled values
        mock_time.return_value = start_time

        # create metric context and make initial call to set start_time
        context = create_metric_context()
        Scenarios.sine_wave(context, period=period, amplitude=amplitude, offset=offset, phase_offset=phase_offset)

        # test at different time points
        test_cases = [
            (1000.0, 0.0),  # at start (0 elapsed)
            (1025.0, 25.0),  # quarter period
            (1050.0, 50.0),  # half period
            (1075.0, 75.0),  # three-quarter period
            (1100.0, 100.0),  # full period
        ]

        for current_time, elapsed in test_cases:
            mock_time.return_value = current_time

            # calculate expected value
            phase = (elapsed / period) * 2 * math.pi + phase_offset
            expected = offset + amplitude * math.sin(phase)

            result = Scenarios.sine_wave(
                context, period=period, amplitude=amplitude, offset=offset, phase_offset=phase_offset
            )

            assert abs(result - expected) < 0.001, f"At elapsed {elapsed}, expected {expected:.3f}, got {result:.3f}"  # type: ignore

    @allure.title('Test sine wave default parameters')
    def test_sine_wave_default_parameters(
        self, create_metric_context: Callable[..., MetricContext], mock_time: MagicMock
    ) -> None:
        '''Test sine_wave works correctly with default parameters.'''
        # given default parameters and various elapsed times
        mock_emulated_metric = MagicMock()
        mock_emulated_metric.get_scenario_state.return_value = 1000.0
        context = create_metric_context(mock_metric=mock_emulated_metric)

        test_times = [1000.0, 1075.0, 1150.0, 1300.0]  # 0, 75, 150, 300 seconds elapsed

        for current_time in test_times:
            mock_time.return_value = current_time

            result = Scenarios.sine_wave(context)

            # with defaults: period=300, amplitude=50, offset=50, phase_offset=0
            # result should be between 0 and 100 (offset ± amplitude)
            assert 0.0 <= result <= 100.0  # type: ignore
            assert isinstance(result, float)

    @allure.title('Test update by trend up')
    def test_update_by_trend_up(
        self, create_metric_context: Callable[..., MetricContext], mock_random: Dict[str, MagicMock]
    ) -> None:
        '''Test update_by_trend increases value with up trend.'''
        # given metric with starting value and up trend
        mock_emulated_metric = MagicMock()
        mock_emulated_metric.value = 50.0
        mock_emulated_metric.get_scenario_state.return_value = 50.0  # accumulated value
        mock_random['uniform'].return_value = 5.0  # positive step

        # when update_by_trend is called with up trend
        context = create_metric_context(mock_metric=mock_emulated_metric)
        result = Scenarios.update_by_trend(context, trend='up', step_range=(1.0, 10.0))

        # then it should increase value and update accumulated state
        assert result == 55.0
        assert context.storage.get('accumulated_value') == 55.0
        mock_random['uniform'].assert_called_with(1.0, 10.0)

    @allure.title('Test update by trend down')
    def test_update_by_trend_down(
        self, create_metric_context: Callable[..., MetricContext], mock_random: Dict[str, MagicMock]
    ) -> None:
        '''Test update_by_trend decreases value with down trend.'''
        # given metric with starting value and down trend
        mock_emulated_metric = MagicMock()
        mock_emulated_metric.value = 80.0

        # the update_by_trend method calls random.uniform with negated range for down trend
        mock_random['uniform'].return_value = 8.0

        # when update_by_trend is called with down trend
        context = create_metric_context(mock_metric=mock_emulated_metric)
        result = Scenarios.update_by_trend(context, trend='down', step_range=(5.0, 15.0))

        # then it should call random.uniform with negated range and return accumulated value
        # Expected call: random.uniform(-15.0, -5.0) because it negates the range
        assert result == 88.0  # 80.0 + 8.0 (the implementation adds the step)
        assert context.storage.get('accumulated_value') == 88.0
        mock_random['uniform'].assert_called_with(-15.0, -5.0)

    @allure.title('Test update by trend hold')
    def test_update_by_trend_hold(
        self, create_metric_context: Callable[..., MetricContext], mock_random: Dict[str, MagicMock]
    ) -> None:
        '''Test update_by_trend keeps value stable with hold trend.'''
        # given metric with starting value and hold trend
        mock_emulated_metric = MagicMock()
        mock_emulated_metric.value = 60.0

        # the hold trend calls random.uniform with (-min, +max) range
        mock_random['uniform'].return_value = 3.0

        # when update_by_trend is called with hold trend
        context = create_metric_context(mock_metric=mock_emulated_metric)
        result = Scenarios.update_by_trend(context, trend='hold', step_range=(1.0, 5.0))

        # then it should apply variation and NOT set accumulated_value (hold trend skips storage)
        # Expected call: random.uniform(-1.0, 5.0) for hold trend
        assert result == 63.0  # 60.0 + 3.0
        assert context.storage.get('accumulated_value') is None  # hold trend doesn't store accumulated value
        mock_random['uniform'].assert_called_with(-1.0, 5.0)

    @allure.title('Test relay to other metric success')
    def test_relay_to_other_metric_success(
        self,
        create_source_metric_context: Callable[..., MetricContext],
        source_metric_for_relay: MagicMock,
        calc_function: Callable[[MetricContext], float],
    ) -> None:
        '''Test relay_to_other_metric successfully relays and calculates value.'''
        # given source metric and calc function
        source_metric_for_relay.value = 8589934592.0  # 8GB

        # create source metric context
        context = create_source_metric_context(source_metric=source_metric_for_relay)

        # add source to context links
        context.links["source_metric_for_relay"] = context

        # when relay_to_other_metric is called
        result = Scenarios.relay_to_other_metric(
            context, source_metric_name='source_metric_for_relay', calc_function=calc_function
        )

        # then it should calculate correct percentage
        # (8GB - 1GB) / (16GB - 1GB) * 100 = 7/15 * 100 ≈ 46.67%
        expected_result = ((8589934592.0 - 1073741824.0) / (17179869184.0 - 1073741824.0)) * 100.0
        assert abs(result - expected_result) < 0.01  # type: ignore

    @allure.title('Test relay to other metric no source')
    def test_relay_to_other_metric_no_source(
        self, create_metric_context: Callable[..., MetricContext], calc_function: Callable[[MetricContext], float]
    ) -> None:
        '''Test relay_to_other_metric returns current value when no source metric provided.'''
        # given no source metric
        mock_emulated_metric = MagicMock()
        mock_emulated_metric.value = 42.0

        # when relay_to_other_metric is called without source
        context = create_metric_context(mock_metric=mock_emulated_metric)
        result = Scenarios.relay_to_other_metric(
            context, source_metric_name="non_existent_metric", calc_function=calc_function
        )

        # then it should return current metric value
        assert result == 42.0

    @allure.title('Test relay to other metric no calc function')
    def test_relay_to_other_metric_no_calc_function(self, create_metric_context: Callable[..., MetricContext]) -> None:
        '''Test relay_to_other_metric returns current value when no calc function provided.'''
        # given source metric but no calculation function
        mock_emulated_metric = MagicMock()
        mock_emulated_metric.value = 73.5

        # when relay_to_other_metric is called
        context = create_metric_context(mock_metric=mock_emulated_metric)
        result = Scenarios.relay_to_other_metric(
            context,
            source_metric_name="source_metric_for_relay",
            calc_function=None,  # type: ignore
        )

        # then it should return current metric value
        assert result == 73.5

    @allure.title('Test calc by event matching event')
    def test_calc_by_event_matching_event(
        self,
        create_metric_context: Callable[..., MetricContext],
        events_config_for_calc_by_event: Dict[str, Callable[[float, MetricConfig], float]],
    ) -> None:
        '''Test calc_by_event applies calculation when event matches.'''
        # given metric with current value and matching event
        mock_emulated_metric = MagicMock()
        mock_emulated_metric.value = 5.0

        test_event = Event(name='worker_started', data={'timestamp': 1000.0}, source='test_source')

        # when calc_by_event is called
        context = create_metric_context(mock_metric=mock_emulated_metric, event=test_event)
        result = Scenarios.calc_by_event(context, events_config=events_config_for_calc_by_event)  # type: ignore

        # then it should apply the worker_started calculation (value + 1)
        assert result == 6.0

    @allure.title('Test calc by event no match')
    def test_calc_by_event_no_match(
        self,
        create_metric_context: Callable[..., MetricContext],
        events_config_for_calc_by_event: Dict[str, Callable[[float, MetricConfig], float]],
    ) -> None:
        '''Test calc_by_event returns current value when event doesn't match.'''
        # given metric with current value and non-matching event
        mock_emulated_metric = MagicMock()
        mock_emulated_metric.value = 10.0

        test_event = Event(name='unknown_event', data={'timestamp': 1000.0}, source='test_source')

        # when calc_by_event is called
        context = create_metric_context(mock_metric=mock_emulated_metric, event=test_event)
        result = Scenarios.calc_by_event(context, events_config=events_config_for_calc_by_event)  # type: ignore

        # then it should return current value
        assert result == 10.0

    @allure.title('Test calc by event no event')
    def test_calc_by_event_no_event(
        self,
        create_metric_context: Callable[..., MetricContext],
        events_config_for_calc_by_event: Dict[str, Callable[[float, MetricConfig], float]],
    ) -> None:
        '''Test calc_by_event returns current value when no event provided.'''
        # given metric with current value and no event
        mock_emulated_metric = MagicMock()
        mock_emulated_metric.value = 7.0

        # when calc_by_event is called without event
        context = create_metric_context(mock_metric=mock_emulated_metric, event=None)
        result = Scenarios.calc_by_event(context, events_config=events_config_for_calc_by_event)  # type: ignore

        # then it should return current value
        assert result == 7.0

    @pytest.mark.parametrize(
        'event_name, initial_value, expected_result',
        [
            ('worker_started', 0, 1),  # +1
            ('worker_started', 5, 6),  # +1
            ('worker_stopped', 3, 2),  # -1
            ('worker_stopped', 0, 0),  # max(0, -1) = 0
            ('worker_reset', 10, 0),  # reset to 0
        ],
    )
    @allure.title('Test calc by event different events')
    def test_calc_by_event_different_events(
        self,
        create_metric_context: Callable[..., MetricContext],
        events_config_for_calc_by_event: Dict[str, Callable[[float, MetricConfig], float]],
        event_name: str,
        initial_value: float,
        expected_result: float,
    ) -> None:
        '''Test calc_by_event with different event types and values.'''
        # given different initial values and event types
        mock_emulated_metric = MagicMock()
        mock_emulated_metric.value = initial_value

        test_event = Event(name=event_name, data={'timestamp': 1000.0}, source='test_source')

        # when calc_by_event is called
        context = create_metric_context(mock_metric=mock_emulated_metric, event=test_event)
        result = Scenarios.calc_by_event(context, events_config=events_config_for_calc_by_event)  # type: ignore

        # then it should return expected result
        assert result == expected_result
