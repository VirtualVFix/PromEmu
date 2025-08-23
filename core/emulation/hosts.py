# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '09/08/2025 00:00'

import time
import random
import asyncio
from enum import Enum
from functools import partial
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, Dict, List, Tuple, Optional

from app_config import AppConfig
from core.logger import getLogger
from .events import Event, EmulatorEventBus
from .metrics import EmulatedMetric, MetricConfig, MetricType

VALUE_DECIMAL_PLACES = 2  # decimal places for metric values
DEFAULT_CHECK_INTERVAL = 10.0
# hostname generation dictionary
HOST_NAME_DICT = {
    'service': ['stress', 'worker', 'proxy'],
    'number': [f'{i:02d}' for i in range(1, 300)],
    'app': ['app'],
    'environment': ['stage'],
    'cluster': ['lgs01', 'lgs02', 'lgs03', 'lgs04', 'lgs05'],
}


class EHostEvents(Enum):
    '''Enumeration of events for emulated hosts.'''

    HOST_STARTED = 'host_started'
    HOST_STOPPED = 'host_stopped'
    METRICS_PUSHED = 'metrics_pushed'


@dataclass(frozen=True)
class HostConfig:
    '''Configuration for an emulated host.'''

    name: str  # name of the host
    host: str | None = None  # hostname
    ttl: float = 1800.0  # time to live for the host
    interval_range: Tuple[float, float] = (12.0, 17.0)  # reporting interval range
    start_time: float = 0.0  # delay before starting host emulation (in seconds)
    job_name: str = ''  # job name for Prometheus
    labels: Dict[str, str] = field(default_factory=dict)  # labels for Prometheus
    metrics: List[MetricConfig] = field(default_factory=list)  # metrics for the host
    listen_events: Dict[str, Callable] = field(default_factory=dict)  # event listeners


class EmulatedHost:
    '''Represents a single emulated host that generates metrics.'''

    def __init__(
        self,
        config: HostConfig,
        update_callback: Optional[Callable[[str, Dict[str, Any], Dict[str, str]], Awaitable[None]]] = None,
    ) -> None:
        self.log = getLogger(self.__class__.__name__)
        self._config = config
        self._is_running = False  # host is running
        self._is_pending = True  # host is pending to start
        self._host_start_time = time.time()
        self._update_callback = update_callback
        self._last_metrics_data: Dict[str, Any] = {}
        self._emulated_metrics: Dict[str, EmulatedMetric] = {}
        # create unique labels for this host
        self._labels = {
            'name': config.name,
            'host': config.host or self._generate_fake_hostname(),
            'address': self._generate_fake_ip(),
            **config.labels,
        }
        # initialize metrics
        self._init_metrics()
        # subscribe to events
        for event_name, event_handler in config.listen_events.items():
            asyncio.create_task(self._subscribe_to_event(event_name, event_handler))

        self.log.info(f'Created host <{config.name}>: {self.labels["host"]} / {self.labels["address"]}')

    @property
    def config(self) -> HostConfig:
        '''Return the host configuration.'''
        return self._config

    @property
    def labels(self) -> Dict[str, str]:
        '''Return the built host labels.'''
        return self._labels

    @property
    def is_running(self) -> bool:
        '''Return the running state of the host.'''
        return self._is_running

    @property
    def is_pending(self) -> bool:
        '''Return the pending to start state of the host.'''
        return self._is_pending

    @property
    def emulated_metrics(self) -> Dict[str, EmulatedMetric]:
        '''Return the all emulated metrics for the host.'''
        return self._emulated_metrics

    @property
    def last_metrics_data(self) -> Dict[str, Any]:
        '''Return the last metrics data for the host.'''
        return self._last_metrics_data

    def _init_metrics(self) -> None:
        '''Initialize metrics for the host and link related metrics.'''
        self._emulated_metrics = {config.name: EmulatedMetric(config) for config in self.config.metrics}
        for metric in self._emulated_metrics.values():
            # link related metrics
            if metric.config.linked_metrics:
                for linked_metric_name in metric.config.linked_metrics:
                    if linked_metric_name in self._emulated_metrics:
                        metric.add_linked_metric(self._emulated_metrics[linked_metric_name])
                        self.log.info(f'Linked metric <{linked_metric_name}> added to metric <{metric.config.name}>')
                    else:
                        self.log.warning(
                            f'Linked metric <{linked_metric_name}> not found for metric <{metric.config.name}>'
                        )

    def _generate_fake_ip(self) -> str:
        '''Generate a fake IP address for the host.'''
        return f'192.168.{random.randint(1, 30)}.{random.randint(10, 254)}'

    def _generate_fake_hostname(self) -> str:
        '''Generate a fake hostname for the host.'''
        # generate hostname by components
        service = random.choice(HOST_NAME_DICT['service'])
        number = random.choice(HOST_NAME_DICT['number'])
        app = random.choice(HOST_NAME_DICT['app'])
        environment = random.choice(HOST_NAME_DICT['environment'])
        cluster = random.choice(HOST_NAME_DICT['cluster'])
        return f'{service}{number}.{cluster}.{app}.{environment}'

    async def _subscribe_to_event(self, event_name: str, event_handler: Callable) -> None:
        '''Subscribe to a specific event and handle it.'''
        await EmulatorEventBus.subscribe(event_name, partial(self._handle_event, event_handler=event_handler))
        self.log.debug(f'Host <{self.config.name}> subscribed to event: <{event_name}>')

    async def _handle_event(self, event: Event, event_handler: Callable) -> None:
        '''Handle incoming events and call the appropriate handler.'''
        self.log.debug(f'Host <{self.config.name}> received event: <{event.name}/{event.source}>')
        try:
            result = event_handler(event)
            # handle both sync and async event handlers
            if asyncio.iscoroutine(result):
                await result
            elif asyncio.isfuture(result) or hasattr(result, '__await__'):
                await result
            # if result is a Task, we don't need to await
            elif isinstance(result, asyncio.Task):
                # if task is already running, add done callback
                result.add_done_callback(lambda t: None)
        except Exception as e:
            self.log.error(f'Error in event handler for host <{self.config.name}>: <{e}>')

    async def _update_metrics(self) -> Dict[str, Any]:
        '''Update metrics for the host.'''
        if self.is_running:
            try:
                metrics_data = {}
                for metric in self.emulated_metrics.values():
                    value = await metric.update_value()
                    if value is not None:
                        # total state for counters
                        if metric.config.metric_type == MetricType.COUNTER:
                            current_total = metric.scenario_state.get('counter_total', 0.0)
                            new_total = current_total + value
                            metric.scenario_state.set('counter_total', new_total)
                            metrics_data[metric.config.name] = new_total
                        else:
                            metrics_data[metric.config.name] = value
                return metrics_data
            except Exception as e:
                self.log.exception(f'Error generating metrics for host <{self.config.name}>: <{e}>')
        return {}

    async def _run_loop(self) -> None:
        '''Execute the main loop for the host.'''
        try:
            while self.is_running:
                # check TTL
                if time.time() - self._host_start_time > self.config.ttl:
                    self.log.info(f'Host <{self.config.name}> TTL expired, stopping')
                    break
                self._last_metrics_data = await self._update_metrics()
                # send metrics to mixer via callback
                if self._update_callback and self._last_metrics_data:
                    if asyncio.iscoroutinefunction(self._update_callback):
                        await self._update_callback(self.config.name, self.labels, self._last_metrics_data)
                    else:
                        self._update_callback(self.config.name, self.labels, self._last_metrics_data)
                    self.log.debug(f'Sent {len(self._last_metrics_data)} metrics from host <{self.config.name}>')
                # wait before next iteration
                await asyncio.sleep(random.uniform(self.config.interval_range[0], self.config.interval_range[1]))
        except asyncio.CancelledError:
            self.log.debug(f'Host <{self.config.name}> run loop cancelled')
        except Exception as e:
            self.log.error(f'Error in host <{self.config.name}> run loop: <{e}>')
        finally:
            await self.stop()

    async def start(self) -> None:
        '''Start the host core.'''
        if self._is_running:
            self.log.warning(f'Host <{self.config.name}> is already running')
            return

        # apply start delay if configured
        self._is_running = True
        if self.config.start_time > 0:
            self.log.info(f'Host <{self.config.name}> waiting {self.config.start_time:.2f}s before starting')
            await asyncio.sleep(self.config.start_time)

        self._host_start_time = time.time()
        self._task = asyncio.create_task(self._run_loop())
        await EmulatorEventBus.emit(EHostEvents.HOST_STARTED.value, {'labels': self.labels}, self.config.name)
        self.log.info(f'Started host <{self.config.name}>')

    async def stop(self) -> None:
        '''Stop the host core.'''
        if not self.is_running:
            return

        self._is_running = False
        if self._task:
            # cleanup
            for metric in self.emulated_metrics.values():
                metric.scenario_state.clean()
            # cancel task
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                self.log.debug(f'Host <{self.config.name}> run loop cancelled')

        await EmulatorEventBus.emit(EHostEvents.HOST_STOPPED.value, {'labels': self.labels}, self.config.name)
        self.log.info(f'Stopped host <{self.config.name}>')

    def get_status(self) -> Dict[str, Any]:
        '''Get current status of the host.'''
        current_time = time.time()
        status = {
            'name': self.config.name,
            'labels': self.labels,
            'is_running': self.is_running,
            'start_time': f'{self.config.start_time}s',
            'uptime': f'{round(current_time - self._host_start_time if self.is_running else 0, VALUE_DECIMAL_PLACES)}s',
            'ttl_remaining': f'{
                round(
                    max(0, self.config.ttl + self.config.start_time - (current_time - self._host_start_time)),
                    VALUE_DECIMAL_PLACES,
                )
            }s',
            'metrics_count': len(self.config.metrics),
        }

        if AppConfig.SHOW_METRICS_STATUS:
            status['metrics'] = {x.config.name: f'{x.value}{x.config.units}' for x in self.emulated_metrics.values()}
        return status
