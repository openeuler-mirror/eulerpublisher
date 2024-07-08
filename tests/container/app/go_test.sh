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
}

oneTimeTearDown() {
    docker network rm "$DOCKER_NETWORK" > /dev/null 2>&1
}

# 运行go容器
docker_run_go(){
  docker run \
    --rm \
    --name go_test \
    "${DOCKER_IMAGE}" \
    go version
}

# 测试go容器运行是否成功
test_go_start() {
    debug "Creating go container"

    out=$(docker_run_go)
    assertNotNull "Failed to start the container" "${out}" || return 1

    LINUX_ARCH="amd64"
    if [ x"$(uname -m)" == "xaarch64" ]; then
        LINUX_ARCH="arm64"
    fi

    IMAGE_TAG=${DOCKER_IMAGE##*:}
    APP_VERSION=${IMAGE_TAG%%-*}

    expected="go version go$APP_VERSION linux/$LINUX_ARCH"
    assertEquals "Unexpected go version" "${expected}" "${out}" || return 1
}

# Load shUnit2.
load_shunit2
