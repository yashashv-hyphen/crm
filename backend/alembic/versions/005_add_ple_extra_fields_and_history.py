"""add ple extra fields and history table

Revision ID: 005
Revises: 004
Create Date: 2026-07-13
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('ple_records', sa.Column('marketplace_id', sa.String(255), nullable=True))
    op.add_column('ple_records', sa.Column('launch_yn', sa.String(10), nullable=True))
    op.add_column('ple_records', sa.Column('sp_yn', sa.String(10), nullable=True))
    op.add_column('ple_records', sa.Column('coupons_yn', sa.String(10), nullable=True))
    op.add_column('ple_records', sa.Column('cross_launch_final_stage', sa.String(10), nullable=True))

    op.create_table(
        'ple_record_history',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('ple_record_id', UUID(as_uuid=True), sa.ForeignKey('ple_records.id'), nullable=False),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('performed_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('performed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_ple_record_history_ple_record_id', 'ple_record_history', ['ple_record_id'])


def downgrade() -> None:
    op.drop_index('ix_ple_record_history_ple_record_id', table_name='ple_record_history')
    op.drop_table('ple_record_history')
    op.drop_column('ple_records', 'cross_launch_final_stage')
    op.drop_column('ple_records', 'coupons_yn')
    op.drop_column('ple_records', 'sp_yn')
    op.drop_column('ple_records', 'launch_yn')
    op.drop_column('ple_records', 'marketplace_id')
