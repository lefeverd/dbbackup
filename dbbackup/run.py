import logging
import os

from dbbackup import config
from dbbackup.cli import get_cli

_logger = logging.getLogger(__package__)


def configure_logging():
    logging.basicConfig(level=config.LOG_LEVEL.upper())
    _logger.debug("logging configured")


def create_backup_directory():
    _logger.debug("Creating backup directory")
    os.makedirs(config.BACKUP_DIRECTORY, exist_ok=True)


def main():
    configure_logging()
    create_backup_directory()
    cli = get_cli()
    cli()


if __name__ == "__main__":
    main()
