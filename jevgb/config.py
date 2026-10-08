from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config.yaml"
EXAMPLE_PATH = ROOT / "config.example.yaml"

DEFAULTS: dict[str, Any] = {
    "enabled": True,
    "mode": "shadow",            # shadow | active
    "classifier": "auto",        # auto | jev | local  (auto = Jev only if TYPESAFE_API_KEY is set)
    "model": "jev-latest",
    "thresholds": {"min_choice_confidence": 0.55, "reuse_min": 0.65, "subagent_min": 0.75},
    "limits": {"max_browser_sources": 5, "max_retries_same_error": 1, "max_tokens_per_source": 1500},
    "budgets": {"max_context_tokens": 4000},
    "handoff": {"enabled": True, "max_brief_tokens": 1200, "max_summary_tokens": 500, "out_dir": "handoffs"},
    "cache": {"path": ".state/artifacts.json", "ttl_minutes": 120, "max_entries": 200},
    "retry": {"path": ".state/retries.json", "max_same_approach_failures": 2, "window_minutes": 240},
    "dedupe": {"path": ".state/toolcalls.json", "ttl_minutes": 30},
    "tokens": {"log_path": "logs/tokens.jsonl", "estimator": "auto"},
    "logging": {"path": "logs/runs.jsonl"},
}


def _merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def load_config(path: str | Path | None = None, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    path = Path(path or os.environ.get("JGB_CONFIG") or (CONFIG_PATH if CONFIG_PATH.exists() else EXAMPLE_PATH))
    data = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    cfg = _merge(DEFAULTS, data or {})
    cfg = _merge(cfg, overrides or {})
    cfg["_home"] = str(Path(os.environ.get("JGB_HOME") or cfg.get("home") or ROOT))
    return cfg


def resolve(cfg: dict[str, Any], rel: str) -> Path:
    p = Path(rel)
    if not p.is_absolute():
        p = Path(cfg.get("_home") or ROOT) / p
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def resolve_log_path(cfg: dict[str, Any]) -> Path:
    return resolve(cfg, cfg["logging"]["path"])
