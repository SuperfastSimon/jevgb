"""Goal / approach normalization used for cache keys and retry tracking."""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

# Small EN + NL stopword list; only words that never change task meaning.
STOPWORDS = {
    "a", "an", "the", "please", "pls", "can", "could", "you", "me", "for", "to", "of", "and",
    "now", "again", "just", "kindly", "hey", "hi",
    "de", "het", "een", "graag", "even", "aub", "alsjeblieft", "kun", "kan", "je", "jij",
    "voor", "van", "en", "nu", "weer", "nog",
}


def normalize_text(text: str) -> str:
    text = (text or "").lower()
    text = re.sub(r"[^\w\s./-]", " ", text)
    words = [w for w in text.split() if w not in STOPWORDS]
    return " ".join(words)


def stable_key(*parts: Any) -> str:
    raw = json.dumps(parts, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def goal_key(goal: str, kind: str | None = None) -> str:
    return stable_key("goal", normalize_text(goal), (kind or "").lower())


def error_signature(err: str) -> str:
    """Strip volatile bits (numbers, hex ids, paths with digits) so repeats match."""
    err = (err or "").lower()
    err = re.sub(r"0x[0-9a-f]+|[0-9a-f]{8,}", "<id>", err)
    err = re.sub(r"\d+", "<n>", err)
    return normalize_text(err)[:200]
