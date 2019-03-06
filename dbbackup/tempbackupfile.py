import tempfile
import tarfile
from pathlib import Path
import shutil
import os
import logging

_logger = logging.getLogger(__name__)


class TemporaryBackupFile:
    """
    Create and return a temporary file that can be copied to the specified
    destination when closed (and compressed if specified).
    Can be used as context manager (with statement).
    """

    def __init__(self, filename, destination, compress=None):
        self.filename = filename
        self.destination = destination
        self.compress = compress
        self.file_objs = []

    def __enter__(self):
        _logger.debug("Entering TemporaryBackupFile")
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        _logger.debug(f"Created temporary file {self.temp_file.name}")
        self.file_objs.append(self.temp_file)
        return self.temp_file

    def __exit__(self, *args):
        _logger.debug("Exiting TemporaryBackupFile")
        self.close()

    def compress_file(self):
        _logger.debug("Compressing file")
        temp_tar = tempfile.NamedTemporaryFile(delete=False)
        _logger.debug(f"Temporary archive {temp_tar.name}")
        self.file_objs.append(temp_tar)
        temp_tar_name = temp_tar.name
        with tarfile.open(fileobj=temp_tar, mode="w:gz") as tar:
            tar.add(self.temp_file.name, arcname=self.filename)
        temp_tar.close()
        return temp_tar_name

    def close(self):
        self.temp_file.close()
        to_copy = self.temp_file.name
        destination = str(
            Path(self.destination + "/" + self.filename).resolve())
        if self.compress:
            to_copy = self.compress_file()
            destination += ".gz"
        _logger.debug(f"Copying {to_copy} to {destination}")
        shutil.copy(to_copy, destination)
        for file_obj in self.file_objs:
            os.unlink(file_obj.name)
