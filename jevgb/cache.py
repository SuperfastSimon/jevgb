"""Artifact cache with TTL, keyed on the normalized goal (+ optional kind).

An artifact is the *result* of expensive work (research brief, scraped table,
build result). Reusing it costs the tokens to read it; redoing the work costs
whatever it cost the first time. We store that production cost (when the caller
knows it) so the ledger can compare the two honestly.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from jevgb.normalize import goal_key, normalize_text
from jevgb.store import JsonStore
from jevgb.tokens import count_tokens


class ArtifactCache:
    def __init__(self, path: Path, ttl_minutes: float = 120, max_entries: int = 200):
        self.store = JsonStore(path)
        self.ttl_s = float(ttl_minutes) * 60
        self.max_entries = int(max_entries)

    def put(self, goal: str, content: str, *, kind: str | None = None,
            cost_tokens: int | None = None, note: str = "", now: float | None = None) -> dict[str, Any]:
        now = time.time() if now is None else now
        data = self._prune(self.store.load(), now)
        entry = {
            "goal_norm": normalize_text(goal),
            "kind": kind or "",
            "content": content,
            "note": note,
            "created": now,
            "content_tokens": count_tokens(content),
            # None = unknown; the ledger then falls back to content size as a lower bound.
            "cost_tokens": int(cost_tokens) if cost_tokens is not None else None,
        }
        data[goal_key(goal, kind)] = entry
        if len(data) > self.max_entries:
            for k in sorted(data, key=lambda k: data[k]["created"])[: len(data) - self.max_entries]:
                del data[k]
        self.store.save(data)
        return entry

    def get(self, goal: str, *, kind: str | None = None, now: float | None = None) -> dict[str, Any] | None:
        now = time.time() if now is None else now
        entry = self.store.load().get(goal_key(goal, kind))
        if not entry or now - float(entry.get("created", 0)) > self.ttl_s:
            return None
        out = dict(entry)
        out["age_minutes"] = round((now - entry["created"]) / 60, 1)
        return out

    def _prune(self, data: dict[str, Any], now: float) -> dict[str, Any]:
        return {k: v for k, v in data.items() if now - float(v.get("created", 0)) <= self.ttl_s}
