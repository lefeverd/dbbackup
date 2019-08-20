# Backups DB

This image can be used to backup databases.  
It supports the following database engines:

- PostgreSQL
- MySQL

It is meant to be used in a cron, which can launch a container based on this image to backup
databases at regular intervals.  
You can create multiple crons based on your retention policy, for instance a daily, monthly and yearly cron,
each of which will use different values for `DAYS_TO_KEEP` and `BACKUP_SUFFIX`.

See `crontab.sample` for some examples.  
To edit the crontab, use `crontab -e`.

>**WARNING** Use it at your own risk. Please test thoroughly and frequently the dumps to be sure
you can restore the data when time comes.

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
- [Metrics](#metrics)
- [Tests](#tests)

<!-- /TOC -->

# Getting started

To get the help output from the CLI, simply run:

```bash
docker run lefeverd/docker-db-backup:0.1.0
```

## Common configuration

The following environment variables can be used:

- BACKUP_DIR: defines the directory in which the backups will be stored.
**Defaults to /backups. Be sure to persist it using a volume to avoid data loss.**
- DAYS_TO_KEEP: defines the number of days to keep old backups. Based on the modification time.
- BACKUP_SUFFIX: defines a suffix that is added at the end of the backup filename.
- PROMETHEUS_PUSHGATEWAY_URL: URL of the [Prometheus Pushgateway](https://github.com/prometheus/pushgateway) (see [Metrics](#metrics))

## PostgreSQL

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
    lefeverd/docker-db-backup:0.1.0 postgres backup <database>
```

#### Restore

To restore, you can mount the directory containing the backups and restore one of them.  
You can either list the existing ones and restore by using a filename, or provide an absolute
path to an existing dump.

To list the previous backups:

```bash
docker run \
    -e BACKUP_DIR=/backups/ \
    -e PGHOST=localhost \
    -e PGUSER=postgres \
    -e PGPASSWORD=postgres \
    -v <host-backup-directory>:/backups/ \
    lefeverd/docker-db-backup:0.1.0 postgres list
```


```bash
docker run \
    -e BACKUP_DIR=/backups/ \
    -e PGHOST=localhost \
    -e PGUSER=postgres \
    -e PGPASSWORD=postgres \
    -v <host-backup-directory>:/backups/ \
    lefeverd/docker-db-backup:0.1.0 postgres restore <file> <database>
```

You can chose to recreate the database with `--recreate`, or simply create with `--create`,
which will raise an exception if the database already exists.

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
    lefeverd/docker-db-backup:0.1.0 mysql backup <database>
```

#### Restore

To restore, you can mount the directory containing the backups, for instance:

```bash
docker run \
    -e BACKUP_DIR=/backups/ \
    -e MYSQL_HOST=localhost \
    -e MYSQL_USER=test \
    -e MYSQL_PASSWORD=test \
    -v <host-backup-directory>:/backups/ \
    lefeverd/docker-db-backup:0.1.0 mysql restore <file> <database>
```

# Metrics

Because this image should be used mainly in crons, exporting metrics to Prometheus directly is
not possible, as Prometheus works by scraping, and the cron is short lived
(executing the backup then stopping).

Fortunately, there's the [Prometheus Pushgateway](https://github.com/prometheus/pushgateway), which
allows to push metrics to it, and it will take care of exposing them to Prometheus.

This image supports it by setting the `PROMETHEUS_PUSHGATEWAY_URL` environment variable to the URL and port of the Pushgateway.

You should set the `honor_labels` to `true` in Prometheus' scrape configuration for the Pushgateway,
as described [here](https://github.com/prometheus/pushgateway#about-the-job-and-instance-labels).

The following metrics are pushed:

- database_backup_file_size

# Tests

You can run the tests with:

```bash
make test
make test-integration-mysql
make test-integration-postgres
```
