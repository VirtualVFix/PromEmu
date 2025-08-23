#!/usr/bin/env python3
# encoding: utf-8

import argparse
import subprocess
from pathlib import Path
from typing import List, Optional

from core.logger import getLogger

log = getLogger(__name__)


def run_tests(test_paths: Optional[List[str]] = None, allure_dir: str = '.allure-results') -> int:
    '''
    Run pytest with allure.

    Args:
        test_paths: List of test file or directory paths to run.
                    If None, all tests will be run.
        allure_dir: Directory to store allure results.

    Returns:
        Return code from pytest.
    '''
    allure_path = Path(allure_dir)
    if not allure_path.exists():
        allure_path.mkdir(parents=True, exist_ok=True)
        log.info(f'Created allure results directory: <{allure_dir}>')

    cmd = ['pytest', '-v', f'--alluredir={allure_dir}']

    if test_paths:
        cmd.extend(test_paths)

    log.info(f'Running: <{" ".join(cmd)}>')
    result = subprocess.run(cmd, check=False)

    log.info(f'Tests completed with return code: <{result.returncode}>')
    return result.returncode


def generate_report(allure_dir: str = '.allure-results', report_dir: str = 'allure-report') -> int:
    '''
    Generate allure report from results.

    Args:
        allure_dir: Directory with allure results.
        report_dir: Directory to output the report.

    Returns:
        Return code from allure command.
    '''
    allure_path = Path(allure_dir)
    if not allure_path.exists() or not list(allure_path.iterdir()):
        log.error(f'No allure results found in <{allure_dir}>')
        return 1

    cmd = ['allure', 'generate', allure_dir, '-o', report_dir, '--clean']

    # run allure
    log.info(f'Generating report: <{" ".join(cmd)}>')
    try:
        result = subprocess.run(cmd, check=False)
        log.info(f'Report generation completed with return code: <{result.returncode}>')

        if result.returncode == 0:
            report_path = Path(report_dir).resolve()
            log.info(f'Report generated at: <{report_path}>')

        return result.returncode
    except FileNotFoundError:
        log.error('Allure command not found. Make sure allure is installed and in your PATH.')
        log.info('You can install allure using: brew install allure (on macOS)')
        return 1


def serve_report(report_dir: str = 'allure-report', port: int = 8080) -> int:
    '''
    Run Allure report server.

    Args:
        report_dir: Directory with the generated report.
        port: Port to serve the report on.

    Returns:
        Return code from allure command.
    '''
    report_path = Path(report_dir)
    if not report_path.exists():
        log.error(f'No report found in <{report_dir}>')
        return 1

    cmd = ['allure', 'open', report_dir, '-p', str(port)]

    # run allure
    log.info(f'Serving report: <{" ".join(cmd)}>')
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except FileNotFoundError:
        log.error('Allure command not found. Make sure allure is installed and in your PATH.')
        log.info('You can install allure using: brew install allure (on macOS)')
        return 1


def main() -> None:
    '''Main function to run tests with allure reporting.'''
    parser = argparse.ArgumentParser(description='Run tests with allure reporting')
    parser.add_argument('--tests', nargs='*', help='Test files or directories to run')
    parser.add_argument('--allure-dir', default='.allure-results', help='Directory to store allure results')
    parser.add_argument('--report-dir', default='allure-report', help='Directory to output the report')
    parser.add_argument('--port', type=int, default=8080, help='Port to serve the report on')
    parser.add_argument('--only-run', action='store_true', help="Only run tests, don't generate or serve report")
    parser.add_argument('--only-generate', action='store_true', help="Only generate report, don't run tests or serve")
    parser.add_argument(
        '--only-server', action='store_true', help="Run report server only, don't run tests or generate"
    )

    args = parser.parse_args()

    # run tests
    if not args.only_generate and not args.only_server:
        run_code = run_tests(args.tests, args.allure_dir)
        if run_code != 0 and not args.only_run:
            log.warning('Tests failed, but continuing to generate report...')

    # generate report
    if not args.only_run and not args.only_server:
        gen_code = generate_report(args.allure_dir, args.report_dir)
        if gen_code != 0 and not args.only_generate:
            log.warning('Report generation failed, but continuing to serve existing report if available...')

    # run report server
    if not args.only_run and not args.only_generate:
        serve_report(args.report_dir, args.port)


if __name__ == '__main__':
    main()
