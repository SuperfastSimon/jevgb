"""Route a Grok Bot task: guards first, then a classifier, then one action.

Actions: ask_human, stop_retry, skip_duplicate_call, reuse_cache, handoff_build,
run_deterministic, chat_only, allow_subagent, research_capped, proceed_full.
Every routed task gets a token-ledger record (baseline vs actual vs overhead).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jevgb import ledger
from jevgb.cache import ArtifactCache
from jevgb.config import load_config, resolve, resolve_log_path
from jevgb.guards import RetryTracker, ToolCallDeduper
from jevgb.handoff import build_brief
from jevgb.jev_client import jev_available, jev_signals
from jevgb.local_classifier import classify
from jevgb.logger import log_run
from jevgb.tokens import cap_text, count_tokens, estimator_label

BYPASS_MARKERS = ("bypass jev", "no jev", "bypass jevgb", "no jevgb", "bypass jgb", "no jgb")
HISTORY_KEYS = ("history", "history_path")


def _bypassed(state: dict[str, Any]) -> bool:
    raw = " ".join(str(state.get(k, "")) for k in ("goal", "raw", "user_message", "notes")).lower()
    return any(m in raw for m in BYPASS_MARKERS)


def _load_history(state: dict[str, Any]) -> tuple[str, str]:
    """Return (history_text, source). history_path is read locally, so it costs the bot nothing."""
    if state.get("history_path"):
        p = Path(state["history_path"]).expanduser()
        if p.is_file():
            return p.read_text(encoding="utf-8", errors="replace"), "history_path"
        return "", "history_path_missing"
    if state.get("history"):
        h = state["history"]
        return (h if isinstance(h, str) else "\n".join(map(str, h))), "inline"
    return "", "none"


def _signals(jstate: dict[str, Any], cfg: dict[str, Any]) -> tuple[dict[str, Any], str | None]:
    mode = cfg.get("classifier", "auto")
    max_same = int(cfg["limits"].get("max_retries_same_error", 1))
    if mode == "jev" or (mode == "auto" and jev_available()):
        try:
            return jev_signals(jstate, cfg.get("model", "jev-latest")), None
        except Exception as exc:  # network, quota, missing key: fall back, never block the bot
            return classify(jstate, max_same), f"jev unavailable ({type(exc).__name__}); used local rules"
    return classify(jstate, max_same), None


def route_task(state: dict[str, Any], cfg: dict[str, Any] | None = None, *, simulated: bool = False,
               verbose: bool | None = None) -> dict[str, Any]:
    """Return a compact decision. Full classifier signals go to logs/runs.jsonl; pass
    verbose=True (or state["verbose"]) to get them inline. Compact output keeps router overhead low."""
    verbose = bool(state.get("verbose")) if verbose is None else verbose
    cfg = cfg or load_config()
    log_path = resolve_log_path(cfg)
    tok_path = resolve(cfg, cfg["tokens"]["log_path"])
    task_id = str(state.get("task_id") or ledger.new_task_id())
    goal = str(state.get("goal") or state.get("raw") or "")
    state_tokens = count_tokens(json.dumps(state, ensure_ascii=False))

    if not cfg.get("enabled", True) or _bypassed(state):
        out = {"task_id": task_id, "action": "proceed_full", "reason": "disabled or bypass marker",
               "mode": cfg.get("mode"), "classifier": None, "details": {}}
        log_run(log_path, {"event": "route", "goal": goal[:300], **out})
        return out

    jstate = {
        "goal": goal,
        "kind_hint": state.get("kind") or state.get("kind_hint") or "unknown",
        "has_cached_artifact": bool(state.get("cached_artifact")),
        "cached_note": state.get("cached_note") or "",
        "prior_error": state.get("prior_error") or "",
        "same_error_count": int(state.get("same_error_count") or 0),
        "sources_found": int(state.get("sources_found") or 0),
        "constraints": state.get("constraints") or "",
        "repo": state.get("repo") or "",
        "files": state.get("files") or [],
    }
    sig, warn = _signals(jstate, cfg)
    thr, limits = cfg["thresholds"], cfg["limits"]
    min_conf = float(thr.get("min_choice_confidence", 0.55))
    kind = str(state.get("kind") or "")

    cache = ArtifactCache(resolve(cfg, cfg["cache"]["path"]), cfg["cache"]["ttl_minutes"], cfg["cache"]["max_entries"])
    retries = RetryTracker(resolve(cfg, cfg["retry"]["path"]), cfg["retry"]["max_same_approach_failures"],
                           cfg["retry"]["window_minutes"])
    dedupe = ToolCallDeduper(resolve(cfg, cfg["dedupe"]["path"]), cfg["dedupe"]["ttl_minutes"])

    out: dict[str, Any] = {"task_id": task_id, "mode": cfg.get("mode"), "classifier": sig["classifier"]}
    baseline: int | None = None
    actual = 0
    basis = "not_measurable"
    extra: dict[str, Any] = {}

    retry_status = None
    if jstate["prior_error"]:
        retry_status = retries.record_failure(goal, str(state.get("approach") or "default"), jstate["prior_error"],
                                              attempt_tokens=state.get("attempt_tokens"))
    dup = None
    if isinstance(state.get("tool_call"), dict):
        tc = state["tool_call"]
        dup = dedupe.check(str(tc.get("tool")), tc.get("args"))
    hit = cache.get(goal, kind=state.get("cache_kind")) if goal else None

    if sig["intent"] == "account":
        action, reason = "ask_human", "irreversible/account class: needs explicit human approval"
    elif (retry_status and retry_status["stop"]) or (
            jstate["same_error_count"] >= int(limits.get("max_retries_same_error", 1)) and sig["stop_retry"] >= 0.55):
        action = "stop_retry"
        n = retry_status["same_approach_failures"] if retry_status else jstate["same_error_count"]
        reason = f"same approach failed {n}x with the same error; change approach or ask"
        avg = (retry_status or {}).get("avg_attempt_tokens") or state.get("attempt_tokens")
        if avg:
            baseline, basis = int(avg), "one_avoided_attempt(avg of recorded attempts)"
        extra["retry"] = retry_status
    elif dup and dup["duplicate"]:
        action = "skip_duplicate_call"
        reason = f"identical tool call {dup['age_minutes']} min ago; reuse its result"
        notice = f"duplicate of earlier call; result at {dup['result_ref'] or '(earlier in context)'}"
        baseline, actual, basis = int(dup["result_tokens"]), count_tokens(notice), "duplicate_result_size"
        out["duplicate"] = dup
    elif hit:
        action = "reuse_cache"
        reason = f"fresh artifact ({hit['age_minutes']} min old, ttl {cfg['cache']['ttl_minutes']} min)"
        content = cap_text(hit["content"], int(cfg["budgets"]["max_context_tokens"]))
        actual = count_tokens(content)
        if hit.get("cost_tokens"):
            baseline, basis = int(hit["cost_tokens"]), "artifact_production_cost(recorded at put)"
        else:
            baseline, basis = int(hit["content_tokens"]), "artifact_size(lower bound; production cost unknown)"
        out["artifact"] = {"content": content, "age_minutes": hit["age_minutes"], "note": hit.get("note", "")}
    elif jstate["has_cached_artifact"] and sig["reuse_cache"] >= float(thr.get("reuse_min", 0.65)):
        # Caller says it already holds a fresh artifact (upstream behavior). Measurable only with a cost hint.
        action, reason = "reuse_cache", "caller reports a fresh cached artifact"
        if state.get("artifact_cost_tokens"):
            baseline, basis = int(state["artifact_cost_tokens"]), "caller_hint: artifact production cost"
    elif sig["intent"] == "coding" and cfg["handoff"].get("enabled", True):
        action, reason = "handoff_build", "code/repo work: hand a compact brief to Grok Build"
        history, hsrc = _load_history(state)
        hb = build_brief(state, history, max_brief_tokens=int(cfg["handoff"]["max_brief_tokens"]),
                         max_summary_tokens=int(cfg["handoff"]["max_summary_tokens"]), task_id=task_id)
        hpath = resolve(cfg, f"{cfg['handoff']['out_dir']}/{task_id}.md")
        hpath.write_text(hb["markdown"], encoding="utf-8")
        actual = hb["tokens"]
        if history:
            baseline = count_tokens(history + "\n\n" + goal)
            basis = f"full_history_forward(measured from {hsrc})"
        elif state.get("baseline_tokens_hint"):
            baseline, basis = int(state["baseline_tokens_hint"]), "caller_hint(unverified)"
        else:
            baseline, basis = count_tokens(goal), "goal_only(no history given; brief may cost more)"
        out["handoff"] = {"path": str(hpath), "brief_tokens": hb["tokens"], "history_source": hsrc,
                          "send_with": f'grok -p "$(cat {hpath})"',
                          "return_contract": "```build-result``` JSON block; parse with `jevgb result`"}
        extra["handoff_path"] = str(hpath)
    elif sig["intent"] == "lookup" and sig["intent_confidence"] >= min_conf:
        action, reason = "run_deterministic", "intent=lookup"
    elif sig["intent"] == "chat" and sig["intent_confidence"] >= min_conf:
        action, reason = "chat_only", "intent=chat"
    elif sig["needs_subagent"] >= float(thr.get("subagent_min", 0.75)) and sig["intent"] not in ("research", "browser"):
        action, reason = "allow_subagent", f"needs_subagent={sig['needs_subagent']:.2f}"
    elif sig["intent"] in ("research", "browser"):
        cap = int(limits.get("max_browser_sources", 5))
        per = int(limits.get("max_tokens_per_source", 1500))
        action, reason = "research_capped", f"cap at {cap} sources x {per} tokens"
        planned = state.get("planned_sources")
        if planned and int(planned) > cap:
            baseline = int(planned) * per
            actual = cap * per
            basis = "planned_sources x per_source_cap(estimate)"
    else:
        action, reason = "proceed_full", "no cheaper path identified"

    if warn:
        reason += f" [{warn}]"
    out.update({
        "action": action,
        "reason": reason,
        "details": {"intent": sig["intent"], "confidence": sig["intent_confidence"]},
    })
    if action == "research_capped":
        out["details"].update(max_browser_sources=int(limits.get("max_browser_sources", 5)),
                              max_tokens_per_source=int(limits.get("max_tokens_per_source", 1500)))
    if verbose:
        out["details"] = {**sig, **out["details"]}
    # Overhead = what the bot writes (state) + reads (decision). Artifact content is counted as `actual`, not twice.
    shown = {k: v for k, v in out.items() if k != "artifact"}
    overhead = state_tokens + count_tokens(json.dumps(shown, ensure_ascii=False))
    rec = ledger.record(tok_path, task_id=task_id, action=action, baseline_tokens=baseline, actual_tokens=actual,
                        overhead_tokens=overhead, baseline_basis=basis, goal=goal, simulated=simulated,
                        extra=extra or None)
    out["tokens"] = {k: rec[k] for k in ("baseline_tokens", "actual_tokens", "overhead_tokens",
                                          "net_saved_tokens", "baseline_basis")}
    out["tokens"]["estimator"] = estimator_label()
    log_run(log_path, {"event": "route", "task_id": task_id, "goal": goal[:300], "action": action,
                       "reason": reason, "mode": cfg.get("mode"), "classifier": sig["classifier"], "signals": sig})
    return out
