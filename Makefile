.PHONY: init test

all: init

init:
	python3 -m venv ./venv/
	./venv/bin/pip install -r requirements.txt

test:
	./venv/bin/pytest --cov=dbbackup --cov-report html tests/
