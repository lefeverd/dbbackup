from dbbackup import config
from dbbackup.providers.mysql import MySQL


class MySQLConfigBuilder:
    """
    Builds a mysql provider instance from the app config values
    """
    provider_for = "mysql"

    def __init__(self):
        self._instance = None

    def __call__(self):
        exclude_databases = config.EXCLUDE_DATABASES \
            and config.EXCLUDE_DATABASES.split(",") \
            or False
        kwargs = {
            "mysql_bin_directory": config.MYSQL_BIN_DIRECTORY,
            "compress": config.MYSQL_COMPRESS
        }
        if config.MYSQL_HOST:
            kwargs["host"] = config.MYSQL_HOST
        if config.MYSQL_USER:
            kwargs["user"] = config.MYSQL_USER
        if config.MYSQL_PASSWORD:
            kwargs["password"] = config.MYSQL_PASSWORD
        if exclude_databases:
            kwargs["exclude_databases"] = exclude_databases
        instance = MySQL(**kwargs)
        self._instance = instance
        return instance
