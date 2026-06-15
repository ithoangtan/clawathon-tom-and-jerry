from __future__ import annotations

"""Human-friendly workflow identity label.

A workflow is marked on a Jira ticket with ``wf-<slug>`` (derived from the
workflow name) instead of an opaque page id. The same label is attached to the
workflow Confluence page, so an inbound event resolves the page via a
label-filtered search (``app/integrations/jira_handler.py``).

``wf-risk-campaign-review-lucky-wheel`` is readable on the ticket; ``slugify``
strips diacritics and non-alphanumerics so the result is a valid Jira label
(no spaces, no ``:``).
"""

import re
import unicodedata

WORKFLOW_LABEL_PREFIX = "wf-"


def slugify(text: str) -> str:
    """Lowercase ASCII slug: diacritics stripped, non-alnum runs → single ``-``."""
    text = (text or "").replace("đ", "d").replace("Đ", "D")
    ascii_text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")


def workflow_label(name: str) -> str:
    """Return the ``wf-<slug>`` identity label for a workflow name."""
    slug = slugify(name)
    return f"{WORKFLOW_LABEL_PREFIX}{slug}" if slug else f"{WORKFLOW_LABEL_PREFIX}unknown"
