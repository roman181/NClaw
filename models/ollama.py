"""Minimal synchronous client for the Ollama chat API."""
from __future__ import annotations

import os

import httpx


class OllamaError(RuntimeError):
    """Raised when Ollama cannot complete a request."""


class OllamaClient:
    def __init__(
        self,
        host: str | None = None,
        timeout: float = 120.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.host = (host or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")).rstrip("/")
        self.timeout = timeout
        self.transport = transport

    def chat(self, model: str, prompt: str, system: str | None = None) -> str:
        if not model.strip():
            raise ValueError("Model name must not be empty")
        if not prompt.strip():
            raise ValueError("Prompt must not be empty")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            with httpx.Client(timeout=self.timeout, transport=self.transport) as client:
                response = client.post(
                    f"{self.host}/api/chat",
                    json={"model": model, "messages": messages, "stream": False},
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise OllamaError(f"Ollama request failed: {exc}") from exc

        content = payload.get("message", {}).get("content")
        if not isinstance(content, str):
            raise OllamaError("Ollama returned no message content")
        return content
