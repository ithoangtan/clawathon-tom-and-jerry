"""Department key constants for tests — always sourced from the registry."""

from __future__ import annotations

from app.common.departments import (
    DepartmentKey,
    iter_keys,
    routable_departments,
    routable_keys,
)

RISK = DepartmentKey.RISK.value
GROW = DepartmentKey.GROW_ENABLEMENT.value
BANK = DepartmentKey.BANK_PARTNERSHIPS.value
WORKFLOW = DepartmentKey.WORKFLOW.value

# ALL_KEYS / ALL_DEPARTMENT_KEYS historically meant "the Q&A departments". They now
# resolve to the *routable* set (excludes the non-routable ``workflow`` registry), so
# existing Q&A / graph / store / api tests keep their original semantics.
ALL_DEPARTMENT_KEYS = [dept.key for dept in routable_departments()]
ALL_KEYS = list(routable_keys())

# Full registry incl. non-routable backing corpora — for registry-level assertions.
REGISTERED_KEYS = list(iter_keys())

DEFAULT_HOME = DepartmentKey.RISK.value
