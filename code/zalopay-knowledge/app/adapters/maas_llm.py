from __future__ import annotations

"""VngMaasLLM — the :class:`LLMPort` implementation targeting VNG MaaS.

VNG MaaS exposes an **OpenAI-compatible** inference API, so we drive it with the
official ``openai`` client pointed at ``LLM_BASE_URL``.  The same adapter works
unchanged on AgentBase, where the platform injects the MaaS key via the SDK
decorator and the base URL stays identical (03-ARCHITECTURE.md §6).

Design notes that satisfy the port contract:

* **Stateless / thread-safe** — one ``OpenAI`` client is constructed once and
  reused across concurrent department branches (the client is thread-safe).
* **Tier → model** — ``ModelTier.SMALL`` maps to ``SMALL_MODEL`` (routing /
  grading / verify), ``ModelTier.MAIN`` to ``MAIN_MODEL`` (synthesis /
  reconcile).
* **Resilience** — transient failures (timeouts, connection drops, 5xx, rate
  limits) are retried with exponential backoff; on exhaustion we raise the
  port's :class:`LLMUnavailable` so nodes degrade gracefully instead of seeing
  a raw ``openai`` error.
* **Auto-fallback on daily quota** — when a 429 carries ``Retry-After ≥ 1 h``,
  the model is marked quota-exhausted until its reset time and the next
  available chat model from ``GET /v1/models`` is tried automatically.
  No manual fallback list is required.
* **JSON mode** — ``response_format="json"`` asks the model for a JSON object.
  Not every MaaS model honours OpenAI's ``response_format`` parameter, so a
  ``BadRequest`` triggers one retry without it (marked ``degraded``); the
  node-side ``parse_json_response`` still recovers the JSON from prose.
"""

import logging
import threading
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

# Total attempts (1 initial + 2 retries) per call before declaring unavailable.
_MAX_ATTEMPTS = 3

# Retry-After threshold (seconds) above which we treat a 429 as daily quota
# exhausted (not a transient spike) and switch to the next fallback model.
_DAILY_QUOTA_RETRY_AFTER_THRESHOLD = 3600

# How long to cache the model list from /v1/models (seconds).
_MODELS_CACHE_TTL = 600

# In-memory registry: model_id → UTC epoch when daily quota resets.
# Shared across all VngMaasLLM instances in the process.
_quota_exhausted_until: dict[str, float] = {}


def _is_transient(exc: BaseException) -> bool:
    """True for errors worth retrying (network blips, 5xx). Excludes quota-exhausted 429s."""
    if isinstance(exc, RateLimitError):
        # Only retry transient rate limits (short Retry-After); daily quota is handled
        # by the fallback logic in complete(), not by tenacity.
        try:
            retry_after = float(exc.response.headers.get("Retry-After", "0"))
        except Exception:  # noqa: BLE001
            retry_after = 0.0
        return retry_after < _DAILY_QUOTA_RETRY_AFTER_THRESHOLD
    if isinstance(exc, (APITimeoutError, APIConnectionError, InternalServerError)):
        return True
    if isinstance(exc, APIStatusError):
        return 500 <= getattr(exc, "status_code", 0) < 600
    return False


def _mark_quota_exhausted(model: str, retry_after_s: float) -> None:
    _quota_exhausted_until[model] = time.time() + retry_after_s
    logger.warning(
        "Model %s daily quota exhausted; unavailable for %.0fs (~%.1fh)",
        model, retry_after_s, retry_after_s / 3600,
    )


def _is_quota_exhausted(model: str) -> bool:
    reset_at = _quota_exhausted_until.get(model, 0.0)
    if reset_at and time.time() < reset_at:
        return True
    if reset_at:
        _quota_exhausted_until.pop(model, None)
    return False


class VngMaasLLM:
    """Synchronous OpenAI-compatible LLM client for VNG MaaS."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._cfg = settings or get_settings()
        api_key = self._cfg.effective_llm_api_key or "missing"
        self._client = OpenAI(
            base_url=self._cfg.llm_base_url,
            api_key=api_key,
        )
        self._models_cache: list[str] = []
        self._models_cache_ts: float = 0.0
        self._models_cache_lock = threading.Lock()
        # Last successful model per tier — approximate, last-write-wins under concurrency.
        self._last_model: dict[str, str] = {}

    # ── LLMPort ───────────────────────────────────────────────────────────────

    def is_reachable(self, *, timeout_s: float = 3.0) -> bool:
        """Lightweight readiness probe — must not raise."""
        if not self._cfg.effective_llm_api_key:
            return False
        t0 = time.monotonic()
        try:
            self._client.models.list(timeout=timeout_s)
            logger.info("MaaS ping OK (%.0fms)", (time.monotonic() - t0) * 1000)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("MaaS ping failed (%.0fms): %s", (time.monotonic() - t0) * 1000, exc)
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
        """Send *messages* to the *tier* model and return an :class:`LLMResult`.

        Tries the configured primary model first, then falls back through all
        available chat models from the MaaS catalogue (excluding quota-exhausted
        ones) until one succeeds or all are exhausted.
        """
        if not self._cfg.effective_llm_api_key:
            raise LLMUnavailable(
                "MaaS API key is not configured (set LLM_API_KEY or GREENNODE_API_KEY on AgentBase)"
            )

        models_to_try = self._models_for(tier)
        t0 = time.monotonic()
        last_exc: BaseException | None = None

        for model in models_to_try:
            if _is_quota_exhausted(model):
                logger.info("LLM complete: skipping %s (daily quota exhausted)", model)
                continue

            result = self._try_model(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                timeout_s=timeout_s,
                t0=t0,
            )
            if isinstance(result, LLMResult):
                self._last_model[tier.value] = model
                return result
            last_exc = result

        raise LLMUnavailable(
            f"All models exhausted for tier {tier.name}: {last_exc}"
        ) from last_exc

    def get_last_model(self, tier: ModelTier) -> str:
        """Return the model ID last used for *tier*, or the configured primary if none yet."""
        return self._last_model.get(
            tier.value,
            self._cfg.small_model if tier == ModelTier.SMALL else self._cfg.main_model,
        )

    # ── Internals ─────────────────────────────────────────────────────────────

    def _fetch_chat_models(self) -> list[str]:
        """Return cached list of enabled chat model IDs from GET /v1/models.

        Refreshes every ``_MODELS_CACHE_TTL`` seconds.  Falls back to cached
        list (possibly empty) on network error so callers always get a list.
        """
        now = time.time()
        with self._models_cache_lock:
            if now - self._models_cache_ts < _MODELS_CACHE_TTL and self._models_cache:
                return list(self._models_cache)
            try:
                resp = self._client.models.list(timeout=5.0)
                models = [
                    m.id for m in resp.data
                    if getattr(m, "status", "") == "enabled"
                    and getattr(m, "model_type", "") == "messages"
                ]
                self._models_cache = models
                self._models_cache_ts = now
                logger.info("Refreshed MaaS model catalogue: %d chat models available", len(models))
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to refresh model catalogue: %s — using cached list", exc)
            return list(self._models_cache)

    def _models_for(self, tier: ModelTier) -> list[str]:
        """Return ordered model list for *tier*: configured primary first, then
        all other available chat models as dynamic fallbacks."""
        primary = self._cfg.small_model if tier == ModelTier.SMALL else self._cfg.main_model
        if not primary:
            var = "SMALL_MODEL" if tier == ModelTier.SMALL else "MAIN_MODEL"
            raise LLMUnavailable(f"{var} is not configured")

        all_chat_models = self._fetch_chat_models()
        # Primary first, then any other chat model (deduplicated, preserving catalogue order)
        others = [m for m in all_chat_models if m != primary]
        return [primary, *others]

    def _try_model(
        self,
        *,
        model: str,
        messages: list[dict],
        temperature: float,
        max_tokens: int | None,
        response_format: str,
        timeout_s: float | None,
        t0: float,
    ) -> "LLMResult | BaseException":
        """Attempt a completion with *model*; return LLMResult on success or the exception."""
        logger.info("LLM complete model=%s msgs=%d fmt=%s", model, len(messages), response_format)

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
            except RateLimitError as exc:
                try:
                    retry_after = float(exc.response.headers.get("Retry-After", "0"))
                except Exception:  # noqa: BLE001
                    retry_after = 0.0
                if retry_after >= _DAILY_QUOTA_RETRY_AFTER_THRESHOLD:
                    _mark_quota_exhausted(model, retry_after)
                    logger.warning(
                        "LLM model=%s daily quota hit (retry_after=%.0fs); switching to fallback",
                        model, retry_after,
                    )
                else:
                    logger.error(
                        "LLM model=%s rate-limited after retries (%.0fms): %s",
                        model, (time.monotonic() - t0) * 1000, exc,
                    )
                return exc
            except BadRequestError as exc:
                last_exc = exc
                if use_json:
                    logger.warning(
                        "MaaS rejected JSON mode for %s; retrying as text (%.0fms)",
                        model, (time.monotonic() - t0) * 1000,
                    )
                    continue
                logger.error("LLM model=%s bad request: %s", model, exc)
                return exc
            except (APITimeoutError, APIConnectionError, InternalServerError, APIStatusError) as exc:
                logger.error(
                    "LLM model=%s unavailable after retries (%.0fms): %s",
                    model, (time.monotonic() - t0) * 1000, exc,
                )
                return exc

            degraded = retried or (want_json and not use_json)
            result = self._to_result(resp, degraded=degraded, model_used=model)
            logger.info(
                "LLM model=%s → %d tokens degraded=%s (%.0fms)",
                model, (result.usage or {}).get("total_tokens", 0),
                degraded, (time.monotonic() - t0) * 1000,
            )
            return result

        return last_exc or Exception(f"exhausted modes for {model}")

    def _call_with_retry(self, kwargs: dict):
        """Call the chat endpoint with exponential-backoff retries for transient errors."""
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
        """Map an OpenAI ChatCompletion response onto :class:`LLMResult`."""
        try:
            text = resp.choices[0].message.content or ""
        except (IndexError, AttributeError):
            text = ""
        usage = resp.usage.model_dump() if getattr(resp, "usage", None) else {}
        return LLMResult(text=text, raw=resp.model_dump(), usage=usage, degraded=degraded, model_used=model_used)


# Exported for unit tests that patch/inspect the mapper directly.
_to_result = VngMaasLLM._to_result
