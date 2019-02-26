import logging
from pathlib import Path
import subprocess

from dbbackup.providers import AbstractProvider

_logger = logging.getLogger(__name__)
DEFAULT_MYSQL_HOST = "127.0.0.1"
DEFAULT_MYSQL_USER = "root"
DEFAULT_MYSQL_BIN_DIRECTORY = "/usr/local/bin/"


class MySQL(AbstractProvider):
    def __init__(self,
                 host=DEFAULT_MYSQL_HOST,
                 user=DEFAULT_MYSQL_USER,
                 password=None,
                 mysql_bin_directory=DEFAULT_MYSQL_BIN_DIRECTORY):
        self.host = host
        self.user = user
        self.password = password
        self.mysql_bin_directory = mysql_bin_directory

    def get_databases(self):
        mysql_bin = str(Path(self.mysql_bin_directory + '/mysql').resolve())
        get_db_cmd = [
            mysql_bin, '--skip-column-names', '-h', self.host, '-u', self.user
        ]
        if self.password:
            get_db_cmd.append(f"-p{self.password}")
        get_db_cmd.append('-e')
        get_db_cmd.append('SHOW DATABASES;')
        _logger.debug(f"command: {get_db_cmd}")
        _logger.debug(f"command (str): {(' ').join(get_db_cmd)}")
        databases = subprocess.check_output(get_db_cmd).splitlines()
        return databases

    def execute_backup(self):
        # grep -Ev "(Database|information_schema|performance_schema)
        databases = self.get_databases()
        _logger.debug(f"Found databases: {databases}")
        #backup_cmd = ['/usr/bin/mysqldump']
        #subprocess.check_call(backup_cmd)
        print("Executing MySQL backup")

    def list_backups(self):
        print("Listing backups")
