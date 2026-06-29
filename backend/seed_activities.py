"""Run from backend container: python /app/scripts/seed_activities.py"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import Base
from app.models.activity import Activity
from app.models.sub_disposition import SubDisposition

SYNC_URL = settings.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
engine = create_engine(SYNC_URL)

ACTIVITIES = [
    "RNC Pending",
    "IDV Pending",
    "RTL Pending",
    "FBA Pending",
    "SP Pending",
    "Open Spending",
    "NARF Pending",
    "GSI",
]

COMMON_SUB_DISPOSITIONS = [
    "Did Not Pick",
    "Call Back Later",
    "Not Interested",
    "Wrong Number",
    "Number Busy",
    "Interested",
    "Language Barrier",
]

ACTIVITY_SPECIFIC = {
    "RNC Pending": [
        "Not Interested - Fee Issue",
        "Not Interested - Lost Interest",
        "Registration Link Not Working",
        "Already Registered",
    ],
    "IDV Pending": [
        "Documents Not Ready",
        "IDV Link Not Working",
        "Verification Failed",
        "Pending Govt ID",
    ],
    "RTL Pending": [
        "Technical Issue",
        "Catalog Not Ready",
        "Awaiting Launch Approval",
    ],
    "FBA Pending": [
        "Not Interested in FBA",
        "Shipment Pending",
        "FC Not Available",
    ],
    "SP Pending": [
        "Not Interested in Ads",
        "Budget Issue",
        "Ad Account Not Set Up",
    ],
    "Open Spending": [
        "No Coupon Participation",
        "Budget Exhausted",
        "Coupon Not Applicable",
    ],
    "NARF Pending": [
        "NARF Not Applicable",
        "Pending Documents",
        "Awaiting Approval",
    ],
    "GSI": [
        "GSI Not Applicable",
        "In Progress",
        "Completed",
    ],
}

with Session(engine) as session:
    for i, name in enumerate(ACTIVITIES, 1):
        existing = session.query(Activity).filter_by(name=name).first()
        if not existing:
            activity = Activity(id=uuid.uuid4(), name=name, position_order=i)
            session.add(activity)
            print(f"  Created activity: {name} (position {i})")
        else:
            print(f"  Activity already exists: {name}")

    session.flush()

    # Common sub-dispositions
    for name in COMMON_SUB_DISPOSITIONS:
        existing = session.query(SubDisposition).filter_by(name=name, is_common=True).first()
        if not existing:
            sd = SubDisposition(id=uuid.uuid4(), activity_id=None, name=name, is_common=True)
            session.add(sd)
            print(f"  Common sub-disp: {name}")

    # Activity-specific
    for act_name, sub_disps in ACTIVITY_SPECIFIC.items():
        activity = session.query(Activity).filter_by(name=act_name).first()
        if not activity:
            continue
        for sd_name in sub_disps:
            existing = session.query(SubDisposition).filter_by(name=sd_name, activity_id=activity.id).first()
            if not existing:
                sd = SubDisposition(id=uuid.uuid4(), activity_id=activity.id, name=sd_name, is_common=False)
                session.add(sd)
                print(f"  [{act_name}] sub-disp: {sd_name}")

    session.commit()
    print("\nSeed complete.")
