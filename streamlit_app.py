# streamlit_app.py
from dotenv import load_dotenv
load_dotenv()

import os
import streamlit as st
import pandas as pd
from datetime import datetime
from app.db import init_db, SessionLocal
from app.models import SourceFile, Report, FinancialData
from app.data_parsing.pdf_parser import parse_pdf
from app.data_parsing.excel_parser import parse_excel
from app.nlp.summarizer import summarize_text
from app.services.finance_api import fetch_yfinance_history
from app.services.news_api import fetch_news
from app.automation import start_scheduler
import plotly.express as px
from streamlit_option_menu import option_menu

# ---------------------------
# INIT
# ---------------------------
st.set_page_config(page_title="AI Financial Data Platform", layout="wide")
init_db()

# ---------------------------
# CUSTOM CSS THEME
# ---------------------------
st.markdown("""
<style>
.main { background-color: #f4faff; }
[data-testid="stHorizontalBlock"] {
    background: linear-gradient(90deg, #0d6efd, #004080);
    border-radius: 12px;
    padding: 10px 20px;
    margin-bottom: 20px;
}
.st-emotion-cache-1v0mbdj {color: white !important; font-weight: 600;}
.st-emotion-cache-1v0mbdj:hover {color: #d9eaff !important;}
div[data-testid="stMetricValue"] { color: #004080; font-size: 22px; font-weight: 700; }
div[data-testid="stMetricLabel"] { color: #0d6efd; font-weight: 500; }
h1, h2, h3 { color: #004080; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# NAVBAR
# ---------------------------
selected = option_menu(
    menu_title=None,
    options=["Dashboard", "Upload & Parse", "Market & News", "Scheduler", "Database"],
    icons=["speedometer", "upload", "graph-up", "clock", "database"],
    orientation="horizontal",
)

# ---------------------------
# HELPER FUNCTIONS
# ---------------------------
def save_report_to_db(title, content, summary):
    db = SessionLocal()
    r = Report(title=title, content=content, summary=summary)
    db.add(r)
    db.commit()
    db.refresh(r)
    db.close()
    return r

def save_sourcefile(filename, filetype, metadata=None):
    db = SessionLocal()
    s = SourceFile(filename=filename, file_type=filetype, file_metadata=metadata)
    db.add(s)
    db.commit()
    db.refresh(s)
    db.close()
    return s

def save_financial_dataframe(ticker, df):
    if df is None or df.empty:
        return 0
    db = SessionLocal()
    inserted = 0
    for _, row in df.iterrows():
        date_val = None
        if "date" in row:
            date_val = pd.to_datetime(row["date"]).to_pydatetime()
        elif "Date" in row:
            date_val = pd.to_datetime(row["Date"]).to_pydatetime()
        fd = FinancialData(
            ticker=ticker,
            date=date_val,
            open=row.get("open") or row.get("Open"),
            high=row.get("high") or row.get("High"),
            low=row.get("low") or row.get("Low"),
            close=row.get("close") or row.get("Close"),
            volume=row.get("volume") or row.get("Volume")
        )
        db.add(fd)
        inserted += 1
    db.commit()
    db.close()
    return inserted

# ---------------------------
# DASHBOARD
# ---------------------------
if selected == "Dashboard":
    st.title("📊 Dashboard Overview")
    db = SessionLocal()
    reports_count = db.query(Report).count()
    tickers = db.query(FinancialData.ticker).distinct().count()
    latest_news = 5
    db.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Reports", reports_count)
    col2.metric("Tickers Tracked", tickers)
    col3.metric("Latest News", latest_news)

    st.markdown("---")
    st.subheader("📈 Recent Market Snapshot")
    db = SessionLocal()
    rows = db.query(FinancialData).order_by(FinancialData.date.desc()).limit(100).all()
    db.close()
    if rows:
        df = pd.DataFrame([{"date": r.date, "ticker": r.ticker, "close": r.close} for r in rows])
        fig = px.line(df, x="date", y="close", color="ticker", title="Recent Prices")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No market data yet. Go to Market & News tab to fetch.")

# ---------------------------
# UPLOAD & PARSE
# ---------------------------
elif selected == "Upload & Parse":
    st.header("📂 Upload & Parse Financial Reports")
    uploaded_file = st.file_uploader("Upload PDF/Excel/CSV", type=['pdf','xlsx','xls','csv'])
    
    if uploaded_file:
        fname = uploaded_file.name
        file_bytes = uploaded_file.read()
        try:
            # PDF
            if fname.lower().endswith(".pdf"):
                parsed = parse_pdf(file_bytes)
                if not parsed["text"].strip():
                    st.warning("⚠️ No text extracted from this PDF.")
                else:
                    st.text_area("Extracted Text", value=parsed["text"][:3000], height=250)
                if parsed["tables"]:
                    for i, df in enumerate(parsed["tables"]):
                        st.write(f"Table {i+1}", df.head())
                        # Save table to FinancialData if columns exist
                        if set(["date","open","high","low","close","volume"]).issubset([c.lower() for c in df.columns]):
                            inserted = save_financial_dataframe(fname, df)
                            st.success(f"✅ Table {i+1}: {inserted} rows saved to database")
                else:
                    st.info("No tables found in PDF.")
                if st.button("Save Report to DB"):
                    summary = summarize_text(parsed["text"], max_length=150)
                    save_sourcefile(fname, "pdf")
                    save_report_to_db(fname, parsed["text"], summary)
                    st.success("✅ Report saved")
            
            # Excel / CSV
            else:
                try:
                    sheets = parse_excel(file_bytes, fname)
                    if not sheets:
                        st.warning("⚠️ No sheets found in the uploaded Excel/CSV file.")
                    for name, df in sheets.items():
                        st.write("Sheet:", name)
                        st.dataframe(df.head())
                        # Save sheet to FinancialData if columns exist
                        lower_cols = [c.lower() for c in df.columns]
                        if set(["date","open","high","low","close","volume"]).issubset(lower_cols):
                            inserted = save_financial_dataframe(name, df)
                            st.success(f"✅ Sheet '{name}': {inserted} rows saved to database")
                    if st.button("Save Excel metadata"):
                        save_sourcefile(fname, "excel", metadata={"sheets": list(sheets.keys())})
                        st.success("✅ Excel metadata saved")
                except Exception as e:
                    st.error(f"❌ Failed to parse Excel/CSV: {str(e)}")
        except Exception as e:
            st.error(f"❌ Failed to process file: {str(e)}")

# ---------------------------
# MARKET & NEWS
# ---------------------------
elif tab == "Market & News":
    st.header("Market data & News")
    col1, col2 = st.columns(2)
    with col1:
        ticker = st.text_input("Ticker (e.g. AAPL, MSFT, TCS.NS)", value="AAPL")
        period = st.selectbox("Period", ["1mo","3mo","6mo","1y","2y","5y"], index=3)
        if st.button("Fetch market data"):
            df = fetch_yfinance_history(ticker, period=period)
            if df is None or df.empty:
                st.error("No data")
            else:
                st.success(f"Fetched {len(df)} rows for {ticker}")
                st.dataframe(df.head())
                fig = px.line(df, x='Date', y='Close', title=f"{ticker} Close Price")
                st.plotly_chart(fig, use_container_width=True)
                if st.button("Save market data to DB"):
                    n = save_financial_dataframe(ticker, df)
                    st.info(f"Inserted ~{n} rows")

    with col2:
        query = st.text_input("News query", "stocks")
        if st.button("Fetch News"):
            news = fetch_news(query, page_size=5)
            if "error" in news:
                st.error(news["error"])
            else:
                for art in news.get("articles", []):
                    st.subheader(art["title"])
                    st.caption(art["source"])
                    st.write(art["description"])
                    st.markdown(f"[Read more]({art['url']})")
                    st.markdown("---")

# ---------------------------
# SCHEDULER
# ---------------------------
elif selected == "Scheduler":
    st.header("⏰ Scheduler")
    tickers_text = st.text_input("Tickers (comma separated)", "AAPL,MSFT")
    minutes = st.number_input("Interval (minutes)", min_value=10, value=60)
    if st.button("Start Scheduler"):
        tickers = [t.strip() for t in tickers_text.split(",") if t.strip()]
        def grab_and_save(tk):
            df = fetch_yfinance_history(tk, period="1mo")
            if df is not None and not df.empty:
                save_financial_dataframe(tk, df)
        start_scheduler(grab_and_save, tickers, minutes=minutes)
        st.success(f"Scheduler started for {', '.join(tickers)}")

# ---------------------------
# DATABASE
# ---------------------------
elif selected == "Database":
    st.header("🗄️ Database Preview")
    db = SessionLocal()

    st.subheader("Recent Reports")
    reports = db.query(Report).order_by(Report.created_at.desc()).limit(5).all()
    for r in reports:
        st.write(f"**{r.title}** – {r.created_at}")
        st.caption(r.summary)

    st.subheader("Recent Financial Data")
    rows = db.query(FinancialData).order_by(FinancialData.date.desc()).limit(10).all()
    if rows:
        df = pd.DataFrame([{
            "date": r.date,
            "ticker": r.ticker,
            "open": r.open,
            "close": r.close,
            "volume": r.volume
        } for r in rows])
        st.dataframe(df)
    else:
        st.info("No financial data yet.")
    db.close()
