# -*- coding: utf-8 -*-
# Penjurian Lagu - Streamlit App
# Refactored main application file.

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import urllib.parse
from collections import Counter
import io
import re
import datetime
from zoneinfo import ZoneInfo

# --- Core Refactored Modules ---
from core.utils import fmt_num
from core.gsheet import (
    load_all_sheets, get_penilaian_df, ensure_headers,
    find_pen_row_index_df, update_pen_row, append_pen_row,
    load_existing_scores_for_df, open_sheet, _ensure_ws, ws_to_df
)
from core.gdrive import (
    resolve_source, drive_download_bytes, fetch_bytes_cached, drive_get_meta
)
from core.pdf_utils import embed_pdf, pdf_first_page_png_bytes, extract_pdf_text_cached
from core.config import (
    cfg_get, cfg_list, parse_rubrik, parse_keywords, parse_variants
)
from core.analysis import (
    make_theme_functions,
    score_lyrics_strength,
    highlight_lyrics_v2,
    strip_chords,
    music_features_v2,
    score_harmonic_richness_v2,
    detect_key_from_chords,
    detect_genre,
    get_clean_lyrics_for_song,
    analyze_originality_signals,
    calculate_internal_similarity,
    build_suggestions,
    chord_sequence_from_sources,
    _make_dynamic_binner,
    _pick_text_variant,
    score_creativity_v3,
    score_singability_v2,
    process_penilaian_data,
    _build_pen_full_df
)
from core.exports import (
    export_excel_lengkap,
    export_pdf_rekap,
    export_pdf_winners,
    export_certificates_zip,
    _make_bar_png
)

# ---------- Page config ----------
st.set_page_config(
    page_title="LOMBA CIPTA LAGU THEME SONG BULAN KELUARGA GKI PERUMNAS 2025",
    page_icon="🎵",
    layout="wide",
)

# ---------- Global CSS ----------
st.markdown("""
<style>
  .rubrik-cell{ border:1px solid #E6E9F0; border-radius:10px; padding:.7rem .8rem; min-height:78px; background:#fff; }
  .rubrik-col-aspek{ font-weight:600; }
  .rubrik-col-bobot{ text-align:center; font-weight:600; }
  .r5{ background:#E9F8EF; } .r4{ background:#F1FAF0; } .r3{ background:#FFF5DA; } .r2{ background:#FFECE0; } .r1{ background:#FFE5E7; }
  .rubrik-head{ font-weight:700; background:#F8FAFF; border:1px solid #E3E6EC; border-radius:10px; padding:.6rem .75rem; text-align:center; }
  .block-container{ max-width:1300px; }
  .stAudio { width: 100% !important; }
  @media (max-width: 640px) {
    .block-container { padding-top: 0.5rem; padding-bottom: 3.5rem; }
    .stTabs [data-baseweb="tab-list"] { gap: .25rem; }
    .stTabs [data-baseweb="tab"] { padding: .35rem .6rem; font-size: 0.92rem; }
  }
</style>
""", unsafe_allow_html=True)

if st.session_state.pop("__scroll_top", False):
    components.html("<script>window.scrollTo({top: 0, behavior: 'smooth'});</script>", height=0)

# ---------- Asset Paths ----------
ASSETS = {
    "BANNER": "assets/banner.png",
    "LOGO": "assets/logo.png",
    "WATERMARK_IMG": "assets/watermark.png",
    "WATERMARK_TEXT": "GKI PERUMNAS"
}

# =========================
# Load Data and Config
# =========================
try:
    sh, cfg_df, judges_df, rubrik_df, kw_df, variants_df, songs_df, pen_ws, win_df, idx_ws, idx_df = load_all_sheets()
    pen_df = get_penilaian_df()

    # --- Parse Configurations ---
    RUBRIK = parse_rubrik(rubrik_df)
    VARIANTS = parse_variants(variants_df)
    PHRASES, KEYWORDS = parse_keywords(kw_df)
    theme_score, highlight_matches = make_theme_functions(PHRASES, KEYWORDS)
    R_KEYS = [r["key"] for r in RUBRIK]
    JURIS = sorted(judges_df["juri"].dropna().astype(str).tolist()) if not judges_df.empty else []

    # --- App Behavior Config ---
    FORM_OPEN = cfg_get(cfg_df, "FORM_OPEN", True, bool)
    SHOW_AUTHOR = cfg_get(cfg_df, "SHOW_AUTHOR", False, bool)
    THEME = cfg_get(cfg_df, "THEME", "Tema")
    WIN_N = cfg_get(cfg_df, "WINNERS_TOP_N", 3, int)
    AUTO_WIN = cfg_get(cfg_df, "SHOW_WINNERS_AUTOMATIC", True, bool)
    DEFAULT_TEXT_VIEW = (cfg_get(cfg_df, "DEFAULT_TEXT_VIEW", "auto", str) or "auto").lower()

    # --- Content Priority Config ---
    DISPLAY_TEXT_PRIORITY = cfg_list(cfg_df, "DISPLAY_TEXT_PRIORITY", "lirik_text,full_score,syair_chord,extract_syair,extract_notasi")
    THEME_SCORE_PRIORITY = cfg_list(cfg_df, "THEME_SCORE_PRIORITY", "lirik_text,syair_chord,full_score,extract_syair,extract_notasi")
    CHORD_SOURCE_PRIORITY = cfg_list(cfg_df, "CHORD_SOURCE_PRIORITY", "chords_list,syair_chord,full_score,extract_notasi,extract_syair")
    LYRICS_SCORE_PRIORITY = cfg_list(cfg_df, "LYRICS_SCORE_PRIORITY", "lirik_text,syair_chord,full_score,extract_syair,extract_notasi")

except Exception as e:
    st.error(f"Gagal memuat data dari Google Sheets. Pastikan konfigurasi `secrets.toml` benar dan sheet dibagikan ke email service account.")
    st.exception(e)
    st.stop()

# =========================
# Build Song Dictionary
# =========================
def build_songs_dict():
    if songs_df.empty: return {}
    df = songs_df.fillna(""); out = {}
    for _, r in df.iterrows():
        title = r.get("judul", "").strip()
        if not title: continue
        out[title] = {
            "judul": title,
            "author": r.get("pengarang","").strip(),
            "audio":  resolve_source(r.get("audio_path","").strip(), "audio", cfg_df, idx_df, idx_ws),
            "notasi": resolve_source(r.get("notasi_path","").strip(), "notasi", cfg_df, idx_df, idx_ws),
            "syair":  resolve_source(r.get("syair_path","").strip(), "syair", cfg_df, idx_df, idx_ws),
            "lirik_text":  r.get("lirik_text","").strip(),
            "chords_list": r.get("chords_list","").strip(),
            "full_score":  r.get("full_score","").strip(),
            "syair_chord": r.get("syair_chord","").strip(),
        }
    return out

SONGS = build_songs_dict()
TITLES = songs_df["judul"].dropna().tolist() if not songs_df.empty and "judul" in songs_df.columns else []

# --- Precompute Music Scores ---
def _compute_all_music_raw():
    raws_map, vals = {}, []
    for t, aset in SONGS.items():
        try:
            rv = score_harmonic_richness_v2(aset, cfg_df, CHORD_SOURCE_PRIORITY)
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
        p = _build_pen_full_df(pen_df, RUBRIK, VARIANTS)
        avg = p.groupby("judul", as_index=False)["total"].mean()
        ranking = avg.sort_values("total", ascending=False).head(WIN_N).reset_index(drop=True)
        winners = [f"{i+1}. {row['judul']} — {row['total']:.2f}" for i, row in ranking.iterrows()]
    elif not win_df.empty and "judul" in win_df.columns:
        winners = [f"{r['rank']}. {r['judul']}" if r.get('rank') else f"- {r['judul']}" for _, r in win_df.iterrows()]
    if winners:
        st.markdown("### 🏆 Pemenang")
        st.write("\n".join([f"- {w}" for w in winners]))

if not FORM_OPEN:
    show_winner_only()
    st.stop()


# =========================
# App UI Starts Here
# =========================
try:
    st.image(ASSETS["BANNER"], use_container_width=True)
except Exception:
    st.title("Penjurian Lomba Cipta Lagu")

with st.sidebar:
    st.markdown("### 🧑‍⚖️ Juri aktif")
    if "active_juri" not in st.session_state:
        st.session_state.active_juri = None
    juri_list = sorted(list(JURIS))
    pick_juri = st.selectbox(
        "Pilih juri",
        options=["— pilih juri —"] + juri_list,
        index=(0 if st.session_state.active_juri is None or st.session_state.active_juri not in juri_list
               else 1 + juri_list.index(st.session_state.active_juri)),
        help="Pilihan ini berlaku untuk semua menu.",
    )
    if pick_juri != "— pilih juri —":
        if pick_juri != st.session_state.active_juri:
            st.session_state.active_juri = pick_juri
            st.rerun()
    else:
        st.session_state.active_juri = None

active_juri = st.session_state.active_juri
if not active_juri:
    st.warning("Silakan pilih **juri** di sidebar untuk mulai menilai.")
    st.stop()

NAV_OPTS = ["📝 Penilaian", "🔎 Analisis Syair", "🎼 Analisis Musik", "🧮 Nilai Saya", "📊 Hasil & Analitik"]
nav_selection = st.radio("Menu", NAV_OPTS, key="nav", horizontal=True, label_visibility="collapsed")

st.markdown("---")

pen_mine = pen_df[pen_df["juri"] == active_juri] if "juri" in pen_df.columns else pd.DataFrame()
scores_mine = {}
if not pen_mine.empty:
    pen_mine = pen_mine.sort_values("timestamp").drop_duplicates(subset="judul", keep="last")
    pen_mine['total'] = pd.to_numeric(pen_mine['total'], errors='coerce')
    scores_mine = pd.Series(pen_mine.total.values, index=pen_mine.judul).dropna().to_dict()

formatted_labels = []
for index, row in songs_df.dropna(subset=['judul']).iterrows():
    title = row['judul']
    alias = row.get('Alias')
    prefix = alias if alias else f"{index + 1:02d}"
    label = f"#{prefix} | {title}"
    author = SONGS.get(title, {}).get("author", "")
    if SHOW_AUTHOR and author:
        label += f", oleh {author}"
    if title in scores_mine:
        score = scores_mine[title]
        label = f"✅ {label} (Skor: {float(score):.1f})"
    else:
        label = f"📝 {label}"
    formatted_labels.append(label)

if "selected_title" not in st.session_state:
    st.session_state["selected_title"] = TITLES[0] if TITLES else None

current_index = 0
if st.session_state["selected_title"]:
    try:
        current_index = TITLES.index(st.session_state["selected_title"])
    except (ValueError, IndexError):
        current_index = 0

selected_label = st.selectbox("Pilih Lagu untuk Dinilai/Dianalisis", formatted_labels, index=current_index)
judul = re.split(r"\s*\(Skor:|\s*,\s*oleh", selected_label.split('|', 1)[1])[0].strip()
st.session_state["selected_title"] = judul
aset = SONGS.get(judul, {})
pengarang = aset.get("author", "")
st.markdown("---")

if nav_selection == "📝 Penilaian":
    with st.container():

        st.markdown(f"**Judul:** {judul}" + (f" • **Pengarang:** _{pengarang}_" if (SHOW_AUTHOR and pengarang) else ""))

        # --- Prefill nilai existing (fresh, bukan cache awal) ---
        prefill_key = f"__prefilled_auto::{active_juri}::{judul}::{pengarang}"
        if not st.session_state.get(prefill_key, False):
            ws_pen_fresh = _ensure_ws(open_sheet(), "Penilaian", ["timestamp","juri","judul","author","total"])
            pen_df_latest = ws_to_df(ws_pen_fresh)
            prev_scores = load_existing_scores_for_df(pen_df_latest, active_juri, judul, pengarang, R_KEYS, VARIANTS)
            if prev_scores:
                limits = {r["key"]: (int(r["min"]), int(r["max"])) for r in RUBRIK}
                for k, v in prev_scores.items():
                    lo, hi = limits.get(k, (1, 5))
                    if v is not None and lo <= v <= hi:
                        st.session_state[f"rate::{judul}::{k}"] = int(v)
                st.caption("Nilai sebelumnya dimuat otomatis. Silakan ubah jika perlu.")
            st.session_state[prefill_key] = True

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

        # ANALISIS ORISINALITAS
        with st.expander("🕵️‍♂️ Analisis Orisinalitas (Bantuan untuk Juri)"):
            st.subheader("Sinyal Konten Generik / Potensi AI")
            lyrics_for_analysis = get_clean_lyrics_for_song(aset, LYRICS_SCORE_PRIORITY)
            chords_for_analysis = chord_sequence_from_sources(aset, CHORD_SOURCE_PRIORITY)
            signals = analyze_originality_signals(lyrics_for_analysis, chords_for_analysis)
            c1, c2, c3 = st.columns(3)
            c1.metric("Skor Klise (0-100)", f"{signals.get('cliche_score', 0)}")
            c2.metric("Keragaman Kata (TTR)", f"{signals.get('ttr', 0):.2f}")
            c3.metric("Jumlah Akor Unik", f"{signals.get('num_chords', 0)}")

            st.markdown("---")
            st.subheader("Perbandingan dengan Peserta Lain")
            with st.spinner("Membandingkan dengan lagu lain..."):
                df_similar = calculate_internal_similarity(judul, SONGS, LYRICS_SCORE_PRIORITY, CHORD_SOURCE_PRIORITY)
            if not df_similar.empty:
                st.dataframe(df_similar, hide_index=True, use_container_width=True)
            else:
                st.caption("Belum cukup data untuk perbandingan internal.")

            st.markdown("---")
            st.subheader("Alat Pengecekan Eksternal")
            if lyrics_for_analysis:
                lines = [line.strip() for line in lyrics_for_analysis.split('\n') if 20 < len(line.strip()) < 70]
                search_query = lines[0] if lines else lyrics_for_analysis.split('\n')[0]
                query_with_quotes = '"' + search_query + '"'
                google_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query_with_quotes)}"
                st.link_button("Cari Cuplikan Lirik di Google ↗", google_url)

            if chords_for_analysis:
                chord_query = " ".join(chords_for_analysis[:8])
                chord_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(f'{chord_query} chord progression')}"
                st.link_button("Cari Progresi Akor di Google ↗", chord_url)

        st.markdown("---")
        st.subheader(f"Rubrik Penilaian")

        # ... (full rubric rendering logic) ...
        # ... (submission logic) ...

elif nav_selection == "📊 Hasil & Analitik":
    st.title("📊 Hasil & Analitik")
    p, ranking, by_song, jstat, corr_aspek, present_keys, avg = process_penilaian_data(pen_df, RUBRIK, VARIANTS, SHOW_AUTHOR, SONGS)
    if p is None:
        st.info("Belum ada penilaian yang masuk.")
    else:
        st.subheader("🏆 Leaderboard (dengan jarak ke posisi berikutnya)")
        cols = ["judul", "total", "lead_to_next"] + (["Pengarang"] if SHOW_AUTHOR else [])
        st.dataframe(ranking[cols], use_container_width=True, hide_index=True)
        # ... all other charts and tables ...
    st.subheader("⬇️ Export Hasil")
    st.download_button("📥 Excel Lengkap", data=export_excel_lengkap(pen_df, SONGS, RUBRIK, VARIANTS, SHOW_AUTHOR, CHORD_SOURCE_PRIORITY), file_name="Rekap_Penilaian_Lengkap.xlsx")
    st.download_button("📥 PDF Rekap", data=export_pdf_rekap(pen_df, SONGS, RUBRIK, VARIANTS, CHORD_SOURCE_PRIORITY), file_name="Rekap_Penilaian.pdf")
    st.download_button("🏆 PDF Pemenang", data=export_pdf_winners(pen_df, SONGS, RUBRIK, VARIANTS, WIN_N), file_name="Pemenang_Analitik.pdf")
    st.download_button("🎓 ZIP e-Certificate", data=export_certificates_zip(songs_df, pen_df, RUBRIK, VARIANTS, WIN_N, ASSETS), file_name="Certificates.zip")
