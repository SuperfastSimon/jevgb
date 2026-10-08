"""Token *estimates* for local accounting.

Grok's tokenizer is not public in this package, so every number here is an
estimate. With `tiktoken` installed we count with the `cl100k_base` encoding as
a proxy; otherwise we fall back to ceil(chars / 4). The estimator label is
written into every ledger record so reports never hide which method was used.
"""
from __future__ import annotations

import math
import os
from functools import lru_cache
from typing import Callable

CHARS4 = "chars/4 (rough estimate)"
TIKTOKEN = "tiktoken cl100k_base (proxy estimate, not Grok's tokenizer)"


def _chars4(text: str) -> int:
    return math.ceil(len(text) / 4) if text else 0


@lru_cache(maxsize=4)
def _get_counter(preference: str) -> tuple[Callable[[str], int], str]:
    if preference in ("auto", "tiktoken"):
        try:
            import tiktoken  # type: ignore

            enc = tiktoken.get_encoding("cl100k_base")  # may need a one-time download
            return (lambda t: len(enc.encode(t, disallowed_special=())) if t else 0), TIKTOKEN
        except Exception:
            if preference == "tiktoken":
                raise
    return _chars4, CHARS4


def estimator(preference: str | None = None) -> tuple[Callable[[str], int], str]:
    """Return (count_fn, label). JGB_ESTIMATOR=chars4|tiktoken|auto overrides."""
    pref = (os.environ.get("JGB_ESTIMATOR") or preference or "auto").lower()
    if pref in ("chars4", "chars/4"):
        pref = "chars4"
    return _get_counter(pref)


def count_tokens(text: str, preference: str | None = None) -> int:
    fn, _ = estimator(preference)
    return fn(text or "")


def estimator_label(preference: str | None = None) -> str:
    return estimator(preference)[1]


def cap_text(text: str, max_tokens: int, preference: str | None = None) -> str:
    """Context budget cap: keep head and tail within ~max_tokens, mark the cut."""
    if max_tokens <= 0 or count_tokens(text, preference) <= max_tokens:
        return text
    marker = "\n[... trimmed to fit context budget ...]\n"
    # Work in characters, then shrink until the estimate fits.
    budget_chars = max_tokens * 4
    while budget_chars > 40:
        head = text[: int(budget_chars * 0.6)]
        tail = text[-int(budget_chars * 0.3):]
        out = head + marker + tail
        if count_tokens(out, preference) <= max_tokens:
            return out
        budget_chars = int(budget_chars * 0.85)
    return text[: max_tokens]  # degenerate tiny budgets
