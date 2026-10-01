"""
LLM Factory
Role: Construct the configured LLMClient implementation from environment
variables, so callers never need to know which provider is in use.
"""

import os

from utils.llm_client import LLMClient
from utils.deepseek_client import DeepSeekClient
from utils.gemini_client import GeminiClient
from utils.gemini_openai_client import GeminiOpenAIClient

SUPPORTED_PROVIDERS = ("deepseek", "gemini", "gemini-sdk")


def create_llm_client(provider: str = None) -> LLMClient:
    """
    Build an LLMClient for the configured provider.

    Args:
        provider: Explicit provider name ("deepseek" or "gemini"). If omitted,
            read from the LLM_PROVIDER environment variable, defaulting to
            "deepseek". "gemini" uses Gemini's OpenAI-compatible endpoint;
            "gemini-sdk" uses the legacy google-generativeai SDK.

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

    if provider in ("gemini", "gemini-sdk"):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY (or GOOGLE_API_KEY) not found in environment variables")
        model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
        if provider == "gemini-sdk":
            # Legacy path through the google-generativeai SDK
            return GeminiClient(api_key=api_key, model_name=model)
        # Default: Gemini's OpenAI-compatible endpoint
        return GeminiOpenAIClient(api_key=api_key, model_name=model)

    raise ValueError(
        f"Unsupported LLM_PROVIDER '{provider}'. Supported providers: {', '.join(SUPPORTED_PROVIDERS)}"
    )
