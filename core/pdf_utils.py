import streamlit as st
import base64
import fitz  # PyMuPDF
import io

# =========================
# PDF Utilities
# =========================

def embed_pdf(source: dict, height: int = 720):
    """Embeds a PDF in the Streamlit app from various sources."""
    if not source or source.get("mode") == "none":
        st.warning("PDF tidak ditemukan.")
        return

    pdf_bytes = None
    if source.get("mode") == "drive":
        # Lazy import to avoid circular dependency
        from .gdrive import drive_download_bytes
        pdf_bytes = drive_download_bytes(source.get("id"))
    elif source.get("mode") == "url":
        # Lazy import
        from .gdrive import fetch_bytes_cached
        pdf_bytes = fetch_bytes_cached(source.get("direct"))
    elif source.get("mode") == "local":
        try:
            with open(source.get("path"), "rb") as f:
                pdf_bytes = f.read()
        except FileNotFoundError:
            st.error(f"File lokal tidak ditemukan: {source.get('path')}")
            return

    if pdf_bytes:
        base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="{height}" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    else:
        st.warning("Gagal memuat PDF.")

@st.cache_data(ttl=3600)
def pdf_first_page_png_bytes(source: dict, dpi: int = 150) -> bytes | None:
    """Renders the first page of a PDF as a PNG image."""
    if not source or source.get("mode") == "none":
        return None

    pdf_bytes = None
    if source.get("mode") == "drive":
        from .gdrive import drive_download_bytes
        pdf_bytes = drive_download_bytes(source.get("id"))
    elif source.get("mode") == "url":
        from .gdrive import fetch_bytes_cached
        pdf_bytes = fetch_bytes_cached(source.get("direct"))
    elif source.get("mode") == "local":
        try:
            with open(source.get("path"), "rb") as f:
                pdf_bytes = f.read()
        except FileNotFoundError:
            return None

    if not pdf_bytes:
        return None

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        if len(doc) > 0:
            page = doc.load_page(0)
            pix = page.get_pixmap(dpi=dpi)
            img_bytes = pix.tobytes("png")
            return img_bytes
        return None
    except Exception:
        return None

@st.cache_data(ttl=3600)
def extract_pdf_text_cached(source: dict) -> str:
    """Extracts all text from a PDF."""
    if not source or source.get("mode") == "none":
        return ""

    pdf_bytes = None
    if source.get("mode") == "drive":
        from .gdrive import drive_download_bytes
        pdf_bytes = drive_download_bytes(source.get("id"))
    elif source.get("mode") == "url":
        from .gdrive import fetch_bytes_cached
        pdf_bytes = fetch_bytes_cached(source.get("direct"))
    elif source.get("mode") == "local":
        try:
            with open(source.get("path"), "rb") as f:
                pdf_bytes = f.read()
        except FileNotFoundError:
            return ""

    if not pdf_bytes:
        return ""

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        return text
    except Exception:
        return ""
