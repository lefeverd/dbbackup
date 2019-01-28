#!/bin/bash

# define some colors to use for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'


function cleanup () {
  docker-compose -p backup -f docker-compose-postgres.sample.yml kill
  docker-compose -p backup -f docker-compose-postgres.sample.yml rm -f
}

function build_and_run() {
    docker-compose -p backup -f docker-compose-postgres.sample.yml build && 
    docker-compose -p backup -f docker-compose-postgres.sample.yml up -d postgres
    printf "Waiting for postgres to start"
    sleep 5
    printf "Starting backup"
    docker-compose -p backup -f docker-compose-postgres.sample.yml up -d backup-postgres
    if [ $? -ne 0 ] ; then
        printf "${RED}Docker Compose Failed${NC}\n"
        exit -1
    fi
}

function main () {
  build_and_run

  # wait for the test service to complete and grab the exit code
  TEST_EXIT_CODE=$(docker wait backup-postgres)

  # output the logs for the test (for clarity)
  docker logs backup-postgres

  # inspect the output of the test and display respective message
  if [[ "$TEST_EXIT_CODE" -ne 0 ]]; then
    printf "${RED}Tests Failed${NC} - Exit Code: $TEST_EXIT_CODE\n"
  else
    printf "${GREEN}Tests Passed${NC}\n"
  fi

  # call the cleanup fuction
  cleanup

  # exit the script with the same code as the test service code
  exit $TEST_EXIT_CODE

}

# catch unexpected failures, do cleanup and output an error message
trap 'cleanup ; printf "${RED}Tests Failed For Unexpected Reasons${NC}\n"'\
  HUP INT QUIT PIPE TERM

main
