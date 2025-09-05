from typing import Callable, Tuple

def HASH_DF(df):
    return pd.util.hash_pandas_object(df).sum()

def is_url(s: str) -> bool:
    return s.strip().startswith(("http://", "https://"))

def _patch_sa():
    # Patch for gspread_pandas bug in service account auth
    # https://github.com/spreadsheets/gspread-pandas/issues/234
    from gspread_pandas.conf import get_config
    from google.oauth2.service_account import Credentials
    get_config(
        conf_dir=".",
        creds_dir=".",
        creds_filename="gcp_service_account.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"],
        creds_class=Credentials
    )

def fmt_num(x, nd=2):
    try:
        f = float(x)
        if abs(f - round(f)) < 1e-9:
            return str(int(round(f)))
        return f"{f:.{nd}f}"
    except (ValueError, TypeError):
        return str(x)

def _map_0_100_to_1_5(x: float) -> int:
    cuts = [20, 40, 60, 80]
    return 1 + sum(x >= c for c in cuts)

def _norm_id(s: str) -> str:
    import re
    import unicodedata
    s = s.lower()
    try:
        s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    except Exception:
        pass
    s = re.sub(r"[^a-z0-9\s']+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def _pick_text_variant(
    song: dict,
    order: list,
    extract_from_syair: Callable[[], str],
    extract_from_notasi: Callable[[], str],
) -> Tuple[str, str]:
    # This function now needs strip_chords, so we import it locally to avoid circular deps
    from .analysis import strip_chords

    for src in order:
        if src in {"full_score", "syair_chord", "lirik_text"}:
            val = str(song.get(src, "") or "").strip()
            if val: return src, val
        elif src == "extract_syair":
            try:    txt = (extract_from_syair() or "").strip()
            except: txt = ""
            if txt: return "extract_syair", txt
        elif src == "extract_notasi":
            try:    txt = (extract_from_notasi() or "").strip()
            except: txt = ""
            if txt: return "extract_notasi", txt
        elif src == "lirik_text":
            val = str(song.get("lirik_text", "") or "").strip()
            if val: return "lirik_text", val
            sc = str(song.get("syair_chord", "") or "").strip()
            if sc:
                try:
                    plain = strip_chords(sc).strip()
                    if plain:
                        return "lirik_text_from_syair_chord", plain
                except Exception:
                    pass
    return "none", ""
