import base64
import io
import streamlit as st
import streamlit.components.v1 as components
import fitz  # PyMuPDF
from typing import Dict, Any

# Assuming gdrive.py contains fetch_bytes_cached
from .gdrive import fetch_bytes_cached, drive_download_bytes

# =========================
# PDF Display and Extraction Helpers
# =========================

def embed_pdf(source_dict: Dict[str, Any], height: int = 720):
    """Embeds a PDF in the Streamlit app from a source dictionary."""
    if not source_dict or source_dict.get("mode") is None or source_dict.get("mode") == "not_found":
        st.warning(f"Dokumen tidak tersedia atau path tidak ditemukan: `{source_dict.get('path', 'N/A')}`")
        return

    # Handle embedding from a URL (Google Drive)
    if source_dict.get("mode") == "url" and source_dict.get("preview"):
        preview_url = source_dict["preview"]
        components.html(f"<iframe src='{preview_url}' width='100%' height='{height}px' style='border:none;'></iframe>",
                        height=height + 20, scrolling=True)
    # Handle embedding from a local file path
    elif source_dict.get("mode") == "local" and source_dict.get("path"):
        try:
            with open(source_dict["path"], "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            components.html(f"<iframe src='data:application/pdf;base64,{b64}' width='100%' height='{height}px' style='border:none;'></iframe>",
                            height=height + 20, scrolling=True)
        except FileNotFoundError:
            st.error(f"File lokal tidak ditemukan: {source_dict['path']}")
    # Handle generic external URLs
    elif source_dict.get("mode") == "external_url" and source_dict.get("url"):
        components.html(f"<iframe src='{source_dict['url']}' width='100%' height='{height}px' style='border:none;'></iframe>",
                        height=height + 20, scrolling=True)


@st.cache_data(ttl=6*3600, show_spinner="Generating PDF preview...", max_entries=256)
def pdf_first_page_png_bytes(source_dict: Dict[str, Any], dpi: int = 150) -> bytes | None:
    """
    Extracts the first page of a PDF as a PNG image and caches it.
    """
    if not source_dict or source_dict.get("mode") is None or source_dict.get("mode") == "not_found":
        return None

    pdf_bytes = None
    try:
        # Get PDF bytes based on the source mode
        if source_dict.get("mode") == "url" and source_dict.get("id"):
            pdf_bytes = drive_download_bytes(source_dict["id"])
        elif source_dict.get("mode") == "local" and source_dict.get("path"):
            with open(source_dict["path"], "rb") as f:
                pdf_bytes = f.read()
        elif source_dict.get("mode") == "external_url" and source_dict.get("url"):
             pdf_bytes = fetch_bytes_cached(source_dict["url"])


        if not pdf_bytes:
            return None

        # Render the first page
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            page = doc.load_page(0)
            pix = page.get_pixmap(dpi=dpi)
            return pix.tobytes("png")

    except Exception:
        # Silently fail to avoid cluttering the UI with errors for broken links
        return None

@st.cache_data(ttl=6*3600, show_spinner="Extracting text from PDF...", max_entries=256)
def extract_pdf_text_cached(source_dict: Dict[str, Any]) -> str:
    """
    Extracts all text from a PDF and caches it.
    """
    if not source_dict or source_dict.get("mode") is None or source_dict.get("mode") == "not_found":
        return ""

    pdf_bytes = None
    try:
        # Get PDF bytes based on the source mode
        if source_dict.get("mode") == "url" and source_dict.get("id"):
            pdf_bytes = drive_download_bytes(source_dict["id"])
        elif source_dict.get("mode") == "local" and source_dict.get("path"):
            with open(source_dict["path"], "rb") as f:
                pdf_bytes = f.read()
        elif source_dict.get("mode") == "external_url" and source_dict.get("url"):
             pdf_bytes = fetch_bytes_cached(source_dict["url"])

        if not pdf_bytes:
            return ""

        # Extract text
        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            text = "".join(page.get_text() for page in doc)
        return (text or "").strip()

    except Exception:
        return ""
