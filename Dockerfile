FROM alpine

LABEL maintainer="David Lefever <lefever.d@gmail.com>"

RUN apk update
RUN apk add --no-cache bash
RUN apk add --no-cache postgresql-client mysql-client curl

COPY scripts/pg_backup.sh /usr/local/bin/pg_backup
COPY scripts/mysql_backup.sh /usr/local/bin/mysql_backup
COPY scripts/common.sh /common.sh
COPY scripts/entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/pg_backup
RUN chmod +x /usr/local/bin/mysql_backup
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["pg_backup"]
