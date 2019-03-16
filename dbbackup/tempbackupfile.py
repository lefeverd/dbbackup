import tempfile
import tarfile
from pathlib import Path
import shutil
import os
import logging
from io import RawIOBase, SEEK_SET

_logger = logging.getLogger(__name__)


class TemporaryBackupFile(RawIOBase):
    """
    Temporary file wrapper, that uses a temporary file until closing,
    then copies it to the final destination (and compress it if specified).
    Can be used as context manager (with statement).
    See https://docs.python.org/3/library/io.html#module-io
    """

    def __init__(self, filename, destination, compress=None, mode='w+b'):
        self.filename = filename
        self.destination = destination
        self.compress = compress
        self.mode = mode

        self._file = tempfile.NamedTemporaryFile(mode=self.mode, delete=False)
        _logger.debug(f"Created temporary file {self._file.name}")

    def __enter__(self):
        _logger.debug("Entering TemporaryBackupFile")
        return self._file

    def __exit__(self, *args):
        _logger.debug("Exiting TemporaryBackupFile")
        self.close()

    def _compress(self):
        _logger.debug("Compressing file")
        temp_tar = tempfile.NamedTemporaryFile(delete=False)
        _logger.debug(f"Temporary archive {temp_tar.name}")
        temp_tar_name = temp_tar.name
        with tarfile.open(fileobj=temp_tar, mode="w:gz") as tar:
            tar.add(self._file.name, arcname=self.filename)
        temp_tar.close()
        return temp_tar_name

    def close(self):
        to_delete = [self._file.name]
        self._file.close()
        to_copy = self._file.name
        destination = str(
            Path(self.destination + "/" + self.filename).resolve())
        if self.compress:
            to_copy = self._compress()
            # TODO: verify that when changing the reference, we have the 2 objs in the to_delete list
            to_delete.append(to_copy)
            destination += ".gz"
        _logger.debug(f"Copying {to_copy} to {destination}")
        shutil.copy(to_copy, destination)
        for filename in to_delete:
            os.unlink(filename)

    @property
    def closed(self):
        return self._file.closed

    @property
    def name(self):
        return self._file.name

    def fileno(self):
        return self._file.fileno()

    def flush(self):
        return self._file.flush()

    def isatty(self):
        return self._file.isatty()

    def readable(self):
        return self._file.readable()

    def readline(self, limit=-1):
        return self._file.readline(limit)

    def readlines(self, hint=-1):
        return self._file.readlines(hint)

    def write(self, b):
        return self._file.write(b)

    def read(self, n=-1):
        return self._file.read(n)

    def seek(self, offset, whence=None):
        return self._file.seek(offset, whence or SEEK_SET)

    def seekable(self):
        return self._file.seekable()

    def tell(self):
        return self._file.tell()

    def writable(self):
        return self._file.writable()

    def writelines(self, lines):
        return self._file.writelines(lines)

    def readinto(self, b):
        return self._file.readinto(b)
