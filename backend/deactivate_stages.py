"""Run from backend container: python /app/scripts/deactivate_stages.py"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models.activity import Activity

SYNC_URL = settings.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
engine = create_engine(SYNC_URL)

STAGES_TO_DEACTIVATE = [
    "FBA Pending",
    "SP Pending",
    "Open Spending",
    "NARF Pending",
]

with Session(engine) as session:
    for name in STAGES_TO_DEACTIVATE:
        activity = session.query(Activity).filter_by(name=name).first()
        if not activity:
            print(f"  Activity not found: {name}")
            continue
        if not activity.is_active:
            print(f"  Already inactive: {name}")
            continue
        activity.is_active = False
        print(f"  Deactivated: {name}")

    session.commit()
    print("\nDeactivation complete.")
