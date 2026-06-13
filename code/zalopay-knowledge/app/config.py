from __future__ import annotations

"""Application configuration via pydantic-settings.

All environment variables documented in .env.example are declared here with
strong types.  Import ``get_settings()`` everywhere — never read ``os.environ``
directly in application code.
"""

from functools import lru_cache
from typing import Any

from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.common.departments import ROLES, DepartmentKey


class Settings(BaseSettings):
    """Application settings loaded from environment / .env file.

    All secrets (API keys, tokens) are read-only at startup; the class is
    treated as immutable after construction.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # tolerate GREENNODE_* injected by platform
    )

    # ── Application ──────────────────────────────────────────────────────────

    app_env: str = Field(default="local", description="Runtime environment: local | agentbase")
    log_level: str = Field(default="info", description="Log verbosity: debug|info|warning|error")
    app_version: str = Field(default="0.1.0", description="Semantic version string")

    # ── VNG MaaS LLM ─────────────────────────────────────────────────────────

    llm_base_url: str = Field(
        default="https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1",
        description="OpenAI-compatible inference base URL",
    )
    llm_api_key: str = Field(default="", description="MaaS API key")
    small_model: str = Field(default="", description="Model id for routing/grading/verify tier")
    main_model: str = Field(default="", description="Model id for synthesis/reconcile tier")

    # ── Embeddings ────────────────────────────────────────────────────────────

    embedding_model: str = Field(
        default="intfloat/multilingual-e5-small",
        description="HuggingFace model id for local embeddings (384-dim, VI+EN)",
    )

    # ── Confluence ────────────────────────────────────────────────────────────

    confluence_base_url: str = Field(default="", description="https://<site>.atlassian.net/wiki")
    confluence_email: str = Field(default="", description="Atlassian account email for Basic auth")
    confluence_api_token: str = Field(default="", description="Atlassian API token")

    # Space keys — one per department
    confluence_space_risk: str = Field(default="", description="Space key for Risk department")
    confluence_space_grow: str = Field(
        default="", description="Space key for Grow Enablement department"
    )
    confluence_space_bank: str = Field(
        default="", description="Space key for Bank Partnerships department"
    )

    # ── Google Drive ──────────────────────────────────────────────────────────

    gdrive_sa_json_path: str = Field(
        default="", description="Path to service-account JSON (preferred for production)"
    )
    gdrive_api_key: str = Field(
        default="", description="Google API key (fallback when SA JSON not provided)"
    )
    gdrive_folder_id: str = Field(
        default="", description="Drive folder ID to sync PDFs from"
    )

    # ── Index & retrieval ────────────────────────────────────────────────────

    index_dir: str = Field(
        default="/data/index",
        description="Base directory for FAISS partitions, SQLite meta, and HF cache",
    )
    grade_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Min relevance score for a chunk to pass the grade gate (0–1)",
    )
    topk: int = Field(
        default=8,
        ge=1,
        le=100,
        description="Number of chunks to retrieve per department per query",
    )

    # ── Graph timeouts ────────────────────────────────────────────────────────

    branch_timeout_s: float = Field(
        default=20.0,
        gt=0,
        description="Per-department subgraph timeout in seconds",
    )
    graph_budget_s: float = Field(
        default=30.0,
        gt=0,
        description="Global LangGraph execution budget in seconds",
    )
    route_confidence_min: float = Field(
        default=0.55,
        ge=0.0,
        le=1.0,
        description="Router confidence threshold below which a clarifying question is emitted",
    )

    # ── Memory (STM) ──────────────────────────────────────────────────────────

    memory_id: str = Field(
        default="",
        description="GreenNode AgentBase Memory ID (blank locally → stateless stub)",
    )

    # ── Computed properties ───────────────────────────────────────────────────

    @computed_field  # type: ignore[misc]
    @property
    def confluence_space_map(self) -> dict[str, str]:
        """Map of department key → Confluence space key.

        Only includes entries where the space key is non-empty so callers can
        check ``if dept_key in settings.confluence_space_map`` to guard sync.
        """
        raw: dict[str, str] = {
            DepartmentKey.RISK: self.confluence_space_risk,
            DepartmentKey.GROW_ENABLEMENT: self.confluence_space_grow,
            DepartmentKey.BANK_PARTNERSHIPS: self.confluence_space_bank,
        }
        return {k: v for k, v in raw.items() if v}

    @computed_field  # type: ignore[misc]
    @property
    def role_dept_access(self) -> dict[str, list[str]]:
        """Which departments each role may query.

        MVP: every role may access all three departments.  Override this with
        a JSON env var ``ROLE_DEPT_ACCESS`` in the future if you need RBAC.
        All role→department mappings must use the canonical department keys
        from ``app.common.departments``.
        """
        all_depts: list[str] = [
            DepartmentKey.RISK,
            DepartmentKey.GROW_ENABLEMENT,
            DepartmentKey.BANK_PARTNERSHIPS,
        ]
        return {role: list(all_depts) for role in ROLES}

    @computed_field  # type: ignore[misc]
    @property
    def is_local(self) -> bool:
        """True when running in the local docker-compose environment."""
        return self.app_env == "local"

    @computed_field  # type: ignore[misc]
    @property
    def is_agentbase(self) -> bool:
        """True when deployed on GreenNode AgentBase."""
        return self.app_env == "agentbase"

    # ── Validators ────────────────────────────────────────────────────────────

    @model_validator(mode="after")
    def _warn_missing_models(self) -> "Settings":
        """Emit a warning if LLM model ids are not configured.

        We don't fail hard here so the container can still start and serve the
        /health endpoint even without a fully configured LLM — the chat
        endpoint will degrade gracefully.
        """
        import logging

        logger = logging.getLogger(__name__)
        if not self.small_model:
            logger.warning(
                "SMALL_MODEL is not set — routing/grading nodes will fail at runtime"
            )
        if not self.main_model:
            logger.warning(
                "MAIN_MODEL is not set — synthesis/reconcile nodes will fail at runtime"
            )
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton.

    Call ``get_settings.cache_clear()`` in tests to reload from environment.
    """
    return Settings()
