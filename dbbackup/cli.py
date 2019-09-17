import logging
import click

from dbbackup import builders

_logger = logging.getLogger(__package__)


class MySQLDatabaseCommand(click.MultiCommand):
    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.provider = builders.get(name)
        self.commands = {
            "backup": self.cmd_backup,
            "list": self.cmd_list,
            "restore": self.cmd_restore,
            "cleanup": self.cmd_cleanup
        }

    def cmd_backup(self):
        return click.Command(
            "backup", callback=getattr(self.provider, "execute_backup"),
            params=[
                click.Argument(["database"], required=False),
                click.Option(
                    ["-e", "--exclude"],
                    multiple=True,
                    help="Exclude database. You can use this option multiple times \
                    to exclude multiple databases.")],
            help="Backup the specified database, or all if none is specified. System databases "
            "such as information_schema and performance_schema will not be included by default, "
            "unless specified.")

    def cmd_list(self):
        return click.Command(
            "list", callback=getattr(self.provider, "list_backups"))

    def cmd_restore(self):
        return click.Command(
            "restore",
            callback=getattr(self.provider, "restore_backup"),
            params=[
                click.Argument(["backup_file"]),
                click.Argument(["database"]),
                click.Option(
                    ["--recreate"],
                    is_flag=True,
                    help="Drop the database if it already exists (display a warning if not), "
                        "and create the database."),
                click.Option(["--create"],
                             is_flag=True,
                             help="Create the database. Will raise an \
                             exception if the database already exists.")
            ])

    def cmd_cleanup(self):
        return click.Command(
            "cleanup", 
            callback=getattr(self.provider, "cleanup"),
            params=[
                click.Argument(["days_to_keep"])])

    def list_commands(self, ctx):
        return self.commands.keys()

    def get_command(self, ctx, cmd_name):
        return self.commands.get(cmd_name)()


class PostgreSQLDatabaseCommand(click.MultiCommand):
    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.provider = builders.get(name)
        self.commands = {
            "backup": self.cmd_backup,
            "list": self.cmd_list,
            "restore": self.cmd_restore,
            "cleanup": self.cmd_cleanup
        }

    def cmd_backup(self):
        return click.Command(
            "backup", callback=getattr(self.provider, "execute_backup"),
            params=[
                click.Argument(["database"], required=False),
                click.Option(
                    ["-e", "--exclude"],
                    multiple=True,
                    help="Exclude database. You can use this option multiple times "
                    "to exclude multiple databases.")],
            help="Backup the specified database, or all if none is specified.")

    def cmd_list(self):
        return click.Command(
            "list", callback=getattr(self.provider, "list_backups"))

    def cmd_restore(self):
        return click.Command(
            "restore",
            callback=getattr(self.provider, "restore_backup"),
            params=[
                click.Argument(["backup_file"]),
                click.Argument(["database"]),
                click.Option(
                    ["--recreate"],
                    is_flag=True,
                    help="Drop the database if it already exists (display a warning if not), "
                        "and create the database."),
                click.Option(["--create"],
                             is_flag=True,
                             help="Create the database. Will raise an "
                             "exception if the database already exists.")
            ])

    def cmd_cleanup(self):
        return click.Command(
            "cleanup", 
            callback=getattr(self.provider, "cleanup"),
            params=[
                click.Argument(["days_to_keep"])])

    def list_commands(self, ctx):
        return self.commands.keys()

    def get_command(self, ctx, cmd_name):
        return self.commands.get(cmd_name)()


class RootGroup(click.Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


def get_cli():
    root_group = RootGroup()
    mysql_commands = MySQLDatabaseCommand("mysql")
    root_group.add_command(mysql_commands)
    postgres_commands = PostgreSQLDatabaseCommand("postgres")
    root_group.add_command(postgres_commands)
    return root_group
