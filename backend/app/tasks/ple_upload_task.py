import io
import logging
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.celery_app import celery_app
from app.config import settings
from app.services.s3_service import download_file_from_s3
from app.services.upload_service import get_dev_temp_path
from app.utils.ple_parser import (
    LAUNCHES_FIELDS, MCID_DETAIL_FIELDS, LAUNCHES_SHEET_NAME_HINTS,
    find_header_row, map_columns,
    parse_mcid, parse_field, upsert_ple_record, resolve_lead_and_agent,
)

logger = logging.getLogger(__name__)

_sync_db_url = settings.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
_sync_engine = create_engine(_sync_db_url, pool_pre_ping=True)
SyncSession = sessionmaker(bind=_sync_engine)

_HEADER_SCAN_ROWS = 8


def _get_file_bytes(upload_id: str, s3_key: str) -> bytes:
    if not settings.r2_bucket:
        path = get_dev_temp_path(upload_id)
        with open(path, "rb") as f:
            return f.read()
    return download_file_from_s3(s3_key)


def _finish(session, upload_id: str, status: str, total: int, success: int, errors: int) -> None:
    session.execute(
        text("""
            UPDATE upload_files
            SET status=:s, total_rows=:t, success_rows=:ok, error_rows=:err, completed_at=:now
            WHERE id=:id
        """),
        {"s": status, "t": total, "ok": success, "err": errors,
         "now": datetime.now(timezone.utc), "id": upload_id},
    )


def _pick_best_sheet(file_bytes: bytes, engine: str, target_specs, name_hints: list[str] | None = None):
    """Scan every sheet's first few rows and pick whichever best matches the target
    field candidates (must at least contain an mcid column). If `name_hints` is given,
    a sheet whose name contains one of the hints (case-insensitive) and has a valid mcid
    column wins outright — weekly exports tend to keep stable internal sheet names even
    when business-facing column labels drift, so this is more reliable than pure scoring."""
    xls = pd.ExcelFile(io.BytesIO(file_bytes), engine=engine)
    best = None  # (score, sheet_name, header_row_idx, headers)
    hinted = None
    for sheet in xls.sheet_names:
        try:
            preview = pd.read_excel(xls, sheet_name=sheet, header=None, nrows=_HEADER_SCAN_ROWS)
        except Exception:
            continue
        rows = preview.values.tolist()
        if not rows:
            continue
        idx, headers = find_header_row(rows, target_specs, max_scan=len(rows))
        mapping = map_columns(headers, target_specs)
        if "mcid" not in mapping:
            continue
        score = len(mapping)
        if best is None or score > best[0]:
            best = (score, sheet, idx, headers)
        if hinted is None and name_hints and any(h in sheet.lower() for h in name_hints):
            hinted = (score, sheet, idx, headers)
    return hinted or best


def _is_blank(value) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def _process_upload(upload_file_id: str, engine: str, target_specs, source: str, name_hints: list[str] | None = None) -> dict:
    with SyncSession() as session:
        try:
            row = session.execute(
                text("SELECT s3_key FROM upload_files WHERE id=:id"), {"id": upload_file_id}
            ).fetchone()
            if not row:
                logger.error("upload_file not found: %s", upload_file_id)
                return {"status": "error"}

            session.execute(text("UPDATE upload_files SET status='processing' WHERE id=:id"), {"id": upload_file_id})
            session.commit()

            file_bytes = _get_file_bytes(upload_file_id, row[0])
            best = _pick_best_sheet(file_bytes, engine, target_specs, name_hints)
            if best is None:
                _finish(session, upload_file_id, "failed", 0, 0, 0)
                session.commit()
                return {"status": "error", "detail": "No sheet with a recognizable MCID column found"}

            _, sheet_name, header_idx, headers = best
            mapping = map_columns(headers, target_specs)

            full = pd.read_excel(
                io.BytesIO(file_bytes), sheet_name=sheet_name, header=None,
                engine=engine, skiprows=header_idx + 1,
            )

            success, errors, total = 0, 0, 0
            for _, row_series in full.iterrows():
                values = row_series.tolist()
                if all(_is_blank(v) for v in values):
                    continue
                total += 1

                mcid_col = mapping.get("mcid")
                if mcid_col is None or mcid_col >= len(values):
                    errors += 1
                    continue
                mcid = parse_mcid(values[mcid_col])
                if not mcid:
                    errors += 1
                    continue

                field_values = {}
                for field, col in mapping.items():
                    if field == "mcid" or col >= len(values):
                        continue
                    raw = values[col]
                    field_values[field] = parse_field(field, None if _is_blank(raw) else raw)

                rec = upsert_ple_record(session, mcid, field_values, source)
                resolve_lead_and_agent(session, rec)
                success += 1

            _finish(session, upload_file_id, "completed", total, success, errors)
            session.commit()
            logger.info("PLE %s upload %s done: %d ok, %d err", source, upload_file_id, success, errors)
            return {"status": "completed", "success": success, "errors": errors}

        except Exception as exc:
            session.rollback()
            logger.exception("PLE %s upload failed: %s", source, exc)
            _finish(session, upload_file_id, "failed", 0, 0, 0)
            session.commit()
            return {"status": "error"}


@celery_app.task(bind=True, name="process_ple_launches_upload")
def process_ple_launches_upload(self, upload_file_id: str) -> dict:
    return _process_upload(upload_file_id, "pyxlsb", LAUNCHES_FIELDS, "launches", LAUNCHES_SHEET_NAME_HINTS)


@celery_app.task(bind=True, name="process_ple_mcid_upload")
def process_ple_mcid_upload(self, upload_file_id: str) -> dict:
    return _process_upload(upload_file_id, "openpyxl", MCID_DETAIL_FIELDS, "mcid")
