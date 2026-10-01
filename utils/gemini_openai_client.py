"""
Gemini via its OpenAI-compatible endpoint
Role: Use Google Gemini (including the free tier from Google AI Studio) through
the same OpenAI chat-completions code path as DeepSeek. This avoids the
deprecated google-generativeai SDK and retired model names.
"""

from utils.deepseek_client import DeepSeekClient

GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class GeminiOpenAIClient(DeepSeekClient):
    provider_label = "Gemini"
    default_base_url = GEMINI_OPENAI_BASE_URL

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        if not api_key:
            raise ValueError("API key is required for GeminiOpenAIClient")
        super().__init__(api_key=api_key, model_name=model_name)
