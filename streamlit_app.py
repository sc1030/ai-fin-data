company_locations = {
    "AAPL": "37.3349,-122.0090",   # Apple HQ (Cupertino, CA)
    "MSFT": "47.6426,-122.1366",   # Microsoft HQ (Redmond, WA)
    "GOOGL": "37.4220,-122.0841",  # Google HQ (Mountain View, CA)
    "AMZN": "47.6220,-122.3360",   # Amazon HQ (Seattle, WA)
    "TSLA": "37.3947,-122.1500",   # Tesla HQ (Palo Alto, CA)
    "TCS.NS": "19.0760,72.8777"    # Tata Consultancy (Mumbai, India)
}
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

import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
import streamlit as st
import pandas as pd
import plotly.express as px
import folium
from streamlit_folium import st_folium
from st_aggrid import AgGrid, GridOptionsBuilder
# ---------------------------
# CUSTOM CSS THEME
# ---------------------------
st.markdown("""
<style>
/* Background */
.main {
    background-color: #f4faff;
}

/* Navbar */
[data-testid="stHorizontalBlock"] {
    background: linear-gradient(90deg, #0d6efd, #004080);
    border-radius: 12px;
    padding: 10px 20px;
    margin-bottom: 20px;
}
.st-emotion-cache-1v0mbdj {color: white !important; font-weight: 600;}
.st-emotion-cache-1v0mbdj:hover {color: #d9eaff !important;}

/* Cards */
div[data-testid="stMetricValue"] {
    color: #004080;
    font-size: 22px;
    font-weight: 700;
}
div[data-testid="stMetricLabel"] {
    color: #0d6efd;
    font-weight: 500;
}

/* Headers */
h1, h2, h3 {
    color: #004080;
    font-weight: 700;
}
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

def save_financial_dataframe(ticker, df, location=None):
    if df is None or df.empty:
        return 0
    db = SessionLocal()
    inserted = 0
    for _, row in df.reset_index().iterrows():
        # Ensure correct datetime
        if "date" in row:
            date_val = pd.to_datetime(row["date"])
        elif "Date" in row:
            date_val = pd.to_datetime(row["Date"])
        else:
            continue

        # Convert to Python datetime safely
        if isinstance(date_val, pd.Series):
            date_val = date_val.iloc[0]
        if hasattr(date_val, "to_pydatetime"):
            date_val = date_val.to_pydatetime()

        try:
            fd = FinancialData(
                ticker=ticker,
                date=date_val,
                open=float(row.get("Open", row.get("open", 0))),
                high=float(row.get("High", row.get("high", 0))),
                low=float(row.get("Low", row.get("low", 0))),
                close=float(row.get("Close", row.get("close", 0))),
                volume=float(row.get("Volume", row.get("volume", 0))),
                location=location
            )
            db.add(fd)
            inserted += 1
        except Exception as e:
            print(f"⚠️ Skipped row due to error: {e}")
    db.commit()
    db.close()
    return inserted

# ---------------------------
# DASHBOARD
# ---------------------------
if selected == "Dashboard":
    st.title("📊 Dashboard Overview")

    # Summary cards & KPIs
    db = SessionLocal()
    reports_count = db.query(Report).count()
    tickers = db.query(FinancialData.ticker).distinct().count()
    latest_news = 5
    rows = db.query(FinancialData).order_by(FinancialData.date.desc()).limit(300).all()
    db.close()

    # Prepare DataFrame for KPIs
    if rows:
        df_kpi = pd.DataFrame([{
            "date": r.date,
            "ticker": r.ticker,
            "close": r.close,
            "volume": r.volume
        } for r in rows])
        avg_close = df_kpi["close"].mean()
        # Highest Gainer: ticker with max close - min close
        gainers = df_kpi.groupby("ticker")["close"].agg(["first", "last"])
        gainers["gain"] = gainers["last"] - gainers["first"]
        highest_gainer = gainers["gain"].idxmax() if not gainers.empty else "-"
        most_active = df_kpi.groupby("ticker")["volume"].sum().idxmax() if not df_kpi.empty else "-"
    else:
        avg_close = 0
        highest_gainer = "-"
        most_active = "-"

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Reports", reports_count)
    col2.metric("Tickers Tracked", tickers)
    col3.metric("Latest News", latest_news)
    col4.metric("Avg Close Price", f"{avg_close:,.2f}")
    col5.metric("Highest Gainer", highest_gainer)
    col6.metric("Most Active Stock", most_active)

    st.markdown("---")
    st.subheader("� Financial Data Summary Table")
    db = SessionLocal()
    rows = db.query(FinancialData).order_by(FinancialData.date.desc()).limit(300).all()
    db.close()
    if rows:
        df = pd.DataFrame([{
            "date": r.date,
            "ticker": r.ticker,
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "volume": r.volume,
            "location": getattr(r, "location", None)
        } for r in rows])

        # Sortable, filterable table
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination()
        gb.configure_default_column(editable=False, groupable=True)
        gb.configure_side_bar()
        gridOptions = gb.build()
        AgGrid(df, gridOptions=gridOptions, enable_enterprise_modules=True)

        st.markdown("---")
        st.subheader("📊 Charts & Graphs")
        chart_type = st.selectbox("Select Chart Type", ["Line", "Bar", "Pie", "Time-Series"])
        if chart_type == "Line":
            fig = px.line(df, x="date", y="close", color="ticker", title="Line Chart - Close Price Over Time")
        elif chart_type == "Bar":
            fig = px.bar(df, x="ticker", y="volume", title="Bar Chart - Volume by Ticker")
        elif chart_type == "Pie":
            fig = px.pie(df, names="ticker", values="close", title="Pie Chart - Close Price Distribution")
        elif chart_type == "Time-Series":
            fig = px.line(df, x="date", y="close", color="ticker", title="Time-Series - Close Price")
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("🗺 Interactive Map")
        if "location" in df.columns and df["location"].notna().any():
            m = folium.Map(location=[20.5937, 78.9629], zoom_start=4)
            for _, row in df.iterrows():
                if pd.notna(row.get("location")):
                    try:
                        lat, lon = map(float, str(row["location"]).split(","))
                        folium.Marker([lat, lon], popup=f"{row['ticker']} - {row['close']}").add_to(m)
                    except:
                        pass
            st_folium(m, width=700, height=500)
        else:
            st.info("No geolocation data found for mapping.")
    else:
        st.info("No market data yet. Go to Market & News tab to fetch.")

# ---------------------------
# UPLOAD
# ---------------------------
elif selected == "Upload & Parse":
    st.header("📂 Upload & Parse Financial Reports")
    uploaded_file = st.file_uploader("Upload PDF/Excel/CSV", type=['pdf','xlsx','xls','csv'])
    if uploaded_file:
        fname = uploaded_file.name
        file_bytes = uploaded_file.read()

        if fname.lower().endswith(".pdf"):
            parsed = parse_pdf(file_bytes)
            st.text_area("Extracted Text", value=parsed["text"][:3000], height=250)
            if parsed["tables"]:
                for i, df in enumerate(parsed["tables"]):
                    st.write(f"Table {i+1}", df.head())
            if st.button("Save Report to DB"):
                summary = summarize_text(parsed["text"], max_length=150)
                save_sourcefile(fname, "pdf")
                save_report_to_db(fname, parsed["text"], summary)
                st.success("✅ Report saved")

        else:
            sheets = parse_excel(file_bytes, fname)
            for name, df in sheets.items():
                st.write("Sheet:", name)
                st.dataframe(df.head())
            if st.button("Save Excel metadata"):
                save_sourcefile(fname, "excel", metadata={"sheets": list(sheets.keys())})
                st.success("✅ Excel metadata saved")

# ---------------------------
# MARKET & NEWS
# ---------------------------
elif selected == "Market & News":
    st.subheader("📈 Market Data & 📰 News")

tickers_input = st.text_input(
    "Tickers (comma separated, e.g. AAPL, MSFT, TCS.NS)",
    "AAPL, MSFT, TCS.NS"
)
period = st.selectbox("Period", ["1mo", "3mo", "6mo", "1y", "5y"], index=3)

if st.button("Fetch Market Data"):
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]
    combined = pd.DataFrame()

    for tk in tickers:
        try:
            import yfinance as yf
            df_t = yf.download(tk, period=period, interval="1d")

            if not df_t.empty:
                df_t = df_t.reset_index()
                df_t["ticker"] = tk
                df_t.rename(
                    columns={
                        "Date": "date",
                        "Open": "open",
                        "High": "high",
                        "Low": "low",
                        "Close": "close",
                        "Adj Close": "adj_close",
                        "Volume": "volume"
                    },
                    inplace=True
                )
                combined = pd.concat([combined, df_t], ignore_index=True)
                loc = company_locations.get(tk, "37.77,-122.42")
                save_financial_dataframe(tk, df_t, location=loc)
            else:
                st.warning(f"⚠️ No data returned for {tk}")
        except Exception as e:
            st.error(f"❌ Failed to fetch {tk}: {e}")

    if not combined.empty:
        st.write("📊 Market Data Sample", combined.head())
        st.write("📈 Summary Statistics")
        stats = combined.groupby("ticker")["close"].agg(
            ["mean", "min", "max"]
        ).reset_index()
        stats.rename(
            columns={"mean": "Average Close", "min": "Min Close", "max": "Max Close"},
            inplace=True
        )
        st.dataframe(stats)
        try:
            fig = px.line(
                combined,
                x="date",
                y="close",
                color="ticker",
                title="Close Price Over Time"
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"⚠️ Market data could not be plotted: {e}")
    else:
        st.warning("⚠️ No market data could be combined for plotting.")
    st.markdown("---")

    st.subheader("📰 Latest News by Ticker")
    for tk in [t.strip().upper() for t in tickers_input.split(",") if t.strip()]:
        st.write(f"### {tk} News")
        news = fetch_news(tk, page_size=3)
        if not news or "error" in news:
            st.error(news.get("error", f"Failed to fetch news for {tk}."))
        else:
            for art in news.get("articles", []):
                st.markdown(f"**{art['title']}** ({art['source']})")
                st.caption(art.get("publishedAt", ""))
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
