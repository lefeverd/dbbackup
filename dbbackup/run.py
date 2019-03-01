import logging
import click
import os

from dbbackup import config
from dbbackup import providers

_logger = logging.getLogger(__package__)


def configure_logging():
    logging.basicConfig(level=config.LOG_LEVEL.upper())
    _logger.debug("logging configured")


def create_backup_directory():
    _logger.debug("Creating backup directory")
    os.makedirs(config.BACKUP_DIRECTORY)


@click.group()
@click.option(
    '--provider',
    default=config.PROVIDER,
    type=click.Choice(['mysql', 'postgres']))
@click.pass_context
def cligroup(ctx, provider):
    ctx.ensure_object(dict)
    ctx.obj['provider_name'] = provider
    ctx.obj['provider'] = providers.get(provider)


def invoke(ctx, command):
    provider = ctx.obj.get('provider', False)
    if not provider:
        raise Exception("Could not get provider from ctx.")
    _logger.debug(f"Executing {command} on {provider}")
    getattr(provider, command)()


@cligroup.command(name="backup")
@click.pass_context
def backup_command(ctx):
    invoke(ctx, "execute_backup")


@cligroup.command(name="list")
@click.pass_context
def list_command(ctx):
    invoke(ctx, "list_backups")


def main():
    configure_logging()
    create_backup_directory()
    cligroup()


if __name__ == "__main__":
    main()
