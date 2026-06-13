from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from openai import APIConnectionError, BadRequestError, RateLimitError

from app.adapters.maas_llm import VngMaasLLM, _is_transient
from app.config import Settings
from app.ports.errors import LLMUnavailable
from app.ports.types import LLMResult, ModelTier


def _chat_response(text: str = "hello", **usage) -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
        usage=SimpleNamespace(model_dump=lambda: usage or {"total_tokens": 10}),
        model_dump=lambda: {"id": "chatcmpl-test", "choices": [{"message": {"content": text}}]},
    )


@pytest.fixture
def llm_settings() -> Settings:
    return Settings(
        llm_api_key="test-key",
        small_model="small-model",
        main_model="main-model",
        llm_base_url="https://maas.example/v1",
        log_level="error",
    )


@pytest.fixture
def maas_llm(llm_settings: Settings) -> VngMaasLLM:
    return VngMaasLLM(llm_settings)


def _api_error(cls, message: str, status_code: int):
    response = MagicMock()
    response.status_code = status_code
    return cls(message, response=response, body=None)


def test_is_transient_recognises_retryable_errors() -> None:
    assert _is_transient(_api_error(RateLimitError, "rate", 429))
    assert _is_transient(APIConnectionError(request=MagicMock()))
    assert not _is_transient(_api_error(BadRequestError, "bad", 400))


def test_to_result_parses_text_and_usage() -> None:
    resp = _chat_response("parsed text", prompt_tokens=3, completion_tokens=5)
    result = VngMaasLLM._to_result(resp, degraded=False)

    assert isinstance(result, LLMResult)
    assert result.text == "parsed text"
    assert result.usage == {"prompt_tokens": 3, "completion_tokens": 5}
    assert result.degraded is False
    assert result.raw["id"] == "chatcmpl-test"


def test_complete_returns_parsed_result(maas_llm: VngMaasLLM) -> None:
    maas_llm._client = MagicMock()
    maas_llm._client.chat.completions.create.return_value = _chat_response(
        '{"intent": "question"}',
        prompt_tokens=1,
        completion_tokens=2,
    )

    result = maas_llm.complete(
        tier=ModelTier.SMALL,
        messages=[{"role": "user", "content": "hi"}],
        temperature=0.0,
    )

    assert result.text == '{"intent": "question"}'
    maas_llm._client.chat.completions.create.assert_called_once()
    call_kwargs = maas_llm._client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "small-model"
    assert call_kwargs["messages"] == [{"role": "user", "content": "hi"}]


def test_complete_raises_when_api_key_missing() -> None:
    llm = VngMaasLLM(Settings(llm_api_key="", small_model="s", main_model="m", log_level="error"))

    with pytest.raises(LLMUnavailable, match="API key"):
        llm.complete(tier=ModelTier.SMALL, messages=[])


def test_complete_uses_greennode_api_key_on_agentbase() -> None:
    settings = Settings(
        app_env="agentbase",
        llm_api_key="",
        greennode_api_key="platform-key",
        small_model="s",
        main_model="m",
        log_level="error",
    )
    llm = VngMaasLLM(settings)
    llm._client = MagicMock()
    llm._client.chat.completions.create.return_value = _chat_response("ok")

    result = llm.complete(tier=ModelTier.SMALL, messages=[{"role": "user", "content": "hi"}])

    assert result.text == "ok"
    llm._client.chat.completions.create.assert_called_once()


def test_complete_raises_when_model_unconfigured(llm_settings: Settings) -> None:
    llm = VngMaasLLM(llm_settings.model_copy(update={"small_model": ""}))

    with pytest.raises(LLMUnavailable, match="SMALL_MODEL"):
        llm.complete(tier=ModelTier.SMALL, messages=[])


def test_complete_json_mode_falls_back_on_bad_request(maas_llm: VngMaasLLM) -> None:
    maas_llm._client = MagicMock()
    bad_response = MagicMock()
    bad_response.status_code = 400
    maas_llm._client.chat.completions.create.side_effect = [
        BadRequestError("json unsupported", response=bad_response, body=None),
        _chat_response('{"ok": true}'),
    ]

    result = maas_llm.complete(
        tier=ModelTier.MAIN,
        messages=[{"role": "user", "content": "json please"}],
        response_format="json",
    )

    assert result.text == '{"ok": true}'
    assert result.degraded is True
    assert maas_llm._client.chat.completions.create.call_count == 2
    first_kwargs = maas_llm._client.chat.completions.create.call_args_list[0].kwargs
    second_kwargs = maas_llm._client.chat.completions.create.call_args_list[1].kwargs
    assert first_kwargs["response_format"] == {"type": "json_object"}
    assert "response_format" not in second_kwargs


def test_complete_raises_llm_unavailable_after_transient_exhaustion(maas_llm: VngMaasLLM) -> None:
    maas_llm._client = MagicMock()
    maas_llm._client.chat.completions.create.side_effect = RateLimitError(
        "rate", response=MagicMock(), body=None
    )

    with patch("app.adapters.maas_llm._MAX_ATTEMPTS", 1):
        with pytest.raises(LLMUnavailable, match="unavailable after retries"):
            maas_llm.complete(tier=ModelTier.SMALL, messages=[{"role": "user", "content": "x"}])


def test_complete_applies_default_timeout_when_unset(maas_llm: VngMaasLLM) -> None:
    maas_llm._client = MagicMock()
    maas_llm._client.chat.completions.create.return_value = _chat_response("ok")

    maas_llm.complete(tier=ModelTier.SMALL, messages=[{"role": "user", "content": "hi"}])

    call_kwargs = maas_llm._client.chat.completions.create.call_args.kwargs
    assert call_kwargs["timeout"] == maas_llm._cfg.llm_request_timeout_s


def test_complete_honours_explicit_timeout_override(maas_llm: VngMaasLLM) -> None:
    maas_llm._client = MagicMock()
    maas_llm._client.chat.completions.create.return_value = _chat_response("ok")

    maas_llm.complete(
        tier=ModelTier.SMALL,
        messages=[{"role": "user", "content": "hi"}],
        timeout_s=12.5,
    )

    call_kwargs = maas_llm._client.chat.completions.create.call_args.kwargs
    assert call_kwargs["timeout"] == 12.5


def test_is_reachable_true_when_models_list_succeeds(maas_llm: VngMaasLLM) -> None:
    maas_llm._client = MagicMock()
    maas_llm._client.models.list.return_value = MagicMock()

    assert maas_llm.is_reachable(timeout_s=1.0) is True
    maas_llm._client.models.list.assert_called_once_with(timeout=1.0)


def test_is_reachable_false_without_api_key() -> None:
    llm = VngMaasLLM(Settings(llm_api_key="", small_model="s", main_model="m", log_level="error"))
    assert llm.is_reachable() is False


def test_is_reachable_false_on_client_error(maas_llm: VngMaasLLM) -> None:
    maas_llm._client = MagicMock()
    maas_llm._client.models.list.side_effect = APIConnectionError(request=MagicMock())

    assert maas_llm.is_reachable(timeout_s=1.0) is False


def test_complete_raises_llm_unavailable_on_api_timeout(maas_llm: VngMaasLLM) -> None:
    from openai import APITimeoutError

    maas_llm._client = MagicMock()
    maas_llm._client.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())

    with patch("app.adapters.maas_llm._MAX_ATTEMPTS", 1):
        with pytest.raises(LLMUnavailable, match="unavailable after retries"):
            maas_llm.complete(
                tier=ModelTier.SMALL,
                messages=[{"role": "user", "content": "slow"}],
            )
