company_locations = {
    "AAPL": {"lat": 37.3349, "lon": -122.0090},   # Apple Park, Cupertino
    "MSFT": {"lat": 47.6426, "lon": -122.1396},   # Microsoft HQ, Redmond
    "GOOGL": {"lat": 37.4220, "lon": -122.0841},  # Googleplex, Mountain View
    "AMZN": {"lat": 47.6225, "lon": -122.3365},   # Amazon, Seattle
    "TSLA": {"lat": 37.3947, "lon": -122.1503},   # Tesla, Palo Alto
    "META": {"lat": 37.4845, "lon": -122.1477},   # Meta, Menlo Park
}

from app.models import FinancialData
from datetime import datetime

def save_financial_data(session, ticker, price, volume, pe_ratio):
    location = company_locations.get(
        ticker, {"lat": 37.7749, "lon": -122.4194}  # Default: San Francisco
    )
    loc_str = f"{location['lat']},{location['lon']}"
    data = FinancialData(
        ticker=ticker,
        close=price,
        volume=volume,
        # If you have a pe_ratio field, add it here
        date=datetime.utcnow(),
        location=loc_str
    )
    session.add(data)
    session.commit()
    return data
import yfinance as yf
import pandas as pd

def fetch_yfinance_history(ticker: str, period: str = "1y"):
    try:
        df = yf.download(ticker, period=period, interval="1d")
        if df.empty:
            return None
        df.reset_index(inplace=True)
        df.rename(
            columns={"Date": "date", "Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"},
            inplace=True
        )
        return df
    except Exception as e:
        return None
