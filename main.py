#!/usr/bin/env python3
# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '09/08/2025 00:00'

'''Main script to run Prometheus metrics core.'''

import sys
import json
import signal
import asyncio
import argparse
from typing import Any, Dict

from core.logger import getLogger
from core.emulation import loader
from app_config import AppConfig, APP_NAME, APP_VERSION
from core.emulation.mixer import MetricsMixer, MixerConfig


log = getLogger(__file__)


class GracefulKiller:
    '''Handle graceful shutdown on SIGINT/SIGTERM.'''

    def __init__(self) -> None:
        self.kill_now = False
        signal.signal(signal.SIGINT, self._exit_gracefully)
        signal.signal(signal.SIGTERM, self._exit_gracefully)

    def _exit_gracefully(self, signum: Any, frame: Any) -> None:
        log.info(f'Received signal <{signum}>, shutting down gracefully...')
        self.kill_now = True


async def main() -> int:
    '''Run main entry point.'''
    parser = argparse.ArgumentParser(description='Prometheus Metrics Emulator')
    parser.add_argument(
        '-cd',
        '--config-dir',
        default=AppConfig.CONFIGS_DIR,
        help='Configuration directory (default: emulation/configs/)',
    )
    parser.add_argument(
        '-c', '--config', help='Configuration file name (without .py extension) or use --list-configs to see available'
    )
    parser.add_argument(
        '-cls', '--class', dest='class_name', help='Specific class name to use from config file (optional)'
    )
    parser.add_argument(
        '-ls', '--list-configs', action='store_true', help='List available configuration files and exit'
    )
    parser.add_argument(
        '-pwg',
        '--pushgateway-url',
        default=AppConfig.PUSHGATEWAY_URL,
        help=f'Pushgateway URL (default: <{AppConfig.PUSHGATEWAY_URL}>)',
    )
    parser.add_argument(
        '-pi',
        '--push-interval',
        type=float,
        default=AppConfig.PUSHGATEWAY_PUSH_INTERVAL,
        help=f'Push interval in seconds (default: <{AppConfig.PUSHGATEWAY_PUSH_INTERVAL}>)',
    )
    parser.add_argument(
        '-ca',
        '--config-args',
        nargs='*',
        help='Additional arguments to pass to config build method (format: --config-args key=value key2=value2 ...)',
    )
    parser.add_argument(
        '-si',
        '--status-interval',
        type=float,
        default=AppConfig.SHOW_STATUS_INTERVAL_SEC,
        help=f'Status report interval in seconds (default: <{AppConfig.SHOW_STATUS_INTERVAL_SEC}>)',
    )
    args = parser.parse_args()

    # list configs and exit if requested
    if args.list_configs:
        log.info('Available configuration files:')
        configs = loader.list_available_configs()
        if configs:
            for i, config_name in enumerate(configs):
                log.info(f' {i + 1}: {config_name}')
                try:
                    classes = loader.get_config_classes(config_name)
                    if classes:
                        log.info(f'{" " * 4}Class(es): <{", ".join(classes)}>')
                except loader.ConfigLoadError as e:
                    log.info(f'{" " * 4}(Error loading classes: {e})')
        else:
            log.info(f'{" " * 2}No configuration files found in <{AppConfig.CONFIGS_DIR}>')
        sys.exit(0)

    # validate config argument
    if not args.config:
        available = loader.list_available_configs()
        if available:
            log.error(f'Please specify --config. Available configs: {", ".join(available)}')
            log.info('Use --list-configs for detailed information.')
        else:
            log.info(f'No configuration files found in {AppConfig.CONFIGS_DIR}')
            log.info('Please create a configuration file or use --list-configs to verify.')
        sys.exit(1)

    # parse config arguments
    config_kwargs: Dict[str, Any] = {}
    if args.config_args:
        for arg in args.config_args:
            if '=' in arg:
                key, value = arg.split('=', 1)
                # convert value to appropriate type
                try:
                    # int
                    config_kwargs[key] = int(value)
                except ValueError:
                    try:
                        # float
                        config_kwargs[key] = float(value)
                    except ValueError:
                        # bool
                        if value.lower() in ('true', 'false'):
                            config_kwargs[key] = value.lower() == 'true'
                        else:
                            # string
                            config_kwargs[key] = value
            else:
                log.error(f'Invalid config argument format: {arg} (expected key=value)')
                sys.exit(1)

    # load configuration
    try:
        log.info(f'Loading configuration: <{args.config}>')
        if args.class_name:
            log.info(f'Using class: <{args.class_name}>')
        if config_kwargs:
            log.info(f'Config arguments: {config_kwargs}')
        loaded_config = loader.load_config(args.config, args.class_name, **config_kwargs)
    except loader.ConfigLoadError as e:
        if AppConfig.DEBUG_MODE:
            log.exception(f'Error loading configuration: {e}')
        else:
            log.error(f'Error loading configuration: {e}')
        sys.exit(1)

    # override config values from command line
    mixer_config = MixerConfig(
        hosts=loaded_config.hosts,
        pushgateway_url=args.pushgateway_url,
        push_interval=args.push_interval,
        default_job_name=loaded_config.default_job_name,
        cleanup_on_start=loaded_config.cleanup_on_start,
        cleanup_on_finish=loaded_config.cleanup_on_finish,
    )

    # create emulator
    mixer = MetricsMixer(mixer_config)
    killer = GracefulKiller()

    log.blank()
    log.info(f'{"-" * 30}')
    log.info(f'Starting metrics emulation with <{len(mixer_config.hosts)}> hosts')
    log.info(f'Configuration: <{args.config}>')
    if args.class_name:
        log.info(f'Class: <{args.class_name}>')
    if config_kwargs:
        log.info(f'Config arguments: {config_kwargs}')
    log.info(f'Pushgateway URL: <{mixer_config.pushgateway_url}>')
    log.info('Press Ctrl+C to stop')
    log.info(f'{"-" * 30}')
    log.blank()

    # start emulation
    try:
        emulation_task = asyncio.create_task(mixer.run_until_complete())
        status_task = asyncio.create_task(status_reporter(mixer, args.status_interval, killer))
        killer_task = asyncio.create_task(wait_for_killer(killer))

        # wait for first task to complete
        done, pending = await asyncio.wait([emulation_task, killer_task], return_when=asyncio.FIRST_COMPLETED)

        # cancel remaining tasks
        for task in pending:
            task.cancel()

        status_task.cancel()

        # stop emulator if needed
        if killer.kill_now:
            await mixer.stop()
    except Exception as e:
        if AppConfig.DEBUG_MODE:
            log.exception(f'Error during emulation: <{e}>')
        else:
            log.error(f'Error during emulation: <{e}>')
        await mixer.stop()
        sys.exit(1)

    log.info('Emulation finished')
    sys.exit(0)


async def status_reporter(mixer: MetricsMixer, interval: float, killer: GracefulKiller) -> None:
    '''Report status periodically.'''
    while not killer.kill_now:
        try:
            await asyncio.sleep(interval)
            status = mixer.get_status()
            if not killer.kill_now:
                log.blank()
                log.info('--- Status Report ---')
                log.info('Running' if mixer.is_running else 'Stopped')
                log.info(f'Hosts: <{status["active_hosts"]}/{status["total_hosts"]}> active')
                log.info(f'Status: {json.dumps(status, indent=2)}')
                log.info('-' * 30)
        except asyncio.CancelledError:
            log.debug('Status reporter cancelled')
            break
        except Exception as e:
            log.exception(f'Error in status reporter: <{e}>')


async def wait_for_killer(killer: GracefulKiller) -> None:
    '''Wait for graceful shutdown signal.'''
    while not killer.kill_now:
        await asyncio.sleep(0.1)


if __name__ == '__main__':
    try:
        msg = f'--- {APP_NAME} v{APP_VERSION} ---'
        log.blank()
        log.info('-' * len(msg))
        log.info(msg)
        log.info('-' * len(msg))
        log.blank()
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log.warning('\nInterrupted by user')
        sys.exit(0)
    except Exception as e:
        if AppConfig.DEBUG_MODE:
            log.exception(f'Unexpected error: <{e}>')
        else:
            log.error(f'Unexpected error: <{e}>')
        sys.exit(1)
