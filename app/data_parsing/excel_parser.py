import pandas as pd
from io import BytesIO
import os

def parse_excel(file_bytes, filename):
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".csv":
        df = pd.read_csv(BytesIO(file_bytes))
        return {"CSV_Data": df}

    elif ext in [".xls", ".xlsx"]:
        return pd.read_excel(BytesIO(file_bytes), sheet_name=None, engine="openpyxl")

    else:
        raise ValueError("Unsupported file format. Please upload .csv, .xls, or .xlsx")
