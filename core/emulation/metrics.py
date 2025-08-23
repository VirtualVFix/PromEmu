# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '09/08/2025 00:00'

import time
import asyncio
from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from app_config import AppConfig
from core.logger import getLogger
from .storage import StateStorage
from .events import Event, EmulatorEventBus

VALUE_DECIMAL_PLACES = 2  # decimal places for metric values


class MetricType(Enum):
    '''Metric types supported by the system.'''

    GAUGE = 'gauge'
    COUNTER = 'counter'
    HISTOGRAM = 'histogram'


@dataclass(frozen=True)
class MetricConfig:
    '''Configuration for a metric.'''

    name: str  # name of the metric
    metric_type: MetricType = MetricType.GAUGE  # type of the metric
    value_range: tuple[float, float] = (0.0, 100.0)  # range of possible values
    init_value: Optional[float] = None  # initial value
    units: str = ''  # units of measurement
    start_time: float = 0.0  # start time for the metric
    ttl: float = float('inf')  # ttl for the metric
    update_interval: float = 10.0  # interval for generating new values
    listen_events: List[str] = field(default_factory=list)  # event listeners
    linked_metrics: List[str] = field(default_factory=list)  # linked metrics
    scenario: Optional[Callable[..., Optional[float]]] = (
        None  # scenario function for custom value generation with various arguments
    )
    scenario_data: Dict[str, Any] = field(default_factory=dict)  # data for scenario functions
    description: str = ''  # description of the metric for Prometheus


@dataclass(frozen=True)
class MetricContext:
    '''Metric context for scenarios.'''

    data: MetricConfig  # metric config
    value: Optional[float] = None  # metric value
    event: Optional[Event] = None  # event that triggered this metric
    timestamp: float = time.time()  # timestamp of the metric
    storage: StateStorage = field(default_factory=StateStorage)  # storage for metric state
    links: Dict[str, 'MetricContext'] = field(default_factory=dict)  # links to other metrics


class EmulatedMetric:
    '''Represents a single emulated metric.'''

    def __init__(self, config: MetricConfig):
        self.log = getLogger(self.__class__.__name__)
        self._value: Optional[float] = config.init_value
        self._config: MetricConfig = config
        self._is_active: bool = False
        self._start_time: float = time.time() + config.start_time
        self._last_update: float = 0.0
        self._linked_metrics: Dict[str, EmulatedMetric] = {}
        self._scenario_state: StateStorage = StateStorage()

        # subscribe events
        for event_name in config.listen_events:
            asyncio.create_task(self._subscribe_to_event(event_name))

    @property
    def value(self) -> Optional[float]:
        '''Return the current value of the metric.'''
        return self._value

    @property
    def config(self) -> MetricConfig:
        '''Return the configuration of the metric.'''
        return self._config

    @property
    def scenario_state(self) -> StateStorage:
        '''Return the scenario state storage of the metric.'''
        return self._scenario_state

    @property
    def is_active(self) -> bool:
        '''Return the active state of the metric.'''
        return self._is_active

    def add_linked_metric(self, metric: 'EmulatedMetric') -> None:
        '''
        Add a linked metric to the metric.

        Args:
            metric: the metric to link
        '''
        self._linked_metrics[metric.config.name] = metric

    async def _subscribe_to_event(self, event_name: str) -> None:
        '''
        Subscribe to events.

        Args:
            event_name: the event to subscribe to
        '''
        await EmulatorEventBus.subscribe(event_name, self._handle_event)
        self.log.debug(f'Subscribed to event: <{event_name}> for metric <{self.config.name}>')

    async def _handle_event(self, event: Event) -> None:
        '''
        Handle incoming events.

        Args:
            event: the event to handle
        '''
        self.log.debug(f'Metric <{self.config.name}> received event: <{event.name}/{event.source}>')
        await self.update_value(event)

    def _build_metric_context(self, event: Optional[Event] = None) -> MetricContext:
        '''
        Build metric context for scenario.

        Args:
            event: the event to build context for

        Returns:
            MetricContext: the metric context
        '''
        links = {}
        # build linked metrics context
        for name, metric in self._linked_metrics.items():
            links[name] = MetricContext(
                value=metric.value,
                event=event,
                data=metric.config,
                timestamp=time.time(),
                storage=metric._scenario_state,
            )
        # build metric context
        return MetricContext(
            value=self.value,
            event=event,
            data=self.config,
            timestamp=time.time(),
            links=links,
            storage=self._scenario_state,
        )

    async def _update_value_by_scenario(self, event: Optional[Event] = None) -> Optional[float]:
        '''
        Update metric value by scenario.

        Args:
            event: the event that triggered the update

        Returns:
            Optional[float]: the new metric value
        '''
        if self.config.scenario:
            try:
                context = self._build_metric_context(event)
                value = self.config.scenario(context, **self.config.scenario_data)
                if event:
                    self.log.debug(
                        f'Metric <{self.config.name}> value updated to <{self.value}{self.config.units}> '
                        f'by event <{event.name}/{event.source}>'
                    )
                return value
            except Exception as e:
                if AppConfig.DEBUG_MODE:
                    self.log.exception(f'Error in scenario for metric <{self.config.name}>: <{e}>')
                else:
                    self.log.error(f'Error in scenario for metric <{self.config.name}>: <{e}>')
        return self.value

    async def update_value(self, event: Optional[Event] = None) -> Optional[float]:
        '''
        Generate a new metric value.

        Args:
            event: the event that triggered the update

        Returns:
            Optional[float]: the new metric value
        '''
        # skip time check if event trigered
        if event is None:
            current_time = time.time()
            if current_time < self._start_time:
                return None

            if self.config.ttl != float('inf'):
                if current_time > self._start_time + self.config.ttl:
                    return None

            # check update interval
            if current_time - self._last_update < self.config.update_interval:
                return self.value

            self._last_update = current_time

        # call scenario if defined
        self._value = await self._update_value_by_scenario(event)
        if self._value is not None:
            # check value range
            if self._value < self.config.value_range[0]:
                self._value = self.config.value_range[0]
            elif self._value > self.config.value_range[1]:
                self._value = self.config.value_range[1]
        # cut value to 2 decimal places
        self._value = round(self._value, VALUE_DECIMAL_PLACES) if self._value is not None else None
        return self.value
