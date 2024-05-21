#!/bin/bash
#finished!
. "$(dirname "$0")/../common/common_funs.sh"
. "$(dirname "$0")/../common/common_vars.sh"
# cheat sheet:
#  assertTrue $? 
#  assertEquals ["explanation"] 1 2
#  oneTimeSetUp()
#  oneTimeTearDown()
#  setUp() - run before each test
#  tearDown() - run after each test

# DOCKER_NETWORK="nginx_test_network"
# CONTAINER_NAME="nginx_test_container"
HTTP_PORT=8080
oneTimeSetUp() {
    # Remove image before test.
    remove_current_image

    # Make sure we're using the latest OCI image.
    docker pull --quiet "${DOCKER_IMAGE}" > /dev/null
    docker network create "$DOCKER_NETWORK" > /dev/null 2>&1
    # Cleanup stale resources
    tearDown
}

tearDown() {
    for container in $(docker ps --filter "name=$DOCKER_PREFIX" --format "{{.Names}}"); do
        debug "Removing container ${container}"
        stop_container_sync "${container}"
    done

}

# oneTimeTearDown() {
#     docker stop "$CONTAINER_NAME" > /dev/null 2>&1
#     docker network rm "$DOCKER_NETWORK" > /dev/null 2>&1
# }
setUp() {
    # Start Nginx container
    suffix=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 8 | head -n 1)
    docker run \
       --rm \
       -d \
       --name "${DOCKER_PREFIX}_${suffix}" \
       -p "${HTTP_PORT}:80" \
       "$@" \
       "${DOCKER_IMAGE}"
    sleep 5 # Allow time for container to start
}

test_nginx_start() {
    debug "Starting nginx container"
    setUp
    assertTrue "Failed to start the nginx container" "$?"
}
test_nginx_connect_http() {
    debug "Testing HTTP connection to nginx container"
    local response=$(wget -q -O - http://localhost:"${HTTP_PORT}" || true)
    assertTrue "Failed to connect to nginx via HTTP" "[ -n \"$response\" ]"
}

# Load shUnit2.
load_shunit2