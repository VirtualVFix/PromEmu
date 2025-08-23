# You cannot modify or share anything without sacrifice.
# All rights reserved by forest fairy.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '09/08/2025 00:00'

'''Example configuration for metrics core.'''

import random
import datetime
from typing import Tuple

from core.emulation import utils
from .base import BaseEmulatorConfig
from core.emulation.mixer import MixerConfig
from core.emulation.scenarios import Scenarios
from core.emulation.events import EmulatorEventBus
from core.emulation.hosts import EHostEvents, HostConfig
from core.emulation.metrics import MetricConfig, MetricType


HOSTS_COUNT = 10
HOSTS_TTL_SEC = 1800.0  # 30 minutes
HOSTS_INTERVAL_SRANGE = (14.0, 16.0)
METRICS_INTERVAL_SEC = 10.0


class HostsLoadWithPeaksConfig(BaseEmulatorConfig):
    '''Create hosts configuration with load peaks.'''

    def __init__(self) -> None:
        super().__init__()

    def build(
        self,
        hosts_count: int = HOSTS_COUNT,
        hosts_ttl: float = HOSTS_TTL_SEC,
        hosts_interval_range: Tuple[float, float] = HOSTS_INTERVAL_SRANGE,
        metrics_interval: float = METRICS_INTERVAL_SEC,
        split_jobs: bool = False,
    ) -> MixerConfig:
        '''
        Build the configuration.

        Args:
            hosts_count: number of hosts to create
            hosts_ttl: ttl for hosts
            hosts_interval_range: interval range for hosts
            metrics_interval: interval for metrics
            split_jobs: whether to split Pushgateway jobs for hosts
        '''
        job_name = f'hosts_load_peaks_{datetime.datetime.now().isoformat().replace(":", "-")}'

        # balancer host - triggers load peaks
        root_host = HostConfig(
            name='balancer-1',
            host='stress.balancer.node01.test.stage',
            job_name=f'{job_name}_balancer' if split_jobs else job_name,
            ttl=hosts_ttl,
            interval_range=hosts_interval_range,
            labels={'environment': 'stage'},
            listen_events={
                'feature_on': lambda event: EmulatorEventBus.emit(
                    name='peak_load_start', data=event.data, source='balancer-1'
                ),
                'feature_off': lambda event: EmulatorEventBus.emit(
                    name='peak_load_end', data=event.data, source='balancer-1'
                ),
            },
            metrics=[
                MetricConfig(
                    name='heavy_task_active',
                    metric_type=MetricType.GAUGE,
                    value_range=(0.0, 1.0),
                    update_interval=metrics_interval,
                    scenario=Scenarios.feature_toggle,
                    scenario_data={'start_time': 60.0, 'duration': 90.0, 'interval': 30.0, 'source': 'balancer-1'},
                    description='Heavy computational task status (0=off, 1=on)',
                )
            ],
        )

        # worker hosts that react to load peaks
        worker_hosts = []
        for i in range(1, hosts_count + 1):
            # build metrics
            metrics = [
                # CPU
                MetricConfig(
                    name='cpu_usage_percent',
                    metric_type=MetricType.GAUGE,
                    value_range=(0.0, 100),
                    units='%',
                    update_interval=metrics_interval,
                    listen_events=['peak_load_start', 'peak_load_end'],
                    scenario=Scenarios.switch_scenario_by_events,
                    scenario_data={
                        'default_scenario': 'random_in_range',
                        'default_scenario_data': {'value_range': (5.0, 25.0)},
                        'events_config': {
                            'peak_load_start': {
                                'scenario': 'random_in_range',
                                'scenario_data': {'value_range': (75.0, 100.0)},
                            },
                            'peak_load_end': {},  # reset to default
                        },
                    },
                    description='CPU usage percentage',
                ),
                # memory
                MetricConfig(
                    name='memory_usage_bytes',
                    metric_type=MetricType.GAUGE,
                    value_range=(utils.size_to_bytes('1Gb'), utils.size_to_bytes('16Gb')),
                    init_value=utils.size_to_bytes('3Gb'),
                    units='bytes',
                    update_interval=metrics_interval,
                    listen_events=['peak_load_start', 'peak_load_end'],
                    scenario=Scenarios.switch_scenario_by_events,
                    scenario_data={
                        'default_scenario': 'update_by_trend',
                        'default_scenario_data': {
                            'trend': 'hold',
                            'step_range': (utils.size_to_bytes('50Mb'), utils.size_to_bytes('300Mb')),
                        },
                        'events_config': {
                            'peak_load_start': {
                                'scenario': 'update_by_trend',
                                'scenario_data': {
                                    'trend': 'up',
                                    'step_range': (utils.size_to_bytes('100Mb'), utils.size_to_bytes('1Gb')),
                                },
                            },
                            'peak_load_end': {
                                'scenario': 'update_by_trend',
                                'duration': 35.0,
                                'scenario_data': {
                                    'trend': 'down',
                                    'step_range': (utils.size_to_bytes('500Mb'), utils.size_to_bytes('1Gb')),
                                },
                            },
                        },
                    },
                    description='Memory usage in bytes',
                ),
                MetricConfig(
                    name='memory_usage_percent',
                    metric_type=MetricType.GAUGE,
                    value_range=(0.0, 100.0),
                    units='%',
                    update_interval=metrics_interval,
                    linked_metrics=['memory_usage_bytes'],
                    scenario=Scenarios.relay_to_other_metric,
                    scenario_data={
                        'source_metric_name': 'memory_usage_bytes',
                        'calc_function': utils.calc_percent_usage,
                    },
                    description='Memory usage percentage',
                ),
                # disk
                MetricConfig(
                    name='disk_usage_bytes',
                    metric_type=MetricType.GAUGE,
                    value_range=(utils.size_to_bytes('100Gb'), utils.size_to_bytes('200Gb')),
                    init_value=utils.size_to_bytes('100.5Gb'),
                    units='bytes',
                    update_interval=metrics_interval,
                    listen_events=['peak_load_start', 'peak_load_end'],
                    scenario=Scenarios.switch_scenario_by_events,
                    scenario_data={
                        'default_scenario': 'update_by_trend',
                        'default_scenario_data': {
                            'trend': 'hold',
                            'step_range': (utils.size_to_bytes('50Mb'), utils.size_to_bytes('100Mb')),
                        },
                        'events_config': {
                            'peak_load_start': {
                                'scenario': 'update_by_trend',
                                'scenario_data': {
                                    'trend': 'up',
                                    'step_range': (utils.size_to_bytes('1Gb'), utils.size_to_bytes('3Gb')),
                                },
                            },
                            'peak_load_end': {
                                'scenario': 'update_by_trend',
                                'duration': 60.0,
                                'scenario_data': {
                                    'trend': 'down',
                                    'step_range': (utils.size_to_bytes('1Gb'), utils.size_to_bytes('3Gb')),
                                },
                            },
                        },
                    },
                    description='Disk usage in bytes',
                ),
                MetricConfig(
                    name='disk_usage_percent',
                    metric_type=MetricType.GAUGE,
                    value_range=(0.0, 100.0),
                    units='%',
                    update_interval=metrics_interval,
                    listen_events=['peak_load_start', 'peak_load_end'],
                    linked_metrics=['disk_usage_bytes'],
                    scenario=Scenarios.relay_to_other_metric,
                    scenario_data={'source_metric_name': 'disk_usage_bytes', 'calc_function': utils.calc_percent_usage},
                    description='Disk usage percentage',
                ),
                # IO
                MetricConfig(
                    name='io_utilization_percent',
                    metric_type=MetricType.GAUGE,
                    value_range=(0.0, 100.0),
                    units='%',
                    update_interval=metrics_interval,
                    listen_events=['peak_load_start', 'peak_load_end'],
                    scenario=Scenarios.switch_scenario_by_events,
                    scenario_data={
                        'default_scenario': 'random_in_range',
                        'default_scenario_data': {'value_range': (5.0, 30.0)},
                        'events_config': {
                            'peak_load_start': {
                                'scenario': 'random_in_range',
                                'scenario_data': {'value_range': (50.0, 100.0)},
                            },
                            'peak_load_end': {},  # reset to default
                        },
                    },
                    description='IO utilization percentage',
                ),
                MetricConfig(
                    name='io_operations_per_second',
                    metric_type=MetricType.GAUGE,
                    value_range=(1000, 10000),
                    units='ops',
                    update_interval=metrics_interval,
                    linked_metrics=['io_utilization_percent'],
                    scenario=Scenarios.relay_to_other_metric,
                    scenario_data={
                        'source_metric_name': 'io_utilization_percent',
                        'calc_function': lambda x: x.value * 100,
                    },
                    description='IO operations per second',
                ),
                # network
                MetricConfig(
                    name='network_speed_mbps',
                    metric_type=MetricType.GAUGE,
                    value_range=(utils.size_to_bytes('1Mbit'), utils.size_to_bytes('100Mbit')),
                    init_value=utils.size_to_bytes('500Kbit'),
                    units='Mbps',
                    update_interval=metrics_interval,
                    listen_events=['peak_load_start', 'peak_load_end'],
                    scenario=Scenarios.switch_scenario_by_events,
                    scenario_data={
                        'default_scenario': 'random_in_range',
                        'default_scenario_data': {
                            'value_range': (utils.size_to_bytes('1Mbit'), utils.size_to_bytes('10Mbit'))
                        },
                        'events_config': {
                            'peak_load_start': {
                                'scenario': 'random_in_range',
                                'scenario_data': {
                                    'value_range': (utils.size_to_bytes('5Mbit'), utils.size_to_bytes('100Mbit'))
                                },
                            },
                            'peak_load_end': {},  # reset to default
                        },
                    },
                    description='Network speed in Mbps',
                ),
                MetricConfig(
                    name='network_packet_loss_percent',
                    metric_type=MetricType.GAUGE,
                    value_range=(0.0, 100.0),
                    units='%',
                    update_interval=metrics_interval,
                    listen_events=['peak_load_start', 'peak_load_end'],
                    scenario=Scenarios.switch_scenario_by_events,
                    scenario_data={
                        'default_scenario': 'random_in_range',
                        'default_scenario_data': {'value_range': (0.0, 3.0)},
                        'events_config': {
                            'peak_load_start': {
                                'scenario': 'random_in_range',
                                'scenario_data': {'value_range': (0.5, 25.0)},
                            },
                            'peak_load_end': {},  # reset to default
                        },
                    },
                    description='Network packet loss percentage',
                ),
                # network latency
                MetricConfig(
                    name='network_latency_ms',
                    metric_type=MetricType.GAUGE,
                    value_range=(0.0, 10000.0),
                    units='ms',
                    update_interval=metrics_interval,
                    listen_events=['peak_load_start', 'peak_load_end'],
                    scenario=Scenarios.switch_scenario_by_events,
                    scenario_data={
                        'default_scenario': 'random_in_range',
                        'default_scenario_data': {'value_range': (10.0, 150.0)},
                        'events_config': {
                            'peak_load_start': {
                                'scenario': 'random_in_range',
                                'scenario_data': {'value_range': (150.0, 1200.0)},
                            },
                            'peak_load_end': {},  # reset to default
                        },
                    },
                    description='Network latency in milliseconds',
                ),
                # GPU
                MetricConfig(
                    name='gpu_memory_usage_bytes',
                    metric_type=MetricType.GAUGE,
                    value_range=(utils.size_to_bytes('500Mb'), utils.size_to_bytes('8Gb')),
                    init_value=utils.size_to_bytes('1Gb'),
                    units='bytes',
                    update_interval=metrics_interval,
                    listen_events=['peak_load_start', 'peak_load_end'],
                    scenario=Scenarios.switch_scenario_by_events,
                    scenario_data={
                        'default_scenario': 'update_by_trend',
                        'default_scenario_data': {
                            'trend': 'hold',
                            'step_range': (utils.size_to_bytes('50Mb'), utils.size_to_bytes('200Mb')),
                        },
                        'events_config': {
                            'peak_load_start': {
                                'scenario': 'update_by_trend',
                                'scenario_data': {
                                    'trend': 'up',
                                    'step_range': (utils.size_to_bytes('50Mb'), utils.size_to_bytes('500Mb')),
                                },
                            },
                            'peak_load_end': {
                                'scenario': 'update_by_trend',
                                'duration': 65.0,
                                'scenario_data': {
                                    'trend': 'down',
                                    'step_range': (utils.size_to_bytes('50Mb'), utils.size_to_bytes('500Mb')),
                                },
                            },
                        },
                    },
                    description='GPU memory usage in bytes',
                ),
                MetricConfig(
                    name='gpu_memory_usage_percent',
                    metric_type=MetricType.GAUGE,
                    value_range=(0.0, 100.0),
                    units='%',
                    update_interval=metrics_interval,
                    linked_metrics=['gpu_memory_usage_bytes'],
                    scenario=Scenarios.relay_to_other_metric,
                    scenario_data={
                        'source_metric_name': 'gpu_memory_usage_bytes',
                        'calc_function': utils.calc_percent_usage,
                    },
                    description='GPU memory usage percentage',
                ),
                MetricConfig(
                    name='gpu_usage_percent',
                    metric_type=MetricType.GAUGE,
                    value_range=(0.0, 100.0),
                    units='%',
                    update_interval=metrics_interval,
                    listen_events=['peak_load_start', 'peak_load_end'],
                    scenario=Scenarios.switch_scenario_by_events,
                    scenario_data={
                        'default_scenario': 'random_in_range',
                        'default_scenario_data': {'value_range': (1.0, 25.0)},
                        'events_config': {
                            'peak_load_start': {
                                'scenario': 'random_in_range',
                                'scenario_data': {'value_range': (20.0, 100.0)},
                            },
                            'peak_load_end': {},  # reset to default
                        },
                    },
                    description='GPU usage percentage',
                ),
                # workers metrics
                MetricConfig(
                    name='workers_count',
                    metric_type=MetricType.GAUGE,
                    value_range=(0, 1),
                    units='unit',
                    listen_events=[EHostEvents.HOST_STARTED.value, EHostEvents.HOST_STOPPED.value],
                    scenario=Scenarios.calc_by_event,
                    scenario_data={
                        'events_config': {
                            EHostEvents.HOST_STARTED.value: lambda context: context.value + 1
                            if context.value is not None
                            else 1,
                            EHostEvents.HOST_STOPPED.value: lambda context: context.value - 1
                            if context.value is not None
                            else 0,
                        }
                    },
                    update_interval=metrics_interval,
                    description='Number of active workers',
                ),
                MetricConfig(
                    name='workers_uptime_seconds',
                    metric_type=MetricType.GAUGE,
                    value_range=(0.0, float('inf')),
                    units='seconds',
                    update_interval=metrics_interval,
                    scenario=Scenarios.time_duration,
                    description='Uptime of worker in seconds',
                ),
            ]

            # create host
            worker_host = HostConfig(
                name=f'worker-{i:02d}',
                host=f'stress.worker-{i:02d}.test.stage',
                start_time=round(random.uniform(0.0, 45.0), 2),  # random start time
                job_name=f'{job_name}_{i:02d}' if split_jobs else job_name,
                ttl=hosts_ttl,
                interval_range=hosts_interval_range,
                labels={'environment': 'stage'},
                metrics=metrics,
            )
            worker_hosts.append(worker_host)

        return MixerConfig(hosts=[root_host] + worker_hosts)
