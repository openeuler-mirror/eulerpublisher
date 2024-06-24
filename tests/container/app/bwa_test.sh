#!/bin/sh

. "$(dirname "$0")/../common/common_funs.sh"
. "$(dirname "$0")/../common/common_vars.sh"

readonly LOCAL_PORT=59080

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

docker_run_bwa() {
    suffix=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 8 | head -n 1)
    docker run \
       --rm \
       -d \
       --name "${DOCKER_PREFIX}_${suffix}" \
       "$@" \
       "${DOCKER_IMAGE}"
}

wait_bwa_container_ready() {
    local container="${1}"
    wait_container_ready "${container}" "bwa"
}

test_bwa_ok() {
    debug "Creating BWA container"
    container=$(docker_run_bwa)

    assertNotNull "Failed to start the container" "${container}" || return 1
    wait_bwa_container_ready "${container}" || return 1

    # 在这里检查BWA容器是否正常运行，例如：
    container_status=$(docker inspect --format='{{.State.Status}}' "${container}")
    assertEquals "Container status is not running" "running" "${container_status}"
    
    echo "OK"
}


load_shunit2
