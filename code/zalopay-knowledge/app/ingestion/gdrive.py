from __future__ import annotations

"""Google Drive PDF sync — lists PDFs and extracts text with pypdf."""

import io
import logging
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from app.config import Settings

logger = logging.getLogger(__name__)


class GDriveClient:
    """Read-only Drive folder listing + PDF download."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._service = None

    def configured(self) -> bool:
        return bool(
            self._settings.gdrive_folder_id
            and (self._settings.gdrive_sa_json_path or self._settings.gdrive_api_key)
        )

    def _get_service(self):
        if self._service is not None:
            return self._service
        from googleapiclient.discovery import build

        if self._settings.gdrive_sa_json_path:
            from google.oauth2 import service_account

            creds = service_account.Credentials.from_service_account_file(
                self._settings.gdrive_sa_json_path,
                scopes=["https://www.googleapis.com/auth/drive.readonly"],
            )
            self._service = build("drive", "v3", credentials=creds, cache_discovery=False)
        elif self._settings.gdrive_api_key:
            self._service = build("drive", "v3", developerKey=self._settings.gdrive_api_key)
        else:
            raise ValueError("Google Drive credentials are not configured")
        return self._service

    def list_pdfs(self) -> list[dict[str, Any]]:
        service = self._get_service()
        folder_id = self._settings.gdrive_folder_id
        q = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
        results = (
            service.files()
            .list(q=q, fields="files(id, name, modifiedTime, webViewLink)", pageSize=100)
            .execute()
        )
        return results.get("files", [])

    def download_pdf(self, file_id: str) -> bytes:
        service = self._get_service()
        data = service.files().get_media(fileId=file_id).execute()
        return data

    def extract_text(self, pdf_bytes: bytes) -> list[tuple[int, str]]:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages: list[tuple[int, str]] = []
        for i, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append((i, text))
        return pages


def save_pdf_local(pdf_bytes: bytes, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(pdf_bytes)
