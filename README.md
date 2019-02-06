# Backups DB

This container can be used to backup databases.  
It supports the following database engines:

- PostgreSQL
- MySQL

It is meant to be used in a cron, which can launch a container based on this image to backup
databases on regular intervals.  
You can create multiple crons based on your retention policy, for instance a daily, monthly and yearly cron,
each of which will use different values for `DAYS_TO_KEEP` and `BACKUP_SUFFIX`.

See `crontab.sample` for some examples.  
To edit the crontab, use `crontab -e`.

<!-- TOC -->

- [Backups DB](#backups-db)
- [Getting started](#getting-started)
    - [Common configuration](#common-configuration)
    - [PostgreSQL](#postgresql)
        - [Configuration](#configuration)
        - [Examples](#examples)
            - [Backup](#backup)
            - [Restore](#restore)
    - [MySQL](#mysql)
        - [Configuration](#configuration-1)
        - [Examples](#examples-1)
            - [Backup](#backup-1)
            - [Restore](#restore-1)
- [Tests](#tests)
- [Notes](#notes)

<!-- /TOC -->

# Getting started

By default, the command executed when the container starts is `pg_backup`,
which will backup postgres databases.

## Common configuration

The following environment variables can be used:

- DAYS_TO_KEEP: defines the number of days to keep old backups. Based on the modification time.
- BACKUP_SUFFIX: defines a suffix that is added at the end of the backup filename.
- BACKUP_DIR: defines the directory in which the backups will be stored.

## PostgreSQL

See [./scripts/pg_backup.sh](./scripts/pg_backup.sh) for more information about
the postgres backups.

### Configuration

- PGHOST: defines the PostgreSQL host
- PGUSER: defines the PostgreSQL user
- PGPASSWORD: defines the PostgreSQL password
- PG_BACKUP_TYPE: either custom (default, .dump) or plain, to backup to plain sql files (compressed to .sql.gz).

The script also support the default PostgreSQL environment variables [listed here](https://www.postgresql.org/docs/9.3/static/libpq-envars.html).

### Examples

#### Backup

```bash
docker run \
    -e DAYS_TO_KEEP=7 \
    -e BACKUP_SUFFIX=-daily \
    -e BACKUP_DIR=/backups/ \
    -e PGHOST=localhost \
    -e PGUSER=postgres \
    -e PGPASSWORD=postgres \
    -v <host-backup-directory>:/backups/ \
    lefeverd/docker-db-backup:0.1.0
```

#### Restore

To restore, you can mount the directory containing the backups and executing `pg_restore`, for instance:

```bash
docker run \
    -e PGHOST=localhost \
    -e PGUSER=postgres \
    -e PGPASSWORD=postgres \
    -v <host-backup-directory>:/backups/ \
    lefeverd/docker-db-backup:0.1.0 bash -c \
    "
    pg_restore -Fc -d postgres -C \"/backups/<backup-file.dump>\"
    "
```

## MySQL

See [./scripts/mysql_backup.sh](./scripts/mysql_backup.sh) for more information about
the postgres backups.

### Configuration

- MYSQL_HOST: defines the MySQL hostname
- MYSQL_USER: defines the MySQL user
- MYSQL_PASSWORD: defines the MySQL password

### Examples

#### Backup

```bash
docker run \
    -e DAYS_TO_KEEP=7 \
    -e BACKUP_SUFFIX=-daily \
    -e BACKUP_DIR=/backups/ \
    -e MYSQL_HOST=database-host \
    -e MYSQL_USER=test \
    -e MYSQL_PASSWORD=test \
    -v <host-backup-directory>:/backups/ \
    lefeverd/docker-db-backup:0.1.0 mysql_backup
```

#### Restore

To restore, you can mount the directory containing the backups, for instance:

```bash
docker run \
    -e MYSQL_HOST=localhost \
    -e MYSQL_USER=test \
    -e MYSQL_PASSWORD=test \
    -v <host-backup-directory>:/backups/ \
    lefeverd/docker-db-backup:0.1.0 bash -c \
    "
    gunzip < \"/backups/<backup-file.sql.gz>\" | mysql -p -h database-host -u test -ptest test
    "
```

# Tests

Some basic tests can be run to ensure that the backups are correctly executed and can be restored.

```bash
./tests/integration-test-mysql.sh
./tests/integration-test-postgres.sh
```

# Notes

Currently, the script will backup all databases (in separate files).
