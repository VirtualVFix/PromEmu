# Prometheus Metrics Emulator (PromEmu)

This module provides a comprehensive solution for emulating Prometheus metrics with realistic scenarios, event-driven behavior, and multi-host simulation.

> **Quick Setup**: For a complete monitoring environment, use the pre-configured Docker infrastructure in [`docker/`](docker/README.md) which includes Pushgateway, Prometheus, and Grafana with dashboards.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
  - [Install Dependencies](#install-dependencies)
  - [Basic Usage](#basic-usage)
  - [Example Output](#example-output)
- [Configuration](#configuration)
  - [Configuration Loader](#configuration-loader)
  - [Available Configurations](#available-configurations)
  - [Creating Custom Configurations](#creating-custom-configurations)
  - [Host Configuration](#host-configuration)
  - [Metric Configuration](#metric-configuration)
- [Built-in Scenarios](#built-in-scenarios)
  - [Basic Scenarios](#basic-scenarios)
  - [Wave Pattern Scenarios](#wave-pattern-scenarios)
  - [Trend-Based Scenarios](#trend-based-scenarios)
  - [Selection Scenarios](#selection-scenarios)
  - [Toggle Scenarios](#toggle-scenarios)
  - [Advanced Scenarios](#advanced-scenarios)
  - [Custom Scenario Development](#custom-scenario-development)
- [Configuration Structure](#configuration-structure)
  - [Mixer Configuration](#mixer-configuration)
  - [Host Configuration](#host-configuration-1)
  - [Metric Configuration](#metric-configuration-1)
  - [Configuration Loader Usage](#configuration-loader-usage)
  - [Environment-Specific Configurations](#environment-specific-configurations)
  - [Environment Configuration](#environment-configuration)
- [Custom Scenarios](#custom-scenarios)
- [Event System](#event-system)
- [Architecture](#architecture)
- [Pushgateway Job Management](#pushgateway-job-management)
  - [Single Job Pattern (Consolidated)](#single-job-pattern-consolidated)
  - [Multiple Jobs Pattern (Distributed)](#multiple-jobs-pattern-distributed)
  - [Job Grouping Behavior](#job-grouping-behavior)
  - [Metrics Merging and Conflict Detection](#metrics-merging-and-conflict-detection)
  - [Configuration Examples](#configuration-examples)
  - [Job Lifecycle Management](#job-lifecycle-management)
- [Infrastructure Requirements](#infrastructure-requirements)
  - [Quick Setup with Docker](#quick-setup-with-docker)
  - [Manual Setup](#manual-setup)
- [Troubleshooting](#troubleshooting)
  - [Connection Issues](#connection-issues)
  - [High CPU Usage](#high-cpu-usage)
  - [Missing Metrics](#missing-metrics)
- [Examples](#examples)
  - [Available Configurations](#available-configurations-1)
  - [Using Different Configuration Classes](#using-different-configuration-classes)
  - [Configuration Loader API](#configuration-loader-api)

## Features

- **Dynamic Configuration Loading**: Load any configuration file from the `configs` directory
- **Event-driven Architecture**: Hosts can emit and listen to events for coordinated behavior
- **Async Host Isolation**: Each host runs in its own async task
- **Flexible Metric Scenarios**: Predefined and custom scenario functions
- **Prometheus Integration**: Direct push to Pushgateway
- **Configurable TTL**: Hosts have individual time-to-live settings
- **Realistic Host Simulation**: Fake IP addresses and host labels

## Quick Start

### Install Dependencies

First, install the required dependencies:

```bash
pip install prometheus-client
```

### Basic Usage

```bash
# list available configurations
PYTHONPATH=. python main.py --list-configs

# run with a specific configuration
PYTHONPATH=. python main.py --config hosts_load_with_peaks

# run with specific class from config
PYTHONPATH=. python main.py --config hosts_load_with_peaks --class HostsLoadWithPeaksConfig

# run with config arguments (passed to build method)
PYTHONPATH=. python main.py --config hosts_load_with_peaks --config-args hosts_count=5 hosts_ttl=600

# custom pushgateway URL
PYTHONPATH=. python main.py --config single_host_load --pushgateway-url http://your-pushgateway:9091

# custom push interval
PYTHONPATH=. python main.py --config single_host_load --push-interval 10.0

# custom status report interval (default: 30 seconds)
PYTHONPATH=. python main.py --config single_host_load --status-interval 10
```

### Example Output
```
python main.py --config hosts_load_with_peaks --config-args hosts_ttl=160 hosts_count=5
18:10:57 INFO/main: Loading configuration: <hosts_load_with_peaks>
18:10:57 INFO/main: Config arguments: {'hosts_ttl': 160, 'hosts_count': 5}
...
18:10:57 INFO/EmulatedHost: Created host <worker-05>: stress.worker-05.test.stage / 192.168.21.118
18:10:57 INFO/MetricsMixer: Job <hosts_load_peaks_2025-08-19T18-10-57.288633>: 6 hosts
18:10:57 INFO/MetricsMixer: Created MetricsMixer with 6 hosts across 1 job groups

18:10:57 INFO/main: ------------------------------
18:10:57 INFO/main: Starting metrics emulation with <6> hosts
18:10:57 INFO/main: Configuration: <hosts_load_with_peaks>
18:10:57 INFO/main: Config arguments: {'hosts_ttl': 160, 'hosts_count': 5}
18:10:57 INFO/main: Pushgateway URL: <http://localhost:9091>
18:10:57 INFO/main: Press Ctrl+C to stop
18:10:57 INFO/main: ------------------------------

18:10:57 INFO/MetricsMixer: Starting MetricsMixer...
...
18:11:27 INFO/main: --- Status Report ---
18:11:27 INFO/main: Running
18:11:27 INFO/main: Hosts: <6/6> active
18:11:27 INFO/main: Status: {
  "is_running": true,
  "pushgateway_url": "http://localhost:9091",
  "push_interval": 15.0,
  "total_jobs": 1,
  "total_hosts": 6,
  "active_hosts": 6,
  "total_metrics": 16,
  "jobs": {
    "hosts_load_peaks_2025-08-19T18-10-57.288633": {
      "hosts_count": 6,
      "metrics_count": 16,
      "host_names": [
        "balancer-1",
        "worker-01",
        "worker-02",
        "worker-03",
        "worker-04",
        "worker-05"
      ],
      "hosts": [
        {
          "name": "balancer-1",
          "labels": {
            "name": "balancer-1",
            "host": "stress.balancer.node01.test.stage",
            "address": "192.168.27.10",
            "environment": "stage"
          },
          "is_running": true,
          "start_time": "0.0s",
          "uptime": "30.0s",
          "ttl_remaining": "130.0s",
          "metrics_count": 1
        },
        ...
      ]
    }
  }
}
...
```

## Configuration

### Configuration Loader

The emulation system uses a dynamic configuration loader that works with class-based configurations inheriting from `BaseEmulatorConfig`:

```python
from core.emulation.loader import load_config

# load configuration with auto-detection (finds classes ending with 'Config')
config = load_config('hosts_load_with_peaks')

# load with specific class
config = load_config('hosts_load_with_peaks', 'HostsLoadWithPeaksConfig')

# pass parameters to config build method
config = load_config('hosts_load_with_peaks', hosts_count=5, hosts_ttl=300)
```

### Available Configurations

Use `PYTHONPATH=. python main.py --list-configs` to see all available configurations:

- `hosts_load_with_peaks`: Complex multi-host scenario with coordinated load peaks (default: 10 hosts, 15 min)
- `single_host_load`: Simple single-host configuration for testing and development (default: 10 min)

### Creating Custom Configurations

Create a new file in `configs/your_config.py`:

```python
from typing import Any
from core.emulation.hosts import HostConfig
from core.emulation.mixer import MixerConfig
from core.emulation.metrics import MetricConfig, MetricType, Scenarios
from configs.base import BaseEmulatorConfig

class YourConfig(BaseEmulatorConfig):
    '''Your custom configuration class.'''
    
    def build(self, **kwargs: Any) -> MixerConfig:
        '''Build the configuration.'''
        
        host = HostConfig(
            name='my-server',
            host='server01.prod.company.com',
            ttl=600.0,  # 10 minutes
            interval=15.0,  # report every 15 seconds
            labels={'environment': 'prod', 'service': 'api'},
            metrics=[
                MetricConfig(
                    name='response_time_ms',
                    metric_type=MetricType.GAUGE,
                    value_range=(10.0, 500.0),
                    default_value=50.0,
                    update_interval=10.0,
                    scenario=Scenarios.random_walk,
                    description='API response time in milliseconds'
                )
            ]
        )
        
        return MixerConfig(
            pushgateway_url='http://localhost:9091',
            hosts=[host]
        )
```

Then run with: `PYTHONPATH=. python main.py --config your_config`

**Note**: The configuration system uses a centralized `EmulatorAppConfiguration` class for default values and environment variable support. You can override defaults using environment variables prefixed with `PME_` (e.g., `PME_PUSHGATEWAY_URL`, `PME_DEBUG_MODE`).

### Host Configuration

```python
from core.emulation.hosts import HostConfig
from core.emulation.metrics import MetricConfig, Scenarios

host_config = HostConfig(
    name='web-server-01',
    host='server01.prod.company.com',  # optional, auto-generated if not provided
    ttl=1800.0,              # 30 minutes
    interval=15.0,           # reporting interval in seconds
    job_name='web-servers',  # pushgateway job name (optional, uses default if empty)
    labels={'role': 'web', 'datacenter': 'east'},
    listen_events={},        # event handlers (optional)
    metrics=[
        MetricConfig(
            name='cpu_usage_percent',
            update_interval=10.0,  # generate every 10 seconds
            listen_events=['load_peak_start', 'load_peak_end'],
            scenario=Scenarios.load_peak_cpu,
            description='CPU usage reacting to load peaks'
        )
    ]
)
```

### Metric Configuration

```python
from core.emulation.metrics import MetricConfig, MetricType, Scenarios

# gauge metric with custom scenario
cpu_metric = MetricConfig(
    name='cpu_usage_percent',
    metric_type=MetricType.GAUGE,
    value_range=(0.0, 100.0),
    default_value=15.0,
    units='%',
    update_interval=10.0,
    listen_events=['load_peak_start', 'load_peak_end'],
    scenario=Scenarios.load_peak_cpu,
    description='CPU usage percentage'
)

# counter metric
requests_metric = MetricConfig(
    name='http_requests_total',
    metric_type=MetricType.COUNTER,
    value_range=(0.0, 100.0),
    default_value=5.0,
    update_interval=5.0,
    description='Total HTTP requests'
)

# histogram metric
response_time_metric = MetricConfig(
    name='http_response_time',
    metric_type=MetricType.HISTOGRAM,
    value_range=(0.001, 2.0),
    default_value=0.05,
    units='seconds',
    update_interval=5.0,
    description='HTTP response time distribution'
)
```

## Built-in Scenarios

The emulation system provides a comprehensive set of predefined scenarios for realistic metric behavior. Each scenario is designed to simulate real-world patterns and can be configured with custom parameters.

### Basic Scenarios

#### `do_nothing`
Returns the current metric value without modifications.
- **Use case**: Baseline metrics that should remain constant
- **Parameters**: None
- **Returns**: Current metric value unchanged

#### `random_in_range`  
Generates random values within the specified range.
- **Use case**: Simulating unpredictable metrics like network jitter
- **Parameters**: 
  - `value_range`: Optional tuple defining min/max values (defaults to metric's configured range)
- **Returns**: Random float within specified range

#### `time_duration`
Calculates elapsed time since metric initialization.
- **Use case**: Uptime counters, session duration metrics
- **Parameters**: None
- **Returns**: Seconds elapsed since first call
- **State**: Stores start timestamp in `context.storage`

### Wave Pattern Scenarios

#### `sine_wave`
Creates smooth oscillating patterns using mathematical sine waves.
- **Use case**: Periodic load patterns, temperature fluctuations, daily traffic cycles
- **Parameters**:
  - `period`: Cycle duration in seconds (default: 300.0)
  - `amplitude`: Wave amplitude (default: 50.0)
  - `offset`: Vertical offset/center line (default: 50.0)
  - `phase_offset`: Phase shift in radians (default: 0.0)

```python
# Example: 5-minute cycle oscillating between 25-75%
scenario=Scenarios.sine_wave,
scenario_data={'period': 300.0, 'amplitude': 25.0, 'offset': 50.0}
```

### Trend-Based Scenarios

#### `update_by_trend`
Accumulates values based on configurable trend direction.
- **Use case**: Gradually increasing metrics like disk usage, gradual performance degradation
- **Parameters**:
  - `trend`: Direction - 'up', 'down', or 'hold' (default: 'hold')
  - `step_range`: Tuple defining min/max step size (default: (1.0, 5.0))
- **Behavior**:
  - `up`: Positive steps within range
  - `down`: Negative steps within range  
  - `hold`: Random steps in both directions

```python
# Example: Gradually increasing disk usage
scenario=Scenarios.update_by_trend,
scenario_data={'trend': 'up', 'step_range': (0.1, 2.0)}
```

### Selection Scenarios

#### `variety_selection`
Weighted random selection from predefined values.
- **Use case**: Service states, discrete performance levels, status indicators
- **Parameters**:
  - `values`: List of possible values to select from
  - `varieties`: List of weights for each value (must match values length)
  - `change_probability`: Chance of changing value each call (0.0-1.0, default: 0.1)

```python
# Example: Service health status (mostly healthy, occasionally degraded)
scenario=Scenarios.variety_selection,
scenario_data={
    'values': [100.0, 75.0, 50.0, 25.0],  # health percentages
    'varieties': [0.7, 0.2, 0.08, 0.02],  # weights (70% healthy, 20% good, 8% degraded, 2% poor)
    'change_probability': 0.15
}
```

### Toggle Scenarios

#### `feature_toggle`
Simulates feature flags with configurable timing and state changes.
- **Use case**: Feature rollouts, maintenance windows, batch job execution
- **Parameters**:
  - `start_time`: Delay before first toggle (default: 30.0)
  - `duration`: Time in 'on' state (default: 60.0)
  - `interval`: Time in 'off' state between cycles (default: 15.0)
  - `on_value`: Value when active (default: 1.0)
  - `off_value`: Value when inactive (default: 0.0)
  - `source`: Optional source identifier for emitted events
- **Events**: Emits `feature_on` and `feature_off` events on state changes

### Advanced Scenarios

#### `switch_scenario_by_events`
Dynamically switches between different scenarios based on incoming events.
- **Use case**: Complex behavioral changes, incident response patterns
- **Parameters**:
  - `events_config`: Dictionary mapping event names to scenario configurations
  - `default_scenario`: Fallback scenario name when no events match
  - `default_scenario_data`: Parameters for the default scenario
- **Event Config Structure**:
  - `scenario`: Name of scenario to execute
  - `scenario_data`: Parameters for the scenario
  - `duration`: Optional time limit for using this scenario

```python
# Example: Normal load with incident spikes
scenario=Scenarios.switch_scenario_by_events,
scenario_data={
    'events_config': {
        'incident_start': {
            'scenario': 'sine_wave',
            'scenario_data': {'amplitude': 80.0, 'period': 60.0},
            'duration': 300.0
        }
    },
    'default_scenario': 'random_in_range',
    'default_scenario_data': {'value_range': (10.0, 30.0)}
}
```

#### `relay_to_other_metric`
Calculates values based on another metric using a transformation function.
- **Use case**: Derived metrics, percentage calculations, dependent relationships
- **Parameters**:
  - `source_metric_name`: Name of the source metric to calculate value from
  - `calc_function`: Function taking MetricContext and returning calculated value

```python
# Example: Memory usage percentage based on absolute consumption
def calc_memory_percent(source_context: MetricContext) -> Optional[float]:
    """Calculate memory percentage from absolute values."""
    absolute_memory = source_context.value
    max_memory = source_context.data.value_range[1]
    return (absolute_memory / max_memory) * 100.0

scenario=Scenarios.relay_to_other_metric,
scenario_data={
    'source_metric_name': 'memory_consumption_bytes',
    'calc_function': calc_memory_percent
}
```

#### `calc_by_event`
Updates metric values based on event-driven calculations.
- **Use case**: Counters that change based on system events, dynamic scaling metrics
- **Parameters**:
  - `events_config`: Dictionary mapping event names to calculation functions

```python
# Example: Worker count that changes based on scaling events
def worker_started(context: MetricContext) -> Optional[float]:
    return context.value + 1

def worker_stopped(context: MetricContext) -> Optional[float]:
    return max(0, context.value - 1)

def scale_up(context: MetricContext) -> Optional[float]:
    return context.value + 5

def scale_down(context: MetricContext) -> Optional[float]:
    return max(0, context.value - 3)

scenario=Scenarios.calc_by_event,
scenario_data={
    'events_config': {
        'worker_started': worker_started,
        'worker_stopped': worker_stopped,
        'scale_up': scale_up,
        'scale_down': scale_down
    }
}
```

### Custom Scenario Development

When creating custom scenarios, follow this structure:

```python
@staticmethod
def custom_scenario(
    context: MetricContext,
    param1: float = 1.0,
    param2: str = 'default'
) -> Optional[float]:
    '''
    Custom scenario description.
    
    Args:
        context: the emulated metric context
        param1: description of parameter 1
        param2: description of parameter 2
    '''
    # Access current metric value
    current_value = context.value
    
    # Use context.storage for state persistence
    last_value = context.storage.get('last_value', current_value)
    context.storage.set('last_value', current_value)
    
    # Access metric configuration
    metric_config = context.data
    
    # Check for events
    if context.event:
        # Handle event-driven behavior
        if context.event.name == 'custom_event':
            return current_value * 2.0
    
    # Access linked metrics
    if 'source_metric' in context.links:
        source_context = context.links['source_metric']
        # Use source metric for calculations
    
    # Return calculated float value or None
    return float(calculated_value)
```

## Configuration Structure

### Mixer Configuration

The main configuration structure controls the entire emulation environment through the `MetricsMixer`:

```python
@dataclass
class MixerConfig:
    '''Configuration for MetricsMixer.'''
    
    hosts: List[HostConfig] = field(default_factory=list)  # List of host configurations
    pushgateway_url: str = 'http://localhost:9091'  # Pushgateway endpoint
    push_interval: float = 15.0  # Push interval in seconds
    default_job_name: str = 'emulated_host_...'  # Default job name for hosts without job_name
    cleanup_on_start: bool = True  # Cleanup pushgateway on start
    cleanup_on_finish: bool = True  # Cleanup pushgateway on finish
```

### Host Configuration

Each host in the emulation is configured independently:

```python
@dataclass  
class HostConfig:
    '''Configuration for a single emulated host.'''
    
    name: str  # unique identifier for the host
    host: str = ''  # hostname/IP (auto-generated if empty)
    ttl: float = float('inf')  # time-to-live in seconds
    interval: float = 30.0  # reporting interval to pushgateway
    job_name: str = ''  # pushgateway job name (uses default_job_name if empty)
    labels: Dict[str, str] = field(default_factory=dict)  # prometheus labels
    listen_events: Dict[str, str] = field(default_factory=dict)  # event handlers
    metrics: List[MetricConfig] = field(default_factory=list)  # metric definitions
```

**Key Configuration Options:**

- **`name`**: Unique identifier used in logs and status reports
- **`host`**: Hostname (generates fake name like `stress01.lgs01.app.stage` if not provided)
- **`ttl`**: Host lifetime - how long it runs before stopping automatically
- **`interval`**: How often metrics are pushed to Pushgateway
- **`job_name`**: Pushgateway job name for grouping metrics (uses default_job_name if empty)
- **`labels`**: Additional Prometheus labels attached to all metrics from this host
- **`listen_events`**: Maps event names to handler method names (rarely used directly)
- **`metrics`**: List of metrics this host will generate

### Metric Configuration

Individual metrics are configured with detailed parameters:

```python
@dataclass(frozen=True)
class MetricConfig:
    '''Configuration for a single metric.'''
    
    name: str  # metric name (becomes prometheus metric name)
    metric_type: MetricType = MetricType.GAUGE  # GAUGE, COUNTER, or HISTOGRAM
    value_range: tuple[float, float] = (0.0, 100.0)  # valid value bounds
    default_value: float = 0.0  # initial value
    units: str = ''  # units for display (not sent to prometheus)
    start_time: float = 0.0  # delay before metric becomes active
    duration: float = float('inf')  # how long metric stays active
    update_interval: float = 10.0  # how often new values are generated
    listen_events: List[str] = field(default_factory=list)  # events that trigger updates
    scenario: Optional[Callable] = None  # scenario function for value generation
    scenario_data: Dict[str, Any] = field(default_factory=dict)  # parameters for scenario
    description: str = ''  # prometheus HELP text
```

**Configuration Examples:**

```python
# Basic gauge metric with random values
basic_cpu = MetricConfig(
    name='cpu_usage_percent',
    metric_type=MetricType.GAUGE,
    value_range=(0.0, 100.0),
    default_value=15.0,
    update_interval=5.0,
    description='CPU usage percentage'
)

# Counter that increments based on events
request_counter = MetricConfig(
    name='http_requests_total', 
    metric_type=MetricType.COUNTER,
    default_value=0.0,
    listen_events=['http_request'],
    scenario=Scenarios.calc_by_event,
    scenario_data={
        'events_config': {
            'http_request': lambda value, config: value + 1
        }
    }
)

# Complex metric with sine wave pattern and event overrides
complex_metric = MetricConfig(
    name='load_average',
    value_range=(0.0, 10.0),
    update_interval=10.0,
    listen_events=['load_spike', 'load_normal'],
    scenario=Scenarios.switch_scenario_by_events,
    scenario_data={
        'events_config': {
            'load_spike': {
                'scenario': 'sine_wave',
                'scenario_data': {'amplitude': 4.0, 'offset': 6.0, 'period': 120.0},
                'duration': 300.0
            }
        },
        'default_scenario': 'sine_wave', 
        'default_scenario_data': {'amplitude': 1.0, 'offset': 2.0, 'period': 600.0}
    }
)
```

### Configuration Loader Usage

The configuration loader provides flexible ways to manage configurations:

```python
from core.emulation.loader import load_config, ConfigLoadError

# basic usage - auto-detects classes ending with 'Config'
config = load_config('hosts_load_with_peaks')
# load specific class from config file
config = load_config('hosts_load_with_peaks', 'HostsLoadWithPeaksConfig')
# pass parameters to config build method
config = load_config('hosts_load_with_peaks', hosts_count=12, hosts_ttl=1800)

# error handling
try:
    config = load_config('nonexistent_config')
except ConfigLoadError as e:
    print(f'Configuration error: {e}')
```

### Environment-Specific Configurations

Create different configurations for different environments:

```python
# configs/production.py
class ProductionConfig(BaseEmulatorConfig):
    '''Production-like configuration with realistic load patterns.'''
    
    def build(self, replica_count: int = 10, **kwargs: Any) -> MixerConfig:
        '''Build production configuration.'''
        hosts = []
        
        # create multiple web servers
        for i in range(replica_count):
            hosts.append(HostConfig(
                name=f'web-{i:02d}',
                ttl=3600.0,  # 1 hour
                job_name='web-servers',  # shared job name
                labels={'service': 'web', 'environment': 'prod'},
                metrics=[
                    MetricConfig(name='cpu_percent', scenario=Scenarios.sine_wave),
                    MetricConfig(name='memory_percent', scenario=Scenarios.update_by_trend)
                ]
            ))
        
        return MixerConfig(hosts=hosts)

class StagingConfig(BaseEmulatorConfig):
    '''Staging configuration with shorter TTL and fewer hosts.'''
    
    def build(self, **kwargs: Any) -> MixerConfig:
        '''Build staging configuration.'''
        # ... staging-specific setup
```

**Usage:**
```bash
PYTHONPATH=. python main.py --config production --class ProductionConfig
PYTHONPATH=. python main.py --config production --class StagingConfig
```

### Environment Configuration

The emulation system supports environment-based configuration through the `EmulatorAppConfiguration` class:

```bash
# override pushgateway URL
export PME_PUSHGATEWAY_URL=http://prod-pushgateway:9091

# enable debug mode
export PME_DEBUG_MODE=true

# disable pushgateway cleanup on start
export PME_PUSHGATEWAY_CLEANUP_ON_START=false

# change status update interval
export PME_SHOW_STATUS_INTERVAL_SEC=60

# show detailed metrics status
export PME_SHOW_METRICS_STATUS=true
```

## Custom Scenarios

Create custom scenario functions using the MetricContext API:

```python
def custom_scenario(context: MetricContext) -> Optional[float]:
    """Custom scenario that doubles values on 'boost' events."""
    current_value = context.value
    
    if context.event:
        if context.event.name == 'boost-event':
            context.storage.set('boost_active', True)
            return current_value * 2.0
        elif context.event.name == 'normal-event':
            context.storage.set('boost_active', False)
            return current_value * 0.5
    
    # Check stored state
    boost_active = context.storage.get('boost_active', False)
    if boost_active:
        return current_value * 1.1  # gradual increase
    else:
        return current_value * 0.99  # gradual decrease

# use in MetricConfig
MetricConfig(
    name='custom_metric',
    listen_events=['boost-event', 'normal-event'],
    scenario=custom_scenario
)
```

## Event System

The emulation uses an async event bus for host coordination:

```python
from core.emulation.events import Event, EmulatorEventBus

# emit events manually
await EmulatorEventBus.emit(Event('custom_event', {'data': 'value'}, 'source-host'))

# subscribe to events (usually done automatically by hosts)
async def handle_event(event: Event):
    print(f"Received: {event.name} from {event.source}")

await EmulatorEventBus.subscribe('custom_event', handle_event)
```

## Architecture

```
MetricsMixer
├── Job Groups (grouped by job_name)
│   ├── CollectorRegistry (per job)
│   └── EmulatedHost (async task per host)
│       ├── EmulatedMetric (multiple per host)
│       │   ├── Scenario function
│       │   └── Metric value generation
│       └── Callback to mixer
├── Centralized Pushgateway Communication
└── EventBus (global async event system)
```

## Pushgateway Job Management

The `MetricsMixer` provides sophisticated job management for pushgateway, supporting both single and multiple job patterns based on host configuration.

### Single Job Pattern (Consolidated)

When hosts don't specify a `job_name` or share the same `job_name`, they are grouped into a single pushgateway job:

```python
# All hosts use the same job (default_job_name)
hosts = [
    HostConfig(name='web-01', metrics=[...]),  # no job_name specified
    HostConfig(name='web-02', metrics=[...]),  # no job_name specified
    HostConfig(name='web-03', metrics=[...]),  # no job_name specified
]

config = MixerConfig(
    hosts=hosts,
    default_job_name='web-cluster'  # all hosts grouped under this job
)
```

**Benefits:**
- **Consolidated metrics** - All host metrics appear under one job in pushgateway
- **Simplified monitoring** - Single job to scrape in Prometheus
- **Resource efficient** - One registry and push operation

**Use cases:**
- Load-balanced services where hosts are interchangeable
- Cluster monitoring where individual host identity is less important
- Development/testing with fewer monitoring complexity

### Multiple Jobs Pattern (Distributed)

When hosts specify different `job_name` values, they create separate pushgateway jobs:

```python
# Each host or service gets its own job
hosts = [
    HostConfig(name='web-01', job_name='web-servers', metrics=[...]),
    HostConfig(name='web-02', job_name='web-servers', metrics=[...]),  # shared job
    HostConfig(name='api-01', job_name='api-servers', metrics=[...]),  # separate job
    HostConfig(name='db-01', job_name='database', metrics=[...]),      # separate job
]

config = MixerConfig(hosts=hosts)
```

**Benefits:**
- **Service isolation** - Different services have separate job namespaces
- **Granular control** - Independent lifecycle management per job
- **Flexible grouping** - Mix of shared and isolated jobs as needed
- **Scalable monitoring** - Easy to add/remove service types

**Use cases:**
- Microservices architecture with distinct service types
- Multi-tenant environments requiring isolation
- Production systems with complex service dependencies

### Job Grouping Behavior

The mixer automatically groups hosts by job name:

```python
# Example: Mixed job configuration
hosts = [
    HostConfig(name='web-01', job_name='frontend'),     # Job: frontend
    HostConfig(name='web-02', job_name='frontend'),     # Job: frontend (merged)
    HostConfig(name='api-01', job_name='backend'),      # Job: backend
    HostConfig(name='worker-01'),                       # Job: default_job_name
    HostConfig(name='worker-02'),                       # Job: default_job_name (merged)
]
```

**Resulting pushgateway jobs:**
- `frontend` - Contains metrics from web-01 and web-02
- `backend` - Contains metrics from api-01
- `default_job_name` - Contains metrics from worker-01 and worker-02

### Metrics Merging and Conflict Detection

When multiple hosts share the same job, the mixer:

1. **Merges compatible metrics** - Same metric name with different labels
2. **Warns about conflicts** - Same metric name with identical labels
3. **Maintains separate registries** - One Prometheus registry per job
4. **Handles updates efficiently** - Only affected jobs are pushed

```python
# Example: Metric merging
# Host web-01 (job: frontend)
MetricConfig(name='cpu_usage', labels={'instance': 'web-01'})

# Host web-02 (job: frontend) 
MetricConfig(name='cpu_usage', labels={'instance': 'web-02'})

# Result: Single job 'frontend' with two cpu_usage metrics differentiated by instance label
```

### Configuration Examples

**Single Job for Load Balancer Pool:**
```python
class LoadBalancerConfig(BaseEmulatorConfig):
    def build(self, pool_size: int = 5) -> MixerConfig:
        hosts = [
            HostConfig(
                name=f'lb-{i:02d}',
                # no job_name - all use default_job_name
                labels={'pool': 'main', 'instance': f'lb-{i:02d}'},
                metrics=[MetricConfig(name='requests_per_sec')]
            )
            for i in range(pool_size)
        ]
        
        return MixerConfig(
            hosts=hosts,
            default_job_name='load-balancer-pool'
        )
```

**Multiple Jobs for Microservices:**
```python
class MicroservicesConfig(BaseEmulatorConfig):
    def build(self) -> MixerConfig:
        hosts = [
            # Frontend service
            HostConfig(name='frontend-01', job_name='frontend-service', 
                      metrics=[MetricConfig(name='http_requests')]),
            HostConfig(name='frontend-02', job_name='frontend-service',
                      metrics=[MetricConfig(name='http_requests')]),
            
            # Backend API
            HostConfig(name='api-01', job_name='api-service',
                      metrics=[MetricConfig(name='api_calls')]),
            
            # Database
            HostConfig(name='db-01', job_name='database-service',
                      metrics=[MetricConfig(name='db_connections')]),
        ]
        
        return MixerConfig(hosts=hosts)
```

### Job Lifecycle Management

The mixer handles complete job lifecycle:

- **Startup**: Optionally cleans existing jobs (`cleanup_on_start=True`)
- **Runtime**: Groups hosts, merges metrics, pushes to separate jobs
- **Shutdown**: Optionally cleans mixer-managed jobs (`cleanup_on_finish=True`)

**Status Reporting:**
```json
{
  "is_running": true,
  "pushgateway_url": "http://localhost:9091",
  "push_interval": 15.0,
  "total_jobs": 3,
  "total_hosts": 4,
  "active_hosts": 4,
  "total_metrics": 12,
  "jobs": {
    "frontend-service": {
      "hosts_count": 2,
      "metrics_count": 6,
      "host_names": ["frontend-01", "frontend-02"]
    },
    "api-service": {
      "hosts_count": 1,
      "metrics_count": 3,
      "host_names": ["api-01"]
    },
    "database-service": {
      "hosts_count": 1,
      "metrics_count": 3,
      "host_names": ["db-01"]
    }
  }
}
```

## Infrastructure Requirements

### Quick Setup with Docker
The easiest way to get started is using the provided Docker infrastructure. The `docker/` directory contains a complete monitoring stack with Pushgateway, Prometheus, and Grafana, all pre-configured to work with the emulation system.

For detailed setup instructions, configuration options, and troubleshooting, see the [Docker Infrastructure Documentation](docker/README.md).

```bash
# start all infrastructure services
cd docker
./manage.sh start

# this starts:
# - Pushgateway on http://localhost:9091
# - Prometheus on http://localhost:9090  
# - Grafana on http://localhost:3000 (admin/admin123)
```

### Manual Setup
If you prefer manual setup:

1. **Pushgateway**: `docker run -p 9091:9091 prom/pushgateway`
2. **Prometheus**: Configure to scrape Pushgateway  
3. **Grafana**: For visualization

For detailed infrastructure documentation, configuration examples, management scripts, and troubleshooting guides, see the [Docker Infrastructure Documentation](docker/README.md).

## Troubleshooting

### Connection Issues
- Verify Pushgateway is running: `curl http://localhost:9091/metrics`
- Check firewall settings for port 9091

### High CPU Usage
- Reduce `update_interval` values in metric configs
- Decrease number of concurrent hosts

### Missing Metrics
- Check logs for push errors
- Verify metric names don't conflict
- Ensure Prometheus is scraping Pushgateway correctly

## Examples

### Available Configurations

The `configs/` directory contains ready-to-use configurations:

- **hosts_load_with_peaks**: Complex scenario with coordinated load peaks across multiple hosts (1 balancer + 9 workers)
  - Class: `HostsLoadWithPeaksConfig`
  - Default: 10 hosts, 15 minutes TTL
  - Features: Event-driven load peaks, CPU/memory/disk metrics, coordinated behavior
- **single_host_load**: Simple single-host configuration for development and testing
  - Class: `SingleHostLoadConfig`
  - Default: 1 host, 10 minutes TTL
  - Features: Basic CPU, memory, and I/O utilization metrics

Each configuration demonstrates different aspects:
- **Coordinated Events**: Controller host triggers events that worker hosts respond to
- **Realistic Patterns**: CPU spikes, memory usage, database connections
- **Multiple Metric Types**: Gauges, counters, and histograms
- **Time-based Scenarios**: Sine waves, random walks, load peaks

### Using Different Configuration Classes

```bash
# use default class (auto-detects classes ending with 'Config')
PYTHONPATH=. python main.py --config hosts_load_with_peaks

# use specific class
PYTHONPATH=. python main.py --config hosts_load_with_peaks --class HostsLoadWithPeaksConfig

# list all available configurations and their classes
PYTHONPATH=. python main.py --list-configs
```

### Configuration Loader API

The configuration loader provides additional functionality:

```python
from core.emulation.loader import load_config, list_available_configs, get_config_classes
from core.emulation.mixer import MetricsMixer

# list all available config files
configs = list_available_configs()  # ['hosts_load_with_peaks', 'single_host_load']

# list classes in a specific config
classes = get_config_classes('hosts_load_with_peaks')  # ['HostsLoadWithPeaksConfig']

# load configuration with error handling
try:
    config = load_config('my_config', 'MyCustomConfig')
    mixer = MetricsMixer(config)
except ConfigLoadError as e:
    print(f'Configuration error: {e}')
```
