# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/14/2025 00:00'

'''
Positive tests for scenarios module - switch_scenario_by_events functionality.
'''

from typing import Any, Dict
from unittest.mock import MagicMock

import allure

from core.emulation.events import Event
from core.emulation.scenarios import Scenarios
from core.emulation.storage import StateStorage
from core.emulation.metrics import MetricContext


@allure.feature('Scenarios')
@allure.story('Switch Scenario by Events')
class TestSwitchScenarioByEvents:
    '''Tests for switch_scenario_by_events scenario function.'''

    @allure.title('Test switch with matching event')
    def test_switch_with_matching_event(
        self,
        create_metric_context: Any,
        mock_event: Event,
        events_config_for_switching: Dict[str, Dict[str, Any]],
        mock_random: Dict[str, MagicMock],
        mock_time: MagicMock,
    ) -> None:
        '''Test switch_scenario_by_events executes event-specific scenario.'''
        # given a matching event and configuration
        mock_event.name = 'peak_load_start'
        mock_random['uniform'].return_value = 85.0  # value within peak load range
        mock_time.return_value = 1000.0

        mock_metric = MagicMock()
        mock_metric.value = 50.0
        context = create_metric_context(mock_metric=mock_metric, event=mock_event)

        # when switch_scenario_by_events is called with matching event
        result = Scenarios.switch_scenario_by_events(
            context, events_config=events_config_for_switching, default_scenario='do_nothing'
        )

        # then it should execute the event's scenario (random_in_range with peak load range)
        assert result == 85.0
        mock_random['uniform'].assert_called_with(75.0, 100.0)

        # and store event state in context storage
        assert context.storage.get('last_event_params') == {'value_range': (75.0, 100.0)}
        assert context.storage.get('last_event_timestamp') == 1000.0
        assert context.storage.get('last_event_duration') == 60.0

    @allure.title('Test switch with event no duration')
    def test_switch_with_event_no_duration(
        self,
        create_metric_context: Any,
        mock_event: Event,
        events_config_for_switching: Dict[str, Dict[str, Any]],
        mock_random: Dict[str, MagicMock],
        mock_time: MagicMock,
    ) -> None:
        '''Test switch_scenario_by_events with event that has no duration limit.'''
        # given event without duration
        mock_event.name = 'peak_load_end'
        mock_random['uniform'].return_value = 15.0
        mock_time.return_value = 1500.0

        mock_metric = MagicMock()
        mock_metric.value = 50.0
        context = create_metric_context(mock_metric=mock_metric, event=mock_event)

        # when switch_scenario_by_events is called
        result = Scenarios.switch_scenario_by_events(context, events_config=events_config_for_switching)

        # then it should execute the event's scenario and set duration to None
        assert result == 15.0
        assert context.storage.get('last_event_duration') is None

    @allure.title('Test switch continues last event within duration')
    def test_switch_continues_last_event_within_duration(
        self, create_metric_context: Any, mock_random: Dict[str, MagicMock], mock_time: MagicMock
    ) -> None:
        '''Test switch_scenario_by_events continues using last event scenario within duration.'''
        # given a last event scenario that's still active
        mock_scenario_func = MagicMock(return_value=95.0)
        mock_time.return_value = 1030.0  # 30 seconds after event (within 60s duration)

        mock_metric = MagicMock()
        mock_metric.value = 50.0
        context = create_metric_context(mock_metric=mock_metric, event=None)

        # Set up storage state as if an event scenario was previously executed
        context.storage.set('last_event_scenario', mock_scenario_func)
        context.storage.set('last_event_duration', 60.0)
        context.storage.set('last_event_timestamp', 1000.0)
        context.storage.set('last_event_params', {'value_range': (75.0, 100.0)})

        # when switch_scenario_by_events is called without new event
        result = Scenarios.switch_scenario_by_events(context, events_config={})

        # then it should continue using the last event scenario
        assert result == 95.0
        mock_scenario_func.assert_called_once_with(context, value_range=(75.0, 100.0))

    @allure.title('Test switch expires last event after duration')
    def test_switch_expires_last_event_after_duration(
        self, create_metric_context: Any, mock_random: Dict[str, MagicMock], mock_time: MagicMock
    ) -> None:
        '''Test switch_scenario_by_events stops using last event scenario after duration expires.'''
        # given a last event scenario that has expired
        mock_scenario_func = MagicMock(return_value=95.0)
        mock_time.return_value = 1070.0  # 70 seconds after event (beyond 60s duration)
        mock_random['uniform'].return_value = 25.0

        mock_metric = MagicMock()
        mock_metric.value = 50.0
        context = create_metric_context(mock_metric=mock_metric, event=None)

        # Set up storage state as if an event scenario was previously executed (but expired)
        context.storage.set('last_event_scenario', mock_scenario_func)
        context.storage.set('last_event_duration', 60.0)
        context.storage.set('last_event_timestamp', 1000.0)
        context.storage.set('last_event_params', {'value_range': (75.0, 100.0)})

        # when switch_scenario_by_events is called without new event but with default scenario
        result = Scenarios.switch_scenario_by_events(
            context,
            events_config={},
            default_scenario='random_in_range',
            default_scenario_data={'value_range': (0.0, 50.0)},
        )

        # then it should not use the expired scenario and fall back to default
        mock_scenario_func.assert_not_called()
        assert result == 25.0
        mock_random['uniform'].assert_called_with(0.0, 50.0)

    @allure.title('Test switch no duration limit')
    def test_switch_no_duration_limit(self, create_metric_context: Any, mock_time: MagicMock) -> None:
        '''Test switch_scenario_by_events continues indefinitely when no duration set.'''
        # given a last event scenario with no duration limit
        mock_scenario_func = MagicMock(return_value=88.0)
        mock_time.return_value = 2000.0  # 1000 seconds later

        mock_metric = MagicMock()
        mock_metric.value = 50.0
        context = create_metric_context(mock_metric=mock_metric, event=None)

        # Set up storage state as if an event scenario was previously executed (no duration limit)
        context.storage.set('last_event_scenario', mock_scenario_func)
        context.storage.set('last_event_duration', None)  # no duration limit
        context.storage.set('last_event_timestamp', 1000.0)
        context.storage.set('last_event_params', {'value_range': (80.0, 90.0)})

        # when switch_scenario_by_events is called long after the event
        result = Scenarios.switch_scenario_by_events(context, events_config={})

        # then it should still use the last event scenario
        assert result == 88.0
        mock_scenario_func.assert_called_once_with(context, value_range=(80.0, 90.0))

    @allure.title('Test switch falls back to default')
    def test_switch_falls_back_to_default(self, create_metric_context: Any, mock_random: Dict[str, MagicMock]) -> None:
        '''Test switch_scenario_by_events uses default scenario when no active event scenario.'''
        # given no active event scenario
        mock_random['uniform'].return_value = 12.5

        mock_metric = MagicMock()
        mock_metric.value = 50.0
        context = create_metric_context(mock_metric=mock_metric, event=None)

        # when switch_scenario_by_events is called with default scenario
        result = Scenarios.switch_scenario_by_events(
            context,
            events_config={},
            default_scenario='random_in_range',
            default_scenario_data={'value_range': (10.0, 20.0)},
        )

        # then it should use the default scenario
        assert result == 12.5
        mock_random['uniform'].assert_called_with(10.0, 20.0)

    @allure.title('Test switch returns random no default')
    def test_switch_returns_random_no_default(
        self, mock_emulated_metric: MagicMock, mock_random: Dict[str, MagicMock]
    ) -> None:
        '''Test switch_scenario_by_events returns random value when no default scenario provided.'''
        # given no active event scenario and no default scenario - use existing value_range from fixture
        mock_emulated_metric.get_scenario_state.return_value = None
        # fixture already has config.value_range = (0.0, 100.0)
        mock_random['uniform'].return_value = 45.0

        # when switch_scenario_by_events is called without default scenario
        # create metric context
        context = MetricContext(
            data=mock_emulated_metric.config, value=mock_emulated_metric.value, event=None, storage=StateStorage()
        )
        result = Scenarios.switch_scenario_by_events(context, events_config={})

        # then it should return random value in metric range
        assert result == 45.0
        mock_random['uniform'].assert_called_with(0.0, 100.0)

    @allure.title('Test switch event resets to default')
    def test_switch_event_resets_to_default(
        self, create_metric_context: Any, mock_random: Dict[str, MagicMock]
    ) -> None:
        '''Test switch_scenario_by_events resets to default when event has no scenario.'''
        # given event configuration without scenario (just resets)
        events_config: Dict[str, Dict[str, Any]] = {'reset_event': {}}  # no scenario key
        mock_random['uniform'].return_value = 30.0

        mock_metric = MagicMock()
        mock_metric.value = 50.0
        mock_event = MagicMock(spec=Event)
        mock_event.name = 'reset_event'
        mock_event.timestamp = 1000.0
        context = create_metric_context(mock_metric=mock_metric, event=mock_event)

        # when switch_scenario_by_events is called with reset event
        result = Scenarios.switch_scenario_by_events(
            context,
            events_config=events_config,
            default_scenario='random_in_range',
            default_scenario_data={'value_range': (20.0, 40.0)},
        )

        # then it should reset and use default scenario
        assert context.storage.get('last_event_scenario') is None
        assert context.storage.get('last_event_duration') is None
        assert context.storage.get('last_event_timestamp') is None
        assert result == 30.0

    @allure.title('Test switch handles scenario errors')
    def test_switch_handles_scenario_errors(
        self, create_metric_context: Any, mock_random: Dict[str, MagicMock]
    ) -> None:
        '''Test switch_scenario_by_events handles errors in scenario execution gracefully.'''
        # given event configuration with invalid scenario that will raise error
        events_config = {
            'error_event': {
                'scenario': 'nonexistent_scenario',  # this will cause AttributeError
                'scenario_data': {},
            }
        }
        # fixture already has config.value_range = (0.0, 100.0)
        mock_random['uniform'].return_value = 50.0

        mock_metric = MagicMock()
        mock_metric.value = 50.0
        mock_metric.config.value_range = (0.0, 100.0)
        mock_event = MagicMock(spec=Event)
        mock_event.name = 'error_event'
        context = create_metric_context(mock_metric=mock_metric, event=mock_event)

        # when switch_scenario_by_events is called with invalid scenario
        result = Scenarios.switch_scenario_by_events(context, events_config=events_config)

        # then it should handle the error and return random value
        assert result == 50.0
        mock_random['uniform'].assert_called_with(0.0, 100.0)

    @allure.title('Test switch handles last scenario errors')
    def test_switch_handles_last_scenario_errors(
        self, create_metric_context: Any, mock_random: Dict[str, MagicMock], mock_time: MagicMock
    ) -> None:
        '''Test switch_scenario_by_events handles errors in last scenario execution gracefully.'''

        # given a last event scenario that will raise an error
        def error_scenario(context: MetricContext, **kwargs: Any) -> float:
            raise ValueError('Test error in scenario')

        mock_random['uniform'].return_value = 42.0
        mock_time.return_value = 1500.0  # 500 seconds later

        mock_metric = MagicMock()
        mock_metric.value = 50.0
        context = create_metric_context(mock_metric=mock_metric, event=None)

        # Set up storage state with error scenario
        context.storage.set('last_event_scenario', error_scenario)
        context.storage.set('last_event_duration', None)
        context.storage.set('last_event_timestamp', 1000.0)
        context.storage.set('last_event_params', {})

        # when switch_scenario_by_events is called and error occurs
        result = Scenarios.switch_scenario_by_events(
            context,
            events_config={},
            default_scenario='random_in_range',
            default_scenario_data={'value_range': (40.0, 45.0)},
        )

        # then it should handle the error gracefully and return default
        assert result == 42.0
        mock_random['uniform'].assert_called_with(40.0, 45.0)

    @allure.title('Test switch complex event scenario')
    def test_switch_complex_event_scenario(
        self, create_metric_context: Any, mock_time: MagicMock, mock_asyncio_create_task: Any
    ) -> None:
        '''Test switch_scenario_by_events with complex scenario that has state.'''
        # given event with feature_toggle scenario
        events_config = {
            'feature_event': {
                'scenario': 'feature_toggle',
                'scenario_data': {
                    'start_time': 0.0,
                    'duration': 30.0,
                    'interval': 10.0,
                    'on_value': 1.0,
                    'off_value': 0.0,
                },
                'duration': 120.0,
            }
        }
        mock_time.return_value = 1000.0

        mock_metric = MagicMock()
        mock_metric.value = 50.0
        mock_event = MagicMock(spec=Event)
        mock_event.name = 'feature_event'
        context = create_metric_context(mock_metric=mock_metric, event=mock_event)

        # when switch_scenario_by_events is called with complex scenario
        result = Scenarios.switch_scenario_by_events(context, events_config=events_config)

        # then it should execute the feature_toggle scenario and set up state
        assert isinstance(result, (int, float))
        assert context.storage.get('last_event_scenario') is not None
        assert context.storage.get('last_event_timestamp') == 1000.0
        assert context.storage.get('last_event_duration') == 120.0
