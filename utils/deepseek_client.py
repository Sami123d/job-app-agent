"""
DeepSeek API Client Wrapper
Role: Handle all interactions with DeepSeek API via OpenAI client with robust error handling.
"""

import os
from typing import Dict, Any, Optional
from openai import OpenAI, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.llm_client import LLMClient


class DeepSeekClient(LLMClient):
    """
    Wrapper for DeepSeek API (OpenAI-compatible) to handle configuration, generation, and error handling.
    """

    provider_label = "DeepSeek"
    default_base_url = "https://api.deepseek.com"

    def __init__(self, api_key: str, model_name: str = "deepseek-chat", base_url: Optional[str] = None):
        """
        Initialize the DeepSeek client.

        Args:
            api_key: DeepSeek API Key
            model_name: Model version to use (default: deepseek-chat)
        """
        if not api_key:
            raise ValueError("API key is required for DeepSeekClient")

        # Bound each request: the SDK default (600s timeout + 2 retries) can
        # leave the UI hanging for minutes when the provider is overloaded.
        # Retries are handled by tenacity below.
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url or self.default_base_url,
            timeout=float(os.getenv("LLM_TIMEOUT", "60")),
            max_retries=0,
        )
        self.model_name = model_name

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=6),
        reraise=True,
    )
    def generate_content(self, prompt: str, system_instruction: str = "", config: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate text content from DeepSeek with retry logic.

        Args:
            prompt: The input prompt string
            system_instruction: System prompt/role definition
            config: Optional generation config (temperature, etc.)

        Returns:
            Generated text string
        """
        try:
            print(f"🤖 Calling {self.provider_label} ({self.model_name})...")
            temperature = config.get("temperature", 0.7) if config else 0.7

            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                stream=False
            )
            return response.choices[0].message.content

        except RateLimitError:
            print("⚠️  Rate limit exceeded. Retrying...")
            raise
        except Exception as e:
            print(f"❌ {self.provider_label} API Error: {e}")
            raise
