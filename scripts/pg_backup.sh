#!/bin/bash

# Inspired from
# https://wiki.postgresql.org/wiki/Automated_Backup_on_Linux
# This script is the pg_backup_rotated.sh.
# Modified to not create a directory per day, and keep specified number of backups.

set -e
set -o pipefail

source /common.sh

PG_BACKUP_TYPE=${PG_BACKUP_TYPE:-custom}
DAYS_TO_KEEP=${DAYS_TO_KEEP:-7}
BACKUP_SUFFIX=${BACKUP_SUFFIX:-}
BACKUP_DIR=${BACKUP_DIR:-}

function help() {
	echo "$0"
	echo "	-h prints help"
	echo "	Environment variables:"
	echo "		DAYS_TO_KEEP: number of days after which old backup files will be deleted"
	echo "		BACKUP_SUFFIX: suffix of the backup file"
	echo "		BACKUP_DIR: output directory"
	echo "		PG_BACKUP_TYPE: either plain (.tar.gz sql) or custom (.dump)"
    echo "  Default PostgreSQL environment variables can be used, see"
    echo "  https://www.postgresql.org/docs/9.3/static/libpq-envars.html"
}

function pre_checks() {
    if [ "$BACKUP_USER" != "" -a "$(id -un)" != "$BACKUP_USER" ]; then
        log "This script must be run as $BACKUP_USER. Exiting." 
        exit 1
    fi
	if [ -z "$BACKUP_DIR" ]; then
		log "BACKUP_DIR is required but not found. Exiting."
		exit 1
	fi
    mkdir -p "$BACKUP_DIR"
	if [ "$PG_BACKUP_TYPE" != "plain" -a "$PG_BACKUP_TYPE" != "custom" ]; then
		log "PG_BACKUP_TYPE supports only plain or custom. Exiting."
		exit 1
	fi
    endsWithSlash "$BACKUP_DIR" || BACKUP_DIR="${BACKUP_DIR}/"
}

function perform_backups() {
    log "Starting backup of all databases"

    local suffix=$1
    suffix="`date +\%Y-\%m-\%d-\%H%M`$SUFFIX"
    
    BACKUP_FILTER_CLAUSE=""
    if [ -n "$BACKUP_ONLY_FILTER" ] && [ "$BACKUP_ONLY_FILTER" != "false" ]; then
        BACKUP_FILTER_CLAUSE=" and datname ~ '$BACKUP_ONLY_FILTER'"
    fi
    
    FULL_BACKUP_QUERY="select datname from pg_database where not datistemplate and datallowconn $BACKUP_FILTER_CLAUSE order by datname;"
    
    local databases # in two steps to catch eventual errors (otherwise return code is code of local assignment)
    databases=$(psql -At -c "$FULL_BACKUP_QUERY" postgres)
    for database in $databases; do
        backup_filename="${BACKUP_DIR}${database}_${suffix}"
        if [ "$PG_BACKUP_TYPE" = "plain" ]; then
            log "Plain backup of ${database} to ${backup_filename}.sql.gz"
            
            if ! pg_dump -Fp "$database" | gzip > "${backup_filename}.sql.gz.in_progress"; then
                log "Failed to produce plain backup of ${database}"
                exit 1
            else
                mv "${backup_filename}.sql.gz.in_progress" "${backup_filename}.sql.gz"
                log "database: $database - size: $(du ${backup_filename} | cut -f -1) - file: ${backup_filename}" # Use cut to only show bytes (no filename)
            fi
        fi
        
        if [ "$PG_BACKUP_TYPE" = "custom" ]; then
            log "Custom backup of ${database} to ${backup_filename}.dump"

            if ! pg_dump -Fc "$database" -f "${backup_filename}.dump.in_progress"; then
                log "Failed to produce custom backup of ${database}"
                exit 1
            else
                mv "${backup_filename}.dump.in_progress" "${backup_filename}.dump"
                log "database $database - size: $(du ${backup_filename}.dump  | cut -f -1) - file: ${backup_filename}.dump" # Use cut to only show bytes (no filename)
            fi
        fi
        
    done
    
    log "All database backups completed"
}

function prune_old_backups() {
    log "Deleting old backups"
	if [ -z "$BACKUP_SUFFIX" ]; then
		find $BACKUP_DIR -maxdepth 1 -type f -mtime +$DAYS_TO_KEEP -name "*-${BACKUP_SUFFIX}.*" -exec rm -rf '{}' ';'
	else
		find $BACKUP_DIR -maxdepth 1 -type f -mtime +$DAYS_TO_KEEP -exec rm -rf '{}' ';'
	fi
    log "Deleting old backups done"
}

function main(){
	if [ "$1" = "-h" ]; then
		help
		exit 0
	fi
	pre_checks
	prune_old_backups
    perform_backups "$BACKUP_SUFFIX"
}

main "$@"