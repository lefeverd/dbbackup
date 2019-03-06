import logging
from pathlib import Path
import subprocess
import os
from datetime import datetime
import re

from dbbackup.providers import AbstractProvider
from dbbackup import config
from dbbackup.tempbackupfile import TemporaryBackupFile
from dbbackup.utils import sizeof_fmt

_logger = logging.getLogger(__name__)
DEFAULT_MYSQL_HOST = "127.0.0.1"
DEFAULT_MYSQL_USER = "root"
DEFAULT_MYSQL_BIN_DIRECTORY = "/usr/local/bin/"
DEFAULT_EXCLUDE_DATABASES = ["information_schema", "performance_schema"]
DEFAULT_COMPRESS = False


class MySQL(AbstractProvider):
    def __init__(self,
                 host=DEFAULT_MYSQL_HOST,
                 user=DEFAULT_MYSQL_USER,
                 password=None,
                 mysql_bin_directory=DEFAULT_MYSQL_BIN_DIRECTORY,
                 exclude_databases=DEFAULT_EXCLUDE_DATABASES,
                 compress=DEFAULT_COMPRESS):
        self.host = host
        self.user = user
        self.password = password
        self.mysql_bin_directory = mysql_bin_directory
        self.exclude_databases = exclude_databases
        self.compress = compress

    def _get_default_command_args(self):
        args = ['-h', self.host, '-u', self.user]
        if self.password:
            args.append(f"-p{self.password}")
        return args

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
        mysql_bin = str(Path(self.mysql_bin_directory + '/mysql').resolve())
        get_db_cmd = [mysql_bin]
        get_db_cmd += self._get_default_command_args()
        get_db_cmd += ['--skip-column-names', '-e', 'SHOW DATABASES;']
        _logger.debug(f"command: {get_db_cmd}")
        _logger.debug(f"command (str): {(' ').join(get_db_cmd)}")
        databases = subprocess.check_output(get_db_cmd).splitlines()
        databases = [database.decode('utf-8') for database in databases]
        return databases

    def backup_database(self, database):
        _logger.debug(f"Starting backup for database {database}")
        filename = self.construct_backup_filename(database)
        with TemporaryBackupFile(filename, config.BACKUP_DIRECTORY,
                                 self.compress) as temp_file:
            backup_cmd = self.get_backup_command(database)
            output = subprocess.check_call(backup_cmd, stdout=temp_file)
            _logger.debug(f"Command output: {output}")
        _logger.debug("Done")

    def get_backup_command(self, database):
        mysqldump_bin = str(
            Path(self.mysql_bin_directory + '/mysqldump').resolve())
        backup_cmd = [mysqldump_bin]
        backup_cmd += self._get_default_command_args()
        backup_cmd += ["--databases", f"{database}"]
        _logger.debug(f"command: {backup_cmd}")
        _logger.debug(f"command (str): {(' ').join(backup_cmd)}")
        return backup_cmd

    def construct_backup_filename(self, database):
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = config.BACKUP_SUFFIX or ""
        return f"{date_str}-{database}{suffix}.sql"

    def list_backups(self):
        _logger.debug("Listing backups")
        backup_files = self.get_backups()
        for backup_file in backup_files:
            self.display_backup(backup_file)

    def display_backup(self, backup_file):
        size = os.stat(
            str(
                Path(self.get_backup_absolute_directory() + "/" +
                     backup_file).resolve())).st_size
        print(f"{backup_file}\t{sizeof_fmt(size)}")

    def get_backups(self):
        directory = self.get_backup_absolute_directory()
        backup_files = [
            a_file for a_file in os.listdir(directory)
            if self.is_backup(a_file)
        ]
        backup_files.sort(reverse=True)
        return backup_files

    def is_backup(self, a_file):
        return (re.search(r"^\d{8}_\d{6}.*", a_file)
                and (a_file.endswith(".sql") or a_file.endswith(".tar.gz"))
                and config.BACKUP_SUFFIX in a_file)
