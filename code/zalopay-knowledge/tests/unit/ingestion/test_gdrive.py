from __future__ import annotations

from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings
from app.ingestion.gdrive import GDriveClient, save_pdf_local


def _mock_google_build():
    """Inject fake google API modules for _get_service credential checks."""
    discovery = ModuleType("googleapiclient.discovery")
    discovery.build = MagicMock()
    googleapiclient = ModuleType("googleapiclient")
    googleapiclient.discovery = discovery  # type: ignore[attr-defined]
    return patch.dict(
        "sys.modules",
        {
            "googleapiclient": googleapiclient,
            "googleapiclient.discovery": discovery,
        },
    )


class TestGDriveClient:
    def test_configured_with_folder_and_api_key(self, gdrive_settings: Settings):
        client = GDriveClient(gdrive_settings)
        assert client.configured() is True

    def test_not_configured_without_folder(self, tmp_path):
        settings = Settings(
            gdrive_api_key="key",
            gdrive_folder_id="",
            index_dir=str(tmp_path / "index"),
        )
        client = GDriveClient(settings)
        assert client.configured() is False

    def test_list_pdfs_queries_drive_api(self, gdrive_settings: Settings):
        client = GDriveClient(gdrive_settings)
        mock_service = MagicMock()
        mock_files = MagicMock()
        mock_list = MagicMock()
        mock_list.execute.return_value = {
            "files": [
                {
                    "id": "file-1",
                    "name": "partner-guide.pdf",
                    "modifiedTime": "2025-01-10T08:00:00Z",
                    "webViewLink": "https://drive.google.com/file/d/file-1",
                }
            ]
        }
        mock_files.list.return_value = mock_list
        mock_service.files.return_value = mock_files

        with patch.object(client, "_get_service", return_value=mock_service):
            pdfs = client.list_pdfs()

        assert len(pdfs) == 1
        assert pdfs[0]["name"] == "partner-guide.pdf"
        q = mock_files.list.call_args[1]["q"]
        assert gdrive_settings.gdrive_folder_id in q
        assert "application/pdf" in q

    def test_download_pdf_returns_bytes(self, gdrive_settings: Settings):
        client = GDriveClient(gdrive_settings)
        pdf_bytes = b"%PDF-1.4 mock content"
        mock_service = MagicMock()
        mock_files = MagicMock()
        mock_get_media = MagicMock()
        mock_get_media.execute.return_value = pdf_bytes
        mock_files.get_media.return_value = mock_get_media
        mock_service.files.return_value = mock_files

        with patch.object(client, "_get_service", return_value=mock_service):
            result = client.download_pdf("file-1")

        assert result == pdf_bytes
        mock_files.get_media.assert_called_once_with(fileId="file-1")

    def test_extract_text_from_pdf_pages(self, gdrive_settings: Settings):
        client = GDriveClient(gdrive_settings)
        mock_page_1 = MagicMock()
        mock_page_1.extract_text.return_value = "  Bank partnership overview.  "
        mock_page_2 = MagicMock()
        mock_page_2.extract_text.return_value = ""
        mock_page_3 = MagicMock()
        mock_page_3.extract_text.return_value = "Fee schedule details."

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page_1, mock_page_2, mock_page_3]

        with patch("app.ingestion.gdrive.PdfReader", return_value=mock_reader):
            pages = client.extract_text(b"%PDF-mock")

        assert pages == [
            (1, "Bank partnership overview."),
            (3, "Fee schedule details."),
        ]

    def test_extract_text_empty_pdf(self, gdrive_settings: Settings):
        client = GDriveClient(gdrive_settings)
        mock_reader = MagicMock()
        mock_reader.pages = []

        with patch("app.ingestion.gdrive.PdfReader", return_value=mock_reader):
            assert client.extract_text(b"%PDF-empty") == []

    def test_get_service_raises_without_credentials(self, tmp_path):
        settings = Settings(index_dir=str(tmp_path / "index"))
        client = GDriveClient(settings)
        with _mock_google_build():
            with pytest.raises(ValueError, match="not configured"):
                client._get_service()


class TestSavePdfLocal:
    def test_writes_bytes_to_destination(self, tmp_path: Path):
        dest = tmp_path / "pdfs" / "doc.pdf"
        payload = b"%PDF-1.4 test"
        save_pdf_local(payload, dest)
        assert dest.exists()
        assert dest.read_bytes() == payload
