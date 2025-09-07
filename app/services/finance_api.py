import yfinance as yf
import pandas as pd

def fetch_yfinance_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """
    Returns a DataFrame with Date, Open, High, Low, Close, Volume for the given ticker
    """
    df = yf.download(
        tickers=ticker,
        period=period,
        interval=interval,
        progress=False,
        auto_adjust=False  # 👈 explicitly set to avoid FutureWarning
    )
    
    if df.empty:
        return df

    # Reset index so Date is a column
    df = df.reset_index()

    # Handle MultiIndex (e.g., ('Close', 'AAPL')) → 'Close'
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0].lower() for col in df.columns]
    else:
        df.columns = [str(c).lower() for c in df.columns]

    # Keep only the needed columns if present
    keep = ["date", "open", "high", "low", "close", "volume"]
    df = df[[c for c in keep if c in df.columns]]

    return df
