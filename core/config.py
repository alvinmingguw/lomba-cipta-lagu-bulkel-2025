import streamlit as st
import pandas as pd
from typing import List

# =========================
# Configuration Loading & Parsing
# =========================

@st.cache_data(ttl=300)
def load_all_configs_and_data(_sh):
    """
    Loads all configuration sheets (config, judges, rubrik, keywords, variants)
    and the main data sheets (songs, penilaian) from the Google Sheet object.
    Returns a tuple of DataFrames and Worksheet objects.
    """
    def _get_df(name):
        try:
            ws = _sh.worksheet(name)
            return pd.DataFrame(ws.get_all_records())
        except Exception:
            return pd.DataFrame()

    def _get_ws(name):
        try:
            return _sh.worksheet(name)
        except Exception:
            return None

    cfg_df      = _get_df("Config")
    judges_df   = _get_df("Juri")
    rubrik_df   = _get_df("Rubrik")
    kw_df       = _get_df("Keywords")
    variants_df = _get_df("Variants")
    songs_df    = _get_df("Songs")
    win_df      = _get_df("Winners") # Manual winners list

    # Worksheets needed for writing/indexing
    pen_ws = _get_ws("Penilaian")
    idx_ws = _get_ws("Index")
    idx_df = _get_df("Index") # Also get DF for reading

    return cfg_df, judges_df, rubrik_df, kw_df, variants_df, songs_df, pen_ws, win_df, idx_ws, idx_df

def parse_rubrik(df: pd.DataFrame) -> list[dict]:
    """Parses the Rubrik DataFrame into a list of dictionaries."""
    if df is None or df.empty:
        return []
    out = []
    for _, r in df.iterrows():
        key = str(r.get("key", "")).strip()
        if not key:
            continue
        desc = {}
        for i in range(1, 6):
            d = str(r.get(f"desc{i}", "") or "").strip()
            if d:
                desc[i] = d
        out.append({
            "key": key,
            "aspek": str(r.get("aspek", key)).strip(),
            "bobot": float(r.get("bobot", 0)),
            "min": int(r.get("min", 1)),
            "max": int(r.get("max", 5)),
            "desc": desc,
        })
    return out

def parse_variants(df: pd.DataFrame) -> dict:
    """Parses the Variants DataFrame into a dictionary for renaming columns."""
    if df is None or df.empty:
        return {}
    return {str(r["variant"]).strip(): str(r["key"]).strip() for _, r in df.iterrows() if r.get("variant") and r.get("key")}

def parse_keywords(df: pd.DataFrame) -> tuple[list, list]:
    """Parses the Keywords DataFrame into phrases and keywords lists."""
    if df is None or df.empty:
        return [], []
    phrases = df[df["type"] == "phrase"][["keyword", "weight"]].values.tolist()
    keywords = df[df["type"] == "keyword"][["keyword", "weight"]].values.tolist()
    return phrases, keywords

def cfg_get(df: pd.DataFrame, key: str, default=None, cast_type=None):
    """Gets a specific configuration value by key from the Config DataFrame."""
    if df is None or df.empty or "key" not in df.columns or key not in set(df["key"]):
        return default
    val = df[df["key"] == key]["value"].iloc[0]
    if cast_type:
        try:
            if cast_type == bool:
                return str(val).strip().lower() in ("true", "1", "yes", "ya")
            return cast_type(val)
        except (ValueError, TypeError):
            return default
    return val

def cfg_list(df: pd.DataFrame, key: str, default: str) -> List[str]:
    """Gets a comma-separated config value as a list of strings."""
    raw = cfg_get(df, key, default, str)
    return [item.strip() for item in raw.split(",") if item.strip()]
