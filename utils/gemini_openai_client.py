"""
Gemini via its OpenAI-compatible endpoint
Role: Use Google Gemini (including the free tier from Google AI Studio) through
the same OpenAI chat-completions code path as DeepSeek. This avoids the
deprecated google-generativeai SDK and retired model names.
"""

import os
from typing import Any, Dict, Optional

from utils.deepseek_client import DeepSeekClient

GEMINI_OPENAI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class GeminiOpenAIClient(DeepSeekClient):
    provider_label = "Gemini"
    default_base_url = GEMINI_OPENAI_BASE_URL

    def __init__(self, api_key: str, model_name: str = "gemini-flash-latest"):
        if not api_key:
            raise ValueError("API key is required for GeminiOpenAIClient")
        super().__init__(api_key=api_key, model_name=model_name)
        # Free tier: the main model can be overloaded (503) or rate limited
        # (429); retry once on the lighter model with the same key.
        self.fallback_model = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-flash-lite-latest")

    def generate_content(self, prompt: str, system_instruction: str = "", config: Optional[Dict[str, Any]] = None) -> str:
        try:
            return super().generate_content(prompt, system_instruction, config)
        except Exception as e:
            if not self.fallback_model or self.fallback_model == self.model_name:
                raise
            print(f"⚠️  {self.model_name} failed ({e}); falling back to {self.fallback_model}")
            primary = self.model_name
            self.model_name = self.fallback_model
            try:
                return super().generate_content(prompt, system_instruction, config)
            finally:
                self.model_name = primary
