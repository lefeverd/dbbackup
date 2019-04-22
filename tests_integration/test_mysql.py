import os
import subprocess
from unittest import mock
from pathlib import Path
import tempfile

from pytest import raises, mark

from dbbackup import config
from dbbackup.providers.mysql import MySQL


def get_users(mysql_provider, database):
    res = []
    command = mysql_provider._get_command()
    command += [
        '-D', database, '--skip-column-names', '-e', "select * from users;"
    ]
    proc = subprocess.run(command, stdout=subprocess.PIPE)
    for line in proc.stdout.splitlines():
        user_id, username = line.split()
        res.append((user_id.decode('utf-8'), username.decode('utf-8')))
    return res


@mark.usefixtures("test_database")
class TestMysql:
    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_correctly_done(self, mock_datetime, mysql_provider):
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            temp_dir):
                mysql_provider.execute_backup()
                backups = os.listdir(temp_dir)
                assert len(backups) == 3
                assert "20190101_000000-sys-daily.sql" in backups
                assert "20190101_000000-mysql-daily.sql" in backups
                assert "20190101_000000-test-daily.sql" in backups

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_multiple_databases_correctly_done(
            self, mock_datetime, mysql_provider, create_database,
            seed_database):
        mock_datetime.return_value = "20190101_000000"
        create_database("another")
        seed_database("another")
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            temp_dir):
                mysql_provider.execute_backup()
                backups = os.listdir(temp_dir)
                assert len(backups) == 4
                assert "20190101_000000-sys-daily.sql" in backups
                assert "20190101_000000-mysql-daily.sql" in backups
                assert "20190101_000000-test-daily.sql" in backups
                assert "20190101_000000-another-daily.sql" in backups

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_compression(self, mock_datetime):
        mysql = MySQL(
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            host=config.MYSQL_HOST,
            mysql_bin_directory=config.MYSQL_BIN_DIRECTORY,
            compress=True)
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            temp_dir):
                mysql.execute_backup()
                backups = os.listdir(temp_dir)
                assert len(backups) == 3
                assert "20190101_000000-sys-daily.sql.gz" in backups
                assert "20190101_000000-mysql-daily.sql.gz" in backups
                assert "20190101_000000-test-daily.sql.gz" in backups

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_get_backups(self, mock_datetime, mysql_provider):
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            temp_dir):
                mysql_provider.execute_backup()
                backups = mysql_provider.get_backups()
                assert len(backups) == 3
                assert "20190101_000000-sys-daily.sql" in backups
                assert "20190101_000000-mysql-daily.sql" in backups
                assert "20190101_000000-test-daily.sql" in backups

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_get_backups_with_compression(self, mock_datetime):
        mysql = MySQL(
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            host=config.MYSQL_HOST,
            mysql_bin_directory=config.MYSQL_BIN_DIRECTORY,
            compress=True)
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            temp_dir):
                mysql.execute_backup()
                backups = mysql.get_backups()
                assert len(backups) == 3
                assert "20190101_000000-sys-daily.sql.gz" in backups
                assert "20190101_000000-mysql-daily.sql.gz" in backups
                assert "20190101_000000-test-daily.sql.gz" in backups

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_restore(self, mock_datetime, mysql_provider,
                            drop_database):
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            str(Path(temp_dir).resolve())):
                mysql_provider.execute_backup()
                drop_database("test")
                users = get_users(mysql_provider, "test")
                assert len(users) == 0
                backup_file = Path(temp_dir) / "20190101_000000-test-daily.sql"
                mysql_provider.restore_backup(backup_file.resolve())
                users = get_users(mysql_provider, "test")
                assert len(users) == 1
                assert users[0][0] == "1"
                assert users[0][1] == "supertestuser"

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_restore_file_not_in_backup_directory(
            self, mock_datetime, mysql_provider):
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            str(Path(temp_dir).resolve())):
                mysql_provider.execute_backup()
                with tempfile.TemporaryDirectory() as tempdir:
                    backup_file = Path(
                        tempdir) / "20190101_000000-test-daily.sql"
                    open(backup_file, 'a').close()
                    with raises(Exception) as e:
                        mysql_provider.restore_backup(backup_file)
                    assert 'is not inside BACKUP_DIRECTORY' in str(e.value)

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_restore_relative_file(self, mock_datetime, mysql_provider,
                                          drop_database):
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            str(Path(temp_dir).resolve())):
                mysql_provider.execute_backup()
                drop_database("test")
                users = get_users(mysql_provider, "test")
                assert len(users) == 0
                backup_file = "20190101_000000-test-daily.sql"
                mysql_provider.restore_backup(backup_file)
                users = get_users(mysql_provider, "test")
                assert len(users) == 1
                assert users[0][0] == "1"
                assert users[0][1] == "supertestuser"

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_restore_unexisting_file(self, mock_datetime,
                                            mysql_provider):
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            str(Path(temp_dir).resolve())):
                mysql_provider.execute_backup()
                backup_file = "20190101_000000-test-daily-fake.sql"
                with raises(Exception) as e:
                    mysql_provider.restore_backup(backup_file)
                assert "does not exist" in str(e.value)

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_restore_compressed_file(self, mock_datetime,
                                            drop_database):
        mysql = MySQL(
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            host=config.MYSQL_HOST,
            mysql_bin_directory=config.MYSQL_BIN_DIRECTORY,
            compress=True)
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            str(Path(temp_dir).resolve())):
                mysql.execute_backup()
                drop_database("test")
                users = get_users(mysql, "test")
                assert len(users) == 0
                backup_file = "20190101_000000-test-daily.sql.gz"
                mysql.restore_backup(backup_file)
                users = get_users(mysql, "test")
                assert len(users) == 1
                assert users[0][0] == "1"
                assert users[0][1] == "supertestuser"
