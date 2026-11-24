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
    def _is_cjk(character: str) -> bool:
        codepoint = ord(character)
        return (
            0x2E80 <= codepoint <= 0x2FFF
            or 0x3000 <= codepoint <= 0x30FF
            or 0x3100 <= codepoint <= 0x31FF
            or 0x3400 <= codepoint <= 0x4DBF
            or 0x4E00 <= codepoint <= 0x9FFF
            or 0xA960 <= codepoint <= 0xA97F
            or 0xAC00 <= codepoint <= 0xD7AF
            or 0xF900 <= codepoint <= 0xFAFF
            or 0xFF00 <= codepoint <= 0xFFEF
            or 0x20000 <= codepoint <= 0x3134F
        )

    @staticmethod
    def estimate_tokens(text: str) -> int:
        if not text:
            return 0

        cjk_characters = sum(TokenGuard._is_cjk(character) for character in text)
        non_cjk = "".join(character for character in text if not TokenGuard._is_cjk(character))
        byte_estimate = math.ceil(len(non_cjk.encode("utf-8")) / 4)
        lexical_units = re.findall(r"\w+|[^\w\s]", non_cjk, flags=re.UNICODE)
        lexical_estimate = math.ceil(len(lexical_units) * 1.3)
        non_cjk_estimate = max(byte_estimate, lexical_estimate)

        # CJK text often has no whitespace boundaries. Budget at least 1.5
        # estimated tokens per CJK code point rather than one per whole run.
        cjk_estimate = math.ceil(cjk_characters * 1.5)
        return non_cjk_estimate + cjk_estimate

    def check(self, prompt: str, system: str | None = None) -> TokenCheck:
        combined = f"{system or ''}\n{prompt}"
        return TokenCheck(
            estimated_tokens=self.estimate_tokens(combined),
            context_window=self.context_window,
            threshold=self.threshold,
        )
