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


def is_concrete_provider(provider):
    return inspect.isclass(provider) \
        and provider.__name__ != AbstractProvider.__name__ \
        and issubclass(provider, AbstractProvider)


def get_provider_module(module_name):
    return import_module('.' + module_name, package=__package__)


def get_provider_class(provider_module):
    clsmembers = inspect.getmembers(provider_module, is_concrete_provider)
    if not clsmembers or len(clsmembers) != 1:
        raise ProviderClassNotFoundError(
            f"Could not find subclass of {AbstractProvider.__name__} \
            in {provider_module.__name__}")
    return clsmembers[0][1]


def get(provider_name, *args, **kwargs):
    try:
        _logger.debug(f"Getting provider {provider_name}")
        provider_module = get_provider_module(provider_name)
        _logger.debug(f"Got module {provider_module}")
        provider_class = get_provider_class(provider_module)
        _logger.debug(f"Got class {provider_class}")
        provider_instance = provider_class(*args, **kwargs)
        _logger.debug(f"Created instance {provider_instance}")
        return provider_instance
    except (AttributeError, ModuleNotFoundError):
        raise ImportError('Could not find {} provider.'.format(provider_name))
