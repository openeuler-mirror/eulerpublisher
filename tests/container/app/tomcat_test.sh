#!/bin/sh

. "$(dirname "$0")/../common/common_funs.sh"
. "$(dirname "$0")/../common/common_vars.sh"

readonly LOCAL_PORT=8080

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
    container=$(docker run --rm -dit --name "${DOCKER_PREFIX}_${suffix}" -p "$LOCAL_PORT:8080" "${DOCKER_IMAGE}")

    # You definitely need to wait the docker begin to run.
    echo "Start the Docker container..."
    sleep 5
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

test_tomcat_server() {
    # Check if the Tomcat server is running
    output=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$LOCAL_PORT)
    assertEquals "Tomcat server is not running" "200" "$output"
}

# Load shUnit2.
load_shunit2
