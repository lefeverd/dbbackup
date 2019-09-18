import unittest
import os
from unittest import mock
from pathlib import Path
import time
from datetime import datetime, timedelta
from dbbackup.providers import postgres
from tempfile import TemporaryDirectory, _TemporaryFileWrapper


def Any(cls):
    class Any(cls):
        def __eq__(self, other):
            return True

    return Any()


class TestPostgresProvider(unittest.TestCase):
    @mock.patch(
        'dbbackup.providers.postgres.Postgres.backup_database', autospec=True)
    @mock.patch(
        'dbbackup.providers.postgres.Postgres.get_databases', autospec=True)
    @mock.patch('dbbackup.providers.postgres.get_file_size', autospec=True)
    def test_execute_backup(self, mock_get_file_size, mock_get_databases,
                            mock_backup_database):
        mock_get_file_size.return_value = "1024"
        mock_backup_database.return_value = '20190101_000000-test-daily.dump'
        mock_get_databases.return_value = ['test_database', 'test_database2']
        provider = postgres.Postgres('/tmp')
        provider.execute_backup()
        mock_backup_database.assert_has_calls([
            mock.call(provider, 'test_database'),  # Method is called with self
            mock.call(provider, 'test_database2')
        ])

    @mock.patch(
        'dbbackup.providers.postgres.Postgres.backup_database', autospec=True)
    @mock.patch(
        'dbbackup.providers.postgres.Postgres.get_databases', autospec=True)
    @mock.patch('dbbackup.providers.postgres.get_file_size', autospec=True)
    def test_execute_backup_callback(self, mock_get_file_size,
                                     mock_get_databases, mock_backup_database):
        mock_get_file_size.return_value = "1024"
        mock_backup_database.return_value = '20190101_000000-test-daily.dump'
        mock_get_databases.return_value = ['test']
        provider = postgres.Postgres('/tmp')

        callback = mock.Mock()

        provider.register_callback(callback)
        provider.execute_backup()
        callback.backup_done.assert_called_with(
            Any(str), 'test', '20190101_000000-test-daily.dump', '1024')

    @mock.patch('dbbackup.providers.postgres.TemporaryBackupFile.close')
    @mock.patch('dbbackup.providers.postgres.subprocess.run')
    @mock.patch('dbbackup.providers.postgres.Postgres._get_backup_command')
    def test_temporary_file_wrapper(self, _get_backup_command, mock_run,
                                    mock_close):
        _get_backup_command.return_value = "cmd"
        mock_close.return_value = True
        provider = postgres.Postgres('/tmp')
        provider.backup_database('test_database')
        assert mock_run.call_args[0][0] == 'cmd'
        assert isinstance(mock_run.call_args[1]['stdout'],
                          _TemporaryFileWrapper)

    @mock.patch('dbbackup.providers.postgres.Postgres._is_older_than')
    @mock.patch('dbbackup.providers.postgres.Postgres._remove')
    @mock.patch('dbbackup.providers.postgres.Postgres.get_backups')
    def test_cleanup_called(self, mock_get_backups, mock_remove,
                            mock_is_older_than):
        mock_get_backups.return_value = ["backup_one"]
        mock_is_older_than.return_value = True
        mock_remove.return_value = True
        provider = postgres.Postgres('/tmp')
        provider.cleanup(0)
        assert mock_remove.called

    def test_cleanup_zero_days(self):
        with TemporaryDirectory() as tmpdir:
            file_absolute = Path(tmpdir + "/" +
                                 "20190101_000000-test-daily.dump")
            f = open(file_absolute, 'w+b')
            f.write(b"backup content")
            f.close()

            provider = postgres.Postgres(str(Path(tmpdir).resolve()))
            provider.cleanup(0)
            assert not Path(f.name).exists()

    def test_cleanup_one_day(self):
        with TemporaryDirectory() as tmpdir:
            # First file has mtime = now
            file_absolute = Path(tmpdir + "/" +
                                 "20190102_000000-test-daily.dump")
            f1 = open(file_absolute, 'w+b')
            f1.write(b"backup content")
            f1.close()

            # Second file, we modify mtime to be yesterday
            file_absolute = Path(tmpdir + "/" +
                                 "20190101_000000-test-daily.dump")
            f2 = open(file_absolute, 'w+b')
            f2.write(b"backup content")
            f2.close()

            yesterday = datetime.now() - timedelta(days=1)
            modTime = time.mktime(yesterday.timetuple())

            os.utime(f2.name, (modTime, modTime))

            provider = postgres.Postgres(str(Path(tmpdir).resolve()))

            # Cleanup files older than 1 day
            provider.cleanup(1)

            assert Path(f1.name).exists()
            assert not Path(f2.name).exists()

    @mock.patch(
        'dbbackup.providers.postgres.Postgres._get_formatted_current_datetime')
    def test_backup_filename(self, mock_datetime):
        mock_datetime.return_value = "20190101_000000"
        provider = postgres.Postgres('/tmp', backup_suffix="-daily")
        backup_filename = provider.construct_backup_filename("test")
        assert backup_filename == "20190101_000000-test-daily.dump"
