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
        instance = MySQL(
            config.MYSQL_HOST,
            config.MYSQL_USER,
            config.MYSQL_PASSWORD,
            mysql_bin_directory=config.MYSQL_BIN_DIRECTORY,
            compress=config.MYSQL_COMPRESS)
        self._instance = instance
        return instance
