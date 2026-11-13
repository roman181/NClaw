"""Conservative local context-budget estimation for the single Llama model."""
from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TokenCheck:
    estimated_tokens: int
    context_window: int
    threshold: float

    @property
    def usage_ratio(self) -> float:
        return self.estimated_tokens / self.context_window

    @property
    def should_handoff(self) -> bool:
        return self.usage_ratio >= self.threshold


class TokenGuard:
    """Estimate prompt size before sending it; this is not Ollama's exact token count."""

    def __init__(self, context_window: int | None = None, threshold: float | None = None) -> None:
        self.context_window = context_window or int(os.getenv("NCLAW_CONTEXT_WINDOW", "8192"))
        self.threshold = threshold if threshold is not None else float(
            os.getenv("NCLAW_TOKEN_THRESHOLD", "0.90")
        )
        if self.context_window < 256:
            raise ValueError("Context window must be at least 256 tokens")
        if not 0.1 <= self.threshold <= 1.0:
            raise ValueError("Token threshold must be between 0.1 and 1.0")

    @staticmethod
    def estimate_tokens(text: str) -> int:
        if not text:
            return 0
        byte_estimate = math.ceil(len(text.encode("utf-8")) / 4)
        lexical_units = re.findall(r"\\w+|[^\\w\\s]", text, flags=re.UNICODE)
        lexical_estimate = math.ceil(len(lexical_units) * 1.3)
        return max(byte_estimate, lexical_estimate)

    def check(self, prompt: str, system: str | None = None) -> TokenCheck:
        combined = f"{system or ''}\\n{prompt}"
        return TokenCheck(
            estimated_tokens=self.estimate_tokens(combined),
            context_window=self.context_window,
            threshold=self.threshold,
        )
