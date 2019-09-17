import os
import subprocess
from unittest import mock
from pathlib import Path
import tempfile
import requests

from pytest import raises, mark

from dbbackup import config
from dbbackup.providers.mysql import MySQL
from dbbackup.callbacks.prometheus import PrometheusPushGatewayCallback


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
                assert "20190101_000000-test-daily.sql" in backups
                assert "20190101_000000-sys-daily.sql" in backups
                assert "20190101_000000-mysql-daily.sql" in backups

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_specific_database_correctly_done(self, mock_datetime,
                                                     mysql_provider):
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            temp_dir):
                mysql_provider.execute_backup(database="test")
                backups = os.listdir(temp_dir)
                assert len(backups) == 1
                assert "20190101_000000-test-daily.sql" in backups

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_specific_unexisting_database(self, mock_datetime,
                                                 mysql_provider):
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            temp_dir):
                with raises(Exception) as e:
                    mysql_provider.execute_backup(database="testfake")
                assert "Database testfake doesn't exist" in str(e.value)

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_specific_unexisting_database_backup_database(
            self, mock_datetime, mysql_provider):
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            temp_dir):
                with raises(Exception) as e:
                    mysql_provider.backup_database(database="testfake")
                assert "Could not backup database testfake: retcode 2 - stderr None." in str(
                    e.value)

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_exclude_database_correctly_done(self, mock_datetime,
                                                    mysql_provider):
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            temp_dir):
                mysql_provider.execute_backup(exclude="sys")
                backups = os.listdir(temp_dir)
                assert len(backups) == 2
                assert "20190101_000000-mysql-daily.sql" in backups
                assert "20190101_000000-test-daily.sql" in backups

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_exclude_multiple_database_correctly_done(
            self, mock_datetime, mysql_provider):
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            temp_dir):
                mysql_provider.execute_backup(
                    exclude=["sys", "performance_schema"])
                backups = os.listdir(temp_dir)
                assert len(backups) == 2
                assert "20190101_000000-mysql-daily.sql" in backups
                assert "20190101_000000-test-daily.sql" in backups

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_system_database_correctly_done(self, mock_datetime,
                                                   mysql_provider):
        """
        By default, system databases (such as information_schema) are not backuped.
        """
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            temp_dir):
                with raises(Exception) as e:
                    # By default, it will raise an exception because of access rights.
                    # But at least, we'll know it tried to backup it.
                    mysql_provider.execute_backup(
                        database="information_schema")
                assert "Could not backup database information_schema: retcode 2 - stderr None." in str(
                    e.value)

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
        'dbbackup.callbacks.prometheus.PrometheusPushGatewayCallback.get_hostname'
    )
    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_done_pushgateway_callback(self, mock_datetime,
                                              mock_get_hostname):
        mock_datetime.return_value = "20190101_000000"
        mock_get_hostname.return_value = "myhostname"
        mysql = MySQL(
            user=config.MYSQL_USER,
            password=config.MYSQL_PASSWORD,
            host=config.MYSQL_HOST,
            mysql_bin_directory=config.MYSQL_BIN_DIRECTORY)
        pushgateway_callback = PrometheusPushGatewayCallback(
            config.PROMETHEUS_PUSHGATEWAY_URL)
        mysql.register_callback(pushgateway_callback)
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            temp_dir):
                mysql.execute_backup()
                response = requests.get(
                    f"{config.PROMETHEUS_PUSHGATEWAY_URL}/metrics")
                assert response.status_code == 200
                metrics = response.text
                assert 'dbbackup_last_backup_file_size{instance="",job="myhostname-test"}' in metrics
                assert 'dbbackup_last_success_timestamp{instance="",job="myhostname-test"}' in metrics
                assert 'dbbackup_last_backup_file_size{instance="",job="myhostname-mysql"}' in metrics
                assert 'dbbackup_last_success_timestamp{instance="",job="myhostname-mysql"}' in metrics
                assert 'dbbackup_last_backup_file_size{instance="",job="myhostname-sys"}' in metrics
                assert 'dbbackup_last_success_timestamp{instance="",job="myhostname-sys"}' in metrics

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
                mysql_provider.restore_backup(
                    backup_file.resolve(), "test", create=True)
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
                        mysql_provider.restore_backup(backup_file, "test")
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
                mysql_provider.restore_backup(backup_file, "test", create=True)
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
                    mysql_provider.restore_backup(backup_file, "test")
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
                mysql.restore_backup(backup_file, "test", create=True)
                users = get_users(mysql, "test")
                assert len(users) == 1
                assert users[0][0] == "1"
                assert users[0][1] == "supertestuser"

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_restore_other_database(self, mock_datetime, mysql_provider,
                                           drop_database):
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            str(Path(temp_dir).resolve())):
                drop_database("testnew")
                mysql_provider.execute_backup()
                backup_file = "20190101_000000-test-daily.sql"
                mysql_provider.restore_backup(
                    backup_file, "testnew", create=True)
                users = get_users(mysql_provider, "test")
                assert len(users) == 1
                assert users[0][0] == "1"
                assert users[0][1] == "supertestuser"
                users = get_users(mysql_provider, "testnew")
                assert len(users) == 1
                assert users[0][0] == "1"
                assert users[0][1] == "supertestuser"

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_restore_create_database_already_exists(
            self, mock_datetime, mysql_provider, drop_database):
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            str(Path(temp_dir).resolve())):
                mysql_provider.execute_backup()
                backup_file = "20190101_000000-test-daily.sql"
                with raises(Exception) as e:
                    mysql_provider.restore_backup(
                        backup_file, "test", create=True)
                assert "Could not create database" in str(e.value)
                assert "database exists" in str(e.value)

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_restore_other_database_unexisting(
            self, mock_datetime, mysql_provider, drop_database):
        mock_datetime.return_value = "20190101_000000"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            str(Path(temp_dir).resolve())):
                drop_database("testnew")
                mysql_provider.execute_backup()
                backup_file = "20190101_000000-test-daily.sql"
                with raises(Exception) as e:
                    mysql_provider.restore_backup(backup_file, "testnew")
                assert "Unknown database" in str(e.value)
