from __future__ import annotations

"""Workflow platform — the agent-as-executor layer.

A *workflow* is an ordinary Confluence page (space ``Workflow``, label
``zalopay-workflow``) written to the template in
``use-case/SOLUTION-workflow-platform.md`` (Tầng 1).  This package turns such a
page into something the graph can run:

- :mod:`app.workflow.models` — typed :class:`WorkflowDefinition` / steps / lifecycle.
- :mod:`app.workflow.parser` — LLM-based extraction (page text → definition) plus
  the ACTIVE-only execution gate (:func:`is_executable`).

Discovery and execution live as graph nodes
(``app/graph/nodes/workflow_discovery.py`` / ``workflow_executor.py``).
"""

from app.workflow.models import (
    LifecycleState,
    WorkflowDefinition,
    WorkflowStep,
    WorkflowTrigger,
)
from app.workflow.parser import is_executable, parse_workflow
from app.workflow.triggers import match_trigger

__all__ = [
    "LifecycleState",
    "WorkflowStep",
    "WorkflowTrigger",
    "WorkflowDefinition",
    "parse_workflow",
    "is_executable",
    "match_trigger",
]
