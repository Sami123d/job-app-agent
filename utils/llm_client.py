"""
LLM Client Abstraction
Role: Define a provider-agnostic interface for text/JSON generation so agents
don't depend on a specific LLM vendor (DeepSeek, Gemini, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import json


class LLMClient(ABC):
    """
    Abstract base class all LLM provider clients must implement.

    Subclasses only need to implement `generate_content`; JSON generation
    and response parsing are shared here so every provider behaves
    identically from the caller's point of view.
    """

    @abstractmethod
    def generate_content(
        self,
        prompt: str,
        system_instruction: str = "",
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate raw text content from the model."""
        raise NotImplementedError

    def generate_json(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Generate and parse JSON content.

        Args:
            prompt: Input prompt requesting JSON
            system_instruction: System role
            temperature: Lower temperature for structured data (default 0.0)

        Returns:
            Parsed JSON dictionary
        """
        config = self._json_generation_config(temperature)

        if "JSON" not in prompt:
            prompt += "\n\nReturn the result as a valid JSON object."
        if system_instruction and "JSON" not in system_instruction:
            system_instruction += "\nProvide output in JSON format."

        response_text = self.generate_content(prompt, system_instruction, config)
        return self._parse_json_safe(response_text)

    def _json_generation_config(self, temperature: float) -> Dict[str, Any]:
        """
        Base generation config used for `generate_json`. Providers that support
        stronger structured-output guarantees (e.g. Gemini's response_mime_type)
        can override this to opt in without changing the shared interface.
        """
        return {"temperature": temperature}

    @staticmethod
    def _parse_json_safe(text: str) -> Dict[str, Any]:
        """
        Safely parse a JSON string, handling Markdown fences and common errors.

        Args:
            text: Raw string from LLM

        Returns:
            Parsed dictionary
        """
        try:
            cleaned = text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            print(f"❌ JSON Decode Error: {e}")
            print(f"Raw text start: {text[:100]}")
            try:
                start = text.find("{")
                end = text.rfind("}") + 1
                if start != -1 and end != -1:
                    return json.loads(text[start:end])
            except Exception:
                pass
            raise ValueError(f"Invalid JSON response: {e}")
