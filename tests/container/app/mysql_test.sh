#!/bin/sh

. "$(dirname "$0")/../common/common_funs.sh"
. "$(dirname "$0")/../common/common_vars.sh"

readonly LOCAL_PORT=59080
readonly MYSQL_ROOT_PASSWORD="1234"  # 需要替换为实际的root密码

oneTimeSetUp() {
    # Remove image before test.
    remove_current_image

    # Make sure we're using the latest OCI image.
    docker pull --quiet "${DOCKER_IMAGE}" > /dev/null

    # Cleanup stale resources
    tearDown
}

tearDown() {
    for container in $(docker ps --filter "name=$DOCKER_PREFIX" --format "{{.Names}}"); do
        debug "Removing container ${container}"
        stop_container_sync "${container}"
    done
}

docker_run_mysql() {
    local suffix=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 8 | head -n 1)
    docker run \
        --rm \
        --name "${DOCKER_PREFIX}_${suffix}" \
        -p "${LOCAL_PORT}:3306" \
        -e MYSQL_ROOT_PASSWORD="${MYSQL_ROOT_PASSWORD}" \
        -d \
        "${DOCKER_IMAGE}"
}

wait_mysql_container_ready() {
    local container="${1}"
    local log="mysql"

    wait_container_ready "${container}" "${log}"
}

test_mysql_service() {
    debug "Creating MySQL container with default configuration"
    container=$(docker_run_mysql)
    assertNotNull "Failed to start the MySQL container" "${container}" || return 1

    wait_mysql_container_ready "${container}" || return 1

}

load_shunit2
