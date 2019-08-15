import logging
from pathlib import Path
import subprocess
import os
from datetime import datetime
import re
import tarfile
import tempfile
import shutil

from dbbackup.providers import AbstractProvider
from dbbackup import config
from dbbackup.tempbackupfile import TemporaryBackupFile
from dbbackup.utils import sizeof_fmt

_logger = logging.getLogger(__name__)
DEFAULT_PSQL_HOST = "127.0.0.1"
DEFAULT_PSQL_PORT = "5432"
DEFAULT_PSQL_USER = "postgres"
DEFAULT_PSQL_BIN_DIRECTORY = "/usr/local/bin/"
DEFAULT_EXCLUDE_DATABASES = []
DEFAULT_BACKUP_TYPE = "c"  # c|d|t|p (custom, directory, tar, plain text)
"""
PostgreSQL backup provider.
"""


class Postgres(AbstractProvider):
    def __init__(self,
                 psql_bin_directory=DEFAULT_PSQL_BIN_DIRECTORY,
                 exclude_databases=DEFAULT_EXCLUDE_DATABASES,
                 backup_type=DEFAULT_BACKUP_TYPE):
        """
        Postgres environment variables will be respected,
        see https://www.postgresql.org/docs/9.3/libpq-envars.html
        """
        self.psql_bin_directory = psql_bin_directory
        self.exclude_databases = exclude_databases
        self.backup_type = backup_type
        self.validate_config()

    def validate_config(self):
        if self.backup_type not in ('c', 'd', 't', 'p'):
            raise Exception(
                "backup_type must be c, d, t or p (see pg_dump help)")

    def _get_default_command_args(self):
        return []

    def execute_backup(self):
        databases = self.get_databases()
        databases = [
            database for database in databases
            if database not in self.exclude_databases
        ]
        _logger.debug(f"Found databases: {databases}")
        for database in databases:
            self.backup_database(database)

    def get_databases(self):
        get_db_cmd = self._get_databases_command()
        databases = subprocess.check_output(get_db_cmd).splitlines()
        databases = [database.decode('utf-8') for database in databases]
        return databases

    def _get_databases_command(self):
        command = self._get_command()
        command += [
            '-At', '-c',
            'select datname from pg_database where not datistemplate and datallowconn order by datname;'
        ]
        _logger.debug(f"command: {command}")
        _logger.debug(f"command (str): {(' ').join(command)}")
        return command

    def _get_command(self):
        psql_bin_path = Path(self.psql_bin_directory + '/psql')
        psql_bin = str(psql_bin_path.resolve())
        if not psql_bin_path.exists():
            raise Exception(f"psql binary not found: {psql_bin}")
        command = [psql_bin]
        command += self._get_default_command_args()
        return command

    def backup_database(self, database):
        _logger.info(f"Starting backup for database {database}")
        filename = self.construct_backup_filename(database)
        with TemporaryBackupFile(filename,
                                 config.BACKUP_DIRECTORY) as temp_file:
            backup_cmd = self._get_backup_command(database)
            output = subprocess.check_call(backup_cmd, stdout=temp_file)
            _logger.debug(f"Command output: {output}")
        _logger.info("Done")

    def _get_backup_command(self, database):
        pg_dump_bin_path = Path(self.psql_bin_directory + '/pg_dump')
        pg_dump_bin = str(pg_dump_bin_path.resolve())
        if not pg_dump_bin_path.exists():
            raise Exception(f"pg_dump binary not found: {pg_dump_bin}")

        backup_cmd = [pg_dump_bin]
        backup_cmd += self._get_default_command_args()
        backup_cmd.append(f"-F{self.backup_type}")
        backup_cmd.append(database)
        _logger.debug(f"command: {backup_cmd}")
        _logger.debug(f"command (str): {(' ').join(backup_cmd)}")
        return backup_cmd

    def construct_backup_filename(self, database):
        date_str = self._get_formatted_current_datetime()
        suffix = config.BACKUP_SUFFIX or ""
        extension = self.get_extension()
        return f"{date_str}-{database}{suffix}{extension}"

    def _get_formatted_current_datetime(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def get_extension(self):
        if self.backup_type == 'p':
            return ".sql"
        if self.backup_type == 'c':
            return ".dump"
        if self.backup_type == 't':
            return ".tar"

    def list_backups(self):
        _logger.debug("Listing backups")
        _logger.info(f"Backup directory: {config.BACKUP_DIRECTORY}")
        backup_files = self.get_backups()
        for backup_file in backup_files:
            self.display_backup(backup_file)

    def display_backup(self, backup_file):
        size = os.stat(
            str(Path(config.BACKUP_DIRECTORY + "/" +
                     backup_file).resolve())).st_size
        print(f"{backup_file}\t{sizeof_fmt(size)}")

    def get_backups(self):
        backup_files = [
            a_file for a_file in os.listdir(config.BACKUP_DIRECTORY)
            if self.is_backup(a_file)
        ]
        backup_files.sort(reverse=True)
        return backup_files

    def is_backup(self, a_file):
        return (
            re.search(r"^\d{8}_\d{6}.*", a_file)
            and (a_file.endswith(".sql") or a_file.endswith(".tar")
                 or a_file.endswith(".dump")) and
            (config.BACKUP_SUFFIX in a_file if config.BACKUP_SUFFIX else True))

    def restore_backup(self, backup_file, force=None):
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

        backup_file = str(backup_file_path)
        tmpdir = None
        if not self.is_backup(backup_file_path.name):
            raise Exception(f"File {backup_file} is not a valid backup.")

        if backup_file.endswith(".gz"):
            tmpdir = tempfile.mkdtemp()
            with tarfile.open(backup_file) as tf:
                tf.extractall(path=tmpdir)
            backup_file = Path(tmpdir) / Path(backup_file).name[:-3]

        command = self._get_restore_command()
        command.append(backup_file)

        output = subprocess.check_output(command)
        _logger.debug(f"Restore process output {output}")

        if tmpdir:
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                _logger.warn(f"Could not delete temporary directory {tmpdir}")

    def _get_restore_command(self):
        pg_restore_bin_path = Path(self.psql_bin_directory + '/pg_restore')
        pg_restore_bin = str(pg_restore_bin_path.resolve())
        if not pg_restore_bin_path.exists():
            raise Exception(f"pg_restore binary not found: {pg_restore_bin}")

        restore_cmd = [pg_restore_bin]
        restore_cmd += self._get_default_command_args()
        restore_cmd.append("--exit-on-error")
        # Need to connect to an existing db, otherwise it will simply output to STDOUT
        restore_cmd += ["--dbname", "postgres"]
        restore_cmd.append("--create")
        _logger.debug(f"command: {restore_cmd}")
        _logger.debug(f"command (str): {(' ').join(restore_cmd)}")
        return restore_cmd