from sqlalchemy import and_, func

from app.models.lead import Lead

# RNC/IDV/RTL/Launch: the flow the Stage Summary matrix cross-tabs leads
# against. "Other" catches everything that doesn't substring-match one of
# these — legacy activities (FBA/SP/Open Spending/NARF/GSI), New
# Registration, or leads that have moved past RTL into a later activity
# without having launched yet.
STAGE_BUCKETS = ["RNC", "IDV", "RTL", "Launch", "Other"]

# Row axis for the matrix: a lead can't originally be *assigned* to Launch
# (it's a terminal state reached, not assigned into), so the row axis drops
# it — any lead whose stage_assigned nonetheless looks like "Launch" folds
# into Other.
ROW_STAGE_BUCKETS = ["RNC", "IDV", "RTL", "Other"]

_KEYWORDS = {"RNC": "rnc", "IDV": "idv", "RTL": "rtl", "Launch": "launch"}


def bucket_stage_name(name: str | None) -> str:
    """Substring-match a stage/activity name into one of STAGE_BUCKETS,
    mirroring movement_engine._activity_entry_field's matching style."""
    if not name:
        return "Other"
    lowered = name.lower()
    for bucket, keyword in _KEYWORDS.items():
        if keyword in lowered:
            return bucket
    return "Other"


def bucket_assigned_stage(name: str | None) -> str:
    """Like bucket_stage_name, but for the row axis: Launch isn't a valid
    assignment bucket, so it folds into Other."""
    bucket = bucket_stage_name(name)
    return "Other" if bucket == "Launch" else bucket


def bucket_current_stage(current_stage: str | None, final_stage: str | None) -> str:
    """A lead's current-stage bucket: Launch takes priority (final_stage is
    the only place "launched" is recorded — there's no Launch activity),
    otherwise bucket by the live current_stage name."""
    if final_stage and "launch" in final_stage.lower():
        return "Launch"
    return bucket_stage_name(current_stage)


def assigned_stage_condition(bucket: str):
    """SQL WHERE condition matching Lead.stage_assigned to a bucket."""
    col = func.coalesce(Lead.stage_assigned, "")
    if bucket == "Other":
        return and_(*[~col.ilike(f"%{kw}%") for kw in _KEYWORDS.values()])
    return col.ilike(f"%{_KEYWORDS[bucket]}%")


def current_stage_condition(bucket: str):
    """SQL WHERE condition matching (Lead.current_stage, Lead.final_stage)
    to a bucket, mirroring bucket_current_stage's Python logic."""
    final_col = func.coalesce(Lead.final_stage, "")
    current_col = func.coalesce(Lead.current_stage, "")
    is_launch = final_col.ilike("%launch%")

    if bucket == "Launch":
        return is_launch
    if bucket == "Other":
        return and_(
            ~is_launch,
            *[~current_col.ilike(f"%{kw}%") for kw in _KEYWORDS.values() if kw != "launch"],
        )
    return and_(~is_launch, current_col.ilike(f"%{_KEYWORDS[bucket]}%"))
