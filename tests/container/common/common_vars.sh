#!/bin/bash

# Default registry is `docker.io`
readonly DOCKER_REGISTRY="${DOCKER_REGISTRY:-docker.io}"
readonly DOCKER_NAMESPACE="${DOCKER_NAMESPACE:-openeuler}"
readonly DOCKER_PACKAGE="${DOCKER_PACKAGE:-$(basename "$0" | sed 's@\(.*\)_test\.sh@\1@')}"
readonly DOCKER_TAG="${DOCKER_TAG:-latest}"
readonly DOCKER_IMAGE="${DOCKER_IMAGE:-${DOCKER_REGISTRY}/${DOCKER_NAMESPACE}/${DOCKER_PACKAGE}:${DOCKER_TAG}}"

readonly DOCKER_PREFIX="${DOCKER_PREFIX:-oe_${DOCKER_PACKAGE}_test}"
readonly DOCKER_NETWORK="${DOCKER_NETWORK:-${DOCKER_PREFIX}_net}"

# List of all supported architectures for the images.
readonly SUPPORTED_ARCHITECTURES="amd64 arm64"
# List of all supported registries.
readonly SUPPORTED_REGISTRIES="hub.oepkgs.net quay.io docker.io"
