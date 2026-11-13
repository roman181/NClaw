"""Bounded, private-network-only Ollama chat client."""
from __future__ import annotations

import ipaddress
import math
import os
from urllib.parse import urlsplit, urlunsplit

import httpx

MAX_PROMPT_CHARS = 16_000
MAX_SYSTEM_CHARS = 4_000
MAX_MODEL_CHARS = 120
MAX_RESPONSE_BYTES = 65_536


class OllamaError(RuntimeError):
    """Raised when Ollama cannot complete a request safely."""


def _validated_host(host: str) -> str:
    try:
        parsed = urlsplit(host)
        hostname = parsed.hostname
        if (
            parsed.scheme not in {"http", "https"}
            or not hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in {"", "/"}
        ):
            raise ValueError
        try:
            address = ipaddress.ip_address(hostname)
            allowed = address.is_private or address.is_loopback
        except ValueError:
            allowed = hostname.lower() == "localhost" or hostname.lower().endswith(".local")
        if not allowed:
            raise ValueError
        port = parsed.port
        if port is not None and not 1 <= port <= 65535:
            raise ValueError
        return urlunsplit((parsed.scheme, parsed.netloc, "", "", "")).rstrip("/")
    except ValueError as exc:
        raise ValueError(
            "Ollama host must be a private IP, localhost, or .local hostname without credentials"
        ) from exc


class OllamaClient:
    """Call only an explicitly configured private Ollama endpoint."""

    def __init__(
        self,
        host: str | None = None,
        timeout: float = 60.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.host = _validated_host(
            (host or os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")).strip()
        )
        if not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or not 0.1 <= timeout <= 120:
            raise ValueError("Ollama timeout must be between 0.1 and 120 seconds")
        self.timeout = float(timeout)
        self.transport = transport

    def chat(self, model: str, prompt: str, system: str | None = None) -> str:
        if not isinstance(model, str) or not model.strip() or len(model) > MAX_MODEL_CHARS:
            raise ValueError("Model name must contain 1 to 120 characters")
        if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > MAX_PROMPT_CHARS:
            raise ValueError("Prompt must contain 1 to 16000 characters")
        if system is not None and (not isinstance(system, str) or len(system) > MAX_SYSTEM_CHARS):
            raise ValueError("System instruction must not exceed 4000 characters")

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            with httpx.Client(
                timeout=self.timeout,
                transport=self.transport,
                follow_redirects=False,
            ) as client:
                with client.stream(
                    "POST",
                    f"{self.host}/api/chat",
                    json={"model": model, "messages": messages, "stream": False},
                ) as response:
                    response.raise_for_status()
                    chunks = []
                    response_size = 0
                    for chunk in response.iter_bytes():
                        response_size += len(chunk)
                        if response_size > MAX_RESPONSE_BYTES:
                            raise OllamaError("Ollama response exceeds the 64 KiB limit")
                        chunks.append(chunk)
                payload = httpx.Response(200, content=b"".join(chunks)).json()
        except OllamaError:
            raise
        except (httpx.HTTPError, ValueError) as exc:
            raise OllamaError("Ollama request failed or returned invalid JSON") from exc

        content = payload.get("message", {}).get("content") if isinstance(payload, dict) else None
        if not isinstance(content, str):
            raise OllamaError("Ollama returned no message content")
        if len(content.encode("utf-8")) > MAX_RESPONSE_BYTES:
            raise OllamaError("Ollama message exceeds the 64 KiB limit")
        return content
