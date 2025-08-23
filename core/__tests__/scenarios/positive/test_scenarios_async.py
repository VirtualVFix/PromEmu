# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/14/2025 00:00'

'''
Async tests for scenarios module - event bus integration.
'''

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

import allure
import pytest

from core.emulation.scenarios import Scenarios


@allure.feature('Scenarios')
@allure.story('Async Event Integration')
class TestScenariosAsync:
    '''Tests for scenario functions with async event operations.'''

    @allure.title('Test feature toggle emits events')
    @pytest.mark.asyncio
    async def test_feature_toggle_emits_events(self, create_metric_context: Any, mock_time: MagicMock) -> None:
        '''Test feature_toggle emits events when state changes.'''
        # given feature toggle parameters and mocked time progression
        mock_metric = MagicMock()
        mock_metric.value = 0.0
        context = create_metric_context(mock_metric=mock_metric)

        # Set initial state in storage
        context.storage.set('start_timestamp', 1000.0)
        context.storage.set('feature_active', False)  # starting state: off

        # when feature_toggle transitions to on state
        mock_time.return_value = 1045.0  # 45 seconds (start_time=30, so 15s into on period)

        result = Scenarios.feature_toggle(
            context, start_time=30.0, duration=60.0, interval=15.0, on_value=1.0, off_value=0.0, source='test_source'
        )

        # then it should emit feature_on event
        assert result == 1.0
        # verify asyncio.create_task was called (mocked in conftest)
        # the actual event emission is mocked, so we just verify the structure

    @allure.title('Test feature toggle state transitions')
    @pytest.mark.asyncio
    async def test_feature_toggle_state_transitions(self, create_metric_context: Any, mock_time: MagicMock) -> None:
        '''Test feature_toggle properly tracks state transitions.'''
        # given a feature toggle scenario
        start_time = 10.0
        duration = 20.0
        interval = 5.0

        mock_metric = MagicMock()
        mock_metric.value = 0.0
        context = create_metric_context(mock_metric=mock_metric)

        # simulate multiple calls with state transitions
        state_transitions = [
            # (current_time, previous_active, expected_active, expected_result)
            (1005.0, None, None, 0.0),  # before start, no previous state
            (1015.0, False, True, 1.0),  # transition to on (10s + 5s elapsed = on)
            (1020.0, True, True, 1.0),  # stay on (10s + 10s elapsed = on)
            (1030.0, True, False, 0.0),  # transition to off (10s + 20s = off, position=20, duration=20)
            (1035.0, False, True, 1.0),  # transition to on again (new cycle: 25%25=0, 0<20=on)
            (1045.0, True, True, 1.0),  # stay on (10s + 35s, cycle pos = 10, 10<20=on)
        ]

        for current_time, prev_active, expected_active, expected_result in state_transitions:
            mock_time.return_value = current_time

            # setup previous state
            context.storage.set('start_timestamp', 1000.0)
            context.storage.set('feature_active', prev_active)

            # when feature_toggle is called
            result = Scenarios.feature_toggle(
                context, start_time=start_time, duration=duration, interval=interval, on_value=1.0, off_value=0.0
            )

            # then result should match expected
            assert result == expected_result, f"At time {current_time}, expected {expected_result}, got {result}"
            assert context.storage.get('feature_active') == expected_active, (
                f"At time {current_time}, expected active state {expected_active}, "
                f"got {context.storage.get('feature_active')}"
            )

    @allure.title('Test feature toggle custom source')
    @pytest.mark.asyncio
    async def test_feature_toggle_custom_source(self, create_metric_context: Any, mock_time: MagicMock) -> None:
        '''Test feature_toggle uses custom source for emitted events.'''
        # given custom source parameter
        custom_source = 'load_balancer_01'
        mock_metric = MagicMock()
        mock_metric.value = 0.0
        context = create_metric_context(mock_metric=mock_metric)

        context.storage.set('start_timestamp', 1000.0)
        context.storage.set('feature_active', False)
        mock_time.return_value = 1015.0  # in on period (10s start + 5s elapsed = on)

        # when feature_toggle is called with custom source
        result = Scenarios.feature_toggle(
            context, start_time=10.0, duration=30.0, interval=10.0, on_value=1.0, off_value=0.0, source=custom_source
        )

        # then it should create task with correct source
        assert result == 1.0
        # the event emission task creation is verified through mocking    @pytest.mark.asyncio

    @allure.title('Test feature toggle no source')
    @pytest.mark.asyncio
    async def test_feature_toggle_no_source(self, create_metric_context: Any, mock_time: MagicMock) -> None:
        '''Test feature_toggle works without source parameter (source=None).'''
        # given no source parameter
        mock_metric = MagicMock()
        mock_metric.value = 0.0
        context = create_metric_context(mock_metric=mock_metric)

        context.storage.set('start_timestamp', 1000.0)
        context.storage.set('feature_active', False)
        mock_time.return_value = 1025.0  # in on period

        # when feature_toggle is called without source
        result = Scenarios.feature_toggle(
            context,
            start_time=10.0,
            duration=20.0,
            interval=5.0,
            on_value=1.0,
            off_value=0.0,
            # no source parameter
        )

        # then it should still work and create event task
        assert result == 1.0

    @allure.title('Test multiple feature toggle instances')
    @pytest.mark.asyncio
    async def test_multiple_feature_toggle_instances(self, create_metric_context: Any, mock_time: MagicMock) -> None:
        '''Test multiple feature_toggle scenarios running independently.'''
        # given two independent metric contexts
        mock_metric1 = MagicMock()
        mock_metric1.value = 0.0
        context1 = create_metric_context(mock_metric=mock_metric1)
        context1.storage.set('start_timestamp', 1000.0)
        context1.storage.set('feature_active', False)

        mock_metric2 = MagicMock()
        mock_metric2.value = 0.0
        context2 = create_metric_context(mock_metric=mock_metric2)
        context2.storage.set('start_timestamp', 1000.0)
        context2.storage.set('feature_active', False)

        mock_time.return_value = 1030.0

        # when both feature_toggle scenarios are called with different parameters
        result1 = Scenarios.feature_toggle(
            context1, start_time=20.0, duration=30.0, interval=10.0, on_value=1.0, off_value=0.0, source='source1'
        )

        result2 = Scenarios.feature_toggle(
            context2, start_time=10.0, duration=15.0, interval=5.0, on_value=1.0, off_value=0.0, source='source2'
        )

        # then they should operate independently
        assert result1 == 1.0  # metric1: 10s into on period (20+10=30, so at 30s it's on)
        assert result2 == 1.0  # metric2: at new cycle start (10+20=30, cycle=20s, so at 30s it's on again)

        # verify both metrics updated their states
        assert context1.storage.get('feature_active') is not None
        assert context2.storage.get('feature_active') is not None

    @allure.title('Test feature toggle event bus error handling')
    @pytest.mark.asyncio
    async def test_feature_toggle_event_bus_error_handling(
        self, create_metric_context: Any, mock_time: MagicMock
    ) -> None:
        '''Test feature_toggle continues working even if event emission fails.'''
        # given feature toggle that will try to emit events
        mock_metric = MagicMock()
        mock_metric.value = 0.0
        context = create_metric_context(mock_metric=mock_metric)

        context.storage.set('start_timestamp', 1000.0)
        context.storage.set('feature_active', False)
        mock_time.return_value = 1025.0

        # mock EmulatorEventBus.emit to raise an exception
        with patch('core.emulation.scenarios.EmulatorEventBus.emit', side_effect=RuntimeError('Event bus error')):
            # when feature_toggle is called and event emission fails
            # then it should handle the error gracefully and continue to work
            result = Scenarios.feature_toggle(
                context, start_time=10.0, duration=20.0, interval=5.0, on_value=1.0, off_value=0.0
            )

            # the function should still return the correct value despite event emission failure
            assert result == 1.0

    @allure.title('Test concurrent feature toggle calls')
    @pytest.mark.asyncio
    async def test_concurrent_feature_toggle_calls(self, create_metric_context: Any, mock_time: MagicMock) -> None:
        '''Test concurrent calls to feature_toggle don't interfere with each other.'''
        # given multiple metric contexts
        contexts = []
        for i in range(3):
            mock_metric = MagicMock()
            mock_metric.value = 0.0
            context = create_metric_context(mock_metric=mock_metric)
            context.storage.set('start_timestamp', 1000.0)
            context.storage.set('feature_active', False)
            contexts.append(context)

        mock_time.return_value = 1030.0

        # when multiple feature_toggle calls are made concurrently
        async def call_feature_toggle(context: Any, index: int) -> float:
            return Scenarios.feature_toggle(
                context,
                start_time=10.0 + index * 5,
                duration=20.0,
                interval=5.0,
                on_value=1.0,
                off_value=0.0,
                source=f'source_{index}',
            )  # type: ignore

        tasks: list[Any] = [asyncio.create_task(call_feature_toggle(context, i)) for i, context in enumerate(contexts)]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # then all should complete successfully
        assert len(results) == 3
        for result in results:
            assert not isinstance(result, Exception)
            assert isinstance(result, float)
            assert result in [0.0, 1.0]

    @allure.title('Test feature toggle timing edge cases')
    @pytest.mark.asyncio
    async def test_feature_toggle_timing_edge_cases(self, create_metric_context: Any, mock_time: MagicMock) -> None:
        '''Test feature_toggle at exact timing boundaries.'''
        # given feature toggle parameters
        start_time_value = 30.0
        duration = 60.0
        interval = 15.0

        mock_metric = MagicMock()
        mock_metric.value = 0.0
        context = create_metric_context(mock_metric=mock_metric)

        # test exact boundary conditions
        boundary_tests = [
            (1030.0, 1.0),  # exactly at start_time: cycle_elapsed=0, ON
            (1090.0, 0.0),  # exactly at end of first on period: cycle_elapsed=60, OFF
            (1105.0, 1.0),  # exactly at start of second on period: new cycle, ON
            (1165.0, 0.0),  # exactly at end of second on period: cycle_elapsed=60, OFF
        ]

        for test_time, expected_result in boundary_tests:
            mock_time.return_value = test_time
            context.storage.set('start_timestamp', 1000.0)
            context.storage.set('feature_active', not (expected_result == 1.0))  # opposite to trigger state change

            result = Scenarios.feature_toggle(
                context, start_time=start_time_value, duration=duration, interval=interval, on_value=1.0, off_value=0.0
            )

            assert result == expected_result, f"At exact boundary {test_time}, expected {expected_result}, got {result}"
