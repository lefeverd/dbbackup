import os
from dotenv import load_dotenv

load_dotenv(verbose=True)

# General
DAYS_TO_KEEP = os.environ.get("DAYS_TO_KEEP", 7)
BACKUP_SUFFIX = os.environ.get("BACKUP_SUFFIX", False)
PROVIDER = os.environ.get("PROVIDER", False)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Prometheus Pushgateway - metrics
PROMETHEUS_PUSHGATEWAY_URL = os.environ.get("PROMETHEUS_PUSHGATEWAY_URL",
                                            False)

# Storage
BACKUP_DIRECTORY = os.environ.get("BACKUP_DIRECTORY", False)

# Provider - Postgres
PGHOST = os.environ.get("PGHOST", False)
PGUSER = os.environ.get("PGUSER", False)
PGPASSWORD = os.environ.get("PGPASSWORD", False)
PG_BACKUP_TYPE = os.environ.get("PG_BACKUP_TYPE", False)

# Provider - MySQL
MYSQL_HOST = os.environ.get("MYSQL_HOST", False)
MYSQL_USER = os.environ.get("MYSQL_USER", False)
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", False)
MYSQL_BIN_DIRECTORY = os.environ.get("MYSQL_BIN", "/usr/local/bin/")
