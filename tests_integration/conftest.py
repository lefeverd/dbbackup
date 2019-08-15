import subprocess

import pytest

from dbbackup import config
from dbbackup.providers.mysql import MySQL
from dbbackup.providers.postgres import Postgres


@pytest.fixture()
def mysql_provider():
    mysql = MySQL(
        user=config.MYSQL_USER,
        password=config.MYSQL_PASSWORD,
        host=config.MYSQL_HOST,
        mysql_bin_directory=config.MYSQL_BIN_DIRECTORY)
    return mysql


@pytest.fixture()
def postgres_provider():
    postgres = Postgres(psql_bin_directory=config.PG_BIN_DIRECTORY)
    return postgres


@pytest.fixture()
def test_database(mysql_provider, create_database, seed_database,
                  drop_database):
    """
    Fixture that provides a test database, with seed data, 
    and drop it afterwards.
    """
    if not config.MYSQL_BIN_DIRECTORY:
        raise Exception("No MYSQL_BIN_DIRECTORY defined.")
    if not config.MYSQL_HOST:
        raise Exception("No MYSQL_HOST defined.")
    create_database("test")
    seed_database("test")
    yield
    drop_database("test")
    drop_database("another")


@pytest.fixture()
def create_database(mysql_provider):
    def _create(database):
        command = mysql_provider._get_command()
        command += ['-e', f"create database if not exists {database};"]
        subprocess.check_call(command)

    return _create


@pytest.fixture()
def seed_database(mysql_provider):
    def _seed(database):
        command = mysql_provider._get_command()
        command += [
            '-D', database, '-e',
            "create table users (id numeric, name varchar(20)); insert into users (id, name) VALUES (1, 'supertestuser');"
        ]
        subprocess.check_call(command)

    return _seed


@pytest.fixture()
def drop_database(mysql_provider):
    def _drop(database):
        command = mysql_provider._get_command()
        command += ['-e', f"drop database if exists {database}"]
        subprocess.check_output(command)

    return _drop


@pytest.fixture()
def test_postgres_database(postgres_provider, create_postgres_database,
                           seed_postgres_database, drop_postgres_database):
    """
    Fixture that provides a test database, with seed data, 
    and drop it afterwards.
    """
    if not config.PG_BIN_DIRECTORY:
        raise Exception("No PG_BIN_DIRECTORY defined.")
    if not config.PGHOST:
        raise Exception("No PGHOST defined.")
    create_postgres_database("test")
    seed_postgres_database("test")
    yield
    drop_postgres_database("test")
    drop_postgres_database("another")


@pytest.fixture()
def create_postgres_database(postgres_provider, drop_postgres_database):
    def _create(database):
        command = postgres_provider._get_command()
        command += ['-c', f"create database {database};"]
        try:
            drop_postgres_database(database)
        except Exception as e:
            pass  # Do nothing
        subprocess.check_call(command)

    return _create


@pytest.fixture()
def seed_postgres_database(postgres_provider):
    def _seed(database):
        command = postgres_provider._get_command()
        command += [
            database, '-c',
            "create table users (id numeric, name varchar(20)); insert into users (id, name) VALUES (1, 'supertestuser');"
        ]
        subprocess.check_call(command)

    return _seed


@pytest.fixture()
def drop_postgres_database(postgres_provider):
    def _drop(database):
        command = postgres_provider._get_command()
        command += ['-c', f"drop database if exists {database}"]
        subprocess.check_output(command)

    return _drop
