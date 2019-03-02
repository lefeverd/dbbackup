import logging
from pathlib import Path
import subprocess
import tempfile
import shutil
import os
from datetime import datetime

from dbbackup.providers import AbstractProvider
from dbbackup import config

_logger = logging.getLogger(__name__)
DEFAULT_MYSQL_HOST = "127.0.0.1"
DEFAULT_MYSQL_USER = "root"
DEFAULT_MYSQL_BIN_DIRECTORY = "/usr/local/bin/"
DEFAULT_EXCLUDE_DATABASES = ["information_schema", "performance_schema"]


class MySQL(AbstractProvider):
    def __init__(self,
                 host=DEFAULT_MYSQL_HOST,
                 user=DEFAULT_MYSQL_USER,
                 password=None,
                 mysql_bin_directory=DEFAULT_MYSQL_BIN_DIRECTORY,
                 exclude_databases=DEFAULT_EXCLUDE_DATABASES):
        self.host = host
        self.user = user
        self.password = password
        self.mysql_bin_directory = mysql_bin_directory
        self.exclude_databases = exclude_databases

    def _get_default_command_args(self):
        args = ['-h', self.host, '-u', self.user]
        if self.password:
            args.append(f"-p{self.password}")
        return args

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

    def construct_backup_filename(self, database):
        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = config.BACKUP_SUFFIX or ""
        return f"{date_str}-{database}{suffix}.sql"

    def get_backup_absolute_file(self, database):
        filename = self.construct_backup_filename(database)
        return Path(config.BACKUP_DIRECTORY + '/' + filename).resolve()

    def backup_database(self, database):
        _logger.debug(f"Starting backup for database {database}")
        mysqldump_bin = str(
            Path(self.mysql_bin_directory + '/mysqldump').resolve())
        backup_cmd = [mysqldump_bin]
        backup_cmd += self._get_default_command_args()
        backup_cmd += ["--databases", f"{database}"]
        _logger.debug(f"command: {backup_cmd}")
        _logger.debug(f"command (str): {(' ').join(backup_cmd)}")
        fd, path = tempfile.mkstemp()
        try:
            _logger.debug(f"Starting backup in file {path}")
            output = subprocess.check_call(backup_cmd, stdout=fd)
            output_file = self.get_backup_absolute_file(database)
            _logger.debug(f"Copying file to final destination {output_file}")
            shutil.copy(path, str(output_file))
            _logger.debug("Done")
        finally:
            _logger.debug("Removing temporary file")
            os.remove(path)
            _logger.debug("Done")
        _logger.debug(f"Command output: {output}")

    def execute_backup(self):
        databases = self.get_databases()
        databases = [
            database for database in databases
            if database not in self.exclude_databases
        ]
        _logger.debug(f"Found databases: {databases}")
        for database in databases:
            self.backup_database(database)

    def list_backups(self):
        print("Listing backups")
