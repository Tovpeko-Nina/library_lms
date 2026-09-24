# Схема данных

Текущая реализация использует PostgreSQL. Источником исполняемой схемы до внедрения Alembic в ЛР3 является `app/core/database.py`; эта страница описывает её предметный смысл.

```mermaid
erDiagram
    USERS {
        UUID user_id PK
        VARCHAR login UK
        VARCHAR email UK
        TEXT password_hash
        VARCHAR first_name
        VARCHAR last_name
        VARCHAR phone
        TEXT address
        VARCHAR role
        BOOLEAN is_verified
        DATE registration_date
        TEXT faculty
        TEXT department
        TEXT group_name
        DATE graduation_date
        BOOLEAN is_active
        TIMESTAMPTZ last_login
        INTEGER token_version
    }

    BOOKS {
        UUID book_id PK
        VARCHAR isbn UK
        TEXT title
        TEXT author
        TEXT genre
        TEXT publication_date
        TEXT publisher
        NUMERIC replacement_cost
        TEXT description
        INTEGER pages
        TEXT language
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    BOOK_COPIES {
        UUID copy_id PK
        UUID book_id FK
        TEXT branch
        VARCHAR status
        INTEGER copy_number
        TEXT inventory_number UK
        INTEGER publication_year
        INTEGER edition_number
        DATE issue_date
        DATE due_date
        TEXT damage_description
        DATE damaged_date
        DATE lost_date
        UUID lost_by_user_id FK
        DATE acquisition_date
        NUMERIC price
        TEXT condition
    }

    LOANS {
        UUID loan_id PK
        UUID copy_id FK
        UUID user_id FK
        UUID librarian_id FK
        DATE issue_date
        DATE due_date
        DATE return_date
        BOOLEAN is_renewed
        INTEGER renewal_count
        BOOLEAN is_lost
        BOOLEAN is_damaged
        TEXT damage_note
        DATE status_changed_date
        NUMERIC fine_amount
        BOOLEAN fine_paid
        TEXT notes
    }

    FINES {
        UUID fine_id PK
        UUID loan_id FK
        UUID user_id FK
        NUMERIC amount
        VARCHAR type
        TEXT description
        DATE created_date
        DATE paid_date
        BOOLEAN is_paid
    }

    RESERVATIONS {
        UUID reservation_id PK
        UUID copy_id FK
        UUID user_id FK
        DATE reservation_date
        VARCHAR status
        DATE expiry_date
        INTEGER priority
        BOOLEAN notified
        INTEGER preferred_publication_year
        INTEGER preferred_edition_number
    }

    BOOK_QUEUE {
        UUID queue_id PK
        UUID book_id FK
        UUID user_id FK
        INTEGER position
        VARCHAR status
        TIMESTAMPTZ created_at
        TIMESTAMPTZ notified_at
        TIMESTAMPTZ expiry_date
        INTEGER preferred_publication_year
        INTEGER preferred_edition_number
    }

    NOTIFICATIONS {
        UUID notification_id PK
        UUID user_id FK
        TEXT type
        TEXT title
        TEXT message
        TIMESTAMPTZ sent_date
        BOOLEAN is_read
        TIMESTAMPTZ read_date
        TEXT link
    }

    BORROWING_POLICY {
        UUID policy_id PK
        INTEGER max_books_per_user
        INTEGER max_loan_days
        NUMERIC daily_fine_rate
        NUMERIC lost_book_fee
        NUMERIC damaged_book_fee
        INTEGER max_renewals
        INTEGER renewal_days
        NUMERIC max_fine_amount
        INTEGER overdue_grace_period
        TIMESTAMPTZ updated_at
        UUID updated_by FK
    }

    INVENTORY_REPORTS {
        UUID report_id PK
        UUID librarian_id FK
        TIMESTAMPTZ generated_date
        DATE period_start
        DATE period_end
        INTEGER total_books
        INTEGER available_books
        INTEGER issued_books
        INTEGER lost_books
        INTEGER damaged_books
        INTEGER reserved_books
        JSONB books_by_branch
        JSONB lost_books_list
        JSONB damaged_books_list
        TEXT file_path
    }

    USAGE_REPORTS {
        UUID report_id PK
        UUID librarian_id FK
        TIMESTAMPTZ generated_date
        DATE period_start
        DATE period_end
        INTEGER total_loans
        INTEGER total_readers
        NUMERIC average_loan_duration
        JSONB popularity_ranking
        JSONB overdue_items
        NUMERIC total_fines_collected
        JSONB most_active_readers
        TEXT file_path
    }

    INVENTORY_LOG {
        UUID log_id PK
        UUID copy_id FK
        UUID librarian_id FK
        TEXT old_status
        TEXT new_status
        TEXT reason
        TIMESTAMPTZ changed_date
        UUID changed_by_user FK
        UUID loan_id FK
    }

    AUDIT_LOG {
        UUID entry_id PK
        UUID user_id FK
        TEXT action
        TEXT entity_type
        UUID entity_id
        JSONB old_values
        JSONB new_values
        INET ip_address
        TEXT user_agent
        TIMESTAMPTZ timestamp
        TEXT status
    }

    USERS ||--o{ LOANS : borrows
    USERS ||--o{ LOANS : processes
    USERS ||--o{ FINES : receives
    USERS ||--o{ RESERVATIONS : places
    USERS ||--o{ BOOK_QUEUE : joins
    USERS ||--o{ NOTIFICATIONS : receives
    USERS ||--o{ INVENTORY_REPORTS : creates
    USERS ||--o{ USAGE_REPORTS : creates
    USERS ||--o{ INVENTORY_LOG : records
    USERS o|--o{ INVENTORY_LOG : changes
    USERS ||--o{ AUDIT_LOG : performs
    USERS o|--o{ BOOK_COPIES : loses
    USERS o|--o{ BORROWING_POLICY : updates

    BOOKS ||--o{ BOOK_COPIES : contains
    BOOKS ||--o{ BOOK_QUEUE : queues

    BOOK_COPIES ||--o{ LOANS : loaned_in
    BOOK_COPIES ||--o{ RESERVATIONS : reserved_in
    BOOK_COPIES ||--o{ INVENTORY_LOG : tracked_in

    LOANS ||--o{ FINES : causes
    LOANS o|--o{ INVENTORY_LOG : referenced_by
```

## Основные сущности

| Таблица | Назначение | Первичный ключ |
|---|---|---|
| `users` | читатели, библиотекари и администраторы | `user_id` |
| `books` | библиографические издания | `book_id` |
| `book_copies` | физические экземпляры изданий | `copy_id` |
| `loans` | история выдач и возвратов | `loan_id` |
| `fines` | начисленные штрафы | `fine_id` |
| `reservations` | бронирования конкретных экземпляров | `reservation_id` |
| `book_queue` | очередь читателей на издание | `queue_id` |
| `notifications` | сообщения пользователям | `notification_id` |
| `borrowing_policy` | правила выдачи и штрафов | `policy_id` |
| `inventory_log` | журнал состояния экземпляров | `log_id` |
| `audit_log` | журнал значимых действий | `entry_id` |
| `inventory_reports` | сохранённые инвентарные отчёты | `report_id` |
| `usage_reports` | сохранённые отчёты использования | `report_id` |

## Кардинальности и правила

- Одно издание имеет любое число физических экземпляров.
- При добавлении нового физического экземпляра сотрудник обязательно указывает год издания; номер издания необязателен. Экземпляры одной каталожной книги могут относиться к разным выпускам.
- Один экземпляр участвует во многих выдачах во времени, но одновременно должен иметь не более одной активной выдачи.
- Пользователь может иметь много выдач, броней, штрафов и уведомлений.
- Выдачу оформляет один библиотекарь для одного читателя.
- Штраф связан с выдачей, ставшей причиной начисления.
- Бронь относится к экземпляру, очередь — к изданию в целом.
- При заказе читатель может необязательно указать предпочтительные год и номер издания; эти параметры сохраняются и для непосредственной брони, и для очереди.

Справочные значения: роли `ADMIN`, `LIBRARIAN`, `STUDENT`, `EMPLOYEE`; состояния экземпляра `AVAILABLE`, `ISSUED`, `RESERVED`, `LOST`, `DAMAGED`; типы штрафов `OVERDUE`, `LOST_BOOK`, `DAMAGED_BOOK`.

Идентификаторы хранятся как `UUID`, логические значения как `BOOLEAN`, деньги как `NUMERIC(12,2)`, даты как `DATE`, события как `TIMESTAMPTZ`, структурированные отчёты как `JSONB`. Управляемые миграции схемы добавляются в ЛР3.
