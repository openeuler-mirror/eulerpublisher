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
    debug "pulling image ${DOCKER_IMAGE}"
    docker pull --quiet "${DOCKER_IMAGE}" > /dev/null
    debug "done pulling image ${DOCKER_IMAGE}"

    docker network create "$DOCKER_NETWORK" > /dev/null 2>&1

    # Cleanup stale resources
    tearDown
}

tearDown() {
    for container in $(docker ps --filter "name=$DOCKER_PREFIX" --format "{{.Names}}"); do
        debug "Removing container ${container}"
        docker network remove "$DOCKER_NETWORK"
        stop_container_sync "${container}"
    done
}

wait_go_container_ready() {
    local container="${1}"
    wait_container_ready "${container}" "go"
}

# 测试go容器运行是否成功
test_go_start() {
    debug "Creating go container"
    local container=$(run_container_service)
    assertNotNull "Failed to start the container" "${container}" || return 1
    
    wait_go_container_ready "${container}" || return 1
    local status=$(docker inspect --format='{{.State.Status}}' "${container}")
    assertEquals "Container status is not running" "running" "${status}"
}


# 运行go Hello World
test_hello_world() {
    debug "Test run hello world!"
    local out=$(docker_run_go go run /tmp/HelloWorld.go)
    assertEquals "Hello World" "${out}" || return 1
}

# 运行go容器
docker_run_go(){
  suffix=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 8 | head -n 1)
  docker run \
    --rm \
    --name "${DOCKER_PREFIX}_${suffix}" \
    -v ${ROOTDIR}/go_test_data/HelloWorld.go:/tmp/HelloWorld.go \
    "${DOCKER_IMAGE}" \
    "$@"
}

# Load shUnit2.
load_shunit2
