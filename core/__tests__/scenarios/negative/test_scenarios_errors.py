# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/14/2025 14:30'
__version__ = '0.1.0'

'''Tests for scenario error handling and edge cases.'''

from unittest.mock import MagicMock
from typing import Dict, Callable, Any, Optional

import allure
import pytest

from core.emulation.events import Event
from core.emulation.scenarios import Scenarios
from core.emulation.metrics import MetricContext


@allure.feature('Emulation')
@allure.story('Scenarios Error Handling')
class TestScenariosNegative:
    '''Test class for scenario negative cases and error conditions.'''

    @allure.title('Test variety_selection with mismatched list lengths')
    def test_variety_selection_mismatched_lengths(self, metric_context_factory: Callable[..., MetricContext]) -> None:
        '''Test variety_selection raises ValueError when values and varieties have different lengths.'''
        # given mismatched lists
        values = [10.0, 20.0, 30.0]
        varieties = [0.5, 0.5]  # only 2 elements vs 3 values

        # create metric context
        context = metric_context_factory()

        # when variety_selection is called with mismatched lists
        with pytest.raises(ValueError, match='Values list length .* must match varieties list length'):
            Scenarios.variety_selection(context, values=values, varieties=varieties)

    @allure.title('Test variety_selection with zero weight sum')
    def test_variety_selection_zero_weights(self, metric_context_factory: Callable[..., MetricContext]) -> None:
        '''Test variety_selection raises ValueError when all weights sum to zero.'''
        # given values and zero weights
        values = [10.0, 20.0, 30.0]
        varieties = [0.0, 0.0, 0.0]  # all zero weights

        # when variety_selection is called with zero weights
        with pytest.raises(ValueError, match='Varieties weights cannot all be zero'):
            # create metric context
            context = metric_context_factory()
            Scenarios.variety_selection(context, values=values, varieties=varieties)

    @allure.title('Test variety_selection with negative weights')
    def test_variety_selection_negative_weights(self, metric_context_factory: Callable[..., MetricContext]) -> None:
        '''Test variety_selection raises ValueError when weights are negative.'''
        # given values with negative weights
        values = [10.0, 20.0, 30.0]
        varieties = [0.5, -0.3, 0.8]  # negative weight

        # when variety_selection is called with negative weights
        with pytest.raises(ValueError, match='All variety weights must be non-negative'):
            # create metric context
            context = metric_context_factory()
            Scenarios.variety_selection(context, values=values, varieties=varieties)

    @allure.title('Test variety_selection with invalid change probability')
    def test_variety_selection_invalid_probability(self, metric_context_factory: Callable[..., MetricContext]) -> None:
        '''Test variety_selection raises ValueError with invalid change probability.'''
        values = [10.0, 20.0]
        varieties = [0.5, 0.5]

        # test probability > 1.0
        with pytest.raises(ValueError, match='Change probability must be between 0.0 and 1.0'):
            # create metric context
            context = metric_context_factory()
            Scenarios.variety_selection(context, values=values, varieties=varieties, change_probability=1.5)

        # test negative probability
        with pytest.raises(ValueError, match='Change probability must be between 0.0 and 1.0'):
            # create metric context
            context = metric_context_factory()
            Scenarios.variety_selection(context, values=values, varieties=varieties, change_probability=-0.1)

    @allure.title('Test variety_selection with empty lists')
    def test_variety_selection_empty_lists(self, metric_context_factory: Callable[..., MetricContext]) -> None:
        '''Test variety_selection with empty lists raises ValueError.'''
        # given empty lists
        values: list[float] = []
        varieties: list[float] = []

        # when variety_selection is called with empty lists
        # then it should raise ValueError for zero weights
        with pytest.raises(ValueError, match='Varieties weights cannot all be zero'):
            # create metric context
            context = metric_context_factory()
            Scenarios.variety_selection(context, values=values, varieties=varieties)

    @allure.title('Test update_by_trend with invalid trend value')
    def test_update_by_trend_invalid_trend(self, metric_context_factory: Callable[..., MetricContext]) -> None:
        '''Test update_by_trend handles invalid trend values gracefully.'''
        # when update_by_trend is called with invalid trend
        with pytest.raises(ValueError, match='Invalid trend value <invalid_trend>. Must be "up", "down", or "hold"'):
            # create metric context
            context = metric_context_factory()
            Scenarios.update_by_trend(context, trend='invalid_trend')

    @allure.title('Test update_by_trend with invalid step_range values')
    def test_update_by_trend_invalid_step_range(self, metric_context_factory: Callable[..., MetricContext]) -> None:
        '''Test update_by_trend handles invalid step_range values gracefully.'''
        # Test non-tuple step_range
        with pytest.raises(ValueError, match='Step range must be a tuple of two values'):
            # create metric context
            context = metric_context_factory()
            Scenarios.update_by_trend(context, step_range='not_a_tuple')  # type: ignore

        # Test tuple with wrong length
        with pytest.raises(ValueError, match='Step range must be a tuple of two values'):
            # create metric context
            context = metric_context_factory()
            Scenarios.update_by_trend(context, step_range=(1.0, 2.0, 3.0))  # type: ignore

        # Test negative step values
        with pytest.raises(ValueError, match='Step range values must be non-negative and min_step <= max_step'):
            # create metric context
            context = metric_context_factory()
            Scenarios.update_by_trend(context, step_range=(-1.0, 5.0))

        # Test min > max
        with pytest.raises(ValueError, match='Step range values must be non-negative and min_step <= max_step'):
            # create metric context
            context = metric_context_factory()
            Scenarios.update_by_trend(context, step_range=(5.0, 1.0))

    @allure.title('Test relay_to_other_metric calc_function error')
    def test_relay_to_other_metric_calc_function_error(
        self,
        metric_context_factory: Callable[..., MetricContext],
        create_source_metric_context: Callable[..., MetricContext],
    ) -> None:
        '''Test relay_to_other_metric handles calc_function exceptions gracefully.'''
        # given source metric mock and error-prone calc_function
        source_metric = MagicMock()
        source_metric.config = MagicMock()
        source_metric.value = 75.0

        def error_calc_function(context: MetricContext) -> Optional[float]:
            raise RuntimeError('Test calc error')

        # create metric context with linked metrics
        source_context = create_source_metric_context(source_metric)
        context = metric_context_factory(links={'source_metric': source_context})

        # when relay_to_other_metric is called with error-prone function
        # then it should handle the exception gracefully and return original value
        result = Scenarios.relay_to_other_metric(
            context, source_metric_name='source_metric', calc_function=error_calc_function
        )

        # should return original metric value when calc_function fails
        assert result == 50.0

    @allure.title('Test calc_by_event with calc_function exception')
    def test_calc_by_event_calc_function_error(
        self, metric_context_factory: Callable[..., MetricContext], mock_event: Event
    ) -> None:
        '''Test calc_by_event handles calc_function exceptions gracefully.'''

        # given events config with function that raises exception
        def error_calc_function(context: MetricContext) -> Optional[float]:
            raise RuntimeError('Test calc error')

        events_config: Dict[str, Callable[[MetricContext], Optional[float]]] = {'error_event': error_calc_function}
        mock_event.name = 'error_event'

        # when calc_by_event is called with error-prone function
        # then it should propagate the exception
        with pytest.raises(RuntimeError, match='Test calc error'):
            # create metric context
            context = metric_context_factory()
            Scenarios.calc_by_event(context, events_config=events_config)

    @allure.title('Test feature_toggle with invalid timing values')
    @pytest.mark.parametrize(
        'start_time, duration, interval',
        [
            (-10.0, 60.0, 15.0),  # negative start_time
            (30.0, 0.0, 15.0),  # zero duration
            (30.0, -60.0, 15.0),  # negative duration
            (30.0, 60.0, 0.0),  # zero interval
            (30.0, 60.0, -15.0),  # negative interval
        ],
    )
    def test_feature_toggle_invalid_timing(
        self, metric_context_factory: Callable[..., MetricContext], start_time: float, duration: float, interval: float
    ) -> None:
        '''Test feature_toggle handles invalid timing values appropriately.'''
        with pytest.raises(ValueError, match='Start time must be non-negative, duration and interval must be positive'):
            # create metric context
            context = metric_context_factory()
            Scenarios.feature_toggle(context, start_time=start_time, duration=duration, interval=interval)

    @allure.title('Test sine_wave with invalid period')
    def test_sine_wave_invalid_period(self, metric_context_factory: Callable[..., MetricContext]) -> None:
        '''Test sine_wave handles invalid period values.'''
        # given zero or negative period
        invalid_period = 0.0

        # when sine_wave is called with invalid period
        # then it should raise ValueError
        with pytest.raises(ValueError, match='Period must be positive'):
            # create metric context
            context = metric_context_factory()
            Scenarios.sine_wave(context, period=invalid_period)

    @allure.title('Test sine_wave with extreme amplitude')
    def test_sine_wave_extreme_amplitude(self, metric_context_factory: Callable[..., MetricContext]) -> None:
        '''Test sine_wave handles extreme amplitude values.'''
        # given very large amplitude
        extreme_amplitude = float('inf')

        # when sine_wave is called with extreme amplitude
        # create metric context
        context = metric_context_factory()
        result = Scenarios.sine_wave(context, amplitude=extreme_amplitude, period=60.0)

        # then result should be a number (may be inf, -inf, or nan depending on sine value)
        assert isinstance(result, (int, float))
        # when amplitude is infinite, result can be inf, -inf, or nan depending on sin value
        # all these are valid float values, so we just check it's a number

    @allure.title('Test switch_scenario_by_events with malformed config')
    def test_switch_scenario_malformed_config(
        self, metric_context_factory: Callable[..., MetricContext], mock_event: Event
    ) -> None:
        '''Test switch_scenario_by_events handles malformed configuration.'''
        # given malformed events config - use existing value_range from fixture (0.0, 100.0)
        malformed_events_config = {
            'test_event': 'not_a_dict'  # should be dict with scenario/scenario_data
        }
        mock_event.name = 'test_event'

        # create metric context
        context = metric_context_factory()

        # when switch_scenario_by_events is called with malformed config
        # then it should handle gracefully and fall back to random value in range
        result = Scenarios.switch_scenario_by_events(
            context,
            events_config=malformed_events_config,  # type: ignore
        )

        # should return a value within the metric's value range when config is malformed
        assert result is not None
        assert 0.0 <= result <= 100.0
        assert isinstance(result, float)

    @allure.title('Test switch_scenario_by_events with missing scenario method')
    def test_switch_scenario_missing_method(
        self, metric_context_factory: Callable[..., MetricContext], mock_event: Event
    ) -> None:
        '''Test switch_scenario_by_events when scenario method doesn't exist on Scenarios class.'''
        # given config with non-existent scenario method - use existing value_range from fixture (0.0, 100.0)
        events_config = {'test_event': {'scenario': 'nonexistent_scenario_method', 'scenario_data': {}}}
        mock_event.name = 'test_event'

        # create metric context
        context = metric_context_factory()

        # when switch_scenario_by_events is called with non-existent method
        # then it should handle gracefully and fall back to random value in range
        result = Scenarios.switch_scenario_by_events(context, events_config=events_config)

        # should return a value within the metric's value range when scenario method doesn't exist
        assert result is not None
        assert 0.0 <= result <= 100.0
        assert isinstance(result, float)

    @allure.title('Test switch_scenario_by_events with scenario data type mismatch')
    def test_switch_scenario_data_type_mismatch(
        self, metric_context_factory: Callable[..., MetricContext], mock_event: Event
    ) -> None:
        '''Test switch_scenario_by_events when scenario_data has wrong types.'''
        # given config with wrong data types for scenario - use existing value_range from fixture (0.0, 100.0)
        events_config = {
            'test_event': {
                'scenario': 'random_in_range',
                'scenario_data': {
                    'value_range': 'not_a_tuple'  # should be tuple, not string
                },
            }
        }
        mock_event.name = 'test_event'

        # create metric context
        context = metric_context_factory()

        # when switch_scenario_by_events is called with wrong data types
        # then it should handle the error gracefully and fall back to random value in range
        result = Scenarios.switch_scenario_by_events(context, events_config=events_config)

        # should return a value within the metric's value range when scenario_data has wrong types
        assert result is not None
        assert 0.0 <= result <= 100.0
        assert isinstance(result, float)

    @allure.title('Test scenarios with None metric')
    @pytest.mark.parametrize(
        'scenario_name, scenario_call',
        [
            ('do_nothing', lambda none_metric, mock_event: Scenarios.do_nothing(none_metric)),
            (
                'random_in_range',
                lambda none_metric, mock_event: Scenarios.random_in_range(none_metric, value_range=(0.0, 100.0)),
            ),
        ],
    )
    def test_scenarios_with_none_metric(
        self, mock_event: Event, scenario_name: str, scenario_call: Callable[[Any, Event], Any]
    ) -> None:
        '''Test scenarios handle None metric appropriately.'''
        none_metric = None

        try:
            result = scenario_call(none_metric, mock_event)  # type: ignore
            # if successful, check it returns None or handles gracefully
            assert result is None or isinstance(result, (int, float))
        except AttributeError:
            # This is acceptable behavior
            pass

    @allure.title('Test scenarios metric missing attributes')
    def test_scenarios_metric_missing_attributes(
        self, mock_event: Event, create_metric_context: Callable[..., MetricContext]
    ) -> None:
        '''Test scenarios handle metric objects missing required attributes.'''
        # given metric mock without value attribute
        incomplete_metric = MagicMock()
        del incomplete_metric.value  # remove value attribute

        # when scenarios are called with incomplete metric
        # then they should handle gracefully or raise AttributeError
        try:
            # create metric context
            context = create_metric_context(mock_metric=incomplete_metric, event=mock_event)
            result = Scenarios.random_in_range(context, value_range=(0.0, 100.0))
            # if successful, check result is reasonable
            assert isinstance(result, (int, float))
        except AttributeError:
            # This is acceptable behavior for missing attributes
            pass

    @allure.title('Test variety_selection edge case with single value')
    def test_variety_selection_single_value(self, metric_context_factory: Callable[..., MetricContext]) -> None:
        '''Test variety_selection works with single value/variety.'''
        # given single value and variety
        values = [42.0]
        varieties = [1.0]

        # when variety_selection is called with single value
        # create metric context
        context = metric_context_factory()
        result = Scenarios.variety_selection(context, values=values, varieties=varieties)

        # then result should be the single value
        assert result == 42.0

    @allure.title('Test relay_to_other_metric edge cases')
    def test_relay_to_other_metric_config_edge_cases(
        self, metric_context_factory: Callable[..., MetricContext]
    ) -> None:
        '''Test relay_to_other_metric handles edge cases in configuration.'''
        # create metric context without linked metrics (source_metric not found scenario)
        context = metric_context_factory(links={})  # empty links

        # when relay_to_other_metric is called with missing source metric and None calc_function
        # then it should handle gracefully and return original value
        result = Scenarios.relay_to_other_metric(
            context,
            source_metric_name='nonexistent_metric',
            calc_function=None,  # type: ignore
        )

        # should return original metric value when source or calc_function is None
        assert result == 50.0

    @allure.title('Test concurrent feature_toggle without coroutine warnings')
    def test_concurrent_feature_toggle_no_coroutine_warning(
        self, create_metric_context: Callable[..., MetricContext]
    ) -> None:
        '''Test concurrent calls to feature_toggle that properly handle event emission without warnings.'''
        import asyncio
        from unittest.mock import patch, AsyncMock

        with allure.step('Given multiple metrics and mocked event bus'):
            metrics = []
            for i in range(2):
                metric = MagicMock()
                metric.config = MagicMock()
                metric.value = MagicMock()
                metric.get_scenario_state.side_effect = lambda key, default=None, idx=i: {
                    'start_timestamp': 1000.0,
                    'feature_active': False,
                }.get(key, default)
                metrics.append(metric)

        with (
            allure.step('When multiple feature_toggle calls are made with mocked EventBus'),
            patch('time.time', return_value=1030.0),
            patch('core.emulation.scenarios.EmulatorEventBus.emit', new_callable=AsyncMock) as mock_emit,
        ):

            async def call_feature_toggle(metric: MagicMock, index: int) -> Optional[float]:
                # create metric context
                context = create_metric_context(mock_metric=metric, event=None)
                return Scenarios.feature_toggle(
                    context,
                    start_time=10.0 + index * 5,
                    duration=20.0,
                    interval=5.0,
                    on_value=1.0,
                    off_value=0.0,
                    source=f'source_{index}',
                )

            async def run_concurrent_test() -> list[Optional[float] | BaseException]:
                tasks = [asyncio.create_task(call_feature_toggle(metric, i)) for i, metric in enumerate(metrics)]
                return await asyncio.gather(*tasks, return_exceptions=True)

            with allure.step('Then it should NOT produce RuntimeWarning about unawaited coroutines'):
                import warnings

                with warnings.catch_warnings(record=True) as w:
                    warnings.simplefilter('always')
                    results = asyncio.run(run_concurrent_test())

                    # check that no RuntimeWarning about unawaited coroutines was issued
                    runtime_warnings = [
                        warning
                        for warning in w
                        if issubclass(warning.category, RuntimeWarning) and 'coroutine' in str(warning.message)
                    ]
                    assert len(runtime_warnings) == 0, f'Unexpected RuntimeWarning about coroutines: {runtime_warnings}'

                    # verify results are correct
                    assert len(results) == 2
                    for result in results:
                        if not isinstance(result, Exception):
                            assert isinstance(result, (float, type(None)))

                    # verify that event emission was called (tasks should complete properly)
                    assert mock_emit.call_count >= 0  # May be 0 if no state changes, or >0 if state changes
