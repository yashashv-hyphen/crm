"""add campaigns and campaign_leads tables

Revision ID: 003
Revises: 002
Create Date: 2026-07-03
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'campaigns',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(300), nullable=False),
        sa.Column('created_by', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_table(
        'campaign_leads',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('campaign_id', UUID(as_uuid=True), sa.ForeignKey('campaigns.id'), nullable=False),
        sa.Column('lead_id', UUID(as_uuid=True), sa.ForeignKey('leads.id'), nullable=False),
        sa.Column('merchant_id', sa.String(100), nullable=False),
        sa.Column('event_remark', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_campaign_leads_campaign_id', 'campaign_leads', ['campaign_id'])
    op.create_index('ix_campaign_leads_lead_id', 'campaign_leads', ['lead_id'])


def downgrade() -> None:
    op.drop_table('campaign_leads')
    op.drop_table('campaigns')
