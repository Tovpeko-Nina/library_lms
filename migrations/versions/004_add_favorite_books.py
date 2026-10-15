"""Add reader favorite books.

Revision ID: 004
Revises: 003
"""

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE favorite_books (
            user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            book_id UUID NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
            added_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, book_id)
        );
        CREATE INDEX idx_favorite_books_user_added
            ON favorite_books(user_id, added_at DESC);
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE favorite_books")
