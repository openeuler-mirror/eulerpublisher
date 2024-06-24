#!/bin/sh

# 导入测试框架
. "$(dirname "$0")/../common/common_funs.sh"
. "$(dirname "$0")/../common/common_vars.sh"

# 设置 Squid 配置文件路径
readonly SQUID_CONF="/etc/squid/squid.conf"

# 设置本地 Squid 代理端口
readonly LOCAL_PORT=3128

oneTimeSetUp() {
    # 移除已有的 Squid 容器
    tearDown

    # 确保使用最新的 OCI 镜像
    docker pull --quiet "${DOCKER_IMAGE}" > /dev/null
}

tearDown() {
    # 停止并删除所有包含 DOCKER_PREFIX 的 Squid 容器
    for container in $(docker ps --filter "name=$DOCKER_PREFIX" --format "{{.Names}}"); do
        debug "Removing container ${container}"
        stop_container_sync "${container}"
    done
}

# 启动 Squid 容器
docker_run_squid() {
    suffix=$(tr -dc 'a-zA-Z0-9' < /dev/urandom | fold -w 8 | head -n 1)
    docker run \
       --rm \
       -d \
       --name "${DOCKER_PREFIX}_${suffix}" \
       -p "${LOCAL_PORT}:3128" \
       "$@" \
       "${DOCKER_IMAGE}"
}

# 等待 Squid 容器就绪
wait_squid_container_ready() {
    local container="${1}"
    local log="squid"
    wait_container_ready "${container}" "${log}"
}

# 测试 Squid 代理是否正常工作
test_squid_proxy() {
    debug "Creating default Squid proxy container"
    container=$(docker_run_squid)

    assertNotNull "Failed to start the container" "${container}" || return 1
    wait_squid_container_ready "${container}" || return 1

    # 使用 curl 测试 Squid 代理
    curl --proxy "http://127.0.0.1:${LOCAL_PORT}" --silent --show-error --output /dev/null "http://example.com"
    assertTrue "Squid proxy test failed" $?

    # 如果测试通过，输出 "ok"
    echo "ok"
}

# 执行测试
load_shunit2
