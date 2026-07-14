# Pipeline Flow (RNC → IDV → RTL → Launch) — Design

## Problem

The dashboards (FOS and Admin) currently show a generic "Moved to Next" column per
activity stage, computed as `Lead.current_activity_id == <stage> AND Lead.final_stage
IS NOT NULL`. In practice this is always 0, because a lead whose `current_activity_id`
is still RNC/IDV by definition hasn't had `final_stage` set yet — the check is
self-contradictory. This doesn't answer what stakeholders actually care about: of the
leads that existed at a stage, how many moved to the next stage of the real funnel
(RNC → IDV → RTL → Launch), and how many have launched overall.

## Goals

- Redefine the existing Stage Summary table (same table, same columns, same tab —
  no new widget) so it reflects the real flow:
  - **RNC row** — Total Assigned: leads that entered RNC. Moved to Next: leads that
    also entered IDV (i.e. progressed out of RNC). Pending: the remainder still sitting
    in RNC.
  - **IDV row** — Total Assigned: leads that entered IDV. Moved to Next: leads that
    also entered RTL. Pending: remainder still sitting in IDV.
  - **RTL row** — Total Assigned: leads that entered RTL. Moved to Next: leads whose
    `final_stage` indicates Launch. Pending: remainder still sitting in RTL, not yet
    launched.
  - **New Launch row** — Total Assigned: total launched leads. Moved to Next: — (dash,
    terminal stage, no "next"). Pending: — (dash).
- Purely a reporting/read-side change:
  - No changes to `movement_engine.py`, lead update/movement logic, or `LeadHistory`.
  - No schema migrations — computed from existing columns.
- Must be real, rendered frontend UI, visible on:
  - FOS Dashboard ("Stages" tab) — the existing table itself changes.
  - Admin Dashboard (overall table) and per-agent (inside the agent-wise section) —
    same redefinition applied everywhere `StageSummaryRow` currently renders.

## Non-goals

- Changing FBA/SP/Open Spending/NARF/GSI rows — those keep today's `moved_to_next`
  logic (`final_stage.isnot(None)`) unchanged; only RNC/IDV/RTL are redefined and a
  Launch row is added.
- Changing how `current_activity_id`, `final_stage`, or entry-date fields are written.
- A separate standalone funnel widget — explicitly rejected in favor of updating the
  existing table in place.

## Stage detection logic

Using existing `Lead` columns, no new fields. For a lead currently attributed to a
given row, "entered stage X" means the corresponding entry-date column is set:

| Row | Total Assigned | Moved to Next | Pending |
|---|---|---|---|
| RNC | `rnc_entry_date IS NOT NULL` | `rnc_entry_date IS NOT NULL AND idv_entry_date IS NOT NULL` | Total − Moved |
| IDV | `idv_entry_date IS NOT NULL` | `idv_entry_date IS NOT NULL AND rtl_entry_date IS NOT NULL` | Total − Moved |
| RTL | `rtl_entry_date IS NOT NULL` | `rtl_entry_date IS NOT NULL AND final_stage ILIKE '%launch%'` | Total − Moved |
| Launch | `final_stage ILIKE '%launch%'` | — (dash, terminal) | — (dash) |

All rows additionally filter `is_archived = False`, plus whatever filters already
apply to the surrounding dashboard call (`fos_id`, `year`, `date_of_assignment`
range for admin — same pattern `_stage_summary_for_fos` uses today).

This replaces `current_activity_id == <stage>` as the row-membership condition for
RNC/IDV/RTL (a lead counts toward a row once it has entered that stage, even if it
has since moved further — this is what makes "Moved to Next" meaningful instead of
always-zero). FBA/SP/Open Spending/NARF/GSI rows are untouched and keep using
`current_activity_id` + the old `moved_to_next` check.

## Backend changes

`backend/app/services/dashboard_service.py`:
- New function `_flow_stage_row(condition_field, next_field_or_launch, label, fos_id,
  db, from_date=None, to_date=None, year=None) -> StageSummaryRow` implementing one row
  of the table above (reused for RNC/IDV/RTL), plus a small dedicated query for the
  Launch row.
- `_stage_summary_for_fos`: for activities named RNC/IDV/RTL, build their
  `StageSummaryRow` via the new flow logic instead of the current
  `current_activity_id` + `final_stage.isnot(None)` logic; append a Launch row after
  RTL. All other activities (FBA/SP/Open Spending/NARF/GSI) and the New Registration
  row keep today's logic unchanged.
- `get_admin_dashboard`'s overall-summary loop gets the same RNC/IDV/RTL/Launch
  treatment, mirroring `_stage_summary_for_fos` (both currently duplicate this kind of
  per-activity loop, so the flow logic is factored into one shared helper used by both).

`backend/app/schemas/dashboard.py`:
- `StageSummaryRow.moved_to_next` and `.pending` become `int | None` (`None` renders as
  "—" for the terminal Launch row, which has no activity_id and no next stage).
- No new schema types — the Launch row is just another `StageSummaryRow` with
  `activity_id=None`, `activity_name="Launch"`.

## Frontend changes

No new components. `stageName()` in `FosDashboard.jsx` / equivalent in
`AdminDashboard.jsx` already strips " Pending" suffixes for display — "Launch" needs
no special-casing, it renders like any other row. `ClickableNumber` on `moved_to_next`/
`pending` must tolerate `null` (render "—", not clickable) for the Launch row.

`frontend/src/pages/FosDashboard.jsx`:
- No structural change — `data.stage_summary` already renders via `.map()`. The new
  Launch row simply appears because the backend now includes it. `ClickableNumber`
  needs a `null`-safe guard (skip `onClick`/render "—" when value is `null`).

`frontend/src/pages/AdminDashboard.jsx`:
- Same: overall table and each agent's `stage_summary` table render the new Launch row
  and updated RNC/IDV/RTL semantics automatically via existing `.map()` logic. Apply
  the same `null`-safe `ClickableNumber` guard here (used in both the overall table and
  the per-agent pivot table).

## Testing / verification

- Backend: unit-test the new flow-row logic against seeded leads with known
  entry-date/final_stage combinations — verify RNC/IDV/RTL Total/Moved/Pending and the
  Launch row count, with and without `fos_id`/`year`/date-range filters.
- Frontend: `/verify` in-browser — confirm the FOS "Stages" tab and Admin dashboard
  (overall + at least one agent) show the redefined RNC/IDV/RTL numbers, a visible
  Launch row, and that drill-down clicks on non-dash cells navigate to `/leads`
  correctly filtered.
