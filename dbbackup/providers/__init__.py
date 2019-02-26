import abc
from importlib import import_module
import inspect
import logging

_logger = logging.getLogger(__name__)


class ProviderClassNotFoundError(Exception):
    pass


class AbstractProvider(abc.ABC):
    @abc.abstractclassmethod
    def execute_backup(self):
        pass

    @abc.abstractclassmethod
    def list_backups(self):
        pass


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
