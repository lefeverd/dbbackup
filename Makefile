.PHONY: init test

all: init

init:
	python3 -m venv ./venv/
	./venv/bin/pip install -r requirements.txt

test:
	ENV_FILE=.env.test.mysql ./venv/bin/pytest --cov=dbbackup --cov-report html tests/

test-integration-mysql:
	ENV_FILE=.env.test.mysql ./venv/bin/pytest tests_integration/test_mysql.py

test-integration-postgres:
	ENV_FILE=.env.test.postgres ./venv/bin/pytest tests_integration/test_postgres.py
