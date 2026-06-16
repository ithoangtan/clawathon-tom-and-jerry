from __future__ import annotations

"""JiraPort — interface for the workflow platform's Jira actions.

Workflow steps of type ``fetch``/``action`` read a ticket, create issues /
sub-tasks, and post comments. Nodes depend only on this Protocol so the concrete
``JiraClient`` (or a no-op stub when Jira is unconfigured) can be swapped freely.

Raises:
    app.ports.errors.JiraUnavailable: on transport/auth/API errors. Callers
        should degrade gracefully (report the action as not-performed) rather
        than failing the whole workflow run.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class JiraPort(Protocol):
    """Minimal Jira Cloud action surface used by workflow execution."""

    def get_issue(self, key: str) -> dict:
        """Fetch one issue. Returns at least ``{"key", "url", "summary", "status"}``."""
        ...

    def create_issue(
        self,
        *,
        project: str | None = None,
        summary: str,
        description: str = "",
        issuetype: str = "Task",
        parent: str | None = None,
        assignee: str | None = None,
    ) -> dict:
        """Create an issue (or sub-task when *parent* is set).

        Args:
            project: Project key; defaults to the client's configured project.
            summary: Issue summary line.
            description: Plain-text description (wrapped into Atlassian Document Format).
            issuetype: Jira issue type name (e.g. ``Task``, ``Sub-task``, ``Epic``).
            parent: Parent issue key — when set, creates a sub-task under it.
            assignee: Optional Atlassian accountId to assign.

        Returns:
            ``{"key", "url", ...}`` for the created issue. When the client is in
            dry-run mode, returns a synthetic dict with ``"dry_run": True`` and no
            network call.
        """
        ...

    def add_comment(
        self,
        *,
        key: str,
        body: str,
        code_block: str | None = None,
        code_language: str = "json",
    ) -> dict:
        """Post a comment (wrapped into ADF) on issue *key*.

        Args:
            body: Intro/plain-text paragraph(s).
            code_block: When set, appended as an ADF ``codeBlock`` (e.g. a JSON
                dump) so it renders as a fenced code block in Jira.
            code_language: Syntax-highlight language for the code block.

        Returns the created comment payload, or a synthetic ``dry_run`` dict.
        """
        ...

    def add_labels(self, *, key: str, labels: list[str]) -> dict:
        """Add labels to issue *key* (Jira labels — no spaces/colons).

        Used by the workflow executor to tag a ticket with ``agent-wf-<page_id>``
        so inbound webhooks can resolve which workflow the ticket belongs to.
        Returns ``{"key", "labels"}`` or a synthetic ``dry_run`` dict.
        """
        ...

    def assign_issue(self, *, key: str, account_id: str) -> dict:
        """Reassign issue *key* to the Atlassian *account_id* (the ``reassign``
        reaction verb — e.g. return a ticket to its reporter).

        Returns ``{"key", "account_id"}`` or a synthetic ``dry_run`` dict.
        """
        ...

    def is_ready(self) -> bool:
        """True when Jira is configured and reachable. Never raises."""
        ...
