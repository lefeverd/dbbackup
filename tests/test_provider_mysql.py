import unittest
import os
from unittest import mock
from pathlib import Path
import time
from datetime import datetime, timedelta
from dbbackup.providers import mysql
from tempfile import TemporaryDirectory, _TemporaryFileWrapper


class TestMysqlProvider(unittest.TestCase):
    def test_default_command_args_default_values(self):
        provider = mysql.MySQL()
        args = provider._get_default_command_args()
        assert args[0] == '-h'
        assert args[1] == mysql.DEFAULT_MYSQL_HOST
        assert args[2] == '-u'
        assert args[3] == mysql.DEFAULT_MYSQL_USER

    def test_default_command_args_values(self):
        provider = mysql.MySQL(host='myhost', user='myuser')
        args = provider._get_default_command_args()
        assert args[0] == '-h'
        assert args[1] == 'myhost'
        assert args[2] == '-u'
        assert args[3] == 'myuser'

    def test_default_command_args_with_password(self):
        provider = mysql.MySQL(
            host='myhost', user='myuser', password='mypassword')
        args = provider._get_default_command_args()
        assert args[0] == '-h'
        assert args[1] == 'myhost'
        assert args[2] == '-u'
        assert args[3] == 'myuser'
        assert args[4] == '-pmypassword'

    @mock.patch(
        'dbbackup.providers.mysql.MySQL.backup_database', autospec=True)
    @mock.patch('dbbackup.providers.mysql.MySQL.get_databases', autospec=True)
    def test_execute_backup(self, mock_get_databases, mock_backup_database):
        mock_backup_database.return_value = True
        mock_get_databases.return_value = ['test_database', 'test_database2']
        provider = mysql.MySQL()
        provider.execute_backup()
        mock_backup_database.assert_has_calls([
            mock.call(provider, 'test_database'),  # Method is called with self
            mock.call(provider, 'test_database2')
        ])

    @mock.patch('dbbackup.providers.mysql.TemporaryBackupFile.close')
    @mock.patch('dbbackup.providers.mysql.subprocess.run')
    @mock.patch('dbbackup.providers.mysql.MySQL._get_backup_command')
    def test_temporary_file_wrapper(self, _get_backup_command, mock_run,
                                    mock_close):
        _get_backup_command.return_value = "cmd"
        mock_close.return_value = True
        provider = mysql.MySQL()
        provider.backup_database('test_database')
        assert mock_run.call_args[0][0] == 'cmd'
        assert isinstance(mock_run.call_args[1]['stdout'],
                          _TemporaryFileWrapper)

    @mock.patch('dbbackup.providers.mysql.MySQL._is_older_than')
    @mock.patch('dbbackup.providers.mysql.MySQL._remove')
    @mock.patch('dbbackup.providers.mysql.MySQL.get_backups')
    def test_cleanup_called(self, mock_get_backups, mock_remove,
                            mock_is_older_than):
        mock_get_backups.return_value = ["backup_one"]
        mock_is_older_than.return_value = True
        mock_remove.return_value = True
        provider = mysql.MySQL()
        provider.cleanup(0)
        assert mock_remove.called

    def test_cleanup_zero_days(self):
        with TemporaryDirectory() as tmpdir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            str(Path(tmpdir).resolve())):
                file_absolute = Path(tmpdir + "/" +
                                     "20190101_000000-test-daily.sql")
                f = open(file_absolute, 'w+b')
                f.write(b"backup content")
                f.close()

                provider = mysql.MySQL()
                provider.cleanup(0)
                assert not Path(f.name).exists()

    def test_cleanup_one_day(self):
        with TemporaryDirectory() as tmpdir:
            with mock.patch('dbbackup.providers.mysql.config.BACKUP_DIRECTORY',
                            str(Path(tmpdir).resolve())):

                # First file has mtime = now
                file_absolute = Path(tmpdir + "/" +
                                     "20190102_000000-test-daily.sql")
                f1 = open(file_absolute, 'w+b')
                f1.write(b"backup content")
                f1.close()

                # Second file, we modify mtime to be yesterday
                file_absolute = Path(tmpdir + "/" +
                                     "20190101_000000-test-daily.sql")
                f2 = open(file_absolute, 'w+b')
                f2.write(b"backup content")
                f2.close()

                yesterday = datetime.now() - timedelta(days=1)
                modTime = time.mktime(yesterday.timetuple())

                os.utime(f2.name, (modTime, modTime))

                provider = mysql.MySQL()

                # Cleanup files older than 1 day
                provider.cleanup(1)

                assert Path(f1.name).exists()
                assert not Path(f2.name).exists()
