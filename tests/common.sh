#!/bin/bash

# define some colors to use for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# printf "${GREEN}Test Passed${NC}\n"

function check_status() {
  status="$1"
  message="$2"
  if [[ "$status" -ne 0 ]]; then
    printf "${RED}Test Failed${NC} - Exit Code: $status - message: $message\n"
    cleanup
    exit -1
  else
    printf "${GREEN}OK${NC}\n"
  fi
}

function cleanup_docker_container() {
  container_name="$1"
  docker kill "${container_name}" > /dev/null 2>&1
  docker rm -f "${container_name}" > /dev/null 2>&1
}

function build_docker_image () {
    IMAGE_TAG="$1"
    docker build -t "lefeverd/docker-db-backup:${IMAGE_TAG}" .
}
