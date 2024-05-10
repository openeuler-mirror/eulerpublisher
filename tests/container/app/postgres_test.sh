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
  docker stop postgres_test > /dev/null 2>&1
    docker network rm "$DOCKER_NETWORK" > /dev/null 2>&1
}
# 运行postgres容器
docker_run_postgres(){
  docker run \
    --rm \
    --name postgres_test \
    -d \
    -p 5432:5432 \
    -e POSTGRES_PASSWORD=postgres \
    "${DOCKER_IMAGE}"
    #debug "${DOCKER_IMAGE}"
}

# 在容器中运行psql命令，进行简单的查询
docker_connect_postgres(){
  debug "Connecting to postgres container"
  docker exec \
  postgres_test \
  psql \
  -U postgres \
  -c "SELECT 1;"
}


test_postgres_start() {

    debug "Creating postgres container"

    container=$(docker_run_postgres)
    assertNotNull "Failed to start the container" "${container}" || return 1

    #echo "${container}"

    sleep 5
    out=$(docker_connect_postgres)

    # 判断命令是否执行成功
    assertTrue "Failed to connect to the container" "$?" || return 1
    
}

# Load shUnit2.
load_shunit2
