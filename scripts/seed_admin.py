"""Creates the first admin user. Run from backend container after migrations."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.models.user import User

SYNC_URL = settings.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")
engine = create_engine(SYNC_URL)

ADMIN_NAME = os.environ.get("ADMIN_NAME", "Super Admin")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@newtrendscommerce.in")

with Session(engine) as session:
    existing = session.query(User).filter_by(email=ADMIN_EMAIL).first()
    if existing:
        print(f"Admin already exists: {ADMIN_EMAIL}")
    else:
        admin = User(id=uuid.uuid4(), full_name=ADMIN_NAME, email=ADMIN_EMAIL, role="admin")
        session.add(admin)
        session.commit()
        print(f"Admin created: {ADMIN_EMAIL}")
        print("Login at /login with this email to receive OTP.")
