import logging
from dbbackup.providers import AbstractProvider

_logger = logging.getLogger(__name__)


class MySQL(AbstractProvider):
    def execute_backup(self):
        print("Executing MySQL backup")

    def list_backups(self):
        print("Listing backups")
