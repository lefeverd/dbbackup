import socket
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway


class PrometheusPushGatewayCallback:
    def __init__(self, address):
        self.address = address

    def backup_done(self, date_iso, database, filename, size):
        registry = CollectorRegistry()
        g = Gauge(
            'dbbackup_last_success_timestamp',
            'Last time a batch job successfully finished',
            registry=registry)
        g.set_to_current_time()
        g2 = Gauge(
            'dbbackup_last_backup_file_size',
            'Last backup file size',
            registry=registry)
        g2.set(size)
        push_to_gateway(
            self.address,
            job=f'{self.get_hostname()}-{database}',
            registry=registry)

    def get_hostname(self):
        return socket.gethostname()
