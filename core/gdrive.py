import streamlit as st
import io
import requests
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# =========================
# Google Drive Client & Helpers
# =========================

@st.cache_resource(ttl=600)
def _drive_service():
    """Initializes the Google Drive API service."""
    creds_json = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(
        creds_json,
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    return build("drive", "v3", credentials=creds)

@st.cache_data(ttl=3600)
def _fetch_gdrive_index(idx_df, idx_ws):
    """
    Fetches the Google Drive file index. Tries DataFrame first, then falls back to worksheet API call.
    """
    if idx_df is not None and not idx_df.empty:
        return idx_df.set_index("path").to_dict().get("id", {})
    if idx_ws is not None:
        return {r["path"]: r["id"] for r in idx_ws.get_all_records() if r.get("path") and r.get("id")}
    return {}

def resolve_source(path: str, category: str, cfg, idx_df, idx_ws) -> dict:
    """
    Resolves a path into a dictionary containing mode, id, direct URL, etc.
    Modes: 'drive', 'url', 'local', 'none'.
    """
    if not path or not isinstance(path, str):
        return {"mode": "none"}

    path = path.strip()
    GDRIVE_INDEX = _fetch_gdrive_index(idx_df, idx_ws)

    # Check for full Google Drive URL
    if "drive.google.com/file/d/" in path:
        file_id = path.split("/d/")[1].split("/")[0]
        return {"mode": "drive", "id": file_id, "direct": f"https://drive.google.com/uc?id={file_id}"}

    # Check for indexed path
    if path in GDRIVE_INDEX:
        file_id = GDRIVE_INDEX[path]
        return {"mode": "drive", "id": file_id, "direct": f"https://drive.google.com/uc?id={file_id}"}

    # Check for other URLs
    if path.startswith(("http://", "https://")):
        return {"mode": "url", "direct": path}

    # Assume local path otherwise
    return {"mode": "local", "path": path}

@st.cache_data(ttl=3600)
def drive_download_bytes(file_id: str) -> bytes | None:
    """Downloads a file from Google Drive and returns its content as bytes."""
    if not file_id:
        return None
    try:
        service = _drive_service()
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh.getvalue()
    except Exception as e:
        st.error(f"Gagal mengunduh dari Drive (ID: {file_id}): {e}")
        return None

@st.cache_data(ttl=3600)
def fetch_bytes_cached(url: str) -> bytes | None:
    """Fetches bytes from a URL with caching."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        return response.content
    except requests.RequestException:
        return None

@st.cache_data(ttl=3600)
def drive_get_meta(file_id: str) -> dict | None:
    """Gets metadata for a file in Google Drive."""
    if not file_id:
        return None
    try:
        service = _drive_service()
        return service.files().get(fileId=file_id, fields="id, name, mimeType, webViewLink, size").execute()
    except Exception:
        return None

def streamable_gdrive_audio_src(file_id: str) -> str | None:
    """Returns a streamable URL for a Google Drive audio file."""
    if not file_id:
        return None
    # This is a common format for creating a direct-ish link, but may not always work
    return f"https://drive.google.com/uc?export=download&id={file_id}"
