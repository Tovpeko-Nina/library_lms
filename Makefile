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

.PHONY: help setup run test test-unit test-api test-integration test-migration test-recovery recovery-check test-db-up test-db-down quality format migrate backup restore verify up down container-check

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
	@echo "  make quality          форматирование, линтер, типы и SAST"
	@echo "  make format           автоматически отформатировать Python-код"
	@echo "  make migrate          применение текущей схемы БД"
	@echo "  make backup           резервная копия PostgreSQL"
	@echo "  make restore BACKUP_FILE=... CONFIRM_RESTORE=yes"
	@echo "  make verify           полный набор локальных проверок"
	@echo "  make up               запуск Docker Compose"
	@echo "  make down             остановка Docker Compose"
	@echo "  make container-check  проверка контейнерного окружения"

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

quality:
	test -x $(VENV_PYTHON) || { echo "Нет виртуального окружения: выполните make setup"; exit 2; }
	$(VENV_PYTHON) -m ruff format --check app scripts tests
	$(VENV_PYTHON) -m ruff check app scripts tests
	$(VENV_PYTHON) -m mypy
	$(VENV_PYTHON) -m bandit -c pyproject.toml -r app scripts
	if command -v node >/dev/null 2>&1; then
		node --check static/js/main.js
	else
		echo "Предупреждение: Node.js не найден, проверка синтаксиса JavaScript пропущена."
	fi

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
	$(VENV_PYTHON) scripts/migrate.py
	@echo "Все миграции Alembic применены."

backup:
	test -f .env || { echo "Нет .env: сначала выполните make setup"; exit 2; }
	set -a
	source .env
	set +a
	mkdir -p backups
	backup_file="backups/lms_$$(date +%Y%m%d_%H%M%S).dump"
	$(VENV_PYTHON) scripts/backup.py --output "$$backup_file"

restore:
	test -n "$(BACKUP_FILE)" || { echo "Укажите BACKUP_FILE: make restore BACKUP_FILE=backups/file.dump CONFIRM_RESTORE=yes"; exit 2; }
	test "$(CONFIRM_RESTORE)" = "yes" || { echo "Восстановление изменит БД. Добавьте CONFIRM_RESTORE=yes"; exit 2; }
	test -f "$(BACKUP_FILE)" || { echo "Файл не найден: $(BACKUP_FILE)"; exit 2; }
	test -f .env || { echo "Нет .env: сначала выполните make setup"; exit 2; }
	set -a
	source .env
	set +a
	$(VENV_PYTHON) scripts/restore.py --backup-file "$(BACKUP_FILE)" --confirm

verify: quality test

up:
	docker compose up --build --detach

down:
	docker compose down

container-check:
	docker compose config --quiet
	docker compose up --build --detach --wait
	curl --fail --silent --show-error http://127.0.0.1:8000/health
	@echo
	@echo "Контейнерное окружение работает. Остановить: make down"
