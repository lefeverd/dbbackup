from dbbackup import config
from dbbackup.providers.postgres import Postgres


class PostgresConfigBuilder:
    """
    Builds a postgres provider instance from the app config values
    """
    provider_for = "postgres"

    def __init__(self):
        self._instance = None

    def __call__(self):
        exclude_databases = config.EXCLUDE_DATABASES \
            and config.EXCLUDE_DATABASES.split(",") \
            or False
        kwargs = {"psql_bin_directory": config.PG_BIN_DIRECTORY}
        if config.PG_BACKUP_TYPE:
            kwargs["backup_type"] = config.PG_BACKUP_TYPE
        if exclude_databases:
            kwargs["exclude_databases"] = exclude_databases
        instance = Postgres(**kwargs)
        self._instance = instance
        return instance
