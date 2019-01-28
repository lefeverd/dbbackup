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
        - [Raw Docker](#raw-docker)
        - [Docker-compose](#docker-compose)
    - [MySQL](#mysql)
        - [Configuration](#configuration-1)
        - [Raw Docker](#raw-docker-1)
        - [Docker-compose](#docker-compose-1)
- [Tests](#tests)

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

### Raw Docker

```
docker build -t backup-db:0.1 .
```

```bash
docker run \
    -e DAYS_TO_KEEP=7 \
    -e BACKUP_SUFFIX=-daily \
    -e BACKUP_DIR=/backups/ \
    -e PGHOST=localhost \
    -e PGUSER=postgres \
    -e PGPASSWORD=postgres \
    backup-db:0.1
```

### Docker-compose

An example can be found in `docker-compose-postgres.sample.yaml`.  
It starts a `postgres` container and a `backup-postgres` container.

```bash
docker-compose -f docker-compose-postgres.sample.yml up -d
```

When running for the first time, the `backup-postgres` container should exit with an error,
because the `postgres` container initialization take some time.
You can already check the logs with:

```bash
docker-compose logs -f backup-postgres
```

After a few seconds, you can run `docker-compose -f docker-compose-postgres.sample.yml up -d` again, this time
the `backup` container should finish without errors.  
Check the logs again to verify that the dump was created.

## MySQL

See [./scripts/mysql_backup.sh](./scripts/mysql_backup.sh) for more information about
the postgres backups.

### Configuration

- MYSQL_HOST: defines the MySQL hostname
- MYSQL_USER: defines the MySQL user
- MYSQL_PASSWORD: defines the MySQL password
- MYSQL_DATABASE: defines the MySQL database

### Raw Docker

```
docker build -t backup-db:0.1 .
```

```bash
docker run \
    -e DAYS_TO_KEEP=7 \
    -e BACKUP_SUFFIX=-daily \
    -e BACKUP_DIR=/backups/ \
    -e PGHOST=localhost \
    -e PGUSER=postgres \
    -e PGPASSWORD=postgres \
    backup-db:0.1
```

### Docker-compose

An example can be found in `docker-compose-mysql.sample.yaml`.  
It starts a `mysql` container and a `backup-mysql` container.

```bash
docker-compose -f docker-compose-mysql.sample.yml up -d
```

When running for the first time, the `backup-mysql` container should exit with an error,
because the `mysql` container initialization take some time.
You can already check the logs with:

```bash
docker-compose logs -f backup-mysql
```

After a few seconds, you can run `docker-compose -f docker-compose-mysql.sample.yml up -d` again, this time
the `backup` container should finish without errors.  
Check the logs again to verify that the dump was created.

# Tests

Some basic tests can be run to ensure the backup container exits with a correct status code (0).

```bash
./integration-test-mysql.sh
./integration-test-postgres.sh
```

These tests can be improved to verify the content of the backups.
