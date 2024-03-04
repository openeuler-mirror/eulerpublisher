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

readonly TIME_ZONE="${TIME_ZONE:-UTC}"
readonly INSTALL_PACKAGES="wget tar systemd vim make"

oneTimeSetUp() {
    # Remove image before test.
    remove_current_image

    # Make sure we're using the newest image.
    docker pull --quiet "${DOCKER_IMAGE}" > /dev/null

    # Cleanup stale resources
    tearDown
}

tearDown() {
    for container in $(docker ps -a --filter "name=$DOCKER_PREFIX" --format "{{.Names}}"); do
        debug "Removing container ${container}"
        docker rm -f "${container}" > /dev/null
    done
}

oneTimeTearDown() {
    remove_current_image
}

docker_run() {
    suffix=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 8 | head -n 1)
    docker run \
       --name "${DOCKER_PREFIX}_${suffix}" \
       "${DOCKER_IMAGE}" \
       "$@"
}

test_image_cves() {
    pattern="No vulnerable"
    ret=$(docker scout cves ${DOCKER_IMAGE} 2>/dev/null)
    assertTrue "Found Vulnerabilities" "$(echo $ret | grep "${pattern}")"
}

test_static_image() {
    image_info=$(docker image inspect "$DOCKER_IMAGE" 2>/dev/null)
    os=$(echo "$image_info" | jq -r '.[0].Os')
    assertEquals "linux" "$os"
}

test_timezone_config() {
    assertTrue "Time zone is not $TIME_ZONE" "docker_run date | grep $TIME_ZONE"
}

test_release_version() {
    info=$(docker_run cat /etc/os-release | grep -w "VERSION")
    version=$(echo $info | sed -E 's/VERSION="(.*)"/\1/' | tr -d '()' | tr ' ' '-')
    # Compare in lowercase
    tag=$(echo "$DOCKER_TAG" | tr '[:upper:]' '[:lower:]')
    version=$(echo "$version" | tr '[:upper:]' '[:lower:]')
    assertEquals "$tag" "$version"
}

test_support_archs() {
    find_support_archs
    retval=$?
    assertEquals "$target is not supported" 0 ${retval}
}

test_install_packages() {
    retval=0
    if docker_run sh -c "yum -y update && yum -y install ${INSTALL_PACKAGES}" \
            > /dev/null 2>&1;
    then
        debug "Installation succeeded"
    else
        fail "ERROR: installation failed"
        retval=1
    fi
    assertEquals 0 ${retval}
}

load_shunit2