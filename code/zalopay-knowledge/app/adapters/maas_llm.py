from __future__ import annotations

"""OpenAI LLM adapter — the :class:`LLMPort` implementation targeting OpenAI.

Switched from VNG MaaS (Qwen/baai models) to OpenAI (gpt-5.4-nano).
The previous VNG MaaS implementation with model-catalogue fallback and
daily-quota tracking is commented out at the bottom of this file for reference.

On AgentBase: the OpenAI API key is fetched from the Identity provider
``identity-openai`` (Access Control → API Key provider).
Local dev: set ``OPENAI_API_KEY`` in .env or the ``OPENAI_API_KEY`` env var.

The class is still named ``VngMaasLLM`` for backward compatibility so
``deps.py`` and any other importers do not need changes.
"""

import logging
import time

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    BadRequestError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)
from tenacity import Retrying, retry_if_exception, stop_after_attempt, wait_exponential

from app.config import Settings, get_settings
from app.ports.errors import LLMUnavailable
from app.ports.types import LLMResult, ModelTier

logger = logging.getLogger(__name__)

_MAX_ATTEMPTS = 3


def _is_transient(exc: BaseException) -> bool:
    """True for errors worth retrying with backoff."""
    if isinstance(exc, RateLimitError):
        try:
            retry_after = float(exc.response.headers.get("Retry-After", "0"))
        except Exception:  # noqa: BLE001
            retry_after = 0.0
        return retry_after < 3600
    if isinstance(exc, (APITimeoutError, APIConnectionError, InternalServerError)):
        return True
    if isinstance(exc, APIStatusError):
        return 500 <= getattr(exc, "status_code", 0) < 600
    return False


def _resolve_api_key(cfg: Settings) -> str:
    """Fetch OpenAI key from AgentBase Identity or fall back to env var."""
    from app.adapters.openai_credentials import resolve_openai_api_key
    return resolve_openai_api_key(cfg)


class VngMaasLLM:
    """OpenAI LLM client (gpt-5.4-nano) — backward-compat name kept for deps.py."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._cfg = settings or get_settings()
        api_key = _resolve_api_key(self._cfg)
        self._client = OpenAI(
            api_key=api_key or "missing",  # "missing" → fails only on actual call
            base_url=self._cfg.openai_base_url or None,
        )
        self._last_model: dict[str, str] = {}

    # ── LLMPort ───────────────────────────────────────────────────────────────

    def is_reachable(self, *, timeout_s: float = 3.0) -> bool:
        """Lightweight readiness probe — must not raise."""
        t0 = time.monotonic()
        try:
            self._client.models.list(timeout=timeout_s)
            logger.info("OpenAI ping OK (%.0fms)", (time.monotonic() - t0) * 1000)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("OpenAI ping failed (%.0fms): %s", (time.monotonic() - t0) * 1000, exc)
            return False

    def complete(
        self,
        *,
        tier: ModelTier,
        messages: list[dict],
        temperature: float = 0.0,
        max_tokens: int | None = None,
        response_format: str = "text",
        timeout_s: float | None = None,
    ) -> LLMResult:
        """Send *messages* to the model for *tier* and return an :class:`LLMResult`."""
        model = self._cfg.small_model if tier == ModelTier.SMALL else self._cfg.main_model
        if not model:
            var = "SMALL_MODEL" if tier == ModelTier.SMALL else "MAIN_MODEL"
            raise LLMUnavailable(f"{var} is not configured")

        t0 = time.monotonic()
        want_json = response_format == "json"
        effective_timeout = timeout_s if timeout_s is not None else self._cfg.llm_request_timeout_s

        base_kwargs: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "timeout": effective_timeout,
        }
        if max_tokens is not None:
            base_kwargs["max_tokens"] = max_tokens

        json_modes = [True, False] if want_json else [False]
        last_exc: BaseException | None = None

        for use_json in json_modes:
            kwargs = dict(base_kwargs)
            if use_json:
                kwargs["response_format"] = {"type": "json_object"}
            try:
                resp, retried = self._call_with_retry(kwargs)
            except BadRequestError as exc:
                last_exc = exc
                if use_json:
                    logger.warning(
                        "OpenAI rejected JSON mode for %s; retrying as text (%.0fms)",
                        model, (time.monotonic() - t0) * 1000,
                    )
                    continue
                logger.error("LLM model=%s bad request: %s", model, exc)
                raise LLMUnavailable(str(exc)) from exc
            except (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError, APIStatusError) as exc:
                logger.error(
                    "LLM model=%s unavailable after retries (%.0fms): %s",
                    model, (time.monotonic() - t0) * 1000, exc,
                )
                raise LLMUnavailable(str(exc)) from exc

            degraded = retried or (want_json and not use_json)
            result = self._to_result(resp, degraded=degraded, model_used=model)
            self._last_model[tier.value] = model
            logger.info(
                "LLM model=%s → %d tokens degraded=%s (%.0fms)",
                model, (result.usage or {}).get("total_tokens", 0),
                degraded, (time.monotonic() - t0) * 1000,
            )
            return result

        raise LLMUnavailable(f"exhausted modes for {model}: {last_exc}") from last_exc

    def get_last_model(self, tier: ModelTier) -> str:
        return self._last_model.get(
            tier.value,
            self._cfg.small_model if tier == ModelTier.SMALL else self._cfg.main_model,
        )

    # ── internals ─────────────────────────────────────────────────────────────

    def _call_with_retry(self, kwargs: dict):
        retrying = Retrying(
            stop=stop_after_attempt(_MAX_ATTEMPTS),
            wait=wait_exponential(multiplier=0.5, max=8),
            retry=retry_if_exception(_is_transient),
            reraise=True,
        )
        resp = None
        for attempt in retrying:
            with attempt:
                attempt_num = retrying.statistics.get("attempt_number", 1)
                if attempt_num > 1:
                    logger.warning("LLM retry attempt=%d model=%s", attempt_num, kwargs.get("model", "?"))
                resp = self._client.chat.completions.create(**kwargs)
        retried = int(retrying.statistics.get("attempt_number", 1)) > 1
        return resp, retried

    @staticmethod
    def _to_result(resp, *, degraded: bool, model_used: str = "") -> LLMResult:
        try:
            text = resp.choices[0].message.content or ""
        except (IndexError, AttributeError):
            text = ""
        usage = resp.usage.model_dump() if getattr(resp, "usage", None) else {}
        return LLMResult(text=text, raw=resp.model_dump(), usage=usage, degraded=degraded, model_used=model_used)


# Exported for unit tests that patch/inspect the mapper directly.
_to_result = VngMaasLLM._to_result


# =============================================================================
# VNG MaaS (legacy) — commented out
# =============================================================================
#
# The previous implementation drove the VNG MaaS OpenAI-compatible endpoint
# (https://maas-llm-aiplatform-hcm.api.vngcloud.vn/v1) using GREENNODE_API_KEY
# or LLM_API_KEY.  It included:
#
#   - _fetch_chat_models(): GET /v1/models → filter status=="enabled" && model_type=="messages"
#   - _MODELS_CACHE_TTL = 600s model catalogue cache
#   - _quota_exhausted_until: dict[str, float] — daily-quota registry
#   - _DAILY_QUOTA_RETRY_AFTER_THRESHOLD = 3600s
#   - _models_for(tier): primary from config + dynamic catalogue fallbacks
#   - _try_model(): attempt one model, mark quota on 429 Retry-After ≥ 1h,
#     switch to next model automatically
#
# Replaced by the simpler OpenAI implementation above (no catalogue, no quota
# tracking — OpenAI enforces rate limits transparently via 429s).
#
# To re-enable VNG MaaS: restore effective_llm_api_key usage in __init__,
# restore _fetch_chat_models / _models_for / _try_model, set LLM_BASE_URL and
# LLM_API_KEY (or GREENNODE_API_KEY on AgentBase).
# =============================================================================
