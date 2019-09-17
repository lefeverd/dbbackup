import abc
from datetime import datetime
import os
from pathlib import Path
import logging

from dbbackup import config

_logger = logging.getLogger(__name__)


class AbstractProvider(abc.ABC):
    callbacks = []

    @abc.abstractclassmethod
    def execute_backup(self, database=None, exclude=None):
        pass

    @abc.abstractclassmethod
    def list_backups(self):
        pass

    @abc.abstractclassmethod
    def restore_backup(self, backup_file, database, recreate=None,
                       create=None):
        pass

    def cleanup(self, days_to_keep):
        backups = self.get_backups()
        for backup in backups:
            backup_absolute = Path(config.BACKUP_DIRECTORY + "/" + backup)
            if self._is_older_than(backup_absolute, days_to_keep):
                _logger.info(
                    f"Removing backup {backup} >= {days_to_keep} days")
                self._remove(backup_absolute)

    def _is_older_than(self, backup, days):
        now = datetime.now().timestamp()
        backup_timestamp = os.path.getmtime(backup)
        age_days = (now - backup_timestamp) / (60 * 60 * 24)
        _logger.debug(f"Backup {backup} age {age_days} days")
        return age_days >= float(days)

    def _remove(self, backup):
        return backup.unlink()

    def verify_backup_file(self, backup_file):
        backup_file_path = Path(backup_file)
        if not backup_file_path.is_absolute():
            backup_file_path = Path(config.BACKUP_DIRECTORY) / backup_file
            backup_file_path = backup_file_path.resolve()

        if not backup_file_path.exists():
            raise Exception(f"File {backup_file_path} does not exist.")

        try:
            backup_file_path.relative_to(config.BACKUP_DIRECTORY)
        except ValueError:
            raise Exception(
                f"File {backup_file} is not inside BACKUP_DIRECTORY \
                    {config.BACKUP_DIRECTORY}")

        return str(backup_file_path)

    def register_callback(self, callback):
        self.callbacks.append(callback)

    def notify_callbacks(self, event, *args, **kwargs):
        for callback in self.callbacks:
            try:
                getattr(callback, event)(*args, **kwargs)
            except Exception as e:
                _logger.warn(
                    f"Could not call method {event} on callback {callback}", e)
