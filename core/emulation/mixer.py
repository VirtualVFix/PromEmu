# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '16/08/2025 00:35'

import json
import time
import asyncio
import datetime
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from prometheus_client import CollectorRegistry, Gauge, Counter, Histogram, push_to_gateway, delete_from_gateway

from app_config import AppConfig
from core.logger import getLogger
from .events import EmulatorEventBus
from .metrics import MetricType, MetricConfig
from .hosts import EmulatedHost, HostConfig, EHostEvents

JOB_NAME_PREFIX = 'emulated_host_'


@dataclass(frozen=True)
class MixerConfig:
    '''Configuration for MetricsMixer.'''

    hosts: List[HostConfig] = field(default_factory=list)  # list of hosts to be emulated
    pushgateway_url: str = AppConfig.PUSHGATEWAY_URL  # pushgateway url
    push_interval: float = AppConfig.PUSHGATEWAY_PUSH_INTERVAL  # push interval
    default_job_name: str = (
        f'{JOB_NAME_PREFIX}{datetime.datetime.now().isoformat().replace(":", "-")}'  # default job name
    )
    cleanup_on_start: bool = AppConfig.PUSHGATEWAY_CLEANUP_ON_START  # cleanup on start
    cleanup_on_finish: bool = AppConfig.PUSHGATEWAY_CLEANUP_ON_FINISH  # cleanup on finish


class MixerError(Exception):
    '''Exception raised when mixer fails.'''

    def __init__(self, message: str):
        super().__init__(message)


class MetricsMixer:
    '''Centralized metrics mixer that handles pushgateway communication and job lifecycle.'''

    def __init__(self, config: MixerConfig):
        self.log = getLogger(self.__class__.__name__)
        self._config = config
        self._is_running = False
        # mixer TTL
        self._mixer_start_time = 0.0
        self._push_task: Optional[asyncio.Task] = None
        self._ttl = max(host.start_time + host.ttl for host in config.hosts)

        # job registries: job_name -> CollectorRegistry
        self._job_registries: Dict[str, CollectorRegistry] = {}
        # merged metrics: job_name -> metric_name -> host_name -> metric_data
        self._merged_metrics: Dict[str, Dict[str, Dict[str, Any]]] = {}
        # track hosts by job name
        self._job_hosts: Dict[str, List[EmulatedHost]] = {}
        # setup job grouping
        self._setup_job_grouping()
        self.log.info(
            f'Created MetricsMixer with {len(self._config.hosts)} hosts across {len(self._job_registries)} job groups'
        )

    @property
    def config(self) -> MixerConfig:
        '''Return the configuration of the mixer.'''
        return self._config

    @property
    def is_running(self) -> bool:
        '''Return the running state of the mixer.'''
        return self._is_running

    def _setup_job_grouping(self) -> None:
        '''Group hosts by job name and create registries.'''
        # group hosts by job name
        host_names: Dict[str, List[str]] = {}
        for host_config in self._config.hosts:
            job_name = host_config.job_name or self._config.default_job_name
            if job_name not in self._job_hosts:
                self._job_hosts[job_name] = []
                self._job_registries[job_name] = CollectorRegistry()
                self._merged_metrics[job_name] = {}
            if host_config.name not in host_names.get(job_name, []):
                # create host with callback
                self._job_hosts[job_name].append(
                    EmulatedHost(config=host_config, update_callback=self.update_metrics_by_host)
                )
                host_names[job_name] = host_names.get(job_name, []) + [host_config.name]
            else:
                raise MixerError(f'Host <{host_config.name}> already exists in job <{job_name}>')

        # log job distribution
        for job_name, hosts in self._job_hosts.items():
            self.log.info(f'Job <{job_name}>: {len(hosts)} hosts')

    def _get_job_name(self, host_config: HostConfig) -> str:
        '''Get job name for a host.'''
        return host_config.job_name or self._config.default_job_name

    def _setup_prometheus_metrics_for_job(self, job_name: str) -> None:
        '''Prometheus metrics setup by job.'''
        # check if metrics are already set up for this job
        if job_name in self._merged_metrics and len(self._merged_metrics[job_name]) > 0:
            return

        registry = self._job_registries[job_name]
        hosts = self._job_hosts[job_name]

        # collect all unique metrics across hosts in this job
        unique_metrics: Dict[str, Dict[str, Any]] = {}
        all_label_names: Set[str] = set()

        # get all metrics and labels
        for host in hosts:
            all_label_names.update(host.labels.keys())
            for name, metric in host.emulated_metrics.items():
                if name not in unique_metrics:
                    unique_metrics[name] = {'config': metric.config, 'hosts': []}
                host_list = unique_metrics[name]['hosts']
                if isinstance(host_list, list):
                    host_list.append({'host_config': host, 'labels': host.labels})

        # create Prometheus metrics in registry
        label_names = list(all_label_names)
        for metric_name, metric_info in unique_metrics.items():
            metric_config: MetricConfig = metric_info['config']
            try:
                prom_metric: Gauge | Counter | Histogram
                # GAUGE
                if metric_config.metric_type == MetricType.GAUGE:
                    prom_metric = Gauge(
                        metric_name,
                        metric_config.description or f'{metric_name} metric',
                        labelnames=label_names,
                        registry=registry,
                    )
                # COUNTER
                elif metric_config.metric_type == MetricType.COUNTER:
                    prom_metric = Counter(
                        metric_name,
                        metric_config.description or f'{metric_name} counter',
                        labelnames=label_names,
                        registry=registry,
                    )
                # HISTOGRAM
                elif metric_config.metric_type == MetricType.HISTOGRAM:
                    prom_metric = Histogram(
                        metric_name,
                        metric_config.description or f'{metric_name} histogram',
                        labelnames=label_names,
                        registry=registry,
                    )
                else:
                    raise ValueError(f'Unsupported metric type: {metric_config.metric_type}')

                # store metric reference for later updates
                if job_name not in self._merged_metrics:
                    self._merged_metrics[job_name] = {}
                if metric_name not in self._merged_metrics[job_name]:
                    self._merged_metrics[job_name][metric_name] = {}

                self._merged_metrics[job_name][metric_name]['_prom_metric'] = prom_metric
                self._merged_metrics[job_name][metric_name]['_metric_type'] = metric_config.metric_type
            except Exception as e:
                raise MixerError(f'Failed to create metric {metric_name} for job {job_name}') from e

    async def update_metrics_by_host(
        self, host_name: str, labels: Dict[str, str], metrics_data: Dict[str, Any]
    ) -> None:
        '''Metrics update callback.'''
        # find host config
        host_config = None
        for host in self.config.hosts:
            if host.name == host_name:
                host_config = host
                break

        if not host_config:
            self.log.warning(f'Host <{host_name}> not found in configuration!')
            return

        job_name = self._get_job_name(host_config)
        # ensure job metrics are setup
        self._setup_prometheus_metrics_for_job(job_name)

        # update merged metrics
        for metric_name, value in metrics_data.items():
            if metric_name in self._merged_metrics[job_name]:
                # check for duplicate metrics with same labels
                existing_hosts = [
                    h
                    for h in self._merged_metrics[job_name][metric_name].keys()
                    if h != '_prom_metric' and h != '_metric_type'
                ]

                for existing_host in existing_hosts:
                    if existing_host == host_name:
                        continue
                    existing_data = self._merged_metrics[job_name][metric_name][existing_host]
                    if existing_data.get('labels') == labels:
                        self.log.warning(
                            f'Duplicate metric <{metric_name}> with identical labels from hosts '
                            f'<{existing_host}> and <{host_name}>. This metric will be overwritten!'
                        )

                # store host metric data
                self._merged_metrics[job_name][metric_name][host_name] = {
                    'value': value,
                    'labels': labels,
                    'timestamp': time.time(),
                }

                # update Prometheus metric
                prom_metric = self._merged_metrics[job_name][metric_name]['_prom_metric']
                metric_type = self._merged_metrics[job_name][metric_name]['_metric_type']

                try:
                    if metric_type == MetricType.GAUGE:
                        prom_metric.labels(**labels).set(value)
                    elif metric_type == MetricType.COUNTER:
                        # for counters, we need to set the total value
                        prom_metric.labels(**labels)._value._value = value
                    elif metric_type == MetricType.HISTOGRAM:
                        prom_metric.labels(**labels).observe(value)
                except Exception as e:
                    self.log.error(f'Failed to update metric {metric_name} for host {host_name}: {e}')

    async def _run_loop(self) -> None:
        '''Push metrics to pushgateway main loop.'''
        try:
            while self.is_running:
                await self._push_all_jobs()
                await asyncio.sleep(self.config.push_interval)
        except asyncio.CancelledError:
            self.log.debug('Push metrics loop cancelled')
        except Exception as e:
            if AppConfig.DEBUG_MODE:
                self.log.exception(f'Error in push metrics loop: {e}')
            else:
                self.log.error(f'Error in push metrics loop: {e}')
        finally:
            await self.stop()

    async def _push_all_jobs(self) -> None:
        '''Push all job metrics to pushgateway.'''
        for job_name, registry in self._job_registries.items():
            try:
                push_to_gateway(self.config.pushgateway_url, job=job_name, registry=registry)
                # emit push event
                host_names = [host.config.name for host in self._job_hosts[job_name]]
                await EmulatorEventBus.emit(
                    EHostEvents.METRICS_PUSHED.value,
                    {
                        'job_name': job_name,
                        'hosts': host_names,
                        'metrics_count': len(self._merged_metrics.get(job_name, {})),
                    },
                    f'mixer-{job_name}',
                )
                self.log.info(f'Pushed metrics for job <{job_name}> with {len(host_names)} hosts')
            except Exception as e:
                if AppConfig.DEBUG_MODE:
                    self.log.exception(f'Failed to push metrics for job {job_name}: {e}')
                else:
                    self.log.error(f'Failed to push metrics for job {job_name}: {e}')

    async def cleanup_all_jobs(self) -> None:
        '''Clean all jobs from pushgateway.'''
        try:
            self.log.info('Cleaning up pushgateway jobs...')
            # get all existing jobs from pushgateway
            metrics_url = f"{self.config.pushgateway_url.rstrip('/')}/api/v1/metrics"

            with urllib.request.urlopen(metrics_url) as response:
                if response.status != 200:
                    self.log.warning(f'Failed to get metrics from pushgateway: status {response.status}')
                    return

                data = json.loads(response.read().decode())
                if data.get('status') != 'success':
                    self.log.warning('Pushgateway returned non-success status')
                    return

                # extract job names
                jobs = set()
                for metric_group in data.get('data', []):
                    job_name = metric_group.get('labels', {}).get('job')
                    if job_name:
                        jobs.add(job_name)

                self.log.info(f'Found {len(jobs)} jobs to cleanup: {list(jobs)}')

                # delete each job individually
                delete_count = 0
                for job_name in jobs:
                    try:
                        delete_url = (
                            f'{self.config.pushgateway_url.rstrip("/")}/metrics/job/{urllib.parse.quote(job_name)}'
                        )
                        req = urllib.request.Request(delete_url, method='DELETE')

                        with urllib.request.urlopen(req) as delete_response:
                            if delete_response.status in (200, 202):
                                delete_count += 1
                                self.log.debug(f'Deleted job: {job_name}')
                            else:
                                self.log.warning(f'Failed to delete job {job_name}: status {delete_response.status}')
                    except Exception as e:
                        if AppConfig.DEBUG_MODE:
                            self.log.exception(f'Error deleting job {job_name}: {e}')
                        else:
                            self.log.error(f'Error deleting job {job_name}: {e}')
                self.log.info(f'Cleaned {delete_count}/{len(jobs)} pushgateway jobs')
        except Exception as e:
            if AppConfig.DEBUG_MODE:
                self.log.exception(f'Failed to cleanup pushgateway: {e}')
            else:
                self.log.error(f'Failed to cleanup pushgateway: {e}')

    async def cleanup_mixer_jobs(self) -> None:
        '''Clean up only the jobs managed by this mixer.'''
        try:
            self.log.info('Cleaning up mixer jobs...')
            delete_count = 0

            for job_name in self._job_registries.keys():
                try:
                    delete_from_gateway(self.config.pushgateway_url, job=job_name)
                    delete_count += 1
                    self.log.debug(f'Cleaned up job: {job_name}')
                except Exception as e:
                    if AppConfig.DEBUG_MODE:
                        self.log.exception(f'Failed to cleanup job {job_name}: {e}')
                    else:
                        self.log.error(f'Failed to cleanup job {job_name}: {e}')

            self.log.info(f'Cleaned up {delete_count}/{len(self._job_registries)} mixer jobs')

        except Exception as e:
            if AppConfig.DEBUG_MODE:
                self.log.exception(f'Failed to cleanup mixer jobs: {e}')
            else:
                self.log.error(f'Failed to cleanup mixer jobs: {e}')

    async def start(self) -> None:
        '''Start the metrics mixer.'''
        if self.is_running:
            self.log.warning('MetricsMixer is already running')
            return

        self._is_running = True
        self._mixer_start_time = time.time()
        self.log.info('Starting MetricsMixer...')

        # cleanup on start if configured
        if self.config.cleanup_on_start:
            await self.cleanup_all_jobs()

        # start all hosts
        tasks = []
        for hosts in self._job_hosts.values():
            for host in hosts:
                tasks.append(asyncio.create_task(host.start()))
        asyncio.gather(*tasks, return_exceptions=True)

        # setup metrics for all jobs
        for job_name in self._job_registries.keys():
            self._setup_prometheus_metrics_for_job(job_name)

        # start push loop
        self._push_task = asyncio.create_task(self._run_loop())
        self.log.info(f'Started MetricsMixer with {len(self._job_registries)} job groups')

    async def run_until_complete(self) -> None:
        '''Run until TTL.'''
        await self.start()
        try:
            while self.is_running and any(
                host.is_running or host.is_pending for hosts in self._job_hosts.values() for host in hosts
            ):
                if self._mixer_start_time + self._ttl < time.time():
                    self.log.info('Mixer TTL expired, stopping')
                    break
                await asyncio.sleep(1.0)
        finally:
            await self.stop()

    async def stop(self) -> None:
        '''Stop the metrics mixer.'''
        if not self._is_running:
            return
        self._is_running = False

        # stop hosts
        self.log.info('Stopping hosts...')
        tasks = []
        for hosts in self._job_hosts.values():
            for host in hosts:
                tasks.append(asyncio.create_task(host.stop()))
        await asyncio.gather(*tasks, return_exceptions=True)

        # stop push loop
        self.log.info('Stopping MetricsMixer...')

        if self._push_task:
            self._push_task.cancel()
            try:
                await self._push_task
            except asyncio.CancelledError:
                pass

        # cleanup on finish if configured
        if self.config.cleanup_on_finish:
            await self.cleanup_mixer_jobs()

        self.log.info('MetricsMixer stopped')

    def get_status(self) -> Dict[str, Any]:
        '''Get current status of the mixer.'''
        job_status = {}
        total_hosts = 0
        total_metrics = 0

        for job_name, hosts in self._job_hosts.items():
            host_count = len(hosts)
            metrics_count = len(self._merged_metrics.get(job_name, {}))
            total_hosts += host_count
            total_metrics += metrics_count
            # jobs status
            job_status[job_name] = {
                'hosts_count': host_count,
                'metrics_count': metrics_count,
                'host_names': [host.config.name for host in hosts],
            }
            # hosts status
            if AppConfig.SHOW_HOSTS_STATUS:
                hosts_status = [host.get_status() for host in hosts]
                job_status[job_name]['hosts'] = hosts_status

        return {
            'is_running': self.is_running,
            'pushgateway_url': self.config.pushgateway_url,
            'push_interval': self.config.push_interval,
            'total_jobs': len(self._job_registries),
            'total_hosts': total_hosts,
            'active_hosts': sum(1 for host_list in self._job_hosts.values() for host in host_list if host.is_running),
            'total_metrics': total_metrics,
            'jobs': job_status,
        }
