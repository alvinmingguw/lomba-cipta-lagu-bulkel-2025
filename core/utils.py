import pandas as pd
import re

# Helper to hash dataframes for Streamlit caching
HASH_DF = {pd.DataFrame: lambda df: df.to_csv(index=False)}

# Regex to check if a string is a URL
URL_RE = re.compile(r"^https?://", re.I)

def is_url(x: str) -> bool:
    """Checks if a string is a URL."""
    return bool(x and isinstance(x, str) and URL_RE.search(x))

def _patch_sa(info: dict) -> dict:
    """
    Corrects the newline characters in the private_key of the service account info.
    Streamlit secrets escape the newlines, so they need to be un-escaped.
    """
    info = dict(info) if info else {}
    pk = info.get("private_key", "")
    if "\\n" in pk:
        info["private_key"] = pk.replace("\\n", "\n")
    return info

def fmt_num(v) -> str:
    """Formats a number: integer if whole, one decimal place if fractional."""
    try:
        f = float(v)
        if f.is_integer():
            return str(int(f))
        return f"{f:.1f}"
    except (ValueError, TypeError):
        return str(v)

def _map_0_100_to_1_5(x: float) -> int:
    """Maps a score from a 0-100 scale to a 1-5 scale."""
    if pd.isna(x):
        return 1
    cuts = [20, 40, 60, 80]
    return 1 + sum(x >= c for c in cuts)
