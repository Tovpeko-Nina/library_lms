"""Create the initial library schema.

Revision ID: 001
Revises: None
"""

from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


INITIAL_SCHEMA = """
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    login VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(320) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(30), address TEXT,
    role VARCHAR(20) NOT NULL CHECK (role IN ('ADMIN','LIBRARIAN','STUDENT','EMPLOYEE')),
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    registration_date DATE NOT NULL,
    faculty TEXT, department TEXT, group_name TEXT, graduation_date DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_login TIMESTAMPTZ
);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_verified ON users(is_verified);

CREATE TABLE books (
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
CREATE INDEX idx_books_title ON books(title);
CREATE INDEX idx_books_author ON books(author);
CREATE INDEX idx_books_genre ON books(genre);

CREATE TABLE book_copies (
    copy_id UUID PRIMARY KEY,
    book_id UUID NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    branch TEXT NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('AVAILABLE','ISSUED','RESERVED','LOST','DAMAGED')),
    copy_number INTEGER CHECK (copy_number IS NULL OR copy_number > 0),
    inventory_number TEXT UNIQUE,
    issue_date DATE, due_date DATE,
    damage_description TEXT, damaged_date DATE, lost_date DATE,
    lost_by_user_id UUID REFERENCES users(user_id),
    acquisition_date DATE NOT NULL,
    price NUMERIC(12,2) CHECK (price IS NULL OR price >= 0),
    condition TEXT NOT NULL DEFAULT 'NEW',
    UNIQUE (book_id, copy_number)
);
CREATE INDEX idx_copies_book ON book_copies(book_id);
CREATE INDEX idx_copies_branch_status ON book_copies(branch, status);
CREATE INDEX idx_copies_book_status ON book_copies(book_id, status);

CREATE TABLE loans (
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
    damage_note TEXT, status_changed_date DATE,
    fine_amount NUMERIC(12,2) NOT NULL DEFAULT 0 CHECK (fine_amount >= 0),
    fine_paid BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT
);
CREATE UNIQUE INDEX uq_active_loan_per_copy ON loans(copy_id) WHERE return_date IS NULL;
CREATE INDEX idx_loans_user_issue ON loans(user_id, issue_date DESC);
CREATE INDEX idx_loans_active_due ON loans(due_date) WHERE return_date IS NULL;

CREATE TABLE fines (
    fine_id UUID PRIMARY KEY,
    loan_id UUID NOT NULL REFERENCES loans(loan_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    amount NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    type VARCHAR(30) NOT NULL CHECK (type IN ('OVERDUE','LOST_BOOK','DAMAGED_BOOK')),
    description TEXT, created_date DATE NOT NULL, paid_date DATE,
    is_paid BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE INDEX idx_fines_user_created ON fines(user_id, created_date DESC);
CREATE INDEX idx_fines_unpaid ON fines(user_id) WHERE is_paid = FALSE;

CREATE TABLE reservations (
    reservation_id UUID PRIMARY KEY,
    copy_id UUID NOT NULL REFERENCES book_copies(copy_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    reservation_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('ACTIVE','CANCELLED','FULFILLED','EXPIRED')),
    expiry_date DATE NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    notified BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE UNIQUE INDEX uq_active_reservation_per_copy ON reservations(copy_id) WHERE status = 'ACTIVE';
CREATE INDEX idx_reservations_user_date ON reservations(user_id, reservation_date DESC);
CREATE INDEX idx_reservations_active_expiry ON reservations(expiry_date) WHERE status = 'ACTIVE';

CREATE TABLE notifications (
    notification_id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(user_id),
    type TEXT NOT NULL, title TEXT NOT NULL, message TEXT NOT NULL,
    sent_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_date TIMESTAMPTZ, link TEXT
);
CREATE INDEX idx_notifications_user_sent ON notifications(user_id, sent_date DESC);
CREATE INDEX idx_notifications_unread ON notifications(user_id) WHERE is_read = FALSE;

CREATE TABLE borrowing_policy (
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
INSERT INTO borrowing_policy(policy_id) VALUES(gen_random_uuid());

CREATE TABLE inventory_reports (
    report_id UUID PRIMARY KEY,
    librarian_id UUID NOT NULL REFERENCES users(user_id),
    generated_date TIMESTAMPTZ NOT NULL,
    period_start DATE, period_end DATE,
    total_books INTEGER NOT NULL, available_books INTEGER NOT NULL,
    issued_books INTEGER NOT NULL, lost_books INTEGER NOT NULL,
    damaged_books INTEGER NOT NULL, reserved_books INTEGER NOT NULL,
    books_by_branch JSONB, lost_books_list JSONB, damaged_books_list JSONB,
    file_path TEXT
);
CREATE TABLE usage_reports (
    report_id UUID PRIMARY KEY,
    librarian_id UUID NOT NULL REFERENCES users(user_id),
    generated_date TIMESTAMPTZ NOT NULL,
    period_start DATE NOT NULL, period_end DATE NOT NULL,
    total_loans INTEGER NOT NULL, total_readers INTEGER NOT NULL,
    average_loan_duration NUMERIC(10,2), popularity_ranking JSONB,
    overdue_items JSONB, total_fines_collected NUMERIC(12,2),
    most_active_readers JSONB, file_path TEXT
);
"""


def upgrade() -> None:
    op.execute(INITIAL_SCHEMA)


def downgrade() -> None:
    op.execute(
        "DROP TABLE usage_reports, inventory_reports, borrowing_policy, notifications, "
        "reservations, fines, loans, book_copies, books, users CASCADE"
    )
