#!/bin/bash
set -e

readonly file="$1"
readonly namespace="$2"
readonly repo="$3"
readonly registries="hub.oepkgs.net quay.io docker.io"

# instal docker-pushrm plugin
if [ ! -d "$HOME/.docker/cli-plugins" ]; then
    sudo mkdir -p "$HOME/.docker/cli-plugins"
fi
if [ ! -f $HOME/.docker/cli-plugins/docker-pushrm ]; then
    if [ "$(uname)" = "Darwin" ]; then
        sys="darwin"
    elif [ "$(uname)" = "Linux" ]; then
        sys="linux"
    else
        echo "Unsupported system:" $(uname)
    fi
    if [ "$(uname -m)" = "x86_64" ]; then
        curl -fSL -o $HOME/.docker/cli-plugins/docker-pushrm https://github.com/christian-korneck/docker-pushrm/releases/download/v1.9.0/docker-pushrm_${sys}_amd64
    elif [ "$(uname -m)" == "aarch64" ]; then
        curl -fSL -o $HOME/.docker/cli-plugins/docker-pushrm https://github.com/christian-korneck/docker-pushrm/releases/download/v1.9.0/docker-pushrm_${sys}_arm64
    fi
    sudo chmod +x $HOME/.docker/cli-plugins/docker-pushrm
fi 

# push readme to all registries.
for registry in ${registries}; do
    para=""
    if [ "$registry" == "hub.oepkgs.net" ]; then
        para="-p harbor2"
    fi
    docker login ${registry}
    docker pushrm ${para} -f ${file} ${registry}/${namespace}/${repo}
    echo "Succeed to push README to" ${registry}/${namespace}/${repo}
done
