import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
from typing import List, Dict, Any
import datetime
from zoneinfo import ZoneInfo

from .utils import _patch_sa

# =========================
# Google clients (cached)
# =========================
@st.cache_resource
def _gs_client() -> gspread.client.Client:
    """Initializes and caches the gspread client."""
    info = _patch_sa(st.secrets.get("gcp_service_account"))
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)

def open_sheet() -> gspread.Spreadsheet:
    """Opens the Google Sheet using the ID from Streamlit secrets."""
    return _gs_client().open_by_key(st.secrets["gsheet_id"])

@st.cache_resource
def get_penilaian_ws() -> gspread.Worksheet:
    """
    Gets the 'Penilaian' worksheet object, caching it as a resource.
    """
    sh = open_sheet()
    return _ensure_ws(sh, "Penilaian")

def get_penilaian_df() -> pd.DataFrame:
    """

    Retrieves the 'Penilaian' DataFrame, using st.session_state as a per-session cache
    to avoid repeated GSheet API calls on minor interactions.
    """
    # Use a more robust key to avoid clashes
    cache_key = 'penilaian_df_cached_v1'
    if cache_key not in st.session_state or st.session_state[cache_key] is None:
        ws = get_penilaian_ws()
        st.session_state[cache_key] = ws_to_df(ws)
    return st.session_state[cache_key]

# =========================
# Worksheet utils
# =========================
def _ensure_ws(sh: gspread.Spreadsheet, title: str, headers: List[str] = None, rows: int = 1000, cols: int = 26) -> gspread.Worksheet:
    """Ensures a worksheet with the given title and headers exists."""
    try:
        ws = sh.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=str(rows), cols=str(max(cols, (len(headers) if headers else 0) + 2)))
        if headers:
            ws.update("A1", [headers])
    return ws

def ws_to_df(ws: gspread.Worksheet) -> pd.DataFrame:
    """Converts a worksheet to a pandas DataFrame."""
    vals = ws.get_all_values()
    if not vals:
        return pd.DataFrame()
    hdr, body = vals[0], vals[1:]
    return pd.DataFrame(body, columns=hdr) if body else pd.DataFrame(columns=hdr)

def ensure_headers(ws: gspread.Worksheet, headers: List[str]) -> List[str]:
    """Ensures the worksheet has the specified headers, adding any missing ones."""
    existing = ws.row_values(1)
    if existing == headers:
        return headers

    # Find headers that are in the sheet but not in our target list
    extras = [h for h in existing if h and h not in headers]
    final_headers = headers + extras

    # Update the sheet only if the headers are actually different
    if final_headers != existing:
        ws.update("A1", [final_headers])

    return final_headers

# =========================
# Load all data from GSheet
# =========================
@st.cache_data(ttl=180, show_spinner="Memuat data dari Google Sheets...")
def load_all_sheets() -> tuple:
    """
    Loads all necessary worksheets and DataFrames from the Google Sheet.
    Caches the result for 3 minutes to improve performance.
    """
    sh = open_sheet()

    # Define expected sheets and their headers
    sheet_specs = {
        "Config": ["key", "value"],
        "Judges": ["juri"],
        "Rubrik": ["key", "aspek", "bobot", "min_score", "max_score", "desc_5", "desc_4", "desc_3", "desc_2", "desc_1"],
        "Keywords": ["type", "text", "weight"],
        "Variants": ["from_name", "to_key"],
        "Songs": ["judul", "pengarang", "audio_path", "notasi_path", "syair_path", "lirik_text", "chords_list", "full_score", "syair_chord", "Alias"],
        "Penilaian": ["timestamp", "juri", "judul", "author", "total"],
        "Winners": ["rank", "judul", "catatan"],
        "DriveIndex": ["name", "id", "mimeType", "modifiedTime", "parentHint"]
    }

    worksheets = {name: _ensure_ws(sh, name, headers) for name, headers in sheet_specs.items()}

    # Return a mix of DataFrames and Worksheet objects as needed
    return (
        sh,
        ws_to_df(worksheets["Config"]),
        ws_to_df(worksheets["Judges"]),
        ws_to_df(worksheets["Rubrik"]),
        ws_to_df(worksheets["Keywords"]),
        ws_to_df(worksheets["Variants"]),
        ws_to_df(worksheets["Songs"]),
        worksheets["Penilaian"],  # Return the worksheet object for direct interaction
        ws_to_df(worksheets["Winners"]),
        worksheets["DriveIndex"], # Return worksheet object for direct appends
        ws_to_df(worksheets["DriveIndex"])
    )

# =========================
# Penilaian I/O
# =========================
def find_pen_row_index_df(pen_df: pd.DataFrame, juri: str, judul: str, author: str) -> int | None:
    """Finds the row index for a given assessment in the DataFrame."""
    if pen_df.empty:
        return None

    # Create boolean masks for filtering
    is_juri = pen_df["juri"] == juri
    is_judul = pen_df["judul"] == judul

    # Handle author matching, considering it might be an empty string
    if "author" in pen_df.columns:
        is_author = pen_df["author"].fillna("") == (author or "")
        mask = is_juri & is_judul & is_author
    else:
        mask = is_juri & is_judul

    idx = pen_df.index[mask].tolist()
    # Return the GSheet row number (index + 2)
    return (idx[0] + 2) if idx else None

def load_existing_scores_for_df(pen_df: pd.DataFrame, juri: str, judul: str, author: str, rubrik_keys: List[str], variants: Dict[str, str]) -> Dict[str, int]:
    """Loads existing scores for a specific entry from the Penilaian DataFrame."""
    if pen_df is None or pen_df.empty:
        return {}

    df = pen_df.rename(columns=lambda c: variants.get(c, c)).copy()

    q_juri = df["juri"] == juri
    q_judul = df["judul"] == judul

    if "author" in df.columns:
        q_author = df["author"].fillna("") == (author or "")
        df_filtered = df[q_juri & q_judul & q_author]
    else:
        df_filtered = df[q_juri & q_judul]

    if df_filtered.empty:
        return {}

    # Get the latest entry based on timestamp if available
    if "timestamp" in df_filtered.columns:
        df_filtered["timestamp"] = pd.to_datetime(df_filtered["timestamp"], errors="coerce")
        latest_row = df_filtered.sort_values("timestamp", ascending=False).iloc[0]
    else:
        latest_row = df_filtered.iloc[-1]

    scores = {}
    for key in rubrik_keys:
        value = latest_row.get(key)
        if pd.notna(value) and str(value).strip() != "":
            try:
                scores[key] = int(float(value))
            except (ValueError, TypeError):
                pass  # Ignore values that can't be converted to int
    return scores

def update_pen_row(ws: gspread.Worksheet, headers: List[str], rownum: int, juri: str, judul: str, author: str, scores: Dict[str, int], total: float):
    """Updates a specific row in the Penilaian worksheet."""
    row_data = {h: "" for h in headers}
    row_data.update({
        "timestamp": datetime.datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S"),
        "juri": juri,
        "judul": judul,
        "author": author,
        "total": round(float(total), 2)
    })
    row_data.update(scores)

    # Build the list in the correct header order
    final_row = [row_data.get(h, "") for h in headers]
    ws.update(f"A{rownum}", [final_row], value_input_option="USER_ENTERED")

def append_pen_row(ws: gspread.Worksheet, headers: List[str], juri: str, judul: str, author: str, scores: Dict[str, int], total: float):
    """Appends a new row to the Penilaian worksheet."""
    row_data = {h: "" for h in headers}
    row_data.update({
        "timestamp": datetime.datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S"),
        "juri": juri,
        "judul": judul,
        "author": author,
        "total": round(float(total), 2)
    })
    row_data.update(scores)

    # Build the list in the correct header order
    final_row = [row_data.get(h, "") for h in headers]
    ws.append_row(final_row, value_input_option="USER_ENTERED")
