"""Deterministic guards that make savings structurally likely.

- RetryTracker: stop after N failures of the *same approach* with the *same error*.
- ToolCallDeduper: flag a repeated identical tool call inside a TTL and point to
  the earlier result instead of re-running and re-reading it.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from jevgb.normalize import error_signature, normalize_text, stable_key
from jevgb.store import JsonStore
from jevgb.tokens import count_tokens


class RetryTracker:
    def __init__(self, path: Path, max_failures: int = 2, window_minutes: float = 240):
        self.store = JsonStore(path)
        self.max_failures = int(max_failures)
        self.window_s = float(window_minutes) * 60

    def _key(self, goal: str, approach: str, error: str) -> str:
        return stable_key("retry", normalize_text(goal), normalize_text(approach), error_signature(error))

    def record_failure(self, goal: str, approach: str, error: str, *,
                       attempt_tokens: int | None = None, now: float | None = None) -> dict[str, Any]:
        now = time.time() if now is None else now
        data = {k: v for k, v in self.store.load().items() if now - v.get("last", 0) <= self.window_s}
        key = self._key(goal, approach, error)
        e = data.get(key, {"count": 0, "first": now, "attempt_tokens": []})
        e["count"] += 1
        e["last"] = now
        if attempt_tokens:
            e["attempt_tokens"] = (e.get("attempt_tokens") or [])[-4:] + [int(attempt_tokens)]
        data[key] = e
        self.store.save(data)
        return self.status(goal, approach, error, now=now, _data=data)

    def status(self, goal: str, approach: str, error: str, *, now: float | None = None,
               _data: dict[str, Any] | None = None) -> dict[str, Any]:
        now = time.time() if now is None else now
        data = _data if _data is not None else self.store.load()
        e = data.get(self._key(goal, approach, error))
        count = e["count"] if e and now - e.get("last", 0) <= self.window_s else 0
        toks = (e or {}).get("attempt_tokens") or []
        return {
            "same_approach_failures": count,
            "max_failures": self.max_failures,
            "stop": count >= self.max_failures,
            "avg_attempt_tokens": int(sum(toks) / len(toks)) if toks else None,
        }

    def reset(self, goal: str, approach: str, error: str) -> None:
        data = self.store.load()
        data.pop(self._key(goal, approach, error), None)
        self.store.save(data)


class ToolCallDeduper:
    def __init__(self, path: Path, ttl_minutes: float = 30):
        self.store = JsonStore(path)
        self.ttl_s = float(ttl_minutes) * 60

    @staticmethod
    def _key(tool: str, args: Any) -> str:
        return stable_key("tool", tool, args)

    def check(self, tool: str, args: Any, *, now: float | None = None) -> dict[str, Any]:
        now = time.time() if now is None else now
        e = self.store.load().get(self._key(tool, args))
        if e and now - e["ts"] <= self.ttl_s:
            return {"duplicate": True, "age_minutes": round((now - e["ts"]) / 60, 1),
                    "result_ref": e.get("result_ref", ""), "result_tokens": e.get("result_tokens", 0),
                    "preview": e.get("preview", "")}
        return {"duplicate": False}

    def store_result(self, tool: str, args: Any, result: str, *, result_ref: str = "",
                     now: float | None = None) -> None:
        now = time.time() if now is None else now
        data = {k: v for k, v in self.store.load().items() if now - v["ts"] <= self.ttl_s}
        data[self._key(tool, args)] = {
            "ts": now, "result_ref": result_ref, "result_tokens": count_tokens(result),
            "preview": (result or "")[:200],
        }
        self.store.save(data)
