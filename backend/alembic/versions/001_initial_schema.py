"""Initial schema — all tables

Revision ID: 001
Revises:
Create Date: 2026-06-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("role", sa.String(10), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "otps",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("otp_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_otps_user_id", "otps", ["user_id"])

    op.create_table(
        "activities",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
        sa.Column("position_order", sa.Integer, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "sub_dispositions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("activity_id", UUID(as_uuid=True), sa.ForeignKey("activities.id"), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_common", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_sub_dispositions_activity_id", "sub_dispositions", ["activity_id"])

    op.create_table(
        "custom_columns",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("data_type", sa.String(20), nullable=False),
        sa.Column("activity_ids", ARRAY(UUID(as_uuid=True)), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "upload_files",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("activity_id", UUID(as_uuid=True), sa.ForeignKey("activities.id"), nullable=True),
        sa.Column("admin_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("s3_key", sa.String(1000), nullable=False),
        sa.Column("upload_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'pending'"),
        sa.Column("total_rows", sa.Integer, nullable=True),
        sa.Column("success_rows", sa.Integer, nullable=True),
        sa.Column("error_rows", sa.Integer, nullable=True),
        sa.Column("task_id", sa.String(255), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "leads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("merchant_id", sa.String(100), unique=True, nullable=False),
        sa.Column("seller_name", sa.String(500), nullable=True),
        sa.Column("mobile_number", sa.String(20), nullable=True),
        sa.Column("email_id", sa.String(255), nullable=True),
        sa.Column("stage_assigned", sa.String(255), nullable=True),
        sa.Column("date_of_assignment", sa.Date, nullable=True),
        sa.Column("week_no", sa.Integer, nullable=True),
        sa.Column("year", sa.Integer, nullable=True),
        sa.Column("current_activity_id", UUID(as_uuid=True), sa.ForeignKey("activities.id"), nullable=True),
        sa.Column("current_stage", sa.String(255), nullable=True),
        sa.Column("sub_disposition", sa.String(255), nullable=True),
        sa.Column("final_stage", sa.String(255), nullable=True),
        sa.Column("week_of_movement", sa.Integer, nullable=True),
        sa.Column("assigned_fos_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("remark", sa.Text, nullable=True),
        sa.Column("follow_up_date", sa.Date, nullable=True),
        sa.Column("rnc_entry_date", sa.Date, nullable=True),
        sa.Column("idv_entry_date", sa.Date, nullable=True),
        sa.Column("rtl_entry_date", sa.Date, nullable=True),
        sa.Column("fba_entry_date", sa.Date, nullable=True),
        sa.Column("sp_entry_date", sa.Date, nullable=True),
        sa.Column("open_spending_entry_date", sa.Date, nullable=True),
        sa.Column("narf_entry_date", sa.Date, nullable=True),
        sa.Column("gsi_entry_date", sa.Date, nullable=True),
        sa.Column("custom_data", JSONB, nullable=True),
        sa.Column("is_archived", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("archive_year", sa.Integer, nullable=True),
        sa.Column("source_upload_id", UUID(as_uuid=True), sa.ForeignKey("upload_files.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_leads_merchant_id", "leads", ["merchant_id"])
    op.create_index("ix_leads_assigned_fos", "leads", ["assigned_fos_id"])
    op.create_index("ix_leads_activity", "leads", ["current_activity_id"])
    op.create_index("ix_leads_follow_up", "leads", ["follow_up_date"])
    op.create_index("ix_leads_archived", "leads", ["is_archived", "archive_year"])
    op.create_index("ix_leads_mobile", "leads", ["mobile_number"])

    op.create_table(
        "upload_errors",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("upload_file_id", UUID(as_uuid=True), sa.ForeignKey("upload_files.id"), nullable=False),
        sa.Column("row_number", sa.Integer, nullable=False),
        sa.Column("merchant_id", sa.String(100), nullable=True),
        sa.Column("error_type", sa.String(100), nullable=False),
        sa.Column("error_detail", sa.Text, nullable=False),
    )
    op.create_index("ix_upload_errors_file_id", "upload_errors", ["upload_file_id"])

    op.create_table(
        "lead_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("old_value", sa.Text, nullable=True),
        sa.Column("new_value", sa.Text, nullable=True),
        sa.Column("performed_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_lead_history_lead_id", "lead_history", ["lead_id"])

    op.create_table(
        "lead_assignments",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=False),
        sa.Column("from_fos_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("to_fos_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("assigned_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_lead_assignments_lead_id", "lead_assignments", ["lead_id"])


def downgrade() -> None:
    op.drop_table("lead_assignments")
    op.drop_table("lead_history")
    op.drop_table("upload_errors")
    op.drop_table("leads")
    op.drop_table("upload_files")
    op.drop_table("custom_columns")
    op.drop_table("sub_dispositions")
    op.drop_table("activities")
    op.drop_table("otps")
    op.drop_table("users")
