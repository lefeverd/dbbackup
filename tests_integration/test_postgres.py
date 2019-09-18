import os
import subprocess
from unittest import mock
from pathlib import Path
import tempfile

from pytest import raises, mark

from dbbackup import config
from dbbackup.providers.postgres import Postgres


def get_users(postgres_provider, database):
    res = []
    command = postgres_provider._get_command()
    command += [database, '-At', '-c', "select * from users;"]
    proc = subprocess.run(command, stdout=subprocess.PIPE)
    for line in proc.stdout.splitlines():
        user_id, username = line.decode().split("|")
        res.append((user_id, username))
    return res


@mark.usefixtures("test_postgres_database")
class TestPostgres:
    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_correctly_done(self, mock_datetime, postgres_provider):
        mock_datetime.return_value = "20190101_000000"
        postgres_provider.execute_backup()
        backups = os.listdir(postgres_provider.backup_directory)
        assert len(backups) == 2
        assert "20190101_000000-postgres.dump" in backups
        assert "20190101_000000-test.dump" in backups

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_specific_database_correctly_done(self, mock_datetime,
                                                     postgres_provider):
        mock_datetime.return_value = "20190101_000000"
        postgres_provider.execute_backup(database="test")
        backups = os.listdir(postgres_provider.backup_directory)
        assert len(backups) == 1
        assert "20190101_000000-test.dump" in backups

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_specific_unexisting_database(self, mock_datetime,
                                                 postgres_provider):
        mock_datetime.return_value = "20190101_000000"
        with raises(Exception) as e:
            postgres_provider.execute_backup(database="testfake")
        assert "Database testfake doesn't exist" in str(e.value)

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_specific_unexisting_database_backup_database(
            self, mock_datetime, postgres_provider):
        mock_datetime.return_value = "20190101_000000"
        with raises(Exception) as e:
            postgres_provider.backup_database(database="testfake")
        assert "Could not backup database testfake: retcode 1 - stderr None." in str(
            e.value)

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_exclude_database_correctly_done(self, mock_datetime,
                                                    postgres_provider):
        mock_datetime.return_value = "20190101_000000"
        postgres_provider.execute_backup(exclude="postgres")
        backups = os.listdir(postgres_provider.backup_directory)
        assert len(backups) == 1
        assert "20190101_000000-test.dump" in backups

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_exclude_multiple_database_correctly_done(
            self, mock_datetime, postgres_provider, create_postgres_database):
        mock_datetime.return_value = "20190101_000000"
        create_postgres_database("another")
        postgres_provider.execute_backup(exclude=["test", "postgres"])
        backups = os.listdir(postgres_provider.backup_directory)
        assert len(backups) == 1
        assert "20190101_000000-another.dump" in backups

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_compression(self, mock_datetime):
        with tempfile.TemporaryDirectory() as temp_dir:
            postgres = Postgres(
                str(Path(temp_dir).resolve()),
                psql_bin_directory=config.PG_BIN_DIRECTORY,
                backup_type='t')
            mock_datetime.return_value = "20190101_000000"
            postgres.execute_backup()
            backups = os.listdir(postgres.backup_directory)
            assert len(backups) == 2
            assert "20190101_000000-postgres.tar" in backups
            assert "20190101_000000-test.tar" in backups

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_get_backups(self, mock_datetime, postgres_provider):
        mock_datetime.return_value = "20190101_000000"
        postgres_provider.execute_backup()
        backups = postgres_provider.get_backups()
        assert len(backups) == 2
        assert "20190101_000000-postgres.dump" in backups
        assert "20190101_000000-test.dump" in backups

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_get_backups_with_compression(self, mock_datetime):
        with tempfile.TemporaryDirectory() as temp_dir:
            postgres = Postgres(
                str(Path(temp_dir).resolve()),
                psql_bin_directory=config.PG_BIN_DIRECTORY,
                backup_type='t')
            mock_datetime.return_value = "20190101_000000"
            postgres.execute_backup()
            backups = postgres.get_backups()
            assert len(backups) == 2
            assert "20190101_000000-postgres.tar" in backups
            assert "20190101_000000-test.tar" in backups

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_restore(self, mock_datetime, postgres_provider,
                            drop_postgres_database):
        mock_datetime.return_value = "20190101_000000"
        postgres_provider.execute_backup()
        drop_postgres_database("test")
        users = get_users(postgres_provider, "test")
        assert len(users) == 0
        backup_file = Path(
            postgres_provider.backup_directory) / "20190101_000000-test.dump"
        postgres_provider.restore_backup(
            backup_file.resolve(), "test", create=True)
        users = get_users(postgres_provider, "test")
        assert len(users) == 1
        assert users[0][0] == "1"
        assert users[0][1] == "supertestuser"

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_restore_file_not_in_backup_directory(
            self, mock_datetime, postgres_provider):
        mock_datetime.return_value = "20190101_000000"
        postgres_provider.execute_backup()
        with tempfile.TemporaryDirectory() as tempdir:
            backup_file = Path(tempdir) / "20190101_000000-test.dump"
            open(backup_file, 'a').close()
            with raises(Exception) as e:
                postgres_provider.restore_backup(backup_file, "test")
            assert 'is not inside BACKUP_DIRECTORY' in str(e.value)

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_restore_relative_file(
            self, mock_datetime, postgres_provider, drop_postgres_database):
        mock_datetime.return_value = "20190101_000000"
        postgres_provider.execute_backup()
        drop_postgres_database("test")
        users = get_users(postgres_provider, "test")
        assert len(users) == 0
        backup_file = "20190101_000000-test.dump"
        postgres_provider.restore_backup(backup_file, "test", create=True)
        users = get_users(postgres_provider, "test")
        assert len(users) == 1
        assert users[0][0] == "1"
        assert users[0][1] == "supertestuser"

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_restore_unexisting_file(self, mock_datetime,
                                            postgres_provider):
        mock_datetime.return_value = "20190101_000000"
        postgres_provider.execute_backup()
        backup_file = "20190101_000000-test-fake.dump"
        with raises(Exception) as e:
            postgres_provider.restore_backup(backup_file, "test")
        assert "does not exist" in str(e.value)

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_restore_compressed_file(self, mock_datetime,
                                            drop_postgres_database):
        with tempfile.TemporaryDirectory() as temp_dir:
            postgres = Postgres(
                str(Path(temp_dir).resolve()),
                psql_bin_directory=config.PG_BIN_DIRECTORY,
                backup_type='t')
            mock_datetime.return_value = "20190101_000000"
            postgres.execute_backup()
            drop_postgres_database("test")
            users = get_users(postgres, "test")
            assert len(users) == 0
            backup_file = "20190101_000000-test.tar"
            postgres.restore_backup(backup_file, "test", create=True)
            users = get_users(postgres, "test")
            assert len(users) == 1
            assert users[0][0] == "1"
            assert users[0][1] == "supertestuser"

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_restore_other_database(
            self, mock_datetime, postgres_provider, drop_postgres_database):
        mock_datetime.return_value = "20190101_000000"
        drop_postgres_database("testnew")
        postgres_provider.execute_backup()
        backup_file = "20190101_000000-test.dump"
        postgres_provider.restore_backup(backup_file, "testnew", create=True)
        users = get_users(postgres_provider, "test")
        assert len(users) == 1
        assert users[0][0] == "1"
        assert users[0][1] == "supertestuser"
        users = get_users(postgres_provider, "testnew")
        assert len(users) == 1
        assert users[0][0] == "1"
        assert users[0][1] == "supertestuser"

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_restore_database_relation_already_exists(
            self, mock_datetime, postgres_provider, drop_postgres_database):
        mock_datetime.return_value = "20190101_000000"
        postgres_provider.execute_backup()
        backup_file = "20190101_000000-test.dump"
        with raises(Exception) as e:
            postgres_provider.restore_backup(backup_file, "test")
        assert "Could not restore database" in str(e.value)
        assert "relation \"users\" already exists" in str(e.value)

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_restore_create_database_already_exists(
            self, mock_datetime, postgres_provider, drop_postgres_database):
        mock_datetime.return_value = "20190101_000000"
        postgres_provider.execute_backup()
        backup_file = "20190101_000000-test.dump"
        with raises(Exception) as e:
            postgres_provider.restore_backup(backup_file, "test", create=True)
        assert "Could not create database" in str(e.value)
        assert "already exists" in str(e.value)

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_restore_other_database_unexisting(
            self, mock_datetime, postgres_provider, drop_postgres_database):
        mock_datetime.return_value = "20190101_000000"
        drop_postgres_database("testnew")
        postgres_provider.execute_backup()
        backup_file = "20190101_000000-test.dump"
        with raises(Exception) as e:
            postgres_provider.restore_backup(backup_file, "testnew")
        assert "does not exist" in str(e.value)
