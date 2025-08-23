# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/09/2025 19:04'
__version__ = '0.1.0'

import time
import random
import asyncio
from typing import Any, Callable, Optional

from core.logger import getLogger
from .metrics import MetricContext
from .events import EmulatorEventBus

log = getLogger(__file__)


class Scenarios:
    '''
    Collection of predefined scenario functions.

    Scenario structure:
    - Each scenario is a static method that takes an MetricContext as a parameter
    - Scenarios can maintain state between calls using the metric's storage.
    '''

    @staticmethod
    def do_nothing(context: MetricContext) -> Optional[float]:
        '''
        Return the current metric value without any modifications.

        Args:
            context: the emulated metric instance
        '''
        return context.value

    @staticmethod
    def random_in_range(context: MetricContext, value_range: Optional[tuple[float, float]] = None) -> Optional[float]:
        '''
        Generate a random value within the specified or metric's configured range.

        Args:
            context: the emulated metric instance
            value_range: optional range for the random value, defaults to metric's configured range
        '''
        if value_range is None:
            value_range = context.data.value_range
        return random.uniform(value_range[0], value_range[1])

    @staticmethod
    def feature_toggle(
        context: MetricContext,
        start_time: float = 30.0,
        duration: float = 60.0,
        interval: float = 15.0,
        on_value: float = 1.0,
        off_value: float = 0.0,
        source: Optional[str] = None,
    ) -> Optional[float]:
        '''
        Feature toggle scenario with configurable timing and values.

        Simulates a feature flag that toggles between on and off states based on timing configuration.
        Emits events when state changes occur.

        Args:
            context: the emulated metric instance
            start_time: seconds to wait before first toggle
            duration: seconds to stay in on state
            interval: seconds between toggle cycles
            on_value: value when feature is on
            off_value: value when feature is off
            source: optional source identifier for emitted events
        '''
        current_time = time.time()

        if start_time < 0 or duration <= 0 or interval <= 0:
            raise ValueError('Start time must be non-negative, duration and interval must be positive')

        # initialize start time if not set
        if context.storage.get('start_timestamp') is None:
            context.storage.set('start_timestamp', current_time)

        start_timestamp = context.storage.get('start_timestamp')
        elapsed = current_time - start_timestamp

        # haven't reached start time yet
        if elapsed < start_time:
            return off_value

        # calculate position in cycle
        cycle_elapsed = elapsed - start_time
        cycle_length = duration + interval
        cycle_position = cycle_elapsed % cycle_length

        # determine if we're in on or off state
        is_on = cycle_position < duration
        previous_state = context.storage.get('feature_active', False)

        # emit events when state changes
        if is_on != previous_state:
            context.storage.set('feature_active', is_on)
            if is_on:
                asyncio.create_task(
                    EmulatorEventBus.emit('feature_on', data={'timestamp': current_time}, source=source)
                )
            else:
                asyncio.create_task(
                    EmulatorEventBus.emit('feature_off', data={'timestamp': current_time}, source=source)
                )

        return on_value if is_on else off_value

    @staticmethod
    def sine_wave(
        context: MetricContext,
        period: float = 300.0,
        amplitude: float = 50.0,
        offset: float = 50.0,
        phase_offset: float = 0.0,
    ) -> Optional[float]:
        '''
        Create configurable sine wave pattern based on elapsed time.

        Generates values following a mathematical sine wave pattern with configurable parameters.

        Args:
            context: the emulated metric instance
            period: period in seconds for full cycle
            amplitude: amplitude of the wave
            offset: vertical offset of the wave
            phase_offset: phase offset in radians
        '''
        import math

        if period <= 0:
            raise ValueError('Period must be positive')

        # initialize if first call
        if context.storage.get('sine_start_time') is None:
            context.storage.set('sine_start_time', time.time())

        start_time = context.storage.get('sine_start_time')
        elapsed = time.time() - start_time

        phase = (elapsed / period) * 2 * math.pi + phase_offset
        return float(offset + amplitude * math.sin(phase))

    @staticmethod
    def variety_selection(
        context: MetricContext, values: list[float], varieties: list[float], change_probability: float = 0.1
    ) -> Optional[float]:
        '''
        Select values from a list based on variety weights.

        Uses weighted random selection to choose from provided values with configurable change probability.

        Args:
            context: the emulated metric instance
            values: list of possible values to select from
            varieties: list of weights/probabilities for each value (must match values length)
            change_probability: probability of changing value each call (0.0-1.0)
        '''
        # check that both lists have equal size
        if len(values) != len(varieties):
            raise ValueError(f'Values list length <{len(values)}> must match varieties list length <{len(varieties)}>')

        # validate that all weights are non-negative
        if any(w < 0 for w in varieties):
            raise ValueError('All variety weights must be non-negative')

        # validate change_probability is in valid range
        if not 0.0 <= change_probability <= 1.0:
            raise ValueError('Change probability must be between 0.0 and 1.0')

        # normalize varieties to ensure they sum to 1.0
        total_weight = sum(varieties)
        if total_weight == 0:
            raise ValueError('Varieties weights cannot all be zero')

        normalized_varieties = [w / total_weight for w in varieties]

        # initialize with first value if not set
        current_index = context.storage.get('variety_index', 0)

        # randomly change value based on probability
        if random.random() < change_probability:
            # weighted random selection
            rand_value = random.random()
            cumulative = 0.0
            for i, weight in enumerate(normalized_varieties):
                cumulative += weight
                if rand_value <= cumulative:
                    current_index = i
                    break

            context.storage.set('variety_index', current_index)

        return float(values[current_index])

    @staticmethod
    def switch_scenario_by_events(
        context: MetricContext,
        events_config: dict[str, dict[str, Any]],
        default_scenario: Optional[str] = None,
        default_scenario_data: Optional[dict[str, Any]] = None,
    ) -> Optional[float]:
        '''
        Switch scenario based on event triggers.

        Default scenario is used when no event matches or when no new event triggers a new scenario.
        Switched scenario is stored in the metric's scenario state and used until its duration expires if set
        or it's reset by another event.

        Args:
            context: the emulated metric instance
            events_config: mapping of event names to configuration dictionaries
                Each config can contain:
                - 'scenario': str - name of scenario to execute
                - 'scenario_data': dict - parameters for the scenario
                - 'duration': float - seconds to keep using this event's scenario, then switch to default scenario
            default_scenario: name of scenario to execute when no event matches
            default_scenario_data: parameters for the default scenario
        '''
        if default_scenario_data is None:
            default_scenario_data = {}

        current_time = time.time()

        # check if we have a matching event configuration
        if context.event and events_config and context.event.name in events_config:
            event_config = events_config[context.event.name]

            # execute event-specific scenario if specified
            if 'scenario' in event_config:
                scenario_name = event_config['scenario']
                scenario_data = event_config.get('scenario_data', {})
                scenario_duration = event_config.get('duration')

                # store last triggered event scenario info
                context.storage.set('last_event_params', scenario_data)
                context.storage.set('last_event_timestamp', current_time)
                if scenario_duration is not None:
                    context.storage.set('last_event_duration', float(scenario_duration))
                else:
                    context.storage.set('last_event_duration', None)

                # get scenario function - handle both string names and callable objects
                scenario_func = None
                if isinstance(scenario_name, str) and hasattr(Scenarios, scenario_name):
                    scenario_func = getattr(Scenarios, scenario_name)
                elif callable(scenario_name):
                    scenario_func = scenario_name

                if scenario_func:
                    try:
                        result = scenario_func(context, **scenario_data)
                        context.storage.set('last_event_scenario', scenario_func)
                        return float(result)  # type: ignore
                    except Exception as e:
                        log.error(f"Error occurred while executing scenario '{scenario_name}': {e}")
                        return random.uniform(context.data.value_range[0], context.data.value_range[1])
            else:
                # reset to default scenario
                context.storage.set('last_event_scenario', None)
                context.storage.set('last_event_duration', None)
                context.storage.set('last_event_timestamp', None)

        # check if we should use last triggered event scenario
        last_event_scenario = context.storage.get('last_event_scenario')
        last_event_duration = context.storage.get('last_event_duration')
        last_event_timestamp = context.storage.get('last_event_timestamp')

        if (
            last_event_scenario
            and last_event_timestamp
            and (last_event_duration is None or current_time - last_event_timestamp <= last_event_duration)
        ):
            last_event_params = context.storage.get('last_event_params', {})
            try:
                return float(last_event_scenario(context, **last_event_params))
            except Exception as e:
                log.error(f"Error occurred while executing last event scenario '{last_event_scenario}': {e}")

        # execute default scenario
        if default_scenario:
            if hasattr(Scenarios, default_scenario):
                scenario_func = getattr(Scenarios, default_scenario)
                try:
                    result = scenario_func(context, **default_scenario_data)
                    return float(result)
                except Exception as e:
                    log.error(f"Error occurred while executing default scenario '{default_scenario}': {e}")

        # return random value in metric's current value range
        return random.uniform(context.data.value_range[0], context.data.value_range[1])

    @staticmethod
    def time_duration(context: MetricContext) -> float:
        '''
        Calculate elapsed time since metric initialization.

        Returns the number of seconds elapsed since the metric was first created or scenario was first called.

        Args:
            context: the metric context
        '''
        current_time = time.time()

        # initialize start time on first call
        if context.storage.get('uptime_start') is None:
            context.storage.set('uptime_start', current_time)
            return 0.0

        start_time = context.storage.get('uptime_start')
        uptime_seconds = current_time - start_time

        return float(uptime_seconds)

    @staticmethod
    def update_by_trend(
        context: MetricContext, trend: str = 'hold', step_range: tuple[float, float] = (1.0, 5.0)
    ) -> float:
        '''
        Update metric value based on trend direction within specified range.

        Accumulates values based on trend direction, maintaining state between calls.

        Args:
            context: the metric context
            trend: direction of trend - 'up', 'down', or 'hold'
            step_range: (min_step, max_step) range for up/down trend changes
        '''
        # validate step_range format
        if not isinstance(step_range, tuple) or len(step_range) != 2:
            raise ValueError('Step range must be a tuple of two values (min_step, max_step)')

        min_step, max_step = step_range
        if min_step < 0 or max_step < 0 or min_step > max_step:
            raise ValueError('Step range values must be non-negative and min_step <= max_step')

        # get accumulated value from scenario state
        accumulated_value = context.storage.get('accumulated_value', context.value)

        # value trend
        if trend == 'up':
            step = random.uniform(step_range[0], step_range[1])
        elif trend == 'down':
            step = random.uniform(-step_range[1], -step_range[0])
        elif trend == 'hold':
            step = random.uniform(-step_range[0], step_range[1])
            return float(accumulated_value + step)  # skip metric accumulation
        else:
            raise ValueError(f'Invalid trend value <{trend}>. Must be "up", "down", or "hold"')

        # accumulate the step to the current value
        new_accumulated_value = accumulated_value + step
        context.storage.set('accumulated_value', new_accumulated_value)

        return float(new_accumulated_value)

    @staticmethod
    def relay_to_other_metric(
        context: MetricContext, source_metric_name: str, calc_function: Callable[[MetricContext], Optional[float]]
    ) -> Optional[float]:
        '''
        Relay scenario that calculates value based on another metric using provided function.

        Args:
            context: the emulated metric instance
            source_metric_name: name of the source metric to calculate value from
            calc_function: function to calculate value based on source metric
        '''
        source_metric_context = context.links.get(source_metric_name, None)
        if source_metric_context:
            try:
                return calc_function(source_metric_context)
            except Exception as e:
                log.error(f'Error occurred while relaying to <{source_metric_context.data.name}> metric: {e}')
        else:
            log.error(f'Source metric <{source_metric_name}> is not provided!')
        return context.value

    @staticmethod
    def calc_by_event(
        context: MetricContext, events_config: Optional[dict[str, Callable[[MetricContext], Optional[float]]]]
    ) -> Optional[float]:
        '''
        Calculate metric value based on events.

        Args:
            context: the metric context
            events_config: configuration for event-based calculations

        Usage example:
            # count workers based on events
            workers_count_metric(
                context=context,
                events_config={
                    'worker_started': lambda value, config: value + 1,
                    'worker_stopped': lambda value, config: value - 1
                }
            )
        '''
        if context.event and events_config:
            calc_function = events_config.get(context.event.name)
            if calc_function:
                return calc_function(context)
        return context.value
