# Стратегия тестирования Library LMS

## 1. Назначение документа

Документ определяет единый подход к тестированию Library Management System:

- какие требования проверяются;
- как требования связываются с автоматическими тестами;
- какие уровни и техники тестирования применяются;
- как рассчитываются функциональное покрытие и покрытие кода;
- как изолируются тестовые данные PostgreSQL;
- какие проверки входят в `make verify`;
- какие критерии должны быть выполнены перед принятием изменения.

Стратегия основана на требованиях из `docs/TZ.md`, описании API из
`docs/API.md`, схеме данных из `docs/ER.md` и требованиях лабораторной работы №3.

## 2. Нормативная и методическая основа

| Документ или подход | Применение в проекте |
|---|---|
| ISO/IEC/IEEE 29119-2:2021 | организация процесса планирования, выполнения и завершения тестирования |
| ISO/IEC/IEEE 29119-3:2021 | структура тестовой документации и отчётных материалов |
| ISO/IEC/IEEE 29119-4:2021 | классы эквивалентности, граничные значения, таблицы решений и переходы состояний |
| ISO/IEC 25010:2023 | оценка функциональности, надёжности, безопасности и сопровождаемости |
| ISTQB CTFL 4.0.1 | практические техники анализа и проектирования тестов |
| OWASP ASVS | проверка аутентификации, авторизации, валидации и защиты данных |

Эти документы используются как методическая основа. Настоящий учебный проект не
заявляет о формальной сертификации на соответствие перечисленным стандартам.

## 3. Тестовая база

Тестовые ожидания выводятся не из текущего поведения программы, а из требований.

| Источник | Что определяет |
|---|---|
| `docs/TZ.md` | функции, бизнес-правила, безопасность, ошибки и надёжность |
| `docs/API.md` | маршруты, методы, роли и структура HTTP-взаимодействия |
| `docs/ER.md` | сущности, отношения и ограничения целостности |
| Pydantic-схемы | обязательные поля, типы и допустимые диапазоны |
| миграции Alembic | последовательные версии схемы PostgreSQL |
| требования ЛР3 | тесты, миграции, SAST, backup/restore и `make verify` |

При расхождении реализации и ТЗ ожидаемое поведение определяется ТЗ. Расхождение
фиксируется как дефект или как необходимость согласованно изменить требования.

## 4. Классификация требований

| Префикс | Группа | Количество | Целевое покрытие |
|---|---|---:|---:|
| `FR` | функциональные возможности | 26 | минимум 11/26, целевое 18/26 |
| `BR` | обязательные бизнес-правила | 20 | 20/20 |
| `SEC` | требования безопасности | 13 | 13/13 |
| `ERR` | валидация и обработка ошибок | 10 | 10/10 |
| `MIG` | миграции схемы | 7 | 7/7 |
| `REC` | резервное копирование и восстановление | 8 | 8/8 |
| `QA` | локальный проверочный контур | 16 | 16/16 |
|  | **Всего** | **100** | метрики считаются отдельно по группам |

Группы не объединяются в один процент: высокое покрытие каталога не должно
скрывать отсутствие тестов безопасности, транзакций или восстановления данных.

## 5. Функциональные требования (`FR`)

| ID | Требование | Приоритет | Основной уровень проверки |
|---|---|---|---|
| `FR-01` | регистрация читателя | высокий | API + PostgreSQL |
| `FR-02` | вход по логину и паролю | критический | API + PostgreSQL |
| `FR-03` | хранение пароля в виде bcrypt-хэша | критический | integration |
| `FR-04` | выдача JWT после успешного входа | критический | API |
| `FR-05` | проверка роли на защищённых операциях | критический | API |
| `FR-06` | просмотр каталога | средний | API + PostgreSQL |
| `FR-07` | поиск по каталогу | средний | integration |
| `FR-08` | фильтрация каталога | средний | integration |
| `FR-09` | создание библиографического издания | высокий | API + PostgreSQL |
| `FR-10` | изменение библиографического издания | средний | API + PostgreSQL |
| `FR-11` | создание физического экземпляра | высокий | API + PostgreSQL |
| `FR-12` | изменение физического экземпляра | высокий | integration |
| `FR-13` | верификация пользователя | высокий | API + PostgreSQL |
| `FR-14` | деактивация пользователя | высокий | API + PostgreSQL |
| `FR-15` | выдача экземпляра | критический | integration |
| `FR-16` | возврат экземпляра | критический | integration |
| `FR-17` | продление выдачи | высокий | integration |
| `FR-18` | бронирование доступного экземпляра | критический | integration |
| `FR-19` | постановка читателя в очередь | высокий | integration |
| `FR-20` | штраф за просрочку | высокий | unit + integration |
| `FR-21` | штраф за утрату | высокий | integration |
| `FR-22` | штраф за повреждение | высокий | integration |
| `FR-23` | создание и просмотр уведомлений | средний | integration |
| `FR-24` | формирование инвентарного отчёта | средний | integration |
| `FR-25` | формирование статистического отчёта | средний | integration |
| `FR-26` | изменение администратором правил выдачи | высокий | API + PostgreSQL |
| `FR-27` | управление избранными книгами читателя | средний | unit + integration |

Минимальное функциональное покрытие рассчитывается с округлением вверх:

```text
ceil(27 × 0,40) = ceil(10,8) = 11 функций
```

Рекомендуемая цель имеет запас над минимальным порогом:

```text
19 / 27 × 100% = 70,37%
```

## 6. Обязательные бизнес-правила (`BR`)

| ID | Правило | Приоритет |
|---|---|---|
| `BR-01` | саморегистрация разрешена только для `STUDENT` и `EMPLOYEE` | критический |
| `BR-02` | выдача разрешена только активному читателю | критический |
| `BR-03` | выдача разрешена только верифицированному читателю | критический |
| `BR-04` | без брони выдать можно только экземпляр `AVAILABLE` | критический |
| `BR-05` | экземпляр `RESERVED` можно выдать только владельцу брони | критический |
| `BR-06` | выдача по брони переводит бронь в `FULFILLED` | критический |
| `BR-07` | число активных выдач не превышает установленный лимит | критический |
| `BR-08` | число продлений не превышает установленный лимит | высокий |
| `BR-09` | после выдачи экземпляр получает статус `ISSUED` | критический |
| `BR-10` | после обычного возврата экземпляр получает статус `AVAILABLE` | критический |
| `BR-11` | активные брони отображаются библиотекарю | высокий |
| `BR-12` | очередь читателей отображается библиотекарю | высокий |
| `BR-13` | новая заявка создаёт служебное уведомление | высокий |
| `BR-14` | утерянный экземпляр получает статус `LOST` | высокий |
| `BR-15` | повреждённый экземпляр получает статус `DAMAGED` | высокий |
| `BR-16` | при просрочке может создаваться штраф `OVERDUE` | высокий |
| `BR-17` | при утрате может создаваться штраф `LOST_BOOK` | высокий |
| `BR-18` | при повреждении может создаваться штраф `DAMAGED_BOOK` | высокий |
| `BR-19` | повторная активная бронь одного издания запрещена | высокий |
| `BR-20` | при отсутствии экземпляра читатель ставится в очередь | высокий |

Все правила этой группы обязательны, поэтому целевое покрытие составляет 100%.

## 7. Требования безопасности (`SEC`)

| ID | Требование | Основная проверка |
|---|---|---|
| `SEC-01` | секреты и настройки передаются через окружение | config test + review |
| `SEC-02` | `.env`, пароли, ключи и локальные БД не хранятся в Git | repository check |
| `SEC-03` | JWT-секрет не имеет рабочего значения по умолчанию | unit |
| `SEC-04` | первый администратор создаётся интерактивной CLI-командой | integration |
| `SEC-05` | пароль содержит не менее 12 символов | boundary unit test |
| `SEC-06` | пароль занимает не более 72 байт в UTF-8 | boundary unit test |
| `SEC-07` | пароль хранится только как bcrypt-хэш | integration |
| `SEC-08` | пароль и `password_hash` не возвращаются клиенту | API |
| `SEC-09` | пароли не попадают в журналы и аргументы процессов | integration + review |
| `SEC-10` | смена пароля отзывает ранее выданные JWT | API |
| `SEC-11` | выход отзывает ранее выданные JWT | API |
| `SEC-12` | защищённые операции проверяют JWT | API |
| `SEC-13` | защищённые операции проверяют роль пользователя | API |

Дополнительно весь Python-код проверяется Bandit. Локальное подавление правила
анализатора допускается только рядом с конкретной строкой и с объяснением причины.

## 8. Валидация и обработка ошибок (`ERR`)

| ID | Условие | Ожидаемый результат |
|---|---|---|
| `ERR-01` | отсутствует обязательное поле | HTTP `422` |
| `ERR-02` | неверный тип, формат или диапазон | HTTP `422` |
| `ERR-03` | неверный логин или пароль | HTTP `401` без уточнения причины |
| `ERR-04` | отсутствует аутентификация | HTTP `401` |
| `ERR-05` | JWT повреждён, просрочен или отозван | HTTP `401` |
| `ERR-06` | аутентифицированному пользователю недостаточно прав | HTTP `403` |
| `ERR-07` | запрошенная сущность отсутствует | HTTP `404` |
| `ERR-08` | нарушено бизнес-правило | согласованный HTTP `400` или `409` |
| `ERR-09` | конфликт или повторная активная операция | HTTP `409` |
| `ERR-10` | ошибка составной записи | полный rollback транзакции |

Перед фиксацией API-контракта коды `400` и `409` должны быть унифицированы:
`400` используется для некорректной операции, `409` — для конфликта с текущим
состоянием ресурса.

## 9. Требования миграций (`MIG`)

| ID | Требование |
|---|---|
| `MIG-01` | миграции применяются к чистой БД |
| `MIG-02` | существуют не менее трёх последовательных миграций |
| `MIG-03` | заполненная БД обновляется без потери данных |
| `MIG-04` | повторный `upgrade head` не повреждает схему |
| `MIG-05` | новая функция приложения создаётся через миграцию |
| `MIG-06` | текущая версия схемы фиксируется Alembic |
| `MIG-07` | ошибка миграции обнаруживается `make verify` |

## 10. Требования восстановления (`REC`)

| ID | Требование |
|---|---|
| `REC-01` | `make backup` создаёт резервную копию |
| `REC-02` | копия создаётся из явно выбранной тестовой БД |
| `REC-03` | `make restore` требует явного подтверждения |
| `REC-04` | восстановление требует существующий dump-файл |
| `REC-05` | удалённые данные восстанавливаются |
| `REC-06` | изменённые данные возвращаются к сохранённому состоянию |
| `REC-07` | структура БД восстанавливается вместе с данными |
| `REC-08` | recovery-тест не затрагивает основную БД |

## 11. Требования проверочного контура (`QA`)

| ID | Требование |
|---|---|
| `QA-01` | `make setup` выполняет первоначальную настройку |
| `QA-02` | основные зависимости имеют зафиксированные версии |
| `QA-03` | `make test` запускает автоматические тесты |
| `QA-04` | `make quality` запускает форматирование и статический анализ |
| `QA-05` | Ruff проверяет форматирование и линтерные правила |
| `QA-06` | mypy выполняет статическую проверку типов |
| `QA-07` | Bandit выполняет SAST |
| `QA-08` | формируется JUnit-отчёт |
| `QA-09` | формируется отчёт покрытия |
| `QA-10` | покрытие кода не ниже 40% |
| `QA-11` | `make verify` запускает весь обязательный набор проверок |
| `QA-12` | ошибка любой проверки приводит к ошибке `make verify` |
| `QA-13` | запрещён необоснованный пропуск тестов |
| `QA-14` | запрещено необоснованно снижать порог покрытия |
| `QA-15` | запрещены необоснованные исключения анализаторов |
| `QA-16` | функциональное изменение проходит полный `make verify` |

## 12. Уровни тестирования

| Уровень | Объект | PostgreSQL | Примеры |
|---|---|---:|---|
| Unit | одна функция или правило | нет | пароль, диапазон года, чистый расчёт штрафа |
| Integration | сервис и настоящая БД | да | регистрация, выдача, бронь, rollback |
| API | HTTP, зависимости, сервис и БД | да | `401`, `403`, `404`, структура JSON |
| Migration | последовательность версий схемы | отдельная БД | чистая и заполненная БД |
| Recovery | `pg_dump` и `pg_restore` | отдельная БД | удаление и восстановление данных |
| Scenario | сквозной пользовательский поток | да | регистрация — верификация — выдача — возврат |

## 13. Техники тест-дизайна

| Техника | Применение |
|---|---|
| Классы эквивалентности | роли, статусы, допустимые и недопустимые входные данные |
| Граничные значения | длина пароля, год, лимит выдач и продлений, суммы |
| Таблицы решений | выдача с учётом роли, верификации, статуса и брони |
| Переходы состояний | `AVAILABLE → RESERVED → ISSUED → AVAILABLE` |
| Сценарии использования | полный путь читателя и библиотекаря |
| Error guessing | дубликаты, чужие идентификаторы, повторный запрос, пустые данные |
| Mutation testing | изменение `>=` на `>`, `and` на `or`, статусов и лимитов |

### 13.1. Границы пароля

| Условие | Значения | Ожидание |
|---|---|---|
| минимум 12 символов | 11, 12, 13 | ошибка, успех, успех |
| максимум 72 байта | 71, 72, 73 | успех, успех, ошибка |

### 13.2. Границы года экземпляра

| Значение | Ожидание |
|---:|---|
| 999 | ошибка |
| 1000 | успех |
| 1001 | успех |
| 9998 | успех |
| 9999 | успех |
| 10000 | ошибка |

### 13.3. Таблица решений для выдачи

| Случай | Активен | Верифицирован | Статус экземпляра | Бронь принадлежит читателю | Результат |
|---|---:|---:|---|---:|---|
| R1 | да | да | `AVAILABLE` | нет брони | выдать |
| R2 | нет | да | `AVAILABLE` | нет брони | запретить |
| R3 | да | нет | `AVAILABLE` | нет брони | запретить |
| R4 | да | да | `ISSUED` | нет брони | запретить |
| R5 | да | да | `RESERVED` | да | выдать и выполнить бронь |
| R6 | да | да | `RESERVED` | нет | запретить |
| R7 | да | да | `LOST` или `DAMAGED` | неважно | запретить |
| R8 | да | да | `AVAILABLE` | нет брони | запретить при достигнутом лимите |

## 14. Тестовое окружение и изоляция

Основная БД `lms` никогда не используется автоматическими тестами. Для
параллельных групп выделяются отдельные БД одного тестового PostgreSQL.

| Группа | База данных | Особенности |
|---|---|---|
| Unit | не требуется | нет внешних сервисов |
| Integration и API | `lms_test_integration` | очистка таблиц между тестами |
| Migration | `lms_test_migration` | схема может полностью пересоздаваться |
| Recovery | `lms_test_recovery` | данные намеренно повреждаются и восстанавливаются |

Защитные требования:

- имя тестовой БД должно содержать `test`;
- тесты отказываются очищать БД, не удовлетворяющую этому условию;
- тестовые секреты хранятся только в локальном `.env.test`;
- `.env.test` не включается в Git;
- постоянная пользовательская БД не используется в fixture;
- тестовые записи получают уникальные UUID, login и email.

## 15. Стратегия параллельного запуска

Независимые группы могут выполняться одновременно:

```text
make verify
├── quality                 без изменения БД
├── unit                    без БД
├── integration + API      lms_test_integration
├── migration              lms_test_migration
└── recovery               lms_test_recovery
```

Внутри миграционной и recovery-группы порядок остаётся последовательным:

```text
Migration: base → 001 → 002 → 003 → 004 (head)
Recovery: данные → backup → повреждение → restore → сравнение
```

Unit-тесты при росте набора могут запускаться через `pytest-xdist`. Внутренняя
параллельность integration-тестов допускается только после выделения отдельной
БД каждому worker (`lms_test_integration_gw0`, `..._gw1`).

Каждая параллельная группа формирует отдельные артефакты:

```text
reports/junit-unit.xml
reports/junit-integration.xml
reports/junit-migration.xml
reports/junit-recovery.xml
.coverage.unit
.coverage.integration
.coverage.migration
.coverage.recovery
```

После завершения групп coverage-файлы объединяются, и порог применяется к
общему результату, а не к каждому набору отдельно.

## 16. Расчёт метрик

### 16.1. Покрытие требований

```text
Requirement coverage = Passed requirements / All requirements × 100%
```

Требование засчитывается один раз независимо от числа связанных тестов. В
расчёт входят только требования со статусом `Passed`, а не `Planned`.

### 16.2. Покрытие кода

Используются покрытие инструкций и ветвей:

```text
Code coverage =
    (выполненные инструкции + пройденные ветви)
    / (все инструкции + все ветви) × 100%
```

Обязательный порог уже включён в конфигурации покрытия:

```text
coverage >= 40%
```

Если покрытие опускается ниже порога, `make test` и `make verify` завершаются с
ошибкой. Текущие unit-тесты используют подмену слоя БД, поэтому интеграционные
тесты с отдельной PostgreSQL всё ещё обязательны для проверки настоящего SQL,
ограничений схемы и транзакций.

### 16.3. Mutation score

```text
Mutation score =
    killed mutants / (all mutants - equivalent mutants) × 100%
```

Мутационное тестирование применяется в первую очередь к выдаче, бронированию,
лимитам, продлению, расчёту штрафа и контролю доступа.

## 17. Матрица трассировки

Для каждого требования фиксируются связанные тесты и результат.

| Requirement | Test ID или имя | Уровень | Статус |
|---|---|---|---|
| `SEC-05` | `test_registration_rejects_password_shorter_than_twelve_characters` | unit | Implemented |
| `SEC-06` | `test_registration_rejects_password_longer_than_bcrypt_limit` | unit | Implemented |
| `FR-11` | `test_copy_requires_publication_year` | unit, частичная проверка | Implemented |
| `BR-05` | `test_reserved_copy_cannot_be_issued_to_another_reader` | integration | Planned |
| `BR-06` | `test_issued_reservation_becomes_fulfilled` | integration | Planned |
| `ERR-10` | `test_failed_issue_rolls_back_all_changes` | integration | Planned |
| `QA-04` | `test_schema_is_created_in_dedicated_postgresql` | integration | Implemented |
| `ERR-09` | `test_database_rejects_duplicate_login` | integration | Implemented |
| `FR-11` | `test_database_rejects_invalid_copy_publication_year` | integration | Implemented |
| `ERR-10` | `test_get_db_rolls_back_transaction_after_error` | integration | Implemented |
| `MIG-03` | `test_populated_database_upgrades_without_data_loss` | migration | Planned |
| `REC-05` | `test_deleted_data_is_restored_from_backup` | recovery | Planned |

Статусы:

| Статус | Значение |
|---|---|
| `Planned` | тест запланирован, но ещё не реализован |
| `Implemented` | тест написан, но итоговое требование может быть покрыто частично |
| `Passed` | требование полностью подтверждено успешным тестом |
| `Failed` | тест обнаружил несоответствие |
| `Blocked` | выполнение невозможно по документированной внешней причине |

### 17.1. Уже реализованные тесты

В таблице перечислены фактически существующие тестовые функции. Параметризованный
тест может порождать несколько тестовых случаев, но в таблице указывается один
идентификатор функции.

| Pytest test | Покрываемые требования | Статус и ограничение |
|---|---|---|
| `test_create_environment_generates_private_secrets` | `QA-01`, `SEC-01`, `SEC-02` | Implemented; проверяет локальное создание `.env` |
| `test_create_environment_preserves_existing_file` | `QA-01`, `SEC-02` | Implemented; проверяет сохранение содержимого и права `0600` |
| `test_create_environment_requires_known_placeholders` | `QA-01`, `SEC-03` | Implemented; проверяет отказ для неправильного шаблона |
| `test_env_flag_accepts_true_values` | `QA-01` | Implemented; параметризован |
| `test_env_flag_treats_other_values_as_false` | `QA-01` | Implemented; параметризован |
| `test_env_flag_uses_default_when_variable_is_missing` | `QA-01` | Implemented |
| `test_registration_accepts_valid_password` | `SEC-05`, `SEC-06` | Implemented; только валидация, не регистрация в БД |
| `test_registration_rejects_password_shorter_than_twelve_characters` | `SEC-05`, `ERR-02` | Implemented |
| `test_registration_rejects_password_longer_than_bcrypt_limit` | `SEC-06`, `ERR-02` | Implemented |
| `test_copy_requires_publication_year` | `FR-11`, `ERR-01` | Implemented; частичная проверка Pydantic |
| `test_copy_rejects_publication_year_outside_supported_range` | `FR-11`, `ERR-02` | Implemented; параметризован |
| `test_copy_allows_missing_edition_number` | `FR-11` | Implemented; частичная проверка Pydantic |
| `test_password_is_stored_as_bcrypt_hash` | `FR-03`, `SEC-07` | Implemented |
| `test_wrong_password_does_not_match_bcrypt_hash` | `FR-03`, `ERR-03` | Implemented |
| `test_created_token_contains_required_identity_and_security_claims` | `FR-04`, `SEC-12` | Implemented |
| `test_token_with_wrong_issuer_or_audience_is_rejected` | `SEC-12`, `ERR-05` | Implemented; параметризован |
| `test_expired_token_is_rejected` | `SEC-12`, `ERR-05` | Implemented |
| `test_inactive_reader_cannot_borrow_copy` | `BR-02`, `ERR-08` | Implemented с подменой БД |
| `test_unverified_reader_cannot_borrow_copy` | `BR-03`, `ERR-08` | Implemented с подменой БД |
| `test_available_copy_can_be_issued_without_reservation` | `FR-15`, `BR-04`, `BR-09` | Implemented с подменой БД |
| `test_reserved_copy_can_be_issued_to_reservation_owner` | `FR-15`, `BR-05`, `BR-06`, `BR-09` | Implemented с подменой БД |
| `test_reader_at_active_loan_limit_cannot_borrow` | `BR-07`, `ERR-08` | Implemented с подменой БД |
| `test_loan_at_renewal_limit_cannot_be_renewed` | `BR-08`, `ERR-08` | Implemented с подменой БД |
| `test_normal_return_sets_copy_status_to_available` | `FR-16`, `BR-10` | Implemented с подменой БД |
| `test_lost_return_sets_copy_status_and_creates_fine` | `FR-21`, `BR-14`, `BR-17` | Implemented с подменой БД |
| `test_damaged_return_sets_copy_status_and_creates_fine` | `FR-22`, `BR-15`, `BR-18` | Implemented с подменой БД |
| `test_overdue_return_creates_overdue_fine` | `FR-20`, `BR-16` | Implemented с подменой БД |
| `test_duplicate_active_reservation_is_rejected` | `BR-19`, `ERR-09` | Implemented с подменой БД |
| `test_unavailable_book_places_reader_in_queue_and_notifies_staff` | `FR-19`, `BR-13`, `BR-20` | Implemented с подменой БД |
| `test_active_reservations_and_queue_are_visible_to_staff` | `BR-11`, `BR-12` | Implemented с подменой БД |

`FR-11` пока не получает статус `Passed`: существующие тесты проверяют только
входную схему и не подтверждают вставку экземпляра в PostgreSQL.

### 17.2. Обязательные тесты бизнес-правил

Ниже приведён минимальный каталог тестов, необходимый для покрытия всех `BR`.
Один тест может покрывать несколько требований, но каждое правило должно иметь
хотя бы один положительный или отрицательный тест, реально обнаруживающий его
нарушение.

| Test ID | Pytest test | Покрываемые правила | Суть проверки | Статус |
|---|---|---|---|---|
| `AUTH-BR-001` | `test_student_can_self_register` | `BR-01`, `FR-01` | роль `STUDENT` разрешена | Planned |
| `AUTH-BR-002` | `test_employee_can_self_register` | `BR-01`, `FR-01` | роль `EMPLOYEE` разрешена | Planned |
| `AUTH-BR-003` | `test_admin_and_librarian_cannot_self_register` | `BR-01`, `ERR-08` | служебные роли отклоняются | Planned |
| `LOAN-BR-001` | `test_inactive_reader_cannot_borrow_copy` | `BR-02`, `ERR-08` | неактивному читателю отказано, БД не изменена | Implemented |
| `LOAN-BR-002` | `test_unverified_reader_cannot_borrow_copy` | `BR-03`, `ERR-08` | неверифицированному читателю отказано | Implemented |
| `LOAN-BR-003` | `test_available_copy_can_be_issued_without_reservation` | `BR-04`, `BR-09`, `FR-15` | `AVAILABLE` выдаётся и становится `ISSUED` | Implemented |
| `LOAN-BR-004` | `test_non_available_copy_cannot_be_issued_without_reservation` | `BR-04`, `ERR-08` | `ISSUED`, `LOST`, `DAMAGED` не выдаются | Implemented |
| `LOAN-BR-005` | `test_reserved_copy_can_be_issued_to_reservation_owner` | `BR-05`, `BR-06`, `BR-09`, `FR-15` | владелец получает экземпляр, бронь исполнена | Implemented |
| `LOAN-BR-006` | `test_reserved_copy_cannot_be_issued_to_another_reader` | `BR-05`, `ERR-08`, `ERR-10` | чужая бронь не меняет `loans`, `copies`, `reservations` | Implemented |
| `LOAN-BR-007` | `test_available_copy_can_be_issued_without_reservation` | `BR-07`, `FR-15` | выдача при числе книг ниже лимита разрешена | Implemented |
| `LOAN-BR-008` | `test_reader_at_active_loan_limit_cannot_borrow` | `BR-07`, `ERR-08` | на точной границе лимита новая выдача запрещена | Implemented |
| `LOAN-BR-009` | `test_loan_below_renewal_limit_can_be_renewed` | `BR-08`, `FR-17` | продление до лимита разрешено | Implemented |
| `LOAN-BR-010` | `test_loan_at_renewal_limit_cannot_be_renewed` | `BR-08`, `ERR-08` | на границе лимита продление запрещено | Implemented |
| `LOAN-BR-011` | `test_successful_issue_sets_copy_status_to_issued` | `BR-09`, `FR-15` | статус и даты выдачи сохранены | Planned |
| `LOAN-BR-012` | `test_normal_return_sets_copy_status_to_available` | `BR-10`, `FR-16` | обычный возврат делает экземпляр доступным | Implemented |
| `RES-BR-001` | `test_active_reservations_and_queue_are_visible_to_staff` | `BR-11`, `FR-23` | активная бронь есть в списке сотрудника | Implemented |
| `RES-BR-002` | `test_active_reservations_and_queue_are_visible_to_staff` | `BR-12`, `FR-19` | ожидающий читатель и позиция видны сотруднику | Implemented |
| `RES-BR-003` | `test_unavailable_book_places_reader_in_queue_and_notifies_staff` | `BR-13`, `FR-23` | заявка создаёт служебное уведомление | Implemented |
| `RETURN-BR-001` | `test_lost_return_sets_copy_status_and_creates_fine` | `BR-14`, `BR-17`, `FR-16`, `FR-21` | статус `LOST`, штраф `LOST_BOOK` | Implemented |
| `RETURN-BR-002` | `test_damaged_return_sets_copy_status_and_creates_fine` | `BR-15`, `BR-18`, `FR-16`, `FR-22` | статус `DAMAGED`, штраф `DAMAGED_BOOK` | Implemented |
| `FINE-BR-001` | `test_overdue_return_creates_overdue_fine` | `BR-16`, `FR-20` | просрочка после grace period создаёт штраф | Implemented |
| `FINE-BR-002` | `test_return_within_grace_period_does_not_create_fine` | `BR-16`, `FR-20` | проверяется нижняя граница просрочки | Implemented |
| `RES-BR-004` | `test_duplicate_active_reservation_is_rejected` | `BR-19`, `ERR-09` | вторая активная заявка не создаётся | Implemented |
| `RES-BR-005` | `test_unavailable_book_places_reader_in_queue_and_notifies_staff` | `BR-20`, `FR-19` | вместо фиктивной брони создаётся `WAITING` | Implemented |

Плановое покрытие после успешной реализации таблицы:

```text
BR coverage = 20 / 20 × 100% = 100%
```

### 17.3. Функциональные тесты

Таблица дополняет бизнес-тесты операциями, которые не полностью покрываются
правилами `BR`.

| Test ID | Pytest test | Требования | Статус |
|---|---|---|---|
| `AUTH-FR-001` | `test_student_registration_persists_bcrypt_hash` | `FR-01`, `SEC-07` | Implemented |
| `AUTH-FR-002` | `test_valid_login_returns_bearer_token` | `FR-02`, `FR-04` | Implemented |
| `AUTH-FR-003` | `test_invalid_password_is_rejected` | `FR-02`, `ERR-03` | Implemented |
| `AUTH-FR-004` | `test_password_is_stored_as_bcrypt_hash` | `FR-03`, `SEC-07` | Implemented |
| `ACCESS-FR-001` | `test_librarian_cannot_use_reader_favorites_api` | `FR-05`, `SEC-13`, `ERR-06` | Implemented |
| `BOOK-FR-001` | `test_catalog_applies_search_and_availability_filters` | `FR-06` | Implemented |
| `BOOK-FR-002` | `test_catalog_applies_search_and_availability_filters` | `FR-07` | Implemented |
| `BOOK-FR-003` | `test_catalog_applies_search_and_availability_filters` | `FR-08` | Implemented |
| `BOOK-FR-004` | `test_librarian_can_create_book` | `FR-09` | Implemented |
| `BOOK-FR-005` | `test_book_update_writes_all_editable_fields` | `FR-10` | Implemented |
| `COPY-FR-001` | `test_librarian_can_add_copy_with_required_year` | `FR-11` | Implemented |
| `COPY-FR-002` | `test_copy_status_change_is_recorded_in_inventory_log` | `FR-12` | Implemented |
| `USER-FR-001` | `test_librarian_can_verify_reader` | `FR-13` | Implemented |
| `USER-FR-002` | `test_admin_can_deactivate_user` | `FR-14` | Implemented |
| `NOTICE-FR-001` | `test_notification_owner_can_mark_it_as_read` | `FR-23` | Implemented |
| `REPORT-FR-001` | `test_inventory_report_counts_statuses_and_branches` | `FR-24` | Implemented |
| `REPORT-FR-002` | `test_usage_report_aggregates_loans_readers_and_paid_fines` | `FR-25` | Implemented |
| `POLICY-FR-001` | `test_updated_policy_is_written_and_returned` | `FR-26`, `BR-07` | Implemented |
| `FAVORITE-FR-001` | `test_reader_can_add_list_and_remove_favorite` | `FR-27` | Implemented |

Вместе с тестами из раздела 17.2 автоматические сценарии сопоставлены со всеми
27 из 27 функциональных требований. Это даёт трассировочное покрытие 100%, что
выше обязательных 40%. Уровень доказательства различается: критические HTTP и
PostgreSQL-сценарии проверяются интеграционно, часть вспомогательной логики —
unit-тестами с контролируемой подменой БД.

### 17.4. Тесты безопасности

| Test ID | Pytest test | Требования | Статус |
|---|---|---|---|
| `SEC-T-001` | `test_application_requires_secret_key` | `SEC-01`, `SEC-03` | Planned |
| `SEC-T-002` | `test_repository_does_not_track_secret_files` | `SEC-02` | Planned |
| `SEC-T-003` | `test_admin_bootstrap_does_not_accept_password_argument` | `SEC-04`, `SEC-09` | Planned |
| `SEC-T-004` | `test_password_with_eleven_characters_is_rejected` | `SEC-05`, `ERR-02` | Planned |
| `SEC-T-005` | `test_password_with_twelve_characters_is_accepted` | `SEC-05` | Planned |
| `SEC-T-006` | `test_password_with_seventy_two_utf8_bytes_is_accepted` | `SEC-06` | Planned |
| `SEC-T-007` | `test_password_over_seventy_two_utf8_bytes_is_rejected` | `SEC-06`, `ERR-02` | Implemented under current schema test name |
| `SEC-T-008` | `test_user_responses_never_contain_password_hash` | `SEC-08` | Planned |
| `SEC-T-009` | `test_password_is_not_written_to_logs` | `SEC-09` | Planned |
| `SEC-T-010` | `test_password_change_revokes_existing_token` | `SEC-10` | Planned |
| `SEC-T-011` | `test_logout_revokes_existing_token` | `SEC-11` | Planned |
| `SEC-T-012` | `test_expired_wrong_issuer_and_wrong_audience_tokens_are_rejected` | `SEC-12`, `ERR-05` | Planned |
| `SEC-T-013` | `test_valid_reader_token_cannot_access_admin_operation` | `SEC-13`, `ERR-06` | Planned |

### 17.5. Тесты обработки ошибок и транзакций

| Test ID | Pytest test | Требования | Статус |
|---|---|---|---|
| `ERR-T-001` | `test_missing_required_field_returns_422` | `ERR-01` | Planned |
| `ERR-T-002` | `test_invalid_field_format_returns_422` | `ERR-02` | Planned |
| `ERR-T-003` | `test_invalid_credentials_return_401_without_user_disclosure` | `ERR-03` | Planned |
| `ERR-T-004` | `test_protected_endpoint_without_token_returns_401` | `ERR-04` | Planned |
| `ERR-T-005` | `test_invalid_or_revoked_token_returns_401` | `ERR-05` | Planned |
| `ERR-T-006` | `test_authenticated_reader_without_permission_returns_403` | `ERR-06` | Planned |
| `ERR-T-007` | `test_missing_entity_returns_404` | `ERR-07` | Planned |
| `ERR-T-008` | `test_business_rule_violation_returns_documented_status` | `ERR-08` | Planned |
| `ERR-T-009` | `test_duplicate_active_operation_returns_409` | `ERR-09` | Planned |
| `ERR-T-010` | `test_failed_issue_rolls_back_loan_copy_reservation_and_notification` | `ERR-10` | Planned |

### 17.6. Тесты миграций и восстановления

| Test ID | Pytest test | Требования | Статус |
|---|---|---|---|
| `MIG-T-001` | `test_clean_database_upgrades_to_head` | `MIG-01`, `MIG-02`, `MIG-05`, `MIG-06` | Implemented |
| `MIG-T-002` | `test_revisions_are_applied_in_order` | `MIG-02`, `MIG-06` | Implemented |
| `MIG-T-003` | `test_populated_database_upgrades_without_data_loss` | `MIG-03` | Implemented |
| `MIG-T-004` | `test_upgrade_head_is_idempotent` | `MIG-04` | Implemented |
| `MIG-T-005` | `test_new_feature_schema_exists_after_final_migration` | `MIG-05` | Planned |
| `MIG-T-006` | `test_broken_migration_error_is_not_swallowed` | `MIG-07`, `QA-12` | Implemented |
| `REC-T-001` | `recovery-check: pg_dump creates dump` | `REC-01`, `REC-02` | Implemented |
| `REC-T-002` | `test_restore_requires_explicit_confirmation` | `REC-03` | Planned |
| `REC-T-003` | `test_restore_rejects_missing_dump_file` | `REC-04` | Planned |
| `REC-T-004` | `recovery-check restores deleted row` | `REC-05`, `REC-07` | Implemented |
| `REC-T-005` | `recovery-check restores modified row` | `REC-06` | Implemented |
| `REC-T-006` | `recovery-check uses lms_test container` | `REC-08` | Implemented |

### 17.7. Правило именования тестов

Имя теста описывает наблюдаемое поведение:

```text
test_<условие или действие>_<ожидаемый результат>
```

Хорошие примеры:

```python
test_reader_at_active_loan_limit_cannot_borrow()
test_reserved_copy_can_be_issued_to_reservation_owner()
test_failed_issue_rolls_back_all_changes()
```

Неподходящие имена:

```python
test_loan_1()
test_error()
test_service()
```

В коде связь с требованиями оформляется маркерами:

```python
@pytest.mark.integration
@pytest.mark.requirement("FR-15")
@pytest.mark.requirement("BR-05")
@pytest.mark.requirement("BR-06")
@pytest.mark.requirement("BR-09")
def test_reserved_copy_can_be_issued_to_reservation_owner():
    ...
```

Наличие маркера ещё не делает требование покрытым: тест должен проверять
существенные состояния и успешно выполняться в изолированном окружении.

## 18. Командный интерфейс

| Команда | Назначение |
|---|---|
| `make setup` | первоначальная настройка окружения |
| `make run` | локальный запуск приложения |
| `make test` | автоматические тесты и отчёты |
| `make test-unit` | быстрые unit-тесты без PostgreSQL |
| `make test-api` | HTTP API-тесты с временной PostgreSQL |
| `make test-integration` | интеграционные тесты с временной PostgreSQL |
| `make test-migration` | проверка цепочки миграций на PostgreSQL |
| `make test-recovery` | проверка backup, повреждения и восстановления |
| `make quality` | Ruff, mypy, Bandit и проверка JavaScript |
| `make migrate` | применение миграций |
| `make backup` | создание резервной копии |
| `make restore` | восстановление резервной копии |
| `make verify` | полный обязательный проверочный контур |
| `make up` | запуск контейнерного окружения |
| `make down` | остановка контейнерного окружения |
| `make container-check` | проверка контейнерного окружения |

Окончательный `make verify` должен завершаться ошибкой при падении любого
обязательного этапа.

## 19. Политика пропусков и исключений

- Нельзя добавлять `skip` или `xfail` только для получения зелёного результата.
- Каждый пропуск должен содержать причину и ссылку на задачу.
- Нельзя снижать порог покрытия без отдельного обоснования в PR/MR.
- Нельзя глобально отключать правило Ruff, mypy или Bandit для сокрытия дефекта.
- Локальное исключение анализатора допускается только для ложного срабатывания,
  рядом с конкретной строкой и с комментарием, объясняющим безопасность.
- Нельзя удалять отрицательные или граничные тесты ради прохождения проверки.
- Порядок выполнения тестов не должен влиять на результат.
- Повторный запуск не должен требоваться для маскировки нестабильного теста.

## 20. Критерии приёмки ЛР3

| Критерий | Требуемый результат |
|---|---|
| Функциональное покрытие | 27 из 27 `FR` сопоставлены с автоматическими тестами |
| Бизнес-правила | 20 из 20 `BR` |
| Безопасность | 13 из 13 `SEC` |
| Ошибки | 10 из 10 `ERR` |
| Миграции | 7 из 7 `MIG` |
| Восстановление | 8 из 8 `REC` |
| Проверочный контур | 16 из 16 `QA` |
| Покрытие кода | не менее 40% с учётом ветвей |
| Unit и integration | все обязательные тесты пройдены |
| Пропущенные критические тесты | 0 |
| Ruff/mypy/Bandit | успешно, без необоснованных исключений |
| Чистая БД | `upgrade head` выполнен успешно |
| Заполненная БД | данные сохранены после обновления |
| Backup/restore | контрольные данные восстановлены |
| `make verify` | код возврата 0 |

Значения в этой таблице являются целевыми критериями. Фактически достигнутые
результаты должны формироваться после запуска тестов и не подменяться плановыми.
