import os
import io
import re
import requests
import streamlit as st
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from typing import Dict, Any

from .utils import _patch_sa, HASH_DF, is_url

# =========================
# Google Drive Service
# =========================
@st.cache_resource
def _drive_service():
    """Initializes and caches the Google Drive API service."""
    info = _patch_sa(st.secrets.get("gcp_service_account"))
    scopes = ["https://www.googleapis.com/auth/drive.readonly"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    # The refresh token logic is handled by the credentials object itself.
    # No need to manually call creds.refresh(Request()) here.
    return build("drive", "v3", credentials=creds, cache_discovery=False)

# =========================
# Drive URL and Download Helpers
# =========================
def drive_preview_url(file_id: str) -> str:
    """Returns an embeddable preview URL for a Google Drive file."""
    return f"https://drive.google.com/file/d/{file_id}/preview"

def drive_direct_url(file_id: str) -> str:
    """Returns a basic download URL for a Google Drive file."""
    return f"https://drive.google.com/uc?export=download&id={file_id}"

@st.cache_data(ttl=6*3600, show_spinner="Fetching file metadata...", max_entries=256)
def drive_get_meta(file_id: str, fields: str = "id,name,mimeType,size,webContentLink") -> Dict[str, Any]:
    """Gets and caches metadata for a Google Drive file."""
    try:
        svc = _drive_service()
        meta = svc.files().get(fileId=file_id, fields=fields).execute()
        return meta or {}
    except Exception as e:
        st.error(f"Error fetching metadata for file ID {file_id}: {e}")
        return {}

@st.cache_data(show_spinner="Downloading file from Drive...", hash_funcs=HASH_DF, max_entries=128)
def drive_download_bytes(file_id: str) -> bytes | None:
    """Downloads and caches file content from Google Drive as bytes."""
    try:
        svc = _drive_service()
        request = svc.files().get_media(fileId=file_id)
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request, chunksize=2 * 1024 * 1024) # 2MB chunks
        done = False
        while not done:
            _, done = downloader.next_chunk()
        return buf.getvalue()
    except Exception as e:
        # Don't show error for every failed download, could be noisy
        # st.warning(f"Could not download file {file_id}: {e}")
        return None

@st.cache_data(ttl=3600, show_spinner="Fetching remote content...", max_entries=128)
def fetch_bytes_cached(url: str) -> bytes | None:
    """Fetches and caches content from a generic URL."""
    try:
        r = requests.get(url, timeout=25)
        r.raise_for_status() # Raises an exception for bad status codes
        return r.content
    except requests.RequestException:
        return None

def pick_audio_format(mime: str | None, fallback_url: str | None = None) -> str | None:
    """Picks the correct audio MIME type for the Streamlit audio player."""
    if mime:
        if mime in ("audio/mpeg", "audio/mp3"): return "audio/mpeg"
        if mime in ("audio/x-m4a", "audio/mp4", "audio/aac"): return "audio/mp4"
        if mime.startswith("audio/"): return mime
    # Fallback based on file extension
    if fallback_url:
        lower_url = fallback_url.lower()
        if ".m4a" in lower_url: return "audio/mp4"
        if ".mp3" in lower_url: return "audio/mpeg"
    return None # Let Streamlit infer

def streamable_gdrive_audio_src(file_id: str) -> Dict[str, Any]:
    """
    Prepares a dictionary for st.audio, preferring a direct URL stream.
    Falls back to downloading bytes if the direct URL is not accessible.
    """
    if not file_id:
        return {"mode": None}

    meta = drive_get_meta(file_id) or {}
    mime = meta.get("mimeType")

    # The direct URL is often sufficient and much lighter than downloading bytes.
    url = drive_direct_url(file_id)
    return {"mode": "url", "url": url, "mime": pick_audio_format(mime, url)}

# =========================
# Drive File Resolution and Indexing
# =========================
def _drive_search_by_name(name: str, parent_id: str = None, mime_hint: str = None) -> list:
    """Searches for a file by name within a specific Drive folder."""
    svc = _drive_service()
    escaped_name = name.replace("'", "\\'")
    query_parts = [f"name = '{escaped_name}'", "trashed = false"]
    if parent_id:
        query_parts.append(f"'{parent_id}' in parents")
    if mime_hint:
        query_parts.append(f"mimeType contains '{mime_hint}'")

    query = " and ".join(query_parts)
    try:
        res = svc.files().list(
            q=query,
            spaces="drive",
            fields="files(id,name,mimeType,modifiedTime,parents)",
            pageSize=5,
            orderBy="modifiedTime desc"
        ).execute()
        return res.get("files", [])
    except Exception:
        return []

def _idx_lookup(idx_df: pd.DataFrame, name: str) -> Dict[str, Any] | None:
    """Looks up a file in the DriveIndex DataFrame."""
    if idx_df is None or idx_df.empty:
        return None
    row = idx_df[idx_df["name"] == name]
    return row.iloc[0].to_dict() if not row.empty else None

def _idx_append(ws_idx, record: Dict[str, str]):
    """Appends a new record to the DriveIndex worksheet."""
    headers = ["name", "id", "mimeType", "modifiedTime", "parentHint"]
    # Ensure order is correct
    ws_idx.append_row([record.get(h, "") for h in headers], value_input_option="USER_ENTERED")

def is_gdrive_id_like(x: str) -> bool:
    """Checks if a string looks like a Google Drive file ID."""
    return bool(re.fullmatch(r"[A-Za-z0-9_-]{20,}", x or ""))

def resolve_source(raw_value: str, kind: str, cfg: pd.DataFrame, idx_df: pd.DataFrame, ws_idx) -> Dict[str, Any]:
    """
    Resolves a path/URL/ID from the 'Songs' sheet into a dictionary
    containing direct and preview links for media files.
    """
    if not raw_value:
        return {"mode": None}

    # 1. Check for full Google Drive URL
    if is_url(raw_value):
        match = re.search(r"/d/([A-Za-z0-9_-]+)", raw_value) or re.search(r"[?&]id=([A-Za-z0-9_-]+)", raw_value)
        if match:
            file_id = match.group(1)
            return {"mode": "url", "id": file_id, "preview": drive_preview_url(file_id), "direct": drive_direct_url(file_id)}
        # If it's a URL but not a recognizable Drive link, return it as is
        return {"mode": "external_url", "url": raw_value}

    # 2. Check for Google Drive ID
    if is_gdrive_id_like(raw_value):
        file_id = raw_value
        return {"mode": "url", "id": file_id, "preview": drive_preview_url(file_id), "direct": drive_direct_url(file_id)}

    # 3. Fallback to local path (for local testing)
    if os.path.exists(raw_value):
        return {"mode": "local", "path": raw_value}

    # 4. Search in Drive Index or via API as a last resort
    hit = _idx_lookup(idx_df, raw_value)
    if not hit:
        from .gsheet import cfg_get # Local import to avoid circular dependency
        parent = cfg_get(cfg, f"DRIVE_FOLDER_{kind.upper()}_ID") or cfg_get(cfg, "DRIVE_FOLDER_ROOT_ID")
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
                _idx_append(ws_idx, {"name": raw_value, **hit})

    if hit:
        return {"mode": "url", "id": hit["id"], "preview": drive_preview_url(hit["id"]), "direct": drive_direct_url(hit["id"])}

    # If all else fails, treat it as a broken link/path
    return {"mode": "not_found", "path": raw_value}
