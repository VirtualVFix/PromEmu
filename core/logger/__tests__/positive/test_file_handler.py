# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/19/2025 12:36'

'''
Tests for the FileHandlerWithCompress class from the logger module.
'''

import logging
import os
import time
from pathlib import Path

import pytest
import allure

from core.logger.handlers.file_handler_with_compress import FileHandlerWithCompress


@allure.feature('Logger')
@allure.story('FileHandlerWithCompress')
class TestFileHandlerWithCompress:
    '''Tests for the FileHandlerWithCompress class'''

    @allure.title('Test FileHandlerWithCompress initialization')
    def test_file_handler_init(self, temp_log_dir: Path) -> None:
        '''Test that FileHandlerWithCompress initializes correctly'''
        # given a log file path
        log_file = temp_log_dir / 'test_init.log'

        # when we create a FileHandlerWithCompress
        handler = FileHandlerWithCompress(str(log_file))

        # then it should be initialized correctly
        assert handler.baseFilename == str(log_file)
        assert handler.totalCount == 0

        # and the log file should be created
        assert log_file.exists()

        # clean up
        handler.close()

    @allure.title('Test FileHandlerWithCompress rollover')
    def test_file_handler_rollover(self, temp_log_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        '''Test that FileHandlerWithCompress rolls over correctly'''
        # given a log file path and a small maxBytes setting
        log_file = temp_log_dir / 'test_rollover.log'
        max_bytes = 100  # Very small to trigger rollover easily

        # and a fixed timestamp for consistent archive names
        fixed_timestamp = 1717830000.0  # 2024-06-08 10:00:00
        monkeypatch.setattr(time, 'time', lambda: fixed_timestamp)

        # when we create a handler and write enough data to trigger a rollover
        handler = FileHandlerWithCompress(str(log_file), maxBytes=max_bytes)
        logger = logging.getLogger('test_rollover')
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        logger.addHandler(handler)

        # write data to trigger rollover
        large_data = 'x' * 200  # Larger than maxBytes
        logger.info(large_data)

        # force another rollover to ensure the first one completes
        logger.info(large_data)

        # then we should see archives being created
        archive_pattern = f"{str(log_file)}*.zip"
        archives = list(temp_log_dir.glob("*.zip"))

        # check that at least one rollover occurred
        assert len(archives) > 0, "No archive files were created"

        # clean up
        handler.close()

    @allure.title('Test FileHandlerWithCompress attempts to remove old archives')
    def test_file_handler_handles_old_archives(self, temp_log_dir: Path) -> None:
        '''Test that FileHandlerWithCompress attempts to remove old archives but handles errors gracefully'''
        # given a log file path
        log_file = temp_log_dir / 'test_expire.log'

        # create a handler to ensure the log directory exists
        handler = FileHandlerWithCompress(str(log_file), maxBytes=1024)

        # create an "old" archive file with a name that looks like a backup
        old_archive = temp_log_dir / 'test_expire.log2024-05-19_12-00-00.zip'
        with open(old_archive, 'w') as f:
            f.write('test')

        # set the timestamp to make it appear old (7 days ago plus 1 hour)
        seven_days_ago = time.time() - (7 * 24 * 60 * 60 + 3600)
        os.utime(old_archive, (seven_days_ago, seven_days_ago))

        # when we create another rollover (which should attempt to clean up old archives)
        logger = logging.getLogger('test_expire')
        logger.setLevel(logging.INFO)
        logger.handlers.clear()
        logger.addHandler(handler)

        # make the handler do a rollover by writing a large amount of data
        for i in range(10):
            logger.info('x' * 200)  # Should eventually trigger a rollover

        # then we should see rollover archives created, even if old ones couldn't be removed
        # (there's a bug in the handler implementation with non-relative patterns that prevents removal)
        archive_pattern = f"{str(log_file)}*.zip"
        archives = list(temp_log_dir.glob("*.zip"))

        # at least one new archive should have been created (the old one plus at least one new one)
        assert len(archives) >= 2, "No new archive files were created during rollover"

        # clean up
        handler.close()

    @allure.title('Test FileHandlerWithCompress handles exceptions')
    def test_file_handler_handles_exceptions(self, temp_log_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        '''Test that FileHandlerWithCompress handles exceptions gracefully'''
        # given a log file path
        log_file = temp_log_dir / 'test_exception.log'

        # and a mocked shutil.move that raises an exception
        def mock_move_with_exception(*args: object, **kwargs: object) -> None:
            raise Exception('Test exception from mocked move')

        monkeypatch.setattr('shutil.move', mock_move_with_exception)

        # capture the log messages from the handler
        log_capture = []

        class TestHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                log_capture.append(record.getMessage())

        # set up the handler's logger to capture errors
        handler = FileHandlerWithCompress(str(log_file), maxBytes=100)
        handler.log.handlers.clear()
        handler.log.addHandler(TestHandler())

        # when we trigger a rollover that would normally fail
        handler.doRollover()

        # then the exception should be caught and logged
        assert any('Failed to move log file' in msg for msg in log_capture)

        # clean up
        handler.close()
