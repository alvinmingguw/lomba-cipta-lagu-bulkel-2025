import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from gspread.utils import rowcol_to_a1
import datetime
from zoneinfo import ZoneInfo

# =========================
# Google Sheet Client & Helpers
# =========================

@st.cache_resource(ttl=600)
def open_sheet():
    """Opens a connection to the Google Sheet using service account credentials."""
    creds_json = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(
        creds_json,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    return gspread.authorize(creds).open_by_key(st.secrets["sheet_key"])

def _ensure_ws(sh, name, headers=None):
    """Ensures a worksheet with the given name and headers exists."""
    try:
        ws = sh.worksheet(name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=name, rows="100", cols="20")
        if headers:
            ws.append_row(headers)
    return ws

@st.cache_data(ttl=300)
def ws_to_df(ws):
    """Converts a worksheet to a DataFrame."""
    if not ws:
        return pd.DataFrame()
    return pd.DataFrame(ws.get_all_records())

def ensure_headers(ws, headers: list[str]):
    """Ensures the worksheet has the specified headers, adding any that are missing."""
    if not headers:
        return []
    try:
        existing = ws.row_values(1)
    except gspread.exceptions.APIError:
        existing = []

    if not existing:
        ws.update("A1", [headers])
        return headers

    new_headers = list(existing)
    appended = False
    for h in headers:
        if h not in new_headers:
            new_headers.append(h)
            appended = True

    if appended:
        ws.update("A1", [new_headers])

    return new_headers

@st.cache_data(ttl=120)
def get_penilaian_ws():
    """Gets the 'Penilaian' worksheet, ensuring it exists."""
    sh = open_sheet()
    return _ensure_ws(sh, "Penilaian", ["timestamp", "juri", "judul", "author", "total"])

@st.cache_data(ttl=120, show_spinner="Membaca data penilaian...")
def get_penilaian_df(ws=None):
    """
    Gets the 'Penilaian' worksheet as a DataFrame.
    Uses a cached worksheet object if provided.
    """
    if ws is None:
        ws = get_penilaian_ws()
    return ws_to_df(ws)


# =========================
# Penilaian I/O
# =========================
def find_pen_row_index_df(pen_df: pd.DataFrame, juri: str, judul: str, author: str) -> int | None:
    """Finds the row index for a specific entry in the Penilaian DataFrame."""
    if pen_df.empty:
        return None
    df = pen_df.copy()
    m = (df["juri"] == juri) & (df["judul"] == judul)
    if "author" in df.columns:
        m &= (df["author"].fillna("") == (author or ""))
    idx = df.index[m].tolist()
    return (idx[0] + 2) if idx else None

def load_existing_scores_for_df(pen_df: pd.DataFrame, juri: str, judul: str, author: str, rubrik_keys: list, variants: dict):
    """Loads existing scores for a specific entry from the Penilaian DataFrame."""
    if pen_df is None or pen_df.empty:
        return {}
    df = pen_df.rename(columns=lambda c: variants.get(c, c)).copy()
    q = (df["juri"] == juri) & (df["judul"] == judul)
    if "author" in df.columns:
        df = df[q & (df["author"].fillna("") == (author or ""))]
    else:
        df = df[q]
    if df.empty:
        return {}
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.sort_values("timestamp").tail(1)
    row = df.iloc[0]
    out = {}
    for k in rubrik_keys:
        v = row.get(k)
        if v is None or str(v).strip() == "":
            continue
        try:
            out[k] = int(float(v))
        except (ValueError, TypeError):
            pass
    return out

def load_existing_scores_for(juri, judul, author, rubrik_keys, variants):
    ws_pen2 = _ensure_ws(open_sheet(), "Penilaian", ["timestamp","juri","judul","author","total"])
    df = ws_to_df(ws_pen2)
    if df.empty:
        return {}
    df = df.rename(columns=lambda c: variants.get(c, c))
    q = (df["juri"] == juri) & (df["judul"] == judul)
    if "author" in df.columns:
        df1 = df[q & (df["author"].fillna("") == (author or ""))]
        if df1.empty:
            df1 = df[q]
    else:
        df1 = df[q]
    if df1.empty:
        return {}
    if "timestamp" in df1.columns:
        df1["timestamp"] = pd.to_datetime(df1["timestamp"], errors="coerce")
        df1 = df1.sort_values("timestamp").tail(1)
    row = df1.iloc[0]
    out = {}
    for k in rubrik_keys:
        v = row.get(k)
        if v is None or str(v).strip() == "":
            continue
        try:
            out[k] = int(float(v))
        except (ValueError, TypeError):
            pass
    return out

def update_pen_row(ws, headers: list, rownum: int, juri: str, judul: str, author: str, scores: dict, total: float):
    """Updates a specific row in the Penilaian worksheet."""
    row = {h: "" for h in headers}
    row["timestamp"] = datetime.datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")
    row["juri"] = juri
    row["judul"] = judul
    row["author"] = author
    for k, v in scores.items():
        if k in headers:
            row[k] = v
    row["total"] = round(float(total), 2)
    ws.update(f"{rownum}:{rownum}", [[row[h] for h in headers]], value_input_option="USER_ENTERED")

def ensure_pen_headers(ws, rubrik_keys: list):
    """Ensures the Penilaian worksheet has all required headers."""
    headers = ["timestamp", "juri", "judul", "author"] + rubrik_keys + ["total"]
    return ensure_headers(ws, headers)

def append_pen_row(ws, headers: list, juri: str, judul: str, author: str, scores: dict, total: float):
    """Appends a new row to the Penilaian worksheet."""
    row = {h: "" for h in headers}
    row["timestamp"] = datetime.datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")
    row["juri"] = juri
    row["judul"] = judul
    row["author"] = author
    for k, v in scores.items():
        if k in headers:
            row[k] = v
    row["total"] = round(float(total), 2)
    ws.append_row([row[h] for h in headers], value_input_option="USER_ENTERED")
