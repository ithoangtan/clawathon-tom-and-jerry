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
* **JSON mode** — ``response_format="json"`` asks the model for a JSON object.
  Not every MaaS model honours OpenAI's ``response_format`` parameter, so a
  ``BadRequest`` triggers one retry without it (marked ``degraded``); the
  node-side ``parse_json_response`` still recovers the JSON from prose.
"""

import logging

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


def _is_transient(exc: BaseException) -> bool:
    """True for errors worth retrying (network blips, rate limits, 5xx)."""
    if isinstance(
        exc,
        (APITimeoutError, APIConnectionError, RateLimitError, InternalServerError),
    ):
        return True
    if isinstance(exc, APIStatusError):  # BadRequest (400) falls through → False
        return 500 <= getattr(exc, "status_code", 0) < 600
    return False


class VngMaasLLM:
    """Synchronous OpenAI-compatible LLM client for VNG MaaS."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Build the shared OpenAI client from settings."""
        self._cfg = settings or get_settings()
        api_key = self._cfg.effective_llm_api_key or "missing"
        self._client = OpenAI(
            base_url=self._cfg.llm_base_url,
            api_key=api_key,
        )

    # ── LLMPort ───────────────────────────────────────────────────────────────

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
        """Send *messages* to the *tier* model and return an :class:`LLMResult`."""
        model = self._model_for(tier)
        if not self._cfg.effective_llm_api_key:
            raise LLMUnavailable(
                "MaaS API key is not configured (set LLM_API_KEY or GREENNODE_API_KEY on AgentBase)"
            )

        want_json = response_format == "json"
        base_kwargs: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            base_kwargs["max_tokens"] = max_tokens
        if timeout_s is not None:
            base_kwargs["timeout"] = timeout_s

        # Try JSON mode first when requested; fall back to plain text if the
        # model rejects the response_format parameter.
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
                        "MaaS rejected JSON response_format for %s; retrying as text",
                        model,
                    )
                    continue  # fall through to the text attempt
                raise LLMUnavailable(f"MaaS rejected the request: {exc}") from exc
            except (
                APITimeoutError,
                APIConnectionError,
                RateLimitError,
                InternalServerError,
                APIStatusError,
            ) as exc:
                raise LLMUnavailable(
                    f"MaaS unavailable after retries: {exc}"
                ) from exc

            degraded = retried or (want_json and not use_json)
            return self._to_result(resp, degraded=degraded)

        # Only reachable if JSON mode BadRequested and we exhausted json_modes
        # without a successful text attempt (text attempt would have returned).
        raise LLMUnavailable(
            f"MaaS rejected the request: {last_exc}"
        ) from last_exc

    # ── Internals ─────────────────────────────────────────────────────────────

    def _model_for(self, tier: ModelTier) -> str:
        """Resolve the configured model id for *tier* (raises if unset)."""
        model = self._cfg.small_model if tier == ModelTier.SMALL else self._cfg.main_model
        if not model:
            var = "SMALL_MODEL" if tier == ModelTier.SMALL else "MAIN_MODEL"
            raise LLMUnavailable(f"{var} is not configured")
        return model

    def _call_with_retry(self, kwargs: dict):
        """Call the chat endpoint with exponential-backoff retries.

        Returns ``(response, retried)`` where ``retried`` is True when more than
        one attempt was needed (surfaced as ``degraded`` in the result).
        """
        retrying = Retrying(
            stop=stop_after_attempt(_MAX_ATTEMPTS),
            wait=wait_exponential(multiplier=0.5, max=8),
            retry=retry_if_exception(_is_transient),
            reraise=True,
        )
        resp = None
        for attempt in retrying:
            with attempt:
                resp = self._client.chat.completions.create(**kwargs)
        retried = int(retrying.statistics.get("attempt_number", 1)) > 1
        return resp, retried

    @staticmethod
    def _to_result(resp, *, degraded: bool) -> LLMResult:
        """Map an OpenAI ChatCompletion response onto :class:`LLMResult`."""
        try:
            text = resp.choices[0].message.content or ""
        except (IndexError, AttributeError):
            text = ""
        usage = resp.usage.model_dump() if getattr(resp, "usage", None) else {}
        return LLMResult(text=text, raw=resp.model_dump(), usage=usage, degraded=degraded)


# Exported for unit tests that patch/inspect the mapper directly.
_to_result = VngMaasLLM._to_result
