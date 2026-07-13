import uuid
from datetime import datetime, date
from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class PleRecord(Base):
    __tablename__ = "ple_records"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mcid: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True)

    agent_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agent_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)

    # Launches-file fields
    fba_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fba_live_selection: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sp_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cp_adoption: Mapped[str | None] = mapped_column(String(255), nullable=True)
    narf_cross_launch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    buyable_asin: Mapped[int | None] = mapped_column(Integer, nullable=True)
    marketplace_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Working-file (MCID detail) fields
    launch_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    launch_week: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fba_launch_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    fba_launch_week: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sp_launch_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    sp_launch_week: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sp_spend: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    cp_launch_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    coupon_launch_week: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cl_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    total_live_selection: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fba_live_selection_wf: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_gms: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    fba_gms: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    swas: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    fba_swas: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    fba_intransit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    launch_yn: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sp_yn: Mapped[str | None] = mapped_column(String(10), nullable=True)
    coupons_yn: Mapped[str | None] = mapped_column(String(10), nullable=True)
    cross_launch_final_stage: Mapped[str | None] = mapped_column(String(10), nullable=True)

    launches_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mcid_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
