import pandas as pd
from typing import List, Dict, Any, Tuple

# =========================
# Configuration Parsers
# =========================

def cfg_get(cfg_df: pd.DataFrame, key: str, default: Any = None, cast: type = str) -> Any:
    """
    Gets a value from the configuration DataFrame by key, with a default and type casting.
    """
    if cfg_df.empty:
        return default

    row = cfg_df[cfg_df["key"] == key]
    if row.empty:
        return default

    val = row["value"].iloc[0]

    if val is None or pd.isna(val):
        return default

    try:
        if cast == bool:
            return str(val).strip().lower() in ("1", "true", "yes", "y", "on")
        if cast == int:
            return int(float(val))
        return cast(val)
    except (ValueError, TypeError):
        return default

def cfg_list(cfg_df: pd.DataFrame, key: str, default_csv: str = "") -> List[str]:
    """
    Gets a comma-separated list of values from the configuration DataFrame.
    Also handles aliasing for common terms.
    """
    raw_value = cfg_get(cfg_df, key, default_csv, cast=str) or default_csv

    # Aliases to map user-friendly names to internal column names
    alias_map = {
        "full": "full_score", "syair": "lirik_text", "lyrics": "lirik_text",
        "lyric": "lirik_text", "chord": "chords_list", "chords": "chords_list",
        "notasi": "extract_notasi", "score": "full_score",
    }

    # Split, strip, and apply aliases
    items = [s.strip() for s in raw_value.split(",") if s.strip()]
    return [alias_map.get(item.lower(), item) for item in items]

def parse_rubrik(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Parses the 'Rubrik' DataFrame into a more usable list of dictionaries."""
    if df.empty:
        return []

    # Ensure numeric columns are of the correct type, coercing errors
    for col in ["bobot", "min_score", "max_score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Fill NaNs with default values
    df["min_score"] = df.get("min_score", 1).fillna(1).astype(int)
    df["max_score"] = df.get("max_score", 5).fillna(5).astype(int)
    df["bobot"] = df.get("bobot", 0).fillna(0)

    # Drop rows where essential keys are missing
    df = df.dropna(subset=["key", "aspek"])

    rubrik_items = []
    for _, row in df.iterrows():
        descriptions = {k: (row.get(f"desc_{k}") or "") for k in [1, 2, 3, 4, 5]}
        rubrik_items.append({
            "key": str(row["key"]).strip(),
            "aspek": str(row["aspek"]).strip(),
            "bobot": float(row["bobot"]),
            "min": int(row["min_score"]),
            "max": int(row["max_score"]),
            "desc": descriptions
        })
    return rubrik_items

def parse_keywords(df: pd.DataFrame) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
    """Parses the 'Keywords' DataFrame into separate lists of phrases and keywords."""
    phrases, keywords = [], []
    if df.empty:
        return phrases, keywords

    for _, row in df.iterrows():
        keyword_type = str(row.get("type", "")).strip().lower()
        text = str(row.get("text", "")).strip()

        if not text:
            continue

        try:
            weight = float(row.get("weight", 1.0))
        except (ValueError, TypeError):
            weight = 1.0

        if keyword_type == "phrase":
            phrases.append((text, weight))
        elif keyword_type == "keyword":
            keywords.append((text, weight))

    return phrases, keywords

def parse_variants(df: pd.DataFrame) -> Dict[str, str]:
    """Parses the 'Variants' DataFrame into a mapping for old to new column names."""
    mapping = {}
    if df.empty:
        return mapping

    for _, row in df.iterrows():
        from_name = str(row.get("from_name", "")).strip()
        to_key = str(row.get("to_key", "")).strip()
        if from_name and to_key:
            mapping[from_name] = to_key

    return mapping
