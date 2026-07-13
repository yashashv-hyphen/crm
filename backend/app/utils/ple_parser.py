import re
import uuid
from datetime import datetime, date, timezone, timedelta

from app.models.ple_record import PleRecord

_EXCEL_EPOCH = datetime(1899, 12, 30)


def _norm(value) -> str:
    if value is None:
        return ""
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def find_header_row(rows: list[tuple], target_specs: list[tuple[str, list[str]]], max_scan: int = 8) -> tuple[int, list[str]]:
    """Scan the first `max_scan` rows of a sheet and return the (index, normalized headers)
    of whichever row has the most matches against the target field candidate substrings.
    Handles sheets whose real header isn't row 0 (e.g. title/weight rows above it)."""
    best_idx, best_score, best_headers = 0, -1, []
    for i in range(min(max_scan, len(rows))):
        headers = [_norm(c) for c in rows[i]]
        score = 0
        for _field, candidates in target_specs:
            if any(any(cand in h for cand in candidates) for h in headers if h):
                score += 1
        if score > best_score:
            best_score, best_idx, best_headers = score, i, headers
    return best_idx, best_headers


def map_columns(headers: list[str], target_specs: list[tuple[str, list[str]]]) -> dict[str, int]:
    """Map each target field to a column index. Fields earlier in target_specs (more specific,
    e.g. 'fba_launch_date') claim their column before later/generic fields (e.g. 'launch_date').
    Within a field, candidates are tried in priority order (not header/column order) so the
    most-preferred synonym wins even if a lower-priority synonym happens to appear at an
    earlier column index; exact header matches are preferred over substring matches."""
    used: set[int] = set()
    mapping: dict[str, int] = {}
    for field, candidates in target_specs:
        found = None
        for cand in candidates:
            for i, h in enumerate(headers):
                if i in used or not h:
                    continue
                if h == cand:
                    found = i
                    break
            if found is not None:
                break
        if found is None:
            for cand in candidates:
                for i, h in enumerate(headers):
                    if i in used or not h:
                        continue
                    if cand in h:
                        found = i
                        break
                if found is not None:
                    break
        if found is not None:
            mapping[field] = found
            used.add(found)
    return mapping


def parse_mcid(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, float):
        return str(int(value))
    s = str(value).strip()
    return s or None


def parse_date(value) -> date | None:
    if value is None:
        return None
    try:
        import pandas as pd
        if pd.isna(value):
            return None
    except (TypeError, ValueError, ImportError):
        pass
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        try:
            return (_EXCEL_EPOCH + timedelta(days=float(value))).date()
        except (OverflowError, ValueError):
            return None
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
    return None


def parse_int(value) -> int | None:
    if value is None:
        return None
    try:
        if isinstance(value, str):
            value = value.strip().replace(",", "")
            if not value:
                return None
        return int(float(value))
    except (ValueError, TypeError):
        return None


def parse_float(value) -> float | None:
    if value is None:
        return None
    try:
        if isinstance(value, str):
            value = value.strip().replace(",", "")
            if not value:
                return None
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_str(value) -> str | None:
    if value is None:
        return None
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    s = str(value).strip()
    return s or None


_BLANK_AGENT_SENTINELS = {"not avalaible", "not available", "n/a", "na", "none", "-", "unassigned", "unknown"}


def parse_agent_name(value) -> str | None:
    s = parse_str(value)
    if s is None or s.lower() in _BLANK_AGENT_SENTINELS:
        return None
    return s


_FIELD_PARSERS = {
    "agent_name": parse_agent_name,
    "fba_live_selection": parse_int,
    "buyable_asin": parse_int,
    "launch_date": parse_date,
    "fba_launch_date": parse_date,
    "sp_launch_date": parse_date,
    "sp_spend": parse_float,
    "cp_launch_date": parse_date,
    "total_live_selection": parse_int,
    "fba_live_selection_wf": parse_int,
    "total_gms": parse_float,
    "fba_gms": parse_float,
    "swas": parse_float,
    "fba_swas": parse_float,
    "fba_intransit": parse_int,
}


def parse_field(field: str, value):
    return _FIELD_PARSERS.get(field, parse_str)(value)


# Candidates ordered specific-before-generic so map_columns doesn't let a generic
# field (e.g. "launch_date") steal a more specific field's column (e.g. "fba_launch_date").
LAUNCHES_FIELDS: list[tuple[str, list[str]]] = [
    ("mcid", ["merchant customer id", "mcid", "merchant id"]),
    ("agent_name", ["bd am", "opportunity owner", "fba opportunity owner", "gse name", "gse", "agent", "owner"]),
    ("marketplace_id", ["marketplace id", "marketplace"]),
    ("fba_live_selection", ["fba live selection", "fba live seletion", "fba ba t4w"]),
    ("fba_status", ["fba status", "is fba launched", "is fba active", "fba active", "is fba"]),
    ("sp_status", ["sp status", "is sp active", "is sp"]),
    ("cp_adoption", ["any deal adoption", "deal adoption cp", "coupon adoption", "is coupon active", "is coupon granted", "is cp"]),  # priority order: adoption-worded first, then "active", then "granted"
    ("cross_launch_final_stage", ["cross launch final stage", "final stage"]),
    ("narf_cross_launch", ["narf cross launch", "narf", "is perfect launched", "cross launch"]),
    ("buyable_asin", ["buyable asin", "total live selection"]),
    ("launch_yn", ["launch yes no", "launch y n", "is launched"]),
    ("sp_yn", ["sp yes no", "sp y n"]),
    ("coupons_yn", ["coupons yes no", "coupons y n", "coupons"]),
]

# Sheet-name hints, checked before falling back to header fuzzy-scoring across all sheets —
# weekly exports tend to keep a stable internal "raw"/flat-table sheet name even when the
# business-facing column labels drift, so a name-based match is more reliable than scoring.
LAUNCHES_SHEET_NAME_HINTS = ["raw"]

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


def upsert_ple_record(session, mcid: str, values: dict, source: str) -> PleRecord:
    """source: 'launches' or 'mcid'. Sets agent_name from the launches file preferentially,
    falling back to the mcid-detail file's GSE Name only when not already set."""
    rec = session.query(PleRecord).filter_by(mcid=mcid).one_or_none()
    if rec is None:
        rec = PleRecord(id=uuid.uuid4(), mcid=mcid)
        session.add(rec)

    for field, value in values.items():
        if field in ("mcid",):
            continue
        if field == "agent_name":
            if value and (source == "launches" or not rec.agent_name):
                rec.agent_name = value
            continue
        setattr(rec, field, value)

    now = datetime.now(timezone.utc)
    if source == "launches":
        rec.launches_uploaded_at = now
    else:
        rec.mcid_uploaded_at = now
    return rec


def resolve_lead_and_agent(session, rec: PleRecord) -> None:
    """Best-effort link to an existing lead (by merchant_id) and CRM user (by full_name)."""
    from sqlalchemy import text

    if rec.lead_id is None:
        lead_row = session.execute(
            text("SELECT id FROM leads WHERE merchant_id=:mid"), {"mid": rec.mcid}
        ).fetchone()
        if lead_row:
            rec.lead_id = lead_row[0]

    if rec.agent_name and rec.agent_user_id is None:
        user_row = session.execute(
            text("SELECT id FROM users WHERE lower(full_name)=lower(:name)"),
            {"name": rec.agent_name.strip()},
        ).fetchone()
        if user_row:
            rec.agent_user_id = user_row[0]
