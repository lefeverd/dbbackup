import os
import unittest
import subprocess
from unittest import mock
from pathlib import Path
import tempfile

from dbbackup import config
from dbbackup.providers.mysql import MySQL

_mysql = MySQL(
    user=config.MYSQL_USER,
    password=config.MYSQL_PASSWORD,
    host=config.MYSQL_HOST,
    mysql_bin_directory=config.MYSQL_BIN_DIRECTORY)


def create_database(database):
    command = _mysql._get_command()
    command += ['-e', f"create database if not exists {database};"]
    subprocess.check_call(command)


def seed_database(database):
    command = _mysql._get_command()
    command += [
        '-D', database, '-e',
        "create table users (id numeric, name varchar(20)); insert into users (id, name) VALUES (1, 'supertestuser');"
    ]
    subprocess.check_call(command)


class TestMysql(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not config.MYSQL_BIN_DIRECTORY:
            cls.fail("No MYSQL_BIN_DIRECTORY defined.")
        if not config.MYSQL_HOST:
            cls.fail("No MYSQL_HOST defined.")

        cls.tearDownClass()
        create_database("test")
        seed_database("test")

    @classmethod
    def tearDownClass(cls):
        cleanup_command = _mysql._get_command()
        cleanup_command += ['-e', "drop database if exists test;"]
        cleanup_command += ['-e', "drop database if exists another;"]
        subprocess.check_call(cleanup_command)

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_correctly_done(self, mock_datetime):
        mock_datetime.return_value = "20190101"
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            temp_dir):
                _mysql.execute_backup()
                backups = os.listdir(temp_dir)
                assert len(backups) == 3
                assert "20190101-sys-daily.sql" in backups
                assert "20190101-mysql-daily.sql" in backups
                assert "20190101-test-daily.sql" in backups

    @mock.patch(
        'dbbackup.providers.mysql.MySQL._get_formatted_current_datetime')
    def test_backup_multiple_databases_correctly_done(self, mock_datetime):
        mock_datetime.return_value = "20190101"
        create_database("another")
        seed_database("another")
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            temp_dir):
                _mysql.execute_backup()
                backups = os.listdir(temp_dir)
                assert len(backups) == 4
                assert "20190101-sys-daily.sql" in backups
                assert "20190101-mysql-daily.sql" in backups
                assert "20190101-test-daily.sql" in backups
                assert "20190101-another-daily.sql" in backups
