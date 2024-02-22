#!/bin/bash

ROOTDIR=$(realpath -e "$(dirname "$0")")
export ROOTDIR


load_shunit2() {
  if [ -e /usr/share/shunit2/shunit2 ]; then
    # shellcheck disable=SC1091
    . /usr/share/shunit2/shunit2
  else
    # shellcheck disable=SC1091
    . shunit2
  fi
}

debug() {
    if [ -n "${DEBUG_TESTS}" ]; then
        if [ "${1}" = "-n" ]; then
            shift
            echo -n "$@"
        else
            echo "$@"
        fi
    fi
}

# Creates a new docker container from $DOCKER_IMAGE.
#
# Parameters:
#   $@: parameters to pass through to the container
# Environment:
#   $DOCKER_IMAGE: Name of the image containing the software to be tested.
#       Defaults to "docker.io/ubuntu/<package>:edge"
#   $DOCKER_PREFIX: Common prefix for all containers for this test.
#       Defaults to "oci_<package>_test".
#   $DOCKER_NETWORK: User-created network to connect the container to.
#       Defaults to "oci_<package>_test_net".
#   $SUFFIX: Optional tag for ensuring unique container names.
#       Defaults to a random string.
#
# Stdout: Name of created container.
# Returns: Error code from docker, or 0 on success.
run_container_service() {
    SUFFIX=${SUFFIX:-$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 8 | head -n 1)}
    docker run \
       --network "${DOCKER_NETWORK}" \
       --rm \
       -d \
       --name "${DOCKER_PREFIX}_${SUFFIX}" \
       "${DOCKER_IMAGE}" \
       "$@"
}

# $1: container id
# $2: timeout (optional).  If not specified, defaults to 10 seconds
stop_container_sync() {
    local id=${1}
    local timeout="${2:-10}"
    local max=$timeout

    docker container stop "${id}" > /dev/null 2>&1
    while docker container ls --no-trunc 2>&1 | grep -q "${id}"; do
        sleep 1
        timeout=$((timeout-1))
        if [ "$timeout" -le 0 ]; then
            fail "ERROR, failed to stop container ${id} in ${max} seconds"
            return 1
        fi
    done

    sleep 2
}

# $1: container id
# $2: last message to look for in logs
# $3: timeout (optional).  If not specified, defaults to 60 seconds
wait_container_ready() {
    local id="${1}"
    local msg="${2}"
    local timeout="${3:-60}"
    local max=$timeout

    debug -n "Waiting for container to be ready "
    while ! docker logs "${id}" 2>&1 | grep -E "${msg}"; do
        sleep 1
        timeout=$((timeout - 1))
        if [ $timeout -le 0 ]; then
            fail "ERROR, failed to start container ${id} in ${max} seconds"
            echo "Current container list (docker ps):"
            docker ps
            return 1
        fi
        debug -n "."
    done
    sleep 5
    debug "done"
}

# $1: container id
# ${2...}: source package names to be installed
install_container_packages()
{
    local retval=0
    local id="${1}"
    shift

    docker exec -u root "${id}" yum -qy update > /dev/null
    for package in "${@}"; do
        debug "Installing ${package} into ${id}"
        if docker exec -u root "${id}" \
               yum -qy install "${package}" \
               > /dev/null 2>&1;
        then
            debug "${package} installation succeeded"
        else
            fail "ERROR, failed to install '${package}' into ${id}"
            retval=1
        fi
    done

    return ${retval}
}

# Remove the current image.
# This is useful before starting a test, in order to make sure that
# we're using the latest image available to us.
remove_current_image()
{
    # Remove the current downloaded image.
    if echo "${DOCKER_IMAGE}" | grep -q "^${DOCKER_REGISTRY}"; then
        docker image rm --force "${DOCKER_IMAGE}" > /dev/null 2>&1
    fi
}

find_support_archs() {
    for registry in ${SUPPORTED_REGISTRIES}; do
        image="${registry}/${DOCKER_NAMESPACE}/${DOCKER_PACKAGE}:${DOCKER_TAG}"
        manifests=$(docker manifest inspect $image)
        archs=$(echo "${manifests}" | jq -r '.manifests.[].platform.architecture')
        if [ -z "${archs}" ]; then
            fail "ERROR: Could not obtain manifest list for $image"
            return 1
        fi
        for target in ${SUPPORTED_ARCHITECTURES}; do 
            found=false
            for arch in ${archs}; do
                if [[ "$arch" == "$target" ]]; then
                    found=true
                    break
                fi
            done
            if [ $found == false ]; then
                return 1
            fi
        done
    done
    return 0
}
