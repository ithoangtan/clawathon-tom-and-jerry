from __future__ import annotations

"""Google Drive PDF sync — lists PDFs and extracts text with pypdf."""

import io
import logging
import re
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from app.adapters.gdrive_credentials import (
    GDRIVE_READONLY_SCOPE,
    gdrive_identity_ready,
    resolve_gdrive_credentials,
)
from app.config import Settings

logger = logging.getLogger(__name__)


class GDriveClient:
    """Read-only Drive folder listing + PDF download."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._service = None

    def configured(self) -> bool:
        if not self._settings.gdrive_folder_id:
            return False
        if self._settings.is_agentbase:
            if gdrive_identity_ready(self._settings):
                return True
            return bool(self._settings.gdrive_sa_json_path or self._settings.gdrive_api_key)
        return bool(self._settings.gdrive_sa_json_path or self._settings.gdrive_api_key)

    def _get_service(self):
        if self._service is not None:
            return self._service
        from googleapiclient.discovery import build

        creds_spec = resolve_gdrive_credentials(self._settings)
        kind = creds_spec["kind"]

        if kind == "oauth_token":
            from google.oauth2.credentials import Credentials

            creds = Credentials(token=creds_spec["token"])
            self._service = build("drive", "v3", credentials=creds, cache_discovery=False)
        elif kind == "service_account_info":
            from google.oauth2 import service_account

            creds = service_account.Credentials.from_service_account_info(
                creds_spec["info"],
                scopes=[GDRIVE_READONLY_SCOPE],
            )
            self._service = build("drive", "v3", credentials=creds, cache_discovery=False)
        elif kind == "service_account_file":
            from google.oauth2 import service_account

            creds = service_account.Credentials.from_service_account_file(
                creds_spec["path"],
                scopes=[GDRIVE_READONLY_SCOPE],
            )
            self._service = build("drive", "v3", credentials=creds, cache_discovery=False)
        elif kind == "api_key":
            self._service = build(
                "drive", "v3", developerKey=creds_spec["key"], cache_discovery=False
            )
        else:
            raise ValueError(f"Unsupported GDrive credential kind: {kind}")
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
