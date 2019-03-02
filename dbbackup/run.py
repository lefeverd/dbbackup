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
    os.makedirs(config.BACKUP_DIRECTORY, exist_ok=True)


class DatabaseCommand(click.MultiCommand):
    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.provider = providers.get(name)
        self.commands = {
            "backup": getattr(self.provider, "execute_backup"),
            "list": getattr(self.provider, "list_backups"),
        }

    def list_commands(self, ctx):
        return self.commands.keys()

    def get_command(self, ctx, cmd_name):
        return click.Command(
            cmd_name, callback=self.commands.get(cmd_name, None))


@click.group()
def cliroot():
    pass


def main():
    configure_logging()
    create_backup_directory()
    mysql_commands = DatabaseCommand("mysql")
    cliroot.add_command(mysql_commands)
    cliroot()


if __name__ == "__main__":
    main()
