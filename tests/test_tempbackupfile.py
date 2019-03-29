import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from dbbackup import tempbackupfile


class TestTempbackupfile(unittest.TestCase):
    def test_copy_to_destination(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            tempfile.write(b"This is my file")
            tempfile.close()
            final_file = Path(tmpdir) / "tmpname"
            assert final_file.exists()

    def test_compress(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile(
                "tmpname", tmpdir, compress=True)
            tempfile.write(b"This is my file")
            tempfile.close()
            final_file = Path(tmpdir) / "tmpname.gz"
            assert final_file.exists()

    def test_context_manager(self):
        with TemporaryDirectory() as tmpdir:
            with tempbackupfile.TemporaryBackupFile("tmpname",
                                                    tmpdir) as tempfile:
                tempfile.write(b'Hello\n my friend')
            final_file = Path(tmpdir) / "tmpname"
            assert final_file.exists()

    def test_read_without_seek(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            tempfile.write(b"This is my file")
            buf = tempfile.read(1)
            assert buf == b''

    def test_read_size_with_seek(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            tempfile.write(b"This is my file")
            tempfile.seek(0)
            buf = tempfile.read(1)
            assert buf == b'T'

    def test_fileno(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            assert isinstance(tempfile.fileno(), int)

    def test_isatty(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            assert tempfile.isatty() is False

    def test_readable(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            assert tempfile.readable() is True

    def test_readline(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            tempfile.write(b"Hello\n")
            tempfile.write(b"my friend")
            tempfile.seek(0)
            assert tempfile.readline() == b'Hello\n'
            assert tempfile.readline() == b'my friend'
            assert tempfile.readline() == b''

    def test_readline_limit_one(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            tempfile.write(b"Hello\n")
            tempfile.write(b"my friend")
            tempfile.seek(0)
            assert tempfile.readline(1) == b'H'
            assert tempfile.readline(1) == b'e'
            assert tempfile.readline(1) == b'l'
            assert tempfile.readline(1) == b'l'
            assert tempfile.readline(1) == b'o'
            assert tempfile.readline(1) == b'\n'
            assert tempfile.readline(1) == b'm'
            assert tempfile.readline(1) == b'y'
            assert tempfile.readline(1) == b' '
            assert tempfile.readline(1) == b'f'
            assert tempfile.readline(1) == b'r'
            assert tempfile.readline(1) == b'i'
            assert tempfile.readline(1) == b'e'
            assert tempfile.readline(1) == b'n'
            assert tempfile.readline(1) == b'd'
            assert tempfile.readline(1) == b''

    def test_readline_limit(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            tempfile.write(b"Hello\n")
            tempfile.write(b"my friend")
            tempfile.seek(0)
            assert tempfile.readline(100) == b'Hello\n'
            assert tempfile.readline(100) == b'my friend'
            assert tempfile.readline(100) == b''

    def test_readlines(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            tempfile.write(b"Hello\n")
            tempfile.write(b"my friend")
            tempfile.seek(0)
            assert tempfile.readlines() == [b'Hello\n', b'my friend']

    def test_readlines_hint_one(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            tempfile.write(b"Hello\n")
            tempfile.write(b"my friend")
            tempfile.seek(0)
            assert tempfile.readlines(1) == [b'Hello\n']

    def test_readlines_hint(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            tempfile.write(b"Hello\n")
            tempfile.write(b"my friend")
            tempfile.seek(0)
            assert tempfile.readlines(10) == [b'Hello\n', b'my friend']

    def test_seekable(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            assert tempfile.seekable() is True

    def test_tell(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            assert tempfile.tell() == 0
            tempfile.write(b'H')
            assert tempfile.tell() == 1
            tempfile.write(b'ello')
            assert tempfile.tell() == 5
            tempfile.seek(0)
            assert tempfile.tell() == 0

    def test_writable(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            assert tempfile.writable() is True

    def test_writelines(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            tempfile.writelines([b'Hello\n', b'my friend'])
            tempfile.seek(0)
            assert tempfile.read() == b'Hello\nmy friend'

    def test_readinto(self):
        with TemporaryDirectory() as tmpdir:
            tempfile = tempbackupfile.TemporaryBackupFile("tmpname", tmpdir)
            tempfile.write(b'Hello\n')
            tempfile.write(b'my friend')
            tempfile.seek(0)
            b = bytearray(10)
            bytes_read = tempfile.readinto(b)
            assert bytes_read == 10
