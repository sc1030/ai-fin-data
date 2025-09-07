# 📊 AI Financial Data Platform

An interactive financial data platform built with **Python**, **Streamlit**, and **NLP**.  
It allows users to parse & extract data from PDFs/Excel files, automate financial models, fetch live market data, analyze news, and generate insightful dashboards.  

---

## 🚀 Features
- **Data Parsing & Extraction**  
  - Parse **PDF** and **Excel** financial reports.  
  - Automate updates in multi-sheet Excel models.  

- **Automation**  
  - Automates repetitive financial workflows and calculations.  

- **Interactive Dashboard**  
  - Streamlit-powered visualizations (charts, graphs, summary tables).  
  - Real-time updates and financial insights.  

- **API Integrations**  
  - Market data API for live prices.  
  - News API for financial news sentiment.  

- **NLP Capabilities**  
  - Text summarization of financial reports.  
  - Sentiment analysis of news headlines.  

---

## 🛠️ Tech Stack
- **Frontend / Dashboard:** [Streamlit](https://streamlit.io/)  
- **Backend / Services:** Python (Flask-like modular structure)  
- **Data Parsing:** `pandas`, `openpyxl`, `pdfplumber`  
- **APIs:** Finance & News APIs  
- **NLP:** HuggingFace Transformers / NLTK / TextRank  

---


---

## ⚡ Quick Start

1. Clone this repository:
   ```bash
   git clone https://github.com/sc1030/ai-fin-data.git
   cd ai-fin-data
python -m venv venv
source venv/bin/activate   # On Mac/Linux
venv\Scripts\activate      # On Windows
pip install -r requirements.txt
streamlit run streamlit_app.py
