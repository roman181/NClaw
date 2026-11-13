"""Single-model Llama integration through Ollama."""
from __future__ import annotations

import os

from models.ollama import OllamaClient


class LlamaModel:
    def __init__(self, client: OllamaClient | None = None, model: str | None = None) -> None:
        self.client = client or OllamaClient()
        self.model = model or os.getenv("MODEL_NAME", "llama3.2")

    def generate(self, prompt: str, system: str | None = None) -> str:
        return self.client.chat(self.model, prompt, system=system)
