import abc
from datetime import datetime
import os
from importlib import import_module
import inspect
from pathlib import Path
import logging

from dbbackup import config

_logger = logging.getLogger(__name__)


class ProviderClassNotFoundError(Exception):
    pass


class AbstractProvider(abc.ABC):
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


def get_builder_module(module_name):
    return import_module(
        'dbbackup.builders.' + module_name, package=__package__)


def get_builder_class(builder_module, provider_name):
    clsmembers = inspect.getmembers(builder_module, inspect.isclass)
    clsmembers = [
        clsmember[1] for clsmember in clsmembers
        if getattr(clsmember[1], 'provider_for', False) == provider_name
    ]
    if not clsmembers or len(clsmembers) != 1:
        raise ProviderClassNotFoundError(
            f"Could not find subclass of {AbstractProvider.__name__} \
            in {builder_module.__name__}")
    return clsmembers[0]


def get(provider_name, *args, **kwargs):
    try:
        _logger.debug(f"Getting builder for {provider_name}")
        builder_module = get_builder_module(provider_name)
        _logger.debug(f"Got module {builder_module}")
        builder_class = get_builder_class(builder_module, provider_name)
        _logger.debug(f"Got class {builder_class}")
        provider_instance = builder_class()(*args, **kwargs)
        _logger.debug(f"Created instance {provider_instance}")
        return provider_instance
    except (AttributeError, ModuleNotFoundError):
        raise ImportError('Could not find {} provider.'.format(provider_name))
