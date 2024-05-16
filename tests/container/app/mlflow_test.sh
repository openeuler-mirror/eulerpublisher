#!/bin/sh

. "$(dirname "$0")/../common/common_funs.sh"
. "$(dirname "$0")/../common/common_vars.sh"

readonly LOCAL_PORT=9999

# Set the MLflow tracking server URI
export MLFLOW_TRACKING_URI="http://127.0.0.1:$LOCAL_PORT"

oneTimeSetUp() {
    # Remove image before test.
    remove_current_image

    # Make sure we're using the latest OCI image.
    echo "Pulling the latest image..."
    docker pull "${DOCKER_IMAGE}"
    echo "Image pulled successfully."

    clean
    
    flag=$(pip list | grep mlflow)
    pip install -q mlflow 2> /dev/null

    # Start the Docker container
    suffix=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 8 | head -n 1)
    container=$(docker run --rm -dit --name "${DOCKER_PREFIX}_${suffix}" -p "$LOCAL_PORT:5000" "${DOCKER_IMAGE}")

    # You definitely need to wait the docker begin to run.
    echo "Start the Docker container..."
    sleep 5
}

oneTimeTearDown() {
    clean

    if [[ -n "$flag" ]]; then
        pip uninstall -q -y mlflow 2> /dev/null
    fi
}

clean() {
    for container in $(docker ps --filter "name=$DOCKER_PREFIX" --format "{{.Names}}"); do
        debug "Removing container ${container}"
        stop_container_sync "${container}"
    done
}

test_mlflow_server() {
    # Check if the MLflow server is running  
    output=$(curl -s -o /dev/null -w "%{http_code}" $MLFLOW_TRACKING_URI)
    assertEquals "MLflow server is not running" "200" "$output"
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
