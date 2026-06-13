from __future__ import annotations

"""Sync orchestration — Confluence and Google Drive background jobs."""

import logging
import threading
from pathlib import Path
from typing import Callable

from app.config import Settings, get_settings
from app.ingestion.chunker import chunk_text, classify_doc_type
from app.ingestion.confluence import ConfluenceClient
from app.ingestion.gdrive import GDriveClient
from app.ingestion.indexer import IndexBuilder
from app.store.meta import MetaStore
from app.store.sync_state import SyncOrchestrator

logger = logging.getLogger(__name__)


def _chunk_urls(chunks: list[dict]) -> set[str]:
    return {c["url"] for c in chunks if c.get("url")}


class SyncService:
    """Runs ingestion jobs in background threads."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._cfg = settings or get_settings()
        meta = MetaStore(Path(self._cfg.index_dir) / "meta.db")
        self._orchestrator = SyncOrchestrator(meta)
        self._indexer = IndexBuilder(self._cfg)
        self._confluence = ConfluenceClient(self._cfg)
        self._gdrive = GDriveClient(self._cfg)

    @property
    def orchestrator(self) -> SyncOrchestrator:
        return self._orchestrator

    def trigger_confluence(self, on_complete: Callable[[], None] | None = None) -> bool:
        if not self._orchestrator.start("confluence"):
            return False
        threading.Thread(
            target=self._run_confluence,
            kwargs={"on_complete": on_complete},
            daemon=True,
        ).start()
        return True

    def trigger_gdrive(self, on_complete: Callable[[], None] | None = None) -> bool:
        if not self._orchestrator.start("gdrive"):
            return False
        threading.Thread(
            target=self._run_gdrive,
            kwargs={"on_complete": on_complete},
            daemon=True,
        ).start()
        return True

    def _run_confluence(self, on_complete: Callable[[], None] | None = None) -> None:
        try:
            if not self._confluence.configured():
                raise ValueError("Confluence is not configured")

            total_docs = 0
            total_chunks = 0
            space_map = self._cfg.confluence_space_map

            for dept, space_key in space_map.items():
                self._orchestrator.update_progress(
                    "confluence",
                    {"space": space_key, "department": dept},
                )
                pages = self._confluence.list_pages(space_key)
                dept_chunks: list[dict] = []
                for i, page in enumerate(pages):
                    page_id = str(page.get("id", ""))
                    if not page_id:
                        continue
                    try:
                        text, meta = self._confluence.fetch_page_body(page_id)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Skip page %s: %s", page_id, exc)
                        continue
                    page_title = meta.get("title") or page.get("title", "")
                    page_url = meta.get("url", "")
                    dept_chunks.extend(
                        chunk_text(
                            text,
                            department=dept,
                            doc_type=classify_doc_type(
                                title=page_title,
                                url=page_url,
                                department=dept,
                            ),
                            title=page_title,
                            url=page_url,
                            last_modified=meta.get("last_modified"),
                            source_type="confluence",
                        )
                    )
                    self._orchestrator.update_progress(
                        "confluence",
                        {
                            "pages_processed": i + 1,
                            "pages_total": len(pages),
                            "department": dept,
                        },
                    )
                removed = self._indexer.tombstone_removed_urls(
                    dept, _chunk_urls(dept_chunks)
                )
                if removed:
                    logger.info(
                        "Confluence sync: %d removed page(s) in %s → tombstoned before rebuild",
                        len(removed),
                        dept,
                    )
                count = self._indexer.rebuild_department(dept, dept_chunks)
                total_docs += len(pages)
                total_chunks += count

            self._indexer.reload_retriever()
            self._orchestrator.finish(
                "confluence",
                success=True,
                doc_count=total_docs,
                chunk_count=total_chunks,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("Confluence sync failed")
            self._orchestrator.finish("confluence", success=False, error=str(exc))
        finally:
            if on_complete:
                on_complete()

    def _run_gdrive(self, on_complete: Callable[[], None] | None = None) -> None:
        try:
            files: list[dict] = []
            all_chunks: list[dict] = []
            department = "bank_partnerships"

            if self._gdrive.configured():
                files = self._gdrive.list_pdfs()
                for i, f in enumerate(files):
                    pdf_bytes = self._gdrive.download_pdf(f["id"])
                    for page_num, text in self._gdrive.extract_text(pdf_bytes):
                        file_name = f.get("name", "document.pdf")
                        file_url = f.get("webViewLink", "")
                        all_chunks.extend(
                            chunk_text(
                                text,
                                department=department,
                                doc_type=classify_doc_type(
                                    title=file_name,
                                    url=file_url,
                                    department=department,
                                ),
                                title=file_name,
                                url=file_url,
                                last_modified=f.get("modifiedTime"),
                                source_type="pdf",
                                page=page_num,
                            )
                        )
                    self._orchestrator.update_progress(
                        "gdrive",
                        {"files_processed": i + 1, "files_total": len(files)},
                    )
            else:
                # Local dev fallback: index PDFs from corpus/pdfs/
                from pathlib import Path

                for pdf_dir in (
                    Path(self._cfg.index_dir).parent / "corpus" / "pdfs",
                    Path("corpus/pdfs"),
                ):
                    if pdf_dir.is_dir() and any(pdf_dir.glob("*.pdf")):
                        pdfs = sorted(pdf_dir.glob("*.pdf"))
                        files = [{"name": p.name} for p in pdfs]
                        for i, pdf_path in enumerate(pdfs):
                            for page_num, text in self._gdrive.extract_text(
                                pdf_path.read_bytes()
                            ):
                                pdf_url = f"file://{pdf_path.resolve()}"
                                all_chunks.extend(
                                    chunk_text(
                                        text,
                                        department=department,
                                        doc_type=classify_doc_type(
                                            title=pdf_path.name,
                                            url=pdf_url,
                                            department=department,
                                        ),
                                        title=pdf_path.name,
                                        url=pdf_url,
                                        source_type="pdf",
                                        page=page_num,
                                    )
                                )
                            self._orchestrator.update_progress(
                                "gdrive",
                                {"files_processed": i + 1, "files_total": len(pdfs)},
                            )
                        break
                if not all_chunks:
                    raise ValueError(
                        "Google Drive is not configured and no local PDFs in corpus/pdfs/"
                    )

            removed = self._indexer.tombstone_removed_urls(
                department, _chunk_urls(all_chunks)
            )
            if removed:
                logger.info(
                    "GDrive sync: %d removed PDF(s) → tombstoned before rebuild",
                    len(removed),
                )
            chunk_count = self._indexer.rebuild_department(department, all_chunks)
            self._indexer.reload_retriever()
            self._orchestrator.finish(
                "gdrive",
                success=True,
                doc_count=len(files),
                chunk_count=chunk_count,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("GDrive sync failed")
            self._orchestrator.finish("gdrive", success=False, error=str(exc))
        finally:
            if on_complete:
                on_complete()
