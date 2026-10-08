"""Grok Bot -> Grok Build handoff brief and Grok Build -> Grok Bot return contract.

The brief replaces "forward the whole chat" with a compact, structured task
spec. Chat history (if any) is summarized *before* the handoff and capped to a
token budget. The return contract lets Grok Build answer with a short,
machine-checkable block the bot can relay without re-reading the full session.
"""
from __future__ import annotations

import json
import re
from typing import Any

from jevgb.tokens import cap_text, count_tokens

KEEP_CUES = re.compile(
    r"\b(must|should|don'?t|do not|never|always|only|acceptance|accept|done when|test|tests|error|"
    r"fail\w*|decid\w*|constraint|requirement|deadline|keep|avoid|moet|niet|nooit|altijd|alleen|graag|"
    r"klaar als|eis\w*)\b|[\w/.-]+\.(py|ts|tsx|js|md|yaml|yml|toml|json|sh)\b",
    re.IGNORECASE,
)

RESULT_STATUSES = ("done", "partial", "blocked", "failed")
RESULT_FENCE = "build-result"


def summarize_history(history: str, max_tokens: int) -> str:
    """Deterministic extractive summary: keep lines with requirements/decisions/paths,
    plus the last few lines (latest intent), de-duplicated, within budget."""
    if not history:
        return ""
    lines = [ln.strip() for ln in history.splitlines() if ln.strip()]
    seen: set[str] = set()
    picked: list[str] = []
    tail = lines[-3:]
    for ln in [l for l in lines if KEEP_CUES.search(l)] + tail:
        key = re.sub(r"\d+", "#", ln.lower())  # near-duplicates that differ only by numbers
        if key in seen:
            continue
        seen.add(key)
        picked.append(ln if len(ln) <= 300 else ln[:297] + "...")
    out: list[str] = []
    for ln in picked:
        candidate = "\n".join(out + ["- " + ln])
        if count_tokens(candidate) > max_tokens:
            break
        out.append("- " + ln)
    return "\n".join(out)


def _as_list(v: Any) -> list[str]:
    if not v:
        return []
    if isinstance(v, str):
        return [s.strip() for s in re.split(r"[\n;]+", v) if s.strip()]
    return [str(x) for x in v]


def build_brief(state: dict[str, Any], history: str = "", *, max_brief_tokens: int = 1200,
                max_summary_tokens: int = 500, task_id: str = "") -> dict[str, Any]:
    brief = {
        "task_id": task_id,
        "goal": str(state.get("goal") or "").strip(),
        "repo": state.get("repo") or "",
        "branch": state.get("branch") or "",
        "files_in_scope": _as_list(state.get("files")),
        "constraints": _as_list(state.get("constraints")),
        "acceptance_criteria": _as_list(state.get("acceptance")) or ["Existing tests pass", "New behavior covered by a test"],
        "do_not_touch": _as_list(state.get("do_not_touch")) or ["secrets / .env / credentials", "git remote, pushes, releases"],
        "context_summary": summarize_history(history, max_summary_tokens),
        "return_contract": RESULT_FENCE,
    }
    md = render_brief(brief)
    if count_tokens(md) > max_brief_tokens:
        # Shrink the free-text parts first; structured fields stay intact.
        brief["context_summary"] = cap_text(brief["context_summary"], max(60, max_summary_tokens // 3))
        md = render_brief(brief)
        if count_tokens(md) > max_brief_tokens:
            md = cap_text(md, max_brief_tokens)
    return {"brief": brief, "markdown": md, "tokens": count_tokens(md)}


def render_brief(b: dict[str, Any]) -> str:
    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {x}" for x in items) if items else "- (none given)"

    parts = [
        f"# Grok Build handoff{(' ' + b['task_id']) if b.get('task_id') else ''}",
        "",
        "## Goal",
        b["goal"] or "(missing — ask before starting)",
        "",
        "## Repo",
        f"- path/url: {b['repo'] or '(current directory)'}" + (f"\n- branch: {b['branch']}" if b.get("branch") else ""),
        "",
        "## Files in scope",
        bullets(b["files_in_scope"]),
        "",
        "## Constraints",
        bullets(b["constraints"]),
        "",
        "## Acceptance criteria",
        bullets(b["acceptance_criteria"]),
        "",
        "## Do not touch",
        bullets(b["do_not_touch"]),
    ]
    if b.get("context_summary"):
        parts += ["", "## Context (summarized from chat; ask if something is missing)", b["context_summary"]]
    parts += [
        "",
        "## Report back (required)",
        f"End your final message with exactly one fenced block tagged `{RESULT_FENCE}` containing JSON:",
        f"```{RESULT_FENCE}",
        json.dumps(RESULT_TEMPLATE, separators=(", ", ": ")),
        "```",
        "Keep `summary` under 600 characters. Do not paste diffs or logs into it; list files instead.",
    ]
    return "\n".join(parts)


RESULT_TEMPLATE = {
    "status": "done | partial | blocked | failed",
    "summary": "what changed and why, <600 chars",
    "files_changed": ["path/one.py"],
    "tests": {"command": "pytest -q", "passed": 0, "failed": 0},
    "acceptance": [{"criterion": "...", "met": True}],
    "open_questions": [],
    "needs_human": False,
    "next_step": "",
}


def parse_build_result(text: str) -> dict[str, Any]:
    """Extract and validate the build-result block. Returns {ok, result, errors}."""
    m = None
    for m in re.finditer(rf"```{RESULT_FENCE}\s*\n(.*?)```", text or "", re.DOTALL):
        pass  # keep the last block
    if not m:
        return {"ok": False, "result": None, "errors": [f"no ```{RESULT_FENCE}``` block found"]}
    try:
        data = json.loads(m.group(1))
    except json.JSONDecodeError as exc:
        return {"ok": False, "result": None, "errors": [f"invalid JSON: {exc}"]}
    errors = []
    if data.get("status") not in RESULT_STATUSES:
        errors.append(f"status must be one of {RESULT_STATUSES}")
    if not isinstance(data.get("summary"), str) or not data["summary"].strip():
        errors.append("summary is required")
    elif len(data["summary"]) > 600:
        errors.append("summary longer than 600 chars")
        data["summary"] = data["summary"][:597] + "..."
    if not isinstance(data.get("files_changed", []), list):
        errors.append("files_changed must be a list")
    tests = data.get("tests") or {}
    if tests and not isinstance(tests, dict):
        errors.append("tests must be an object")
    return {"ok": not errors, "result": data, "errors": errors}


def relay_message(result: dict[str, Any]) -> str:
    """Short text Grok Bot can pass to the user without re-reading the session."""
    r = result
    lines = [f"Grok Build: {r.get('status', '?')} — {r.get('summary', '').strip()}"]
    files = r.get("files_changed") or []
    if files:
        shown = ", ".join(files[:8]) + (f" (+{len(files) - 8} more)" if len(files) > 8 else "")
        lines.append(f"Files: {shown}")
    t = r.get("tests") or {}
    if t:
        lines.append(f"Tests: {t.get('passed', '?')} passed, {t.get('failed', '?')} failed"
                     + (f" ({t['command']})" if t.get("command") else ""))
    unmet = [a.get("criterion", "?") for a in (r.get("acceptance") or []) if not a.get("met")]
    if unmet:
        lines.append("Not met: " + "; ".join(unmet))
    if r.get("open_questions"):
        lines.append("Open questions: " + "; ".join(map(str, r["open_questions"])))
    if r.get("needs_human"):
        lines.append("Needs your decision before continuing.")
    if r.get("next_step"):
        lines.append(f"Next: {r['next_step']}")
    return "\n".join(lines)
