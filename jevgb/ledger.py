"""Token ledger: per-task baseline vs actual, appended as JSONL, plus a report.

baseline = estimated tokens Grok Bot would have spent/sent on the default path
           (e.g. forwarding the full chat to Grok Build, redoing cached work).
actual   = estimated tokens on the routed path (compact brief, reading the
           cached artifact, capped research).
overhead = estimated tokens Grok Bot spends on the router itself (writing the
           state, reading the decision). It is subtracted, so net can be negative.

Every record carries `estimator` and `baseline_basis` so a reader can judge how
solid each number is. Nothing here is hardcoded: all numbers come from counting
real text (or caller-supplied counts, flagged as such).
"""
from __future__ import annotations

import json
import statistics
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from jevgb.tokens import estimator_label


def new_task_id() -> str:
    return "t-" + uuid.uuid4().hex[:10]


def record(path: Path, *, task_id: str, action: str, baseline_tokens: int | None, actual_tokens: int,
           overhead_tokens: int = 0, baseline_basis: str, goal: str = "", simulated: bool = False,
           extra: dict[str, Any] | None = None) -> dict[str, Any]:
    rec: dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "task_id": task_id,
        "action": action,
        "goal": (goal or "")[:160],
        "baseline_tokens": baseline_tokens,
        "actual_tokens": int(actual_tokens),
        "overhead_tokens": int(overhead_tokens),
        "net_saved_tokens": (int(baseline_tokens) - int(actual_tokens) - int(overhead_tokens))
        if baseline_tokens is not None else None,
        "baseline_basis": baseline_basis,
        "estimator": estimator_label(),
        "simulated": bool(simulated),
    }
    if extra:
        rec["extra"] = extra
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def read(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    recs, errors = [], []
    if not path.exists():
        return recs, [f"log not found: {path}"]
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            recs.append(json.loads(line))
        except json.JSONDecodeError:
            errors.append(f"line {i}: invalid JSON skipped")
    return recs, errors


def basis_quality(basis: str) -> str:
    """measured = counted from real text; estimate = formula/assumption; caller = unverified number."""
    b = (basis or "").lower()
    if b.startswith("not_measurable"):
        return "none"
    if b.startswith("caller"):
        return "caller"
    if "estimate" in b or "lower bound" in b or b.startswith("goal_only"):
        return "estimate" if "estimate" in b else "measured"
    return "measured"


def summarize(recs: Iterable[dict[str, Any]]) -> dict[str, Any]:
    recs = list(recs)
    measured = [r for r in recs if r.get("baseline_tokens") is not None]
    by_action: dict[str, dict[str, Any]] = defaultdict(lambda: {"tasks": 0, "baseline": 0, "actual": 0,
                                                                "overhead": 0, "net_saved": 0, "unmeasured": 0})
    for r in recs:
        a = by_action[r.get("action", "?")]
        a["tasks"] += 1
        a["overhead"] += int(r.get("overhead_tokens") or 0)
        if r.get("baseline_tokens") is None:
            a["unmeasured"] += 1
            a["actual"] += int(r.get("actual_tokens") or 0)
            a["net_saved"] -= int(r.get("overhead_tokens") or 0)
            continue
        a["baseline"] += int(r["baseline_tokens"])
        a["actual"] += int(r["actual_tokens"])
        a["net_saved"] += int(r["net_saved_tokens"])
    tb = sum(int(r["baseline_tokens"]) for r in measured)
    ta = sum(int(r["actual_tokens"]) for r in measured)
    to = sum(int(r.get("overhead_tokens") or 0) for r in recs)
    net = tb - ta - to
    nets = [int(r["net_saved_tokens"]) for r in measured]
    by_quality: dict[str, int] = defaultdict(int)
    for r in measured:
        by_quality[basis_quality(r.get("baseline_basis", ""))] += int(r["net_saved_tokens"])
    return {
        "tasks": len(recs),
        "net_saved_by_basis_quality": dict(sorted(by_quality.items())),
        "measured_tasks": len(measured),
        "baseline_tokens": tb,
        "actual_tokens": ta,
        "overhead_tokens": to,
        "net_saved_tokens": net,
        "net_saved_pct": round(100 * net / tb, 1) if tb else None,
        "median_net_saved_per_task": int(statistics.median(nets)) if nets else None,
        "tasks_with_negative_net": sum(1 for n in nets if n < 0),
        "by_action": dict(sorted(by_action.items())),
        "estimators": sorted({r.get("estimator", "?") for r in recs}),
        "baseline_bases": sorted({r.get("baseline_basis", "?") for r in recs}),
        "simulated_records": sum(1 for r in recs if r.get("simulated")),
    }


def format_report(s: dict[str, Any], errors: list[str] | None = None) -> str:
    out = []
    if s["simulated_records"]:
        out.append(f"*** SIMULATED DATA: {s['simulated_records']} of {s['tasks']} records are simulated examples, "
                   "not real usage. ***")
    out.append("JevGB token report (all numbers are ESTIMATES)")
    out.append(f"estimator: {', '.join(s['estimators']) or '-'}")
    if not s["tasks"]:
        out.append("No records yet. Route some tasks first (jevgb route ...).")
        return "\n".join(out + [f"warning: {e}" for e in errors or []])
    pct = f"{s['net_saved_pct']}%" if s["net_saved_pct"] is not None else "n/a"
    out += [
        f"tasks: {s['tasks']} (with measurable baseline: {s['measured_tasks']})",
        f"baseline tokens: {s['baseline_tokens']:,}",
        f"actual tokens:   {s['actual_tokens']:,}",
        f"router overhead: {s['overhead_tokens']:,}",
        f"net saved:       {s['net_saved_tokens']:,} ({pct} of baseline)",
        f"median net saved per measured task: {s['median_net_saved_per_task']}",
        f"tasks where routing cost more than it saved: {s['tasks_with_negative_net']}",
        "",
        "net saved by baseline quality (overhead of unmeasured tasks not included here): "
        + ", ".join(f"{k}={v:,}" for k, v in s["net_saved_by_basis_quality"].items()),
        "",
        f"{'action':<22}{'tasks':>6}{'baseline':>11}{'actual':>10}{'overhead':>10}{'net':>10}",
    ]
    for k, a in s["by_action"].items():
        out.append(f"{k:<22}{a['tasks']:>6}{a['baseline']:>11,}{a['actual']:>10,}{a['overhead']:>10,}{a['net_saved']:>10,}")
    out.append("")
    out.append("baseline bases: " + ", ".join(s["baseline_bases"]))
    out += [f"warning: {e}" for e in errors or []]
    return "\n".join(out)
