# Pipeline Flow Funnel (RNC → IDV → RTL → Launch) — Design

## Problem

The dashboards (FOS and Admin) currently show a generic "Moved to Next" column per
activity stage, computed as `Lead.current_activity_id == <stage> AND Lead.final_stage
IS NOT NULL`. This doesn't answer the question stakeholders actually care about: how
many leads specifically progressed through the real funnel — RNC → IDV → RTL → Launch
— while preserving all existing dashboard data untouched.

## Goals

- Add a dedicated "Pipeline Flow" funnel showing counts (and conversion %) at each of:
  RNC, IDV, RTL, Launch.
- Purely additive, read-only reporting change:
  - No changes to `movement_engine.py`, lead update/movement logic, or `LeadHistory`.
  - No changes to the existing per-activity Stage Summary table (columns, values,
    behavior) on either dashboard — it stays exactly as it is today.
  - No schema migrations — computed from existing columns.
- Must be real, rendered frontend UI (not just new API fields), visible on:
  - FOS Dashboard ("Stages" tab)
  - Admin Dashboard (overall, once) and per-agent (inside the agent-wise section)

## Non-goals

- Changing FBA/SP/Open Spending/NARF/GSI reporting — untouched.
- Changing how `current_activity_id`, `final_stage`, or entry-date fields are written.
- New stage funnels beyond RNC→IDV→RTL→Launch.

## Stage detection logic

Using existing `Lead` columns, no new fields:

| Node | Condition |
|---|---|
| RNC | `rnc_entry_date IS NOT NULL` (entered the funnel) |
| IDV | `idv_entry_date IS NOT NULL` (moved RNC → IDV) |
| RTL | `rtl_entry_date IS NOT NULL` (moved IDV → RTL) |
| Launch | `final_stage ILIKE '%launch%'` (moved RTL → Launch) |

Each node counts leads where `is_archived = False`, plus whatever filters already
apply to the surrounding dashboard call (`fos_id`, `year`, `date_of_assignment`
range for admin).

Conversion % for a node = `count / previous_node_count * 100` (RNC has no conversion,
shown as the funnel baseline / 100%).

## Backend changes

`backend/app/services/dashboard_service.py`:
- New function `_pipeline_flow(fos_id, db, from_date=None, to_date=None, year=None) ->
  list[PipelineFlowStage]` — runs the 4 counts above via 4 independent `select(func.count())`
  queries (same filter pattern as `_stage_summary_for_fos`), returns nodes in order with
  count and conversion_from_previous_pct.
- `get_fos_dashboard`: calls `_pipeline_flow(fos_id, db)`, adds to response.
- `get_admin_dashboard`: calls `_pipeline_flow(fos_id, db, from_date, to_date, year)` for
  the overall funnel (respecting existing filters), and per-agent inside the
  `agent_summaries` loop.

`backend/app/schemas/dashboard.py`:
- New `PipelineFlowStage(BaseModel)`: `stage: str`, `count: int`, `conversion_from_previous_pct: float | None`.
- `FOSDashboardResponse.pipeline_flow: list[PipelineFlowStage]`
- `AdminDashboardResponse.overall_pipeline_flow: list[PipelineFlowStage]`
- `AgentStageSummary.pipeline_flow: list[PipelineFlowStage]`

No changes to `StageSummaryRow`, `_stage_summary_for_fos`, or `_disposition_summary`.

## Frontend changes

New component `frontend/src/components/PipelineFunnel.jsx`:
- Props: `stages` (array of `{stage, count, conversion_from_previous_pct}`), `onStageClick(stage)`.
- Renders 4 connected stat blocks left-to-right (RNC → IDV → RTL → Launch) with count
  and conversion % between consecutive blocks, using the existing `ClickableNumber`
  drill-down pattern to navigate to `/leads` filtered appropriately
  (e.g. `idv_entry_date_set=true`, `final_stage_contains=launch`) — reuses the existing
  `goToLeads`-style navigation already present in both dashboards.

`frontend/src/pages/FosDashboard.jsx`:
- Inside the `activeTab === 'stages'` block, render `<PipelineFunnel stages={data?.pipeline_flow} />`
  above the existing Stage Summary table. Existing table markup/columns unchanged.

`frontend/src/pages/AdminDashboard.jsx`:
- Render `<PipelineFunnel stages={data?.overall_pipeline_flow} />` once near the top of
  the dashboard (below filters, above the existing overall Stage Summary table).
- Inside the agent-wise summary section, render a `<PipelineFunnel>` per agent alongside
  their existing per-activity stage_summary table.
- Existing overall/agent-wise Stage Summary tables unchanged.

## Testing / verification

- Backend: unit-test `_pipeline_flow` against seeded leads with known entry-date/final_stage
  combinations, verifying counts and conversion % at each node, with and without filters.
- Frontend: manually verify via `/verify`-style browser check that the funnel renders on
  both dashboards with real data, drill-down links navigate to correctly filtered
  `/leads` views, and the existing Stage Summary tables are visually unchanged.
