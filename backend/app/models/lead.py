import uuid
from datetime import datetime, date
from sqlalchemy import String, Boolean, Integer, Date, DateTime, Text, ForeignKey, func, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core identifiers
    merchant_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    seller_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    mobile_number: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    alternate_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    alternate_phone_2: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Upload metadata
    stage_assigned: Mapped[str | None] = mapped_column(String(255), nullable=True)
    date_of_assignment: Mapped[date | None] = mapped_column(Date, nullable=True)
    week_no: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Stage tracking
    current_activity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("activities.id"), nullable=True, index=True)
    current_stage: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sub_disposition: Mapped[str | None] = mapped_column(String(255), nullable=True)
    final_stage: Mapped[str | None] = mapped_column(String(255), nullable=True)
    week_of_movement: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Assignment
    assigned_fos_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    follow_up_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)

    # Activity entry dates (milestone tracking)
    rnc_entry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    idv_entry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    rtl_entry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    fba_entry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sp_entry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    open_spending_entry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    narf_entry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gsi_entry_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Custom column values (stored as JSON)
    custom_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=dict)

    # Call tracking
    call_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_call_time: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)

    # Self-created (New Registration)
    is_self_created: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    # Archiving
    is_archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    archive_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Source tracking
    source_upload_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("upload_files.id"), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
