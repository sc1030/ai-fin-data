# app/db.py
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Get DB URL from environment (for Postgres/MySQL in Streamlit Secrets)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # Fallback to SQLite if no DB URL is provided
    DATABASE_URL = "sqlite:///./app_data.db"

# For SQLite we need check_same_thread, for others we don’t
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# app/db.py

def init_db():
    """Initialize database tables (only if they don't exist)"""
    import app.models  # Ensure models are imported

    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        print("✅ Database initialized (tables created if missing)")
    except Exception as e:
        print(f"⚠️ Skipped table creation: {e}")
