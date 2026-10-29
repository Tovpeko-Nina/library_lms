#!/usr/bin/env bash
set -Eeuo pipefail

read -r -a docker_command <<< "${DOCKER:-docker}"
check_port="${CONTAINER_CHECK_PORT:-18000}"
backup_file="$(mktemp --tmpdir library-lms-container-check.XXXXXX.dump)"
check_env="$(mktemp --tmpdir library-lms-container-check.XXXXXX.env)"
chmod 600 "$check_env"
printf 'APP_PORT=%s\n' "$check_port" > "$check_env"
compose=(
    "${docker_command[@]}" compose
    --env-file .env
    --env-file "$check_env"
    --project-name library-lms-container-check
)

cleanup() {
    "${compose[@]}" down --volumes --remove-orphans >/dev/null 2>&1 || true
    rm -f -- "$backup_file" "$check_env"
}
trap cleanup EXIT

database_command() {
    local database_container_id
    database_container_id="$("${compose[@]}" ps --quiet postgres)"
    test -n "$database_container_id"
    timeout 30 "${docker_command[@]}" exec "$database_container_id" sh -euc "$1"
}

echo "[1/10] Проверка Compose-конфигурации и обязательных политик"
"${compose[@]}" config --quiet
if grep -Eq '^[[:space:]]*FROM[[:space:]]+[^[:space:]]*:latest([[:space:]]|$)' Dockerfile; then
    echo "Ошибка: Dockerfile использует latest" >&2
    exit 1
fi
grep -Eq '^USER[[:space:]]+10001:10001$' Dockerfile
grep -Eq '^\.env$' .dockerignore
if grep -Eq 'image:[[:space:]]+[^[:space:]]*:latest([[:space:]]|$)' docker-compose.yml; then
    echo "Ошибка: Compose использует latest" >&2
    exit 1
fi

echo "[2/10] Воспроизводимая сборка и запуск изолированного окружения"
"${compose[@]}" build --pull library-lms
"${compose[@]}" up --detach --wait

echo "[3/10] Healthcheck приложения"
curl --fail --silent --show-error "http://127.0.0.1:${check_port}/health" >/dev/null

echo "[4/10] Непривилегированный пользователь и ограничения ресурсов"
application_id="$("${compose[@]}" ps --quiet library-lms)"
test -n "$application_id"
application_uid="$(timeout 10 "${docker_command[@]}" exec "$application_id" id -u | tr -d '\r')"
test "$application_uid" = "10001"
test "$("${docker_command[@]}" inspect --format '{{.HostConfig.ReadonlyRootfs}}' "$application_id")" = "true"
test "$("${docker_command[@]}" inspect --format '{{.HostConfig.Memory}}' "$application_id")" = "268435456"
test "$("${docker_command[@]}" inspect --format '{{.HostConfig.NanoCpus}}' "$application_id")" = "500000000"
test "$("${docker_command[@]}" inspect --format '{{.HostConfig.PidsLimit}}' "$application_id")" = "100"

echo "[5/10] Порт PostgreSQL не опубликован"
database_id="$("${compose[@]}" ps --quiet postgres)"
published_database_port="$(
    "${docker_command[@]}" inspect \
        --format '{{with (index .NetworkSettings.Ports "5432/tcp")}}{{json .}}{{end}}' \
        "$database_id"
)"
if [[ -n "$published_database_port" ]]; then
    echo "Ошибка: PostgreSQL имеет host-привязку $published_database_port" >&2
    exit 1
fi

echo "[6/10] Сохранность данных после пересоздания контейнера PostgreSQL"
database_command 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "CREATE TABLE IF NOT EXISTS container_check_marker (value TEXT PRIMARY KEY); INSERT INTO container_check_marker(value) VALUES (\$\$volume-survived\$\$) ON CONFLICT DO NOTHING;"'
"${compose[@]}" up --detach --force-recreate --wait postgres
marker="$(database_command 'psql -At -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT value FROM container_check_marker WHERE value=\$\$volume-survived\$\$;"')"
test "$marker" = "volume-survived"

echo "[7/10] Сохранность данных после обновления образа приложения"
"${compose[@]}" build library-lms
"${compose[@]}" up --detach --force-recreate --no-deps --wait library-lms
marker_after_image_update="$(database_command 'psql -At -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT value FROM container_check_marker WHERE value=\$\$volume-survived\$\$;"')"
test "$marker_after_image_update" = "volume-survived"
application_id="$("${compose[@]}" ps --quiet library-lms)"

echo "[8/10] Корректное завершение приложения по SIGTERM"
"${compose[@]}" stop --timeout 20 library-lms
application_exit_code="$(
    "${docker_command[@]}" inspect --format '{{.State.ExitCode}}' "$application_id"
)"
application_oom_killed="$(
    "${docker_command[@]}" inspect --format '{{.State.OOMKilled}}' "$application_id"
)"
test "$application_oom_killed" = "false"
case "$application_exit_code" in
    0|143)
        echo "Приложение завершилось после SIGTERM с кодом $application_exit_code"
        ;;
    *)
        echo "Ошибка: неожиданный код завершения $application_exit_code" >&2
        exit 1
        ;;
esac
"${compose[@]}" up --detach --wait library-lms

echo "[9/10] Backup и восстановление в новый volume"
database_command 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom' > "$backup_file"
"${compose[@]}" down --volumes
"${compose[@]}" up --detach --wait postgres
database_id="$("${compose[@]}" ps --quiet postgres)"
test -n "$database_id"
timeout 30 "${docker_command[@]}" exec --interactive "$database_id" sh -euc \
    'pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists --no-owner --exit-on-error' \
    < "$backup_file"
restored_marker="$(database_command 'psql -At -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT value FROM container_check_marker WHERE value=\$\$volume-survived\$\$;"')"
test "$restored_marker" = "volume-survived"

echo "[10/10] Запуск приложения поверх восстановленной БД"
"${compose[@]}" up --detach --wait library-lms
curl --fail --silent --show-error "http://127.0.0.1:${check_port}/health" >/dev/null

echo "container-check пройден: сборка, non-root, healthcheck, закрытый порт БД,"
echo "лимиты, volume, SIGTERM, backup и восстановление в новый volume проверены."
