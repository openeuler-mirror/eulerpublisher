#!/bin/sh

. "$(dirname "$0")/../common/common_funs.sh"
. "$(dirname "$0")/../common/common_vars.sh"

readonly LOCAL_PORT=3100

oneTimeSetUp() {
    # Remove image before test.
    remove_current_image

    # Make sure we're using the latest OCI image.
    echo "Pulling the latest image..."
    docker pull "${DOCKER_IMAGE}"
    echo "Image pulled successfully."

    clean

    # Start the Docker container
    suffix=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 8 | head -n 1)
    container=$(docker run --rm -dit --name "${DOCKER_PREFIX}_${suffix}" -p "$LOCAL_PORT:3100" "${DOCKER_IMAGE}")

    sleep 10
}

oneTimeTearDown() {
    clean
}

clean() {
    for container in $(docker ps --filter "name=$DOCKER_PREFIX" --format "{{.Names}}"); do
        debug "Removing container ${container}"
        stop_container_sync "${container}"
    done
}

test_loki() {
    # Check if the Loki is running
    log=$(docker logs ${DOCKER_PREFIX}_${suffix} | grep 'Loki started')
    echo $log
    if [ -z "$log" ]; then
        fail "Loki is not running"
    fi
}

# Load shUnit2.
load_shunit2
