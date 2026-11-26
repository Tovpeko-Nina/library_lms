#!/usr/bin/env bash
set -Eeuo pipefail

dind_name="${DIND_NAME:-library-lms-ci-dind}"
dind_image="${DIND_IMAGE:-docker:27.5.1-dind-alpine3.21}"
tools_image="${CI_TOOLS_IMAGE:-library-lms-ci-tools:27.5.1}"
workspace="${GITHUB_WORKSPACE:-$(pwd)}"
read -r -a host_docker_command <<< "${HOST_DOCKER:-docker}"

host_docker() {
    env -u DOCKER_HOST "${host_docker_command[@]}" "$@"
}

dind_host() {
    local address
    address="$(host_docker inspect --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$dind_name")"
    test -n "$address"
    printf 'tcp://%s:2375\n' "$address"
}

dind_docker() {
    DOCKER_HOST="$(dind_host)" docker "$@"
}

start() {
    mkdir -p "$workspace/.ci-cache/pip"
    host_docker rm --force "$dind_name" >/dev/null 2>&1 || true
    host_docker run \
        --detach \
        --privileged \
        --name "$dind_name" \
        --env DOCKER_TLS_CERTDIR= \
        --volume "$workspace:$workspace" \
        "$dind_image" \
        --host=tcp://0.0.0.0:2375 \
        --host=unix:///var/run/docker.sock >/dev/null

    for _ in {1..60}; do
        if dind_docker info >/dev/null 2>&1; then
            echo "DinD готов: $(dind_host)"
            return 0
        fi
        sleep 1
    done

    host_docker logs "$dind_name" >&2 || true
    echo "Docker-in-Docker не запустился за 60 секунд" >&2
    return 1
}

build_tools() {
    dind_docker build \
        --pull \
        --file "$workspace/Dockerfile.ci" \
        --tag "$tools_image" \
        "$workspace"
}

run_in_dind() {
    test "$#" -gt 0 || { echo "Передайте команду для запуска" >&2; return 2; }
    local -a protected_environment=()
    if [[ -n "${DOCKERHUB_USERNAME:-}" ]]; then
        protected_environment+=(--env DOCKERHUB_USERNAME)
    fi
    if [[ -n "${DOCKERHUB_TOKEN:-}" ]]; then
        protected_environment+=(--env DOCKERHUB_TOKEN)
    fi
    dind_docker run \
        --rm \
        --network host \
        --env CI=true \
        --env DOCKER_HOST=tcp://127.0.0.1:2375 \
        --env GITHUB_ACTIONS="${GITHUB_ACTIONS:-false}" \
        --env GITHUB_REF="${GITHUB_REF:-}" \
        --env GITHUB_SHA="${GITHUB_SHA:-local}" \
        --env PIP_CACHE_DIR="$workspace/.ci-cache/pip" \
        "${protected_environment[@]}" \
        --volume "$workspace:$workspace" \
        --workdir "$workspace" \
        "$tools_image" \
        bash -Eeuo pipefail -c "$*"
}

stop() {
    host_docker rm --force "$dind_name" >/dev/null 2>&1 || true
}

case "${1:-}" in
    start)
        start
        ;;
    build-tools)
        build_tools
        ;;
    run)
        shift
        run_in_dind "$@"
        ;;
    stop)
        stop
        ;;
    *)
        echo "Использование: $0 {start|build-tools|run <command>|stop}" >&2
        exit 2
        ;;
esac
