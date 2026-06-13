from __future__ import annotations

"""Prompt loader for versioned YAML prompt files.

Usage::

    from app.prompts import load_prompt, load_yaml

    prompt = load_prompt("router")           # loads router.v1.yaml
    prompt = load_prompt("grade", version=2) # loads grade.v2.yaml

    messages = prompt.render(
        question="What is the KYC threshold?",
        department_catalog="...",
    )
    # returns {"system": "...", "user": "..."}

    refusals = load_yaml("refusal_templates")  # loads raw YAML dict
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_PROMPTS_DIR = Path(__file__).parent


@dataclass
class Prompt:
    """A versioned prompt with system and user templates.

    Templates use Python ``str.format(**kwargs)`` syntax.  All ``{placeholder}``
    names are documented in each YAML file's top-level ``required_inputs`` key.

    Example::

        p = load_prompt("router")
        msgs = p.render(question="...", department_catalog="...")
        # -> {"system": "...", "user": "..."}
    """

    name: str
    version: int
    system: str
    user: str
    required_inputs: list[str]
    description: str

    def render(self, **kwargs: Any) -> dict[str, str]:
        """Format system and user templates with *kwargs*.

        Missing keys are handled gracefully: the ``{placeholder}`` text is
        left as-is rather than raising a ``KeyError``.  This prevents a
        missing optional placeholder from crashing the entire node -- log a
        warning instead so it's visible in the audit trail.

        Args:
            **kwargs: Values for every ``{placeholder}`` in the templates.

        Returns:
            ``{"system": ..., "user": ...}`` ready to pass as messages.

        Note:
            Substitution is targeted: only ``{name}`` tokens for the declared
            ``required_inputs`` are replaced.  Every other brace is left
            untouched, so literal JSON braces in an "Output format" schema do
            NOT need escaping.  (We deliberately avoid ``str.format``/``format_map``
            here — they choke on the ``{ "key": ... }`` examples the prompts
            embed.)
        """
        import logging

        logger = logging.getLogger(__name__)

        missing = [k for k in self.required_inputs if k not in kwargs]
        if missing:
            logger.warning(
                "Prompt %s.v%d is missing required inputs: %s",
                self.name,
                self.version,
                missing,
            )

        return {
            "system": self._substitute(self.system, kwargs, logger),
            "user": self._substitute(self.user, kwargs, logger),
        }

    def _substitute(self, template: str, values: dict, logger) -> str:
        """Replace ``{key}`` for each declared required input; leave the rest as-is.

        Only the documented ``required_inputs`` are treated as placeholders.
        This keeps literal JSON braces (e.g. ``{"intent": ...}`` in output-format
        sections) intact without the prompt author having to double them.
        """
        result = template
        for key in self.required_inputs:
            token = "{" + key + "}"
            if key in values:
                result = result.replace(token, str(values[key]))
            elif token in result:
                logger.warning(
                    "Prompt %s.v%d: placeholder {%s} has no value",
                    self.name,
                    self.version,
                    key,
                )
        return result


def load_prompt(name: str, version: int = 1) -> Prompt:
    """Load ``<name>.v<version>.yaml`` from the prompts directory.

    Args:
        name: Prompt name without version suffix (e.g. ``"router"``).
        version: Integer version number (default 1).

    Returns:
        A :class:`Prompt` instance.

    Raises:
        FileNotFoundError: when the YAML file does not exist.
        ValueError: when the YAML file is missing required keys.
    """
    filename = f"{name}.v{version}.yaml"
    path = _PROMPTS_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {path}.  "
            f"Available prompts: {[f.name for f in _PROMPTS_DIR.glob('*.yaml')]}"
        )

    data = load_yaml(name, version)

    for required_key in ("system", "user"):
        if required_key not in data:
            raise ValueError(
                f"Prompt file {filename} is missing required key '{required_key}'"
            )

    return Prompt(
        name=name,
        version=version,
        system=data["system"],
        user=data["user"],
        required_inputs=data.get("required_inputs", []),
        description=data.get("description", ""),
    )


def load_yaml(name: str, version: int = 1) -> dict[str, Any]:
    """Load raw YAML data from ``<name>.v<version>.yaml``.

    Use this for data files (e.g. ``refusal_templates``) that are not prompt
    templates and should not be wrapped in a :class:`Prompt` object.

    Args:
        name: File name without version suffix.
        version: Integer version number (default 1).

    Returns:
        Parsed YAML as a Python dict.

    Raises:
        FileNotFoundError: when the YAML file does not exist.
    """
    filename = f"{name}.v{version}.yaml"
    path = _PROMPTS_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}
