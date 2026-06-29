"""Add alternate_phone to leads

Revision ID: 002
Revises: 001
Create Date: 2026-06-29
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("alternate_phone", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("leads", "alternate_phone")
