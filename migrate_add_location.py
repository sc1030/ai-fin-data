from sqlalchemy import text
from app.db import engine

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE financial_data ADD COLUMN location VARCHAR;"))
    conn.commit()
    print("✅ Location column added successfully.")
