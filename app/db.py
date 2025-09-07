from dotenv import load_dotenv
load_dotenv()

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Get DB URL from .env or fallback to SQLite
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./app_data.db"

# Handle SQLite separately
if DATABASE_URL.startswith("sqlite:///"):
    db_path = DATABASE_URL.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    """Initialize database tables (only if missing)"""
    import app.models  # Ensure models are imported

    Base.metadata.create_all(bind=engine, checkfirst=True)
    print("✅ Database ready")
