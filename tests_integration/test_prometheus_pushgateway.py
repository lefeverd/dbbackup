from unittest import mock
from datetime import datetime
import requests
from dbbackup import config
from dbbackup.callbacks.prometheus import PrometheusPushGatewayCallback


class TestPrometheusPushgateway:
    @mock.patch(
        'dbbackup.callbacks.prometheus.PrometheusPushGatewayCallback.get_hostname'
    )
    def test_backup_done(self, mock_get_hostname):
        mock_get_hostname.return_value = "myhostname"
        pushgateway = PrometheusPushGatewayCallback(
            config.PROMETHEUS_PUSHGATEWAY_URL)
        pushgateway.backup_done(datetime.now().isoformat(), "test", "test.sql",
                                "1024")
        response = requests.get(f"{config.PROMETHEUS_PUSHGATEWAY_URL}/metrics")
        assert response.status_code == 200
        metrics = response.text
        assert 'dbbackup_last_backup_file_size{instance="",job="myhostname-test"} 1024' in metrics
        assert 'dbbackup_last_success_timestamp{instance="",job="myhostname-test"}' in metrics

    @mock.patch(
        'dbbackup.callbacks.prometheus.PrometheusPushGatewayCallback.get_hostname'
    )
    def test_backup_done_metric_replaced(self, mock_get_hostname):
        """
        Ensure that the metrics pushed to the gateway are replacing old values
        for the same grouping key (which is represented by the job, 
        which is a concatenation of the hostname and the database).
        """
        mock_get_hostname.return_value = "myhostname"
        pushgateway = PrometheusPushGatewayCallback(
            config.PROMETHEUS_PUSHGATEWAY_URL)
        pushgateway.backup_done(datetime.now().isoformat(), "test", "test.sql",
                                "1024")
        pushgateway.backup_done(datetime.now().isoformat(), "test", "test.sql",
                                "2048")
        response = requests.get(f"{config.PROMETHEUS_PUSHGATEWAY_URL}/metrics")
        assert response.status_code == 200
        metrics = response.text
        assert 'dbbackup_last_backup_file_size{instance="",job="myhostname-test"} 2048' in metrics
        assert 'dbbackup_last_backup_file_size{instance="",job="myhostname-test"} 1024' not in metrics
