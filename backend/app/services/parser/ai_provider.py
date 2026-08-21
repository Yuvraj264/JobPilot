from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class AIProvider(ABC):
    """
    Abstract AI Provider Interface for AI-assisted resume parsing and structuring.
    Allows plugging in local LLMs (e.g. Ollama, Llama.cpp) or commercial API providers later.
    """

    @abstractmethod
    def generate_structured_output(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Executes prompt against AI model and returns structured JSON output.
        """
        pass


class LocalMockAIProvider(AIProvider):
    """
    Local Fallback / Offline AI Provider.
    Used when no external AI API key or local LLM server is active.
    Returns safe structured fallback objects.
    """

    def generate_structured_output(self, prompt: str, schema: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "status": "success",
            "provider": "LocalMockAIProvider",
            "message": "AI extraction skipped in local offline mode. Using deterministic extraction results.",
            "data": {}
        }
