import uuid
from contextlib import contextmanager
from datetime import date

import psycopg
from psycopg.rows import dict_row

from .config import DATABASE_URL, INITIAL_ADMIN_PASSWORD, SEED_DEMO_DATA


class Database:
    """Небольшая обёртка над psycopg с единым интерфейсом для сервисов."""

    def __init__(self, connection):
        self.connection = connection

    def execute(self, query, params=None):
        # Сервисы используют DB-API placeholders; psycopg ожидает %s.
        query = query.replace("?", "%s")
        return self.connection.execute(query, params or ())


@contextmanager
def get_db():
    """Открыть PostgreSQL-транзакцию и выполнить commit либо rollback."""
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as connection:
        try:
            yield Database(connection)
            connection.commit()
        except Exception:
            connection.rollback()
            raise


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY,
    login VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(320) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(30),
    address TEXT,
    role VARCHAR(20) NOT NULL CHECK (role IN ('ADMIN','LIBRARIAN','STUDENT','EMPLOYEE')),
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    verification_token TEXT,
    registration_date DATE NOT NULL,
    faculty TEXT,
    department TEXT,
    group_name TEXT,
    graduation_date DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_verified ON users(is_verified);

CREATE TABLE IF NOT EXISTS books (
    book_id UUID PRIMARY KEY,
    isbn VARCHAR(32) UNIQUE,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    genre TEXT,
    publication_date TEXT,
    publisher TEXT,
    replacement_cost NUMERIC(12,2) CHECK (replacement_cost IS NULL OR replacement_cost >= 0),
    description TEXT,
    pages INTEGER CHECK (pages IS NULL OR pages > 0),
    language TEXT NOT NULL DEFAULT 'Русский',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
CREATE INDEX IF NOT EXISTS idx_books_genre ON books(genre);

CREATE TABLE IF NOT EXISTS book_copies (
    copy_id UUID PRIMARY KEY,
    book_id UUID NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    branch TEXT NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('AVAILABLE','ISSUED','RESERVED','LOST','DAMAGED')),
    copy_number INTEGER CHECK (copy_number IS NULL OR copy_number > 0),
    inventory_number TEXT UNIQUE,
    publication_year INTEGER CHECK (publication_year IS NULL OR publication_year BETWEEN 1000 AND 9999),
    edition_number INTEGER CHECK (edition_number IS NULL OR edition_number > 0),
    issue_date DATE,
    due_date DATE,
    damage_description TEXT,
    damaged_date DATE,
    lost_date DATE,
    lost_by_user_id UUID REFERENCES users(user_id),
    acquisition_date DATE NOT NULL,
    price NUMERIC(12,2) CHECK (price IS NULL OR price >= 0),
    condition TEXT NOT NULL DEFAULT 'NEW',
    UNIQUE (book_id, copy_number)
);

ALTER TABLE book_copies
    ADD COLUMN IF NOT EXISTS publication_year INTEGER
    CHECK (publication_year IS NULL OR publication_year BETWEEN 1000 AND 9999);
ALTER TABLE book_copies
    ADD COLUMN IF NOT EXISTS edition_number INTEGER
    CHECK (edition_number IS NULL OR edition_number > 0);

CREATE INDEX IF NOT EXISTS idx_copies_book ON book_copies(book_id);
CREATE INDEX IF NOT EXISTS idx_copies_branch_status ON book_copies(branch, status);
CREATE INDEX IF NOT EXISTS idx_copies_book_status ON book_copies(book_id, status);

CREATE TABLE IF NOT EXISTS loans (
    loan_id UUID PRIMARY KEY,
    copy_id UUID NOT NULL REFERENCES book_copies(copy_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    librarian_id UUID NOT NULL REFERENCES users(user_id),
    issue_date DATE NOT NULL,
    due_date DATE NOT NULL CHECK (due_date >= issue_date),
    return_date DATE,
    is_renewed BOOLEAN NOT NULL DEFAULT FALSE,
    renewal_count INTEGER NOT NULL DEFAULT 0 CHECK (renewal_count >= 0),
    is_lost BOOLEAN NOT NULL DEFAULT FALSE,
    is_damaged BOOLEAN NOT NULL DEFAULT FALSE,
    damage_note TEXT,
    status_changed_date DATE,
    fine_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (fine_amount >= 0),
    fine_paid BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_active_loan_per_copy
    ON loans(copy_id) WHERE return_date IS NULL;
CREATE INDEX IF NOT EXISTS idx_loans_user_issue ON loans(user_id, issue_date DESC);
CREATE INDEX IF NOT EXISTS idx_loans_active_due ON loans(due_date) WHERE return_date IS NULL;

CREATE TABLE IF NOT EXISTS fines (
    fine_id UUID PRIMARY KEY,
    loan_id UUID NOT NULL REFERENCES loans(loan_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    type VARCHAR(30) NOT NULL CHECK (type IN ('OVERDUE','LOST_BOOK','DAMAGED_BOOK')),
    description TEXT,
    created_date DATE NOT NULL,
    paid_date DATE,
    is_paid BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_fines_user_created ON fines(user_id, created_date DESC);
CREATE INDEX IF NOT EXISTS idx_fines_unpaid ON fines(user_id) WHERE is_paid = FALSE;

CREATE TABLE IF NOT EXISTS reservations (
    reservation_id UUID PRIMARY KEY,
    copy_id UUID NOT NULL REFERENCES book_copies(copy_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    reservation_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('ACTIVE','CANCELLED','FULFILLED','EXPIRED')),
    expiry_date DATE NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    notified BOOLEAN NOT NULL DEFAULT FALSE,
    preferred_publication_year INTEGER CHECK (preferred_publication_year IS NULL OR preferred_publication_year BETWEEN 1000 AND 9999),
    preferred_edition_number INTEGER CHECK (preferred_edition_number IS NULL OR preferred_edition_number > 0)
);

ALTER TABLE reservations
    ADD COLUMN IF NOT EXISTS preferred_publication_year INTEGER
    CHECK (preferred_publication_year IS NULL OR preferred_publication_year BETWEEN 1000 AND 9999);
ALTER TABLE reservations
    ADD COLUMN IF NOT EXISTS preferred_edition_number INTEGER
    CHECK (preferred_edition_number IS NULL OR preferred_edition_number > 0);

CREATE UNIQUE INDEX IF NOT EXISTS uq_active_reservation_per_copy
    ON reservations(copy_id) WHERE status = 'ACTIVE';
CREATE INDEX IF NOT EXISTS idx_reservations_user_date ON reservations(user_id, reservation_date DESC);
CREATE INDEX IF NOT EXISTS idx_reservations_active_expiry ON reservations(expiry_date) WHERE status = 'ACTIVE';

CREATE TABLE IF NOT EXISTS notifications (
    notification_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id),
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    sent_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_date TIMESTAMPTZ,
    link TEXT
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_sent ON notifications(user_id, sent_date DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id) WHERE is_read = FALSE;

CREATE TABLE IF NOT EXISTS borrowing_policy (
    policy_id UUID PRIMARY KEY,
    max_books_per_user INTEGER NOT NULL DEFAULT 5 CHECK (max_books_per_user > 0),
    max_loan_days INTEGER NOT NULL DEFAULT 14 CHECK (max_loan_days > 0),
    daily_fine_rate NUMERIC(12,2) NOT NULL DEFAULT 10 CHECK (daily_fine_rate >= 0),
    lost_book_fee NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (lost_book_fee >= 0),
    damaged_book_fee NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (damaged_book_fee >= 0),
    max_renewals INTEGER NOT NULL DEFAULT 2 CHECK (max_renewals >= 0),
    renewal_days INTEGER NOT NULL DEFAULT 7 CHECK (renewal_days > 0),
    max_fine_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (max_fine_amount >= 0),
    overdue_grace_period INTEGER NOT NULL DEFAULT 0 CHECK (overdue_grace_period >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS inventory_reports (
    report_id UUID PRIMARY KEY,
    librarian_id UUID NOT NULL REFERENCES users(user_id),
    generated_date TIMESTAMPTZ NOT NULL,
    period_start DATE,
    period_end DATE,
    total_books INTEGER NOT NULL,
    available_books INTEGER NOT NULL,
    issued_books INTEGER NOT NULL,
    lost_books INTEGER NOT NULL,
    damaged_books INTEGER NOT NULL,
    reserved_books INTEGER NOT NULL,
    books_by_branch JSONB,
    lost_books_list JSONB,
    damaged_books_list JSONB,
    file_path TEXT
);

CREATE TABLE IF NOT EXISTS usage_reports (
    report_id UUID PRIMARY KEY,
    librarian_id UUID NOT NULL REFERENCES users(user_id),
    generated_date TIMESTAMPTZ NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_loans INTEGER NOT NULL,
    total_readers INTEGER NOT NULL,
    average_loan_duration NUMERIC(10,2),
    popularity_ranking JSONB,
    overdue_items JSONB,
    total_fines_collected NUMERIC(12,2),
    most_active_readers JSONB,
    file_path TEXT
);

CREATE TABLE IF NOT EXISTS inventory_log (
    log_id UUID PRIMARY KEY,
    copy_id UUID NOT NULL REFERENCES book_copies(copy_id),
    librarian_id UUID NOT NULL REFERENCES users(user_id),
    old_status TEXT,
    new_status TEXT NOT NULL,
    reason TEXT,
    changed_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    changed_by_user UUID REFERENCES users(user_id),
    loan_id UUID REFERENCES loans(loan_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    entry_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id),
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id UUID,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT
);

CREATE TABLE IF NOT EXISTS book_queue (
    queue_id UUID PRIMARY KEY,
    book_id UUID NOT NULL REFERENCES books(book_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    position INTEGER NOT NULL CHECK (position > 0),
    status VARCHAR(20) NOT NULL CHECK (status IN ('WAITING','NOTIFIED','FULFILLED','CANCELLED','EXPIRED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notified_at TIMESTAMPTZ,
    expiry_date TIMESTAMPTZ,
    preferred_publication_year INTEGER CHECK (preferred_publication_year IS NULL OR preferred_publication_year BETWEEN 1000 AND 9999),
    preferred_edition_number INTEGER CHECK (preferred_edition_number IS NULL OR preferred_edition_number > 0)
);

ALTER TABLE book_queue
    ADD COLUMN IF NOT EXISTS preferred_publication_year INTEGER
    CHECK (preferred_publication_year IS NULL OR preferred_publication_year BETWEEN 1000 AND 9999);
ALTER TABLE book_queue
    ADD COLUMN IF NOT EXISTS preferred_edition_number INTEGER
    CHECK (preferred_edition_number IS NULL OR preferred_edition_number > 0);

CREATE UNIQUE INDEX IF NOT EXISTS uq_active_queue_user_book
    ON book_queue(book_id, user_id) WHERE status IN ('WAITING','NOTIFIED');
CREATE INDEX IF NOT EXISTS idx_queue_book_status_position
    ON book_queue(book_id, status, position);
"""


def init_db():
    """Создать PostgreSQL-схему и, при настройке, начальные данные."""
    from .security import hash_password

    with get_db() as db:
        db.execute(SCHEMA)

        if not db.execute("SELECT 1 FROM borrowing_policy LIMIT 1").fetchone():
            db.execute(
                "INSERT INTO borrowing_policy(policy_id) VALUES(?)",
                (uuid.uuid4(),),
            )

        admin_exists = db.execute(
            "SELECT 1 FROM users WHERE login='admin'"
        ).fetchone()
        if not admin_exists and INITIAL_ADMIN_PASSWORD:
            db.execute(
                """
                INSERT INTO users (
                    user_id, login, email, password_hash,
                    first_name, last_name, role, is_verified, registration_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, TRUE, ?)
                """,
                (
                    uuid.uuid4(), "admin", "admin@library.local",
                    hash_password(INITIAL_ADMIN_PASSWORD),
                    "Администратор", "Системный", "ADMIN", date.today(),
                ),
            )

        if not SEED_DEMO_DATA or db.execute("SELECT 1 FROM books LIMIT 1").fetchone():
            return

        demo_books = [
            ("9785170878561", "Мастер и Маргарита", "Михаил Булгаков", "Роман", "1967", "АСТ"),
            ("9780140449136", "Преступление и наказание", "Фёдор Достоевский", "Классика", "1866", "Penguin"),
            ("9780132350884", "Чистый код", "Роберт Мартин", "Программирование", "2008", "Prentice Hall"),
        ]
        branches = ["AVTOZAVODSKAYA", "KORCHAGINA", "PRYANISHNIKOVA"]

        for book_index, (isbn, title, author, genre, year, publisher) in enumerate(demo_books):
            book_id = uuid.uuid4()
            db.execute(
                """
                INSERT INTO books (
                    book_id, isbn, title, author, genre, publication_date,
                    publisher, description, pages, language
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (book_id, isbn, title, author, genre, year, publisher,
                 "Демонстрационная запись каталога.", 300, "Русский"),
            )
            for number in range(1, 4):
                copy_id = uuid.uuid4()
                db.execute(
                    """
                    INSERT INTO book_copies (
                        copy_id, book_id, branch, status, copy_number,
                        inventory_number, publication_year, edition_number,
                        acquisition_date, price, condition
                    ) VALUES (?, ?, ?, 'AVAILABLE', ?, ?, ?, 1, CURRENT_DATE, ?, 'GOOD')
                    """,
                    (copy_id, book_id, branches[(book_index + number - 1) % 3],
                     number, f"INV-{book_index + 1:02d}-{number:03d}",
                     int(year), 1200 + 100 * book_index),
                )
