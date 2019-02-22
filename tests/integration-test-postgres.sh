#!/bin/bash

DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd)"
source "${DIR}/common.sh"

IMAGE_TAG="test"
BACKUP_DIRECTORY="/tmp/postgres-backups-test/"
DOCKER_NETWORK="postgres-db-test"

function cleanup () {
  cleanup_docker_container postgres-test > /dev/null 2>&1
  cleanup_docker_container postgres-test-backup
  cleanup_docker_container postgres-test-cli
  cleanup_docker_container pushgateway
  docker network rm "${DOCKER_NETWORK}" > /dev/null 2>&1
  rm -rf "${BACKUP_DIRECTORY}"
}

function create_docker_network() {
  docker network create "${DOCKER_NETWORK}"
}

function start_db() {
    docker run -d --name postgres-test --network "${DOCKER_NETWORK}" postgres:10
    if [ $? -ne 0 ] ; then
        printf "${RED}Start database Failed${NC}\n"
        exit -1
    fi
}

function start_cli() {
  docker run \
      -d \
      --rm \
      --name postgres-test-cli \
      -e PGHOST=postgres-test \
      -e PGUSER=postgres \
      --network "${DOCKER_NETWORK}" \
      -v "${BACKUP_DIRECTORY}":/backups/ \
      lefeverd/docker-db-backup:0.1.0 bash -c \
      "
      while true; do sleep 10; done;
      "
}

function start_prometheus_pushgateway() {
  docker run \
  -d \
  --rm \
  --name pushgateway \
  --network "${DOCKER_NETWORK}" \
  prom/pushgateway
}

function reset_db() {
  cleanup_docker_container postgres-test
  start_db
  printf "Waiting for postgres to start\n"
  sleep 10
  output=$(docker exec -ti postgres-test-cli bash -c \
      "
      psql -d test -c \"select * from users\";
      " 2>&1)
  res=$(echo "${output}" | grep -q "does not exist")
  check_status $? "Database test was still existing after postgres kill."
}

function seed_db() {
  docker exec -ti postgres-test-cli bash -c \
    "
    psql -c \"create database test\";
    psql -d test -c \"create table users (id numeric, name varchar(20)); insert into users (id, name) VALUES (1, 'supertestuser')\";
    "
}

function start_backup() {
    docker run \
      --rm \
      --name postgres-test-backup \
      -e DAYS_TO_KEEP=7 \
      -e BACKUP_SUFFIX=-test \
      -e BACKUP_DIR=/backups/ \
      -e PGHOST=postgres-test \
      -e PGUSER=postgres \
      -v "${BACKUP_DIRECTORY}":/backups/ \
      --network "${DOCKER_NETWORK}" \
      lefeverd/docker-db-backup:0.1.0
    check_status $? "Could not execute backup"
}

function get_backup() {
  backup_file=$(cd "${BACKUP_DIRECTORY}" && find -E "." -regex '.*test_[0-9]{4}-[0-9]{2}-[0-9]{2}.*.dump')
  check_status $? "Could not find backup in ${BACKUP_DIRECTORY}" > /dev/null
  echo "${backup_file}"
}

function restore_backup() {
  backup_file=$(get_backup)
  docker exec -ti postgres-test-cli bash -c \
      "
      pg_restore -Fc -d postgres -C \"/backups/${backup_file}\"
      "
  check_status $? "Could not restore backup ${backup_file}"
}

function verify_restore(){
  output=$(docker exec -ti postgres-test-cli bash -c \
      "
      psql -d test -c \"select * from users;\";
      ")
  res=$(echo "${output}" | grep -q "supertestuser")
  check_status $? "Could not find seed data in restored database."
}

function create_mock_backup_files() {
  extension="$1"
  now_epoch=$(date +%s)
  for i in `seq 0 15`; do
    new_time=$((now_epoch - 86400*i))
    touch -t "$(date -r $new_time +%Y%m%d%H%M.%S)" "${BACKUP_DIRECTORY}/test_2019-02-02${i}-test.${extension}"
  done
}

function verify_cleanup() {
  number_of_backups=$(find "${BACKUP_DIRECTORY}/" | wc -l)
  echo "Number of backups: ${number_of_backups}"
  if [[ "$number_of_backups" -ne 11 ]]; then # DAYS_TO_KEEP=7, + 2 backups executed in tests, + 2 special . and .. files
    check_status -1 "Number of backups remaining after cleanup incorrect."
  fi
}

function test_pushgateway_fail() {
    docker run \
      --rm \
      --name postgres-test-backup \
      -e DAYS_TO_KEEP=7 \
      -e BACKUP_SUFFIX=-test \
      -e BACKUP_DIR=/backups/ \
      -e PGHOST=postgres-test \
      -e PGUSER=postgres \
      -e PROMETHEUS_PUSHGATEWAY_URL=http://127.0.0.1:9999 \
      -v "${BACKUP_DIRECTORY}":/backups/ \
      --network "${DOCKER_NETWORK}" \
      "lefeverd/docker-db-backup:${IMAGE_TAG}"
    check_status $? "Could not execute backup"
}

function test_pushgateway() {
    docker run \
      --rm \
      --name postgres-test-backup \
      -e DAYS_TO_KEEP=7 \
      -e BACKUP_SUFFIX=-test \
      -e BACKUP_DIR=/backups/ \
      -e PGHOST=postgres-test \
      -e PGUSER=postgres \
      -e PROMETHEUS_PUSHGATEWAY_URL=http://pushgateway:9091 \
      -v "${BACKUP_DIRECTORY}":/backups/ \
      --network "${DOCKER_NETWORK}" \
      "lefeverd/docker-db-backup:${IMAGE_TAG}"
    check_status $? "Could not execute backup"
}

function verify_pushgateway() {
    postgres_db_metric='file_size{database="postgres",host="postgres-test",instance="",job="postgres-test-postgres",label="Backup file size in Kilobytes"} 4'
    test_db_metric='file_size{database="test",host="postgres-test",instance="",job="postgres-test-test",label="Backup file size in Kilobytes"} 4'
    docker exec -ti pushgateway sh -c "wget -q -O - 127.0.0.1:9091/metrics | grep -q '$postgres_db_metric'"
    check_status $? "Could not find metric for postgres database"
    docker exec -ti pushgateway sh -c "wget -q -O - 127.0.0.1:9091/metrics | grep -q '$test_db_metric'"
    check_status $? "Could not find metric for test database"
}

function main () {
  mkdir -p "${BACKUP_DIRECTORY}/"
  echo "Building image"
  build_docker_image "${IMAGE_TAG}"
  echo "Cleaning up"
  cleanup
  echo "Creating docker network"
  create_docker_network
  echo "Starting database"
  start_db
  echo "Starting cli container"
  start_cli
  printf "Waiting for postgres to start\n"
  sleep 10
  echo "Adding test data"
  seed_db
  printf "Starting backup\n"
  start_backup
  echo "Reseting database"
  reset_db
  echo "Restoring backup"
  restore_backup
  echo "Verifying restore"
  verify_restore
  echo "Creating mock backup files"
  create_mock_backup_files "sql.gz"
  printf "Starting backup to verify cleanup of mock files\n"
  start_backup
  echo "Verifying cleanup of backup files"
  verify_cleanup
  echo "Testing pushgateway failure"
  test_pushgateway_fail
  echo "Starting Prometheus Pushgateway"
  start_prometheus_pushgateway
  printf "Waiting for Pushgateway to start\n"
  sleep 10
  echo "Testing pushgateway"
  test_pushgateway
  echo "Verifying pushgateway metrics"
  verify_pushgateway
  cleanup
}

# catch unexpected failures, do cleanup and output an error message
trap 'cleanup ; printf "${RED}Tests Failed For Unexpected Reasons${NC}\n"'\
  HUP INT QUIT PIPE TERM

main
