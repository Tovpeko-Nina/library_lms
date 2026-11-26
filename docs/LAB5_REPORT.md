# Лабораторная работа №5. Continuous Integration

## Выбранная система

Проект использует GitHub Actions, потому что исходный код уже размещён на
GitHub, отдельный CI-сервер не требуется, а обязательные checks напрямую
подключаются к Pull Request и Ruleset ветки `main`.

Pipeline описан в `.github/workflows/ci.yml`. Внешние Actions закреплены полным
commit SHA, а workflow имеет только разрешение `contents: read`. Публикация в
Docker Hub выполняется обычным Docker CLI и получает учётные данные только в
последнем job.

## События запуска

CI запускается при:

- каждом `push`;
- создании и обновлении Pull Request в `main`;
- `merge_group`, чтобы required check работал с merge queue;
- ручном `workflow_dispatch` для диагностики.

Фильтры путей намеренно не используются: обязательный check не должен исчезнуть
для изменения документации или критического CI-файла.

## Docker-in-Docker

Каждый обязательный job поднимает отдельный привилегированный daemon из образа
`docker:27.5.1-dind-alpine3.21`. GitHub runner выполняет только оркестрацию:
checkout, восстановление кэша и загрузку artifacts. Команды проверки выполняются
в tools-контейнере внутри DinD, а тестовые PostgreSQL и приложение создаются тем
же изолированным daemon.

Контур реализован файлами:

- `Dockerfile.ci` — фиксированный образ Python/Docker/Make/Node/PostgreSQL client;
- `scripts/ci/dind.sh` — запуск daemon, ожидание готовности и запуск команды;
- `scripts/ci/job.sh` — единый lifecycle с обязательной очисткой;
- `.github/actions/dind-check/action.yml` — кэш и artifacts вокруг DinD-команды.

Локально тот же DinD-контур можно проверить командой (она требует
`--privileged` и потому запускается только на доверенной Linux-машине):

```bash
HOST_DOCKER="sudo docker" bash scripts/ci/job.sh \
  'make setup && make test DOCKER=docker'
```

## Структура pipeline

| Job | Локальная команда | Назначение |
|---|---|---|
| Style | `make style` | Ruff format/lint, mypy, JavaScript syntax |
| Tests | `make test` | pytest, API/integration, coverage, JUnit |
| Migrations | `make test-migration` | чистая/заполненная БД и цепочка Alembic |
| Backup recovery | `make test-recovery` | dump, порча и фактическое восстановление |
| Security | `make security` | Bandit, pip-audit и Gitleaks |
| Container check | `make container-check` | полный контур ЛР4 |
| Build image | `make image-build` | SHA-образ и экспорт точного artifact |
| Image scan | `make image-scan` | Trivy HIGH/CRITICAL и secrets |
| Required CI gate | результаты всех jobs | единый required check Ruleset |
| Publish SHA image | `make image-publish` | публикация только успешного `main` |

Jobs до сборки выполняются параллельно. `Build image` имеет `needs` на все
проверки. Trivy загружает сохранённый tar и проверяет именно тот образ, который
затем загружает publish job. Повторная сборка перед публикацией отсутствует.

Первый проход Trivy сохраняет полный JSON со всеми HIGH/CRITICAL-находками.
Второй проход блокирует pipeline для исправимых HIGH/CRITICAL-уязвимостей и
секретов. `--ignore-unfixed` применяется только к blocking-проходу: CVE, для
которой поставщик ещё не выпустил исправление, остаётся в полном отчёте, но не
создаёт невыполнимый gate. Изменение этой политики защищено CODEOWNERS.

## Тестовая БД и отчёты

`compose.test.yml` создаёт отдельную БД `lms_test` на порту 5433 и удаляет её
вместе с volume после job. Production-настройки и данные в CI не используются.

Artifacts хранятся 14 дней:

- `junit.xml`, `coverage.xml`, HTML coverage;
- JSON Bandit, pip-audit и Gitleaks;
- JSON Trivy;
- JSON inspect и tar собранного образа.

Python downloads кэшируются по хэшу `requirements.txt` и
`requirements-dev.txt`. Изменение любой зафиксированной зависимости создаёт
новый ключ кэша.

## Публикация

Docker-образ публикуется только для `push` в `main` и получает тег:

```text
<DOCKERHUB_USERNAME>/library-lms:<полный commit SHA>
```

Тег однозначно связывает artifact с исходным commit. Job `publish` зависит от
`Required CI gate`, сборки и Trivy. При любой ошибке зависимость не достигает
успеха, поэтому публикация не запускается.

В GitHub Settings → Secrets and variables → Actions необходимо создать:

- `DOCKERHUB_USERNAME` — имя пользователя Docker Hub;
- `DOCKERHUB_TOKEN` — access token Docker Hub, не пароль аккаунта.

Перед первым publish в Docker Hub нужно создать репозиторий `library-lms` в
своём namespace и выдать токену только необходимые права чтения/записи.

Секреты не передаются Pull Request jobs и не записываются в репозиторий.

## Защита критических файлов

`.github/CODEOWNERS` назначает владельцев для:

- `.github/` и самого CODEOWNERS;
- `tests/` и стратегии тестирования;
- Makefile, pytest, Ruff/mypy/Bandit и зависимостей;
- Dockerfile, Compose и DinD-скриптов.

После первого успешного CI в GitHub нужно создать Ruleset для `main`:

1. Settings → Rules → Rulesets → New branch ruleset.
2. Target branch: `main`, Enforcement status: Active.
3. Включить Require a pull request before merging.
4. Требовать минимум одно approval.
5. Включить Require review from Code Owners.
6. Включить Dismiss stale approvals и approval последнего push другим участником.
7. Добавить required status check `Required CI gate` от GitHub Actions.
8. Запретить force push и удаление ветки; не выдавать bypass обычным участникам.

CODEOWNERS запрашивает review, а обязательность обеспечивает именно Ruleset.
Unit-тест `test_ci_policy.py` дополнительно обнаруживает удаление jobs, событий,
SHA-тега, DinD или CODEOWNERS, но он не заменяет серверную защиту.

## Демонстрация отрицательных сценариев

### Сломанный тест или миграция

В отдельной ветке временно изменить ожидаемое значение теста либо SQL миграции,
сделать push и открыть PR. Соответствующий job падает, `Build image`,
`Image scan` и `Publish SHA image` не выполняются, Ruleset запрещает merge.

### Тестовый секрет

В одноразовой ветке закоммитить явно тестовый токен формата GitHub PAT. Gitleaks
останавливает Security job и формирует JSON artifact. Такой commit нельзя затем
просто «исправить» следующим commit: сканируется история ветки. После показа
ветку нужно удалить или переписать, а не сливать.

Нельзя использовать настоящий токен даже для демонстрации.

### Удаление проверки

Удалить тест или ослабить `fail_under` в PR. Изменение затрагивает CODEOWNERS,
поэтому требует независимого owner-review; изменение workflow также обнаружит
policy-тест. Без успешного `Required CI gate` GitHub не разрешает merge.

## Почему локальные и CI-команды совпадают

Разные команды создают ситуацию «локально прошло, в CI упало» и позволяют
обойти серверную проверку. CI вызывает тот же Makefile, поэтому правила имеют
один источник истины: разработчик воспроизводит падение локально, а изменение
проверки одновременно влияет на оба контура и попадает под CODEOWNERS.

Полный локальный барьер перед Pull Request:

```bash
make verify DOCKER="sudo docker"
make container-check DOCKER="sudo docker"
```

Контрольный прогон после восстановления правила `BR-02` подтверждает, что
исправленный коммит снова проходит обязательный CI-барьер.

## Соответствие заданию

| Пункт | Реализация |
|---:|---|
| 1–3 | GitHub Actions; `push`, `pull_request`, `merge_group`, ручной запуск |
| 4 | CI вызывает цели того же Makefile, что используются локально |
| 5 | Отдельные jobs style, tests, migrations, backup, security, container, build, publish |
| 6 | Изолированная `lms_test` из `compose.test.yml` |
| 7 | JUnit, coverage и JSON-анализаторы сохраняются как artifacts |
| 8 | pip cache зависит от хэша обоих requirements-файлов |
| 9 | Docker Hub tag равен полному `${GITHUB_SHA}` |
| 10 | build зависит от всех checks, publish — от required gate и image scan |
| 11 | Docker Hub username/token находятся в GitHub Actions Secrets |
| 12 | Gitleaks, pip-audit, Bandit и Trivy |
| 13–14 | CODEOWNERS плюс активный Ruleset и обязательный owner-review |
| 15 | PR с удалением теста/ослаблением policy требует review и зелёный gate |
| 16 | Корректный PR проходит; дефектный останавливается до build/publish |
