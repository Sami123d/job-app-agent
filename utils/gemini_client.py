"""
Gemini API Client Wrapper
Role: Handle all interactions with Google Gemini API with robust error handling and retry logic.
"""

from typing import Dict, Any, Optional
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.llm_client import LLMClient


class GeminiClient(LLMClient):
    """
    Wrapper for Google Gemini API to handle configuration, generation, and error handling.
    """

    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash"):
        """
        Initialize the Gemini client.

        Args:
            api_key: Google API Key
            model_name: Model version to use (default: gemini-1.5-flash)
        """
        if not api_key:
            raise ValueError("API key is required for GeminiClient")

        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.api_key = api_key
        # Gemini takes the system instruction at model-construction time rather
        # than per-call, so we lazily (re)build the model whenever the caller
        # passes a different system_instruction — this keeps generate_content's
        # signature identical to every other LLMClient implementation.
        self._current_system_instruction = None
        self.model = genai.GenerativeModel(model_name)

    def _json_generation_config(self, temperature: float):
        return {"temperature": temperature, "response_mime_type": "application/json"}

    def _get_model(self, system_instruction: str):
        if system_instruction != self._current_system_instruction:
            self.model = genai.GenerativeModel(
                self.model_name,
                system_instruction=system_instruction or None,
            )
            self._current_system_instruction = system_instruction
        return self.model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def generate_content(self, prompt: str, system_instruction: str = "", config: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate text content from Gemini with retry logic.

        Args:
            prompt: The input prompt string
            system_instruction: System prompt/role definition
            config: Optional generation config (temperature, tokens, etc.)

        Returns:
            Generated text string

        Raises:
            google_exceptions.ResourceExhausted: If rate limit exceeded
            ValueError: If generation fails
        """
        try:
            print(f"🤖 Calling Gemini ({self.model_name})...")
            generation_config = config or {"temperature": 0.7}
            model = self._get_model(system_instruction)

            response = model.generate_content(
                prompt,
                generation_config=generation_config
            )
            return response.text

        except google_exceptions.ResourceExhausted:
            print("⚠️  Rate limit exceeded. Retrying...")
            raise
        except Exception as e:
            print(f"❌ Gemini API Error: {e}")
            raise
