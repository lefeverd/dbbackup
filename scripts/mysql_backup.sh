#!/bin/bash

set -e
set -o pipefail

source /common.sh

DAYS_TO_KEEP=${DAYS_TO_KEEP:-30}
BACKUP_DIR=${BACKUP_DIR:-}
BACKUP_SUFFIX=${BACKUP_SUFFIX:-}
MYSQL_HOST=${MYSQL_HOST:-localhost}
MYSQL_USER=${MYSQL_USER:-root}
MYSQL_PASSWORD=${MYSQL_PASSWORD:-root}

function help() {
	echo "$0"
	echo "	-h prints help"
	echo "	Environment variables:"
	echo "		DAYS_TO_KEEP: number of days after which old backup files will be deleted"
	echo "		BACKUP_SUFFIX: suffix of the backup file"
	echo "		BACKUP_DIR: output directory"
	echo "		MYSQL_HOST: mysql hostname"
	echo "		MYSQL_USER: mysql username"
	echo "		MYSQL_PASSWORD: mysql user password"
}

function pre_checks() {
	if [ -z "$BACKUP_DIR" ]; then
		log "BACKUP_DIR is required but not found. Exiting."
		exit 1
	fi
    mkdir -p "$BACKUP_DIR"
    endsWithSlash "$BACKUP_DIR" || BACKUP_DIR="${BACKUP_DIR}/"
}

function prune_old_backups() {
    log "Deleting old backups"
	find $BACKUP_DIR -maxdepth 1 -type f -mtime +$DAYS_TO_KEEP -name "*${BACKUP_SUFFIX}.sql.gz" -exec echo '{}' \; -exec rm -rf '{}' \;
    log "Deleting old backups done"
}

function perform_backups() {
    log "Starting backup of all databases"

    local suffix=$1
    suffix="`date +\%Y-\%m-\%d-\%H\%M\%S`$suffix"

	local databases # in two steps to catch eventual errors (otherwise return code is code of local assignment)
	databases=$(/usr/bin/mysql -h $MYSQL_HOST -u $MYSQL_USER -p$MYSQL_PASSWORD -e "SHOW DATABASES;" | grep -Ev "(Database|information_schema|performance_schema)")
	for database in $databases; do
		backup_filename="${BACKUP_DIR}${database}_${suffix}.sql.gz"
		log "Backup database ${database} to ${backup_filename}"
		if ! /usr/bin/mysqldump -h $MYSQL_HOST -u $MYSQL_USER -p$MYSQL_PASSWORD --databases $database | gzip > "${backup_filename}"; then
			log "Failed to backup database ${database}"
			exit 1
		fi
		log "mysqldump retcode $?"
		log "Backup done"
		log "database: $database - size: $(du ${backup_filename} | cut -f -1) - file: ${backup_filename}" # Use cut to only show bytes (no filename)
	done
    log "Backup of all databases done"
}

function main() {
	if [ "$1" = "-h" ]; then
		help
		exit 0
	fi
	pre_checks
	prune_old_backups
    perform_backups "$BACKUP_SUFFIX"
}

log "Starting MySQL backup"
main
