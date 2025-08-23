# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '09/08/2025 00:00'

from typing import Tuple

from .base import BaseEmulatorConfig
from core.emulation.mixer import MixerConfig
from core.emulation.hosts import HostConfig
from core.emulation.scenarios import Scenarios
from core.emulation.metrics import MetricConfig, MetricType


HOST_TTL_SEC = 600  # 10 minutes
HOST_INTERVALS_RANGE = (14.0, 16.0)
METRICS_INTERVAL_SEC = 10.0


class SingleHostLoadConfig(BaseEmulatorConfig):
    def __init__(self) -> None:
        '''Create single host configuration with system metrics.'''

        super().__init__()

    def build(
        self,
        host_ttl: float = HOST_TTL_SEC,
        host_interval_range: Tuple[float, float] = HOST_INTERVALS_RANGE,
        metric_interval: float = METRICS_INTERVAL_SEC,
    ) -> MixerConfig:
        '''
        Build the configuration.

        Args:
            host_ttl: ttl for host
            host_interval_range: interval range for host
            metric_interval: interval for metrics
        '''
        # create metrics
        metric = [
            MetricConfig(
                name='cpu_usage_percent',
                metric_type=MetricType.GAUGE,
                init_value=50.0,
                value_range=(1.0, 100.0),
                units='%',
                update_interval=metric_interval,
                scenario=Scenarios.sine_wave,
                description='CPU usage percentage',
            ),
            MetricConfig(
                name='memory_usage_percent',
                metric_type=MetricType.GAUGE,
                init_value=50.0,
                value_range=(1.0, 100.0),
                units='%',
                update_interval=metric_interval,
                scenario=Scenarios.sine_wave,
                description='Memory usage percentage',
            ),
            MetricConfig(
                name='io_utilization_percent',
                metric_type=MetricType.GAUGE,
                init_value=50.0,
                value_range=(5.0, 100.0),
                units='%',
                update_interval=metric_interval,
                scenario=Scenarios.sine_wave,
                description='IO utilization percentage',
            ),
        ]
        # create host
        test_host = HostConfig(
            name='test-host-01',
            host='test01.app.dev.lgs01',
            ttl=host_ttl,
            interval_range=host_interval_range,
            labels={'environment': 'stage'},
            metrics=metric,
        )
        return MixerConfig(hosts=[test_host])
