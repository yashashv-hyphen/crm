# PLE MCID Drill-Down & Status Update Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let FOS users click into an individual MCID on the PLE dashboard to see every uploaded field and edit a defined set of status/date fields (audit-logged), and let admins drill from the agent-summary table into an agent's MCIDs and see the same detail plus edit history.

**Architecture:** Five new columns are added to the existing `ple_records` table plus a new `ple_record_history` audit table (mirroring the existing `lead_history` pattern). A `PATCH /api/ple/mcid/{mcid}` endpoint updates editable fields and writes history rows; a `GET /api/ple/mcid/{mcid}/history` endpoint reads them back. The FOS and Admin PLE tabs both gain a shared `PleMcidDrawer` React component (modeled on the existing `LeadDetailDrawer`) for viewing/editing a single MCID.

**Tech Stack:** FastAPI + SQLAlchemy (async) + Alembic on the backend; React + `@tanstack/react-query` + `react-hot-toast` on the frontend. No test framework exists in this repo (no pytest, no JS test runner) — verification is manual, via the running dev stack (`podman-compose`/`docker-compose`, containers already live-reload from bind mounts).

## Global Constraints

- Excel uploads always win: `upsert_ple_record` (`backend/app/utils/ple_parser.py`) must keep silently overwriting any field a re-upload provides a value for — do not add any "don't overwrite if manually edited" logic.
- Editable-by-FOS/admin fields are exactly: `fba_status, sp_status, cl_status, cp_adoption, narf_cross_launch, launch_yn, sp_yn, coupons_yn, cross_launch_final_stage, launch_date, fba_launch_date, sp_launch_date, cp_launch_date`. All other `PleRecord` fields are read-only and must never appear in `PleMcidUpdateRequest`.
- FOS users may only view/edit MCIDs where `PleRecord.agent_user_id == current_user.id`; admins may view/edit any MCID.
- New fields: `marketplace_id`, `launch_yn`, `sp_yn`, `coupons_yn`, `cross_launch_final_stage` — all nullable strings, populated from either uploaded Excel file (see Task 2 for exact header candidates).

---

### Task 1: Database schema — new PleRecord fields + PleRecordHistory audit table

**Files:**
- Modify: `backend/app/models/ple_record.py`
- Create: `backend/app/models/ple_record_history.py`
- Modify: `backend/app/models/__init__.py`
- Create: `backend/alembic/versions/005_add_ple_extra_fields_and_history.py`

**Interfaces:**
- Produces: `PleRecord.marketplace_id: str | None`, `PleRecord.launch_yn: str | None`, `PleRecord.sp_yn: str | None`, `PleRecord.coupons_yn: str | None`, `PleRecord.cross_launch_final_stage: str | None`.
- Produces: `PleRecordHistory` model with columns `id, ple_record_id, field_name, old_value, new_value, performed_by, performed_at`.

- [ ] **Step 1: Add the five new columns to `PleRecord`**

Edit `backend/app/models/ple_record.py` — add these lines right after the existing `buyable_asin` column (still inside the "Launches-file fields" group) and after `fba_intransit` (end of "Working-file" group), matching the file's existing grouping comments:

```python
    # Launches-file fields
    fba_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fba_live_selection: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sp_status: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cp_adoption: Mapped[str | None] = mapped_column(String(255), nullable=True)
    narf_cross_launch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    buyable_asin: Mapped[int | None] = mapped_column(Integer, nullable=True)
    marketplace_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
```

```python
    fba_intransit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    launch_yn: Mapped[str | None] = mapped_column(String(10), nullable=True)
    sp_yn: Mapped[str | None] = mapped_column(String(10), nullable=True)
    coupons_yn: Mapped[str | None] = mapped_column(String(10), nullable=True)
    cross_launch_final_stage: Mapped[str | None] = mapped_column(String(10), nullable=True)
```

- [ ] **Step 2: Create the `PleRecordHistory` model**

Create `backend/app/models/ple_record_history.py`:

```python
import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class PleRecordHistory(Base):
    __tablename__ = "ple_record_history"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ple_record_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("ple_records.id"), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 3: Register the new model**

Edit `backend/app/models/__init__.py`:

```python
from app.models.user import User
from app.models.otp import OTP
from app.models.activity import Activity
from app.models.sub_disposition import SubDisposition
from app.models.custom_column import CustomColumn
from app.models.upload_file import UploadFile
from app.models.upload_error import UploadError
from app.models.lead import Lead
from app.models.lead_history import LeadHistory
from app.models.lead_assignment import LeadAssignment
from app.models.ple_record import PleRecord
from app.models.ple_record_history import PleRecordHistory

__all__ = [
    "User", "OTP", "Activity", "SubDisposition", "CustomColumn",
    "UploadFile", "UploadError", "Lead", "LeadHistory", "LeadAssignment",
    "PleRecord", "PleRecordHistory",
]
```

- [ ] **Step 4: Write the Alembic migration**

Create `backend/alembic/versions/005_add_ple_extra_fields_and_history.py`:

```python
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
```

- [ ] **Step 5: Run the migration against the running dev stack**

Run: `podman exec crm_backend_1 alembic upgrade head`
Expected output ends with: `Running upgrade 004 -> 005, add ple extra fields and history table`

- [ ] **Step 6: Verify the columns and table exist**

Run: `podman exec crm_db_1 psql -U crm_user -d crm_db -c "\d ple_records" | grep -E "marketplace_id|launch_yn|sp_yn|coupons_yn|cross_launch_final_stage"`
Expected: 5 matching lines.

Run: `podman exec crm_db_1 psql -U crm_user -d crm_db -c "\d ple_record_history"`
Expected: table description listing `id, ple_record_id, field_name, old_value, new_value, performed_by, performed_at`.

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/ple_record.py backend/app/models/ple_record_history.py backend/app/models/__init__.py backend/alembic/versions/005_add_ple_extra_fields_and_history.py
git commit -m "Add PLE extra fields and record history table"
```

---

### Task 2: Parser — map the five new fields from Excel

**Files:**
- Modify: `backend/app/utils/ple_parser.py:159-198` (the `LAUNCHES_FIELDS` and `MCID_DETAIL_FIELDS` lists)

**Interfaces:**
- Consumes: `PleRecord` fields from Task 1 (`marketplace_id, launch_yn, sp_yn, coupons_yn, cross_launch_final_stage`).
- Produces: nothing new consumed by later tasks — this only affects what gets populated when admin uploads a file.

- [ ] **Step 1: Add the new candidates to `LAUNCHES_FIELDS`**

In `backend/app/utils/ple_parser.py`, edit the `LAUNCHES_FIELDS` list (currently ends with `("buyable_asin", ["buyable asin", "total live selection"])`) to add:

```python
LAUNCHES_FIELDS: list[tuple[str, list[str]]] = [
    ("mcid", ["merchant customer id", "mcid", "merchant id"]),
    ("agent_name", ["bd am", "opportunity owner", "fba opportunity owner", "gse name", "gse", "agent", "owner"]),
    ("marketplace_id", ["marketplace id", "marketplace"]),
    ("fba_live_selection", ["fba live selection", "fba live seletion", "fba ba t4w"]),
    ("fba_status", ["fba status", "is fba launched", "is fba active", "fba active", "is fba"]),
    ("sp_status", ["sp status", "is sp active", "is sp"]),
    ("cp_adoption", ["any deal adoption", "deal adoption cp", "coupon adoption", "is coupon active", "is coupon granted", "is cp"]),  # priority order: adoption-worded first, then "active", then "granted"
    ("cross_launch_final_stage", ["cross launch final stage", "final stage"]),  # must precede narf_cross_launch: "cross launch" substring-matches "cross launch final stage" headers too
    ("narf_cross_launch", ["narf cross launch", "narf", "is perfect launched", "cross launch"]),
    ("buyable_asin", ["buyable asin", "total live selection"]),
    ("launch_yn", ["launch yes no", "launch y n", "is launched"]),
    ("sp_yn", ["sp yes no", "sp y n"]),
    ("coupons_yn", ["coupons yes no", "coupons y n", "coupons"]),
]
```

**Correction (post-implementation, verified by task review):** the original version of this block placed `cross_launch_final_stage` last, which fails this task's own Step 3 acceptance test — `narf_cross_launch`'s `"cross launch"` candidate substring-matches a `"cross launch final stage"` header first since `map_columns` resolves fields in list order. `cross_launch_final_stage` must come before `narf_cross_launch`, as reflected above.

- [ ] **Step 2: Add the same new candidates to `MCID_DETAIL_FIELDS`**

Edit the `MCID_DETAIL_FIELDS` list to add the same five fields (this file's rows don't have `marketplace_id` per the design's "Launches file only" answer, but `launch_yn`/`sp_yn`/`coupons_yn`/`cross_launch_final_stage` should be detected here too since the design says "auto-detect in both"):

```python
MCID_DETAIL_FIELDS: list[tuple[str, list[str]]] = [
    ("mcid", ["mcid"]),
    ("agent_name", ["gse name", "gse"]),
    ("fba_launch_date", ["fba launch date"]),
    ("fba_launch_week", ["fba launch week"]),
    ("sp_launch_date", ["sp launch date"]),
    ("sp_launch_week", ["sp launch week"]),
    ("sp_spend", ["sp spend"]),
    ("cp_launch_date", ["cp launch date", "cp launch"]),
    ("coupon_launch_week", ["coupon launch week"]),
    ("cl_status", ["cross launch rf", "narf cross launch", "cl"]),
    ("fba_live_selection_wf", ["fba live selection", "fba live seletion"]),
    ("total_live_selection", ["total live selection", "buyable asin"]),
    ("fba_gms", ["fba gms"]),
    ("total_gms", ["total gms"]),
    ("fba_swas", ["fba swas"]),
    ("swas", ["swas"]),
    ("fba_intransit", ["fba intransit", "fba in transit"]),
    ("launch_date", ["launch date"]),
    ("launch_week", ["launch week"]),
    ("launch_yn", ["launch yes no", "launch y n", "is launched"]),
    ("sp_yn", ["sp yes no", "sp y n"]),
    ("coupons_yn", ["coupons yes no", "coupons y n", "coupons"]),
    ("cross_launch_final_stage", ["cross launch final stage", "final stage"]),
]
```

Note: `_FIELD_PARSERS` needs no changes — none of the five new fields are in that dict, so `parse_field` falls through to the default `parse_str`, which is correct (they're all plain text/Yes-No values).

- [ ] **Step 3: Verify column mapping picks up a synthetic header**

Run this ad-hoc check inside the backend container to confirm `map_columns` resolves the new fields without colliding with existing ones:

```bash
podman exec crm_backend_1 python3 -c "
from app.utils.ple_parser import map_columns, LAUNCHES_FIELDS
headers = ['mcid', 'agent', 'marketplace id', 'fba status', 'launch yes no', 'sp yes no', 'coupons', 'cross launch final stage']
normed = [h.lower() for h in headers]
mapping = map_columns(normed, LAUNCHES_FIELDS)
assert mapping['marketplace_id'] == 2, mapping
assert mapping['fba_status'] == 3, mapping
assert mapping['launch_yn'] == 4, mapping
assert mapping['sp_yn'] == 5, mapping
assert mapping['coupons_yn'] == 6, mapping
assert mapping['cross_launch_final_stage'] == 7, mapping
print('OK', mapping)
"
```

Expected: prints `OK {...}` with no `AssertionError`.

- [ ] **Step 4: Commit**

```bash
git add backend/app/utils/ple_parser.py
git commit -m "Map new PLE fields (marketplace_id, launch/SP/coupons Y-N, cross launch final stage) from Excel uploads"
```

---

### Task 3: Schemas — extend PLE Pydantic models

**Files:**
- Modify: `backend/app/schemas/ple.py`

**Interfaces:**
- Consumes: `PleRecord` fields from Task 1.
- Produces: `PleMcidDetailRow` (extended), `PleMcidUpdateRequest` (new), `PleRecordHistoryEntry` (new), `PleAgentSummaryRow.agent_user_id` (new field) — all consumed by Task 4 (service) and Task 5 (router).

- [ ] **Step 1: Rewrite `backend/app/schemas/ple.py`**

```python
import uuid
from datetime import date, datetime
from pydantic import BaseModel


class PleAgentSummaryRow(BaseModel):
    agent: str
    agent_user_id: uuid.UUID | None
    num_launches: int
    fba_status_count: int
    fba_live_selection: int
    sp_status_count: int
    cp_adoption_count: int
    narf_cross_launch_count: int
    buyable_asin: int


class PleMcidDetailRow(BaseModel):
    id: uuid.UUID
    mcid: str
    agent_name: str | None
    agent_user_id: uuid.UUID | None
    marketplace_id: str | None

    # Launches-file fields
    fba_status: str | None
    fba_live_selection: int | None
    sp_status: str | None
    cp_adoption: str | None
    narf_cross_launch: str | None
    buyable_asin: int | None
    launch_yn: str | None
    sp_yn: str | None
    coupons_yn: str | None
    cross_launch_final_stage: str | None

    # Working-file (MCID detail) fields
    launch_date: date | None
    launch_week: str | None
    fba_launch_date: date | None
    fba_launch_week: str | None
    sp_launch_date: date | None
    sp_launch_week: str | None
    sp_spend: float | None
    cp_launch_date: date | None
    coupon_launch_week: str | None
    cl_status: str | None
    total_live_selection: int | None
    fba_live_selection_wf: int | None
    total_gms: float | None
    fba_gms: float | None
    swas: float | None
    fba_swas: float | None
    fba_intransit: int | None

    lead_id: uuid.UUID | None
    launches_uploaded_at: datetime | None
    mcid_uploaded_at: datetime | None
    updated_at: datetime

    model_config = {"from_attributes": True}


class PleMcidUpdateRequest(BaseModel):
    fba_status: str | None = None
    sp_status: str | None = None
    cl_status: str | None = None
    cp_adoption: str | None = None
    narf_cross_launch: str | None = None
    launch_yn: str | None = None
    sp_yn: str | None = None
    coupons_yn: str | None = None
    cross_launch_final_stage: str | None = None
    launch_date: date | None = None
    fba_launch_date: date | None = None
    sp_launch_date: date | None = None
    cp_launch_date: date | None = None


class PleRecordHistoryEntry(BaseModel):
    field_name: str
    old_value: str | None
    new_value: str | None
    performed_by_name: str | None
    performed_at: datetime

    model_config = {"from_attributes": True}
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas/ple.py
git commit -m "Extend PLE schemas with new fields, update request, and history entry"
```

---

### Task 4: Service layer — update, history, and agent-filtered queries

**Files:**
- Modify: `backend/app/services/ple_service.py`

**Interfaces:**
- Consumes: `PleMcidUpdateRequest`, `PleRecordHistoryEntry` (Task 3), `PleRecordHistory` model (Task 1).
- Produces: `get_mcid_record(db, mcid, current_user) -> PleRecord` (raises `HTTPException` 404/403), `update_mcid_record(db, mcid, updates, current_user) -> PleMcidDetailRow`, `get_mcid_history(db, mcid, current_user) -> list[PleRecordHistoryEntry]` — all consumed by Task 5 (router).

- [ ] **Step 1: Rewrite `backend/app/services/ple_service.py`**

```python
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from app.models.ple_record import PleRecord
from app.models.ple_record_history import PleRecordHistory
from app.models.user import User
from app.schemas.ple import (
    PleAgentSummaryRow, PleMcidDetailRow, PleMcidUpdateRequest, PleRecordHistoryEntry,
)

MAX_MCID_ROWS = 5000


async def get_agent_summary(db: AsyncSession) -> list[PleAgentSummaryRow]:
    agent_label = func.coalesce(User.full_name, PleRecord.agent_name, "Unassigned")
    result = await db.execute(
        select(
            agent_label.label("agent"),
            PleRecord.agent_user_id.label("agent_user_id"),
            func.count(PleRecord.id).label("num_launches"),
            func.sum(case((PleRecord.fba_status.isnot(None), 1), else_=0)).label("fba_status_count"),
            func.coalesce(func.sum(PleRecord.fba_live_selection), 0).label("fba_live_selection"),
            func.sum(case((PleRecord.sp_status.isnot(None), 1), else_=0)).label("sp_status_count"),
            func.sum(case((PleRecord.cp_adoption.isnot(None), 1), else_=0)).label("cp_adoption_count"),
            func.sum(case((PleRecord.narf_cross_launch.isnot(None), 1), else_=0)).label("narf_cross_launch_count"),
            func.coalesce(func.sum(PleRecord.buyable_asin), 0).label("buyable_asin"),
        )
        .select_from(PleRecord)
        .outerjoin(User, User.id == PleRecord.agent_user_id)
        .group_by(agent_label, PleRecord.agent_user_id)
        .order_by(func.count(PleRecord.id).desc())
    )
    return [PleAgentSummaryRow(**row._mapping) for row in result.all()]


async def get_mcid_detail(db: AsyncSession, agent_user_id: uuid.UUID | None = None) -> list[PleMcidDetailRow]:
    query = select(PleRecord).order_by(PleRecord.mcid).limit(MAX_MCID_ROWS)
    if agent_user_id is not None:
        query = query.where(PleRecord.agent_user_id == agent_user_id)
    result = await db.execute(query)
    return [PleMcidDetailRow.model_validate(rec) for rec in result.scalars().all()]


_EDITABLE_FIELDS = {
    "fba_status", "sp_status", "cl_status", "cp_adoption", "narf_cross_launch",
    "launch_yn", "sp_yn", "coupons_yn", "cross_launch_final_stage",
    "launch_date", "fba_launch_date", "sp_launch_date", "cp_launch_date",
}


async def get_mcid_record(db: AsyncSession, mcid: str, current_user: User) -> PleRecord:
    result = await db.execute(select(PleRecord).where(PleRecord.mcid == mcid))
    rec = result.scalar_one_or_none()
    if rec is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="MCID not found")
    if current_user.role == "fos" and rec.agent_user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your MCID")
    return rec


async def update_mcid_record(
    db: AsyncSession, mcid: str, updates: PleMcidUpdateRequest, current_user: User,
) -> PleMcidDetailRow:
    rec = await get_mcid_record(db, mcid, current_user)

    update_data = updates.model_dump(exclude_unset=True)
    for field, new_value in update_data.items():
        assert field in _EDITABLE_FIELDS, f"{field} is not editable"
        old_value = getattr(rec, field, None)
        if old_value != new_value:
            db.add(PleRecordHistory(
                id=uuid.uuid4(),
                ple_record_id=rec.id,
                field_name=field,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(new_value) if new_value is not None else None,
                performed_by=current_user.id,
            ))
            setattr(rec, field, new_value)

    rec.updated_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(rec)
    return PleMcidDetailRow.model_validate(rec)


async def get_mcid_history(db: AsyncSession, mcid: str, current_user: User) -> list[PleRecordHistoryEntry]:
    rec = await get_mcid_record(db, mcid, current_user)
    result = await db.execute(
        select(PleRecordHistory, User.full_name)
        .join(User, User.id == PleRecordHistory.performed_by)
        .where(PleRecordHistory.ple_record_id == rec.id)
        .order_by(PleRecordHistory.performed_at.asc())
    )
    return [
        PleRecordHistoryEntry(
            field_name=h.field_name,
            old_value=h.old_value,
            new_value=h.new_value,
            performed_by_name=name,
            performed_at=h.performed_at,
        )
        for h, name in result.all()
    ]
```

Note: the `assert field in _EDITABLE_FIELDS` is a defense against future schema drift (someone adding a field to `PleMcidUpdateRequest` without adding it here) — it can never fire from a valid `PleMcidUpdateRequest` instance today since the schema only declares editable fields, but it stays as a guard.

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/ple_service.py
git commit -m "Add PLE MCID update and history service functions"
```

---

### Task 5: Router — PATCH and history endpoints, agent_user_id filter

**Files:**
- Modify: `backend/app/routers/ple.py`

**Interfaces:**
- Consumes: `ple_service.get_mcid_detail`, `ple_service.update_mcid_record`, `ple_service.get_mcid_history` (Task 4); `PleMcidUpdateRequest`, `PleRecordHistoryEntry` (Task 3).
- Produces: `PATCH /api/ple/mcid/{mcid}`, `GET /api/ple/mcid/{mcid}/history`, `GET /api/ple/mcid-detail?agent_user_id=` — consumed by Task 6 (frontend api).

- [ ] **Step 1: Add the imports and new endpoints**

Edit `backend/app/routers/ple.py` — change the schema import line and the `mcid_detail` endpoint, and add two new endpoints after it:

```python
from app.schemas.ple import PleAgentSummaryRow, PleMcidDetailRow, PleMcidUpdateRequest
```

Replace the existing `mcid_detail` endpoint:

```python
@router.get("/mcid-detail", response_model=list[PleMcidDetailRow])
async def mcid_detail(
    agent_user_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # FOS users only see their own MCIDs; admins see everything, or one agent via ?agent_user_id=.
    filter_agent_user_id = current_user.id if current_user.role == "fos" else agent_user_id
    return await ple_service.get_mcid_detail(db, agent_user_id=filter_agent_user_id)


@router.patch("/mcid/{mcid}", response_model=PleMcidDetailRow)
async def update_mcid(
    mcid: str,
    body: PleMcidUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await ple_service.update_mcid_record(db, mcid, body, current_user)
    await db.commit()
    return result


@router.get("/mcid/{mcid}/history")
async def mcid_history(
    mcid: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ple_service.get_mcid_history(db, mcid, current_user)
```

- [ ] **Step 2: Verify the backend reloads cleanly**

Run: `podman logs --tail 15 crm_backend_1 2>&1 | grep -v level=`
Expected: `Application startup complete.` with no traceback.

- [ ] **Step 3: Manually exercise the new endpoints**

First get a valid session cookie by logging in through the running app (http://localhost:8080) as an admin, then in the browser devtools console or via `document.cookie` copy the `access_token` value, or simpler — run this from inside the backend container using the app's own DB session to sanity check the service layer directly:

```bash
podman exec crm_backend_1 python3 -c "
import asyncio
from app.database import AsyncSessionLocal
from app.services import ple_service
from sqlalchemy import select
from app.models.user import User

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.role == 'admin').limit(1))
        admin = result.scalar_one_or_none()
        if not admin:
            print('No admin user in DB, skipping'); return
        rows = await ple_service.get_mcid_detail(db)
        print('mcid_detail rows:', len(rows))
        if rows:
            mcid = rows[0].mcid
            from app.schemas.ple import PleMcidUpdateRequest
            updated = await ple_service.update_mcid_record(db, mcid, PleMcidUpdateRequest(fba_status='Test Status'), admin)
            await db.commit()
            print('updated fba_status ->', updated.fba_status)
            history = await ple_service.get_mcid_history(db, mcid, admin)
            print('history entries:', len(history), history[-1].field_name if history else None)

asyncio.run(main())
"
```

Expected: prints `mcid_detail rows: N`, `updated fba_status -> Test Status`, and `history entries: M fba_status` with no traceback. (If there are zero PLE records yet because no Excel has been uploaded in this environment, this step will print `mcid_detail rows: 0` and skip the update/history assertions — that's fine, it still proves the query executes; do a full check after Task 9's manual verification once real data exists.)

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/ple.py
git commit -m "Add PLE MCID PATCH and history endpoints, agent_user_id filter on mcid-detail"
```

---

### Task 6: Frontend API client

**Files:**
- Modify: `frontend/src/api/ple.js`

**Interfaces:**
- Produces: `getPleMcidDetail(params)`, `getPleMcidHistory(mcid)`, `updatePleMcid(mcid, updates)` — consumed by Task 7, 8, 9.

- [ ] **Step 1: Rewrite `frontend/src/api/ple.js`**

```javascript
import api from './axios'

export const uploadPleLaunches = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/ple/upload/launches', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const uploadPleMcidDetail = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/ple/upload/mcid-detail', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const getPleAgentSummary = () => api.get('/ple/agent-summary')

export const getPleMcidDetail = (params) => api.get('/ple/mcid-detail', { params })

export const getPleMcidHistory = (mcid) => api.get(`/ple/mcid/${mcid}/history`)

export const updatePleMcid = (mcid, updates) => api.patch(`/ple/mcid/${mcid}`, updates)
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/ple.js
git commit -m "Add PLE MCID history and update API client functions"
```

---

### Task 7: Frontend — shared `PleMcidDrawer` component

**Files:**
- Create: `frontend/src/components/PleMcidDrawer.jsx`

**Interfaces:**
- Consumes: `getPleMcidDetail, getPleMcidHistory, updatePleMcid` (Task 6). Fields on a `PleMcidDetailRow`-shaped object: `mcid, agent_name, marketplace_id, fba_status, fba_live_selection, sp_status, cp_adoption, narf_cross_launch, buyable_asin, launch_yn, sp_yn, coupons_yn, cross_launch_final_stage, launch_date, launch_week, fba_launch_date, fba_launch_week, sp_launch_date, sp_launch_week, sp_spend, cp_launch_date, coupon_launch_week, cl_status, total_live_selection, fba_live_selection_wf, total_gms, fba_gms, swas, fba_swas, fba_intransit`.
- Produces: `export default function PleMcidDrawer({ mcid, onClose })` — consumed by Task 8 (FOS dashboard) and Task 9 (Admin dashboard).

- [ ] **Step 1: Create the component**

Create `frontend/src/components/PleMcidDrawer.jsx`:

```jsx
import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getPleMcidDetail, getPleMcidHistory, updatePleMcid } from '../api/ple'
import toast from 'react-hot-toast'

function DetailRow({ label, value }) {
  if (!value && value !== 0) return null
  return (
    <div className="flex gap-2 py-1.5 border-b border-gray-50 last:border-0">
      <span className="text-xs text-gray-500 w-40 shrink-0">{label}</span>
      <span className="text-xs text-gray-800 font-medium break-all">{value}</span>
    </div>
  )
}

const PENDING_CHECKS = [
  { label: 'FBA Status', field: 'fba_status' },
  { label: 'SP Status', field: 'sp_status' },
  { label: 'CL Status', field: 'cl_status' },
  { label: 'CP Adoption', field: 'cp_adoption' },
  { label: 'Cross Launch', field: 'narf_cross_launch' },
  { label: 'Cross Launch Final Stage', field: 'cross_launch_final_stage' },
  { label: 'Launch Y/N', field: 'launch_yn' },
  { label: 'SP Y/N', field: 'sp_yn' },
  { label: 'Coupons Y/N', field: 'coupons_yn' },
  { label: 'Launch Date', field: 'launch_date' },
  { label: 'FBA Launch Date', field: 'fba_launch_date' },
  { label: 'SP Launch Date', field: 'sp_launch_date' },
  { label: 'CP Launch Date', field: 'cp_launch_date' },
]

function PendingChecklist({ record }) {
  return (
    <div className="grid grid-cols-1 gap-1 mb-4 bg-gray-50 rounded-lg p-3">
      {PENDING_CHECKS.map(({ label, field }) => {
        const done = !!record[field]
        return (
          <div key={field} className="flex items-center gap-2 text-xs">
            <span className={done ? 'text-green-600' : 'text-red-500'}>{done ? '✔' : '✖'}</span>
            <span className="text-gray-700">{label}</span>
          </div>
        )
      })}
    </div>
  )
}

function HistoryTab({ mcid }) {
  const { data: history, isLoading } = useQuery({
    queryKey: ['ple-mcid-history', mcid],
    queryFn: () => getPleMcidHistory(mcid).then((r) => r.data),
  })

  if (isLoading) return <p className="text-sm text-gray-400 py-4 text-center">Loading history…</p>
  if (!history?.length) return <p className="text-sm text-gray-400 py-4 text-center">No changes recorded yet.</p>

  return (
    <div className="space-y-2 mt-2">
      {history.map((entry, i) => (
        <div key={i} className="bg-gray-50 rounded-lg px-3 py-2 text-xs">
          <div className="flex items-center justify-between mb-1">
            <span className="font-semibold text-gray-700">{entry.field_name}</span>
            <span className="text-gray-400">{new Date(entry.performed_at).toLocaleString()}</span>
          </div>
          <div className="text-gray-500">
            {entry.performed_by_name && <span className="font-medium text-gray-600">{entry.performed_by_name} · </span>}
            {entry.old_value != null && (
              <span><span className="line-through text-red-400">{entry.old_value}</span> → </span>
            )}
            <span className="text-green-700 font-medium">{entry.new_value ?? '—'}</span>
          </div>
        </div>
      ))}
    </div>
  )
}

const EDITABLE_STATUS_FIELDS = [
  { label: 'FBA Status', field: 'fba_status' },
  { label: 'SP Status', field: 'sp_status' },
  { label: 'CL Status', field: 'cl_status' },
  { label: 'CP Adoption', field: 'cp_adoption' },
  { label: 'Cross Launch', field: 'narf_cross_launch' },
  { label: 'Cross Launch Final Stage', field: 'cross_launch_final_stage' },
  { label: 'Launch Y/N', field: 'launch_yn' },
  { label: 'SP Y/N', field: 'sp_yn' },
  { label: 'Coupons Y/N', field: 'coupons_yn' },
]

const EDITABLE_DATE_FIELDS = [
  { label: 'Launch Date', field: 'launch_date' },
  { label: 'FBA Launch Date', field: 'fba_launch_date' },
  { label: 'SP Launch Date', field: 'sp_launch_date' },
  { label: 'CP Launch Date', field: 'cp_launch_date' },
]

export default function PleMcidDrawer({ mcid, onClose }) {
  const [tab, setTab] = useState('details')
  const [form, setForm] = useState({})
  const queryClient = useQueryClient()

  const { data: records } = useQuery({
    queryKey: ['ple-mcid-record', mcid],
    queryFn: () => getPleMcidDetail({}).then((r) => r.data),
  })
  const record = records?.find((r) => r.mcid === mcid)

  useEffect(() => {
    if (record) {
      const next = {}
      for (const { field } of [...EDITABLE_STATUS_FIELDS, ...EDITABLE_DATE_FIELDS]) {
        next[field] = record[field] || ''
      }
      setForm(next)
    }
  }, [record?.mcid])

  const mutation = useMutation({
    mutationFn: (updates) => updatePleMcid(mcid, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ple-mcid-record', mcid] })
      queryClient.invalidateQueries({ queryKey: ['ple-mcid-history', mcid] })
      queryClient.invalidateQueries({ queryKey: ['ple-mcid-detail'] })
      queryClient.invalidateQueries({ queryKey: ['ple-agent-summary'] })
      toast.success('Saved')
    },
    onError: () => toast.error('Save failed'),
  })

  const handleSave = () => {
    if (!record) return
    const updates = {}
    for (const { field } of [...EDITABLE_STATUS_FIELDS, ...EDITABLE_DATE_FIELDS]) {
      if ((form[field] || '') !== (record[field] || '')) updates[field] = form[field] || null
    }
    if (!Object.keys(updates).length) { toast('No changes to save', { icon: 'ℹ️' }); return }
    mutation.mutate(updates)
  }

  if (!record) {
    return (
      <div className="fixed inset-0 z-50 flex">
        <div className="flex-1 bg-black/30" onClick={onClose} />
        <div className="w-full max-w-lg bg-white shadow-2xl flex items-center justify-center h-full">
          <span className="text-gray-400 text-sm">Loading…</span>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black/30" onClick={onClose} />
      <div className="w-full max-w-lg bg-white shadow-2xl flex flex-col h-full overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 shrink-0">
          <div>
            <p className="text-xs text-gray-500">MCID</p>
            <p className="font-mono text-sm font-bold text-gray-800">{record.mcid}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl leading-none">✕</button>
        </div>

        <div className="flex border-b border-gray-100 shrink-0">
          {['details', 'update', 'history'].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-5 py-2.5 text-sm font-medium capitalize transition-colors ${
                tab === t ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4">
          {tab === 'details' && (
            <div>
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Pending Checklist</p>
              <PendingChecklist record={record} />

              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Identity</p>
              <DetailRow label="Agent" value={record.agent_name} />
              <DetailRow label="Marketplace ID" value={record.marketplace_id} />

              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-3 mb-1">Status Fields</p>
              <DetailRow label="FBA Status" value={record.fba_status} />
              <DetailRow label="SP Status" value={record.sp_status} />
              <DetailRow label="CL Status" value={record.cl_status} />
              <DetailRow label="CP Adoption" value={record.cp_adoption} />
              <DetailRow label="Cross Launch" value={record.narf_cross_launch} />
              <DetailRow label="Cross Launch Final Stage" value={record.cross_launch_final_stage} />
              <DetailRow label="Launch Y/N" value={record.launch_yn} />
              <DetailRow label="SP Y/N" value={record.sp_yn} />
              <DetailRow label="Coupons Y/N" value={record.coupons_yn} />

              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-3 mb-1">Dates</p>
              <DetailRow label="Launch Date" value={record.launch_date} />
              <DetailRow label="Launch Week" value={record.launch_week} />
              <DetailRow label="FBA Launch Date" value={record.fba_launch_date} />
              <DetailRow label="FBA Launch Week" value={record.fba_launch_week} />
              <DetailRow label="SP Launch Date" value={record.sp_launch_date} />
              <DetailRow label="SP Launch Week" value={record.sp_launch_week} />
              <DetailRow label="CP Launch Date" value={record.cp_launch_date} />
              <DetailRow label="Coupon Launch Week" value={record.coupon_launch_week} />

              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mt-3 mb-1">Metrics</p>
              <DetailRow label="SP Spend" value={record.sp_spend?.toLocaleString()} />
              <DetailRow label="Total Live Selection" value={record.total_live_selection?.toLocaleString()} />
              <DetailRow label="FBA Live Selection" value={record.fba_live_selection?.toLocaleString()} />
              <DetailRow label="FBA Live Selection (WF)" value={record.fba_live_selection_wf?.toLocaleString()} />
              <DetailRow label="Buyable ASIN" value={record.buyable_asin?.toLocaleString()} />
              <DetailRow label="Total GMS" value={record.total_gms?.toLocaleString()} />
              <DetailRow label="FBA GMS" value={record.fba_gms?.toLocaleString()} />
              <DetailRow label="SWAS" value={record.swas?.toLocaleString()} />
              <DetailRow label="FBA SWAS" value={record.fba_swas?.toLocaleString()} />
              <DetailRow label="FBA Intransit" value={record.fba_intransit?.toLocaleString()} />
            </div>
          )}

          {tab === 'update' && (
            <div className="space-y-4">
              {EDITABLE_STATUS_FIELDS.map(({ label, field }) => (
                <div key={field}>
                  <label className="block text-xs text-gray-500 mb-1">{label}</label>
                  <input
                    type="text"
                    value={form[field] || ''}
                    onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              ))}
              {EDITABLE_DATE_FIELDS.map(({ label, field }) => (
                <div key={field}>
                  <label className="block text-xs text-gray-500 mb-1">{label}</label>
                  <input
                    type="date"
                    value={form[field] || ''}
                    onChange={(e) => setForm((f) => ({ ...f, [field]: e.target.value }))}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              ))}
              <button
                onClick={handleSave}
                disabled={mutation.isPending}
                className="w-full bg-blue-600 text-white rounded-lg py-2.5 text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
              >
                {mutation.isPending ? 'Saving…' : 'Save Changes'}
              </button>
            </div>
          )}

          {tab === 'history' && <HistoryTab mcid={mcid} />}
        </div>
      </div>
    </div>
  )
}
```

Note: `getPleMcidDetail({})` re-fetches the caller's full accessible list and finds the matching row client-side, rather than adding a `GET /ple/mcid/{mcid}` single-record endpoint — this keeps the backend surface smaller since the list endpoint already applies the correct FOS/admin visibility filtering, and the lists are capped at 5000 rows (existing `MAX_MCID_ROWS`) so this is cheap. The drawer is opened from a page that already has the list loaded in the query cache (same `['ple-mcid-detail']` key isn't reused here on purpose — see Task 8/9 which pass `agent_user_id` — so this query intentionally issues its own unfiltered-for-FOS/one-agent-for-admin fetch scoped by whatever the current user is allowed to see).

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/PleMcidDrawer.jsx
git commit -m "Add PleMcidDrawer component for MCID detail view and status editing"
```

---

### Task 8: Frontend — wire up FOS PLE tab

**Files:**
- Modify: `frontend/src/pages/FosDashboard.jsx`

**Interfaces:**
- Consumes: `PleMcidDrawer` (Task 7).

- [ ] **Step 1: Add new columns and click-through to `PleTab`**

Replace the `PleTab` function in `frontend/src/pages/FosDashboard.jsx` (currently at the top of the file, from `function PleTab()` through its closing `}`) with:

```jsx
function PleTab() {
  const [selectedMcid, setSelectedMcid] = useState(null)
  const { data: mcidDetail, isLoading } = useQuery({
    queryKey: ['ple-mcid-detail'],
    queryFn: () => getPleMcidDetail().then((r) => r.data),
  })

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {selectedMcid && <PleMcidDrawer mcid={selectedMcid} onClose={() => setSelectedMcid(null)} />}
      <div className="px-5 py-4 border-b border-gray-100">
        <h2 className="font-semibold text-gray-700">MCID-wise Breakdown</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
            <tr>
              <th className="px-5 py-3 text-left">MCID</th>
              <th className="px-3 py-3 text-left">Marketplace ID</th>
              <th className="px-3 py-3 text-left">FBA Status</th>
              <th className="px-3 py-3 text-left">SP Status</th>
              <th className="px-3 py-3 text-left">CP Adoption</th>
              <th className="px-3 py-3 text-left">Cross Launch</th>
              <th className="px-3 py-3 text-left">Cross Launch Final Stage</th>
              <th className="px-3 py-3 text-left">Launch Y/N</th>
              <th className="px-3 py-3 text-left">SP Y/N</th>
              <th className="px-3 py-3 text-left">Coupons Y/N</th>
              <th className="px-3 py-3 text-left">Launch Date</th>
              <th className="px-3 py-3 text-left">Launch Week</th>
              <th className="px-3 py-3 text-left">FBA Launch Date</th>
              <th className="px-3 py-3 text-left">FBA Launch Week</th>
              <th className="px-3 py-3 text-left">SP Launch Date</th>
              <th className="px-3 py-3 text-left">SP Launch Week</th>
              <th className="px-3 py-3 text-right">SP Spend</th>
              <th className="px-3 py-3 text-left">CP Launch Date</th>
              <th className="px-3 py-3 text-left">Coupon Launch Week</th>
              <th className="px-3 py-3 text-left">CL</th>
              <th className="px-3 py-3 text-right">Total Live Selection</th>
              <th className="px-3 py-3 text-right">FBA Live Selection</th>
              <th className="px-3 py-3 text-right">Buyable ASIN</th>
              <th className="px-3 py-3 text-right">Total GMS</th>
              <th className="px-3 py-3 text-right">FBA GMS</th>
              <th className="px-3 py-3 text-right">SWAS</th>
              <th className="px-3 py-3 text-right">FBA SWAS</th>
              <th className="px-3 py-3 text-right">FBA Intransit</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr><td colSpan={27} className="px-5 py-6 text-center text-gray-400">Loading...</td></tr>
            ) : !mcidDetail?.length ? (
              <tr><td colSpan={27} className="px-5 py-6 text-center text-gray-400">No PLE data for your MCIDs yet</td></tr>
            ) : (
              mcidDetail.map((row) => (
                <tr key={row.mcid} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedMcid(row.mcid)}>
                  <td className="px-5 py-3 font-mono text-blue-600 hover:underline">{row.mcid}</td>
                  <td className="px-3 py-3">{row.marketplace_id || '—'}</td>
                  <td className="px-3 py-3">{row.fba_status || '—'}</td>
                  <td className="px-3 py-3">{row.sp_status || '—'}</td>
                  <td className="px-3 py-3">{row.cp_adoption || '—'}</td>
                  <td className="px-3 py-3">{row.narf_cross_launch || '—'}</td>
                  <td className="px-3 py-3">{row.cross_launch_final_stage || '—'}</td>
                  <td className="px-3 py-3">{row.launch_yn || '—'}</td>
                  <td className="px-3 py-3">{row.sp_yn || '—'}</td>
                  <td className="px-3 py-3">{row.coupons_yn || '—'}</td>
                  <td className="px-3 py-3">{row.launch_date || '—'}</td>
                  <td className="px-3 py-3">{row.launch_week || '—'}</td>
                  <td className="px-3 py-3">{row.fba_launch_date || '—'}</td>
                  <td className="px-3 py-3">{row.fba_launch_week || '—'}</td>
                  <td className="px-3 py-3">{row.sp_launch_date || '—'}</td>
                  <td className="px-3 py-3">{row.sp_launch_week || '—'}</td>
                  <td className="px-3 py-3 text-right">{row.sp_spend?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3">{row.cp_launch_date || '—'}</td>
                  <td className="px-3 py-3">{row.coupon_launch_week || '—'}</td>
                  <td className="px-3 py-3">{row.cl_status || '—'}</td>
                  <td className="px-3 py-3 text-right">{row.total_live_selection?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3 text-right">{row.fba_live_selection_wf?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3 text-right">{row.buyable_asin?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3 text-right">{row.total_gms?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3 text-right">{row.fba_gms?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3 text-right">{row.swas?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3 text-right">{row.fba_swas?.toLocaleString() ?? '—'}</td>
                  <td className="px-3 py-3 text-right">{row.fba_intransit?.toLocaleString() ?? '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Add the `PleMcidDrawer` import**

At the top of `frontend/src/pages/FosDashboard.jsx`, edit the import block:

```javascript
import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getFosDashboard } from '../api/dashboard'
import { createNewRegistration } from '../api/leads'
import { getPleMcidDetail } from '../api/ple'
import { useAuth } from '../context/AuthContext'
import PleMcidDrawer from '../components/PleMcidDrawer'
import toast from 'react-hot-toast'
```

- [ ] **Step 3: Verify in the browser**

With the dev stack running (http://localhost:8080), log in as a FOS user who has PLE MCIDs assigned, go to the PLE tab, and confirm: the new columns render, clicking a row opens the drawer, the Details tab shows the pending checklist plus all fields, the Update tab lets you change a status field and shows a toast on save, and the History tab shows the change afterward.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/FosDashboard.jsx
git commit -m "Add full field columns and MCID drill-down drawer to FOS PLE tab"
```

---

### Task 9: Frontend — Admin PLE agent drill-down

**Files:**
- Modify: `frontend/src/pages/AdminDashboard.jsx`

**Interfaces:**
- Consumes: `PleMcidDrawer` (Task 7), `getPleMcidDetail(params)` (Task 6), `PleAgentSummaryRow.agent_user_id` (Task 3).

- [ ] **Step 1: Add agent drill-down state and a per-agent MCID table to `PleTab`**

Replace the `PleTab` function in `frontend/src/pages/AdminDashboard.jsx` with:

```jsx
function PleAgentMcidTable({ agentUserId, agentName, onBack }) {
  const [selectedMcid, setSelectedMcid] = useState(null)
  const { data: mcidDetail, isLoading } = useQuery({
    queryKey: ['ple-mcid-detail', agentUserId],
    queryFn: () => getPleMcidDetail({ agent_user_id: agentUserId }).then((r) => r.data),
  })

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      {selectedMcid && <PleMcidDrawer mcid={selectedMcid} onClose={() => setSelectedMcid(null)} />}
      <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-3">
        <button onClick={onBack} className="text-xs text-blue-600 hover:underline">← Back to agents</button>
        <h2 className="font-semibold text-gray-700">{agentName}'s MCIDs</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
            <tr>
              <th className="px-5 py-3 text-left">MCID</th>
              <th className="px-3 py-3 text-left">FBA Status</th>
              <th className="px-3 py-3 text-left">SP Status</th>
              <th className="px-3 py-3 text-left">CP Adoption</th>
              <th className="px-3 py-3 text-left">Cross Launch</th>
              <th className="px-3 py-3 text-left">Cross Launch Final Stage</th>
              <th className="px-3 py-3 text-left">CL</th>
              <th className="px-3 py-3 text-right">Buyable ASIN</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-50">
            {isLoading ? (
              <tr><td colSpan={8} className="px-5 py-6 text-center text-gray-400">Loading...</td></tr>
            ) : !mcidDetail?.length ? (
              <tr><td colSpan={8} className="px-5 py-6 text-center text-gray-400">No MCIDs for this agent</td></tr>
            ) : (
              mcidDetail.map((row) => (
                <tr key={row.mcid} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedMcid(row.mcid)}>
                  <td className="px-5 py-3 font-mono text-blue-600 hover:underline">{row.mcid}</td>
                  <td className="px-3 py-3">{row.fba_status || '—'}</td>
                  <td className="px-3 py-3">{row.sp_status || '—'}</td>
                  <td className="px-3 py-3">{row.cp_adoption || '—'}</td>
                  <td className="px-3 py-3">{row.narf_cross_launch || '—'}</td>
                  <td className="px-3 py-3">{row.cross_launch_final_stage || '—'}</td>
                  <td className="px-3 py-3">{row.cl_status || '—'}</td>
                  <td className="px-3 py-3 text-right">{row.buyable_asin?.toLocaleString() ?? '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function PleTab() {
  const [selectedAgent, setSelectedAgent] = useState(null)
  const { data: agentSummary, isLoading: loadingAgents } = useQuery({
    queryKey: ['ple-agent-summary'],
    queryFn: () => getPleAgentSummary().then((r) => r.data),
  })

  if (selectedAgent) {
    return (
      <PleAgentMcidTable
        agentUserId={selectedAgent.agent_user_id}
        agentName={selectedAgent.agent}
        onBack={() => setSelectedAgent(null)}
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* User-wise Breakdown */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-700">User-wise Breakdown</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase">
              <tr>
                <th className="px-5 py-3 text-left">Agent</th>
                <th className="px-3 py-3 text-right">Launches</th>
                <th className="px-3 py-3 text-right">FBA Status</th>
                <th className="px-3 py-3 text-right">FBA Live Selection</th>
                <th className="px-3 py-3 text-right">SP</th>
                <th className="px-3 py-3 text-right">Any Deal Adoption (CP)</th>
                <th className="px-3 py-3 text-right">NARF/Cross Launch (CL)</th>
                <th className="px-3 py-3 text-right">Buyable ASIN (Total Live Selection)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {loadingAgents ? (
                <tr><td colSpan={8} className="px-5 py-6 text-center text-gray-400">Loading...</td></tr>
              ) : !agentSummary?.length ? (
                <tr><td colSpan={8} className="px-5 py-6 text-center text-gray-400">No PLE launches data uploaded yet</td></tr>
              ) : (
                agentSummary.map((row) => (
                  <tr key={row.agent} className="hover:bg-gray-50 cursor-pointer" onClick={() => setSelectedAgent(row)}>
                    <td className="px-5 py-3 font-medium text-blue-600 hover:underline">{row.agent}</td>
                    <td className="px-3 py-3 text-right">{row.num_launches?.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right">{row.fba_status_count?.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right">{row.fba_live_selection?.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right">{row.sp_status_count?.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right">{row.cp_adoption_count?.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right">{row.narf_cross_launch_count?.toLocaleString()}</td>
                    <td className="px-3 py-3 text-right">{row.buyable_asin?.toLocaleString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Add the imports**

At the top of `frontend/src/pages/AdminDashboard.jsx`:

```javascript
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { getAdminDashboard } from '../api/dashboard'
import { getPleAgentSummary, getPleMcidDetail } from '../api/ple'
import PleMcidDrawer from '../components/PleMcidDrawer'
```

- [ ] **Step 3: Verify in the browser**

Log in as admin, go to the PLE tab, confirm rows in "User-wise Breakdown" are clickable, clicking one shows that agent's MCID list with a "← Back to agents" link, clicking an MCID row opens the same `PleMcidDrawer`, and its History tab shows any edit made by the FOS user from Task 8's verification step.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/AdminDashboard.jsx
git commit -m "Add agent drill-down to admin PLE dashboard using shared MCID drawer"
```

---

### Task 10: End-to-end verification

**Files:** none (verification only)

- [ ] **Step 1: Restart the full stack to confirm migration + code changes hold together from a clean boot**

```bash
podman restart crm_backend_1 crm_celery-worker_1 crm_frontend_1 crm_nginx_1
```

- [ ] **Step 2: Confirm the backend is healthy**

Run: `curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/docs`
Expected: `200`

- [ ] **Step 3: Confirm the migration is at head**

Run: `podman exec crm_backend_1 alembic current`
Expected: `005 (head)`

- [ ] **Step 4: Full manual walkthrough**

Using the browser at http://localhost:8080:
1. As admin, upload a Launches file and an MCID-detail file that include at least one row with values for the new columns (`Marketplace ID`, `Launch Yes/No`, `SP Yes/No`, `Coupons`, `Cross Launch Final Stage`) — if no such test file is available, this step can instead directly `INSERT`/`UPDATE` a `ple_records` row via `podman exec crm_db_1 psql` to populate the new fields for one MCID assigned to a known FOS test user.
2. Log in as that FOS user, open the PLE tab, confirm the new columns show the uploaded values, click the MCID, confirm the Details tab's pending checklist and full field list match, edit a status field in the Update tab, save, and confirm the History tab shows the change.
3. Log in as admin, open the PLE tab, click that agent, click the same MCID, confirm the Details tab shows the same current values and the History tab shows the FOS user's edit with their name attached.
4. Re-upload the same Launches/MCID-detail file with a different value in the edited column, confirm the value reverts to the uploaded one (Excel-wins behavior) on both dashboards.

- [ ] **Step 5: Report completion**

No commit for this task — it's verification only. If any step fails, return to the relevant task above and fix before considering the feature complete.
