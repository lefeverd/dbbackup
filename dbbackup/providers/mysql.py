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
DEFAULT_MYSQL_HOST = "127.0.0.1"
DEFAULT_MYSQL_USER = "root"
DEFAULT_MYSQL_BIN_DIRECTORY = "/usr/local/bin/"
DEFAULT_COMPRESS = False


class MySQL(AbstractProvider):
    def __init__(self,
                 host=DEFAULT_MYSQL_HOST,
                 user=DEFAULT_MYSQL_USER,
                 password=None,
                 mysql_bin_directory=DEFAULT_MYSQL_BIN_DIRECTORY,
                 compress=DEFAULT_COMPRESS):
        self.host = host
        self.user = user
        self.password = password
        self.mysql_bin_directory = mysql_bin_directory
        self.compress = compress

    def _get_default_command_args(self):
        args = ['-h', self.host, '-u', self.user]
        if self.password:
            args.append(f"-p{self.password}")
        return args

    def execute_backup(self, database=None, exclude=None):
        databases = self.get_databases()

        if database:
            if database not in databases:
                raise Exception(f"Database {database} doesn't exist.")
            databases = [database]

        # Filter out excluded databases
        if exclude:
            databases = [db for db in databases if db not in exclude]

        _logger.debug(f"Starting backup of databases: {databases}")
        for database in databases:
            self.backup_database(database)

    def get_databases(self):
        get_db_cmd = self._get_databases_command()
        databases = subprocess.check_output(get_db_cmd).splitlines()
        databases = [database.decode('utf-8') for database in databases]
        return databases

    def _get_command(self):
        mysql_bin_path = Path(self.mysql_bin_directory + '/mysql')
        mysql_bin = str(mysql_bin_path.resolve())
        if not mysql_bin_path.exists():
            raise Exception(f"mysql binary not found: {mysql_bin}")
        command = [mysql_bin]
        command += self._get_default_command_args()
        return command

    def _get_databases_command(self):
        command = self._get_command()
        command += ['--skip-column-names', '-e', 'SHOW DATABASES;']
        _logger.debug(f"command: {command}")
        _logger.debug(f"command (str): {(' ').join(command)}")
        return command

    def backup_database(self, database):
        _logger.info(f"Starting backup for database {database}")
        filename = self.construct_backup_filename(database)
        with TemporaryBackupFile(filename, config.BACKUP_DIRECTORY,
                                 self.compress) as temp_file:
            backup_cmd = self._get_backup_command(database)
            try:
                completed_process = subprocess.run(
                    backup_cmd, stdout=temp_file)
                _logger.debug(
                    f"Command output: {completed_process.returncode}")
            except subprocess.CalledProcessError as e:
                raise Exception(
                    f"Could not backup database {database}: {e.stderr}")

        _logger.info("Done")

    def _get_backup_command(self, database):
        mysqldump_bin = str(
            Path(self.mysql_bin_directory + '/mysqldump').resolve())
        backup_cmd = [mysqldump_bin]
        backup_cmd += self._get_default_command_args()
        backup_cmd += ["--databases", f"{database}"]
        _logger.debug(f"command: {backup_cmd}")
        _logger.debug(f"command (str): {(' ').join(backup_cmd)}")
        return backup_cmd

    def construct_backup_filename(self, database):
        date_str = self._get_formatted_current_datetime()
        suffix = config.BACKUP_SUFFIX or ""
        return f"{date_str}-{database}{suffix}.sql"

    def _get_formatted_current_datetime(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")

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
        file_name = Path(a_file).name
        return (re.search(r"^\d{8}_\d{6}.*", file_name)
                and (file_name.endswith(".sql") or file_name.endswith(".gz"))
                and (config.BACKUP_SUFFIX in file_name
                     if config.BACKUP_SUFFIX else True))

    def restore_backup(self, backup_file, database, recreate=None,
                       create=None):
        backup_file = self.verify_backup_file(backup_file)
        tmpdir = None
        if not self.is_backup(backup_file):
            raise Exception(f"File {backup_file} is not a valid backup.")

        if backup_file.endswith(".gz"):
            tmpdir = tempfile.mkdtemp()
            with tarfile.open(backup_file) as tf:
                tf.extractall(path=tmpdir)
            backup_file = Path(tmpdir) / Path(backup_file).name[:-3]

        command = self._get_restore_command()
        backup_file_fd = open(backup_file)

        try:
            completed_proc = subprocess.run(
                command, stdin=backup_file_fd, check=True, capture_output=True)
            _logger.debug(
                f"Restore process retcode {completed_proc.returncode}")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Could not restore: {e}")

        if tmpdir:
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                _logger.warn(f"Could not delete temporary directory {tmpdir}")

    def _get_restore_command(self):
        command = self._get_command()
        return command
