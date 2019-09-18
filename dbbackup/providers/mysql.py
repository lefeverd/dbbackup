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
from dbbackup.tempbackupfile import TemporaryBackupFile
from dbbackup.utils import get_file_size, sizeof_fmt

_logger = logging.getLogger(__name__)
DEFAULT_MYSQL_HOST = "127.0.0.1"
DEFAULT_MYSQL_USER = "root"
DEFAULT_MYSQL_BIN_DIRECTORY = "/usr/local/bin/"
DEFAULT_COMPRESS = False
MYSQL_SYSTEM_DATABASES = ["performance_schema", "information_schema"]


class MySQL(AbstractProvider):
    def __init__(self,
                 backup_directory,
                 host=DEFAULT_MYSQL_HOST,
                 user=DEFAULT_MYSQL_USER,
                 password=None,
                 backup_suffix=None,
                 mysql_bin_directory=DEFAULT_MYSQL_BIN_DIRECTORY,
                 compress=DEFAULT_COMPRESS):
        super().__init__(backup_directory)
        self.host = host
        self.user = user
        self.password = password
        self.backup_suffix = backup_suffix
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

        if not exclude:
            exclude = []

        if not isinstance(exclude, (list, tuple)):
            exclude = tuple([exclude])

        # By default, exclude system databases (some are transient/memory, and could
        # result in access right issues)
        # Only exclude them if not expliticly trying to backup them.
        if database not in MYSQL_SYSTEM_DATABASES:
            exclude += tuple(MYSQL_SYSTEM_DATABASES)

        # Filter out excluded databases
        if exclude:
            databases = [db for db in databases if db not in exclude]

        _logger.debug(f"Starting backup of databases: {databases}")
        for database in databases:
            filename = self.backup_database(database)
            size = get_file_size(
                str(
                    Path(self.backup_directory + "/" + filename +
                         (self.compress and ".gz" or "")).resolve()))
            self.notify_callbacks('backup_done',
                                  datetime.now().isoformat(), database,
                                  filename, size)

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
        with TemporaryBackupFile(filename, self.backup_directory,
                                 self.compress) as temp_file:
            backup_cmd = self._get_backup_command(database)
            try:
                subprocess.run(backup_cmd, check=True, stdout=temp_file)
            except subprocess.CalledProcessError as e:
                raise Exception(
                    f"Could not backup database {database}: retcode {e.returncode} - stderr {e.stderr}."
                )
        _logger.info("Done")
        return filename

    def _get_backup_command(self, database):
        mysqldump_bin_path = Path(self.mysql_bin_directory + '/mysqldump')
        mysqldump_bin = str(mysqldump_bin_path.resolve())
        if not mysqldump_bin_path.exists():
            raise Exception(f"mysqldump binary not found: {mysqldump_bin}")

        backup_cmd = [mysqldump_bin]
        backup_cmd += self._get_default_command_args()
        # --databases add the CREATE DATABASE and USE <dbname> in the output
        #backup_cmd += ["--databases", f"{database}"]
        # To be able to restore using another database, do not use --databases
        backup_cmd.append(database)
        _logger.debug(f"command: {backup_cmd}")
        _logger.debug(f"command (str): {(' ').join(backup_cmd)}")
        return backup_cmd

    def construct_backup_filename(self, database):
        date_str = self._get_formatted_current_datetime()
        suffix = self.backup_suffix or ""
        return f"{date_str}-{database}{suffix}.sql"

    def _get_formatted_current_datetime(self):
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def list_backups(self):
        _logger.debug("Listing backups")
        _logger.info(f"Backup directory: {self.backup_directory}")
        backup_files = self.get_backups()
        for backup_file in backup_files:
            self.display_backup(backup_file)

    def display_backup(self, backup_file):
        size = get_file_size(
            str(Path(self.backup_directory + "/" + backup_file).resolve()))
        print(f"{backup_file}\t{sizeof_fmt(size)}")

    def get_backups(self):
        backup_files = [
            a_file for a_file in os.listdir(self.backup_directory)
            if self.is_backup(a_file)
        ]
        backup_files.sort(reverse=True)
        return backup_files

    def is_backup(self, a_file):
        file_name = Path(a_file).name
        return (
            re.search(r"^\d{8}_\d{6}.*", file_name)
            and (file_name.endswith(".sql") or file_name.endswith(".gz")) and
            (self.backup_suffix in file_name if self.backup_suffix else True))

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

        if recreate:
            try:
                self._drop_database(database)
            except Exception:
                _logger.warn(
                    f"Database {database} could not be dropped (maybe it doesn't exist)."
                )

        if recreate or create:
            try:
                self._create_database(database)
            except subprocess.CalledProcessError as e:
                raise Exception(
                    f"Could not create database {database}: {e.output}")

        command = self._get_restore_command()
        command += ["--database", database]
        backup_file_fd = open(backup_file)

        try:
            completed_proc = subprocess.run(
                command, stdin=backup_file_fd, check=True, capture_output=True)
            _logger.debug(
                f"Restore process retcode {completed_proc.returncode}")
        except subprocess.CalledProcessError as e:
            raise Exception(
                f"Could not restore database {database}: {e.output}, {e.stderr}"
            )

        if tmpdir:
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                _logger.warn(f"Could not delete temporary directory {tmpdir}")

    def _drop_database(self, database):
        drop_command = self._get_command()
        drop_command += ["-e", f"DROP DATABASE {database}"]
        output = subprocess.check_output(
            drop_command, stderr=subprocess.STDOUT)
        _logger.debug(f"drop process output {output}")

    def _create_database(self, database):
        create_command = self._get_command()
        create_command += ["-e", f"CREATE DATABASE {database}"]
        output = subprocess.check_output(
            create_command, stderr=subprocess.STDOUT)
        _logger.debug(f"drop process output {output}")

    def _get_restore_command(self):
        command = self._get_command()
        return command
