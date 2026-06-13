from __future__ import annotations

"""Application configuration via pydantic-settings.

All environment variables documented in .env.example are declared here with
strong types.  Import ``get_settings()`` everywhere — never read ``os.environ``
directly in application code.
"""

import logging
import os
from functools import lru_cache

from pydantic import Field, computed_field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.common.departments import (
    all_departments,
    confluence_space_key as lookup_confluence_space_key,
    confluence_space_map as build_confluence_space_map,
    merge_legacy_confluence_env,
    parse_confluence_spaces,
    validate_confluence_space_keys,
)


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
        populate_by_name=True,
    )

    # ── Application ──────────────────────────────────────────────────────────

    app_env: str = Field(default="local", description="Runtime environment: local | agentbase")
    log_level: str = Field(default="info", description="Log verbosity: debug|info|warning|error")
    app_version: str = Field(default="1.0.0", description="Semantic version string")

    # ── VNG MaaS LLM ─────────────────────────────────────────────────────────

    llm_base_url: str = Field(
        default="https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1",
        description="OpenAI-compatible inference base URL",
    )
    llm_api_key: str = Field(default="", description="MaaS API key")
    greennode_api_key: str = Field(
        default="",
        validation_alias="GREENNODE_API_KEY",
        description="Platform-injected MaaS key on AgentBase (fallback when LLM_API_KEY unset)",
    )
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
    confluence_api_token: str = Field(default="", description="Atlassian API token (local dev)")
    confluence_api_key_provider: str = Field(
        default="identity-confluence-zalopay-knowledge",
        description="AgentBase Identity apikey provider for Confluence token on APP_ENV=agentbase",
    )

    # Space keys — JSON map department_key → Confluence space key (see departments registry)
    confluence_spaces: dict[str, str] = Field(
        default_factory=dict,
        validation_alias="CONFLUENCE_SPACES",
        description=(
            "JSON map of department key → Confluence space key. "
            "Legacy per-department CONFLUENCE_SPACE_* vars are merged at startup."
        ),
    )

    # Individual legacy vars declared as fields so pydantic-settings reads them from
    # BOTH os.environ and the env_file (unlike bare os.environ reads in validators).
    # Merged into confluence_spaces by _merge_legacy_confluence_env.
    confluence_space_risk: str = Field(default="", validation_alias="CONFLUENCE_SPACE_RISK")
    confluence_space_grow: str = Field(default="", validation_alias="CONFLUENCE_SPACE_GROW")
    confluence_space_bank: str = Field(default="", validation_alias="CONFLUENCE_SPACE_BANK")

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
    gdrive_oauth_provider: str = Field(
        default="identity-google-space",
        description=(
            "AgentBase Identity OAuth2 provider for Google Drive "
            "(Outbound Auth name in Access Control console)."
        ),
    )
    gdrive_oauth_scopes: str = Field(
        default="https://www.googleapis.com/auth/drive.readonly",
        description="Comma-separated OAuth scopes for GDrive 3LO token",
    )
    gdrive_oauth_agent_user_id: str = Field(
        default="admin",
        description=(
            "Stable user ID passed to AgentBase 3LO flow — identifies which Google account "
            "authorized access. Change only if multiple accounts are needed."
        ),
    )
    gdrive_sa_provider: str = Field(
        default="",
        description=(
            "Optional AgentBase Identity apikey provider storing service-account JSON. "
            "Leave empty when using OAuth only."
        ),
    )

    # ── AgentBase platform (auto-injected) ────────────────────────────────────

    greennode_agent_identity: str = Field(
        default="",
        validation_alias="GREENNODE_AGENT_IDENTITY",
        description="Agent identity name on AgentBase (auto-injected at deploy)",
    )
    greennode_identity_url: str = Field(
        default="",
        validation_alias="GREENNODE_IDENTITY_URL",
        description="Identity service URL (auto-injected at deploy)",
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
    retrieve_pool: int = Field(
        default=40,
        ge=10,
        le=100,
        description="Dense candidate pool size before hybrid fusion + rerank (30–50)",
    )
    topk: int = Field(
        default=8,
        ge=1,
        le=100,
        description="Final chunks kept after rerank (MVP: 5–8)",
    )
    hybrid_search_enabled: bool = Field(
        default=True,
        description="Fuse dense retrieval with BM25 lexical scores (RRF)",
    )
    reranker_enabled: bool = Field(
        default=True,
        description="Apply cross-encoder reranker after hybrid fusion",
    )
    reranker_model: str = Field(
        default="BAAI/bge-reranker-v2-m3",
        description="Cross-encoder model for second-stage reranking",
    )
    compress_enabled: bool = Field(
        default=True,
        description="Extract relevant sentences per graded chunk before synthesis (reduces synthesis tokens ~50%)",
    )

    # ── Graph timeouts ────────────────────────────────────────────────────────

    branch_timeout_s: float = Field(
        default=15.0,
        gt=0,
        description="Per-department subgraph timeout in seconds",
    )
    graph_budget_s: float = Field(
        default=30.0,
        gt=0,
        description="Global LangGraph execution budget in seconds",
    )
    llm_request_timeout_s: float = Field(
        default=60.0,
        gt=0,
        le=300.0,
        description="Default per-request timeout for MaaS chat completions (seconds)",
    )
    health_ping_timeout_s: float = Field(
        default=3.0,
        gt=0,
        le=30.0,
        description="MaaS readiness probe timeout in seconds",
    )
    route_confidence_min: float = Field(
        default=0.55,
        ge=0.0,
        le=1.0,
        description="Router confidence threshold below which a clarifying question is emitted",
    )

    # ── Memory (STM + LTM) ───────────────────────────────────────────────────

    memory_id: str = Field(
        default="",
        description="GreenNode AgentBase Memory ID (blank locally → stateless stub)",
    )
    memory_strategy_id: str = Field(
        default="",
        description=(
            "Long-term memory strategy ID for user-preference namespace. "
            "Obtain from the Memory store detail page after creating a LTMS. "
            "Blank locally → LTM recall disabled."
        ),
    )

    # ── Security (MVP checklist §5–6) ─────────────────────────────────────────

    agent_enabled: bool = Field(
        default=True,
        description="Kill-switch: when false, chat/sync endpoints return 503",
    )
    gateway_trust_required: bool | None = Field(
        default=None,
        description=(
            "When true, reject client-supplied X-GreenNode-AgentBase-* identity headers "
            "unless accompanied by a gateway trust marker. "
            "Unset: false for APP_ENV=local, true for APP_ENV=agentbase."
        ),
    )
    gateway_trust_secret: str = Field(
        default="",
        description=(
            "Optional HMAC secret for X-GreenNode-AgentBase-Gateway-Trust. "
            "When unset, Gateway-Verified: true is required instead"
        ),
    )

    # ── Computed properties ───────────────────────────────────────────────────

    @computed_field  # type: ignore[misc]
    @property
    def gdrive_oauth_scope_list(self) -> list[str]:
        """Parsed OAuth scopes for GDrive Identity M2M requests."""
        raw = (self.gdrive_oauth_scopes or "").strip()
        if not raw:
            return ["https://www.googleapis.com/auth/drive.readonly"]
        return [part.strip() for part in raw.split(",") if part.strip()]

    @computed_field  # type: ignore[misc]
    @property
    def confluence_space_map(self) -> dict[str, str]:
        """Map of department key → Confluence space key, derived from the department registry.

        Only departments with a non-empty space key are included — callers use
        ``dept_key in settings.confluence_space_map`` to check whether a department
        is sync-ready, or ``settings.confluence_space_key(dept_key)`` for a single lookup.
        """
        return build_confluence_space_map(self)

    def confluence_space_key(self, department: str) -> str | None:
        """Return the Confluence space key for *department*, or ``None`` when unset."""
        return lookup_confluence_space_key(self, department)

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

    @computed_field  # type: ignore[misc]
    @property
    def effective_llm_api_key(self) -> str:
        """MaaS key: explicit ``LLM_API_KEY`` wins; on AgentBase fall back to ``GREENNODE_API_KEY``."""
        if self.llm_api_key:
            return self.llm_api_key
        if self.is_agentbase and self.greennode_api_key:
            return self.greennode_api_key
        return ""

    # ── Validators ────────────────────────────────────────────────────────────

    @field_validator("confluence_spaces", mode="before")
    @classmethod
    def _parse_confluence_spaces(cls, value: object) -> dict[str, str]:
        """Accept JSON string, dict, or empty for CONFLUENCE_SPACES."""
        return parse_confluence_spaces(value)

    @model_validator(mode="after")
    def _merge_legacy_confluence_env(self) -> "Settings":
        """Merge legacy CONFLUENCE_SPACE_* env vars when absent from CONFLUENCE_SPACES.

        We read from the declared field values rather than bare os.environ because
        pydantic-settings populates fields from BOTH os.environ and the env_file,
        whereas a direct os.environ lookup misses values that came only from .env.
        """
        env_from_fields: dict[str, str] = {
            "CONFLUENCE_SPACE_RISK": self.confluence_space_risk,
            "CONFLUENCE_SPACE_GROW": self.confluence_space_grow,
            "CONFLUENCE_SPACE_BANK": self.confluence_space_bank,
        }
        merged = merge_legacy_confluence_env(
            self.confluence_spaces, environ={**env_from_fields, **os.environ}
        )
        if merged != self.confluence_spaces:
            object.__setattr__(self, "confluence_spaces", merged)
        validate_confluence_space_keys(self.confluence_spaces)
        return self

    @model_validator(mode="after")
    def _apply_agentbase_security_defaults(self) -> "Settings":
        """Default gateway trust from APP_ENV when GATEWAY_TRUST_REQUIRED is unset."""
        if self.gateway_trust_required is None:
            object.__setattr__(self, "gateway_trust_required", self.is_agentbase)
        return self

    @model_validator(mode="after")
    def _validate_tls_urls(self) -> "Settings":
        """Outbound service URLs must use HTTPS (TLS in transit)."""
        for name, url in (
            ("LLM_BASE_URL", self.llm_base_url),
            ("CONFLUENCE_BASE_URL", self.confluence_base_url),
        ):
            if url and not url.startswith("https://"):
                raise ValueError(f"{name} must use https:// (TLS required)")
        return self

    @model_validator(mode="after")
    def _warn_missing_models(self) -> "Settings":
        """Emit a warning if LLM model ids are not configured.

        We don't fail hard here so the container can still start and serve the
        /health endpoint even without a fully configured LLM — the chat
        endpoint will degrade gracefully.
        """
        logger = logging.getLogger(__name__)
        if not self.small_model:
            logger.warning(
                "SMALL_MODEL is not set — routing/grading nodes will fail at runtime"
            )
        if not self.main_model:
            logger.warning(
                "MAIN_MODEL is not set — synthesis/reconcile nodes will fail at runtime"
            )
        if self.is_agentbase and not self.gateway_trust_secret:
            logger.warning(
                "GATEWAY_TRUST_SECRET is not set — production should use HMAC "
                "gateway trust instead of Gateway-Verified marker alone"
            )
        for dept in all_departments():
            if not self.confluence_space_key(dept.key):
                logger.warning(
                    "No Confluence space for department %r — set CONFLUENCE_SPACES or %s",
                    dept.key,
                    dept.space_env_var,
                )
        return self




@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached application settings singleton.

    Call ``get_settings.cache_clear()`` in tests to reload from environment.
    """
    return Settings()
