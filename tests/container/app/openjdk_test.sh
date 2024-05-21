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

# 运行openJDK容器，查看java版本
docker_run_openjdk(){
  docker run \
    --rm \
    --name openjdk_test \
    openeuler/openjdk:23_13-oe2203sp3 \
    java --version
}

# 测试容器运行是否成功
test_openjdk_start() {
    debug "Creating Java container"

    out=$(docker_run_openjdk | head -n 1)
    assertNotNull "Failed to start the container" "${out}" || return 1

    #输出的java版本信息
    expected="openjdk 23-ea 2024-09-17"
    assertEquals "Unexpected Java version" "${expected}" "${out}" || return 1
}


# Load shUnit2.
load_shunit2
