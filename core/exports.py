import streamlit as st
import pandas as pd
import numpy as np
import io
import os
import re
import datetime
import zipfile
import matplotlib.pyplot as plt
import plotly.express as px
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader

# Note: These functions depend on constants and functions from other modules.
# They will need to be passed in as arguments.
# For example: VARIANTS, RUBRIK, SONGS, CHORD_SOURCE_PRIORITY, WIN_N, etc.

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

def _draw_black_header(canvas_obj, doc, title, subtitle=None):
    W, H = doc.pagesize
    canvas_obj.saveState()
    canvas_obj.setFillColor(colors.black)
    canvas_obj.rect(0, H - 70, W, 70, fill=1, stroke=0)
    canvas_obj.setFillColor(colors.whitesmoke)
    canvas_obj.setFont("Helvetica-Bold", 18)
    canvas_obj.drawString(40, H - 46, title)
    if subtitle:
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.setFillColor(colors.HexColor("#D4AF37"))
        canvas_obj.drawString(40, H - 60, subtitle)
    canvas_obj.restoreState()

def _build_pen_full_df(pen_df_raw: pd.DataFrame, VARIANTS, RUBRIK) -> pd.DataFrame:
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

@st.cache_data(show_spinner=False)
def make_bar_png(series_or_df, title="", width=900, height=400, horizontal=False):
    plt.figure(figsize=(width / 100, height / 100), dpi=100)
    if isinstance(series_or_df, pd.Series):
        plot = series_or_df.sort_values().plot(kind="barh") if horizontal else series_or_df.plot(kind="bar")
    else:
        plot = series_or_df.plot(kind="bar", legend=False)
    plt.title(title)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    return buf.getvalue()

@st.cache_data(show_spinner=False)
def export_excel_lengkap(pen_df2: pd.DataFrame, VARIANTS, RUBRIK, SONGS, SHOW_AUTHOR, CHORD_SOURCE_PRIORITY, _map_0_100_to_1_5) -> bytes:
    from .analysis import chord_sequence_from_sources, detect_key_from_chords

    df_full = _build_pen_full_df(pen_df2, VARIANTS, RUBRIK)
    df_full["total"] = pd.to_numeric(df_full["total"], errors="coerce")
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
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
    return buf.getvalue()

@st.cache_data(show_spinner=False)
def export_pdf_rekap(pen_df2: pd.DataFrame, VARIANTS, RUBRIK, SONGS, CHORD_SOURCE_PRIORITY) -> bytes:
    from .analysis import chord_sequence_from_sources, detect_key_from_chords, detect_genre

    df_full = _build_pen_full_df(pen_df2, VARIANTS, RUBRIK)
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
    doc.build(story)
    return buf.getvalue()

def _draw_certificate_landscape(c, name, song, WATERMARK_IMG, WATERMARK_TEXT, BANNER, LOGO, role="Peserta", winner=False, rank=None):
    from reportlab.lib.colors import HexColor, black, whitesmoke
    W, H = landscape(A4)
    wm = _safe_img(WATERMARK_IMG)
    if wm:
        c.saveState()
        c.setFillAlpha(0.06)
        c.drawImage(wm, W*0.15, H*0.10, width=W*0.70, height=H*0.70, preserveAspectRatio=True, mask='auto')
        c.restoreState()
    elif WATERMARK_TEXT:
        c.saveState()
        c.setFillColor(colors.Color(0,0,0,alpha=0.06))
        c.translate(W/2, H/2); c.rotate(30)
        c.setFont("Helvetica-Bold", 96)
        c.drawCentredString(0, 0, WATERMARK_TEXT)
        c.restoreState()
    bn = _safe_img(BANNER)
    if bn:
        c.drawImage(bn, 0, H-150, width=W, height=150, preserveAspectRatio=True, mask='auto')
    lg = _safe_img(LOGO)
    if lg:
        c.drawImage(lg, 40, H-100, width=90, height=90, preserveAspectRatio=True, mask='auto')
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(W/2, H-65, "SERTIFIKAT PEMENANG" if winner else "SERTIFIKAT")
    c.setFont("Helvetica", 10); c.setFillColor(colors.HexColor("#D4AF37"))
    c.drawCentredString(W/2, H-92, "Lomba Cipta Lagu — GKI Perumnas")
    c.setFillColor(colors.black); c.setFont("Helvetica", 12)
    c.drawCentredString(W/2, H-150, "Diberikan kepada")
    _fit_centered_text(c, name or "(Nama)", y=H-195, max_width=W-180)
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

@st.cache_data(show_spinner=False)
def export_certificates_zip(songs_df: pd.DataFrame, pen_df2: pd.DataFrame, VARIANTS, RUBRIK, WIN_N, WATERMARK_IMG, WATERMARK_TEXT, BANNER, LOGO) -> bytes:
    df_full = _build_pen_full_df(pen_df2, VARIANTS, RUBRIK)
    avg = df_full.groupby("judul", as_index=False)["total"].mean().sort_values("total", ascending=False)
    win = avg.head(WIN_N).reset_index(drop=True)
    winner_rank_by_title = {row["judul"]: (i+1) for i, row in win.iterrows()}
    memzip = io.BytesIO()
    with zipfile.ZipFile(memzip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for _, r in songs_df.fillna("").iterrows():
            title = r.get("judul","").strip()
            name  = r.get("pengarang","").strip() or "Peserta"
            rank  = winner_rank_by_title.get(title)
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=landscape(A4))
            _draw_certificate_landscape(c, name, title, WATERMARK_IMG, WATERMARK_TEXT, BANNER, LOGO, winner=(rank is not None), rank=rank)
            c.showPage(); c.save()
            pdf_bytes = buf.getvalue()
            safe_name = re.sub(r"[^A-Za-z0-9 _-]+","", name)[:60] or "Peserta"
            safe_title= re.sub(r"[^A-Za-z0-9 _-]+","", title)[:60] or "Lagu"
            zf.writestr(f"certificate/{safe_name} - {safe_title}.pdf", pdf_bytes)
    memzip.seek(0)
    return memzip.getvalue()
