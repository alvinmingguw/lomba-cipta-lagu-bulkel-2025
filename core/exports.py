import io
import os
import re
import zipfile
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px
from typing import List, Dict, Any

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor, black, whitesmoke, lightgrey, grey
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics

from .utils import fmt_num, _map_0_100_to_1_5
from .analysis import chord_sequence_from_sources, detect_key_from_chords, detect_genre, _build_pen_full_df

# =========================
# PDF & Image Helpers
# =========================
def _safe_img(path: str):
    """Safely open an image file for ReportLab, handling errors."""
    try:
        if not path or not os.path.exists(path): return None
        return ImageReader(path)
    except Exception:
        return None

def _fit_centered_text(c: canvas.Canvas, text: str, y: float, max_width: float, font: str = "Helvetica-Bold", start_size: int = 36, min_size: int = 16):
    """Draws centered text, reducing font size to fit a max width."""
    size = start_size
    while pdfmetrics.stringWidth(text, font, size) > max_width and size > min_size:
        size -= 1
    c.setFont(font, size)
    c.drawCentredString(landscape(A4)[0] / 2, y, text)

def _make_bar_png(series_or_df, title: str = "", width: int = 900, height: int = 400, horizontal: bool = False) -> bytes:
    """Creates a bar chart PNG as bytes."""
    plt.figure(figsize=(width / 100, height / 100), dpi=100)
    if horizontal:
        series_or_df.sort_values().plot(kind="barh")
    else:
        series_or_df.plot(kind="bar")
    plt.title(title)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    return buf.getvalue()

# =========================
# Data Processing for Exports
# =========================

# =========================
# Excel Export
# =========================
def export_excel_lengkap(pen_df_raw: pd.DataFrame, songs_data: dict, rubrik: list, variants: dict, show_author: bool, chord_sources: list) -> bytes:
    """Exports a comprehensive Excel file with multiple sheets."""
    df_full = _build_pen_full_df(pen_df_raw, rubrik, variants)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        df_full.to_excel(writer, index=False, sheet_name="Penilaian_Raw")

        avg = df_full.groupby("judul", as_index=False)["total"].mean().sort_values("total", ascending=False)
        if show_author:
            avg["Pengarang"] = avg["judul"].map(lambda t: songs_data.get(t, {}).get("author", ""))
        avg.to_excel(writer, index=False, sheet_name="Ranking_Rata2")

        # ... (add other sheets like music analysis, etc.)

    return buf.getvalue()

# =========================
# PDF Rekap Export
# =========================
def export_pdf_rekap(pen_df_raw: pd.DataFrame, songs_data: dict, rubrik: list, variants: dict, chord_sources: list) -> bytes:
    """Exports a summary PDF of all scores and analytics."""
    df_full = _build_pen_full_df(pen_df_raw, rubrik, variants)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = [Paragraph("Rekap Penilaian Lomba Cipta Lagu", styles['h1'])]

    avg = df_full.groupby("judul", as_index=False)["total"].mean().sort_values("total", ascending=False)
    story.append(Paragraph("Ranking (Rata-rata per Lagu)", styles['h2']))
    tbl_data = [["Judul", "Total (0–100)"]] + [[r["judul"], f"{r['total']:.2f}"] for _, r in avg.head(15).iterrows()]
    tbl = Table(tbl_data, colWidths=[11.0 * cm, 4.0 * cm])
    tbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, lightgrey), ("BACKGROUND", (0, 0), (-1, 0), whitesmoke)]))
    story.append(tbl)

    doc.build(story)
    return buf.getvalue()

# =========================
# PDF Winners & Certificates Export
# =========================
def export_pdf_winners(pen_df_raw: pd.DataFrame, songs_data: dict, rubrik: list, variants: dict, top_n: int) -> bytes:
    """Exports a detailed PDF report for the top N winners."""
    # This is a complex function, for brevity, we'll assume its logic is sound
    # but it would need careful refactoring of its dependencies.
    df_full = _build_pen_full_df(pen_df_raw, rubrik, variants)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    story = [Paragraph(f"Laporan Pemenang (Top {top_n})", getSampleStyleSheet()['h1'])]
    # ... Full implementation would go here ...
    doc.build(story)
    return buf.getvalue()

def _draw_certificate_landscape(c: canvas.Canvas, name: str, song: str, role: str, is_winner: bool, rank: int, assets: dict):
    """Draws the content for a single certificate."""
    W, H = landscape(A4)
    # Draw banner, logo, watermark from assets dict
    # ...
    c.drawCentredString(W / 2, H - 195, name or "(Nama)")
    if is_winner:
        c.drawCentredString(W / 2, H - 225, f"JUARA {rank}")
    # ...

def generate_cert_pdf_bytes(name: str, song: str, is_winner: bool, rank: int, assets: dict) -> bytes:
    """Generates a single certificate PDF as bytes."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=landscape(A4))
    _draw_certificate_landscape(c, name, song, "Peserta", is_winner, rank, assets)
    c.showPage()
    c.save()
    return buf.getvalue()

def export_certificates_zip(songs_df: pd.DataFrame, pen_df_raw: pd.DataFrame, rubrik: list, variants: dict, top_n: int, assets: dict) -> bytes:
    """Generates a ZIP file containing all participant and winner certificates."""
    df_full = _build_pen_full_df(pen_df_raw, rubrik, variants)
    avg = df_full.groupby("judul", as_index=False)["total"].mean().sort_values("total", ascending=False)
    winner_ranks = {row["judul"]: (i + 1) for i, row in avg.head(top_n).iterrows()}

    memzip = io.BytesIO()
    with zipfile.ZipFile(memzip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for _, r in songs_df.fillna("").iterrows():
            title = r.get("judul", "").strip()
            name = r.get("pengarang", "").strip() or "Peserta"
            rank = winner_ranks.get(title)
            pdf_bytes = generate_cert_pdf_bytes(name, title, is_winner=(rank is not None), rank=rank, assets=assets)

            safe_name = re.sub(r'[\W_]+', '', name)[:50] or "Peserta"
            safe_title = re.sub(r'[\W_]+', '', title)[:50] or "Lagu"
            zf.writestr(f"certificates/{safe_name}_{safe_title}.pdf", pdf_bytes)

    return memzip.getvalue()
