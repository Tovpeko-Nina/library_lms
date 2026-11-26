SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:

PYTHON ?= python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV_PYTHON) -m pip
UVICORN := $(VENV)/bin/uvicorn

DOCKER ?= docker
TEST_COMPOSE := $(DOCKER) compose -f compose.test.yml -p library-lms-test
GITLEAKS_IMAGE := ghcr.io/gitleaks/gitleaks:v8.30.1
TRIVY_IMAGE := aquasec/trivy:0.76.2
IMAGE_ARCHIVE ?= reports/library-lms-image.tar

.PHONY: help setup run test test-unit test-api test-integration test-migration test-recovery recovery-check test-db-up test-db-down style sast dependency-audit secret-scan security quality format migrate backup db-recreate restore verify up down container-check image-build image-load image-scan image-publish

help:
	@echo "Доступные команды:"
	@echo "  make setup            первоначальная настройка"
	@echo "  make run              локальный запуск"
	@echo "  make test             автоматические тесты и отчёты покрытия"
	@echo "  make test-unit        быстрые unit-тесты без PostgreSQL"
	@echo "  make test-api         HTTP API-тесты с отдельной PostgreSQL"
	@echo "  make test-integration integration-тесты с отдельной PostgreSQL"
	@echo "  make test-migration   последовательные проверки миграций Alembic"
	@echo "  make test-recovery    backup, повреждение и восстановление тестовой БД"
	@echo "  make test-db-up       запуск только тестовой PostgreSQL"
	@echo "  make test-db-down     удаление тестовой PostgreSQL"
	@echo "  make style            форматирование, линтер и проверка типов"
	@echo "  make security         SAST, аудит зависимостей и поиск секретов"
	@echo "  make quality          style и SAST для локальной разработки"
	@echo "  make format           автоматически отформатировать Python-код"
	@echo "  make migrate          применение текущей схемы БД"
	@echo "  make backup           резервная копия PostgreSQL"
	@echo "  make db-recreate CONFIRM_DB_RECREATE=yes  пересоздание контейнерной БД"
	@echo "  make restore BACKUP_FILE=... CONFIRM_RESTORE=yes"
	@echo "  make verify           полный набор локальных проверок"
	@echo "  make up               запуск Docker Compose"
	@echo "  make down             остановка Docker Compose"
	@echo "  make container-check  проверка контейнерного окружения"
	@echo "  make image-build IMAGE=...   сборка и экспорт образа"
	@echo "  make image-scan IMAGE=...    анализ образа через Trivy"
	@echo "  make image-publish IMAGE=... публикация SHA-тега в Docker Hub"

setup:
	$(PYTHON) -c 'import sys; required=(3, 12); current=sys.version_info[:2]; raise SystemExit(0 if current >= required else "Требуется Python 3.12 или новее")'
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install --upgrade pip
	$(VENV_PIP) install -r requirements-dev.txt
	$(VENV_PYTHON) scripts/bootstrap_env.py
	@echo "Первоначальная настройка завершена."
	@echo "Далее: проверьте .env, подготовьте PostgreSQL и выполните make migrate."

run:
	test -f .env || { echo "Нет .env: сначала выполните make setup"; exit 2; }
	test -x $(UVICORN) || { echo "Нет виртуального окружения: выполните make setup"; exit 2; }
	set -a
	source .env
	set +a
	$(UVICORN) app.main:app --host 127.0.0.1 --port 8000 --reload

test:
	test -x $(VENV_PYTHON) || { echo "Нет виртуального окружения: выполните make setup"; exit 2; }
	$(TEST_COMPOSE) up --detach --wait
	trap '$(TEST_COMPOSE) down --volumes' EXIT
	mkdir -p reports
	$(VENV_PYTHON) -m pytest \
		--junitxml=reports/junit.xml \
		--cov=app \
		--cov-report=term-missing \
		--cov-report=html:reports/coverage-html \
		--cov-report=xml:reports/coverage.xml
	$(MAKE) recovery-check DOCKER="$(DOCKER)"

test-unit:
	test -x $(VENV_PYTHON) || { echo "Нет виртуального окружения: выполните make setup"; exit 2; }
	$(VENV_PYTHON) -m pytest -m unit

test-api:
	test -x $(VENV_PYTHON) || { echo "Нет виртуального окружения: выполните make setup"; exit 2; }
	$(TEST_COMPOSE) up --detach --wait
	trap '$(TEST_COMPOSE) down --volumes' EXIT
	$(VENV_PYTHON) -m pytest -m api

test-integration:
	test -x $(VENV_PYTHON) || { echo "Нет виртуального окружения: выполните make setup"; exit 2; }
	$(TEST_COMPOSE) up --detach --wait
	trap '$(TEST_COMPOSE) down --volumes' EXIT
	$(VENV_PYTHON) -m pytest -m integration

test-migration:
	test -x $(VENV_PYTHON) || { echo "Нет виртуального окружения: выполните make setup"; exit 2; }
	$(TEST_COMPOSE) up --detach --wait
	trap '$(TEST_COMPOSE) down --volumes' EXIT
	$(VENV_PYTHON) -m pytest -m migration

test-recovery:
	test -x $(VENV_PYTHON) || { echo "Нет виртуального окружения: выполните make setup"; exit 2; }
	$(TEST_COMPOSE) up --detach --wait
	trap '$(TEST_COMPOSE) down --volumes' EXIT
	$(MAKE) recovery-check DOCKER="$(DOCKER)"

recovery-check:
	export DATABASE_URL="postgresql://lms_test:lms-test-password@127.0.0.1:5433/lms_test"
	$(VENV_PYTHON) -m alembic upgrade head
	$(TEST_COMPOSE) exec -T postgres-test psql -U lms_test -d lms_test -v ON_ERROR_STOP=1 -c \
		"INSERT INTO books(book_id, isbn, title, author) VALUES \
		('00000000-0000-0000-0000-000000000001', 'REC-DELETE', 'Вернуть удалённую', 'Recovery Test'), \
		('00000000-0000-0000-0000-000000000002', 'REC-UPDATE', 'Исходное название', 'Recovery Test') \
		ON CONFLICT (book_id) DO UPDATE SET title=EXCLUDED.title"
	$(TEST_COMPOSE) exec -T postgres-test pg_dump -U lms_test -d lms_test \
		--format=custom --file=/tmp/lms-recovery.dump
	$(TEST_COMPOSE) exec -T postgres-test psql -U lms_test -d lms_test -v ON_ERROR_STOP=1 -c \
		"DELETE FROM books WHERE isbn='REC-DELETE'; \
		 UPDATE books SET title='Повреждённое название' WHERE isbn='REC-UPDATE'"
	$(TEST_COMPOSE) exec -T postgres-test pg_restore -U lms_test -d lms_test \
		--clean --if-exists --no-owner --exit-on-error /tmp/lms-recovery.dump
	restored="$$( $(TEST_COMPOSE) exec -T postgres-test psql -U lms_test -d lms_test \
		--tuples-only --no-align -c \
		"SELECT isbn || ':' || title FROM books WHERE isbn LIKE 'REC-%' ORDER BY isbn" )"
	test "$$restored" = $$'REC-DELETE:Вернуть удалённую\nREC-UPDATE:Исходное название'
	@echo "Recovery-check пройден: удалённые и изменённые данные восстановлены."

test-db-up:
	$(TEST_COMPOSE) up --detach --wait

test-db-down:
	$(TEST_COMPOSE) down --volumes

style:
	test -x $(VENV_PYTHON) || { echo "Нет виртуального окружения: выполните make setup"; exit 2; }
	$(VENV_PYTHON) -m ruff format --check app scripts tests
	$(VENV_PYTHON) -m ruff check app scripts tests
	$(VENV_PYTHON) -m mypy
	if command -v node >/dev/null 2>&1; then
		node --check static/js/main.js
	else
		echo "Предупреждение: Node.js не найден, проверка синтаксиса JavaScript пропущена."
	fi

sast:
	test -x $(VENV_PYTHON) || { echo "Нет виртуального окружения: выполните make setup"; exit 2; }
	mkdir -p reports
	$(VENV_PYTHON) -m bandit -c pyproject.toml -r app scripts \
		--format json --output reports/bandit.json

dependency-audit:
	test -x $(VENV_PYTHON) || { echo "Нет виртуального окружения: выполните make setup"; exit 2; }
	mkdir -p reports .ci-cache/pip-audit
	$(VENV_PYTHON) -m pip_audit --requirement requirements.txt \
		--cache-dir .ci-cache/pip-audit \
		--format json --output reports/pip-audit.json

secret-scan:
	mkdir -p reports
	$(DOCKER) run --rm \
		--volume "$(CURDIR):/repo" \
		$(GITLEAKS_IMAGE) git /repo \
		--redact \
		--report-format=json \
		--report-path=/repo/reports/gitleaks.json

security: sast dependency-audit secret-scan

quality: style sast

format:
	test -x $(VENV_PYTHON) || { echo "Нет виртуального окружения: выполните make setup"; exit 2; }
	$(VENV_PYTHON) -m ruff format app scripts tests
	$(VENV_PYTHON) -m ruff check --fix app scripts tests

migrate:
	test -f .env || { echo "Нет .env: сначала выполните make setup"; exit 2; }
	test -x $(VENV_PYTHON) || { echo "Нет виртуального окружения: выполните make setup"; exit 2; }
	set -a
	source .env
	set +a
	if $(DOCKER) compose ps --status running --services 2>/dev/null | grep -qx 'postgres'; then
		$(DOCKER) compose run --rm --no-deps --build library-lms python scripts/migrate.py
	else
		$(VENV_PYTHON) scripts/migrate.py
	fi
	@echo "Все миграции Alembic применены."

backup:
	test -f .env || { echo "Нет .env: сначала выполните make setup"; exit 2; }
	set -a
	source .env
	set +a
	mkdir -p backups
	backup_file="backups/lms_$$(date +%Y%m%d_%H%M%S).dump"
	if $(DOCKER) compose ps --status running --services 2>/dev/null | grep -qx 'postgres'; then
		$(DOCKER) compose exec -T postgres pg_dump \
			--username="$$POSTGRES_USER" --dbname="$$POSTGRES_DB" \
			--format=custom > "$$backup_file"
		echo "Резервная копия: $$backup_file"
	else
		$(VENV_PYTHON) -m scripts.backup --output "$$backup_file"
	fi

db-recreate:
	test "$(CONFIRM_DB_RECREATE)" = "yes" || { echo "База будет удалена. Добавьте CONFIRM_DB_RECREATE=yes"; exit 2; }
	test -f .env || { echo "Нет .env: сначала выполните make setup"; exit 2; }
	set -a
	source .env
	set +a
	test -n "$$POSTGRES_DB" || { echo "POSTGRES_DB не задан"; exit 2; }
	case "$$POSTGRES_DB" in postgres|template0|template1) echo "Отказ от удаления системной БД: $$POSTGRES_DB"; exit 2;; esac
	$(DOCKER) compose ps --status running --services | grep -qx 'postgres' || { echo "Контейнер PostgreSQL не запущен: выполните make up"; exit 2; }
	$(DOCKER) compose stop library-lms
	$(DOCKER) compose exec -T postgres dropdb \
		--force --if-exists --username="$$POSTGRES_USER" "$$POSTGRES_DB"
	$(DOCKER) compose exec -T postgres createdb \
		--username="$$POSTGRES_USER" --owner="$$POSTGRES_USER" "$$POSTGRES_DB"
	@echo "Пустая база создана. Теперь выполните make restore ..."

restore:
	test -n "$(BACKUP_FILE)" || { echo "Укажите BACKUP_FILE: make restore BACKUP_FILE=backups/file.dump CONFIRM_RESTORE=yes"; exit 2; }
	test "$(CONFIRM_RESTORE)" = "yes" || { echo "Восстановление изменит БД. Добавьте CONFIRM_RESTORE=yes"; exit 2; }
	test -f "$(BACKUP_FILE)" || { echo "Файл не найден: $(BACKUP_FILE)"; exit 2; }
	test -f .env || { echo "Нет .env: сначала выполните make setup"; exit 2; }
	set -a
	source .env
	set +a
	if $(DOCKER) compose ps --status running --services 2>/dev/null | grep -qx 'postgres'; then
		$(DOCKER) compose exec -T postgres pg_restore \
			--username="$$POSTGRES_USER" --dbname="$$POSTGRES_DB" \
			--clean --if-exists --no-owner --exit-on-error < "$(BACKUP_FILE)"
		echo "База восстановлена из: $(BACKUP_FILE)"
	else
		$(VENV_PYTHON) -m scripts.restore --backup-file "$(BACKUP_FILE)" --confirm
	fi

verify: style test security

up:
	$(DOCKER) compose up --build --detach --wait

down:
	$(DOCKER) compose down

container-check:
	DOCKER='$(DOCKER)' bash scripts/container_check.sh

image-build:
	test -n "$(IMAGE)" || { echo "Укажите IMAGE, например IMAGE=library-lms:$${GITHUB_SHA}"; exit 2; }
	mkdir -p reports
	$(DOCKER) build --pull --tag "$(IMAGE)" .
	$(DOCKER) image inspect "$(IMAGE)" > reports/image-inspect.json
	$(DOCKER) image save --output "$(IMAGE_ARCHIVE)" "$(IMAGE)"

image-load:
	test -f "$(IMAGE_ARCHIVE)" || { echo "Архив образа не найден: $(IMAGE_ARCHIVE)"; exit 2; }
	$(DOCKER) image load --input "$(IMAGE_ARCHIVE)"

image-scan:
	test -n "$(IMAGE)" || { echo "Укажите IMAGE"; exit 2; }
	mkdir -p reports
	$(DOCKER) run --rm \
		--volume /var/run/docker.sock:/var/run/docker.sock \
		--volume library-lms-trivy-cache:/root/.cache/ \
		--volume "$(CURDIR)/reports:/reports" \
		$(TRIVY_IMAGE) image \
		--scanners vuln,secret \
		--severity HIGH,CRITICAL \
		--exit-code 0 \
		--format json \
		--output /reports/trivy-image.json \
		"$(IMAGE)"
	$(DOCKER) run --rm \
		--volume /var/run/docker.sock:/var/run/docker.sock \
		--volume library-lms-trivy-cache:/root/.cache/ \
		$(TRIVY_IMAGE) image \
		--scanners vuln,secret \
		--severity HIGH,CRITICAL \
		--ignore-unfixed \
		--exit-code 1 \
		"$(IMAGE)"

image-publish:
	test -n "$(IMAGE)" || { echo "Укажите локальный IMAGE"; exit 2; }
	test -n "$$GITHUB_SHA" || { echo "GITHUB_SHA не задан"; exit 2; }
	test -n "$$DOCKERHUB_USERNAME" || { echo "DOCKERHUB_USERNAME не задан"; exit 2; }
	test -n "$$DOCKERHUB_TOKEN" || { echo "DOCKERHUB_TOKEN не задан"; exit 2; }
	remote_image="$$DOCKERHUB_USERNAME/library-lms:$$GITHUB_SHA"
	echo "$$DOCKERHUB_TOKEN" | $(DOCKER) login --username "$$DOCKERHUB_USERNAME" --password-stdin
	trap '$(DOCKER) logout >/dev/null 2>&1 || true' EXIT
	$(DOCKER) image tag "$(IMAGE)" "$$remote_image"
	$(DOCKER) image push "$$remote_image"
	echo "Опубликован образ: $$remote_image"
