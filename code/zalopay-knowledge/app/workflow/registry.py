from __future__ import annotations

"""In-code workflow registry.

Maps a workflow slug (the part after ``wf-`` in the Jira label) to a
:class:`~app.workflow.models.WorkflowDefinition` instance that is **statically
defined in Python** rather than parsed from a Confluence page at runtime.

When the inbound Jira webhook handler finds a ``wf-<slug>`` label on a ticket,
it checks this registry first. If the slug is present, the hardcoded definition
is used directly — no Confluence page fetch, no LLM parsing. This simplifies
demo setup and avoids the OpenSearch index dependency for the workflow discovery
step.

Adding a new in-code workflow:
    1. Create ``app/workflow/definitions/my_workflow.py``.
    2. Register it here: ``WORKFLOW_REGISTRY["my-workflow"] = MY_WORKFLOW``.
    3. Label the Jira ticket: ``wf-my-workflow``.
"""

from app.workflow.definitions.campaign_risk_review import CAMPAIGN_RISK_REVIEW
from app.workflow.models import WorkflowDefinition

WORKFLOW_REGISTRY: dict[str, WorkflowDefinition] = {
    "campaign-risk-review": CAMPAIGN_RISK_REVIEW,
}
