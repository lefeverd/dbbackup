.PHONY: init test

all: init

init:
	python3 -m venv ./venv/
	./venv/bin/pip install -r requirements.txt

test:
	ENV_FILE=.env.test.mysql ./venv/bin/pytest --cov=dbbackup --cov-report html tests/

test-integration-mysql:
	docker-compose -f docker-compose-mysql.yaml up -d
	sleep 10
	ENV_FILE=.env.test.mysql ./venv/bin/pytest tests_integration/test_mysql.py
	docker-compose -f docker-compose-mysql.yaml stop && docker-compose -f docker-compose-mysql.yaml rm -f

test-integration-postgres:
	docker-compose -f docker-compose-postgres.yaml up -d
	sleep 10
	ENV_FILE=.env.test.postgres ./venv/bin/pytest tests_integration/test_postgres.py
	docker-compose -f docker-compose-postgres.yaml stop && docker-compose -f docker-compose-postgres.yaml rm -f

test-integration-prometheus:
	docker-compose -f docker-compose-prometheus.yaml up -d
	sleep 10
	ENV_FILE=.env.test.mysql ./venv/bin/pytest tests_integration/test_prometheus_pushgateway.py
	docker-compose -f docker-compose-prometheus.yaml stop && docker-compose -f docker-compose-prometheus.yaml rm -f
