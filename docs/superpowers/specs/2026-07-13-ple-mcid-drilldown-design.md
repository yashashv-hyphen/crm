# PLE MCID Drill-Down & Status Update — Design

## Problem

The PLE (Post-Launch Execution) dashboards show only aggregate/summary data today:

- **FOS dashboard** ("MCID-wise Breakdown" tab): shows a subset of MCID-detail-file fields per row, but rows are not clickable and nothing can be edited.
- **Admin dashboard** (PLE agent-summary tab): shows per-agent aggregate counts only (e.g. `fba_status_count`), with no way to drill into an individual agent's MCIDs or see what a FOS user has manually changed.

Neither dashboard exposes the full set of fields admin uploads (Launches-file fields like `fba_status`, `sp_status`, `cp_adoption`, `narf_cross_launch`, `buyable_asin` are currently admin-summary-only), and there is no way for a FOS user to update a status field or leave a record of what changed.

## Goals

1. FOS users can click an MCID row to see **every** field admin has uploaded for it (both Launches-file and MCID-detail-file data), plus a derived "what's still pending" checklist.
2. FOS users can update a defined set of editable status/date fields on an MCID, with changes audit-logged.
3. Admin users can click into an agent from the PLE agent-summary table to see that agent's MCIDs, and from there open the same per-MCID detail view — including the audit history of any FOS edits.
4. New fields requested by admin (`marketplace_id`, `launch_yn`, `sp_yn`, `coupons_yn`, `cross_launch_final_stage`) are captured from the uploaded Excel files and shown alongside existing fields.

## Non-Goals

- Excel upload/parsing UX changes beyond adding the five new column mappings.
- Changing what happens on re-upload: **admin's Excel upload always overwrites** any field it maps to a value for (already true today via `upsert_ple_record`'s generic `setattr` loop — no change needed there). A FOS-edited field is only "safe" from being overwritten until the next time admin uploads a file that has data for that field/MCID.
- Any workflow to prevent/merge conflicting edits between FOS and admin uploads. Excel wins, full stop.

## Data Model Changes

Add five new nullable columns to `PleRecord` (`backend/app/models/ple_record.py`):

| Field | Type | Notes |
|---|---|---|
| `marketplace_id` | `String(255)` | Sourced from Launches file only |
| `launch_yn` | `String(10)` | Yes/No, new/separate from `launch_date` |
| `sp_yn` | `String(10)` | Yes/No, new/separate from `sp_status` |
| `coupons_yn` | `String(10)` | Yes/No, new/separate from `cp_adoption` |
| `cross_launch_final_stage` | `String(10)` | Yes/No, new/separate from `narf_cross_launch` and `cl_status` |

New Alembic migration (`005_add_ple_extra_fields.py`) adding these columns.

### Parser changes (`backend/app/utils/ple_parser.py`)

Add all five fields to **both** `LAUNCHES_FIELDS` and `MCID_DETAIL_FIELDS` candidate-header lists (auto-detect in whichever file actually has the column), with synonym matching, e.g.:

- `marketplace_id`: `["marketplace id", "marketplace"]`
- `launch_yn`: `["launch yes no", "launch y n", "is launched"]` (distinct candidate strings from `launch_date`'s `["launch date"]` so `map_columns` doesn't confuse them)
- `sp_yn`: `["sp yes no", "sp y n"]`
- `coupons_yn`: `["coupons", "coupon yes no"]`
- `cross_launch_final_stage`: `["cross launch final stage", "final stage"]`

`_FIELD_PARSERS` needs no new entries — these are all plain strings, default `parse_str` applies.

No change needed to `upsert_ple_record` — the generic `setattr` loop already handles new fields present in the parsed `values` dict.

## Audit Trail

New model `PleRecordHistory` (`backend/app/models/ple_record_history.py`), mirroring `LeadHistory`:

```
id            UUID, PK
ple_record_id UUID, FK -> ple_records.id, indexed
field_name    String(100)
old_value     Text, nullable
new_value     Text, nullable
performed_by  UUID, FK -> users.id
performed_at  DateTime, server_default now()
```

One row per changed field per PATCH call (a single request that changes 3 fields writes 3 history rows).

## Editable vs Read-Only Fields

**Editable** (FOS-assigned-agent or admin, via PATCH):
`fba_status, sp_status, cl_status, cp_adoption, narf_cross_launch, launch_yn, sp_yn, coupons_yn, cross_launch_final_stage, launch_date, fba_launch_date, sp_launch_date, cp_launch_date`

**Read-only** (admin-upload-only, displayed but not editable):
`marketplace_id, agent_name, launch_week, fba_launch_week, sp_launch_week, sp_spend, coupon_launch_week, total_live_selection, fba_live_selection, fba_live_selection_wf, total_gms, fba_gms, swas, fba_swas, fba_intransit, buyable_asin, lead_id, launches_uploaded_at, mcid_uploaded_at`

## Backend API Changes

### `backend/app/schemas/ple.py`

- `PleMcidDetailRow`: add all fields above (both Launches-file and MCID-detail-file fields, plus the five new fields) so it represents the complete record.
- New `PleMcidUpdateRequest`: optional versions of each editable field (only fields present in the request body get updated/audited).
- New `PleRecordHistoryEntry`: `field_name, old_value, new_value, performed_by_name, performed_at`.

### `backend/app/routers/ple.py`

- `PATCH /api/ple/mcid/{mcid}` — body: `PleMcidUpdateRequest`. Permission: `admin`, or `fos` where `PleRecord.agent_user_id == current_user.id` (404/403 otherwise). For each field present and changed, write a `PleRecordHistory` row, then update the record. Returns the updated `PleMcidDetailRow`.
- `GET /api/ple/mcid/{mcid}/history` — same permission check as above; returns `list[PleRecordHistoryEntry]` ordered by `performed_at`.
- `GET /api/ple/mcid-detail` (existing) — no signature change, but now the FOS-only-sees-own-records filter continues to apply; admin can additionally pass `?agent_user_id=` to filter to one agent's MCIDs (used by the admin drill-down).

### `backend/app/services/ple_service.py`

- `get_mcid_detail`: accept and apply optional `agent_user_id` filter (already partially there for FOS; extend so admin can pass it explicitly as a query param too).
- New `update_mcid_record(db, mcid, updates, performed_by)`: loads the `PleRecord`, diffs requested fields against current values, writes `PleRecordHistory` rows for actual changes, applies updates, commits.
- New `get_mcid_history(db, mcid)`: returns history rows joined with `User.full_name`.

## Frontend Changes

### New shared component: `PleMcidDrawer.jsx`

Modeled on `LeadDetailDrawer.jsx`. Props: `mcid`, `onClose`, `canEdit` (bool).

- **Pending checklist** (derived client-side): one line per tracked status/date field, ✔ if set / ✖ if null — `FBA Status, SP Status, CL Status, CP Adoption, Cross Launch, Cross Launch Final Stage, Launch Y/N, SP Y/N, Coupons Y/N`, plus the four launch dates.
- **Full field list**: every field on the record. Editable fields render as inline text input (status fields) or date picker (date fields) with a single "Save changes" button that PATCHes only the fields actually changed. Read-only fields render as plain text (same `DetailRow` pattern as `LeadDetailDrawer`).
- **History tab**: lists `PleRecordHistoryEntry` rows, same visual pattern as `LeadDetailDrawer`'s `HistoryTab`.
- When `canEdit` is false (e.g. admin viewing an MCID not assigned to them — shouldn't normally happen since admin always has edit rights per the permission model above, so in practice `canEdit` is just `true` for admin and `true` for the FOS user who owns the record) inputs render disabled.

### `frontend/src/pages/FosDashboard.jsx`

- `PleTab`: add the new columns to the table (`Marketplace ID, Launch Y/N, SP Y/N, Coupons Y/N, Cross Launch Final Stage`, plus the previously-admin-only `FBA Status, SP Status, CP Adoption, Cross Launch, Buyable ASIN, FBA Live Selection`).
- Make each row clickable, opening `PleMcidDrawer` with `canEdit=true`.

### `frontend/src/pages/AdminDashboard.jsx`

- Agent-summary table rows become clickable → opens a new per-agent MCID list view (reuses the same table markup as `PleTab`'s breakdown, fetched via `getPleMcidDetail({ agent_user_id })`).
- Rows in that per-agent list are clickable → opens `PleMcidDrawer` with `canEdit=true` (admin can always edit) — showing both the admin-uploaded values and, via the History tab, what the FOS user changed.

### `frontend/src/api/ple.js`

- Add `getPleMcidHistory(mcid)`, `updatePleMcid(mcid, updates)`, and extend `getPleMcidDetail` to accept an optional `agent_user_id` param.

## Testing

- Backend: parser tests for the five new field mappings (both files); PATCH endpoint permission tests (FOS-owns-record vs FOS-not-owner vs admin); history-row-per-changed-field test; re-upload-overwrites-manual-edit test (regression guard for the "Excel always wins" behavior).
- Frontend: manual verification via `/verify` skill — open FOS PLE tab, click an MCID, edit a status, confirm history shows it, confirm admin drill-down from agent-summary shows the same edit.
