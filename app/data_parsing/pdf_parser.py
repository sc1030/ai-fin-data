import pandas as pd
import pdfplumber
from io import BytesIO

def parse_pdf(file_bytes):
    text = ""
    tables = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
            tables.extend(page.extract_tables())
    dfs = [pd.DataFrame(tbl[1:], columns=tbl[0]) for tbl in tables if tbl]
    return {"text": text, "tables": dfs}
