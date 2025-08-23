# All rights reserved by forest fairy.
# You cannot modify or share anything without sacrifice.
# If you don't agree, keep calm and don't look at code bellow!

__author__ = 'VirtualV <https://github.com/virtualvfix>'
__date__ = '05/18/2025 11:54'
__version__ = '0.1.0'


import datetime
import logging
import shutil
import zipfile
from pathlib import Path
from io import TextIOWrapper
from typing import Optional, cast
from logging.handlers import RotatingFileHandler

from ..log_config import LogConfig


class FileHandlerWithCompress(RotatingFileHandler):
    '''Rotation file handler with compress files to zip.'''

    def __init__(
        self,
        filename: str,
        mode: str = 'a',
        maxBytes: int = 0,
        backupCount: int = 0,
        encoding: Optional[str] = 'utf-8',
        delay: bool = False,
    ) -> None:
        super(FileHandlerWithCompress, self).__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        self.totalCount = 0
        self.log = logging.getLogger(self.__class__.__name__)

    def removedOldArchives(self) -> None:
        try:
            # remove the archives over time limit
            expired_time = datetime.datetime.now() - datetime.timedelta(seconds=LogConfig.LOG_BACKUP_EXPIRED_TIME_SEC)
            for archive in Path().glob(f'{self.baseFilename}*.zip'):
                if archive.stat().st_mtime < expired_time.timestamp():
                    archive.unlink(missing_ok=True)
                    self.log.info(f'Removed expired log archive <{archive}>')
        except Exception as e:
            self.log.error(f'Failed to remove old archives: {e}')

    def doRollover(self) -> None:
        '''Rollover logs to files and compress them.'''
        self.totalCount += 1

        if self.stream:
            self.stream.close()
            self.stream = cast(TextIOWrapper, None)

        # rename file
        base_path = Path(self.baseFilename)
        new_name = f'{base_path.stem}.{self.totalCount}.log'
        try:
            shutil.move(self.baseFilename, new_name)
        except Exception as e:
            self.log.error(f'Failed to move log file: {e}')

        # add file to archive
        archive = f'{self.baseFilename}{datetime.datetime.now().strftime(LogConfig.LOG_BACKUP_NAME_FORMAT)}.zip'
        try:
            with zipfile.ZipFile(archive, 'a' if Path(archive).exists() else 'w') as zip_file:
                zip_file.write(new_name, Path(new_name).name, zipfile.ZIP_DEFLATED)
                self.log.info(f'Archived log file <{new_name}> to <{archive}>')
            # remove old files and archives
            Path(new_name).unlink(missing_ok=True)
            self.removedOldArchives()
        except Exception as e:
            self.log.error(f'Failed to archive log file <{archive}>: {e}')

        if not self.delay:
            self.stream = self._open()
