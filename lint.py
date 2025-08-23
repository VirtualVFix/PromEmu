#!/usr/bin/env python3

import sys
import argparse
import subprocess

from core.logger import getLogger

log = getLogger(__file__)


def run_command(cmd: list[str], description: str) -> tuple[bool, str | None]:
    '''
    Run a command and return whether it succeeded and any output.

    Args:
        cmd: List of command parts to execute.
        description: Human-readable description of the command.

    Returns:
        A tuple containing (success_flag, output_or_error).
    '''
    log.info(f'Running {description}...')
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, encoding='utf-8')
        log.info(f'{description} passed!')
    except subprocess.CalledProcessError as e:
        log.error(f'{description} failed!')
        return False, e.stderr
    else:
        return True, result.stdout


def run_ruff() -> bool:
    '''Run Ruff linter and formatter.'''
    success, _ = run_command(['ruff', 'check', '.'], 'Ruff linter')
    if not success:
        return False

    success, _ = run_command(['ruff', 'format', '--check', '.'], 'Ruff formatter')
    return success


def run_mypy() -> bool:
    '''Run MyPy type checker.'''
    success, _ = run_command(['mypy', '.'], 'MyPy type checker')
    return success


def run_bandit() -> bool:
    '''Run Bandit security linter.'''
    success, _ = run_command(['bandit', '-r', '.'], 'Bandit security linter')
    return success


def main() -> int:
    '''Run all linters.'''
    parser = argparse.ArgumentParser(description='Run all linters')
    parser.add_argument('--fix', action='store_true', help='Fix issues when possible')
    args = parser.parse_args()

    all_passed = True

    # Run Ruff (with auto-fix if requested)
    if args.fix:
        all_passed = run_command(['ruff', 'check', '--fix', '.'], 'Ruff linter (fix mode)')[0] and all_passed
        all_passed = run_command(['ruff', 'format', '.'], 'Ruff formatter (fix mode)')[0] and all_passed
    else:
        all_passed = run_ruff() and all_passed

    # Run MyPy
    all_passed = run_mypy() and all_passed

    # Run Bandit
    all_passed = run_bandit() and all_passed

    if all_passed:
        log.info('All linters passed successfully!')
        return 0

    log.error('Some linters reported issues.')
    return 1


if __name__ == '__main__':
    sys.exit(main())
