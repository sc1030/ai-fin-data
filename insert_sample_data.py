import pandas as pd
from datetime import datetime, timedelta
from app.db import SessionLocal
from app.models import FinancialData

company_locations = {
    "AAPL": "37.3349,-122.0090",
    "MSFT": "47.6426,-122.1366",
    "GOOGL": "37.4220,-122.0841",
    "AMZN": "47.6220,-122.3360",
    "TSLA": "37.3947,-122.1500",
    "TCS.NS": "19.0760,72.8777"
}

# Generate fake 5 days of closing data for each company
session = SessionLocal()
base_date = datetime.now()

for ticker, location in company_locations.items():
    for i in range(5):
        day = base_date - timedelta(days=i)
        fd = FinancialData(
            ticker=ticker,
            date=day,
            open=100 + i,
            high=105 + i,
            low=95 + i,
            close=102 + i,
            volume=1000000 + i*5000,
            location=location
        )
        session.add(fd)

session.commit()
session.close()
print("✅ Sample data with geolocation inserted.")
