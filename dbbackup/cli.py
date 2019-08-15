import logging
import click

from dbbackup import providers

_logger = logging.getLogger(__package__)


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


class RootGroup(click.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def get_cli():
    root_group = RootGroup()
    mysql_commands = DatabaseCommand("mysql")
    root_group.add_command(mysql_commands)
    postgres_commands = DatabaseCommand("postgres")
    root_group.add_command(postgres_commands)
    return root_group
