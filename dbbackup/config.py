import os
from pathlib import Path
from dotenv import load_dotenv

ENV_FILE = os.environ.get("ENV_FILE", None)
env_path = Path('.') / (ENV_FILE or '.env')

load_dotenv(dotenv_path=env_path, verbose=True)


def get_bool(value):
    return value == "1" or value == "t" or value == "true" or value == "True"


try:
    BACKUP_DIRECTORY = str(Path(os.environ["BACKUP_DIRECTORY"]).resolve())
except KeyError as e:
    raise Exception(f"Required environment variable {e} is not set.")

# General
DAYS_TO_KEEP = os.environ.get("DAYS_TO_KEEP", 7)
BACKUP_SUFFIX = os.environ.get("BACKUP_SUFFIX", False)
PROVIDER = os.environ.get("PROVIDER", False)
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Prometheus Pushgateway - metrics
PROMETHEUS_PUSHGATEWAY_URL = os.environ.get("PROMETHEUS_PUSHGATEWAY_URL",
                                            False)

# Provider - Postgres
PGHOST = os.environ.get("PGHOST", False)
PGUSER = os.environ.get("PGUSER", False)
PGPASSWORD = os.environ.get("PGPASSWORD", False)
PG_BACKUP_TYPE = os.environ.get("PG_BACKUP_TYPE", False)

# Provider - MySQL
MYSQL_HOST = os.environ.get("MYSQL_HOST", False)
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", False)
MYSQL_BIN_DIRECTORY = os.environ.get("MYSQL_BIN_DIRECTORY", "/usr/local/bin/")
MYSQL_COMPRESS = get_bool(os.environ.get("MYSQL_COMPRESS", False))
