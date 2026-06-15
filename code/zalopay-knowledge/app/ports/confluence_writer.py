from __future__ import annotations

"""ConfluenceWriterPort — write side of Confluence for workflow trigger actions.

The read path (sync/ingestion) lives in ``app/ingestion/confluence.py``. This
port is the *write* surface the workflow platform needs when a Jira event's
trigger action says "update/append a Confluence page" — e.g. posting a workflow
run summary back onto the SOP page.

Raises:
    app.ports.errors.ConfluenceUnavailable: on transport/auth/API errors.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class ConfluenceWriterPort(Protocol):
    """Minimal Confluence Cloud write surface used by trigger actions."""

    def create_page(self, *, space_key: str, title: str, body_storage: str) -> dict:
        """Create a page (Confluence *storage* XHTML body). Returns ``{"id","url"}``."""
        ...

    def update_page(self, *, page_id: str, title: str, body_storage: str) -> dict:
        """Replace a page's body with *body_storage*. Returns ``{"id","url","version"}``."""
        ...

    def append_to_page(self, *, page_id: str, html_fragment: str) -> dict:
        """Append an XHTML *html_fragment* to the page's existing body.

        Reads the current storage body, concatenates, and writes a new version.
        Returns ``{"id","url","version"}``.
        """
        ...

    def add_labels(self, *, page_id: str, labels: list[str]) -> list[str]:
        """Attach global labels to a page. Returns the resulting label names.

        Labels must be colon-free (Confluence rejects ``:``) — use a hyphen,
        e.g. ``status-active``.
        """
        ...

    def is_ready(self) -> bool:
        """True when Confluence write credentials are configured. Never raises."""
        ...
