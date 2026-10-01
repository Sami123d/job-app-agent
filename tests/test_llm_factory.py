import pytest

from utils.llm_factory import create_llm_client
from utils.deepseek_client import DeepSeekClient
from utils.gemini_client import GeminiClient
from utils.gemini_openai_client import GeminiOpenAIClient, GEMINI_OPENAI_BASE_URL


def test_create_llm_client_defaults_to_deepseek(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")

    client = create_llm_client()

    assert isinstance(client, DeepSeekClient)


def test_create_llm_client_selects_gemini(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")

    client = create_llm_client("gemini")

    assert isinstance(client, GeminiOpenAIClient)
    assert str(client.client.base_url).rstrip("/") == GEMINI_OPENAI_BASE_URL.rstrip("/")
    assert client.model_name == "gemini-flash-latest"


def test_gemini_accepts_gemini_api_key_and_model_override(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "fake-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-flash-lite-latest")

    client = create_llm_client("gemini")

    assert client.model_name == "gemini-flash-lite-latest"


def test_create_llm_client_selects_legacy_gemini_sdk(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")

    client = create_llm_client("gemini-sdk")

    assert isinstance(client, GeminiClient)


def test_create_llm_client_raises_when_key_missing(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        create_llm_client("deepseek")


def test_create_llm_client_raises_on_unsupported_provider():
    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        create_llm_client("openai")
