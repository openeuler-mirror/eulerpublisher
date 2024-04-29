#!/bin/bash

. "$(dirname "$0")/../common/common_funs.sh"
. "$(dirname "$0")/../common/common_vars.sh"

# cheat sheet:
#  assertTrue $?
#  assertEquals ["explanation"] 1 2
#  oneTimeSetUp()
#  oneTimeTearDown()
#  setUp() - run before each test
#  tearDown() - run after each test

oneTimeSetUp() {
    # Remove image before test.
    remove_current_image

    # Make sure we're using the latest OCI image.
    docker pull --quiet "${DOCKER_IMAGE}" > /dev/null

    docker network create "$DOCKER_NETWORK" > /dev/null 2>&1
}

oneTimeTearDown() {
  docker stop postgres_test > /dev/null 2>&1
    docker network rm "$DOCKER_NETWORK" > /dev/null 2>&1
}

docker_run_postgres(){
  docker run \
    --rm \
    --name postgres_test \
    -d \
    -p 5432:5432 \
    -e POSTGRES_PASSWORD=postgres \
    "${DOCKER_IMAGE}"
    #debug "${DOCKER_IMAGE}"
}

docker_connect_postgres(){
  debug "Connecting to postgres container"
  docker exec \
  postgres_test \
  psql \
  -U postgres \
  -c "SELECT 1;"
}


test_postgres_start() {

    debug "Creating postgres container"

    container=$(docker_run_postgres)
    assertNotNull "Failed to start the container" "${container}" || return 1

    #echo "${container}"

    sleep 5
    out=$(docker_connect_postgres)

    assertTrue "Failed to connect to the container" "$?" || return 1
    
}

load_shunit2() {
  if [ -e /usr/share/shunit2/shunit2 ]; then
    # shellcheck disable=SC1091
    . /usr/share/shunit2/shunit2
  else
    # shellcheck disable=SC1091
    . shunit2
  fi
}

# Load shUnit2.
load_shunit2
