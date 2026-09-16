import sqlite3
import uuid
from contextlib import contextmanager
from datetime import date

from .config import DATABASE_PATH

DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_db():
    """Открыть соединение с SQLite и автоматически сделать commit/rollback."""
    db = sqlite3.connect(DATABASE_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")

    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# Структура базы данных соответствует сущностям из ER-диаграммы ТЗ.
SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    login TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    phone TEXT,
    address TEXT,
    role TEXT NOT NULL,
    is_verified INTEGER DEFAULT 0,
    verification_token TEXT,
    registration_date TEXT NOT NULL,
    faculty TEXT,
    department TEXT,
    group_name TEXT,
    graduation_date TEXT,
    is_active INTEGER DEFAULT 1,
    last_login TEXT
);

CREATE INDEX IF NOT EXISTS idx_users_login ON users(login);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_verified ON users(is_verified);

CREATE TABLE IF NOT EXISTS books (
    book_id TEXT PRIMARY KEY,
    isbn TEXT UNIQUE,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    genre TEXT,
    publication_date TEXT,
    publisher TEXT,
    replacement_cost REAL,
    description TEXT,
    pages INTEGER,
    language TEXT DEFAULT 'Русский',
    created_at TEXT NOT NULL,
    updated_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_books_title ON books(title);
CREATE INDEX IF NOT EXISTS idx_books_author ON books(author);
CREATE INDEX IF NOT EXISTS idx_books_genre ON books(genre);

CREATE TABLE IF NOT EXISTS book_copies (
    copy_id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
    branch TEXT NOT NULL,
    status TEXT NOT NULL,
    copy_number INTEGER,
    inventory_number TEXT UNIQUE,
    issue_date TEXT,
    due_date TEXT,
    damage_description TEXT,
    damaged_date TEXT,
    lost_date TEXT,
    lost_by_user_id TEXT REFERENCES users(user_id),
    acquisition_date TEXT NOT NULL,
    price REAL,
    condition TEXT DEFAULT 'NEW'
);

CREATE INDEX IF NOT EXISTS idx_copies_book ON book_copies(book_id);
CREATE INDEX IF NOT EXISTS idx_copies_branch ON book_copies(branch);
CREATE INDEX IF NOT EXISTS idx_copies_status ON book_copies(status);
CREATE INDEX IF NOT EXISTS idx_copies_branch_status
    ON book_copies(branch, status);

CREATE TABLE IF NOT EXISTS loans (
    loan_id TEXT PRIMARY KEY,
    copy_id TEXT NOT NULL REFERENCES book_copies(copy_id),
    user_id TEXT NOT NULL REFERENCES users(user_id),
    librarian_id TEXT NOT NULL REFERENCES users(user_id),
    issue_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    return_date TEXT,
    is_renewed INTEGER DEFAULT 0,
    renewal_count INTEGER DEFAULT 0,
    is_lost INTEGER DEFAULT 0,
    is_damaged INTEGER DEFAULT 0,
    damage_note TEXT,
    status_changed_date TEXT,
    fine_amount REAL DEFAULT 0,
    fine_paid INTEGER DEFAULT 0,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_loans_copy ON loans(copy_id);
CREATE INDEX IF NOT EXISTS idx_loans_user ON loans(user_id);
CREATE INDEX IF NOT EXISTS idx_loans_due ON loans(due_date);
CREATE INDEX IF NOT EXISTS idx_loans_issue ON loans(issue_date);
CREATE INDEX IF NOT EXISTS idx_loans_return ON loans(return_date);

CREATE TABLE IF NOT EXISTS fines (
    fine_id TEXT PRIMARY KEY,
    loan_id TEXT NOT NULL REFERENCES loans(loan_id),
    user_id TEXT NOT NULL REFERENCES users(user_id),
    amount REAL NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    created_date TEXT NOT NULL,
    paid_date TEXT,
    is_paid INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_fines_user ON fines(user_id);
CREATE INDEX IF NOT EXISTS idx_fines_loan ON fines(loan_id);
CREATE INDEX IF NOT EXISTS idx_fines_paid ON fines(is_paid);

CREATE TABLE IF NOT EXISTS reservations (
    reservation_id TEXT PRIMARY KEY,
    copy_id TEXT NOT NULL REFERENCES book_copies(copy_id),
    user_id TEXT NOT NULL REFERENCES users(user_id),
    reservation_date TEXT NOT NULL,
    status TEXT NOT NULL,
    expiry_date TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    notified INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_reservations_copy ON reservations(copy_id);
CREATE INDEX IF NOT EXISTS idx_reservations_user ON reservations(user_id);
CREATE INDEX IF NOT EXISTS idx_reservations_status ON reservations(status);
CREATE INDEX IF NOT EXISTS idx_reservations_expiry ON reservations(expiry_date);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    sent_date TEXT NOT NULL,
    is_read INTEGER DEFAULT 0,
    read_date TEXT,
    link TEXT
);

CREATE INDEX IF NOT EXISTS idx_notifications_user
    ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read
    ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_sent
    ON notifications(sent_date);

CREATE TABLE IF NOT EXISTS borrowing_policy (
    policy_id TEXT PRIMARY KEY,
    max_books_per_user INTEGER DEFAULT 5,
    max_loan_days INTEGER DEFAULT 14,
    daily_fine_rate REAL DEFAULT 10,
    lost_book_fee REAL DEFAULT 0,
    damaged_book_fee REAL DEFAULT 0,
    max_renewals INTEGER DEFAULT 2,
    renewal_days INTEGER DEFAULT 7,
    max_fine_amount REAL DEFAULT 0,
    overdue_grace_period INTEGER DEFAULT 0,
    updated_at TEXT NOT NULL,
    updated_by TEXT
);

CREATE TABLE IF NOT EXISTS inventory_reports (
    report_id TEXT PRIMARY KEY,
    librarian_id TEXT NOT NULL REFERENCES users(user_id),
    generated_date TEXT NOT NULL,
    period_start TEXT,
    period_end TEXT,
    total_books INTEGER NOT NULL,
    available_books INTEGER NOT NULL,
    issued_books INTEGER NOT NULL,
    lost_books INTEGER NOT NULL,
    damaged_books INTEGER NOT NULL,
    reserved_books INTEGER NOT NULL,
    books_by_branch TEXT,
    lost_books_list TEXT,
    damaged_books_list TEXT,
    file_path TEXT
);

CREATE TABLE IF NOT EXISTS usage_reports (
    report_id TEXT PRIMARY KEY,
    librarian_id TEXT NOT NULL REFERENCES users(user_id),
    generated_date TEXT NOT NULL,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    total_loans INTEGER NOT NULL,
    total_readers INTEGER NOT NULL,
    average_loan_duration REAL,
    popularity_ranking TEXT,
    overdue_items TEXT,
    total_fines_collected REAL,
    most_active_readers TEXT,
    file_path TEXT
);

CREATE TABLE IF NOT EXISTS inventory_log (
    log_id TEXT PRIMARY KEY,
    copy_id TEXT NOT NULL REFERENCES book_copies(copy_id),
    librarian_id TEXT NOT NULL REFERENCES users(user_id),
    old_status TEXT,
    new_status TEXT NOT NULL,
    reason TEXT,
    changed_date TEXT NOT NULL,
    changed_by_user TEXT REFERENCES users(user_id),
    loan_id TEXT REFERENCES loans(loan_id)
);

CREATE TABLE IF NOT EXISTS audit_log (
    entry_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(user_id),
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    old_values TEXT,
    new_values TEXT,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TEXT NOT NULL,
    status TEXT
);

CREATE TABLE IF NOT EXISTS book_queue (
    queue_id TEXT PRIMARY KEY,
    book_id TEXT NOT NULL REFERENCES books(book_id),
    user_id TEXT NOT NULL REFERENCES users(user_id),
    position INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    notified_at TEXT,
    expiry_date TEXT
);

CREATE INDEX IF NOT EXISTS idx_queue_book_status
    ON book_queue(book_id, status);
CREATE INDEX IF NOT EXISTS idx_queue_user ON book_queue(user_id);

CREATE VIRTUAL TABLE IF NOT EXISTS books_fts
USING fts5(book_id UNINDEXED, title, author, genre, isbn);
"""


def column_exists(db, table, column):
    """Проверить наличие столбца в таблице."""
    columns = db.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row["name"] == column for row in columns)


def init_db():
    """Создать БД, выполнить миграции и добавить демонстрационные данные."""
    from .security import hash_password

    with get_db() as db:
        db.executescript(SCHEMA)

        # Добавляем поля, которых не было в старой версии БД.
        migrations = {
            "lost_book_fee": "REAL DEFAULT 0",
            "damaged_book_fee": "REAL DEFAULT 0",
            "max_renewals": "INTEGER DEFAULT 2",
            "renewal_days": "INTEGER DEFAULT 7",
            "max_fine_amount": "REAL DEFAULT 0",
            "overdue_grace_period": "INTEGER DEFAULT 0",
        }

        for column, definition in migrations.items():
            if not column_exists(db, "borrowing_policy", column):
                db.execute(
                    f"ALTER TABLE borrowing_policy ADD COLUMN {column} {definition}"
                )

        # Создаём правила выдачи по умолчанию.
        policy_exists = db.execute(
            "SELECT 1 FROM borrowing_policy LIMIT 1"
        ).fetchone()

        if not policy_exists:
            db.execute(
                "INSERT INTO borrowing_policy(policy_id, updated_at) "
                "VALUES(?, datetime('now'))",
                (uuid.uuid4().hex,),
            )

        # Создаём демонстрационного администратора.
        admin_exists = db.execute(
            "SELECT 1 FROM users WHERE login='admin'"
        ).fetchone()

        if not admin_exists:
            db.execute(
                """
                INSERT INTO users (
                    user_id, login, email, password_hash,
                    first_name, last_name, role,
                    is_verified, registration_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                """,
                (
                    uuid.uuid4().hex,
                    "admin",
                    "admin@library.local",
                    hash_password("admin123"),
                    "Администратор",
                    "Системный",
                    "ADMIN",
                    str(date.today()),
                ),
            )

        # Заполняем каталог только при первом запуске.
        if db.execute("SELECT 1 FROM books LIMIT 1").fetchone():
            return

        demo_books = [
            (
                "9785170878561",
                "Мастер и Маргарита",
                "Михаил Булгаков",
                "Роман",
                "1967",
                "АСТ",
            ),
            (
                "9780140449136",
                "Преступление и наказание",
                "Фёдор Достоевский",
                "Классика",
                "1866",
                "Penguin",
            ),
            (
                "9780132350884",
                "Чистый код",
                "Роберт Мартин",
                "Программирование",
                "2008",
                "Prentice Hall",
            ),
        ]

        branches = [
            "AVTOZAVODSKAYA",
            "KORCHAGINA",
            "PRYANISHNIKOVA",
        ]

        for book_index, book in enumerate(demo_books):
            isbn, title, author, genre, year, publisher = book
            book_id = uuid.uuid4().hex

            db.execute(
                """
                INSERT INTO books (
                    book_id, isbn, title, author, genre,
                    publication_date, publisher, description,
                    pages, language, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    book_id,
                    isbn,
                    title,
                    author,
                    genre,
                    year,
                    publisher,
                    "Демонстрационная запись каталога.",
                    300,
                    "Русский",
                ),
            )

            db.execute(
                "INSERT INTO books_fts(book_id,title,author,genre,isbn) "
                "VALUES(?,?,?,?,?)",
                (book_id, title, author, genre, isbn),
            )

            # У каждой демонстрационной книги есть 3 экземпляра.
            for number in range(1, 4):
                copy_id = uuid.uuid4().hex
                branch = branches[(book_index + number - 1) % 3]
                inventory_number = f"INV-{book_index + 1:02d}-{number:03d}"
                price = 1200 + 100 * book_index

                db.execute(
                    """
                    INSERT INTO book_copies (
                        copy_id, book_id, branch, status,
                        copy_number, inventory_number,
                        acquisition_date, condition, price
                    )
                    VALUES (?, ?, ?, 'AVAILABLE', ?, ?, date('now'), 'GOOD', ?)
                    """,
                    (
                        copy_id,
                        book_id,
                        branch,
                        number,
                        inventory_number,
                        price,
                    ),
                )
