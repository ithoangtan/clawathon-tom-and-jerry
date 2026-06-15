from __future__ import annotations

"""LLM-based workflow parser: Confluence page text → :class:`WorkflowDefinition`.

The page format is loose Confluence markup, so a deterministic markdown parser is
brittle.  Instead we ask the SMALL model to extract a strict JSON object
(``workflow_parse.v1.yaml``) and validate it with Pydantic.  Any failure becomes
a typed :class:`WorkflowParseError` that the executor turns into a graceful reply.
"""

import logging

from pydantic import ValidationError

from app.config import Settings, get_settings
from app.graph.nodes._helpers import parse_json_response
from app.ports.errors import LLMUnavailable, WorkflowParseError
from app.ports.llm import LLMPort
from app.ports.types import ModelTier
from app.prompts import load_prompt
from app.workflow.models import WorkflowDefinition

logger = logging.getLogger(__name__)

_prompt = load_prompt("workflow_parse")


def parse_workflow(
    page_text: str,
    *,
    llm: LLMPort,
    settings: Settings | None = None,
) -> WorkflowDefinition:
    """Parse the full text of a workflow page into a :class:`WorkflowDefinition`.

    Args:
        page_text: The concatenated text of the workflow Confluence page (all
            chunks, in page order).
        llm: SMALL-tier-capable LLM adapter.
        settings: Injectable settings (defaults to the cached singleton).

    Returns:
        A validated :class:`WorkflowDefinition`.

    Raises:
        WorkflowParseError: on empty input, LLM failure, non-JSON output, or
            schema-validation failure.  Never lets a raw exception escape.
    """
    cfg = settings or get_settings()
    if not (page_text or "").strip():
        raise WorkflowParseError("Workflow page is empty — nothing to parse")

    rendered = _prompt.render(page_text=page_text)
    messages = [
        {"role": "system", "content": rendered["system"]},
        {"role": "user", "content": rendered["user"]},
    ]
    try:
        result = llm.complete(
            tier=ModelTier.SMALL,
            messages=messages,
            temperature=0.0,
            response_format="json",
            timeout_s=cfg.branch_timeout_s,
        )
    except LLMUnavailable as exc:
        raise WorkflowParseError(f"LLM unavailable while parsing workflow: {exc}") from exc

    try:
        data = parse_json_response(result.text)
    except ValueError as exc:
        logger.warning("Workflow parse: non-JSON LLM output: %s", result.text[:200])
        raise WorkflowParseError("Workflow parser returned malformed JSON") from exc

    if not isinstance(data, dict):
        raise WorkflowParseError("Workflow parser did not return a JSON object")

    try:
        defn = WorkflowDefinition.model_validate(data)
    except ValidationError as exc:
        logger.warning("Workflow parse: schema validation failed: %s", exc)
        raise WorkflowParseError(f"Workflow definition failed validation: {exc}") from exc

    if not defn.name:
        raise WorkflowParseError("Workflow definition is missing a name")

    logger.info(
        "Parsed workflow %r (status=%s, %d steps)",
        defn.name,
        defn.definition_status,
        len(defn.steps),
    )
    return defn


def is_executable(defn: WorkflowDefinition) -> tuple[bool, str | None]:
    """The centralised definition-lifecycle gate (SOLUTION §"execute rule").

    Only ``ACTIVE`` workflows run automatically.  ``DEPRECATED`` returns a
    warning (the executor declines to run it in the one-pass demo); every other
    status returns a reason it cannot run.

    Returns:
        ``(True, None)`` when executable; otherwise ``(False, <reason/warning>)``.
    """
    status = defn.definition_status
    if status == "ACTIVE":
        return True, None
    if status == "DEPRECATED":
        return (
            False,
            "This workflow is DEPRECATED — a newer version likely exists. "
            "It will not be run automatically; confirm explicitly to proceed.",
        )
    return (
        False,
        f"This workflow's definition status is {status}; only ACTIVE workflows can be executed.",
    )
