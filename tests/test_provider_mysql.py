from unittest import mock
from dbbackup.providers import mysql
from tempfile import _TemporaryFileWrapper


class TestMysqlProvider:
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

    @mock.patch('dbbackup.providers.mysql.subprocess.check_call')
    @mock.patch('dbbackup.providers.mysql.MySQL._get_backup_command')
    def test_backup_database(self, _get_backup_command, mock_check_call):
        _get_backup_command.return_value = "cmd"
        provider = mysql.MySQL()
        provider.backup_database('test_database')
        assert mock_check_call.call_args[0][0] == 'cmd'
        assert isinstance(mock_check_call.call_args[1]['stdout'],
                          _TemporaryFileWrapper)