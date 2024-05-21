#!/bin/sh
. "$(dirname "$0")/../common/common_funs.sh"
. "$(dirname "$0")/../common/common_vars.sh"

# cheat sheet:
#   assertTrue $? 
#   assertEquals ["explanation"] 1 2
#   oneTimeSetUp()
#   oneTimeTearDown()
#   setUp() - run before each test
#   tearDown() - run after each test

readonly LOCAL_MANAGEMENT_PORT=15672
readonly LOCAL_AMQP_PORT=5672
wait_mycontainer_ready() {
    local id="${1}"
    local timeout="${2:-60}"  # 默认超时时间设置为60秒
    local max=$timeout

    debug "Waiting for container ${id} to be ready"

    for (( i=1; i<=timeout; i++ )); do
        # 使用docker inspect检查容器是否正在运行
        local container_status=$(docker inspect --format '{{.State.Running}}' "$id")
        echo "container_status: $container_status"
        if [ "$container_status" = "true" ]; then
            debug "Container ${id} is ready."
            return 0
        else
            sleep 1
            debug -n "."
        fi
    done

    fail "ERROR, failed to start container ${id} in ${max} seconds"
    echo "Current container list (docker ps):"
    docker ps
    return 1
}
oneTimeSetUp() {
    
    remove_current_image

   
    docker pull --quiet "${DOCKER_IMAGE}" > /dev/null

   
    tearDown
}

tearDown() {
    for container in $(docker ps --filter "name=$DOCKER_PREFIX" --format "{{.Names}}"); do
        debug "Removing container ${container}"
        stop_container_sync "${container}"
    done
}


docker_run_rabbitmq() {
    local suffix=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 8 | head -n 1)
    docker run \
        --rm \
        -d \
        --name "${DOCKER_PREFIX}_${suffix}" \
        -p "${LOCAL_MANAGEMENT_PORT}:${LOCAL_MANAGEMENT_PORT}" \
        -p "${LOCAL_AMQP_PORT}:5672" \
        "${DOCKER_IMAGE}"
}

wait_for_rabbitmq_ready() {
    local container_id="$1"
    # local log="rabbitmq"
    sleep 10
    wait_mycontainer_ready "${container_id}" 
}

test_rabbitmq_service_ready() {
    debug "Creating RabbitMQ container with default configuration"
    container=$(docker_run_rabbitmq)
    assertNotNull "Failed to start the RabbitMQ container" "${container}" || return 1

    if ! wait_for_rabbitmq_ready "${container}"; then
        fail "RabbitMQ did not start within the allocated time."
    fi

    local response=$(wget -q -O - http://localhost:"${LOCAL_AMQP_PORT}" || true)
    assertTrue "Failed to connect to RabbitMQ via HTTP" "[ -n \"$response\" ]"
    echo "response: $response"
    
    
}

# Add more tests to check RabbitMQ functionality, e.g., declaring queues, checking exchanges, etc.

load_shunit2