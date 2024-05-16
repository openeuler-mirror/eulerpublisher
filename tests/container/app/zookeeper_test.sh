# !/bin/sh

. "$(dirname "$0")/../common/common_funs.sh"
. "$(dirname "$0")/../common/common_vars.sh"

# cheat sheet:
#  assertTrue $?
#  assertEquals ["explanation"] 1 2
#  oneTimeSetUp()
#  oneTimeTearDown()
#  setUp() - run before each test
#  tearDown() - run after each test

readonly LOCAL_PORT=59080

oneTimeSetUp() {
    # Remove image before test.
    # remove_current_image

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

docker_run_server() {
    suffix=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 8 | head -n 1)
    docker run \
       --rm \
       -d \
       --name "${DOCKER_PREFIX}_${suffix}" \
       "$@" \
       "${DOCKER_IMAGE}"
}


test_zookeeper() {
    container=$(docker_run_server)
    log="Started AdminServer on address"
    ret=$(wait_container_ready "${container}" "${log}")
    assertNotNull "$(echo $ret | grep "$log")"
}

load_shunit2
