"""Department key constants for tests — always sourced from the registry."""

from __future__ import annotations

from app.common.departments import DepartmentKey, all_departments, iter_keys

RISK = DepartmentKey.RISK.value
GROW = DepartmentKey.GROW_ENABLEMENT.value
BANK = DepartmentKey.BANK_PARTNERSHIPS.value

ALL_DEPARTMENT_KEYS = [dept.key for dept in all_departments()]
ALL_KEYS = list(iter_keys())

DEFAULT_HOME = DepartmentKey.RISK.value
