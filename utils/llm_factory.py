"""
LLM Factory
Role: Construct the configured LLMClient implementation from environment
variables, so callers never need to know which provider is in use.
"""

import os

from utils.llm_client import LLMClient
from utils.deepseek_client import DeepSeekClient
from utils.gemini_client import GeminiClient

SUPPORTED_PROVIDERS = ("deepseek", "gemini")


def create_llm_client(provider: str = None) -> LLMClient:
    """
    Build an LLMClient for the configured provider.

    Args:
        provider: Explicit provider name ("deepseek" or "gemini"). If omitted,
            read from the LLM_PROVIDER environment variable, defaulting to
            "deepseek".

    Returns:
        A concrete LLMClient instance.

    Raises:
        ValueError: If the provider is unsupported or its API key is missing.
    """
    provider = (provider or os.getenv("LLM_PROVIDER", "deepseek")).strip().lower()

    if provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables")
        return DeepSeekClient(api_key=api_key)

    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        return GeminiClient(api_key=api_key)

    raise ValueError(
        f"Unsupported LLM_PROVIDER '{provider}'. Supported providers: {', '.join(SUPPORTED_PROVIDERS)}"
    )
