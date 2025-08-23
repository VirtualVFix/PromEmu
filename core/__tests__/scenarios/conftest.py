# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '08/14/2025 00:00'

import pytest
import time
from unittest.mock import MagicMock, patch
from typing import Any, Dict, List, Callable, Generator

from core.emulation.events import Event
from core.emulation.storage import StateStorage
from core.emulation.metrics import MetricConfig, MetricType, MetricContext


@pytest.fixture
def mock_event() -> Event:
    '''Create a mock event for testing.'''
    return Event(name='test_event', data={'timestamp': time.time()}, source='test_source')


@pytest.fixture
def mock_time() -> Generator[MagicMock, None, None]:
    '''Mock time.time() for predictable testing.'''
    with patch('time.time') as mock_time_func:
        mock_time_func.return_value = 1000.0  # fixed timestamp
        yield mock_time_func


@pytest.fixture
def mock_random() -> Generator[Dict[str, MagicMock], None, None]:
    '''Mock random functions for predictable testing.'''
    with patch('random.uniform') as mock_uniform, patch('random.random') as mock_rand:
        mock_uniform.return_value = 50.0  # predictable random value
        mock_rand.return_value = 0.5  # predictable random value
        yield {'uniform': mock_uniform, 'random': mock_rand}


@pytest.fixture
def basic_metric_config() -> MetricConfig:
    '''Create a basic metric configuration for testing.'''
    return MetricConfig(
        name='test_metric',
        metric_type=MetricType.GAUGE,
        value_range=(0.0, 100.0),
        init_value=50.0,
        units='%',
        update_interval=10.0,
        description='Test metric for scenarios',
    )


@pytest.fixture
def metric_context(basic_metric_config: MetricConfig, mock_event: Event) -> MetricContext:
    '''Create a metric context for testing scenarios.'''
    return MetricContext(
        data=basic_metric_config,
        value=basic_metric_config.init_value,
        event=mock_event,
        timestamp=time.time(),
        storage=StateStorage(),
    )


@pytest.fixture
def mock_emulated_metric(basic_metric_config: MetricConfig) -> MagicMock:
    '''Create a mock EmulatedMetric for testing scenarios.'''
    mock_metric = MagicMock()
    mock_metric.config = basic_metric_config
    mock_metric.value = basic_metric_config.init_value
    mock_metric._scenario_state = {}

    # setup scenario state methods
    def get_scenario_state(key: str, default: Any = None) -> Any:
        return mock_metric._scenario_state.get(key, default)

    def set_scenario_state(key: str, value: Any) -> None:
        mock_metric._scenario_state[key] = value

    mock_metric.get_scenario_state = MagicMock(side_effect=get_scenario_state)
    mock_metric.set_scenario_state = MagicMock(side_effect=set_scenario_state)

    return mock_metric


@pytest.fixture
def source_metric_for_relay() -> MagicMock:
    '''Create a source metric for relay scenario testing.'''
    mock_source = MagicMock()

    # create a custom config instead of using the frozen dataclass
    custom_config = MagicMock()
    custom_config.name = 'memory_usage_bytes'
    custom_config.value_range = (1073741824.0, 17179869184.0)  # 1GB to 16GB in bytes
    custom_config.init_value = 3221225472.0  # 3GB in bytes
    custom_config.units = 'bytes'
    custom_config.description = 'Memory usage in bytes'

    mock_source.config = custom_config
    mock_source.value = 8589934592.0  # 8GB in bytes
    mock_source._scenario_state = {}

    def get_scenario_state(key: str, default: Any = None) -> Any:
        return mock_source._scenario_state.get(key, default)

    def set_scenario_state(key: str, value: Any) -> None:
        mock_source._scenario_state[key] = value

    mock_source.get_scenario_state = MagicMock(side_effect=get_scenario_state)
    mock_source.set_scenario_state = MagicMock(side_effect=set_scenario_state)

    return mock_source


@pytest.fixture
def calc_function() -> Callable[[MetricContext], float]:
    '''Create a simple calculation function for relay testing.'''

    def calc_percent(context: MetricContext) -> float:
        min_val, max_val = context.data.value_range
        value = context.value or 0.0
        return ((value - min_val) / (max_val - min_val)) * 100.0

    return calc_percent


@pytest.fixture
def variety_values_and_weights() -> Dict[str, List[float]]:
    '''Create variety values and weights for variety_selection testing.'''
    return {
        'values': [10.0, 50.0, 90.0],
        'varieties': [0.2, 0.5, 0.3],  # weights that sum to 1.0
    }


@pytest.fixture
def events_config_for_switching() -> Dict[str, Dict[str, Any]]:
    '''Create events configuration for switch_scenario_by_events testing.'''
    return {
        'peak_load_start': {
            'scenario': 'random_in_range',
            'scenario_data': {'value_range': (75.0, 100.0)},
            'duration': 60.0,
        },
        'peak_load_end': {'scenario': 'random_in_range', 'scenario_data': {'value_range': (5.0, 25.0)}},
        'feature_toggle': {
            'scenario': 'feature_toggle',
            'scenario_data': {'start_time': 10.0, 'duration': 30.0, 'interval': 5.0, 'on_value': 1.0, 'off_value': 0.0},
            'duration': 120.0,
        },
    }


@pytest.fixture
def events_config_for_calc_by_event() -> Dict[str, Callable[[MetricContext], float]]:
    '''Create events configuration for calc_by_event testing.'''
    return {
        'worker_started': lambda context: (context.value or 0.0) + 1,
        'worker_stopped': lambda context: max(0, (context.value or 0.0) - 1),
        'worker_reset': lambda context: 0.0,
    }


class MockAsyncioCreateTask:
    '''Helper class to mock asyncio.create_task calls.'''

    def __init__(self) -> None:
        self.log: List[str] = []
        self.created_tasks: List[Any] = []

    def __call__(self, coro: Any) -> MagicMock:
        '''Mock create_task implementation.'''
        task = MagicMock()
        self.created_tasks.append(coro)
        self.log.append(f'Task created for: {coro}')
        return task


@pytest.fixture
def mock_asyncio_create_task() -> Generator[MockAsyncioCreateTask, None, None]:
    '''Mock asyncio.create_task to track task creation.'''
    mock_task_creator = MockAsyncioCreateTask()

    def create_task_mock(coro: Any) -> MagicMock:
        '''Mock create_task that handles coroutines properly.'''
        task = MagicMock()
        mock_task_creator.created_tasks.append(coro)
        mock_task_creator.log.append(f'Task created for: {coro}')

        # If it's a coroutine, we need to close it to avoid warnings
        if hasattr(coro, 'close'):
            coro.close()

        return task

    with patch('asyncio.create_task', side_effect=create_task_mock):
        yield mock_task_creator


@pytest.fixture
def create_metric_context() -> Callable[..., MetricContext]:
    '''Factory fixture for creating MetricContext instances with custom parameters.'''

    def _create_context(
        mock_metric: MagicMock | None = None,
        event: Event | None = None,
        storage: StateStorage | None = None,
        links: Dict[str, MetricContext] | None = None,
        **kwargs: Any,
    ) -> MetricContext:
        '''Create a MetricContext with sensible defaults.'''
        if storage is None:
            storage = StateStorage()

        if links is None:
            links = {}

        # Handle the case when mock_metric is provided
        if mock_metric is not None:
            return MetricContext(
                data=mock_metric.config, value=mock_metric.value, event=event, storage=storage, links=links, **kwargs
            )
        else:
            # Create a minimal context for cases where no mock is needed
            basic_config = MetricConfig(
                name='default_test_metric',
                value_range=(0.0, 100.0),
                init_value=50.0,
                units='%',
                description='Default test metric',
            )
            return MetricContext(data=basic_config, value=50.0, event=event, storage=storage, links=links, **kwargs)

    return _create_context


@pytest.fixture
def create_source_metric_context() -> Callable[..., MetricContext]:
    '''Factory fixture for creating source MetricContext for relay scenarios.'''

    def _create_source_context(
        source_metric: MagicMock, event: Event | None = None, storage: StateStorage | None = None, **kwargs: Any
    ) -> MetricContext:
        '''Create a source MetricContext for relay testing.'''
        if storage is None:
            storage = StateStorage()

        return MetricContext(
            data=source_metric.config, value=source_metric.value, event=event, storage=storage, **kwargs
        )

    return _create_source_context


@pytest.fixture
def metric_context_factory(mock_emulated_metric: MagicMock, mock_event: Event) -> Callable[..., MetricContext]:
    '''Pre-configured factory for the most common MetricContext pattern.'''

    def _create(
        storage: StateStorage | None = None, links: Dict[str, MetricContext] | None = None, **kwargs: Any
    ) -> MetricContext:
        '''Create MetricContext with common test defaults.'''
        if storage is None:
            storage = StateStorage()
        if links is None:
            links = {}

        return MetricContext(
            data=mock_emulated_metric.config,
            value=mock_emulated_metric.value,
            event=mock_event,
            storage=storage,
            links=links,
            **kwargs,
        )

    return _create
