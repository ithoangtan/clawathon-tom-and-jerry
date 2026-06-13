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
from app.ingestion.sync_hash import page_content_hash, resolve_document_chunks
from app.store.meta import MetaStore
from app.store.sync_state import DepartmentSyncResult, SyncOrchestrator, SyncedContentSummary

logger = logging.getLogger(__name__)


def _chunk_urls(chunks: list[dict]) -> set[str]:
    return {c["url"] for c in chunks if c.get("url")}


def _gdrive_author(file_meta: dict) -> str | None:
    owners = file_meta.get("owners")
    if isinstance(owners, list) and owners:
        owner = owners[0]
        if isinstance(owner, dict):
            return owner.get("displayName") or owner.get("emailAddress")
    return None


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

    def trigger_confluence(
        self,
        on_complete: Callable[[], None] | None = None,
        *,
        department: str | None = None,
    ) -> bool:
        if department:
            space_map = self._cfg.confluence_space_map
            if department not in space_map:
                from app.common.departments import space_env_var as dept_env_var
                try:
                    env_var = dept_env_var(department)
                except KeyError:
                    env_var = f"CONFLUENCE_SPACE_{department.upper()}"
                raise ValueError(
                    f"Department {department!r} has no Confluence space configured. "
                    f"Set {env_var}=<space-key> in your environment to enable sync for this department."
                )
        if not self._orchestrator.start("confluence", department=department):
            return False
        threading.Thread(
            target=self._run_confluence,
            kwargs={"on_complete": on_complete, "department": department},
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

    def _run_confluence(
        self,
        on_complete: Callable[[], None] | None = None,
        *,
        department: str | None = None,
    ) -> None:
        try:
            if not self._confluence.configured():
                raise ValueError("Confluence is not configured")

            total_docs = 0
            total_chunks = 0
            space_map = self._cfg.confluence_space_map
            if department:
                space_map = {department: space_map[department]}

            for dept, space_key in space_map.items():
                dept_result = DepartmentSyncResult(
                    department=dept,
                    space_key=space_key,
                    status="running",
                )
                self._orchestrator.record_department_result("confluence", dept_result)
                self._orchestrator.update_progress(
                    "confluence",
                    {"space": space_key, "department": dept},
                )
                pages = self._confluence.list_pages(space_key)
                dept_chunks: list[dict] = []
                source_records: list[dict[str, str | None]] = []
                synced_items: list[SyncedContentSummary] = []
                page_errors: list[str] = []
                for i, page in enumerate(pages):
                    page_id = str(page.get("id", ""))
                    if not page_id:
                        continue
                    try:
                        text, meta = self._confluence.fetch_page_body(page_id)
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Skip page %s: %s", page_id, exc)
                        page_errors.append(f"page {page_id}: {exc}")
                        continue
                    page_title = meta.get("title") or page.get("title", "")
                    page_url = meta.get("url", "")
                    page_labels = meta.get("labels") or []
                    synced_items.append(
                        SyncedContentSummary(
                            source_id=page_id,
                            title=page_title or page_id,
                            url=page_url or None,
                        )
                    )

                    def _build_page_chunks(
                        _text: str = text,
                        _title: str = page_title,
                        _url: str = page_url,
                        _labels: list[str] = page_labels,
                    ) -> list[dict]:
                        return chunk_text(
                            _text,
                            department=dept,
                            doc_type=classify_doc_type(
                                title=_title,
                                url=_url,
                                department=dept,
                                labels=_labels,
                            ),
                            title=_title,
                            url=_url,
                            source=page_id,
                            space=space_key,
                            labels=_labels,
                            author=meta.get("author"),
                            last_modified=meta.get("last_modified"),
                            source_type="confluence",
                        )

                    page_chunks, _skipped = resolve_document_chunks(
                        department=dept,
                        url=page_url,
                        text=text,
                        meta=self._indexer._meta,
                        chunk_builder=_build_page_chunks,
                    )
                    dept_chunks.extend(page_chunks)
                    if page_url:
                        source_records.append(
                            {
                                "url": page_url,
                                "source_id": page_id,
                                "content_hash": page_content_hash(text),
                                "last_modified": meta.get("last_modified"),
                            }
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
                self._indexer._meta.record_source_hashes(dept, source_records)
                total_docs += len(pages)
                total_chunks += count
                self._orchestrator.record_department_result(
                    "confluence",
                    DepartmentSyncResult(
                        department=dept,
                        space_key=space_key,
                        status="success",
                        page_count=len(pages),
                        chunk_count=count,
                        synced_items=synced_items,
                        errors=page_errors[-5:],
                    ),
                )

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
            source_records: list[dict[str, str | None]] = []
            department = "bank_partnerships"

            if self._gdrive.configured():
                files = self._gdrive.list_pdfs()
                for i, f in enumerate(files):
                    pdf_bytes = self._gdrive.download_pdf(f["id"])
                    file_name = f.get("name", "document.pdf")
                    file_url = f.get("webViewLink", "")
                    file_labels: list[str] = []
                    if isinstance(f.get("properties"), dict):
                        for prop in f["properties"].get("tags", []) or []:
                            if isinstance(prop, str):
                                file_labels.append(prop)
                    pages = list(self._gdrive.extract_text(pdf_bytes))
                    combined_text = "\n".join(text for _, text in pages)

                    def _build_pdf_chunks(
                        _pages: list[tuple[int, str]] = pages,
                        _name: str = file_name,
                        _url: str = file_url,
                        _labels: list[str] = file_labels,
                    ) -> list[dict]:
                        chunks: list[dict] = []
                        for page_num, text in _pages:
                            chunks.extend(
                                chunk_text(
                                    text,
                                    department=department,
                                    doc_type=classify_doc_type(
                                        title=_name,
                                        url=_url,
                                        department=department,
                                        labels=_labels,
                                    ),
                                    title=_name,
                                    url=_url,
                                    source=str(f.get("id", "")),
                                    labels=_labels,
                                    author=_gdrive_author(f),
                                    last_modified=f.get("modifiedTime"),
                                    source_type="pdf",
                                    page=page_num,
                                )
                            )
                        return chunks

                    file_chunks, _skipped = resolve_document_chunks(
                        department=department,
                        url=file_url,
                        text=combined_text,
                        meta=self._indexer._meta,
                        chunk_builder=_build_pdf_chunks,
                    )
                    all_chunks.extend(file_chunks)
                    if file_url:
                        source_records.append(
                            {
                                "url": file_url,
                                "source_id": str(f.get("id", "")),
                                "content_hash": page_content_hash(combined_text),
                                "last_modified": f.get("modifiedTime"),
                            }
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
                            pdf_url = f"file://{pdf_path.resolve()}"
                            pages = list(
                                self._gdrive.extract_text(pdf_path.read_bytes())
                            )
                            combined_text = "\n".join(text for _, text in pages)

                            def _build_local_pdf_chunks(
                                _pages: list[tuple[int, str]] = pages,
                                _path: Path = pdf_path,
                                _url: str = pdf_url,
                            ) -> list[dict]:
                                chunks: list[dict] = []
                                for page_num, text in _pages:
                                    chunks.extend(
                                        chunk_text(
                                            text,
                                            department=department,
                                            doc_type=classify_doc_type(
                                                title=_path.name,
                                                url=_url,
                                                department=department,
                                            ),
                                            title=_path.name,
                                            url=_url,
                                            source=str(_path.resolve()),
                                            source_type="pdf",
                                            page=page_num,
                                        )
                                    )
                                return chunks

                            pdf_chunks, _skipped = resolve_document_chunks(
                                department=department,
                                url=pdf_url,
                                text=combined_text,
                                meta=self._indexer._meta,
                                chunk_builder=_build_local_pdf_chunks,
                            )
                            all_chunks.extend(pdf_chunks)
                            source_records.append(
                                {
                                    "url": pdf_url,
                                    "source_id": str(pdf_path.resolve()),
                                    "content_hash": page_content_hash(combined_text),
                                    "last_modified": None,
                                }
                            )
                            self._orchestrator.update_progress(
                                "gdrive",
                                {"files_processed": i + 1, "files_total": len(pdfs)},
                            )
                        break
                if not all_chunks:
                    raise ValueError(
                        "Google Drive is not configured (set GDRIVE_FOLDER_ID + Identity "
                        "identity-google-space or local GDRIVE_* creds) and no local PDFs in corpus/pdfs/"
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
            self._indexer._meta.record_source_hashes(department, source_records)
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
