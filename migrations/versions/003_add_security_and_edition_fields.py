"""Add token invalidation and edition preferences.

Revision ID: 003
Revises: 002
"""

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE users
            ADD COLUMN IF NOT EXISTS token_version INTEGER NOT NULL DEFAULT 0
            CHECK (token_version >= 0);
        ALTER TABLE book_copies
            ADD COLUMN IF NOT EXISTS publication_year INTEGER
            CHECK (publication_year IS NULL OR publication_year BETWEEN 1000 AND 9999),
            ADD COLUMN IF NOT EXISTS edition_number INTEGER
            CHECK (edition_number IS NULL OR edition_number > 0);
        ALTER TABLE reservations
            ADD COLUMN IF NOT EXISTS preferred_publication_year INTEGER
            CHECK (preferred_publication_year IS NULL OR preferred_publication_year BETWEEN 1000 AND 9999),
            ADD COLUMN IF NOT EXISTS preferred_edition_number INTEGER
            CHECK (preferred_edition_number IS NULL OR preferred_edition_number > 0);
        ALTER TABLE book_queue
            ADD COLUMN IF NOT EXISTS preferred_publication_year INTEGER
            CHECK (preferred_publication_year IS NULL OR preferred_publication_year BETWEEN 1000 AND 9999),
            ADD COLUMN IF NOT EXISTS preferred_edition_number INTEGER
            CHECK (preferred_edition_number IS NULL OR preferred_edition_number > 0);
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE book_queue
            DROP COLUMN preferred_edition_number,
            DROP COLUMN preferred_publication_year;
        ALTER TABLE reservations
            DROP COLUMN preferred_edition_number,
            DROP COLUMN preferred_publication_year;
        ALTER TABLE book_copies
            DROP COLUMN edition_number,
            DROP COLUMN publication_year;
        ALTER TABLE users DROP COLUMN token_version;
        """
    )
