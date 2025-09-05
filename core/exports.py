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
from .analysis import chord_sequence_from_sources, detect_key_from_chords, detect_genre, _build_pen_full_df, get_clean_lyrics_for_song, generate_wordcloud_image, music_features_v2

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

def _draw_black_header(c, doc, title, subtitle=None):
    """Helper to draw a black header bar on a ReportLab canvas."""
    W, H = doc.pagesize
    c.saveState()
    c.setFillColor(black)
    c.rect(0, H - 70, W, 70, fill=1, stroke=0)
    c.setFillColor(whitesmoke)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, H - 46, title)
    if subtitle:
        c.setFont("Helvetica", 10)
        c.setFillColor(HexColor("#D4AF37"))
        c.drawString(40, H - 60, subtitle)
    c.restoreState()

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
        # Sheet 1: Raw Penilaian
        df_full.to_excel(writer, index=False, sheet_name="Penilaian_Raw")

        # Sheet 2: Ranking Rata-rata
        avg = df_full.groupby("judul", as_index=False)["total"].mean().sort_values("total", ascending=False)
        if show_author:
            avg["Pengarang"] = avg["judul"].map(lambda t: songs_data.get(t, {}).get("author", ""))
        avg.to_excel(writer, index=False, sheet_name="Ranking_Rata2")

        # Sheet 3: Rata-rata per Aspek
        rub_cols = [r["key"] for r in rubrik if r["key"] in df_full.columns]
        if rub_cols:
            per_aspek = df_full[["judul"] + rub_cols].groupby("judul", as_index=False).mean(numeric_only=True)
            name_map  = {r["key"]: r["aspek"] for r in rubrik}
            per_aspek = per_aspek.rename(columns=name_map)
            per_aspek.to_excel(writer, index=False, sheet_name="Rata2_per_Aspek")

        # Sheet 4: Analisis Musik
        music_rows = []
        for t, aset in songs_data.items():
            seq = chord_sequence_from_sources(aset, chord_sources)
            feats = music_features_v2(seq)
            key_name, key_conf = detect_key_from_chords(seq)
            music_rows.append({
                "Judul": t,
                "Pengarang": aset.get("author",""),
                "Akor_Unik": ", ".join(feats["uniq_list"]) if feats["uniq_list"] else "-",
                "Jumlah_Akor_Unik": len(feats["uniq_list"]),
                "Transisi_Unik": feats["big_count"],
                "Ext%": f"{feats['ext']*100:.1f}%",
                "Slash%": f"{feats['slash']*100:.1f}%",
                "NonDiatonik%": f"{feats['nondi']*100:.1f}%",
                "Key": key_name,
                "KeyConf": key_conf,
            })
        pd.DataFrame(music_rows).to_excel(writer, index=False, sheet_name="Analisis_Musik")

    return buf.getvalue()

# =========================
# PDF Rekap Export
# =========================
def export_pdf_rekap(pen_df_raw: pd.DataFrame, songs_data: dict, rubrik: list, variants: dict, chord_sources: list, lyrics_score_priority: list) -> bytes:
    """Exports a summary PDF of all scores and analytics."""
    df_full = _build_pen_full_df(pen_df_raw, rubrik, variants)

    all_lyrics = " ".join([get_clean_lyrics_for_song(s, lyrics_score_priority) for s in songs_data.values()])
    wordcloud_image = None
    if all_lyrics.strip():
        wordcloud_image = generate_wordcloud_image(all_lyrics)

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

    if wordcloud_image:
        story.append(Spacer(1, 12))
        story.append(Paragraph("Word Cloud (Semua Lirik)", styles['h2']))
        story.append(RLImage(wordcloud_image, width=16*cm, height=8*cm))

    doc.build(story)
    return buf.getvalue()

# =========================
# PDF Winners & Certificates Export
# =========================
def export_pdf_winners(pen_df_raw: pd.DataFrame, songs_data: dict, rubrik: list, variants: dict, top_n: int, chord_sources: list, lyrics_score_priority: list) -> bytes:
    """Exports a detailed PDF report for the top N winners."""
    df_full = _build_pen_full_df(pen_df_raw, rubrik, variants)
    table = df_full.groupby("judul", as_index=False)["total"].mean().sort_values("total", ascending=False).reset_index(drop=True)
    winners = table.head(top_n).reset_index(drop=True)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=86, bottomMargin=36)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="H1C", fontSize=18, leading=22, alignment=1, spaceAfter=10))
    styles.add(ParagraphStyle(name="Sub", fontSize=12, leading=16, spaceBefore=8, spaceAfter=4))
    story = []

    # Winners Summary Page
    story.append(Paragraph("Daftar Pemenang", styles["H1C"]))
    rows = [["Peringkat", "Judul", "Total", "Pengarang", "Selisih"]]
    winners["lead_to_next"] = winners["total"] - winners["total"].shift(-1)
    for i, r in winners.iterrows():
        author = songs_data.get(r["judul"], {}).get("author", "")
        lead = r["lead_to_next"]
        rows.append([i + 1, r["judul"], f"{r['total']:.2f}", author, f"+{lead:.2f}" if pd.notna(lead) else "—"])

    tbl = Table(rows, colWidths=[2*cm, 7*cm, 2.5*cm, 4*cm, 3*cm])
    tbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.3, lightgrey), ("BACKGROUND", (0, 0), (-1, 0), whitesmoke)]))
    story.append(tbl)
    story.append(PageBreak())

    # Individual Winner Pages
    for i, r in winners.iterrows():
        title = r["judul"]
        stats = per_song_profile(df_full, title, rubrik)

        story.append(Paragraph(f"Juara {i+1} — {title}", styles["H1C"]))
        story.append(Paragraph(f"Pengarang: <b>{songs_data.get(title,{}).get('author','')}</b>", styles["Normal"]))
        story.append(Spacer(1, 6))

        lead = r["lead_to_next"]
        bullets = []
        bullets.append(f"Skor rata-rata: <b>{stats['mean_total']:.2f}</b> " + (f"(unggul <b>{lead:.2f}</b> poin dari peringkat berikutnya)" if pd.notna(lead) and lead > 0 else "(unggul tipis)"))

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

        seq_win = chord_sequence_from_sources(songs_data[title], chord_sources)
        key_name, _ = detect_key_from_chords(seq_win)
        genre = detect_genre(seq_win)
        story.append(Paragraph(f"Genre terdeteksi: <b>{genre}</b> • Nada dasar: <b>{key_name}</b>", styles["Normal"]))
        story.append(Spacer(1, 6))
        story.append(Paragraph("Kenapa lagu ini menang?", styles["Sub"]))
        for b in bullets: story.append(Paragraph("• " + b, styles["Normal"]))
        story.append(Spacer(1, 8))

        if not stats["contrib"].empty:
            img1 = _make_bar_png(stats["contrib"], title="Kontribusi Aspek terhadap Total (poin dari 100)", horizontal=True)
            story.append(RLImage(io.BytesIO(img1), width=16*cm, height=8*cm))
            story.append(Spacer(1, 6))
        if not stats["delta"].empty:
            img2 = _make_bar_png(stats["delta"], title="Selisih Kontribusi vs Rata-rata Semua Lagu", horizontal=True)
            story.append(RLImage(io.BytesIO(img2), width=16*cm, height=8*cm))

        if i < len(winners) - 1:
            story.append(PageBreak())

    def on_first(canvas, doc):
        _draw_black_header(canvas, doc, "Daftar Pemenang", datetime.datetime.now().strftime("%d %B %Y"))
    def on_later(canvas, doc):
        _draw_black_header(canvas, doc, "Laporan Pemenang", datetime.datetime.now().strftime("%d %B %Y"))

    doc.build(story, onFirstPage=on_first, onLaterPages=on_later)
    return buf.getvalue()

def per_song_profile(df_full: pd.DataFrame, song: str, rubrik: list) -> dict:
    """Helper to calculate detailed stats for a single song."""
    tmp = df_full[df_full["judul"] == song].copy()
    mean_total = float(tmp["total"].mean())
    std_total  = float(tmp["total"].std(ddof=0)) if len(tmp) > 1 else 0.0
    n_judges   = int(tmp["juri"].nunique()) if "juri" in tmp.columns else 0

    contr = {}
    for r_item in rubrik:
        k, mx, wb = r_item["key"], r_item["max"], r_item["bobot"]
        if k in tmp.columns:
            m = pd.to_numeric(tmp[k], errors="coerce").mean()
            if pd.notna(m): contr[r_item["aspek"]] = (m / max(mx, 1)) * wb
    contr_s = pd.Series(contr).sort_values(ascending=False) if contr else pd.Series(dtype=float)

    base = {}
    for r_item in rubrik:
        k, mx, wb = r_item["key"], r_item["max"], r_item["bobot"]
        if k in df_full.columns:
            m = pd.to_numeric(df_full[k], errors="coerce").mean()
            if pd.notna(m): base[r_item["aspek"]] = (m / max(mx, 1)) * wb
    base_s = pd.Series(base).sort_values(ascending=False) if base else pd.Series(dtype=float)

    delta = (contr_s - base_s).sort_values(ascending=False) if not contr_s.empty else pd.Series(dtype=float)
    strengths = delta.head(2).dropna()
    weaknesses = delta.tail(2).dropna()

    return {
        "mean_total": mean_total,
        "std_total": std_total,
        "n_judges": n_judges,
        "contrib": contr_s,
        "delta": delta,
        "strengths": strengths,
        "weaknesses": weaknesses
    }

def _draw_certificate_landscape(c: canvas.Canvas, name: str, song: str, role: str, is_winner: bool, rank: int, assets: dict):
    """Draws the content for a single certificate."""
    W, H = landscape(A4)

    wm = _safe_img(assets.get("WATERMARK_IMG"))
    if wm:
        c.saveState()
        c.setFillAlpha(0.06)
        c.drawImage(wm, W * 0.15, H * 0.10, width=W * 0.7, height=H * 0.7, preserveAspectRatio=True, mask='auto')
        c.restoreState()

    bn = _safe_img(assets.get("BANNER"))
    if bn:
        banner_h = 150
        c.drawImage(bn, 0, H - banner_h, width=W, height=banner_h, preserveAspectRatio=True, mask='auto')

    lg = _safe_img(assets.get("LOGO"))
    if lg:
        c.drawImage(lg, 40, H - 100, width=90, height=90, preserveAspectRatio=True, mask='auto')

    c.setFillColor(whitesmoke)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(W / 2, H - 65, "SERTIFIKAT PEMENANG" if is_winner else "SERTIFIKAT")
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor("#D4AF37"))
    c.drawCentredString(W / 2, H - 92, "Lomba Cipta Lagu — GKI Perumnas")

    c.setFillColor(black)
    c.setFont("Helvetica", 12)
    c.drawCentredString(W / 2, H - 150, "Diberikan kepada")

    _fit_centered_text(c, name or "(Nama)", y=H-195, max_width=W-180, font="Helvetica-Bold", start_size=36, min_size=16)

    c.setFont("Helvetica", 13)
    if is_winner:
        rank_badge = f"JUARA {rank}" if rank else "PEMENANG"
        c.setFillColor(HexColor("#D4AF37"))
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(W / 2, H - 225, rank_badge)
        c.setFillColor(black)
        c.setFont("Helvetica", 13)
        c.drawCentredString(W / 2, H - 245, "Atas prestasi gemilang dalam Lomba Cipta Lagu.")
    else:
        c.drawCentredString(W / 2, H - 245, f"Atas partisipasi sebagai {role} dalam Lomba Cipta Lagu.")

    if song:
        c.setFont("Helvetica-Oblique", 12)
        _fit_centered_text(c, f'Lagu: “{song}”', y=H - 268, max_width=W - 220, font="Helvetica-Oblique", start_size=12, min_size=10)

    c.setFont("Helvetica", 10)
    c.drawString(60, 80, datetime.datetime.now().strftime("Diterbitkan: %d %B %Y"))
    c.line(60, 120, 260, 120)
    c.drawString(60, 125, "Panitia")
    c.line(W - 260, 120, W - 60, 120)
    c.drawRightString(W - 60, 125, "Ketua Panitia")

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
