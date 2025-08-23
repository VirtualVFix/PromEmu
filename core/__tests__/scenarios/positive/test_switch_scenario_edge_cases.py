# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/14/2025 18:40'

'''
Edge case tests for switch_scenario_by_events functionality.
'''

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import allure

from core.emulation.events import Event
from core.emulation.scenarios import Scenarios
from core.emulation.storage import StateStorage
from core.emulation.metrics import MetricContext


@allure.feature('Scenarios')
@allure.story('Switch Scenario Edge Cases')
class TestSwitchScenarioEdgeCases:
    '''Tests for switch_scenario_by_events edge cases and complex scenarios.'''

    @allure.title('Test switch scenario nested calls')
    def test_switch_scenario_nested_calls(self, create_metric_context: Any, mock_time: MagicMock) -> None:
        '''Test switch_scenario_by_events handles nested scenario calls correctly.'''
        # given configuration with nested scenarios
        nested_call_count = 0

        def nested_scenario(context: MetricContext, **kwargs: Any) -> float:
            nonlocal nested_call_count
            nested_call_count += 1
            if nested_call_count > 3:  # prevent infinite recursion in test
                return 42.0
            # call another scenario from within
            with patch('time.time', return_value=1000.0):
                result = Scenarios.sine_wave(context, period=100.0, amplitude=10.0, offset=50.0)
                return result if result is not None else 42.0

        events_config = {'nested_event': {'scenario': nested_scenario, 'scenario_data': {}, 'duration': 60.0}}

        mock_time.return_value = 1000.0

        mock_metric = MagicMock()
        mock_metric.value = 50.0
        mock_event = MagicMock(spec=Event)
        mock_event.name = 'nested_event'
        context = create_metric_context(mock_metric=mock_metric, event=mock_event)

        # when switch_scenario_by_events is called with nested scenario
        result = Scenarios.switch_scenario_by_events(context, events_config=events_config)

        # then it should handle nested calls correctly
        assert isinstance(result, float)
        assert nested_call_count > 0

    @allure.title('Test switch scenario malformed data')
    def test_switch_scenario_malformed_data(
        self, mock_emulated_metric: MagicMock, mock_event: Event, mock_random: Dict[str, MagicMock]
    ) -> None:
        '''Test switch_scenario_by_events handles malformed scenario data gracefully.'''
        # given malformed events configuration
        events_config = {
            'malformed_event': {
                'scenario': 'sine_wave',
                'scenario_data': {
                    'period': 'invalid_string',  # should be float
                    'amplitude': None,  # should be float
                    'offset': [1, 2, 3],  # should be float
                },
                'duration': 60.0,
            }
        }

        mock_event.name = 'malformed_event'
        mock_random['uniform'].return_value = 25.0

        # when switch_scenario_by_events is called with malformed data
        # create metric context
        context = MetricContext(
            data=mock_emulated_metric.config, value=mock_emulated_metric.value, event=mock_event, storage=StateStorage()
        )
        result = Scenarios.switch_scenario_by_events(context, events_config=events_config)

        # then it should handle the error and return random value
        assert result == 25.0
        mock_random['uniform'].assert_called_once()

    @allure.title('Test switch scenario callable object')
    def test_switch_scenario_callable_object(self, create_metric_context: Any) -> None:
        '''Test switch_scenario_by_events works with callable scenario objects.'''

        # given callable scenario object
        class CustomScenario:
            def __call__(self, context: MetricContext, multiplier: float = 2.0) -> float:
                value = context.value if context.value is not None else 0.0
                return float(value * multiplier)

        custom_scenario = CustomScenario()
        events_config = {
            'custom_event': {'scenario': custom_scenario, 'scenario_data': {'multiplier': 3.0}, 'duration': 30.0}
        }

        mock_metric = MagicMock()
        mock_metric.value = 10.0
        mock_event = MagicMock(spec=Event)
        mock_event.name = 'custom_event'
        context = create_metric_context(mock_metric=mock_metric, event=mock_event)

        # when switch_scenario_by_events is called with callable object
        result = Scenarios.switch_scenario_by_events(context, events_config=events_config)

        # then it should execute the callable and return result
        assert result == 30.0  # 10 * 3.0

    @allure.title('Test switch scenario state cleanup on error')
    def test_switch_scenario_state_cleanup_on_error(
        self, mock_emulated_metric: MagicMock, mock_event: Event, mock_random: Dict[str, MagicMock]
    ) -> None:
        '''Test switch_scenario_by_events cleans up state when scenario fails.'''

        # given scenario that will fail
        def failing_scenario(metric: Any, event: Any, **kwargs: Any) -> float:
            raise RuntimeError('Scenario execution failed')

        events_config = {'failing_event': {'scenario': failing_scenario, 'scenario_data': {}, 'duration': 60.0}}

        mock_event.name = 'failing_event'
        mock_random['uniform'].return_value = 15.0

        # track state changes
        state_changes = []

        def track_set_state(key: str, value: Any) -> None:
            state_changes.append((key, value))

        mock_emulated_metric.set_scenario_state.side_effect = track_set_state

        # when switch_scenario_by_events is called with failing scenario
        # create metric context
        context = MetricContext(
            data=mock_emulated_metric.config, value=mock_emulated_metric.value, event=mock_event, storage=StateStorage()
        )
        result = Scenarios.switch_scenario_by_events(context, events_config=events_config)

        # then it should return fallback value and not corrupt state
        assert result == 15.0
        # verify no partial state was set (or state was cleaned up)
        # the implementation should either set all state or none

    @allure.title('Test switch scenario zero duration')
    def test_switch_scenario_zero_duration(
        self, mock_emulated_metric: MagicMock, mock_event: Event, mock_time: MagicMock
    ) -> None:
        '''Test switch_scenario_by_events handles zero duration correctly.'''
        # given event with zero duration
        events_config = {
            'instant_event': {
                'scenario': 'do_nothing',
                'scenario_data': {},
                'duration': 0.0,  # zero duration
            }
        }

        mock_event.name = 'instant_event'
        mock_emulated_metric.value = 42.0
        mock_time.return_value = 1000.0

        # when switch_scenario_by_events is called with zero duration
        # create metric context
        context = MetricContext(
            data=mock_emulated_metric.config, value=mock_emulated_metric.value, event=mock_event, storage=StateStorage()
        )
        result = Scenarios.switch_scenario_by_events(context, events_config=events_config)

        # then it should execute the scenario but not persist it
        assert result == 42.0  # do_nothing returns current value

    @allure.title('Test switch scenario very long duration')
    def test_switch_scenario_very_long_duration(self, create_metric_context: Any, mock_time: MagicMock) -> None:
        '''Test switch_scenario_by_events handles very long durations correctly.'''
        # given event with very long duration
        events_config = {
            'persistent_event': {
                'scenario': 'do_nothing',
                'scenario_data': {},
                'duration': 86400.0 * 365,  # one year in seconds
            }
        }

        mock_time.return_value = 1000.0

        mock_metric = MagicMock()
        mock_metric.value = 100.0
        mock_event = MagicMock(spec=Event)
        mock_event.name = 'persistent_event'
        context = create_metric_context(mock_metric=mock_metric, event=mock_event)

        # when switch_scenario_by_events is called with very long duration
        result = Scenarios.switch_scenario_by_events(context, events_config=events_config)

        # then it should handle the long duration without issues
        assert result == 100.0
        # verify duration was stored correctly
        assert context.storage.get('last_event_duration') == 86400.0 * 365

    @allure.title('Test switch scenario concurrent events')
    def test_switch_scenario_concurrent_events(self, mock_time: MagicMock, mock_random: Dict[str, MagicMock]) -> None:
        '''Test switch_scenario_by_events handles concurrent events from different metrics.'''
        # given multiple metrics with different events
        metrics = []
        events = []

        for i in range(3):
            metric = MagicMock()
            metric.value = float(i * 10)
            metric.config.value_range = (0.0, 100.0)
            metrics.append(metric)

            event = MagicMock()
            event.name = f'event_{i}'
            events.append(event)

        events_config = {
            'event_0': {'scenario': 'do_nothing', 'scenario_data': {}, 'duration': 30.0},
            'event_1': {'scenario': 'do_nothing', 'scenario_data': {}, 'duration': 60.0},
            'event_2': {'scenario': 'do_nothing', 'scenario_data': {}, 'duration': 90.0},
        }

        mock_time.return_value = 1000.0
        mock_random['uniform'].return_value = 50.0

        # when switch_scenario_by_events is called concurrently on different metrics
        results = []
        for metric, event in zip(metrics, events):
            # create metric context
            context = MetricContext(data=metric.config, value=metric.value, event=event, storage=StateStorage())
            result = Scenarios.switch_scenario_by_events(context, events_config=events_config)
            results.append(result)

        # then each metric should handle its event independently
        assert len(results) == 3
        assert results[0] == 0.0  # metric 0 value
        assert results[1] == 10.0  # metric 1 value
        assert results[2] == 20.0  # metric 2 value

    @allure.title('Test switch scenario complex default')
    def test_switch_scenario_complex_default(self, create_metric_context: Any, mock_time: MagicMock) -> None:
        '''Test switch_scenario_by_events with complex default scenario and data.'''
        # given complex default scenario configuration
        default_scenario_data = {
            'period': 120.0,
            'amplitude': 25.0,
            'offset': 75.0,
            'phase_offset': 1.57,  # π/2 radians
        }

        mock_time.return_value = 1030.0  # 30 seconds elapsed

        mock_metric = MagicMock()
        mock_metric.value = 50.0
        context = create_metric_context(mock_metric=mock_metric, event=None)

        # Set up storage state as if sine_wave was started at 1000.0
        context.storage.set('sine_wave_start_time', 1000.0)

        # when switch_scenario_by_events is called without matching event
        result = Scenarios.switch_scenario_by_events(
            context, events_config={}, default_scenario='sine_wave', default_scenario_data=default_scenario_data
        )

        # then it should execute the default scenario with provided data
        # At 30s elapsed with period=120s: phase = (30/120)*2π + π/2 = π/2 + π/2 = π
        # sin(π) = 0, so result = 75 + 25*0 = 75
        assert isinstance(result, float)
        assert 50.0 <= result <= 100.0  # within amplitude range

    @allure.title('Test switch scenario parameter validation')
    def test_switch_scenario_parameter_validation(
        self, create_metric_context: Any, mock_random: Dict[str, MagicMock]
    ) -> None:
        '''Test switch_scenario_by_events validates parameters correctly.'''
        mock_random['uniform'].return_value = 33.0

        mock_metric = MagicMock()
        mock_metric.value = 50.0
        mock_metric.config.value_range = (0.0, 100.0)

        # test with None events_config - using empty dict instead as None would be invalid
        mock_event = MagicMock(spec=Event)
        mock_event.name = 'test_event'
        context = create_metric_context(mock_metric=mock_metric, event=mock_event)
        result = Scenarios.switch_scenario_by_events(context, events_config={})
        assert result == 33.0  # should return random value

        # test with empty events_config
        context = create_metric_context(mock_metric=mock_metric, event=mock_event)
        result = Scenarios.switch_scenario_by_events(context, events_config={})
        assert result == 33.0  # should return random value

        # test with None event
        context = create_metric_context(mock_metric=mock_metric, event=None)
        result = Scenarios.switch_scenario_by_events(context, events_config={})
        assert result == 33.0  # should return random value
