FROM python:3-alpine

LABEL maintainer="David Lefever <lefever.d@gmail.com>"

WORKDIR /app

RUN apk update
RUN apk add --no-cache bash
RUN apk add --no-cache postgresql-client mysql-client curl

COPY ./dbbackup /app/dbbackup
COPY ./tests /app/tests
COPY ./tests_integration /app/tests_integration
COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

ENV BACKUP_DIRECTORY=/backups
ENV MYSQL_BIN_DIRECTORY=/usr/bin/
ENV PG_BIN_DIRECTORY=/usr/bin/

ENTRYPOINT ["python", "-m", "dbbackup"]
