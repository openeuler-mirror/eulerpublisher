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

docker_run_server() {
    suffix=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 8 | head -n 1)
    docker run \
       --rm \
       -d \
       --name "${DOCKER_PREFIX}_${suffix}" \
       "$@" \
       "${DOCKER_IMAGE}"
}

wait_httpd_container_ready() {
    local container="${1}"
    local log="httpd"
    wait_container_ready "${container}" "${log}"
}

test_default_config() {
    debug "Creating all-defaults httpd container"
    container=$(docker_run_server -p "$LOCAL_PORT:80")

    assertNotNull "Failed to start the container" "${container}" || return 1
    wait_httpd_container_ready "${container}" || return 1
    logs=$(curl -sS http://127.0.0.1:$LOCAL_PORT)
    (echo $logs | grep -Fq 'working properly') || (echo $logs | grep -Fq 'It works')
    assertTrue $?
}

test_default_config_ipv6() {
    debug "Creating all-defaults httpd container"
    container=$(docker_run_server -p "$LOCAL_PORT:80")

    assertNotNull "Failed to start the container" "${container}" || return 1
    wait_httpd_container_ready "${container}" || return 1

    logs=$(curl -sS http://[::1]:$LOCAL_PORT)
    (echo $logs | grep -Fq 'working properly') || (echo $logs | grep -Fq 'It works')
    assertTrue $?
}

test_static_content() {
    debug "Creating all-defaults httpd container"
    test_data_wwwroot="${ROOTDIR}/httpd_test_data/html"
    container=$(docker_run_server -p "$LOCAL_PORT:80" -v "$test_data_wwwroot:/var/www/html:ro")

    assertNotNull "Failed to start the container" "${container}" || return 1
    wait_httpd_container_ready "${container}" || return 1

    orig_checksum=$(md5sum "$test_data_wwwroot/test.txt" | awk '{ print $1 }')
    retrieved_checksum=$(curl -sS http://127.0.0.1:$LOCAL_PORT/test.txt | md5sum | awk '{ print $1 }')

    assertEquals "Checksum mismatch in retrieved test.txt" "${orig_checksum}" "${retrieved_checksum}"
}

load_shunit2
