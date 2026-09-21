import pytest

from utils.llm_factory import create_llm_client
from utils.deepseek_client import DeepSeekClient
from utils.gemini_client import GeminiClient


def test_create_llm_client_defaults_to_deepseek(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake-key")

    client = create_llm_client()

    assert isinstance(client, DeepSeekClient)


def test_create_llm_client_selects_gemini(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-key")

    client = create_llm_client("gemini")

    assert isinstance(client, GeminiClient)


def test_create_llm_client_raises_when_key_missing(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        create_llm_client("deepseek")


def test_create_llm_client_raises_on_unsupported_provider():
    with pytest.raises(ValueError, match="Unsupported LLM_PROVIDER"):
        create_llm_client("openai")
