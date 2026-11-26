#!/usr/bin/env bash
set -Eeuo pipefail

test "$#" -gt 0 || { echo "Передайте команду проверки" >&2; exit 2; }

cleanup() {
    bash scripts/ci/dind.sh stop || true
}
trap cleanup EXIT

bash scripts/ci/dind.sh start
bash scripts/ci/dind.sh build-tools
bash scripts/ci/dind.sh run "$*"
