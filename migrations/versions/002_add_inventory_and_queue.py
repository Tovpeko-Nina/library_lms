"""Add inventory history, audit trail, and the book waiting queue.

Revision ID: 002
Revises: 001
"""

from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE inventory_log (
            log_id UUID PRIMARY KEY,
            copy_id UUID NOT NULL REFERENCES book_copies(copy_id),
            librarian_id UUID NOT NULL REFERENCES users(user_id),
            old_status TEXT, new_status TEXT NOT NULL, reason TEXT,
            changed_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            changed_by_user UUID REFERENCES users(user_id),
            loan_id UUID REFERENCES loans(loan_id)
        );
        CREATE TABLE audit_log (
            entry_id UUID PRIMARY KEY,
            user_id UUID NOT NULL REFERENCES users(user_id),
            action TEXT NOT NULL, entity_type TEXT NOT NULL, entity_id UUID,
            old_values JSONB, new_values JSONB, ip_address INET,
            user_agent TEXT, timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status TEXT
        );
        CREATE TABLE book_queue (
            queue_id UUID PRIMARY KEY,
            book_id UUID NOT NULL REFERENCES books(book_id),
            user_id UUID NOT NULL REFERENCES users(user_id),
            position INTEGER NOT NULL CHECK (position > 0),
            status VARCHAR(20) NOT NULL
                CHECK (status IN ('WAITING','NOTIFIED','FULFILLED','CANCELLED','EXPIRED')),
            created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            notified_at TIMESTAMPTZ, expiry_date TIMESTAMPTZ
        );
        CREATE UNIQUE INDEX uq_active_queue_user_book
            ON book_queue(book_id, user_id) WHERE status IN ('WAITING','NOTIFIED');
        CREATE INDEX idx_queue_book_status_position
            ON book_queue(book_id, status, position);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE book_queue, audit_log, inventory_log")
