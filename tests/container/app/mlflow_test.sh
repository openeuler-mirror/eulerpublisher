#!/bin/sh

. "$(dirname "$0")/../common/common_funs.sh"
. "$(dirname "$0")/../common/common_vars.sh"

readonly LOCAL_PORT=9999

# Set the MLflow tracking server URI
export MLFLOW_TRACKING_URI="http://127.0.0.1:$LOCAL_PORT"

start_mlflow_server() {
    suffix=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 8 | head -n 1)

    # Start the Docker container
    container=$(docker run --rm -dit --name "${DOCKER_PREFIX}_${suffix}" -p "$LOCAL_PORT:5000" "${DOCKER_IMAGE}")

    # Try to start the MLflow server
    output=$(docker exec -d "${container}" mlflow server --host 0.0.0.0 --port 5000 2>&1)

    if echo "$output" | grep -Fq "Permission denied: './mlruns'"; then
        return 1
    fi
}

oneTimeSetUp() {
    # Remove image before test.
    remove_current_image

    # Make sure we're using the latest OCI image.
    docker pull --quiet "${DOCKER_IMAGE}" > /dev/null

    clean

    pip install -q mlflow 2> /dev/null

    start_mlflow_server
}

oneTimeTearDown() {
    clean
}

clean() {
    for container in $(docker ps --filter "name=$DOCKER_PREFIX" --format "{{.Names}}"); do
        debug "Removing container ${container}"
        stop_container_sync "${container}"
    done

    # Remove mlflow in the local environment
    pip uninstall -q -y mlflow 2> /dev/null
}

test_mlflow_server() {
    # Check if the output contains "Permission denied"
    assertTrue "Permission denied when trying to start the MLflow server. Make sure the user in this container has the permission to create directory." \
    "echo \"$output\" | grep -Fq \"Permission denied: './mlruns'\""
}

test_default_experiment() {
    # Check if the default experiment exists
    default_experiment=$(timeout 10 mlflow experiments search | grep "Default")
    assertTrue 'Default experiment does not exist' "[ -n \"$default_experiment\" ]"
}

test_create_experiment() {
    suffix=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 8 | head -n 1)

    # Create a new experiment
    new_experiment_name="test_experiment_${suffix}"
    timeout 10 mlflow experiments create -n "$new_experiment_name"

    # Check if the new experiment was created
    new_experiment=$(timeout 10 mlflow experiments search | grep "$new_experiment_name")
    assertTrue "Experiment $new_experiment_name was not created" "[ -n \"$new_experiment\" ]"
}

# Load shUnit2.
load_shunit2
