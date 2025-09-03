# -*- coding: utf-8 -*-
# Penjurian Lagu - Streamlit + GSheet + GDrive

from zoneinfo import ZoneInfo
import os, io, re, unicodedata, datetime, base64, zipfile, tempfile, math
import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import fitz  # PyMuPDF
import gspread
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from gspread.utils import rowcol_to_a1
import numpy as np
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from typing import Callable, Tuple
import re
import unicodedata
from collections import Counter
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px

import urllib.parse
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------- Page config ----------
st.set_page_config(
    page_title="LOMBA CIPTA LAGU THEME SONG BULAN KELUARGA GKI PERUMNAS 2025",
    page_icon="🎵",
    layout="wide",
)

# ---------- Global CSS ----------
st.markdown("""
<style>
  .rubrik-cell{
    border:1px solid #E6E9F0;
    border-radius:10px;
    padding:.7rem .8rem;
    min-height:78px;
    background:#fff;
  }
  .rubrik-col-aspek{ font-weight:600; }
  .rubrik-col-bobot{ text-align:center; font-weight:600; }

  .r5{ background:#E9F8EF; }
  .r4{ background:#F1FAF0; }
  .r3{ background:#FFF5DA; }
  .r2{ background:#FFECE0; }
  .r1{ background:#FFE5E7; }

  .rubrik-head{
    font-weight:700;
    background:#F8FAFF;
    border:1px solid #E3E6EC;
    border-radius:10px;
    padding:.6rem .75rem;
    text-align:center;
  }
  .block-container{ max-width:1300px; }
  
  /* Full-width audio */
      .stAudio { width: 100% !important; }

      /* Kurangi jarak antar elemen di mobile */
      @media (max-width: 640px) {
        .block-container { padding-top: 0.5rem; padding-bottom: 3.5rem; }
        .stTabs [data-baseweb="tab-list"] { gap: .25rem; }
        .stTabs [data-baseweb="tab"] { padding: .35rem .6rem; font-size: 0.92rem; }
      }
      
</style>
""", unsafe_allow_html=True)

if st.session_state.pop("__scroll_top", False):
    components.html(
        "<script>window.scrollTo({top: 0, behavior: 'smooth'});</script>",
        height=0,
    )

# ---------- Assets (opsional) ----------
BANNER = "assets/banner.png"
LOGO   = "assets/logo.png"
WATERMARK_IMG = "assets/watermark.png"
WATERMARK_TEXT = "GKI PERUMNAS"

# ---------- Helpers umum ----------
HASH_DF = {pd.DataFrame: lambda df: df.to_csv(index=False)}
URL_RE = re.compile(r"^https?://", re.I)
def is_url(x): return bool(x and URL_RE.search(x))

def _patch_sa(info: dict) -> dict:
    info = dict(info) if info else {}
    pk = info.get("private_key", "")
    if "\\n" in pk:
        info["private_key"] = pk.replace("\\n", "\n")
    return info

def fmt_num(v):
    """Format angka: integer jika bulat, 1 desimal jika pecahan"""
    try:
        f = float(v)
        if f.is_integer():
            return str(int(f))
        return f"{f:.1f}"
    except:
        return str(v)



# =========================
# Google clients (cached)
# =========================
@st.cache_resource
def _gs_client():
    info = _patch_sa(st.secrets.get("gcp_service_account"))
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)

@st.cache_resource
def _drive_service():
    info = _patch_sa(st.secrets.get("gcp_service_account"))
    scopes = ["https://www.googleapis.com/auth/drive.readonly"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    creds.refresh(Request())
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def open_sheet():
    return _gs_client().open_by_key(st.secrets["gsheet_id"])

@st.cache_resource
def get_penilaian_ws():
    """Mendapatkan objek worksheet 'Penilaian' dan menyimpannya di cache resource."""
    return _ensure_ws(open_sheet(), "Penilaian")

def get_penilaian_df():
    """
    Mengambil DataFrame Penilaian, menggunakan st.session_state sebagai cache per sesi.
    Ini menghindari panggilan API GSheet pada setiap interaksi kecil.
    """
    if 'pen_df_cached' not in st.session_state:
        # Jika tidak ada di cache sesi, baca dari GSheet dan simpan
        ws = get_penilaian_ws()
        st.session_state.pen_df_cached = ws_to_df(ws)
    return st.session_state.pen_df_cached

# =========================
# Worksheet utils
# =========================
def _ensure_ws(sh, title, headers=None, rows=1000, cols=26):
    try:
        ws = sh.worksheet(title)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=title, rows=str(rows), cols=str(max(cols, (len(headers) if headers else 0) + 2)))
        if headers:
            ws.update("1:1", [headers])
    return ws

def ws_to_df(ws):
    vals = ws.get_all_values()
    if not vals:
        return pd.DataFrame()
    hdr, body = vals[0], vals[1:]
    return pd.DataFrame(body, columns=hdr) if body else pd.DataFrame(columns=hdr)

def ensure_headers(ws, headers):
    existing = ws.row_values(1)
    if existing == headers:
        return headers
    extras = [h for h in existing if h and h not in headers]
    final = headers + extras
    ws.update("1:1", [final])
    return final

# =========================
# Drive helpers + audio streaming-first
# =========================
def drive_preview_url(file_id):  # embed inline
    return f"https://drive.google.com/file/d/{file_id}/preview"

def drive_direct_url(file_id):   # basic download URL (sering OK untuk audio kecil)
    return f"https://drive.google.com/uc?export=download&id={file_id}"

@st.cache_data(ttl=6*3600, show_spinner=False, max_entries=256)
def drive_get_meta(file_id: str, fields="id,name,mimeType,size,webContentLink"):
    try:
        svc = _drive_service()
        meta = svc.files().get(fileId=file_id, fields=fields).execute()
        return meta or {}
    except Exception:
        return {}

@st.cache_data(show_spinner=False, hash_funcs=HASH_DF)
def drive_download_bytes(file_id: str) -> bytes | None:
    try:
        svc = _drive_service()
        request = svc.files().get_media(fileId=file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request, chunksize=1024 * 1024)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buf.getvalue()
    except Exception:
        return None

@st.cache_data(ttl=60, show_spinner=False)
def fetch_bytes_cached(url: str) -> bytes | None:
    try:
        r = requests.get(url, timeout=25)
        return r.content if r.status_code == 200 else None
    except Exception:
        return None

def pick_audio_format(mime: str | None, fallback_url: str | None = None) -> str | None:
    if mime:
        if mime in ("audio/mpeg", "audio/mp3"): return "audio/mpeg"
        if mime in ("audio/x-m4a", "audio/mp4", "audio/aac"): return "audio/mp4"
        if mime.startswith("audio/"): return mime
    if fallback_url and ".m4a" in fallback_url.lower(): return "audio/mp4"
    if fallback_url and ".mp3" in fallback_url.lower(): return "audio/mpeg"
    return None

def streamable_gdrive_audio_src(file_id: str):
    """
    Prefer URL stream (biar browser yang buffering). Fallback -> bytes.
    Return dict: {"mode":"url","url":..., "mime":...} | {"mode":"bytes","data":..., "mime":...} | {"mode":None}
    """
    if not file_id:
        return {"mode": None}
    meta = drive_get_meta(file_id) or {}
    mime = meta.get("mimeType")

    # 1) coba URL langsung (paling ringan)
    url = drive_direct_url(file_id)
    return {"mode":"url", "url": url, "mime": pick_audio_format(mime, url)}

# =========================
# Drive hybrid index + resolve assets
# =========================
def _drive_search_by_name(name, parent_id=None, mime_hint=None):
    svc = _drive_service()
    escaped = name.replace("'", "\\'")
    parts = ["name = '{}'".format(escaped), "trashed = false"]
    if parent_id:
        parts.append("'{}' in parents".format(parent_id))
    if mime_hint:
        parts.append("mimeType contains '{}'".format(mime_hint))
    query = " and ".join(parts)
    res = svc.files().list(
        q=query, spaces="drive",
        fields="files(id,name,mimeType,modifiedTime,parents)",
        pageSize=5, orderBy="modifiedTime desc"
    ).execute()
    return res.get("files", [])

def _idx_lookup(idx_df, name):
    if idx_df is None or idx_df.empty:
        return None
    row = idx_df[idx_df["name"] == name]
    if row.empty:
        return None
    return {
        "id": row["id"].iloc[0],
        "mimeType": row["mimeType"].iloc[0] if "mimeType" in row.columns else "",
        "modifiedTime": row["modifiedTime"].iloc[0] if "modifiedTime" in row.columns else "",
        "parentHint": row["parentHint"].iloc[0] if "parentHint" in row.columns else "",
    }

def _idx_append(ws_idx, rec):
    ws_idx.append_row(
        [rec.get(k,"") for k in ["name","id","mimeType","modifiedTime","parentHint"]],
        value_input_option="USER_ENTERED"
    )

def is_gdrive_id_like(x: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_-]{20,}", x or ""))

def resolve_source(raw_value, kind, cfg, idx_df, ws_idx):
    if not raw_value:
        return {"mode": None}

    # 1. Cek URL
    if is_url(raw_value):
        m = re.search(r"/d/([A-Za-z0-9_-]+)", raw_value) or re.search(r"[?&]id=([A-Za-z0-9_-]+)", raw_value)
        if m:
            fid = m.group(1)
            return {"mode":"url","id":fid,"mime":None,
                    "preview":drive_preview_url(fid),"direct":drive_direct_url(fid)}
        return {"mode":"url","id":None,"mime":None,"preview":raw_value,"direct":raw_value}

    # 2. Cek GDrive ID
    if is_gdrive_id_like(raw_value):
        fid = raw_value
        return {"mode":"url","id":fid,"mime":None,
                "preview":drive_preview_url(fid),"direct":drive_direct_url(fid)}

    # 3. Baru fallback ke path lokal
    if os.path.exists(raw_value):
        return {"mode":"local","path":raw_value}

    # Cari di index / drive
    hit = _idx_lookup(idx_df, raw_value)
    if not hit:
        parent = cfg_get(cfg, f"DRIVE_FOLDER_{kind.upper()}_ID", None) or cfg_get(cfg, "DRIVE_FOLDER_ROOT_ID", None)
        mime_hint = "audio/" if kind == "audio" else "application/pdf"
        files = _drive_search_by_name(os.path.basename(raw_value), parent_id=parent, mime_hint=mime_hint)
        if files:
            f = files[0]
            hit = {
                "id": f["id"],
                "mimeType": f.get("mimeType", ""),
                "modifiedTime": f.get("modifiedTime", ""),
                "parentHint": (parent or ""),
            }
            if ws_idx:
                _idx_append(ws_idx, {
                    "name": raw_value, "id": hit["id"], "mimeType": hit["mimeType"],
                    "modifiedTime": hit["modifiedTime"], "parentHint": hit["parentHint"],
                })
    if hit:
        return {"mode": "url", "id": hit["id"], "mime": hit.get("mimeType"),
                "preview": drive_preview_url(hit["id"]), "direct": drive_direct_url(hit["id"])}
    return {"mode": "url", "id": None, "mime": None, "preview": raw_value, "direct": raw_value}

# =========================
# PDF helpers (cached)
# =========================
def embed_pdf(source_dict, height=720):
    if not source_dict or source_dict["mode"] is None:
        st.info("Dokumen tidak tersedia."); return
    if source_dict["mode"] == "url":
        components.html(f"<iframe src='{source_dict['preview']}' width='100%' height='{height}'></iframe>",
                        height=height+10, scrolling=False)
    else:
        with open(source_dict["path"], "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        components.html(f"<iframe src='data:application/pdf;base64,{b64}' width='100%' height='{height}'></iframe>",
                        height=height+10, scrolling=False)

@st.cache_data(ttl=6*3600, show_spinner=False, max_entries=256)
def pdf_first_page_png_bytes(source_dict, dpi=160):
    try:
        if source_dict["mode"] == "url":
            data = fetch_bytes_cached(source_dict["direct"])
            if not data: return None
            doc = fitz.open(stream=data, filetype="pdf")
        else:
            doc = fitz.open(source_dict["path"])
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=dpi)
        doc.close()
        return pix.tobytes("png")
    except Exception:
        return None

def extract_pdf_text_cached(source_dict):
    try:
        if source_dict["mode"] == "url":
            data = fetch_bytes_cached(source_dict["direct"])
            if not data: return ""
            doc = fitz.open(stream=data, filetype="pdf")
        else:
            doc = fitz.open(source_dict["path"])
        text = "".join(p.get_text() for p in doc)
        doc.close()
        return (text or "").strip()
    except Exception:
        return ""

# =========================
# Load-all (cached configurable)
# =========================
def cfg_get(cfg_df, key, default=None, cast=str):
    if cfg_df.empty:
        return default
    row = cfg_df[cfg_df["key"] == key]
    if row.empty:
        return default
    val = row["value"].iloc[0]
    if cast == bool:
        return str(val).strip().lower() in ("1","true","yes","y","on")
    if cast == int:
        try:
            return int(float(val))
        except:
            return default
    return val

def cfg_list(cfg_df, key, default_csv):
    raw = cfg_get(cfg_df, key, default_csv, cast=str) or default_csv
    alias = {
        "full": "full_score",
        "syair": "lirik_text",
        "lyrics": "lirik_text",
        "lyric": "lirik_text",
        "chord": "chords_list",
        "chords": "chords_list",
        "notasi": "extract_notasi",
        "score": "full_score",
    }
    out = []
    for x in [s.strip() for s in raw.split(",") if s.strip()]:
        out.append(alias.get(x.lower(), x))
    return out

def parse_rubrik(df):
    if df.empty:
        return []
    for col in ["bobot","min_score","max_score"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["min_score"] = df.get("min_score", pd.Series([1]*len(df))).fillna(1).astype(int)
    df["max_score"] = df.get("max_score", pd.Series([5]*len(df))).fillna(5).astype(int)
    df = df.dropna(subset=["key","aspek"])
    rows = []
    for _, r in df.iterrows():
        desc = {k: (r.get(f"desc_{k}") or "") for k in [1,2,3,4,5]}
        rows.append({
            "key": str(r["key"]).strip(),
            "aspek": str(r["aspek"]).strip(),
            "bobot": float(r["bobot"]) if pd.notna(r["bobot"]) else 0.0,
            "min": int(r["min_score"]),
            "max": int(r["max_score"]),
            "desc": desc
        })
    return rows

def parse_keywords(df):
    phrases, keywords = [], []
    if df.empty:
        return phrases, keywords
    for _, r in df.iterrows():
        t = str(r.get("type","")).strip().lower()
        text = str(r.get("text","")).strip()
        try:
            w = float(r.get("weight", 1))
        except:
            w = 1.0
        if not text:
            continue
        if t == "phrase":
            phrases.append((text, w))
        elif t == "keyword":
            keywords.append((text, w))
    return phrases, keywords

def parse_variants(df):
    mapping = {}
    if df.empty:
        return mapping
    for _, r in df.iterrows():
        a = str(r.get("from_name","")).strip()
        b = str(r.get("to_key","")).strip()
        if a and b:
            mapping[a] = b
    return mapping

@st.cache_data(ttl=180, show_spinner=False)  # 3 menit (atur sesuai kebutuhan)
def load_all():
    sh = open_sheet()
    ws_cfg   = _ensure_ws(sh, "Config",     ["key","value"])
    ws_jud   = _ensure_ws(sh, "Judges",     ["juri"])
    ws_rub   = _ensure_ws(sh, "Rubrik",     ["key","aspek","bobot","min_score","max_score","desc_5","desc_4","desc_3","desc_2","desc_1"])
    ws_kw    = _ensure_ws(sh, "Keywords",   ["type","text","weight"])
    ws_var   = _ensure_ws(sh, "Variants",   ["from_name","to_key"])
    ws_songs = _ensure_ws(sh, "Songs",      ["judul","pengarang","audio_path","notasi_path","syair_path","lirik_text","chords_list","full_score","syair_chord"])
    ws_pen   = _ensure_ws(sh, "Penilaian",  ["timestamp","juri","judul","author","total"])
    ws_win   = _ensure_ws(sh, "Winners",    ["rank","judul","catatan"])
    ws_idx   = _ensure_ws(sh, "DriveIndex", ["name","id","mimeType","modifiedTime","parentHint"])
    
    return (
        sh,
        ws_to_df(ws_cfg), ws_to_df(ws_jud), ws_to_df(ws_rub),
        ws_to_df(ws_kw), ws_to_df(ws_var), ws_to_df(ws_songs),
        ws_pen, # HANYA KEMBALIKAN WORKSHEET OBJECT, BUKAN DATAFRAME
        ws_to_df(ws_win),
        ws_idx, ws_to_df(ws_idx)
    )

# =========================
# Tema scoring & chord parsing
# =========================
def _normalize(s):
    s = s.lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9\s']+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def make_theme_functions(phrases, keywords):
    def score(text):
        t = _normalize(text or "")
        s = 0.0
        for p, w in phrases:
            s += t.count(p.lower()) * float(w)
        for k, w in keywords:
            s += len(re.findall(rf"\b{re.escape(k.lower())}\w*\b", t)) * float(w)
        return float(min(round(s, 2), 100.0))
    def highlight(text):
        html = text or ""
        for p, _ in sorted(phrases, key=lambda x: len(x[0]), reverse=True):
            html = re.sub(fr"(?i)({re.escape(p)})", r"<mark>\1</mark>", html)
        for k, _ in keywords:
            html = re.sub(fr"(?i)\b({re.escape(k)}\w*)\b", r"<mark>\1</mark>", html)
        return (html or "<i>(syair kosong)</i>").replace("\n", "<br>")
    return score, highlight

CHORD_TOKEN = re.compile(
    r"^(?:[A-G](?:#|b)?(?:maj7|maj|min|m7|m|7|sus2|sus4|sus|dim|aug|add9|add11|add13|6|9|11|13)?)"
    r"(?:/[A-G](?:#|b)?)?$"
)

SECTION_WORDS = {
    "bait","bait1","bait2","bait3","bait4",
    "reff","ref","reffrein","chorus","prechorus","pre-chorus","pre_chorus",
    "bridge","intro","interlude","outro","ending","coda",
    "verse","verse1","verse2","verse3",
    "do"  # untuk baris seperti "Do = D (4/4)"
}



def _normalize_chord(tok: str) -> str:
    return tok.strip().replace(" ", "")

def extract_chords_strict(text: str) -> list[str]:
    if not text: return []
    tokens = re.split(r"[^\w/#]+", text)
    seen, out = set(), []
    for tok in tokens:
        if not tok: continue
        low = tok.lower()
        if low in SECTION_WORDS: continue
        if CHORD_TOKEN.match(tok):
            norm = _normalize_chord(tok)
            if norm not in seen:
                seen.add(norm)
                out.append(norm)
    return out

# ==== Key detection (major) sederhana, cukup robust untuk data lomba ====
_PC = {"C":0,"C#":1,"Db":1,"D":2,"D#":3,"Eb":3,"E":4,"Fb":4,"E#":5,"F":5,"F#":6,"Gb":6,
       "G":7,"G#":8,"Ab":8,"A":9,"A#":10,"Bb":10,"B":11,"Cb":11,"B#":0}
_PC_TO_NAME = {v:k for k,v in {"C":0,"C#":1,"D":2,"D#":3,"E":4,"F":5,"F#":6,"G":7,"G#":8,"A":9,"A#":10,"B":11}.items()}


def _major_diatonic_pcs(tonic_pc: int) -> set[int]:
    # I  ii  iii IV  V  vi  (VII° sengaja nggak dipakai biar sederhana)
    offs = [0, 2, 4, 5, 7, 9]
    return {(tonic_pc + k) % 12 for k in offs}

def detect_key_from_chords(seq: list[str]) -> tuple[str, float]:
    """
    Return (key_name_major, confidence 0..1).
    Heuristik:
      - Hitung kecocokan root akor dengan set diatonik mayor untuk 12 tonal.
      - I/IV/V bobot 2.0; ii/iii/vi bobot 1.2; non-diatonik penalti -0.5.
      - Confidence = (best - second) / max(1, total_bobot_positif + |penalti|)
    """
    pcs = [p for p in (_root_pc(ch) for ch in seq) if p is not None]
    if not pcs: 
        return ("?", 0.0)

    weights = {0:2.0, 2:1.2, 4:1.2, 5:2.0, 7:2.0, 9:1.2}  # diatonik major offset vs tonic
    scores = []
    for t in range(12):
        diat = _major_diatonic_pcs(t)
        s = 0.0
        for r in pcs:
            # offset r terhadap tonic
            off = (r - t) % 12
            if off in weights:
                s += weights[off]
            else:
                s -= 0.5  # penalti non-diatonik
        scores.append(s)

    best_idx = int(np.argmax(scores))
    best = scores[best_idx]
    second = sorted(scores, reverse=True)[1] if len(scores) > 1 else 0.0
    denom = abs(best) + sum(abs(x) for x in scores) / max(1, len(scores))
    conf = max(0.0, min(1.0, (best - second) / (denom + 1e-9)))
    name = _PC_TO_NAME.get(best_idx, "?")
    return (name, float(round(conf, 3)))


def parse_chords_list_field(val: str) -> list[str]:
    if not val:
        return []
    raw = re.split(r"[,\s]+", val)
    uniq, seen = [], set()
    for tok in raw:
        if not tok: continue
        if CHORD_TOKEN.match(tok):
            t = _normalize_chord(tok)
            if t not in seen:
                seen.add(t)
                uniq.append(t)
    return uniq

def chord_score_from_list(uniq: list[str]) -> int | None:
    n = len(uniq)
    if n == 0:
        return None
    if n <= 3:
        return 1
    if n <= 5:
        return 2
    if n <= 7:
        return 3
    if n <= 10:
        return 4
    return 5

# =========================
# Skor baru: Kekuatan Lirik & Kekayaan Musik
# =========================
STOPWORDS_MINI = set("""
yang dan di ke dari untuk kepada pada dalam itu ini itu pun serta sebagai dengan agar karena jika bila atau tapi namun
the a an and or but of to for in on at from by with as if when while into onto about over under out up down not no
""".split())

# =======================================================================
# 1. ENHANCED KEYWORD DICTIONARIES (Berdasarkan Konteks Tema)
# =======================================================================

# Definisikan kata kunci yang lebih kontekstual
_EMO_WORDS_V2 = {
    # Efesus 5 & Latar Belakang: bijaksana menggunakan waktu, persekutuan
    "tema_dalam": [
        "waktu", "kesempatan", "bijaksana", "arif", "pergunakan", "saksama",
        "hadir", "saat ini", "dekat", "persekutuan"
    ],
    # Konteks kehangatan dan relasi keluarga
    "keluarga": [
        "keluarga", "bersama", "rumah", "ayah", "bunda", "ibu", "anak",
        "kasih", "rukun", "saling menjaga"
    ],
    # Tujuan akhir: iman dan menjadi berkat
    "iman": [
        "iman", "doa", "tuhan", "yesus", "syukur", "berkat", "pengharapan", "setia"
    ]
}

# Imagery/metafora yang relevan dengan tema
_IMAGERY_V2 = [
    "harta", "permata", "berharga", "tak ternilai", "mutiara",
    "pelabuhan", "sauh", "jangkar", "bahtera", "rumahku"
]

# Distraksi modern yang disebutkan dalam latar belakang
_DISTRACTIONS = [
    "dunia maya", "medsos", "layar", "gawai", "sibuk", "sendiri", "jarak"
]

# Klise yang umum
_CLICHES = [
    "tuhan pasti memberkati", "jalanmu lurus", "hidupku indah", "selalu bersama selamanya",
    "tetap semangat", "kau kuatkanku", "percaya saja", "kasih setiamu"
]

# Token untuk mendeteksi struktur lagu
_SECTION_TOKENS = ["reff", "refrein", "chorus", "verse", "bait", "bridge", "pre-chorus", "coda"]

def _norm_id(s: str) -> str:
    s = s.lower()
    try:
        s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    except Exception:
        pass
    s = re.sub(r"[^a-z0-9\s']+", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def _map_0_100_to_1_5(x: float) -> int:
    cuts = [20, 40, 60, 80]
    return 1 + sum(x >= c for c in cuts)

# =======================================================================
# 2. ENHANCED SCORING FUNCTION
# =======================================================================

def _lyrics_strength_score_v2(text: str) -> int:
    """
    Versi 2: Skor 1–5 dengan pemahaman konteks tema "Waktu Bersama Harta Berharga".
    - Menganalisis relevansi dengan Efesus 5 (bijaksana, waktu, kesempatan).
    - Memberi nilai pada penggambaran 'persekutuan' vs. distraksi modern.
    - Tetap mempertimbangkan kualitas puitis dan struktur.
    """
    if not text:
        return 1

    t_norm = _norm_id(text)

    # 1. Kedalaman Tema (Bobot 35%) - Sesuai Efesus 5 & Latar Belakang
    tema_score = sum(t_norm.count(w) for w in _EMO_WORDS_V2["tema_dalam"])
    tema_score = min(tema_score, 8) # Cap at 8 hits

    # 2. Sentuhan Keluarga & Iman (Bobot 25%)
    keluarga_score = sum(t_norm.count(w) for w in _EMO_WORDS_V2["keluarga"])
    iman_score = sum(t_norm.count(w) for w in _EMO_WORDS_V2["iman"])
    relasi_score = min(keluarga_score + iman_score, 10) # Cap at 10 total hits

    # 3. Kualitas Puitis & Imagery (Bobot 20%)
    img_score = sum(1 for kw in _IMAGERY_V2 if kw in t_norm)
    img_score = min(img_score, 5)

    # 4. Struktur Lagu (Bobot 20%)
    lines = [l.strip() for l in t_norm.splitlines() if l.strip()]
    tokens = sum(1 for tok in _SECTION_TOKENS if tok in t_norm)
    uniq_lines = len(set(lines))
    varied_lines = (uniq_lines / max(1, len(lines))) >= 0.7
    struct_score = (2 if tokens >= 1 else 0) + (1 if tokens >= 2 else 0) + (1 if varied_lines else 0)

    # 5. Penalti: Klise & Distraksi Modern tanpa Solusi
    cliche_hits = sum(1 for c in _CLICHES if c in t_norm)
    distraction_hits = sum(1 for d in _DISTRACTIONS if d in t_norm)
    
    # Penalti hanya jika distraksi disebut tanpa solusi (tanpa kata iman/keluarga)
    distraction_penalty = distraction_hits > 0 and not any(w in t_norm for w in _EMO_WORDS_V2["iman"] + ["bersama", "dekat"])

    penal = min(2, cliche_hits) + (2 if distraction_penalty else 0) # Penalti lebih besar untuk distraksi tanpa solusi

    # Agregasi Skor -> 0..100
    raw_score = (
        35 * (tema_score / 8.0) +
        25 * (relasi_score / 10.0) +
        20 * (img_score / 5.0) +
        20 * (struct_score / 4.0) -
        15 * (penal / 4.0)
    )
    raw_score = max(0.0, min(100.0, raw_score))

    return _map_0_100_to_1_5(raw_score)

# =======================================================================
# 3. "BEAUTIFUL" EXPLANATION FUNCTION
# =======================================================================

def explain_lyrics_strength_v2(text: str) -> str:
    """
    Versi 2: Memberikan penjelasan yang 'cantik' dan relevan dengan konteks.
    Mengembalikan string HTML yang sudah diformat.
    """
    if not text:
        return "<p><i>Lirik kosong atau tidak dapat dibaca.</i></p>"

    t_raw = text
    t_norm = _norm_id(t_raw)
    reasons = []

    # Cek Kedalaman Tema (Efesus 5)
    if any(w in t_norm for w in ["waktu", "kesempatan", "bijaksana", "arif", "pergunakan"]):
        reasons.append("✨ **Koneksi Teologis:** Syair ini berhasil menangkap esensi dari Efesus 5, menekankan pentingnya menggunakan <b>waktu</b> dengan <b>bijaksana</b> sebagai respons iman.")

    # Cek Tujuan (Persekutuan & Iman)
    if any(w in t_norm for w in ["persekutuan", "hadir", "dekat", "bersama"]) and any(w in t_norm for w in _EMO_WORDS_V2["iman"]):
        reasons.append("❤️ **Kedalaman Relasional:** Lirik dengan indah menggambarkan tujuan utama tema, yaitu membangun <b>persekutuan keluarga</b> yang berpusat pada <b>iman</b> dan kehadiran Tuhan.")
    elif any(w in t_norm for w in _EMO_WORDS_V2["keluarga"]):
         reasons.append("🏠 **Fokus Keluarga:** Lirik secara konsisten mengangkat nilai kebersamaan dalam keluarga, menjadikannya relevan dengan tema utama.")

    # Cek Imagery
    if any(kw in t_norm for kw in _IMAGERY_V2):
        reasons.append("🎨 **Puitis & Imajinatif:** Penggunaan metafora seperti 'harta' atau 'permata' memperkaya lirik dan membuat pesannya lebih mengena di hati.")

    # Cek Latar Belakang (Distraksi Modern)
    if any(d in t_norm for d in _DISTRACTIONS):
        if not any(w in t_norm for w in _EMO_WORDS_V2["iman"] + ["bersama", "dekat"]):
            reasons.append("⚠️ **Refleksi Kritis (butuh solusi):** Syair secara relevan menyinggung tantangan modern seperti 'dunia maya' atau 'kesibukan', namun akan lebih kuat jika menawarkan persekutuan sebagai solusinya.")
        else:
            reasons.append("💡 **Sangat Kontekstual:** Hebat! Lirik ini tidak hanya mengangkat keindahan keluarga, tapi juga secara realistis mengakui tantangan modern dan menawarkan <b>iman</b> dan <b>kebersamaan</b> sebagai jawabannya.")

    if not reasons:
        reasons.append("📝 **Pesan Tersampaikan:** Lirik ini memiliki pesan yang cukup jelas, namun dapat diperdalam lagi dengan sentuhan teologis dan imajinasi puitis yang lebih kuat.")

    # Format output menjadi HTML yang cantik
    html_output = "<div style='line-height:1.6;'>"
    html_output += "<ul style='margin:0; padding-left: 20px;'>"
    for reason in reasons[:3]: # Ambil maksimal 3 alasan terkuat
        html_output += f"<li style='margin-bottom:8px;'>{reason}</li>"
    html_output += "</ul></div>"
    
    return html_output

# =======================================================================
# 4. NEW MULTI-COLOR HIGHLIGHTING FUNCTION
# =======================================================================

def highlight_lyrics_v2(text: str) -> str:
    """
    Versi 2: Memberikan highlight dengan warna berbeda untuk setiap kategori
    kata kunci, menjadikannya lebih informatif dan 'cantik'.
    """
    if not text:
        return "<i>(Syair kosong)</i>"

    html = text.replace("\n", "<br>")

    # Definisikan warna untuk setiap kategori
    colors = {
        "tema_dalam": "#FFD700",  # Gold
        "iman": "#87CEEB",        # SkyBlue
        "keluarga": "#98FB98",    # PaleGreen
        "imagery": "#FFA07A",     # LightSalmon
        "distraksi": "#D3D3D3"    # LightGray
    }

    all_keywords = {
        "tema_dalam": sorted(_EMO_WORDS_V2["tema_dalam"], key=len, reverse=True),
        "iman": sorted(_EMO_WORDS_V2["iman"], key=len, reverse=True),
        "keluarga": sorted(_EMO_WORDS_V2["keluarga"], key=len, reverse=True),
        "imagery": sorted(_IMAGERY_V2, key=len, reverse=True),
        "distraksi": sorted(_DISTRACTIONS, key=len, reverse=True)
    }

    for category, keywords in all_keywords.items():
        color = colors[category]
        for kw in keywords:
            # (?i) untuk case-insensitive, \b untuk whole word
            pattern = re.compile(fr"\b({re.escape(kw)})\b", re.IGNORECASE)
            # Pastikan tidak me-replace di dalam tag HTML yang sudah ada
            # Ini adalah pendekatan sederhana untuk menghindari double-marking
            def replacer(match):
                # Periksa konteks sebelum dan sesudah match
                pre_match = html[:match.start()]
                post_match = html[match.end():]
                if pre_match.endswith(('>', '"', "'")) or post_match.startswith(('>', '"', "'")):
                    return match.group(0) # Jangan replace jika bagian dari atribut/tag
                return f"<mark style='background-color:{color}; padding: 2px 4px; border-radius:4px;'>{match.group(1)}</mark>"
            
            # Cari dan ganti hanya jika tidak berada di dalam <mark>
            # Ini adalah simplifikasi, untuk kasus kompleks butuh parsing HTML
            temp_html = ""
            last_end = 0
            for m in re.finditer(r"<mark.*?>.*?</mark>", html, re.DOTALL):
                start, end = m.span()
                temp_html += re.sub(pattern, replacer, html[last_end:start])
                temp_html += html[start:end]
                last_end = end
            temp_html += re.sub(pattern, replacer, html[last_end:])
            html = temp_html
            
    return html

def strip_chords(text: str) -> str:
    BRACKET_CHORD = re.compile(r"\[[^\]]+\]")
    INLINE_CHORD  = re.compile(r"(?<!\w)([A-G](?:#|b)?(?:m|maj7|m7|7|sus2|sus4|dim|aug|add9|6|9)?)(?!\w)")
    if not text: return ""
    t = BRACKET_CHORD.sub("", text)
    t = INLINE_CHORD.sub("", t)
    t = re.sub(r"[ \t]+\n", "\n", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()

# --- Kekuatan Lirik (HYBRID, konteks keluarga/rohani, manusiawi) ---
_STOPWORDS_ID = {"yang","dan","di","ke","kau","ku","mu","oh","la","na","ini","itu","karena","untuk","dengan","dalam","pada","ada"}

def _norm_id(s: str) -> str:
    s = s.lower()
    try:
        import unicodedata
        s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    except Exception:
        pass
    s = s.replace("-", "")  # “setia-mu” => “setiamu”
    return s

def _top_word_penalty(words: list[str]) -> int:
    from collections import Counter
    words = [w for w in words if w not in _STOPWORDS_ID]
    if not words: return 0
    cnt = Counter(words); total = sum(cnt.values())
    if not total: return 0
    _, top_freq = cnt.most_common(1)[0]
    return 1 if (top_freq / total) > 0.12 else 0  # terlalu dominan

def _lyrics_strength_score_v2(text: str) -> int:
    """
    Versi 2: Skor 1–5 dengan pemahaman konteks tema "Waktu Bersama Harta Berharga".
    - Menganalisis relevansi dengan Efesus 5 (bijaksana, waktu, kesempatan).
    - Memberi nilai pada penggambaran 'persekutuan' vs. distraksi modern.
    - Tetap mempertimbangkan kualitas puitis dan struktur.
    """
    if not text:
        return 1

    t_norm = _norm_id(text)

    # 1. Kedalaman Tema (Bobot 35%) - Sesuai Efesus 5 & Latar Belakang
    tema_score = sum(t_norm.count(w) for w in _EMO_WORDS_V2["tema_dalam"])
    tema_score = min(tema_score, 8) # Cap at 8 hits

    # 2. Sentuhan Keluarga & Persekutuan (Bobot 25%)
    keluarga_score = sum(t_norm.count(w) for w in _EMO_WORDS_V2["keluarga"])
    keluarga_score = min(keluarga_score, 6)

    # 3. Kualitas Puitis & Imagery (Bobot 20%)
    img_score = sum(1 for kw in _IMAGERY_V2 if kw in t_norm)
    img_score = min(img_score, 5)

    # 4. Struktur Lagu (Bobot 20%)
    lines = [l.strip() for l in t_norm.splitlines() if l.strip()]
    tokens = sum(1 for tok in _SECTION_TOKENS if tok in t_norm)
    uniq_lines = len(set(lines))
    varied_lines = (uniq_lines / max(1, len(lines))) >= 0.7
    struct_score = (2 if tokens >= 1 else 0) + (1 if tokens >= 2 else 0) + (1 if varied_lines else 0)

    # 5. Penalti: Klise & Distraksi Modern
    cliche_hits = sum(1 for c in _CLICHES if c in t_norm)
    distraction_hits = sum(1 for d in _DISTRACTIONS if d in t_norm)
    # Penalti hanya jika distraksi disebut tanpa solusi (tanpa kata 'kasih'/'doa'/'Tuhan')
    distraction_penalty = distraction_hits > 0 and not any(w in t_norm for w in ["kasih", "doa", "tuhan", "yesus"])

    penal = min(2, cliche_hits) + (1 if distraction_penalty else 0)

    # Agregasi Skor -> 0..100
    raw_score = (
        35 * (tema_score / 8.0) +
        25 * (keluarga_score / 6.0) +
        20 * (img_score / 5.0) +
        20 * (struct_score / 4.0) -
        15 * (penal / 3.0)
    )
    raw_score = max(0.0, min(100.0, raw_score))

    return _map_0_100_to_1_5(raw_score)

QUAL_EXT = re.compile(r'(maj7|m7|maj|7|9|11|13|sus2|sus4|sus|dim|aug|add9|6|add11|add13)')

# ====== Root parser & fitur transisi untuk penilaian harmoni v2 ======
_PITCH = {'C':0,'C#':1,'Db':1,'D':2,'D#':3,'Eb':3,'E':4,'Fb':4,'E#':5,'F':5,'F#':6,'Gb':6,'G':7,'G#':8,'Ab':8,'A':9,'A#':10,'Bb':10,'B':11,'Cb':11}
_ROOT_RE = re.compile(r'^([A-G](?:#|b)?)')

def _root_pc(ch: str) -> int | None:
    if not ch: return None
    # ambil root di kiri sebelum slash
    base = ch.split('/')[0].strip()
    m = _ROOT_RE.match(base)
    if not m: return None
    r = m.group(1).upper().replace('♭','b').replace('♯','#')
    return _PITCH.get(r)

def _fifths_move(pc1: int, pc2: int) -> int:
    """+7 ≡ naik perfect 5th, +5 ≡ naik perfect 4th (mod 12) — pakai |delta|==5 atau 7"""
    if pc1 is None or pc2 is None: return 0
    d = (pc2 - pc1) % 12
    return 1 if d in (5,7) else 0

def _repetition_bigram_penalty(seq: list[str]) -> float:
    if len(seq) < 3: return 0.0
    big = list(zip(seq, seq[1:]))
    c = Counter(big)
    rep = sum(v-1 for v in c.values() if v>1)
    return min(rep / max(1,len(big)), 1.0)

def music_features_v2(seq: list[str]) -> dict:
    """hitung fitur yang lebih 'musikal' dari urutan akor"""
    uniq = list(dict.fromkeys(seq))
    U = min(len(set(uniq))/10.0, 1.0)

    # entropi transisi
    big = list(zip(seq, seq[1:])) if len(seq)>1 else []
    if big:
        c = Counter(big); tot = sum(c.values())
        T = _entropy([v/tot for v in c.values()])
    else:
        T = 0.0

    ext = sum(1 for c in seq if QUAL_EXT.search(c)) / max(1,len(seq))
    slash = sum(1 for c in seq if "/" in c) / max(1,len(seq))
    nondi = sum(1 for c in seq if re.match(r'^[A-G](#|b)', c)) / max(1,len(seq))  # proxy aja

    # circle-of-fifths / cadence
    pcs = [_root_pc(c) for c in seq]
    fif = 0; dom_cad = 0; steps = 0
    for i in range(1, len(pcs)):
        if pcs[i-1] is None or pcs[i] is None: 
            continue
        steps += 1
        if _fifths_move(pcs[i-1], pcs[i]): 
            fif += 1
            # treat gerak turun 5th (V->I) sebagai cadence kuat
            d = (pcs[i] - pcs[i-1]) % 12
            if d == 7:  # turun 5th (mis. A -> D)
                dom_cad += 1
    fif_prop = fif / max(1, steps)
    cad_prop = dom_cad / max(1, steps)

    rep_pen = _repetition_bigram_penalty(seq)

    return {
        "U":U, "T":T, "ext":ext, "slash":slash, "nondi":nondi,
        "fif":fif_prop, "cad":cad_prop, "rep_pen":rep_pen,
        "uniq_list": uniq, "big_count": len(set(big))
    }

def score_harmonic_raw_v2(aset: dict) -> float:
    """
    Skor mentah 0..100 untuk 'kekayaan akor' yang lebih peka ke slash/extension
    + penalti besar kalau nol.
    Semua bobot & penalti bisa diatur dari sheet Config (fallback ke default di bawah).
    """
    seq = chord_sequence_from_sources(aset, CHORD_SOURCE_PRIORITY)
    feats = music_features_v2(seq) if seq else {"uniq_list": [], "big_count": 0, "ext": 0.0, "slash": 0.0, "nondi": 0.0}

    # Normalisasi ke 0..1
    uniq_norm = min(len(set(feats["uniq_list"])) / 12.0, 1.0)         # banyak warna akor
    trans_norm = min(float(feats["big_count"]) / 12.0, 1.0)           # variasi transisi
    ext_rate   = float(feats.get("ext", 0.0))                         # proporsi extension
    slash_rate = float(feats.get("slash", 0.0))                       # proporsi slash-bass
    nondi_rate = float(feats.get("nondi", 0.0))                       # proporsi non-diatonik

    # Bobot (bisa diubah dari sheet Config)
    W_EXT = cfg_get(cfg, "MUSIC_W_EXT",   40, int) / 100.0
    W_SLA = cfg_get(cfg, "MUSIC_W_SLASH", 35, int) / 100.0
    W_NDI = cfg_get(cfg, "MUSIC_W_NDI",   25, int) / 100.0
    W_UQ  = cfg_get(cfg, "MUSIC_W_UNIQ",  20, int) / 100.0
    W_TRA = cfg_get(cfg, "MUSIC_W_TRANS", 20, int) / 100.0

    # Penalti besar jika benar-benar tidak ada
    PEN_NO_SLA = cfg_get(cfg, "MUSIC_PENALTY_NO_SLASH", 15, int) / 100.0
    PEN_NO_EXT = cfg_get(cfg, "MUSIC_PENALTY_NO_EXT",   10, int) / 100.0

    raw = 100.0 * (
        W_EXT * ext_rate +
        W_SLA * slash_rate +
        W_NDI * nondi_rate +
        W_UQ  * uniq_norm +
        W_TRA * trans_norm
    )

    if slash_rate == 0.0:
        raw -= 100.0 * PEN_NO_SLA
    if ext_rate == 0.0:
        raw -= 100.0 * PEN_NO_EXT

    return max(0.0, float(raw))


def _entropy(probs):
    return -sum(p*math.log(p+1e-12) for p in probs if p>0)/math.log(max(2, len(probs)))

def chord_sequence_from_sources(aset: dict, order: list[str]) -> list[str]:
    """Ambil urutan chord dari sumber prioritas. Selalu filter dengan regex chord."""
    seq: list[str] = []
    for src in order:
        if src == "chords_list" and aset.get("chords_list"):
            seq = parse_chords_list_field(aset["chords_list"])  # <-- penting: pakai parser!
            break
        if src in ("syair_chord","full_score"):
            seq = extract_chords_strict(aset.get(src,""))
            break
        if src == "extract_notasi" and aset.get("notasi"):
            txt = extract_pdf_text_cached(aset["notasi"]); seq = extract_chords_strict(txt); break
        if src == "extract_syair" and aset.get("syair"):
            txt = extract_pdf_text_cached(aset["syair"]);  seq = extract_chords_strict(txt); break
    return seq

# ---- letakkan dekat fungsi score_harmonic_richness() ----
def score_harmonic_raw(aset: dict) -> float:
    """0..100 (kontinu), sama rumus seperti score_harmonic_richness tapi tidak di-map 1..5"""
    seq = chord_sequence_from_sources(aset, CHORD_SOURCE_PRIORITY)
    if not seq: 
        return 0.0
    uniq = list(dict.fromkeys(seq))
    U = min(len(set(uniq))/10.0, 1.0)

    bigrams = list(zip(seq, seq[1:])) if len(seq) > 1 else []
    if bigrams:
        c = Counter(bigrams); total = sum(c.values())
        T = _entropy([v/total for v in c.values()])
    else:
        T = 0.0

    E = sum(1 for c in seq if QUAL_EXT.search(c)) / max(1,len(seq))
    B = sum(1 for c in seq if "/" in c) / max(1,len(seq))
    X = sum(1 for c in seq if re.match(r'^[A-G](#|b)', c)) / max(1,len(seq))

    # bobot disetel agak “tajam” supaya ada sebaran
    raw = 35*U + 35*T + 20*E + 7*B + 3*X     # total max ~100
    return float(max(0.0, min(100.0, raw)))


def score_harmonic_richness(aset: dict) -> int:
    """
    Skor 1–5 dengan penalti untuk progresi yang sangat 'flat' (tanpa warna).
    Bobot baru: E(extensions)=30, B(slash)=20, X(non-diatonik)=15, T(transisi)=20, U(unik)=15.
    """
    seq = chord_sequence_from_sources(aset, CHORD_SOURCE_PRIORITY)
    if not seq:
        return 1

    uniq = list(dict.fromkeys(seq))
    U = min(len(set(uniq)) / 10.0, 1.0)

    bigrams = list(zip(seq, seq[1:])) if len(seq) > 1 else []
    if bigrams:
        c = Counter(bigrams)
        total = sum(c.values())
        T = _entropy([v / total for v in c.values()])  # 0..1
    else:
        T = 0.0

    E = sum(1 for c in seq if QUAL_EXT.search(c)) / max(1, len(seq))          # extensions
    B = sum(1 for c in seq if "/" in c) / max(1, len(seq))                     # slash chords
    X = sum(1 for c in seq if re.match(r'^[A-G](#|b)', c)) / max(1, len(seq))  # non-diatonik di luar natural key

    # Bobot baru (lebih menghargai 'warna' akor):
    raw = 15*U + 20*T + 30*E + 20*B + 15*X   # 0..100 skala relatif

    # Penalti eksplisit utk progresi yang 'flat':
    if E == 0 and B == 0 and X == 0:
        raw -= 18  # tidak ada warna sama sekali → turunkan
    if len(set(uniq)) <= 4 and T < 0.25:
        raw -= 8   # sedikit akor dan transisi monoton → turunkan lagi

    raw = max(0.0, min(100.0, raw))
    return _map_0_100_to_1_5(raw)


def detect_genre(seq):
    feats = music_features_v2(seq)
    E, B, X, U, T = feats["ext"], feats["slash"], feats["nondi"], feats["U"], feats["T"]

    if E > 0.2 or X > 0.15:
        return "Jazz/Gospel"
    elif B > 0.15 and U <= 6:
        return "Worship/CCM"
    elif X > 0.1 and U <= 5:
        return "Rock"
    elif U >= 7 and E < 0.1 and B < 0.1:
        return "Folk/Acoustic"
    else:
        return "Pop/Ballad"
    
    
# ==========================================================
# FUNGSI UNTUK ANALISIS ORISINALITAS
# ==========================================================

def get_clean_lyrics_for_song(aset: dict) -> str:
    """Helper untuk mendapatkan lirik bersih dari sebuah lagu."""
    # Definisikan fungsi ekstraksi di dalam scope agar aset terikat
    def _ex_sy(): return extract_pdf_text_cached(aset.get("syair", {}))
    def _ex_no(): return extract_pdf_text_cached(aset.get("notasi", {}))
    
    src, txt = _pick_text_variant(aset, LYRICS_SCORE_PRIORITY, _ex_sy, _ex_no)
    return strip_chords(txt) if src in ("syair_chord", "full_score", "extract_notasi") else txt

def analyze_originality_signals(lyrics: str, chord_seq: list) -> dict:
    """Menganalisis sinyal AI atau generik dari lirik dan akor."""
    if not lyrics:
        return {"cliche_score": 0, "ttr": 0, "num_chords": 0}
    
    t_norm = _norm_id(lyrics)
    words = t_norm.split()
    
    # Skor Klise (semakin tinggi, semakin generik)
    cliche_hits = sum(1 for c in _CLICHES if c in t_norm)
    cliche_score = min(cliche_hits * 25, 100) # Setiap klise bernilai 25 poin

    # Keragaman Kosakata (TTR)
    ttr = len(set(words)) / len(words) if words else 0

    return {
        "cliche_score": cliche_score,
        "ttr": ttr,
        "num_chords": len(set(chord_seq))
    }

def calculate_internal_similarity(current_title: str, all_songs: dict) -> pd.DataFrame:
    """Menghitung kemiripan lirik & akor dengan semua lagu lain."""
    if len(all_songs) < 2:
        return pd.DataFrame()

    current_aset = all_songs[current_title]
    current_lyrics = get_clean_lyrics_for_song(current_aset)
    current_chords_str = " ".join(chord_sequence_from_sources(current_aset, CHORD_SOURCE_PRIORITY))

    # Siapkan data lirik untuk perbandingan
    titles = [t for t in all_songs if t != current_title]
    lyrics_corpus = [get_clean_lyrics_for_song(all_songs[t]) for t in titles]

    # Hitung kemiripan lirik menggunakan TF-IDF
    try:
        vectorizer = TfidfVectorizer().fit(lyrics_corpus + [current_lyrics])
        tfidf_matrix = vectorizer.transform(lyrics_corpus)
        current_tfidf = vectorizer.transform([current_lyrics])
        lyric_sims = cosine_similarity(current_tfidf, tfidf_matrix).flatten()
    except ValueError:
        lyric_sims = [0.0] * len(titles) # Terjadi jika lirik kosong

    # Hitung kemiripan akor dan kumpulkan hasil
    results = []
    for i, title in enumerate(titles):
        other_aset = all_songs[title]
        other_chords_str = " ".join(chord_sequence_from_sources(other_aset, CHORD_SOURCE_PRIORITY))
        
        chord_sim = SequenceMatcher(None, current_chords_str, other_chords_str).ratio()
        
        results.append({
            "Judul Lagu Pembanding": title,
            "Kemiripan Lirik (%)": round(lyric_sims[i] * 100, 1),
            "Kemiripan Akor (%)": round(chord_sim * 100, 1)
        })

    df = pd.DataFrame(results)
    df['Skor Gabungan'] = df['Kemiripan Lirik (%)'] * 0.6 + df['Kemiripan Akor (%)'] * 0.4
    return df.sort_values('Skor Gabungan', ascending=False).head(3).drop(columns=['Skor Gabungan'])

# ---------- Auto-suggestions ----------
def _norm_key(s: str) -> str:
    s = (s or "").strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = s.replace("-", " ")
    return re.sub(r"\s+", " ", s)

def _find_key_like(substr: str):
    # alias untuk jaga-jaga variasi penamaan di sheet
    ALIASES = {
        "tema": ["tema","kesesuaian tema","keterkaitan tema","relevansi tema"],
        "lirik": ["lirik","kekuatan lirik","kekuatan syair","syair","diksi","keunikan lirik"],
        "musik": ["musik","aransemen","harmoni","kekayaan akor","kreativitas musik","akor"],
    }
    want = _norm_key(substr)
    candidates = ALIASES.get(want, [want])

    for r in RUBRIK:
        key_n  = _norm_key(r.get("key",""))
        asp_n  = _norm_key(r.get("aspek",""))
        hay    = f"{key_n} {asp_n}"
        if any(c in hay for c in candidates):
            return r["key"]
    return None


# --- PATCH: dynamic percentile binning for harmonic score ---
def _make_dynamic_binner(values: list[float]):
    """Return (bin_func, cuts) where bin_func(v)->1..5 using 20/40/60/80 percentiles."""
    arr = np.array([float(x) for x in values if pd.notna(x)], dtype=float)
    if arr.size == 0:
        return (lambda v: 1), [0, 0, 0, 0]
    cuts = np.percentile(arr, [20, 40, 60, 80]).tolist()  # p20,p40,p60,p80
    def _bin(v: float) -> int:
        try:
            x = float(v)
        except Exception:
            return 1
        return 1 + sum(x >= c for c in cuts)
    return _bin, cuts


# ==============================================================================
# 5-POINT GENERATIVE SCORING SYSTEM (FINAL ENHANCED VERSION)
# ==============================================================================

def _get_lyric_features(text: str) -> dict:
    """Mengekstrak fitur lirik untuk skor kreativitas dan singability."""
    t_norm = _norm_id(text)
    words = t_norm.split()
    if not words:
        return {"ttr": 0, "cliche_hits": 0, "communal_words_prop": 0, "has_chorus": False, "imagery_hits": 0}
    
    total_words = len(words)
    unique_words = len(set(words))
    ttr = unique_words / total_words if total_words > 0 else 0
    cliche_hits = sum(1 for c in _CLICHES if c in t_norm)
    communal_words = sum(1 for w in words if w in ["kita", "kami", "bersama", "umatmu"])
    imagery_hits = sum(1 for img in _IMAGERY_V2 if img in t_norm)
    
    # Cek repetisi struktural (adanya Reff/Chorus)
    has_chorus = any(sec in t_norm for sec in ["reff", "refrein", "chorus"])
    
    return {
        "ttr": ttr, "cliche_hits": cliche_hits,
        "communal_words_prop": communal_words / total_words if total_words > 0 else 0,
        "has_chorus": has_chorus, "imagery_hits": imagery_hits
    }

def score_creativity_v2(aset: dict, lyrics_text: str) -> int:
    """Skor 1-5 untuk Kreativitas & Orisinalitas (Versi 2)."""
    # 1. Fitur Harmoni (Bobot 60%)
    seq = chord_sequence_from_sources(aset, CHORD_SOURCE_PRIORITY)
    harmonic_score = 0.2
    if seq:
        feats = music_features_v2(seq)
        nondi_score = min(feats.get("nondi", 0) * 4, 1.0) # non-diatonic sangat dihargai
        ext_score = min(feats.get("ext", 0) * 2, 1.0)
        trans_score = min(feats.get("big_count", 0) / 15.0, 1.0)
        # Kreativitas tinggi jika berani menggunakan akor non-diatonik DAN ekstensi
        bonus_kombinasi = 0.2 if (nondi_score > 0.5 and ext_score > 0.3) else 0
        harmonic_score = min((0.5 * nondi_score) + (0.3 * ext_score) + (0.2 * trans_score) + bonus_kombinasi, 1.0)

    # 2. Fitur Lirik (Bobot 40%)
    lyric_feats = _get_lyric_features(lyrics_text)
    # TTR tinggi, tidak klise, DAN ada imagery = kreatif
    lyrical_score = (0.5 * lyric_feats["ttr"]) + \
                    (0.3 * (1 - min(lyric_feats["cliche_hits"] / 2.0, 1.0))) + \
                    (0.2 * min(lyric_feats["imagery_hits"] / 3.0, 1.0))
    
    raw_score = 100 * ((0.6 * harmonic_score) + (0.4 * lyrical_score))
    return _map_0_100_to_1_5(raw_score)

def score_singability_v2(aset: dict, lyrics_text: str) -> int:
    """Skor 1-5 untuk Kesesuaian Jemaat (Singability - Versi 2)."""
    # 1. Fitur Harmoni (Bobot 50%)
    seq = chord_sequence_from_sources(aset, CHORD_SOURCE_PRIORITY)
    harmonic_score = 0.8
    if seq:
        feats = music_features_v2(seq)
        complexity_penalty = (0.7 * feats.get("nondi", 0)) + (0.3 * feats.get("ext", 0)) # Non-diatonik lebih berpengaruh
        harmonic_score = 1.0 - min(complexity_penalty, 1.0)

    # 2. Fitur Lirik (Bobot 50%)
    lyric_feats = _get_lyric_features(lyrics_text)
    # Repetisi struktur (ada reff) & kata komunal = mudah dinyanyikan
    repetition_score = 1.0 if lyric_feats["has_chorus"] else 0.4
    communal_score = min(lyric_feats["communal_words_prop"] * 10, 1.0)
    lyrical_score = (0.6 * repetition_score) + (0.4 * communal_score)

    raw_score = 100 * ((0.5 * harmonic_score) + (0.5 * lyrical_score))
    return _map_0_100_to_1_5(raw_score)

# ==========================================================
# FUNGSI SKOR KREATIVITAS V3 (LEBIH ADIL DAN KOMPREHENSIF)
# ==========================================================
def score_creativity_v3(aset: dict, lyrics_text: str) -> int:
    """
    Skor 1-5 untuk Kreativitas & Orisinalitas (Versi 3).
    Menggabungkan analisis sinyal AI/generik dan keberanian musikal.
    """
    # === 1. Pilar Harmoni (Bobot 50%) ===
    seq = chord_sequence_from_sources(aset, CHORD_SOURCE_PRIORITY)
    harmonic_score = 0.0 # Mulai dari nol
    if seq:
        feats = music_features_v2(seq)
        nondi_rate = feats.get("nondi", 0)
        ext_rate = feats.get("ext", 0)
        trans_uniq = feats.get("big_count", 0)
        num_uniq_chords = len(feats.get("uniq_list", []))

        # Poin dari kompleksitas (maks 1.0)
        complexity_score = (0.5 * min(nondi_rate * 4, 1.0)) + \
                           (0.3 * min(ext_rate * 3, 1.0)) + \
                           (0.2 * min(trans_uniq / 15.0, 1.0))
        
        # Bonus untuk "keberanian"
        if nondi_rate > 0.1 and ext_rate > 0.15:
            complexity_score += 0.15

        harmonic_score = min(complexity_score, 1.0)

        # Penalti untuk "terlalu aman" / sangat standar
        if num_uniq_chords <= 4 and ext_rate == 0 and nondi_rate < 0.05:
            harmonic_score *= 0.4 # Kurangi skor secara signifikan

    # === 2. Pilar Lirik (Bobot 50%) ===
    lyrical_score = 0.0 # Mulai dari nol
    if lyrics_text:
        lyric_feats = _get_lyric_features(lyrics_text)
        signals = analyze_originality_signals(lyrics_text, seq)
        
        # Poin dari orisinalitas (100% - penalti klise)
        originality_score = 1.0 - (signals.get("cliche_score", 0) / 100.0)
        
        # Poin dari kualitas puitis (imajinasi & TTR)
        poetic_score = (0.7 * min(lyric_feats.get("imagery_hits", 0) / 3.0, 1.0)) + \
                       (0.3 * (lyric_feats.get("ttr", 0) - 0.3) / 0.5) # Normalisasi TTR
        
        # Rata-rata dari orisinalitas dan kualitas puitis
        lyrical_score = max(0.0, (0.6 * originality_score) + (0.4 * poetic_score))

    # === 3. Agregasi Final ===
    raw_score = 100 * ((0.5 * harmonic_score) + (0.5 * lyrical_score))
    
    return _map_0_100_to_1_5(raw_score)

def build_suggestions(judul: str, aset: dict) -> dict[str, int]:
    """
    Membangun saran skor untuk KELIMA aspek rubrik, menggunakan logika skor V2.
    """
    @st.cache_data
    def _ex_sy_cached(source_dict): return extract_pdf_text_cached(source_dict)
    @st.cache_data
    def _ex_no_cached(source_dict): return extract_pdf_text_cached(source_dict)
    
    def _ex_sy(): return _ex_sy_cached(aset.get("syair", {}))
    def _ex_no(): return _ex_no_cached(aset.get("notasi", {}))

    src_ly, txt_ly = _pick_text_variant(aset, LYRICS_SCORE_PRIORITY, _ex_sy, _ex_no)
    lyrics_clean = strip_chords(txt_ly) if src_ly in ("syair_chord", "full_score", "extract_notasi") else txt_ly

    s_theme = _map_0_100_to_1_5(theme_score(lyrics_clean) if lyrics_clean else 0.0)
    s_lyric = _lyrics_strength_score_v2(lyrics_clean) if lyrics_clean else 1
    raw_music = MUSIC_RAW_MAP.get(judul)
    s_music = int(_MUSIC_BIN_FUNC(raw_music)) if raw_music is not None else 3
    s_kreativ = score_creativity_v3(aset, lyrics_clean)
    s_jemaat = score_singability_v2(aset, lyrics_clean)

    out: dict[str, int] = {}
    k_tema    = _find_key_like("tema")
    k_lirik   = _find_key_like("lirik")
    k_musik   = _find_key_like("musik")
    k_kreativ = _find_key_like("kreativ")
    k_jemaat  = _find_key_like("jemaat")

    if k_tema:    out[k_tema] = int(s_theme)
    if k_lirik:   out[k_lirik] = int(s_lyric)
    if k_musik:   out[k_musik] = int(s_music)
    if k_kreativ: out[k_kreativ] = int(s_kreativ)
    if k_jemaat:  out[k_jemaat] = int(s_jemaat)
    
    return out

# =========================
# Variant picker
# =========================
def _pick_text_variant(
    song: dict,
    order: list,
    extract_from_syair: Callable[[], str],
    extract_from_notasi: Callable[[], str],
) -> Tuple[str, str]:
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

# =========================
# Penilaian I/O
# =========================
def find_pen_row_index_df(pen_df: pd.DataFrame, juri: str, judul: str, author: str) -> int | None:
    if pen_df.empty: 
        return None
    df = pen_df.copy()
    m = (df["juri"] == juri) & (df["judul"] == judul)
    if "author" in df.columns:
        m &= (df["author"].fillna("") == (author or ""))
    idx = df.index[m].tolist()
    return (idx[0] + 2) if idx else None

def load_existing_scores_for_df(pen_df: pd.DataFrame, juri: str, judul: str, author: str, rubrik_keys):
    if pen_df is None or pen_df.empty:
        return {}
    df = pen_df.rename(columns=lambda c: VARIANTS.get(c, c)).copy()
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
        except:
            pass
    return out


def load_existing_scores_for(juri, judul, author, rubrik_keys):
    ws_pen2 = _ensure_ws(open_sheet(), "Penilaian", ["timestamp","juri","judul","author","total"])
    df = ws_to_df(ws_pen2)
    if df.empty: 
        return {}
    df = df.rename(columns=lambda c: VARIANTS.get(c, c))
    q = (df["juri"] == juri) & (df["judul"] == judul)
    if "author" in df.columns:
        df1 = df[q & (df["author"].fillna("") == (author or ""))].copy()
        if df1.empty:
            df1 = df[q].copy()
    else:
        df1 = df[q].copy()
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
        except:
            pass
    return out

def update_pen_row(ws, headers, rownum: int, juri, judul, author, scores: dict, total: float):
    row = {h:"" for h in headers}
    row["timestamp"] = datetime.datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(timespec="seconds")
    row["juri"] = juri; row["judul"] = judul; row["author"] = author
    for k, v in scores.items():
        if k in headers: row[k] = v
    row["total"] = round(float(total), 2)
    ws.update(f"{rownum}:{rownum}", [[row[h] for h in headers]], value_input_option="USER_ENTERED")

def ensure_pen_headers(ws, rubrik_keys):
    headers = ["timestamp","juri","judul","author"] + rubrik_keys + ["total"]
    return ensure_headers(ws, headers)

def append_pen_row(ws, headers, juri, judul, author, scores, total):
    row = {h:"" for h in headers}
    row["timestamp"] = datetime.datetime.now(ZoneInfo("Asia/Jakarta")).isoformat(timespec="seconds")
    row["juri"] = juri
    row["judul"] = judul
    row["author"] = author
    for k, v in scores.items():
        if k in headers: row[k] = v
    row["total"] = round(float(total), 2)
    ws.append_row([row[h] for h in headers], value_input_option="USER_ENTERED")

# =========================
# Load tables & config  
# =========================
sh, cfg, judges_df, rubrik_df, kw_df, variants_df, songs_df, pen_ws, win_df, idx_ws, idx_df = load_all()
pen_df = get_penilaian_df() # Gunakan fungsi caching

if cfg_get(cfg, "HIDE_HEADER", False, bool):
    st.markdown("""
    <style>
      [data-testid="stToolbar"] { display: none !important; }
      header { visibility: hidden; }
      [data-testid="stHeader"] { display: none; }
      .block-container { padding-top: 1rem; }
    </style>
    """, unsafe_allow_html=True)

FORM_OPEN   = cfg_get(cfg, "FORM_OPEN", True, bool)
SHOW_AUTHOR = cfg_get(cfg, "SHOW_AUTHOR", False, bool)
THEME       = cfg_get(cfg, "THEME", "Tema")
WIN_N       = cfg_get(cfg, "WINNERS_TOP_N", 3, int)
AUTO_WIN    = cfg_get(cfg, "SHOW_WINNERS_AUTOMATIC", True, bool)

DISPLAY_TEXT_PRIORITY = cfg_list(cfg, "DISPLAY_TEXT_PRIORITY",
                                 "lirik_text, full_score, syair_chord, extract_syair, extract_notasi")
THEME_SCORE_PRIORITY  = cfg_list(cfg, "THEME_SCORE_PRIORITY",
                                 "lirik_text, syair_chord, full_score, extract_syair, extract_notasi")
CHORD_SOURCE_PRIORITY = cfg_list(cfg, "CHORD_SOURCE_PRIORITY",
                                 "chords_list, syair_chord, full_score, extract_notasi, extract_syair")
LYRICS_SCORE_PRIORITY = cfg_list(
    cfg, "LYRICS_SCORE_PRIORITY",
    "lirik_text, syair_chord, full_score, extract_syair, extract_notasi"
)
DEFAULT_TEXT_VIEW     = (cfg_get(cfg, "DEFAULT_TEXT_VIEW", "auto", str) or "auto").lower()
SHOW_NILAI_CHIP       = cfg_get(cfg, "SHOW_NILAI_CHIP", True, bool)

JURIS = judges_df["juri"].dropna().astype(str).tolist()
SCORE_EMOJI = {5:"🟩",4:"🟩",3:"🟨",2:"🟧",1:"🟥"}

# =========================
# Songs dict + resolve
# =========================
def build_songs_dict():
    if songs_df.empty: return {}
    df = songs_df.fillna(""); out = {}
    for _, r in df.iterrows():
        title = r["judul"].strip()
        if not title: continue
        out[title] = {
            "author": r.get("pengarang","").strip(),
            "audio":  resolve_source(r.get("audio_path","").strip(),  "audio",  cfg, idx_df, idx_ws),
            "notasi": resolve_source(r.get("notasi_path","").strip(), "notasi", cfg, idx_df, idx_ws),
            "syair":  resolve_source(r.get("syair_path","").strip(),  "syair",  cfg, idx_df, idx_ws),
            "lirik_text":  r.get("lirik_text","").strip(),
            "chords_list": r.get("chords_list","").strip(),
            "full_score":  r.get("full_score","").strip(),
            "syair_chord": r.get("syair_chord","").strip(),
        }
    return out


SONGS  = build_songs_dict()
# Ambil urutan judul langsung dari DataFrame untuk menjaga urutan GSheet
if not songs_df.empty and "judul" in songs_df.columns:
    TITLES = songs_df["judul"].dropna().tolist()
else:
    TITLES = []

# --- PATCH: precompute raw harmonic scores & dynamic binner ---
def _compute_all_music_raw():
    raws_map, vals = {}, []
    for t, aset in SONGS.items():
        try:
            rv = score_harmonic_raw_v2(aset)  # raw 0..100 (punyamu)
        except Exception:
            rv = 0.0
        raws_map[t] = float(rv)
        vals.append(float(rv))
    return raws_map, _make_dynamic_binner(vals)

MUSIC_RAW_MAP, (_MUSIC_BIN_FUNC, _MUSIC_BIN_CUTS) = _compute_all_music_raw()


# =========================
# Winner-only gate
# =========================
def show_winner_only():
    st.markdown("## ⛔️ Form Ditutup")
    try:
        st.image("assets/FLYER_01.png", use_container_width=True)
    except Exception:
        pass
    st.info("Terima kasih. Penjurian sudah ditutup.")
    winners = []
    if AUTO_WIN and not pen_df.empty:
        p = pen_df.rename(columns=lambda c: VARIANTS.get(c, c)).copy()
        if "total" in p.columns:
            p["total"] = pd.to_numeric(p["total"], errors="coerce")
        else:
            tot = 0.0
            for r in RUBRIK:
                k, mx, wb = r["key"], r["max"], r["bobot"]
                if k in p.columns:
                    p[k] = pd.to_numeric(p[k], errors="coerce")
                    tot += p[k].fillna(0)/mx*wb
            p["total"] = tot
        avg = p.groupby("judul", as_index=False)["total"].mean()
        ranking = avg.sort_values("total", ascending=False).head(WIN_N).reset_index(drop=True)
        winners = [f"{i+1}. {row['judul']} — {row['total']:.2f}" for i, row in ranking.iterrows()]
    elif not win_df.empty and "judul" in win_df.columns:
        winners = [f"{r['rank']}. {r['judul']}" if r.get('rank') else f"- {r['judul']}" for _, r in win_df.iterrows()]
    if winners:
        st.markdown("### 🏆 Pemenang")
        st.write("\n".join([f"- {w}" for w in winners]))

if not FORM_OPEN:
    # parse rubrik dulu biar variabel global ada
    RUBRIK  = parse_rubrik(rubrik_df); VARIANTS = parse_variants(variants_df)
    show_winner_only()
    st.stop()

# =========================
# NAV helpers
# =========================
def jump_to(tab, song=None):
    st.session_state["__next_nav"] = tab
    if song:
        st.session_state["preselect_title"] = song
    st.rerun()

if "__next_nav" in st.session_state:
    st.session_state["nav"] = st.session_state.pop("__next_nav")

NAV_OPTS = ["📝 Penilaian", "🔬 Analisis Holistik", "🧮 Nilai Saya", "📊 Hasil & Analitik"]
if "nav" not in st.session_state:
    st.session_state.nav = NAV_OPTS[0]

with st.container():
    st.markdown("<div class='app-sticky'>", unsafe_allow_html=True)
    try:
        st.image(BANNER, width='stretch')
    except Exception:
        pass
    # nav = st.radio("Menu", NAV_OPTS, horizontal=True, label_visibility="collapsed", key="nav")
    st.markdown(f"### 📝 Form Penilaian Juri (**{st.session_state.get('active_juri','-')}**)")  
    st.markdown("</div>", unsafe_allow_html=True)

# ===== Global constructs after NAV header =====
RUBRIK  = parse_rubrik(rubrik_df)
R_KEYS  = [r["key"] for r in RUBRIK]
phrases, keywords = parse_keywords(kw_df)
theme_score, highlight_matches = make_theme_functions(phrases, keywords)
VARIANTS = parse_variants(variants_df)


# ==== Sidebar: juri aktif ====
with st.sidebar:
    st.markdown("### 🧑‍⚖️ Juri aktif")
    # init sekali
    if "active_juri" not in st.session_state:
        st.session_state.active_juri = None

    juri_list = sorted(list(JURIS))
    pick_juri = st.selectbox(
        "Pilih juri",
        options=["— pilih juri —"] + juri_list,
        index=(0 if st.session_state.active_juri is None
               else 1 + juri_list.index(st.session_state.active_juri)),
        help="Pilihan ini berlaku untuk semua menu.",
    )

    if pick_juri != "— pilih juri —":
        if pick_juri != st.session_state.active_juri:
            st.session_state.active_juri = pick_juri
            # reset nilai rubrik ketika ganti juri (opsional):
            for r in RUBRIK:
                st.session_state.pop(f"rate::*::{r['key']}", None)
            st.rerun()
    else:
        st.session_state.active_juri = None

# guard kecil
active_juri = st.session_state.active_juri
if not active_juri:
    st.warning("Silakan pilih **juri** di sidebar untuk mulai menilai.")
    st.stop()

# =========================
# Halaman: Penilaian
# =========================
def _bar_png(series, title="", width=1000, height=420, horizontal=False):
    plt.figure(figsize=(width/100, height/100), dpi=110)
    if horizontal:
        series.sort_values().plot(kind="barh")
    else:
        series.plot(kind="bar")
    plt.title(title)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return buf.getvalue()

def _draw_black_header(canvas_obj, doc, title, subtitle=None):
    W, H = doc.pagesize
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.black)
    canvas_obj.rect(0, H-70, W, 70, fill=1, stroke=0)
    canvas_obj.setFillColor(colors.whitesmoke)
    canvas_obj.setFont("Helvetica-Bold", 18)
    canvas_obj.drawString(40, H-46, title)
    if subtitle:
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.setFillColor(colors.HexColor("#D4AF37"))
        canvas_obj.drawString(40, H-60, subtitle)
    canvas_obj.restoreState()

if "nav" not in st.session_state:
    st.session_state.nav = "📝 Penilaian"

# CSS untuk membuat st.radio terlihat seperti st.tabs
st.markdown("""
<style>
    /* Sembunyikan radio bullets */
    div.row-widget.stRadio > div {flex-direction:row; justify-content: center;}
    div.row-widget.stRadio > div[role="radiogroup"] > label {display: none;}
    div.st-emotion-cache-1f1f5cr {width: auto !important;}
    div.row-widget.stRadio > div[role="radiogroup"] {gap: 10px;}

    /* Style untuk tombol radio */
    div.row-widget.stRadio > div[role="radiogroup"] > div {
        display: inline-block;
        background: transparent;
        border: 1px solid transparent;
        border-radius: 10px 10px 0 0;
        padding: 8px 16px;
        margin: 0;
        line-height: 1.5;
        cursor: pointer;
        border-bottom: 2px solid #ddd;
    }

    /* Style untuk tombol radio yang aktif */
    div.row-widget.stRadio > div[role="radiogroup"] > div[data-baseweb="radio"] > div:first-child[aria-checked="true"] ~ div > p {
         font-weight: 600;
    }
    div.row-widget.stRadio > div[role="radiogroup"] > div[data-baseweb="radio"]:has(div:first-child[aria-checked="true"]) {
        border-bottom: 2px solid #1c64f2; /* Warna biru Streamlit */
    }
</style>
""", unsafe_allow_html=True)

NAV_OPTS = ["📝 Penilaian", "🔎 Analisis Syair", "🎼 Analisis Musik", "🧮 Nilai Saya", "📊 Hasil & Analitik"]
nav_selection = st.radio("Menu", NAV_OPTS, key="nav", horizontal=True, label_visibility="collapsed")

# ==========================================================
# PEMILIHAN LAGU GLOBAL (DITEMPATKAN DI SINI)
# ==========================================================
st.markdown("---") # Pemisah visual

# --- 1. Siapkan data lagu yang sudah dinilai oleh juri aktif (DARI DATA TERBARU) ---
# Baca data terbaru dari GSheet untuk memastikan skor yang baru disimpan langsung terlihat
ws_pen_fresh = _ensure_ws(open_sheet(), "Penilaian")

# --- 1. Siapkan data lagu yang sudah dinilai oleh juri aktif (DARI CACHE SESI) ---
pen_df_latest = get_penilaian_df() # Gunakan fungsi caching kita
pen_mine = pen_df_latest[pen_df_latest["juri"] == active_juri] if "juri" in pen_df_latest.columns else pd.DataFrame()

scores_mine = {}
if not pen_mine.empty:
    pen_mine = pen_mine.sort_values("timestamp").drop_duplicates(subset="judul", keep="last")
    # Pastikan kolom 'total' adalah numerik sebelum membuat dictionary untuk menghindari error
    pen_mine['total'] = pd.to_numeric(pen_mine['total'], errors='coerce')
    scores_mine = pd.Series(pen_mine.total.values, index=pen_mine.judul).dropna().to_dict()

# --- 2. Buat daftar label yang sudah diformat ---
formatted_labels = []
# Loop melalui DataFrame untuk mendapatkan akses ke kolom 'Alias' dan 'judul'
for index, row in songs_df.dropna(subset=['judul']).iterrows():
    title = row['judul']
    # Ambil nilai dari kolom 'Alias', jika tidak ada/kosong, gunakan nomor baris biasa
    alias = row.get('Alias')
    prefix = alias if alias else f"{index + 1:02d}"

    author = SONGS.get(title, {}).get("author", "")
    # Gunakan 'prefix' yang sudah kita tentukan untuk membuat label
    label = f"#{prefix} | {title}"

    if SHOW_AUTHOR and author:
        label += f", oleh {author}"

    if title in scores_mine:
        score = scores_mine[title]
        label = f"✅ {label} (Skor: {float(score):.1f})"
    else:
        label = f"📝 {label}"
    formatted_labels.append(label)

# --- 3. Atasi pre-selection dari tab lain (mis. "Nilai Saya") ---
if "selected_title" not in st.session_state:
    st.session_state["selected_title"] = TITLES[0] if TITLES else None
# Honor preselection if it exists
pre_selected_title = st.session_state.get("preselect_title")
if pre_selected_title and pre_selected_title in TITLES:
    st.session_state["selected_title"] = pre_selected_title
    st.session_state.pop("preselect_title", None) # Hapus setelah digunakan

current_index = 0
if st.session_state["selected_title"]:
    try:
        current_index = TITLES.index(st.session_state["selected_title"])
    except ValueError:
        pass

# --- 4. Tampilkan selectbox global ---
selected_label = st.selectbox(
    "Pilih Lagu untuk Dinilai/Dianalisis",
    formatted_labels,
    index=current_index,
    key="global_song_selector",
)

# --- 5. Ambil kembali judul asli dari label yang dipilih (LOGIKA BARU) ---
# Logika ini lebih kuat karena mencari pemisah '|'
# dan mengambil semua teks di kanannya, lalu membersihkan sisanya.
try:
    # Ambil bagian setelah '|'
    judul_raw = selected_label.split('|', 1)[1]
    # Bersihkan dari info skor atau pengarang
    judul = re.split(r"\s*\(Skor:|\s*,\s*oleh", judul_raw)[0].strip()
except IndexError:
    # Fallback jika suatu saat format label tidak mengandung '|'
    judul = selected_label.strip()

# --- 6. Simpan judul asli ke session state untuk konsistensi di semua tab ---
st.session_state["selected_title"] = judul
aset = SONGS.get(judul, {})
pengarang = aset.get("author", "")
st.markdown("---") # Pemisah visual

st.markdown(f"**Judul:** {judul}")
genre = detect_genre(chord_sequence_from_sources(aset, CHORD_SOURCE_PRIORITY))
st.markdown(f"**Detected Genre:** {genre}")

# ====== AUDIO (Streaming-first dari Google Drive atau local path) ======
audio_src = aset.get("audio", {})
if audio_src and audio_src.get("mode"):
    audio_bytes, audio_mime = None, audio_src.get("mime")

    # 1) Coba via Drive API (authed) kalau ada fileId
    if audio_src.get("id"):
        if not audio_mime:
            meta = drive_get_meta(audio_src["id"])
            audio_mime = (meta or {}).get("mimeType", audio_mime)
        audio_bytes = drive_download_bytes(audio_src["id"])

    # 2) Fallback ke URL langsung HANYA jika file memang public.
    #    Deteksi kasar: jika respons mengandung "<html" -> itu bukan audio.
    if audio_bytes is None and audio_src.get("direct"):
        raw = fetch_bytes_cached(audio_src["direct"])  # tanpa auth
        if raw and raw[:500].lower().find(b"<html") == -1:
            audio_bytes = raw

    if audio_bytes:
        # format opsional; streamlit bisa deteksi sendiri.
        st.audio(audio_bytes)  # remove explicit format to let Streamlit infer
    else:
        st.warning(
            "Audio tidak bisa diputar. Pastikan folder/file Google Drive "
            "dibagikan ke service account **Viewer**, atau jadikan file public."
        )
else:
    st.info("Audio belum tersedia (isi kolom `audio_path` di sheet `Songs`).")


if nav_selection == "📝 Penilaian":
    with st.container():

        st.markdown(f"**Judul:** {judul}" + (f" • **Pengarang:** _{pengarang}_" if (SHOW_AUTHOR and pengarang) else ""))
        
        # --- Prefill nilai existing (fresh, bukan cache awal) ---
        prefill_key = f"__prefilled_auto::{active_juri}::{judul}::{pengarang}"
        if not st.session_state.get(prefill_key, False):
            ws_pen_fresh = _ensure_ws(open_sheet(), "Penilaian", ["timestamp","juri","judul","author","total"])
            pen_df_latest = ws_to_df(ws_pen_fresh)
            prev_scores = load_existing_scores_for_df(pen_df_latest, active_juri, judul, pengarang, R_KEYS)
            if prev_scores:
                limits = {r["key"]: (int(r["min"]), int(r["max"])) for r in RUBRIK}
                for k, v in prev_scores.items():
                    lo, hi = limits.get(k, (1, 5))
                    if v is not None and lo <= v <= hi:
                        st.session_state[f"rate::{judul}::{k}"] = int(v)
                st.caption("Nilai sebelumnya dimuat otomatis. Silakan ubah jika perlu.")
            st.session_state[prefill_key] = True


        # Mode edit dari Riwayat
        edit_tg = st.session_state.get("__edit_target")
        is_edit_mode = bool(edit_tg and edit_tg.get("judul") == judul and (edit_tg.get("author","") == pengarang))
        if is_edit_mode:
            st.info("✏️ **Mode edit**: penyimpanan akan *memperbarui* penilaian yang sudah ada, bukan membuat baris baru.")
            if not st.session_state.get("__prefilled", False):
                _old = pen_df[(pen_df["juri"] == active_juri) & (pen_df["judul"] == judul)]
                if "author" in _old.columns:
                    _old = _old[_old["author"].fillna("") == (pengarang or "")]
                if not _old.empty:
                    row_old = _old.iloc[0]
                    for r in RUBRIK:
                        k = r["key"]
                        v = pd.to_numeric(row_old.get(k), errors="coerce")
                        if pd.notna(v):
                            st.session_state[f"rate::{judul}::{k}"] = int(v)
                st.session_state["__prefilled"] = True


        # SYAIR (PDF)
        with st.expander("📝 Syair (klik untuk buka)", expanded=False):
            png = pdf_first_page_png_bytes(aset["syair"], dpi=160)
            if png: st.image(png, caption="Preview halaman 1", width='stretch')
            if st.toggle("Tampilkan PDF penuh di halaman ini", key=f"t_full_syair::{judul}"):
                embed_pdf(aset["syair"], height=720)

        # NOTASI (PDF)
        with st.expander("📄 Notasi (klik untuk buka)", expanded=False):
            png = pdf_first_page_png_bytes(aset["notasi"], dpi=160)
            if png: st.image(png, caption="Preview halaman 1", width='stretch')
            if st.toggle("Tampilkan PDF penuh di halaman ini", key=f"t_full_notasi::{judul}"):
                embed_pdf(aset["notasi"], height=720)

        # SYAIR (teks & highlight)
        with st.expander("🖍️ Syair (teks & highlight tema)", expanded=False):
            view_key = f"view_variant::{judul}"
            if view_key not in st.session_state:
                st.session_state[view_key] = DEFAULT_TEXT_VIEW
            opt_map = {"auto":"Otomatis","full":"Full (rapih)","syair_chord":"Syair + Chord","lirik":"Syair saja","chords":"Chord saja"}
            sel_view = st.radio("Tampilan teks", list(opt_map.keys()),
                                format_func=lambda k: opt_map[k],
                                index=list(opt_map.keys()).index(st.session_state[view_key]),
                                horizontal=True, key=f"radio_{view_key}")
            st.session_state[view_key] = sel_view

            def _extract_syair():  return extract_pdf_text_cached(aset["syair"]) if aset.get("syair") else ""
            def _extract_notasi(): return extract_pdf_text_cached(aset["notasi"]) if aset.get("notasi") else ""

            if sel_view == "auto":
                src, text_for_view = _pick_text_variant(aset, DISPLAY_TEXT_PRIORITY, _extract_syair, _extract_notasi)
            elif sel_view == "full":
                src, text_for_view = _pick_text_variant(aset, ["full_score","syair_chord","lirik_text","extract_syair","extract_notasi"], _extract_syair, _extract_notasi)
            elif sel_view == "syair_chord":
                src, text_for_view = _pick_text_variant(aset, ["syair_chord","full_score","lirik_text","extract_syair","extract_notasi"], _extract_syair, _extract_notasi)
            elif sel_view == "lirik":
                src, text_for_view = _pick_text_variant(aset, ["lirik_text","syair_chord","full_score","extract_syair","extract_notasi"], _extract_syair, _extract_notasi)
            else:
                src, text_for_view = ("chords_list", aset.get("chords_list",""))

            if sel_view == "chords":
                chips = [c.strip() for c in (text_for_view or "").split(",") if c.strip()]
                if chips:
                    st.markdown(" ".join([f"<span style='display:inline-block;padding:.25rem .5rem;border:1px solid #ddd;border-radius:999px;margin:.2rem .25rem'>{c}</span>" for c in chips]),
                                unsafe_allow_html=True)
                else:
                    st.info("Belum ada daftar chord.")
            else:
                hide_chords = st.toggle("Sembunyikan chord di preview", value=False, key=f"hidech::{judul}")
                shown = strip_chords(text_for_view) if (hide_chords and src in ("syair_chord","full_score","extract_notasi")) else text_for_view
                st.markdown("<div style='padding:.8rem; border:1px solid #eee; border-radius:10px; background:#fff'>"
                            + highlight_matches(shown) + "</div>", unsafe_allow_html=True)
                st.caption(f"Sumber: **{src}**")

            src_sc, text_for_score = _pick_text_variant(aset, THEME_SCORE_PRIORITY, _extract_syair, _extract_notasi)
            if src_sc in ("syair_chord","full_score","extract_notasi"):
                text_for_score = strip_chords(text_for_score)
            st.caption(f"Skor tema (prioritas THEME_SCORE_PRIORITY): **{theme_score(text_for_score):.2f}**")
            
        
        # ========= UI helper: selectable rubric cards =========
        # ========= Compact rubric accordion with clickable rows (no radio) =========
        BADGE = {5:"🟩", 4:"🟩", 3:"🟨", 2:"🟧", 1:"🟥"}  # emoji warna simpel & konsisten di semua OS
        OPT_BG  = {5:"#E6F9ED", 4:"#EFFBF3", 3:"#FFF8D9", 2:"#FFECE4", 1:"#FDE2E2"}
        OPT_BRD = {5:"#16A34A", 4:"#22C55E", 3:"#F59E0B", 2:"#F97316", 1:"#EF4444"}

        def render_rubrik_compact(r: dict, *, judul: str, saran_map: dict):
            """
            r: {'key','aspek','bobot','min','max','desc':{1..5:str}}
            judul: judul lagu aktif
            saran_map: mis. {'tema':4,'musik':5,'lirik':4}
            """
            wkey  = f"rate::{judul}::{r['key']}"
            cur   = st.session_state.get(wkey)  # None/1..5

            # --- Header accordion menampilkan aspek + nilai terpilih
            pill = f"{BADGE.get(cur,'◻️')} {cur}" if cur else "—"
            with st.expander(f"{r['aspek']} • Bobot {int(r['bobot'])}% • Nilai: {pill}", expanded=False):

                # info saran (kecil, hanya bila kosong)
                if (r["key"] in saran_map) and (cur is None):
                    st.caption(f"Saran: **{int(saran_map[r['key']])}**")

                # 5 → 1 baris tipis
                for score in [5,4,3,2,1]:
                    txt = r['desc'].get(score) or ""
                    if not txt:
                        continue

                    selected = (cur == score)
                    bg = OPT_BG[score] if selected else "#fff"
                    br = OPT_BRD[score] if selected else "#e5e7eb"

                    # 1 baris = tombol full width (supaya bisa diklik + hemat ruang)
                    # label berisi [badge angka] + teks deskripsi
                    label = f"{BADGE[score]} {score} — {txt}"

                    # CSS global ringan agar tombol tampak seperti 'row' berwarna
                    st.write(
                        f"""
                        <style>
                        .rb-btn-{wkey.replace(':','-')}-{score} > button {{
                            width: 100%; text-align: left;
                            padding: .6rem .85rem; border-radius: 10px;
                            border: 2px solid {br}; background: {bg};
                            font-weight: { '600' if selected else '400' };
                        }}
                        </style>
                        """,
                        unsafe_allow_html=True
                    )
                    if st.button(label, key=f"{wkey}::btn::{score}",
                                use_container_width=True,
                                type=("primary" if selected else "secondary"),
                                help=f"Pilih nilai {score}",
                                ):
                        st.session_state[wkey] = score
                        st.rerun()

        # ==== Context utk RUBRIK ====
        # Ambil judul lagu yang sudah dipilih di header form.
        try:
            current_title = judul          # variabel yang kamu pakai di header
        except NameError:
            # fallback kalau variabel `judul` belum ada (mis. saat awal load)
            current_title = st.session_state.get("pick_song") or list(SONGS.keys())[0]

        pick = current_title
        aset = SONGS.get(pick, {})
        pengarang = aset.get("author", "")

        # Saran otomatis berdasarkan logika terbaru
        SARAN = build_suggestions(pick, aset)

        # (opsional) fallback emoji kalau belum ada
        SCORE_EMOJI = globals().get("SCORE_EMOJI", {5:"🟩",4:"🟩",3:"🟨",2:"🟧",1:"🟥"})

        # Supaya bagian lain yang masih refer ke `judul` tetap aman:
        judul = pick
        

        # ==========================================================
        # PANEL BARU: ANALISIS ORISINALITAS
        # ==========================================================
        with st.expander("🕵️‍♂️ Analisis Orisinalitas (Bantuan untuk Juri)"):
            # 1. Analisis Sinyal AI / Generik
            st.subheader("Sinyal Konten Generik / Potensi AI")
            lyrics_for_analysis = get_clean_lyrics_for_song(aset)
            chords_for_analysis = chord_sequence_from_sources(aset, CHORD_SOURCE_PRIORITY)
            signals = analyze_originality_signals(lyrics_for_analysis, chords_for_analysis)

            c1, c2, c3 = st.columns(3)
            c1.metric("Skor Klise (0-100)", f"{signals['cliche_score']}", help="Semakin tinggi, semakin banyak menggunakan frasa umum. Skor > 50 adalah penanda kuat.")
            c2.metric("Keragaman Kata (TTR)", f"{signals['ttr']:.2f}", help="Rasio kata unik terhadap total kata. Nilai yang sangat rendah (<0.3) atau sangat tinggi (>0.8) bisa jadi tidak wajar.")
            c3.metric("Jumlah Akor Unik", f"{signals['num_chords']}", help="Lagu yang terlalu sederhana (< 4 akor) atau terlalu kompleks bisa jadi pertanda.")

            st.markdown("---")

            # 2. Analisis Plagiarisme Internal
            st.subheader("Perbandingan dengan Peserta Lain")
            with st.spinner("Membandingkan dengan lagu lain..."):
                df_similar = calculate_internal_similarity(judul, SONGS)
            
            if not df_similar.empty:
                st.write("3 lagu lain dalam kompetisi dengan kemiripan tertinggi:")
                st.dataframe(df_similar, hide_index=True, use_container_width=True)
            else:
                st.caption("Belum cukup data untuk perbandingan internal.")

            st.markdown("---")

            # 3. Alat Bantu Pengecekan Eksternal
            st.subheader("Alat Pengecekan Eksternal")
            if lyrics_for_analysis:
                # Ambil cuplikan lirik yang paling mungkin unik (tidak terlalu pendek/panjang)
                lines = [line.strip() for line in lyrics_for_analysis.split('\n') if 20 < len(line.strip()) < 70]
                search_query = lines[0] if lines else lyrics_for_analysis.split('\n')[0]
                
                query_with_quotes = '"' + search_query + '"'
                google_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query_with_quotes)}"
                st.link_button("Cari Cuplikan Lirik di Google ↗", google_url)
            
            if chords_for_analysis:
                chord_query = " ".join(chords_for_analysis[:8]) # Ambil 8 akor pertama
                chord_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(f'{chord_query} chord progression')}"
                st.link_button("Cari Progresi Akor di Google ↗", chord_url)


        # ---------- RUBRIK (layout mobile-friendly: expander per-aspek) ----------
        st.markdown("---")
        # st.subheader(f"Rubrik Penilaian ({THEME})")
        st.subheader(f"Rubrik Penilaian")

        sum_rows, total_ui = [], 0.0
        scores_ui = {}
        for r in RUBRIK:
            render_rubrik_compact(r, judul=pick, saran_map=SARAN)
            wkey = f"rate::{pick}::{r['key']}"
            val = st.session_state.get(wkey)
            scores_ui[r["key"]] = None if val is None else int(val)

            v = scores_ui[r["key"]] or 0
            w = (v / max(int(r["max"]),1)) * float(r["bobot"])
            total_ui += w
            sum_rows.append([r["aspek"], r["bobot"], v if v else "-", f"{w:.2f}"])
            
        # tombol saran (tetap hanya isi yang kosong)
        if st.button("✨ Terapkan saran (hanya yang kosong)"):

            # 1. Tentukan kunci (keys) dari rubrik yang ingin di exclude
            kunci_kreativitas = _find_key_like("kreativ")
            kunci_jemaat = _find_key_like("jemaat")
            keys_to_exclude = {kunci_kreativitas, kunci_jemaat} # Gunakan set untuk pengecekan cepat

            # 2. Loop melalui saran, tapi skip kunci exclude
            for k, v in SARAN.items():
                # Jika kunci (k) ada di dalam daftar exclude, skip
                if k in keys_to_exclude:
                    continue 

                wkey = f"rate::{pick}::{k}"
                if st.session_state.get(wkey) is None:
                    st.session_state[wkey] = int(v)

            st.rerun()

        all_ok = all(scores_ui.get(x["key"]) is not None for x in RUBRIK)
        st.markdown(f"**Total skor sementara:** {total_ui:.2f} / 100")


        # --- KONFIRMASI & SUBMIT ---
        ss = st.session_state
        modal_key = f"__confirm_open::{active_juri}::{judul}"
        if modal_key not in ss:
            ss[modal_key] = False

        # GUNAKAN DATA TERBARU (FRESH) UNTUK SEMUA PENGECEKAN
        ws_pen_fresh = _ensure_ws(open_sheet(), "Penilaian")
        pen_df_latest = ws_to_df(ws_pen_fresh)

        # Cek apakah ada skor yang sudah terisi sebelumnya dari data terbaru
        existing_scores = load_existing_scores_for_df(pen_df_latest, active_juri, judul, pengarang, R_KEYS)

        just_saved_for_this_song = st.session_state.get(f"__just_saved::{judul}", False)

        # Tampilkan pesan HANYA JIKA ADA SKOR YANG DITEMUKAN atau baru saja disimpan
        if existing_scores or just_saved_for_this_song:
            st.info(
                f"Anda sudah pernah menilai **{judul}**. Menekan **Konfirmasi & Simpan** akan **memperbarui** penilaian yang sudah ada."
            )
        else:
            st.caption("Belum ada penilaian Anda untuk lagu ini. Menyimpan akan membuat entri baru.")


        if not all_ok:
            st.warning("Lengkapi semua nilai dulu sebelum submit.")

        st.button(
            "💾 Tinjau & Submit",
            type="primary",
            disabled=not all_ok,
            on_click=lambda: ss.update({modal_key: True})
        )

        if ss[modal_key]:
            st.markdown("### ✅ Konfirmasi Penilaian")
            st.write(
                f"**Juri:** {active_juri} • **Judul:** {judul}"
                + (f" • **Pengarang:** _{pengarang}_" if (SHOW_AUTHOR and pengarang) else "")
            )

            df_confirm = pd.DataFrame(sum_rows, columns=["Aspek","Bobot %","Nilai","Skor Terbobot"])
            for col in ["Bobot %","Nilai","Skor Terbobot"]:
                df_confirm[col] = df_confirm[col].apply(fmt_num)

            st.dataframe(
                df_confirm,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Aspek": st.column_config.TextColumn("Aspek", width="stretch"),
                    "Bobot %": st.column_config.NumberColumn("Bobot %", format="%d"),
                    "Nilai": st.column_config.NumberColumn("Nilai", format="%d"),
                    "Skor Terbobot": st.column_config.NumberColumn("Skor Terbobot", format="%.2f"),
                },
            )
            
            st.write(f"**Total:** {fmt_num(total_ui)} / 100")

            c_ok, c_cancel = st.columns([1,1])
            with c_ok:
                if st.button("✅ Konfirmasi & Simpan", key=f"btn_save::{modal_key}"):
                    # Ambil worksheet & DF terbaru
                    ws_pen_fresh = _ensure_ws(open_sheet(), "Penilaian", ["timestamp","juri","judul","author","total"])
                    pen_df_latest = ws_to_df(ws_pen_fresh)
                    headers = ensure_pen_headers(ws_pen_fresh, R_KEYS)

                    # Cek apakah baris sudah ada
                    rownum = find_pen_row_index_df(pen_df_latest, active_juri, judul, pengarang)

                    if rownum:
                        # Jika baris sudah ada, langsung UPDATE
                        update_pen_row(
                            ws_pen_fresh, headers, rownum,
                            active_juri, judul, pengarang,
                            {k: scores_ui[k] for k in R_KEYS}, total_ui
                        )
                        st.success("Penilaian berhasil diperbarui.")
                    else:
                        # Jika baris belum ada, APPEND (buat baru)
                        append_pen_row(
                            ws_pen_fresh, headers,
                            active_juri, judul, pengarang,
                            {k: scores_ui[k] for k in R_KEYS}, total_ui
                        )
                        st.success("Penilaian baru berhasil disimpan.")

                    if 'pen_df_cached' in st.session_state:
                        del st.session_state.pen_df_cached
                    
                    # untuk membersihkan state setelah simpan
                    ss.pop(f"__prefilled_auto::{active_juri}::{judul}::{pengarang}", None)
                    for r in RUBRIK:
                        ss.pop(f"rate::{judul}::{r['key']}", None)
                    ss[modal_key] = False
                    ss.pop("__edit_target", None)
                    ss.pop("__prefilled", None)
                    st.session_state["__scroll_top"] = True
                    
                    st.rerun()

            with c_cancel:
                st.button("❌ Batal", on_click=lambda: ss.update({modal_key: False}))


# ==============================================================================
# Page: Analisis Syair (FINAL ENHANCED VERSION)
# ==============================================================================
if nav_selection == "🔎 Analisis Syair":
    with st.container():
        st.title("🔍 Analisis Kekuatan Syair")
        st.markdown(f"Menganalisis lirik berdasarkan relevansinya terhadap tema **“{THEME}”** dan latar belakang teologis dari Efesus 5:15-16.")
        
        with st.expander("💡 Panduan Membaca Analisis"):
            st.markdown("""
            - **Skor Tema (1-5):** Mengukur **Relevansi Literal**. Seberapa sering kata kunci dari sheet `Keywords` muncul.
            - **Kekuatan Lirik (1-5):** Mengukur **Kualitas Puitis & Teologis**. Seberapa indah, dalam, dan cerdas lirik menyampaikan pesan.
            """)
        st.markdown("---")

        # --- 1. Data Processing dengan Skor v2 ---
        # (Gunakan @st.cache_data agar tidak dihitung ulang setiap interaksi)
        @st.cache_data
        def process_lyrics_data():
            rows = []
            for t, aset in SONGS.items():
                # Definisikan fungsi helper di dalam scope agar aset terikat
                def _ex_sy(): return extract_pdf_text_cached(aset.get("syair", {}))
                def _ex_no(): return extract_pdf_text_cached(aset.get("notasi", {}))
                
                src_sc, txt = _pick_text_variant(aset, LYRICS_SCORE_PRIORITY, _ex_sy, _ex_no)
                txt_clean = strip_chords(txt) if src_sc in ("syair_chord", "full_score", "extract_notasi") else txt
                
                rows.append({
                    "Judul": t,
                    "Pengarang": aset.get("author", ""),
                    "Syair": txt_clean,
                    # "Skor Tema (1-5)": theme_score(txt_clean) if txt_clean else 0.0,
                    "Skor Tema (1-5)": _map_0_100_to_1_5(theme_score(txt_clean)) if txt_clean else 1,
                    "Kekuatan Lirik (1-5)": _lyrics_strength_score_v2(txt_clean) if txt_clean else 1
                })
            return pd.DataFrame(rows).sort_values(["Kekuatan Lirik (1-5)", "Skor Tema (1-5)"], ascending=False).reset_index(drop=True)

        df_lyrics = process_lyrics_data()
        
        # --- Fungsi Helper Baru untuk Analisis Naratif Tema ---
        def explain_theme_v2(text: str, score: float) -> str:
            """
            Menciptakan narasi yang 'cantik' khusus untuk koneksi ke tema.
            """
            t_norm = _norm_id(text)
            
            # Kalimat pembuka berdasarkan skor
            if score >= 5:
                summary = "Lirik ini **sangat meresonansi** dengan tema, menangkap esensi utamanya secara mendalam."
            elif score >= 3:
                summary = "Syair ini memiliki **koneksi yang baik** dengan tema, dengan beberapa poin kunci yang tersampaikan jelas."
            else:
                summary = "Koneksi lirik dengan tema **cukup terlihat**, meskipun ada beberapa area yang bisa diperdalam lagi."

            points = []
            
            # Point 1: Koneksi ke frasa utama "Waktu Bersama Harta Berharga"
            if "harta" in t_norm and "berharga" in t_norm and "waktu" in t_norm and "bersama" in t_norm:
                points.append("✅ **Tepat Sasaran:** Secara eksplisit menyebutkan 'waktu bersama' sebagai 'harta berharga', langsung menjawab inti tema.")
            elif "waktu" in t_norm and "bersama" in t_norm:
                points.append("✅ **Relevan:** Menekankan pentingnya 'waktu bersama' sebagai fokus utama dalam keluarga.")

            # Point 2: Kedalaman Teologis (Efesus 5)
            if any(w in t_norm for w in ["bijaksana", "arif", "pergunakan", "saksama"]):
                 points.append("📖 **Kedalaman Teologis:** Menangkap gema dari Efesus 5 dengan mengajak pendengar untuk menggunakan waktu secara 'bijaksana' dan 'arif'.")

            # Point 3: Konteks Modern (Distraksi vs Persekutuan)
            if any(d in t_norm for d in _DISTRACTIONS):
                if any(w in t_norm for w in ["persekutuan", "hadir", "dekat"]):
                    points.append("📱 **Sangat Kontekstual:** Berhasil mengangkat pergumulan modern (misal: 'dunia maya', 'sibuk') dan menawarkankan 'persekutuan' sebagai solusinya.")
                else:
                    points.append("⚠️ **Konteks Kurang Solutif:** Menyinggung tantangan modern, namun perlu lebih kuat menawarkan iman dan kebersamaan sebagai jawaban.")

            if not points:
                points.append("📝 **Pesan Umum:** Menyampaikan pesan positif tentang keluarga, namun kaitan spesifik dengan 'mempergunakan waktu' bisa lebih dieksplisitkan.")

            # Gabungkan menjadi HTML
            html = f"<div style='line-height:1.7;'>{summary}<ul>"
            for point in points[:2]: # Maksimal 2 poin terkuat untuk tema
                html += f"<li style='margin-bottom: 5px;'>{point}</li>"
            html += "</ul></div>"
            return html
        
        # --- Fungsi untuk Insight Statistik Umum ---
        def generate_lyrics_insights(df: pd.DataFrame) -> str:
            if df.empty or len(df) < 2: return "<p><i>Belum cukup data untuk menghasilkan insight.</i></p>"
            
            avg_theme_score = df['Skor Tema (1-5)'].mean()
            top_lyric_score_count = df['Kekuatan Lirik (1-5)'].value_counts().idxmax()
            
            insights = [
                f"🎯 **Fokus Tema:** Secara umum, para peserta berhasil menangkap tema dengan baik, terbukti dari **rata-rata Skor Tema sebesar {avg_theme_score:.0f}/100**.",
                f"⭐ **Kualitas Puitis:** Mayoritas lagu memiliki **Kekuatan Lirik di level {top_lyric_score_count}/5**, menunjukkan standar penulisan lirik yang solid di antara peserta.",
                f"💡 **Kunci Keunggulan:** Lagu dengan skor tertinggi seringkali tidak hanya relevan secara tema, tetapi juga mampu **mengintegrasikan kedalaman teologis (dari Efesus 5)** dan menyajikan **solusi iman terhadap tantangan modern**.",
                f"🤔 **Area Pengembangan:** Beberapa lirik sudah menyentuh tema 'waktu bersama', namun seringkali belum sampai pada esensi 'menggunakan waktu dengan bijaksana', yang merupakan peluang untuk pendalaman makna."
            ]
            
            html = "<div style='line-height:1.7;'><ul>"
            for insight in insights:
                html += f"<li style='margin-bottom: 8px;'>{insight}</li>"
            html += "</ul></div>"
            return html

        tab_analisis, tab_statistik = st.tabs(["✍️ Analisis per Lagu", "📊 Statistik Umum"])

        with tab_analisis:
            if not df_lyrics.empty:
                try:
                    row = df_lyrics[df_lyrics["Judul"] == judul].iloc[0]
                    
                    st.header(f"Analisis Mendalam: *{judul}*", divider="blue")
                    col1, col2 = st.columns([6, 4])

                    with col1:
                        st.subheader("Teks Syair dengan Konteks")
                        syair_highlighted = highlight_lyrics_v2(row["Syair"])
                        st.markdown(f"<div style='height: 500px; overflow-y: auto; padding: 1rem; border:1px solid #eee; border-radius:12px; background:#f9fafb; line-height:1.8;'>{syair_highlighted}</div>", unsafe_allow_html=True)
                        st.caption("""
                            <div style='margin-top: 10px; line-height: 1.5;'>
                            <span style='background-color:#FFD700; padding: 2px 5px; border-radius:4px;'>Tema & Teologi</span>
                            <span style='background-color:#87CEEB; padding: 2px 5px; border-radius:4px;'>Iman & Spiritualitas</span>
                            <span style='background-color:#98FB98; padding: 2px 5px; border-radius:4px;'>Keluarga & Relasi</span>
                            <span style='background-color:#FFA07A; padding: 2px 5px; border-radius:4px;'>Imajinasi Puitis</span>
                            <span style='background-color:#D3D3D3; padding: 2px 5px; border-radius:4px;'>Tantangan Modern</span>
                            </div>
                        """, unsafe_allow_html=True)

                    with col2:
                        st.subheader("Skor & Analisis Naratif")
                        with st.container(border=True):
                            st.metric("Skor Tema (Relevansi Literal)", f"{int(row['Skor Tema (1-5)'])}/5")
                            st.markdown(explain_theme_v2(row["Syair"], row['Skor Tema (1-5)']), unsafe_allow_html=True)
                        with st.container(border=True):
                            st.metric("Skor Kekuatan Lirik (Kualitas Puitis)", f"{row['Kekuatan Lirik (1-5)']}/5")
                            st.markdown(explain_lyrics_strength_v2(row["Syair"]), unsafe_allow_html=True)
                except IndexError:
                    st.warning(f"Data analisis untuk lagu '{judul}' tidak ditemukan.")
            else:
                st.info("Belum ada data syair yang dapat dianalisis.")

        with tab_statistik:
            st.subheader("💡 Insight Keseluruhan dari Data Lirik")
            with st.container(border=True):
                st.markdown(generate_lyrics_insights(df_lyrics), unsafe_allow_html=True)
            
            st.subheader("Visualisasi Data Agregat")
            st.markdown("##### Ringkasan Skor Seluruh Lagu")
            cols_show = ["Judul"] + (["Pengarang"] if SHOW_AUTHOR else []) + ["Skor Tema (1-5)", "Kekuatan Lirik (1-5)"]
            st.dataframe(df_lyrics[cols_show], hide_index=True, use_container_width=True,
                column_config={
                    "Skor Tema (1-5)": st.column_config.ProgressColumn("Skor Tema", format="%d", min_value=1, max_value=5),
                    "Kekuatan Lirik (1-5)": st.column_config.NumberColumn("Kekuatan Lirik", format="%d ⭐")
                })
            c1_viz, c2_viz = st.columns(2)
            with c1_viz:
                st.markdown("##### Distribusi Kekuatan Lirik")
                hist_l = px.histogram(df_lyrics, x="Kekuatan Lirik (1-5)", nbins=5, text_auto=True)
                hist_l.update_layout(yaxis_title="Jumlah Lagu", xaxis_title="Skor", title_text="Frekuensi Skor Kualitas Lirik")
                st.plotly_chart(hist_l, use_container_width=True)
            with c2_viz:
                st.markdown("##### Peta Kualitas Syair")
                sc = px.scatter(df_lyrics, x="Skor Tema (1-5)", y="Kekuatan Lirik (1-5)",
                                hover_name="Judul", size="Kekuatan Lirik (1-5)", color="Kekuatan Lirik (1-5)")
                sc.update_layout(xaxis_title="Relevansi Tema (1-5)", yaxis_title="Kualitas Puitis & Teologis (1-5)", title_text="Relevansi vs. Kualitas")
                st.plotly_chart(sc, use_container_width=True)
    
# ==============================================================================
# Page: Analisis Musik (FINAL ENHANCED VERSION)
# ==============================================================================
if nav_selection == "🎼 Analisis Musik":
    with st.container():
        st.title("🎼 Analisis Harmoni & Struktur Musik")
        st.markdown("Menganalisis kekayaan harmoni, kompleksitas progresi, dan karakteristik musikal lainnya dari setiap lagu berdasarkan data akor.")
        st.markdown("---")
        
        @st.cache_data
        def process_music_data():
            rows = []
            for t, aset in SONGS.items():
                seq = chord_sequence_from_sources(aset, CHORD_SOURCE_PRIORITY)
                feats = music_features_v2(seq) if seq else {"uniq_list":[], "big_count":0, "ext":0, "slash":0, "nondi":0}
                raw  = score_harmonic_raw_v2(aset) if 'score_harmonic_raw_v2' in globals() else 0.0
                key_name, key_conf = detect_key_from_chords(seq)
                genre = detect_genre(seq)
                rows.append({
                    "Judul": t, "Pengarang": aset.get("author",""), "raw": float(raw),
                    "Skor Kekayaan Akor (1-5)": _MUSIC_BIN_FUNC(MUSIC_RAW_MAP.get(t, 0.0)) if 'MUSIC_RAW_MAP' in globals() else 3,
                    "Jumlah_Akor_Unik": int(len(set(feats["uniq_list"]))), "Transisi_Unik": int(feats["big_count"]),
                    "%Extensions": f"{feats.get('ext',0)*100:.1f}%", "%Slash": f"{feats.get('slash',0)*100:.1f}%",
                    "%NonDiatonik": f"{feats.get('nondi',0)*100:.1f}%", "Akor_Unik": feats["uniq_list"],
                    "Nada_Dasar": key_name, "KeyConf": key_conf, "Genre": genre,
                })
            df = pd.DataFrame(rows)
            for col in ["%Extensions","%Slash","%NonDiatonik"]:
                df[col+"_num"] = df[col].apply(lambda s: float(str(s).replace('%','')))
            return df.sort_values(
                by=["Skor Kekayaan Akor (1-5)","raw"], ascending=False, kind="mergesort"
            )
            
        
        # --- Fungsi Helper untuk Analisis Naratif yang Dipercantik ---
        def explain_music_features_v3(row: pd.Series) -> str:
            """
            Menciptakan narasi yang 'cantik' dengan bullet points & emoji
            untuk menjelaskan fitur musik sebuah lagu.
            """
            n_uniq = row['Jumlah_Akor_Unik']
            ext = row['%Extensions_num']
            slash = row['%Slash_num']
            nondi = row['%NonDiatonik_num']
            
            # Kalimat pembuka
            summary = f"Lagu ini memiliki fondasi harmoni yang **{'kaya' if n_uniq > 7 else 'fokus dan solid'}**. Analisis mendalam menunjukkan beberapa karakteristik kunci:"
            
            points = []
            
            # Point 1: Palet Harmoni
            if n_uniq <= 5:
                points.append(f"🎼 **Palet Harmoni Sederhana:** Dengan **{n_uniq} akor unik**, progresi menjadi sangat mudah diikuti, cocok untuk dinyanyikan jemaat.")
            elif n_uniq <= 8:
                points.append(f"🎼 **Palet Harmoni Pop Standar:** Menggunakan **{n_uniq} akor unik**, lagu ini memiliki variasi yang cukup untuk menjaga dinamika tanpa terasa rumit.")
            else:
                points.append(f"🎼 **Palet Harmoni Luas:** Penggunaan **{n_uniq} akor unik** menunjukkan eksplorasi harmoni yang kaya dan kreatif, memberikan banyak warna pada lagu.")

            # Point 2: Warna & Kompleksitas
            if ext > 15:
                points.append(f"🎨 **Kaya Warna Jazz/Gospel:** Penggunaan *extensions* (akor 7, 9, maj7) yang signifikan **({ext:.0f}%)** memberikan nuansa modern dan kompleks pada harmoni.")
            elif slash > 10:
                points.append(f"🎨 **Bassline Dinamis:** Kehadiran *slash chords* yang cukup sering **({slash:.0f}%)** menciptakan pergerakan bass yang melodis dan alur yang tidak monoton.")
            elif ext < 5 and slash < 5:
                points.append(f"🎨 **Harmoni Fundamental:** Struktur akor cenderung diatonis dan dasar, mengandalkan kekuatan progresi I-IV-V-vi yang teruji.")
            else:
                points.append(f"🎨 **Sentuhan Modern:** Adanya sedikit *extensions* atau *slash chords* memberi warna pemanis yang efektif pada aransemen.")

            # Point 3: Keunikan & Kreativitas
            if nondi > 5:
                points.append(f"🔥 **Momen Kejutan:** Keberanian memasukkan **{nondi:.0f}% akor non-diatonik** (di luar tangga nada) menjadi nilai tambah, menciptakan progresi yang segar dan tak terduga.")
            else:
                points.append(f"🔥 **Alur yang Familiar:** Progresi akor yang sebagian besar diatonis membuat lagu ini terasa nyaman dan mudah terhubung dengan pendengar.")
            
            # Saran untuk Juri
            suggestion = "Juri dapat mengapresiasi **keseimbangan antara kreativitas dan kemudahan akses** dalam aransemen harmoni lagu ini."
            if n_uniq > 8 or ext > 10:
                suggestion = "Juri dapat mengapresiasi **tingkat kompleksitas dan keberanian musikal** yang ditunjukkan dalam aransemen harmoni ini."
            elif n_uniq <= 5:
                suggestion = "Juri dapat mengapresiasi **efektivitas dan kesederhanaan harmoni** yang sangat mendukung kekuatan lirik dan melodi."

            # Gabungkan semua menjadi HTML
            html = f"<div style='line-height:1.7;'>{summary}<ul>"
            for point in points:
                html += f"<li style='margin-bottom: 5px;'>{point}</li>"
            html += f"</ul><p><b>💡 Saran Analisis:</b> <i>{suggestion}</i></p></div>"
            return html

        # --- Fungsi untuk Insight Statistik Umum ---
        def generate_music_insights(df: pd.DataFrame) -> str:
            if df.empty: return ""
            
            genre_mode = df['Genre'].mode()[0]
            key_mode = df['Nada_Dasar'].mode()[0]
            avg_uniq = df['Jumlah_Akor_Unik'].mean()
            
            insights = [
                f"🎶 **Dominasi Genre:** Sebagian besar lagu ({df['Genre'].value_counts(normalize=True).max():.0%}) cenderung bergenre **{genre_mode}**, menunjukkan preferensi pada progresi yang familiar dan populer.",
                f"🎹 **Nada Dasar Favorit:** Nada dasar yang paling umum digunakan adalah **{key_mode} Mayor**, yang sangat ramah untuk vokal jemaat dan instrumen seperti gitar atau piano.",
                f"📈 **Kompleksitas Umum:** Secara rata-rata, lagu-lagu dalam lomba ini menggunakan **{avg_uniq:.1f} akor unik**. Lagu yang paling menonjol seringkali adalah yang berani bereksplorasi di atas rata-rata ini.",
                f"✨ **Peluang Inovasi:** Data menunjukkan bahwa lagu dengan skor harmoni tinggi seringkali memiliki persentase ***slash chords* (>10%)** atau ***extensions* (>5%)** yang lebih tinggi, menandakan bahwa variasi bassline dan 'pemanis' harmoni sangat dihargai."
            ]
            
            html = "<div style='line-height:1.7;'><ul>"
            for insight in insights:
                html += f"<li style='margin-bottom: 8px;'>{insight}</li>"
            html += "</ul></div>"
            return html
        
        df_music = process_music_data()

        tab_analisis, tab_statistik = st.tabs(["🎧 Analisis per Lagu", "📊 Statistik Umum"])

        with tab_analisis:
            if not df_music.empty:
                try:
                    r = df_music[df_music["Judul"] == judul].iloc[0]
                    
                    st.header(f"Profil Harmoni: *{judul}*", divider="blue")
                    col1, col2 = st.columns([6, 4])

                    with col1:
                        st.subheader("DNA Musikal (Spider Chart)")
                        # SPIDER CHART LAMA YANG LEBIH BAIK
                        akor_unik_pct = min(100.0, (r["Jumlah_Akor_Unik"]/12.0)*100.0)
                        transisi_unik_pct  = min(100.0, (r["Transisi_Unik"]/15.0)*100.0)
                        radar_vals = {
                            "Akor Unik": akor_unik_pct, 
                            "Transisi Unik": transisi_unik_pct, 
                            "Extensions %": r["%Extensions_num"], 
                            "Slash Chords %": r["%Slash_num"], 
                            "Non-Diatonik %": r["%NonDiatonik_num"]
                        }
                        fig = go.Figure(go.Scatterpolar(r=list(radar_vals.values()), theta=list(radar_vals.keys()), fill='toself', name=judul))
                        fig.update_layout(showlegend=False, polar=dict(radialaxis=dict(visible=True, range=[0,100])), margin=dict(l=60, r=60, t=40, b=40))
                        st.plotly_chart(fig, use_container_width=True)

                        st.subheader("Palet Akor yang Digunakan")
                        unique_chords = r["Akor_Unik"]
                        if unique_chords:
                            st.markdown(" ".join([f"<span style='display:inline-block;padding:.25rem .6rem;border:1px solid #ddd;border-radius:999px;margin:.2rem .25rem; background-color:#f8f9fa;'>{c}</span>" for c in unique_chords]), unsafe_allow_html=True)
                        else:
                            st.caption("Tidak ada data akor yang terdeteksi.")

                    with col2:
                        st.subheader("Skor & Analisis Naratif")
                        st.metric("Skor Kekayaan Harmoni", f"{r['Skor Kekayaan Akor (1-5)']}/5")
                        c1m, c2m = st.columns(2)
                        c1m.metric("Genre Terdeteksi", r['Genre'])
                        c2m.metric("Nada Dasar", r['Nada_Dasar'])
                        
                        with st.container(border=True):
                            st.markdown(explain_music_features_v3(r), unsafe_allow_html=True)
                except IndexError:
                    st.warning(f"Data analisis untuk lagu '{judul}' tidak ditemukan.")
            else:
                st.info("Belum ada data musik yang dapat dianalisis.")

        with tab_statistik:
            st.subheader("💡 Insight Keseluruhan dari Data Musik")
            with st.container(border=True):
                st.markdown(generate_music_insights(df_music), unsafe_allow_html=True)
            
            st.subheader("Visualisasi Data Agregat")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Distribusi Nada Dasar (Key)**")
                hist = px.histogram(df_music, x="Nada_Dasar", color="Nada_Dasar", text_auto=True)
                hist.update_layout(showlegend=False, yaxis_title="Jumlah Lagu")
                st.plotly_chart(hist, use_container_width=True)
            with c2:
                st.markdown("**Skor Kekayaan (1–5) per Genre**")
                gbox = px.box(df_music, x="Genre", y="Skor Kekayaan Akor (1-5)", points="all")
                gbox.update_layout(yaxis_title="Skor (1-5)")
                st.plotly_chart(gbox, use_container_width=True)
            st.markdown("**Peta Kompleksitas Harmoni**")
            bub = px.scatter(df_music, x="%Slash_num", y="%Extensions_num", size="Skor Kekayaan Akor (1-5)", color="Genre", hover_name="Judul", labels={"%Slash_num": "% Akor Slash", "%Extensions_num": "% Akor Extensions"})
            st.plotly_chart(bub, use_container_width=True)
            st.markdown("**Rata-rata Fitur per Genre**")
            feat_melt = df_music.melt(
                id_vars=["Genre"], 
                value_vars=["%Extensions_num","%Slash_num","%NonDiatonik_num","Jumlah_Akor_Unik","Transisi_Unik"],
                var_name="Fitur", value_name="Nilai"
            )
            gbar = px.bar(feat_melt, x="Genre", y="Nilai", color="Fitur", barmode="group")
            st.plotly_chart(gbar, use_container_width=True)
            st.markdown("**Korelasi Antar Fitur Musikal (Pearson)**")
            for_corr = df_music[["Skor Kekayaan Akor (1-5)","raw","Jumlah_Akor_Unik","Transisi_Unik",
                        "%Extensions_num","%Slash_num","%NonDiatonik_num"]].copy()
            for_corr.columns = ["Skor (1-5)","Skor Mentah", "Akor Unik", "Transisi Unik", "Ext %", "Slash %", "Non-Diatonik %"]
            corr = for_corr.corr(numeric_only=True)
            corr_fig = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdYlBu", aspect="auto")
            st.plotly_chart(corr_fig, use_container_width=True)

# ==========================================================
# HELPER HALAMAN 'NILAI SAYA'
# ==========================================================
def create_score_breakdown_html(score_data: pd.Series, rubrik_list: list) -> str:
    """Membuat bar mini HTML untuk breakdown skor per aspek."""
    
    # Warna untuk setiap skor dari 1 sampai 5
    colors = {
        1: "#EF4444", # Merah
        2: "#F97316", # Oranye
        3: "#F59E0B", # Kuning
        4: "#22C55E", # Hijau
        5: "#16A34A"  # Hijau Tua
    }
    
    html = "<div style='display: flex; flex-direction: column; gap: 5px; margin-top: 10px;'>"
    
    for r_item in rubrik_list:
        key = r_item['key']
        aspek = r_item['aspek']
        score = pd.to_numeric(score_data.get(key), errors='coerce')
        
        if pd.isna(score):
            continue
            
        score = int(score)
        width_percent = score * 20 # 5 * 20 = 100%
        color = colors.get(score, '#d1d5db') # Abu-abu jika skor tidak valid
        
        # Baris untuk setiap aspek
        html += f"""
        <div style='display: flex; align-items: center; justify-content: space-between; font-size: 0.85rem;'>
            <span style='color: #4b5563;'>{aspek}</span>
            <span style='font-weight: 600; color: {color};'>{score}/5</span>
        </div>
        <div style='width: 100%; background-color: #e5e7eb; border-radius: 999px; height: 6px;'>
            <div style='width: {width_percent}%; background-color: {color}; border-radius: 999px; height: 6px;'></div>
        </div>
        """
    html += "</div>"
    return html

# =========================
# Page: Nilai Saya
# =========================
if nav_selection == "🧮 Nilai Saya":
    with st.container():
        st.title("🧾 Dashboard Penilaian Saya")
        st.caption(f"Juri aktif: **{active_juri}** (ubah di panel kiri)")

        # --- 1. Persiapan Data ---
        pen_df2 = get_penilaian_df()
        mine = pen_df2[pen_df2["juri"] == active_juri].copy() if "juri" in pen_df2.columns else pd.DataFrame()
        
        # Buat dictionary skor untuk pencarian cepat
        mine_scores = {row['judul']: row for i, row in mine.iterrows()}
        
        total_lagu = len(TITLES)
        sudah_dinilai_titles = sorted([t for t in TITLES if t in mine_scores])
        belum_dinilai_titles = sorted([t for t in TITLES if t not in mine_scores])
        
        sudah = len(sudah_dinilai_titles)

        # --- 2. Header Progres & Metrik ---
        st.markdown("---")
        st.subheader("Progres Penilaian Anda")
        
        progress_value = sudah / total_lagu if total_lagu > 0 else 0
        st.progress(progress_value, text=f"{sudah} dari {total_lagu} lagu telah dinilai ({progress_value:.0%})")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Sudah Dinilai", f"{sudah} lagu")
        c2.metric("Perlu Dinilai", f"{len(belum_dinilai_titles)} lagu")
        avg_score = pd.to_numeric(mine['total'], errors='coerce').mean()
        c3.metric("Rata-rata Skor", f"{avg_score:.1f}" if pd.notna(avg_score) else "—")
        st.markdown("---")

        # --- 3. Layout Dua Kolom untuk Daftar Lagu ---
    col_sudah, col_belum = st.columns(2)

    with col_sudah:
        st.subheader(f"✅ Sudah Dinilai ({sudah})")

        # BUNGKUS DAFTAR DENGAN st.expander
        with st.expander("Tampilkan/Sembunyikan Daftar", expanded=False):
            if not sudah_dinilai_titles:
                st.info("Belum ada lagu yang Anda nilai.")
            else:
                # Urutkan berdasarkan skor, tertinggi di atas
                sorted_graded = sorted(sudah_dinilai_titles, key=lambda t: float(mine_scores[t].get('total', 0)), reverse=True)
                for judul_lagu in sorted_graded:
                    data_lagu = mine_scores[judul_lagu]

                    with st.container(border=True):
                        c1s, c2s = st.columns([4, 1])
                        with c1s:
                            line = f"**{judul_lagu}**"
                            auth = SONGS.get(judul_lagu, {}).get("author", "")
                            if SHOW_AUTHOR and auth:
                                line += f" • _{auth}_"
                            st.markdown(line)

                            score_total = pd.to_numeric(data_lagu.get('total', 0))
                            st.markdown(f"##### Skor Total: <span style='color: #16A34A; font-weight: bold;'>{score_total:.2f}</span>", unsafe_allow_html=True)

                        with c2s:
                            if st.button("✏️ Edit", key=f"edit_{judul_lagu}", use_container_width=True):
                                st.session_state["__next_nav"] = "📝 Penilaian"
                                st.session_state["preselect_title"] = judul_lagu
                                st.rerun()

                        # Tampilkan breakdown skor yang cantik
                        score_breakdown_html = create_score_breakdown_html(data_lagu, RUBRIK)
                        components.html(score_breakdown_html, height=220) # Tambahkan tinggi agar pas
                                            
        with col_belum:
            st.subheader(f"📝 Perlu Dinilai ({len(belum_dinilai_titles)})")
            if not belum_dinilai_titles:
                st.success("🎉 Semua lagu sudah selesai Anda nilai!")
            else:
                for judul_lagu in belum_dinilai_titles:
                    with st.container(border=True):
                        c1b, c2b = st.columns([3, 2])
                        with c1b:
                            line = f"**{judul_lagu}**"
                            auth = SONGS.get(judul_lagu, {}).get("author", "")
                            if SHOW_AUTHOR and auth:
                                line += f"<br><small><i>{auth}</i></small>"
                            st.markdown(line, unsafe_allow_html=True)
                        with c2b:
                            if st.button("➡️ Nilai Sekarang", key=f"rate_{judul_lagu}", use_container_width=True, type="primary"):
                                jump_to("📝 Penilaian", judul_lagu)
    
# ====================================================================
# Page: Hasil & Analitik
# ====================================================================
if nav_selection == "📊 Hasil & Analitik":
    
    # Sertifikat
    def _safe_img(path):
        try:
            if not path or not os.path.exists(path): 
                return None
            with open(path, "rb") as f:
                return ImageReader(io.BytesIO(f.read()))
        except Exception:
            return None
    
    def _fit_centered_text(c, text, y, max_width, font="Helvetica-Bold", start_size=36, min_size=16):
        from reportlab.pdfbase import pdfmetrics
        size = start_size
        while pdfmetrics.stringWidth(text, font, size) > max_width and size > min_size:
            size -= 1
        c.setFont(font, size)
        c.drawCentredString(landscape(A4)[0] / 2, y, text)
    
    # --- FUNGSI HELPER (Didefinisikan di dalam scope nav_selection) ---
    @st.cache_data(show_spinner=False, hash_funcs=HASH_DF)
    def _process_penilaian_data(df_raw: pd.DataFrame):
        """Memproses data mentah menjadi format yang siap dianalisis dan divisualisasi."""
        if df_raw.empty or "judul" not in df_raw.columns:
            return None, None, None, None, None, None, None
            
        p = df_raw.rename(columns=lambda c: VARIANTS.get(c, c)).copy()

        for col in ["timestamp", "total"] + [r["key"] for r in RUBRIK]:
            if col in p.columns:
                if col == "timestamp":
                    p[col] = pd.to_datetime(p[col], errors="coerce")
                else:
                    p[col] = pd.to_numeric(p[col], errors="coerce")
        
        if "total" not in p.columns:
            total_calc = np.zeros(len(p), dtype=float)
            for r in RUBRIK:
                k, mx, wb = r["key"], r["max"], r["bobot"]
                if k in p.columns:
                    total_calc += (p[k].fillna(0) / max(mx, 1)) * wb
            p["total"] = total_calc

        avg = p.groupby("judul", as_index=False)["total"].mean(numeric_only=True)
        if SHOW_AUTHOR:
            avg["Pengarang"] = avg["judul"].map(lambda t: SONGS.get(t, {}).get("author", ""))

        ranking = avg.sort_values("total", ascending=False).reset_index(drop=True)
        ranking["lead_to_next"] = ranking["total"] - ranking["total"].shift(-1)
        
        by_song = p.groupby("judul").agg(
            mean_total=("total", "mean"),
            std_total=("total", "std"),
            n_juri=("juri", "nunique")
        ).reset_index()

        jstat = None
        if "juri" in p.columns:
            jstat = p.groupby("juri").agg(
                rata2=("total", "mean"),
                std=("total", "std"),
                n=("total", "count")
            ).reset_index()

        present_keys = [r["key"] for r in RUBRIK if r["key"] in p.columns]
        corr_aspek = None
        if present_keys:
            corr_aspek = p[present_keys + ["total"]].corr(numeric_only=True)["total"].drop("total").sort_values(ascending=False)

        return p, ranking, by_song, jstat, corr_aspek, present_keys, avg

    def _create_bar_chart(df, x, y, x_title, y_title, text=None):
        try:
            fig = px.bar(df, x=x, y=y, text=text, title=None)
            fig.update_layout(xaxis_title=x_title, yaxis_title=y_title)
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.dataframe(df)

    def _create_scatter_chart(df, x, y, size, hover_name, x_title, y_title):
        try:
            bubble = px.scatter(df, x=x, y=y, size=size, hover_name=hover_name, title=None)
            bubble.update_layout(xaxis_title=x_title, yaxis_title=y_title)
            st.plotly_chart(bubble, use_container_width=True)
        except Exception:
            st.dataframe(df)
            
    def _fmt_num(x, nd=2):
        try:
            f = float(x)
            if abs(f - round(f)) < 1e-9:
                return str(int(round(f)))
            return f"{f:.{nd}f}"
        except Exception:
            return str(x)

    def _build_pen_full_df(pen_df_raw: pd.DataFrame) -> pd.DataFrame:
        if pen_df_raw is None or pen_df_raw.empty:
            return pd.DataFrame(columns=["timestamp","juri","judul","author"] + [r["key"] for r in RUBRIK] + ["total"])
        df = pen_df_raw.copy().rename(columns=lambda c: VARIANTS.get(c, c))
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        for r in RUBRIK:
            k = r["key"]
            if k in df.columns:
                df[k] = pd.to_numeric(df[k], errors="coerce")
        if "total" not in df.columns:
            total_calc = np.zeros(len(df), dtype=float)
            for r in RUBRIK:
                k, mx, wb = r["key"], r["max"], r["bobot"]
                if k in df.columns:
                    total_calc += (pd.to_numeric(df[k], errors="coerce").fillna(0) / max(mx, 1)) * wb
            df["total"] = total_calc
        else:
            df["total"] = pd.to_numeric(df["total"], errors="coerce")
        base_cols = ["timestamp","juri","judul","author"]
        rub_cols  = [r["key"] for r in RUBRIK if r["key"] in df.columns]
        others    = [c for c in df.columns if c not in base_cols + rub_cols + ["total"]]
        ordered   = [c for c in base_cols if c in df.columns] + rub_cols + ["total"] + others
        return df[ordered]
        
    def winner_reasons_df(pen_df_raw: pd.DataFrame, top_title: str):
        df_full = _build_pen_full_df(pen_df_raw)
        if df_full.empty or top_title not in set(df_full["judul"]):
            return pd.DataFrame(), "Data penilaian belum cukup untuk analisis alasan pemenang."
        rub_cols = [r["key"] for r in RUBRIK if r["key"] in df_full.columns]
        agg = df_full.groupby("judul", as_index=False)[rub_cols + ["total"]].mean(numeric_only=True)
        order = agg.sort_values("total", ascending=False).reset_index(drop=True)
        top_row = order.iloc[0]
        run_row = order.iloc[1] if len(order) > 1 else None
        med = {}
        for k in rub_cols:
            med[k] = df_full[k].median(skipna=True)
        med_series = pd.Series(med, name="Median")
        win_series = top_row[rub_cols]; win_series.name = "Pemenang"
        run_series = (run_row[rub_cols] if run_row is not None else pd.Series({k: np.nan for k in rub_cols}))
        run_series.name = "Runner-up"
        comp = pd.concat([win_series, run_series, med_series], axis=1)
        comp["Keunggulan_vs_Runner"] = comp["Pemenang"] - comp["Runner-up"]
        comp["Keunggulan_vs_Median"] = comp["Pemenang"] - comp["Median"]
        comp = comp.reset_index().rename(columns={"index": "Aspek"})
        top_aspek = comp.sort_values("Keunggulan_vs_Runner", ascending=False).head(3)
        bullets = []
        for _, r in top_aspek.iterrows():
            asp = r["Aspek"]
            adv = r["Keunggulan_vs_Runner"]
            bullets.append(f"- Unggul pada **{asp}** sebesar **{adv:+.2f}** poin dibanding runner-up.")
        if not bullets:
            bullets = ["- Poin total tertinggi."]
        reason_text = f"'{top_title}' menang karena:\n" + "\n".join(bullets)
        return comp, reason_text
    
    @st.cache_data(show_spinner=False, hash_funcs=HASH_DF)
    def make_bar_png(series_or_df, title="", width=900, height=400):
        plt.figure(figsize=(width/100, height/100), dpi=100)
        if isinstance(series_or_df, pd.Series):
            series_or_df.plot(kind="bar")
        else:
            series_or_df.plot(kind="bar")
        plt.title(title)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)
        return buf.getvalue()

    @st.cache_data(show_spinner=False, hash_funcs=HASH_DF)
    def export_excel_lengkap(pen_df2: pd.DataFrame) -> bytes:
        df_full = _build_pen_full_df(pen_df2)
        df_full["total"] = pd.to_numeric(df_full["total"], errors="coerce")
        buf = io.BytesIO()
        try:
            writer = pd.ExcelWriter(buf, engine="xlsxwriter")
        except Exception:
            writer = pd.ExcelWriter(buf)
        df_full.to_excel(writer, index=False, sheet_name="Penilaian (Raw)")
        avg = df_full.groupby("judul", as_index=False)["total"].mean().sort_values("total", ascending=False)
        if SHOW_AUTHOR:
            avg["Pengarang"] = avg["judul"].map(lambda t: SONGS.get(t,{}).get("author",""))
            avg = avg[["judul","Pengarang","total"]]
        avg.to_excel(writer, index=False, sheet_name="Ranking Rata2")
        rub_cols = [r["key"] for r in RUBRIK if r["key"] in df_full.columns]
        if rub_cols:
            per_aspek = df_full[["judul"] + rub_cols].groupby("judul", as_index=False).mean(numeric_only=True)
            name_map  = {r["key"]: r["aspek"] for r in RUBRIK}
            per_aspek = per_aspek.rename(columns=name_map)
            per_aspek.to_excel(writer, index=False, sheet_name="Rata2 per Aspek")
            ringkas_aspek = per_aspek.drop(columns=["judul"]).mean().sort_values(ascending=False).reset_index()
            ringkas_aspek.columns = ["Aspek","Rata2"]
            ringkas_aspek.to_excel(writer, index=False, sheet_name="Ringkas Aspek")
        music_rows = []
        for t, aset in SONGS.items():
            seq = chord_sequence_from_sources(aset, CHORD_SOURCE_PRIORITY)
            uniq = list(dict.fromkeys(seq))
            bigrams = list(zip(seq, seq[1:])) if len(seq)>1 else []
            ext_rate = sum(1 for c in seq if re.search(r'\d', c)) / max(1,len(seq))
            slash_rate = sum(1 for c in seq if "/" in c) / max(1,len(seq))
            nondi_rate = sum(1 for c in seq if re.match(r'^[A-G](#|b)', c)) / max(1,len(seq))
            raw = 0.0
            key_name, key_conf = detect_key_from_chords(seq)
            music_rows.append({
                "Judul": t,
                "Pengarang": aset.get("author",""),
                "Akor_Unik": ", ".join(uniq) if uniq else "-",
                "Jumlah_Akor_Unik": len(set(uniq)),
                "Transisi_Unik": len(set(bigrams)),
                "Ext%": f"{ext_rate*100:.1f}%",
                "Slash%": f"{slash_rate*100:.1f}%",
                "NonDiatonik%": f"{nondi_rate*100:.1f}%",
                "Key": key_name,
                "KeyConf": key_conf,
                "Skor_Kekayaan(1-5)": int(_map_0_100_to_1_5(min(100, max(0, raw))))
            })
        pd.DataFrame(music_rows).to_excel(writer, index=False, sheet_name="Musik")
        writer.close()
        return buf.getvalue()

    @st.cache_data(show_spinner=False, hash_funcs=HASH_DF)
    def export_pdf_rekap(pen_df2: pd.DataFrame) -> bytes:
        df_full = _build_pen_full_df(pen_df2)
        df_full["total"] = pd.to_numeric(df_full["total"], errors="coerce")
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="H1", fontSize=18, leading=22, spaceAfter=12, alignment=1))
        styles.add(ParagraphStyle(name="H2", fontSize=13, leading=16, spaceBefore=8, spaceAfter=6))
        styles.add(ParagraphStyle(name="Small", fontSize=9, leading=12, textColor=colors.grey))
        story = []
        story.append(Paragraph("Rekap Penilaian Lomba Cipta Lagu", styles["H1"]))
        story.append(Paragraph(datetime.datetime.now().strftime("%d %B %Y %H:%M"), styles["Small"]))
        story.append(Spacer(1, 8))
        avg = df_full.groupby("judul", as_index=False)["total"].mean().sort_values("total", ascending=False)
        story.append(Paragraph("🏆 Ranking (Rata-rata per Lagu)", styles["H2"]))
        top = avg.head(15)
        tbl = Table([["Judul", "Total (0–100)"]] + [[r["judul"], f"{r['total']:.2f}"] for _, r in top.iterrows()], colWidths=[11.0 * cm, 4.0 * cm])
        tbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, colors.lightgrey),("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),("ALIGN", (1, 1), (1, -1), "RIGHT")]))
        story.append(tbl)
        story.append(Spacer(1, 8))
        if not top.empty:
            chart_png = make_bar_png(top.set_index("judul")["total"], title="Top 10 Total Rata-rata")
            story.append(RLImage(io.BytesIO(chart_png), width=16 * cm, height=7 * cm))
            story.append(Spacer(1, 10))
        rub_cols = [r["key"] for r in RUBRIK if r["key"] in df_full.columns]
        if rub_cols:
            per_aspek = df_full[rub_cols].mean().sort_values(ascending=False)
            name_map = {r["key"]: r["aspek"] for r in RUBRIK}
            per_aspek.index = [name_map.get(k, k) for k in per_aspek.index]
            chart2 = make_bar_png(per_aspek, title="Rata-rata per Aspek")
            story.append(Paragraph("📈 Rata-rata Nilai per Aspek", styles["H2"]))
            story.append(RLImage(io.BytesIO(chart2), width=16 * cm, height=7 * cm))
        music_rows = []
        for t, aset in SONGS.items():
            seq = chord_sequence_from_sources(aset, CHORD_SOURCE_PRIORITY)
            key_name, _ = detect_key_from_chords(seq)
            genre = detect_genre(seq)
            music_rows.append({"Judul": t, "Genre": genre, "Key": key_name})
        m = pd.DataFrame(music_rows)
        if not m.empty:
            genre_counts = m["Genre"].value_counts()
            story.append(Paragraph("Distribusi Genre", styles["H2"]))
            img_genre = make_bar_png(genre_counts, title="Count per Genre")
            story.append(RLImage(io.BytesIO(img_genre), width=16*cm, height=7*cm))
            story.append(Spacer(1, 8))
            key_counts = m["Key"].value_counts()
            story.append(Paragraph("Distribusi Nada Dasar (Key)", styles["H2"]))
            img_key = make_bar_png(key_counts, title="Count per Key")
            story.append(RLImage(io.BytesIO(img_key), width=16*cm, height=7*cm))
        doc.build(story)
        return buf.getvalue()

    @st.cache_data(show_spinner=False, hash_funcs=HASH_DF)
    def export_pdf_winners(pen_df2: pd.DataFrame, top_n: int = WIN_N) -> bytes:
        def per_song_profile(df_full: pd.DataFrame, song: str):
            tmp = df_full[df_full["judul"] == song].copy()
            tmp["total"] = pd.to_numeric(tmp["total"], errors="coerce")
            mean_total = float(tmp["total"].mean())
            std_total  = float(tmp["total"].std(ddof=0)) if len(tmp) > 1 else float("nan")
            n_judges   = int(tmp["juri"].nunique()) if "juri" in tmp.columns else int(len(tmp))
            contr = {}
            for r in RUBRIK:
                k, mx, wb = r["key"], r["max"], r["bobot"]
                if k in tmp.columns:
                    m = pd.to_numeric(tmp[k], errors="coerce").mean()
                    if pd.notna(m): contr[r["aspek"]] = (m / max(mx, 1)) * wb
            contr_s = pd.Series(contr).sort_values(ascending=False) if contr else pd.Series(dtype=float)
            base = {}
            for r in RUBRIK:
                k, mx, wb = r["key"], r["max"], r["bobot"]
                if k in pen_df2.columns:
                    m = pd.to_numeric(pen_df2[k], errors="coerce").mean()
                    if pd.notna(m): base[r["aspek"]] = (m / max(mx, 1)) * wb
            base_s = pd.Series(base).sort_values(ascending=False) if base else pd.Series(dtype=float)
            delta = (contr_s - base_s).sort_values(ascending=False) if not contr_s.empty else pd.Series(dtype=float)
            strengths = delta.head(2).dropna()
            weaknesses = delta.tail(2).dropna()
            return {"mean_total": mean_total, "std_total": std_total, "n_judges": n_judges, "contrib": contr_s, "delta": delta, "strengths": strengths, "weaknesses": weaknesses}

        df_full = _build_pen_full_df(pen_df2)
        df_full["total"] = pd.to_numeric(df_full["total"], errors="coerce")
        table = df_full.groupby("judul", as_index=False)["total"].mean().sort_values("total", ascending=False).reset_index(drop=True)
        winners = table.head(top_n).reset_index(drop=True)
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=86, bottomMargin=36)
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="H1C", fontSize=18, leading=22, alignment=1, spaceAfter=10))
        styles.add(ParagraphStyle(name="Kecil", fontSize=9, textColor=colors.grey))
        styles.add(ParagraphStyle(name="Sub", fontSize=12, leading=16, spaceBefore=8, spaceAfter=4))
        story = []
        story.append(Paragraph("Daftar Pemenang", styles["H1C"]))
        rows = [["Peringkat","Judul","Total","Pengarang","Selisih ke berikutnya"]]
        winners = winners.copy()
        winners["lead_to_next"] = winners["total"] - winners["total"].shift(-1)
        for i, r in winners.iterrows():
            author = SONGS.get(r["judul"],{}).get("author","")
            lead = r["lead_to_next"] if pd.notna(r["lead_to_next"]) else np.nan
            rows.append([i+1, r["judul"], f"{r['total']:.2f}", author, (f"+{lead:.2f}" if np.isfinite(lead) else "—")])
        tbl = Table(rows, colWidths=[2*cm, 7.2*cm, 2.8*cm, 4.2*cm, 3.3*cm])
        tbl.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.3,colors.lightgrey),("BACKGROUND",(0,0),(-1,0),colors.whitesmoke),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("ALIGN",(2,1),(2,-1),"RIGHT"),("ALIGN",(4,1),(4,-1),"RIGHT"),]))
        story.append(tbl); story.append(Spacer(1, 8))
        chart_top = _bar_png(winners.set_index("judul")["total"], title="Skor Rata-rata Pemenang")
        story.append(RLImage(io.BytesIO(chart_top), width=16*cm, height=7*cm))
        story.append(PageBreak())
        for i, r in winners.iterrows():
            title = r["judul"]
            stats = per_song_profile(df_full, title)
            rank_txt = f"Juara {i+1}"
            story.append(Paragraph(f"{rank_txt} — {title}", styles["H1C"]))
            story.append(Paragraph(f"Pengarang: <b>{SONGS.get(title,{}).get('author','')}</b>", styles["Normal"]))
            story.append(Spacer(1, 6))
            lead = r["lead_to_next"] if pd.notna(r["lead_to_next"]) else None
            bullets = []
            bullets.append(f"Skor rata-rata: <b>{stats['mean_total']:.2f}</b> " + (f"(unggul <b>{lead:.2f}</b> poin dari peringkat berikutnya)" if lead and lead>0 else "(unggul tipis)"))
            def label_consistency(std):
                if not np.isfinite(std): return "—"
                if std < 2: return "Sangat konsisten"
                if std < 4: return "Cukup konsisten"
                if std < 6: return "Variatif antar juri"
                return "Sangat variatif"
            bullets.append(f"Ketersepakatan juri: <b>{label_consistency(stats['std_total'])}</b> (deviasi {stats['std_total']:.2f}; {stats['n_judges']} juri).")
            if not stats["strengths"].empty:
                stext = ", ".join([f"<b>{k}</b> (+{v:.2f})" for k,v in stats["strengths"].items()])
                bullets.append(f"Kekuatan utama: {stext}.")
            if not stats["weaknesses"].empty:
                wtext = ", ".join([f"<b>{k}</b> ({v:.2f})" for k,v in stats["weaknesses"].items()])
                bullets.append(f"Area perbaikan: {wtext}.")
            seq_win = chord_sequence_from_sources(SONGS[title], CHORD_SOURCE_PRIORITY)
            key_name, _ = detect_key_from_chords(seq_win)
            genre = detect_genre(seq_win)
            story.append(Paragraph(f"Genre terdeteksi: <b>{genre}</b> • Nada dasar: <b>{key_name}</b>", styles["Normal"]))
            story.append(Spacer(1, 6))
            story.append(Paragraph("Kenapa lagu ini menang?", styles["Sub"]))
            for b in bullets: story.append(Paragraph("• " + b, styles["Normal"]))
            story.append(Spacer(1, 8))
            if not stats["contrib"].empty:
                img1 = _bar_png(stats["contrib"], title="Kontribusi Aspek terhadap Total (poin dari 100)", horizontal=True)
                story.append(RLImage(io.BytesIO(img1), width=16*cm, height=8*cm))
                story.append(Spacer(1, 6))
            if not stats["delta"].empty:
                img2 = _bar_png(stats["delta"], title="Selisih Kontribusi vs Rata-rata Semua Lagu", horizontal=True)
                story.append(RLImage(io.BytesIO(img2), width=16*cm, height=8*cm))
            if i < len(winners)-1:
                story.append(PageBreak())
        def _on_first(canvas_obj, doc_obj):
            _draw_black_header(canvas_obj, doc_obj, "Daftar Pemenang", datetime.datetime.now().strftime("%d %B %Y"))
        def _on_later(canvas_obj, doc_obj):
            _draw_black_header(canvas_obj, doc_obj, "Laporan Pemenang", datetime.datetime.now().strftime("%d %B %Y"))
        doc.build(story, onFirstPage=_on_first, onLaterPages=_on_later)
        return buf.getvalue()

    def _draw_certificate_landscape(c, name, song, role="Peserta", winner=False, rank=None):
        W, H = landscape(A4)
        wm = _safe_img(WATERMARK_IMG)
        if wm:
            c.saveState()
            try: c.setFillAlpha(0.06)
            except Exception: pass
            c.drawImage(wm, W*0.15, H*0.10, width=W*0.70, height=H*0.70, preserveAspectRatio=True, mask='auto')
            c.restoreState()
        elif WATERMARK_TEXT:
            c.saveState()
            try: c.setFillColor(colors.Color(0,0,0,alpha=0.06))
            except Exception: c.setFillColor(colors.grey)
            c.translate(W/2, H/2); c.rotate(30)
            c.setFont("Helvetica-Bold", 96)
            c.drawCentredString(0, 0, WATERMARK_TEXT)
            c.restoreState()
        bn = _safe_img(BANNER)
        if bn:
            banner_h = 150
            c.drawImage(bn, 0, H-banner_h, width=W, height=banner_h, preserveAspectRatio=True, mask='auto')
        else:
            c.setFillColor(colors.black); c.rect(0, H-110, W, 110, fill=1, stroke=0)
        lg = _safe_img(LOGO)
        if lg:
            c.drawImage(lg, 40, H-100, width=90, height=90, preserveAspectRatio=True, mask='auto')
        c.setFillColor(colors.whitesmoke)
        c.setFont("Helvetica-Bold", 28)
        c.drawCentredString(W/2, H-65, "SERTIFIKAT PEMENANG" if winner else "SERTIFIKAT")
        c.setFont("Helvetica", 10); c.setFillColor(colors.HexColor("#D4AF37"))
        c.drawCentredString(W/2, H-92, "Lomba Cipta Lagu — GKI Perumnas")
        c.setFillColor(colors.black); c.setFont("Helvetica", 12)
        c.drawCentredString(W/2, H-150, "Diberikan kepada")
        _fit_centered_text(c, name or "(Nama)", y=H-195, max_width=W-180, font="Helvetica-Bold", start_size=36, min_size=16)
        c.setFont("Helvetica", 13)
        if winner:
            rank_badge = f"JUARA {rank}" if rank else "PEMENANG"
            c.setFillColor(colors.HexColor("#D4AF37")); c.setFont("Helvetica-Bold", 18)
            c.drawCentredString(W/2, H-225, rank_badge)
            c.setFillColor(colors.black); c.setFont("Helvetica", 13)
            c.drawCentredString(W/2, H-245, "Atas prestasi gemilang dalam Lomba Cipta Lagu.")
        else:
            c.drawCentredString(W/2, H-245, f"Atas partisipasi sebagai {role} dalam Lomba Cipta Lagu.")
        if song:
            c.setFont("Helvetica-Oblique", 12)
            _fit_centered_text(c, f'Lagu: “{song}”', y=H-268, max_width=W-220, font="Helvetica-Oblique", start_size=12, min_size=10)
        c.setFont("Helvetica", 10)
        c.drawString(60, 80, datetime.datetime.now().strftime("Diterbitkan: %d %B %Y"))
        c.line(60, 120, 260, 120); c.drawString(60, 125, "Panitia")
        c.line(W-260, 120, W-60, 120); c.drawRightString(W-60, 125, "Ketua Panitia")

    @st.cache_data(show_spinner=False, hash_funcs=HASH_DF)
    def generate_cert_pdf_bytes(name, song, winner=False, rank=None) -> bytes:
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=landscape(A4))
        _draw_certificate_landscape(c, name, song, "Peserta", winner, rank)
        c.showPage(); c.save()
        return buf.getvalue()

    @st.cache_data(show_spinner=False, hash_funcs=HASH_DF)
    def export_certificates_zip(songs_df: pd.DataFrame, pen_df2: pd.DataFrame, top_n: int = WIN_N) -> bytes:
        df_full = _build_pen_full_df(pen_df2)
        avg = df_full.groupby("judul", as_index=False)["total"].mean().sort_values("total", ascending=False)
        win = avg.head(top_n).reset_index(drop=True)
        winner_rank_by_title = {row["judul"]: (i+1) for i, row in win.iterrows()}
        memzip = io.BytesIO()
        with zipfile.ZipFile(memzip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for _, r in songs_df.fillna("").iterrows():
                title = r.get("judul","").strip()
                name  = r.get("pengarang","").strip() or "Peserta"
                rank  = winner_rank_by_title.get(title)
                pdf_bytes = generate_cert_pdf_bytes(name, title, winner=(rank is not None), rank=rank)
                safe_name = re.sub(r"[^A-Za-z0-9 _-]+","", name)[:60] or "Peserta"
                safe_title= re.sub(r"[^A-Za-z0-9 _-]+","", title)[:60] or "Lagu"
                zf.writestr(f"certificate/{safe_name} - {safe_title}.pdf", pdf_bytes)
        memzip.seek(0)
        return memzip.getvalue()

    # --- END OF HELPER FUNCTIONS ---


    # --- TAMPILAN UTAMA HALAMAN ---
    with st.container():
        st.title("📊 Hasil & Analitik")
        ws_pen2 = _ensure_ws(open_sheet(), "Penilaian", ["timestamp", "juri", "judul", "author", "total"])
        pen_df2 = ws_to_df(ws_pen2)
        
        p, ranking, by_song, jstat, corr_aspek, present_keys, avg = _process_penilaian_data(pen_df2)

        if p is None:
            st.info("Belum ada penilaian yang masuk.")
        else:
            # --- Leaderboard ---
            st.subheader("🏆 Leaderboard (dengan jarak ke posisi berikutnya)")
            cols = ["judul", "total", "lead_to_next"] + (["Pengarang"] if SHOW_AUTHOR else [])
            st.dataframe(ranking[cols], use_container_width=True, hide_index=True)
            
            _create_bar_chart(
                ranking.head(12), 
                x="judul", 
                y="total",
                x_title="Judul",
                y_title="Rata-rata total (0-100)",
                text=[f"+{val:.2f}" if pd.notna(val) and val > 0 else "" for val in ranking["lead_to_next"].head(12)]
            )

            # --- Konsistensi per lagu (disagreement) & jumlah juri ---
            st.subheader("📉 Stabilitas Penilaian per Lagu")
            _create_scatter_chart(
                by_song, 
                x="mean_total", 
                y="std_total", 
                size="n_juri",
                hover_name="judul", 
                x_title="Rata-rata total", 
                y_title="Deviasi (ketidaksepakatan)"
            )

            # --- Profil Juri & Korelasi ---
            if jstat is not None:
                st.subheader("🧭 Profil Juri (ketat vs longgar)")
                _create_bar_chart(
                    jstat.sort_values("rata2"), 
                    x="juri", 
                    y="rata2", 
                    x_title="Juri", 
                    y_title="Rata-rata total (±SD)", 
                    text="n"
                )
                pivot = p.pivot_table(index="judul", columns="juri", values="total", aggfunc="mean")
                if pivot.shape[1] >= 2:
                    corrj = pivot.corr(method="spearman", min_periods=2)
                    try:
                        heat = px.imshow(corrj, text_auto=".2f", color_continuous_scale="RdYlBu")
                        heat.update_layout(title="Korelasi antar juri (Spearman)")
                        st.plotly_chart(heat, use_container_width=True)
                    except Exception:
                        st.dataframe(corrj)

            # --- Aspek yang paling “memprediksi” total ---
            if corr_aspek is not None:
                st.subheader("🧩 Aspek vs Total")
                _create_bar_chart(
                    corr_aspek, 
                    x=corr_aspek.index, 
                    y=corr_aspek.values, 
                    x_title="Aspek", 
                    y_title="Korelasi ke total"
                )

            # --- Aktivitas penilaian dari waktu ke waktu ---
            if "timestamp" in p.columns and p["timestamp"].notna().any():
                st.subheader("⏱️ Aktivitas Penilaian (timeline)")
                counts = p.dropna(subset=["timestamp"]).groupby(pd.Grouper(key="timestamp", freq="D"))["total"].count()
                try:
                    st.plotly_chart(px.line(counts, markers=True).update_layout(xaxis_title="Tanggal", yaxis_title="Jumlah penilaian"), use_container_width=True)
                except Exception:
                    st.line_chart(counts)
            
            # --- Rata-rata per aspek
            present = [r["key"] for r in RUBRIK if r["key"] in p.columns]
            if present:
                for k in present:
                    p[k] = pd.to_numeric(p[k], errors="coerce")
                tmp = p[present + ["judul"]].groupby("judul", as_index=False).mean(numeric_only=True)
                melt = (
                    tmp.melt(id_vars="judul", var_name="aspek_key", value_name="nilai")
                    .dropna(subset=["nilai"])
                )
                if not melt.empty:
                    name_map = {r["key"]: r["aspek"] for r in RUBRIK}
                    melt["Aspek"] = melt["aspek_key"].map(name_map)
                    st.subheader("📈 Rata-rata Nilai per Aspek")
                    st.bar_chart(melt.groupby("Aspek")["nilai"].mean())
            else:
                melt = pd.DataFrame()
                
            st.markdown("### 📊 Sebaran & Konsistensi Nilai")
            cols = st.columns(4)
            if not avg.empty:
                top_song = avg.sort_values("total", ascending=False).iloc[0]
                max_score = _fmt_num(top_song['total']) if 'total' in top_song else "N/A"
                max_song = top_song['judul'] if 'judul' in top_song else "N/A"
            else:
                max_score, max_song = "N/A", "N/A"
            
            if not by_song.empty and by_song["std_total"].notna().any():
                most_cons = by_song.sort_values("std_total").iloc[0]
                most_div = by_song.sort_values("std_total", ascending=False).iloc[0]
                cons_song, cons_std = most_cons["judul"], _fmt_num(most_cons["std_total"])
                div_song, div_std = most_div["judul"], _fmt_num(most_div["std_total"])
            else:
                cons_song, cons_std = "N/A", "N/A"
                div_song, div_std = "N/A", "N/A"
            
            metrics = [
                ("Skor tertinggi", max_score, max_song),
                ("Rata-rata total", f"{avg['total'].mean():.2f}" if not avg.empty else "N/A", ""),
                ("Lagu paling konsisten", cons_song, f"σ {cons_std}"),
                ("Lagu paling beragam penilaian", div_song, f"σ {div_std}"),
            ]

            for col, (title, val, delta) in zip(cols, metrics):
                with col:
                    st.metric(title, val, delta)

            # --- Insight Cepat ---
            st.markdown("---")
            st.subheader("🔎 Insight Cepat")
            bullets = []

            ranking2 = avg.sort_values("total", ascending=False).reset_index(drop=True).copy()
            ranking2["lead_to_next"] = ranking2["total"] - ranking2["total"].shift(-1)
            if not ranking2.empty:
                top_row = ranking2.iloc[0]
                bullets.append(f"🏆 <b>Juara sementara</b>: <b>{top_row['judul']}</b> (<span style='color:#2E86AB'>{_fmt_num(top_row['total'])}</span>)")
                tight = ranking2[ranking2["lead_to_next"] > 0].sort_values("lead_to_next")
                if not tight.empty:
                    bullets.append(f"⚔️ <b>Persaingan terketat</b>: <b>{tight.iloc[0]['judul']}</b> unggul <span style='color:#8E44AD'>+{_fmt_num(tight.iloc[0]['lead_to_next'])}</span> poin")

            if corr_aspek is not None and not corr_aspek.empty and corr_aspek.notna().any():
                key_to_name = {r["key"]: r["aspek"] for r in RUBRIK}
                top_key = corr_aspek.index[0]
                bullets.append(f"🎯 <b>Aspek paling berpengaruh pada skor total</b>: <b>{key_to_name.get(top_key, top_key)}</b> (r={_fmt_num(corr_aspek.iloc[0])})")

            if not by_song.empty and by_song["std_total"].notna().any():
                most_cons = by_song.sort_values("std_total").iloc[0]
                most_div = by_song.sort_values("std_total", ascending=False).iloc[0]
                bullets.append(f"✅ <b>Paling konsisten antar juri</b>: <b>{most_cons['judul']}</b> (SD {_fmt_num(most_cons['std_total'])})")
                bullets.append(f"⚠️ <b>Paling beragam penilaian</b>: <b>{most_div['judul']}</b> (SD {_fmt_num(most_div['std_total'])})")

            if jstat is not None and not jstat.empty:
                most_len = jstat.sort_values("rata2", ascending=False).iloc[0]
                most_str = jstat.sort_values("rata2", ascending=True).iloc[0]
                bullets.append(f"🧑‍⚖️ <b>Juri paling longgar</b>: <b>{most_len['juri']}</b> (avg {_fmt_num(most_len['rata2'])})")
                bullets.append(f"🧑‍⚖️ <b>Juri paling ketat</b>: <b>{most_str['juri']}</b> (avg {_fmt_num(most_str['rata2'])})")

            if bullets:
                html = "<ul style='line-height:1.6;margin:.2rem 0 0 .5rem'>" + "".join([f"<li>{b}</li>" for b in bullets]) + "</ul>"
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.caption("— Belum cukup data untuk insight —")
            
            # --- Tombol unduhan ---
            st.subheader("⬇️ Export Hasil")
            colx1, colx2 = st.columns(2)
            with colx1:
                st.download_button(
                    "📥 Excel Lengkap (mirror Penilaian + rekap)",
                    data=export_excel_lengkap(pen_df2),
                    file_name="Rekap_Penilaian_Lengkap.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            with colx2:
                st.download_button(
                    "📥 PDF Rekap + Insight",
                    data=export_pdf_rekap(pen_df2),
                    file_name="Rekap_Penilaian.pdf",
                    mime="application/pdf"
                )
            colx3, colx4 = st.columns(2)
            with colx3:
                st.download_button(
                    "🏆 PDF Pemenang (analisis lengkap)",
                    data=export_pdf_winners(pen_df2, top_n=WIN_N),
                    file_name="Pemenang_Analitik.pdf",
                    mime="application/pdf"
                )
            with colx4:
                songs_df = pd.DataFrame([{'judul': t, 'pengarang': SONGS.get(t,{}).get('author','')} for t in SONGS])
                st.download_button(
                    "🎓 ZIP e-Certificate (peserta & pemenang)",
                    data=export_certificates_zip(songs_df, pen_df2, top_n=WIN_N),
                    file_name="Certificates.zip",
                    mime="application/zip"
                )