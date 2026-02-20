from __future__ import annotations

from app.config import settings


class LLMProvider:
    def __init__(self) -> None:
        self.enabled = bool(settings.llm_api_key)

    def chat(self, prompt: str) -> str:
        if not self.enabled:
            return "LLM provider is disabled. Set LLM_API_KEY to enable."
        return f"Stub response for: {prompt[:100]}"
