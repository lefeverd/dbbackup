#!/bin/bash

DIR="$(cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd)"
source "${DIR}/common.sh"

IMAGE_TAG="test"
BACKUP_DIRECTORY="/tmp/mysql-backups-test/"
DOCKER_NETWORK="mysql-db-test"

function cleanup () {
  cleanup_docker_container mysql-test > /dev/null 2>&1
  cleanup_docker_container mysql-test-backup
  cleanup_docker_container mysql-test-cli
  docker network rm "${DOCKER_NETWORK}" > /dev/null 2>&1
  rm -rf "${BACKUP_DIRECTORY}"
}

function create_docker_network() {
  docker network create "${DOCKER_NETWORK}"
}

function start_db() {
    docker run \
      -d \
      --name mysql-test \
      --network "${DOCKER_NETWORK}" \
      -e MYSQL_DATABASE=test \
      -e MYSQL_USER=test \
      -e MYSQL_PASSWORD=test \
      -e MYSQL_ROOT_PASSWORD=test \
      mysql:5.7
    if [ $? -ne 0 ] ; then
        printf "${RED}Start database Failed${NC}\n"
        exit -1
    fi
}

function start_cli() {
  docker run \
      -d \
      --rm \
      --name mysql-test-cli \
      -e MYSQL_HOST=mysql-test \
      -e MYSQL_USER=mysql \
      --network "${DOCKER_NETWORK}" \
      -v "${BACKUP_DIRECTORY}":/backups/ \
      "lefeverd/docker-db-backup:${IMAGE_TAG}" bash -c \
      "
      while true; do sleep 10; done;
      "
}

function reset_db() {
  cleanup_docker_container mysql-test
  start_db
  printf "Waiting for mysql to start\n"
  sleep 10
  output=$(docker exec -ti mysql-test-cli bash -c \
      "
      mysql -h mysql-test -u test -ptest -D test -e \"select * from users\";
      " 2>&1)
  res=$(echo "${output}" | grep -q "doesn't exist")
  check_status $? "Database test was still existing after mysql kill."
}

function seed_db() {
  docker exec -ti mysql-test-cli bash -c \
    "
    mysql -h mysql-test -u test -ptest -D test -e \"create table users (id numeric, name varchar(20)); insert into users (id, name) VALUES (1, 'supertestuser')\";
    "
}

function start_backup() {
    docker run \
      --rm \
      --name mysql-test-backup \
      -e DAYS_TO_KEEP=7 \
      -e BACKUP_SUFFIX=-test \
      -e BACKUP_DIR=/backups/ \
      -e MYSQL_HOST=mysql-test \
      -e MYSQL_USER=test \
      -e MYSQL_PASSWORD=test \
      -v "${BACKUP_DIRECTORY}":/backups/ \
      --network "${DOCKER_NETWORK}" \
      "lefeverd/docker-db-backup:${IMAGE_TAG}" mysql_backup
    check_status $? "Could not execute backup"
}

function get_backup() {
  backup_file=$(cd "${BACKUP_DIRECTORY}" && find -E "." -regex '.*test_[0-9]{4}-[0-9]{2}-[0-9]{2}.*.sql.gz')
  check_status $? "Could not find backup in ${BACKUP_DIRECTORY}" > /dev/null
  echo "${backup_file}"
}

function restore_backup() {
  backup_file=$(get_backup)
  docker exec -ti mysql-test-cli bash -c \
      "
      gunzip < \"/backups/${backup_file}\" | mysql -p -h mysql-test -u test -ptest test
      "
  check_status $? "Could not restore backup ${backup_file}"
}

function verify_restore(){
  output=$(docker exec -ti mysql-test-cli bash -c \
      "
      mysql -h mysql-test -u test -ptest -D test -e \"select * from users;\"; 
      ")
  res=$(echo "${output}" | grep -q "supertestuser")
  check_status $? "Could not find seed data in restored database."
}

function create_mock_backup_files() {
  now_epoch=$(date +%s)
  for i in `seq 0 15`; do
    new_time=$((now_epoch - 86400*i))
    touch -t "$(date -r $new_time +%Y%m%d%H%M.%S)" "${BACKUP_DIRECTORY}/test_2019-02-02${i}-test.sql.gz"
  done
}

function verify_cleanup() {
  number_of_backups=$(find "${BACKUP_DIRECTORY}/" | wc -l)
  echo "Number of backups: ${number_of_backups}"
  if [[ "$number_of_backups" -ne 11 ]]; then # DAYS_TO_KEEP=7, + 2 backups executed in tests, + 2 special . and .. files
    check_status -1 "Number of backups remaining after cleanup incorrect."
  fi
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
  printf "Waiting for mysql to start\n"
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
  create_mock_backup_files
  printf "Starting backup to verify cleanup of mock files\n"
  start_backup
  echo "Verifying cleanup of backup files"
  verify_cleanup
  echo "Cleaning up"
  cleanup
}

# catch unexpected failures, do cleanup and output an error message
trap 'cleanup ; printf "${RED}Tests Failed For Unexpected Reasons${NC}\n"'\
  HUP INT QUIT PIPE TERM

main
