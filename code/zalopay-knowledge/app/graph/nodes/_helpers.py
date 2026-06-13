from __future__ import annotations

"""Shared helpers for graph nodes.

Pure functions only — no LLM/IO side effects, no global state.  Keeping these
here lets every node stay small and lets us unit-test the fiddly bits (JSON
repair, claim extraction, language detection) in isolation.
"""

import json
import re
import time
from typing import Any

from app.graph.state import Chunk, Citation


# ── Time / budget ──────────────────────────────────────────────────────────────

def remaining_budget(deadline_ts: float | None) -> float:
    """Return seconds left until *deadline_ts*, or ``inf`` when unset.

    Nodes use this to derive a per-call LLM ``timeout_s`` and to refuse early
    instead of overrunning the global graph budget.
    """
    if not deadline_ts:
        return float("inf")
    return max(0.0, deadline_ts - time.time())


def budget_exceeded(deadline_ts: float | None) -> bool:
    """True when the graph budget deadline has already passed."""
    return remaining_budget(deadline_ts) <= 0.0


# ── JSON parsing ────────────────────────────────────────────────────────────────

_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


def parse_json_response(text: str) -> Any:
    """Best-effort parse of an LLM response that should be JSON.

    Handles the common ways a model wraps JSON despite "JSON only" instructions:
    markdown code fences, leading prose, and trailing commentary.  We strip
    fences, then fall back to extracting the first balanced ``{...}`` or
    ``[...]`` span.

    Args:
        text: Raw model output.

    Returns:
        The parsed object (dict or list).

    Raises:
        ValueError: when no valid JSON can be recovered.
    """
    if text is None:
        raise ValueError("Cannot parse JSON from None")

    candidate = _FENCE_RE.sub("", text.strip())

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    span = _first_json_span(candidate)
    if span is not None:
        try:
            return json.loads(span)
        except json.JSONDecodeError:
            pass

    raise ValueError(f"No valid JSON found in model output: {text[:200]!r}")


def _first_json_span(text: str) -> str | None:
    """Return the first balanced ``{...}`` or ``[...]`` substring, or None."""
    start = None
    opener = None
    closer = None
    for i, ch in enumerate(text):
        if ch in "{[":
            start = i
            opener = ch
            closer = "}" if ch == "{" else "]"
            break
    if start is None:
        return None

    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == opener:
            depth += 1
        elif ch == closer:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


# ── Chunk rendering ─────────────────────────────────────────────────────────────

def render_chunks(chunks: list[Chunk], *, start: int = 1) -> str:
    """Render *chunks* as a numbered block for grade/synthesize prompts.

    Each chunk is labelled ``[n]`` (numbered from *start*) and annotated with
    its lifecycle state so the synthesize prompt can apply the deprecation /
    sunset rules.  ``start=0`` matches the grade prompt's 0-indexed contract;
    ``start=1`` matches the synthesize prompt's 1-indexed citation contract.
    """
    blocks: list[str] = []
    for offset, ch in enumerate(chunks):
        idx = start + offset
        lifecycle = (ch.get("lifecycle_state") or "active").upper()
        title = ch.get("title") or "(untitled)"
        section = ch.get("section")
        header = f"[{idx}] {title}"
        if section:
            header += f" — {section}"
        if lifecycle != "ACTIVE":
            header += f"  ({lifecycle})"
        blocks.append(f"{header}\n{ch.get('text', '').strip()}")
    return "\n\n".join(blocks)


def chunk_to_citation(chunk: Chunk) -> Citation:
    """Project a retrieved :class:`Chunk` into a response :class:`Citation`."""
    lifecycle = chunk.get("lifecycle_state") or "active"
    return Citation(
        title=chunk.get("title", "(untitled)"),
        url=chunk.get("url", ""),
        section=chunk.get("section"),
        last_modified=chunk.get("last_modified"),
        lifecycle_state=lifecycle,
        deprecated=lifecycle == "deprecated",
        successor_url=None,
        source_type=chunk.get("source_type"),
        page=chunk.get("page"),
    )


# ── Claim extraction (for the verify node) ──────────────────────────────────────

_CITATION_MARKER_RE = re.compile(r"\[(\d+)\]")


def extract_claims(answer: str, chunks: list[Chunk]) -> list[dict]:
    """Split *answer* into citation-bearing claims paired with their source text.

    A "claim" is a sentence (or list item) that contains at least one ``[n]``
    citation marker.  Each marker is resolved to the 1-indexed chunk it cites;
    the claim is paired with the concatenated text of every chunk it references.

    Args:
        answer: The synthesized answer with inline ``[n]`` markers.
        chunks: The graded chunks, in the same order the markers index into
                (marker ``[1]`` → ``chunks[0]``).

    Returns:
        A list of ``{"id", "claim", "cited": [int], "source_text"}`` dicts —
        one per citation-bearing sentence.  Sentences with no marker are
        excluded (nothing to verify against).
    """
    claims: list[dict] = []
    # Split on sentence terminators and newlines while keeping it simple/robust.
    segments = re.split(r"(?<=[.!?])\s+|\n+", answer)
    claim_id = 0
    for seg in segments:
        seg = seg.strip()
        if not seg:
            continue
        markers = [int(m) for m in _CITATION_MARKER_RE.findall(seg)]
        if not markers:
            continue
        cited_texts: list[str] = []
        valid_markers: list[int] = []
        for n in markers:
            if 1 <= n <= len(chunks):
                cited_texts.append(chunks[n - 1].get("text", ""))
                valid_markers.append(n)
        if not cited_texts:
            continue
        claims.append(
            {
                "id": claim_id,
                "claim": seg,
                "cited": valid_markers,
                "source_text": "\n---\n".join(cited_texts),
            }
        )
        claim_id += 1
    return claims


def render_claims(claims: list[dict]) -> str:
    """Render extracted claims for the verify prompt's ``claims_with_sources``."""
    blocks: list[str] = []
    for c in claims:
        blocks.append(
            f"Claim id {c['id']}: {c['claim']}\n"
            f"Cited source text:\n{c['source_text'].strip()}"
        )
    return "\n\n".join(blocks)


# ── Language detection ──────────────────────────────────────────────────────────

# Characters that only appear in Vietnamese (precomposed diacritics + đ).
_VI_CHARS = set(
    "ăâđêôơưĂÂĐÊÔƠƯ"
    "àáạảãâầấậẩẫăằắặẳẵ"
    "èéẹẻẽêềếệểễ"
    "ìíịỉĩ"
    "òóọỏõôồốộổỗơờớợởỡ"
    "ùúụủũưừứựửữ"
    "ỳýỵỷỹ"
    "ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨ"
    "ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸ"
)


def detect_language(text: str) -> str:
    """Return ``"vi"`` if *text* looks Vietnamese, else ``"en"``.

    Heuristic: any Vietnamese-specific diacritic ⇒ Vietnamese.  This is a cheap
    pre-LLM signal used by ``ingest_context``; the model is never asked to
    detect language, keeping the path token-free.
    """
    if not text:
        return "en"
    if any(ch in _VI_CHARS for ch in text):
        return "vi"
    return "en"


# ── Role style ──────────────────────────────────────────────────────────────────

_ROLE_STYLE: dict[str, str] = {
    "engineer": (
        "Technical and precise. Use exact field names, thresholds, and config "
        "keys. Prefer numbered steps and code-style formatting for procedures."
    ),
    "pm": (
        "Outcome-oriented. Lead with the decision or policy, then the rationale. "
        "Keep it concise; surface trade-offs and ownership clearly."
    ),
    "ops": (
        "Action-first. Give the runbook steps in order, call out prerequisites "
        "and escalation contacts, and highlight anything time-sensitive."
    ),
    "risk": (
        "Compliance-focused. State the rule, the threshold, and the source of "
        "authority explicitly. Be conservative and flag any ambiguity."
    ),
    "business": (
        "Plain-language and non-technical. Avoid jargon; explain implications "
        "for partners or customers. Keep it short and reassuring."
    ),
}

_DEFAULT_ROLE_STYLE = (
    "Clear and professional. Lead with the direct answer, then supporting detail."
)


def role_style_for(role: str | None) -> str:
    """Return the synthesis tone guidance for *role* (falls back to a default)."""
    if not role:
        return _DEFAULT_ROLE_STYLE
    return _ROLE_STYLE.get(role.lower(), _DEFAULT_ROLE_STYLE)
