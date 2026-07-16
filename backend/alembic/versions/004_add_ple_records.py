"""add ple_records table

Revision ID: 004
Revises: 003
Create Date: 2026-07-12
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'ple_records',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('mcid', sa.String(100), nullable=False, unique=True),
        sa.Column('lead_id', UUID(as_uuid=True), sa.ForeignKey('leads.id'), nullable=True),
        sa.Column('agent_name', sa.String(255), nullable=True),
        sa.Column('agent_user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('fba_status', sa.String(255), nullable=True),
        sa.Column('fba_live_selection', sa.Integer(), nullable=True),
        sa.Column('sp_status', sa.String(255), nullable=True),
        sa.Column('cp_adoption', sa.String(255), nullable=True),
        sa.Column('narf_cross_launch', sa.String(255), nullable=True),
        sa.Column('buyable_asin', sa.Integer(), nullable=True),
        sa.Column('launch_date', sa.Date(), nullable=True),
        sa.Column('launch_week', sa.String(100), nullable=True),
        sa.Column('fba_launch_date', sa.Date(), nullable=True),
        sa.Column('fba_launch_week', sa.String(100), nullable=True),
        sa.Column('sp_launch_date', sa.Date(), nullable=True),
        sa.Column('sp_launch_week', sa.String(100), nullable=True),
        sa.Column('sp_spend', sa.Numeric(14, 2), nullable=True),
        sa.Column('cp_launch_date', sa.Date(), nullable=True),
        sa.Column('coupon_launch_week', sa.String(100), nullable=True),
        sa.Column('cl_status', sa.String(255), nullable=True),
        sa.Column('total_live_selection', sa.Integer(), nullable=True),
        sa.Column('fba_live_selection_wf', sa.Integer(), nullable=True),
        sa.Column('total_gms', sa.Numeric(14, 2), nullable=True),
        sa.Column('fba_gms', sa.Numeric(14, 2), nullable=True),
        sa.Column('swas', sa.Numeric(14, 2), nullable=True),
        sa.Column('fba_swas', sa.Numeric(14, 2), nullable=True),
        sa.Column('fba_intransit', sa.Integer(), nullable=True),
        sa.Column('launches_uploaded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('mcid_uploaded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_ple_records_mcid', 'ple_records', ['mcid'], unique=True)
    op.create_index('ix_ple_records_agent_user_id', 'ple_records', ['agent_user_id'])


def downgrade() -> None:
    op.drop_index('ix_ple_records_agent_user_id', table_name='ple_records')
    op.drop_index('ix_ple_records_mcid', table_name='ple_records')
    op.drop_table('ple_records')
