from __future__ import annotations
import io
import os
import re
import tempfile
from typing import Tuple, List

import pandas as pd
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from .excel_loader import load_excel_file, LoadReport

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]

MIME_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MIME_GOOGLE_SHEETS = "application/vnd.google-apps.spreadsheet"
MIME_SHORTCUT = "application/vnd.google-apps.shortcut"


def extract_folder_id(folder_id_or_url: str) -> str:
    if not folder_id_or_url:
        return ""
    s = str(folder_id_or_url).strip()
    m = re.search(r"/folders/([a-zA-Z0-9_-]+)", s)
    if m:
        return m.group(1)
    m = re.search(r"[?&]id=([a-zA-Z0-9_-]+)", s)
    if m:
        return m.group(1)
    return s


def get_services(credentials_path: str):
    creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=SCOPES)
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)
    sheets = build("sheets", "v4", credentials=creds, cache_discovery=False)
    return drive, sheets


def list_drive_files(drive, folder_id: str, recursive: bool = True):
    files = []
    query = f"'{folder_id}' in parents and trashed = false"
    page_token = None
    while True:
        resp = drive.files().list(
            q=query,
            fields="nextPageToken, files(id,name,mimeType,shortcutDetails)",
            pageSize=1000,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        for f in resp.get("files", []):
            # Resolver shortcuts
            if f.get("mimeType") == MIME_SHORTCUT and f.get("shortcutDetails"):
                target_id = f["shortcutDetails"].get("targetId")
                target_mime = f["shortcutDetails"].get("targetMimeType")
                if target_id:
                    f = {"id": target_id, "name": f.get("name"), "mimeType": target_mime or f.get("mimeType"), "shortcut": True}
            files.append(f)
            if recursive and f.get("mimeType") == "application/vnd.google-apps.folder":
                files.extend(list_drive_files(drive, f["id"], recursive=True))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files


def download_xlsx_from_drive(drive, file_id: str, mime_type: str, filename: str) -> str:
    if mime_type == MIME_GOOGLE_SHEETS:
        request = drive.files().export_media(fileId=file_id, mimeType=MIME_XLSX)
    else:
        request = drive.files().get_media(fileId=file_id, supportsAllDrives=True)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
    tmp.write(fh.getvalue())
    tmp.close()
    return tmp.name


def load_from_drive(folder_id_or_url: str, credentials_path: str) -> Tuple[pd.DataFrame, List[LoadReport], list]:
    folder_id = extract_folder_id(folder_id_or_url)
    drive, _ = get_services(credentials_path)
    files = list_drive_files(drive, folder_id, recursive=True)
    frames = []
    reports: List[LoadReport] = []
    scanned = []
    for f in files:
        name = f.get("name", "")
        mime = f.get("mimeType", "")
        scanned.append({"name": name, "mimeType": mime, "id": f.get("id")})
        is_supported = mime in [MIME_GOOGLE_SHEETS, MIME_XLSX] or name.lower().endswith((".xlsx", ".xlsm"))
        if not is_supported:
            continue
        try:
            tmp_path = download_xlsx_from_drive(drive, f["id"], mime, name)
            df, reps = load_excel_file(tmp_path, source_name=name)
            if not df.empty:
                frames.append(df)
            reports.extend(reps)
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        except Exception as e:
            reports.append(LoadReport(name, "", "error", 0, str(e)))
    if frames:
        return pd.concat(frames, ignore_index=True), reports, scanned
    return pd.DataFrame(), reports, scanned
