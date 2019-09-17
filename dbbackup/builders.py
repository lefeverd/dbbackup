import inspect
import logging
import sys
from dbbackup import config
from dbbackup.providers import AbstractProvider
from dbbackup.providers.mysql import MySQL
from dbbackup.providers.postgres import Postgres

_logger = logging.getLogger(__name__)


def get_builder_module(module_name):
    return sys.modules[__name__]


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


class ProviderClassNotFoundError(Exception):
    pass


class MySQLConfigBuilder:
    """
    Builds a mysql provider instance from the app config values
    """
    provider_for = "mysql"

    def __init__(self):
        self._instance = None

    def __call__(self):
        exclude_databases = config.EXCLUDE_DATABASES \
            and config.EXCLUDE_DATABASES.split(",") \
            or False
        kwargs = {
            "mysql_bin_directory": config.MYSQL_BIN_DIRECTORY,
            "compress": config.MYSQL_COMPRESS
        }
        if config.MYSQL_HOST:
            kwargs["host"] = config.MYSQL_HOST
        if config.MYSQL_USER:
            kwargs["user"] = config.MYSQL_USER
        if config.MYSQL_PASSWORD:
            kwargs["password"] = config.MYSQL_PASSWORD
        if exclude_databases:
            kwargs["exclude_databases"] = exclude_databases
        instance = MySQL(**kwargs)
        self._instance = instance
        return instance


class PostgresConfigBuilder:
    """
    Builds a postgres provider instance from the app config values
    """
    provider_for = "postgres"

    def __init__(self):
        self._instance = None

    def __call__(self):
        exclude_databases = config.EXCLUDE_DATABASES \
            and config.EXCLUDE_DATABASES.split(",") \
            or False
        kwargs = {"psql_bin_directory": config.PG_BIN_DIRECTORY}
        if config.PG_BACKUP_TYPE:
            kwargs["backup_type"] = config.PG_BACKUP_TYPE
        if exclude_databases:
            kwargs["exclude_databases"] = exclude_databases
        instance = Postgres(**kwargs)
        self._instance = instance
        return instance
