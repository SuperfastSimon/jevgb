#!/usr/bin/env python3
"""Dry-run demo with SIMULATED data. No network, no API keys, no real usage.

Every input below (chat history, web pages, build transcript) is synthetic text
generated in this file. Token numbers are real *counts of that synthetic text*
by the active estimator, so they show how the accounting works, not what you
will save in practice. Output records are flagged "simulated": true.

Writes:
  examples/demo/tokens.SIMULATED.jsonl   ledger records
  examples/demo/handoffs/*.md            generated Grok Build briefs
  jevgb/dashboard_static/demo-data.js                 the same data for the dashboard's demo mode
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jevgb import ledger  # noqa: E402
from jevgb.cache import ArtifactCache  # noqa: E402
from jevgb.config import load_config, resolve  # noqa: E402
from jevgb.guards import ToolCallDeduper  # noqa: E402
from jevgb.handoff import parse_build_result, relay_message  # noqa: E402
from jevgb.router import route_task  # noqa: E402
from jevgb.tokens import count_tokens, estimator_label  # noqa: E402

OUT = ROOT / "examples" / "demo"


def synthetic_chat(turns: int) -> str:
    """A fake, repetitive chat between a user and Grok Bot (SIMULATED)."""
    lines = []
    topics = ["the landing page copy", "lunch plans", "an unrelated calendar question", "the weekly report",
              "a CSV export that looked off", "which coffee place is open"]
    for i in range(turns):
        t = topics[i % len(topics)]
        lines.append(f"user: [simulated turn {i}] Quick question about {t}, can you take a look when you have time?")
        lines.append(f"bot: [simulated turn {i}] Sure. Here is a longer answer about {t} with some detail, a few options, "
                     f"and a recap of what we discussed earlier so the thread stays readable for both of us.")
    lines += [
        "user: For the API: the /export endpoint must keep returning CSV, do not touch billing/.",
        "user: Tests must pass with pytest; add a test for the empty-dataset case.",
        "user: Can you fix the crash in app/export.py when the dataset is empty?",
    ]
    return "\n".join(lines)


def synthetic_page(i: int) -> str:
    return (f"[simulated web page {i}] " + "Lorem-style filler about agent tooling, pricing tables, and release notes. " * 60)


BUILD_TRANSCRIPT = (
    "[simulated Grok Build session]\n" + "\n".join(
        f"tool: read_file app/export.py lines {i*40}-{i*40+40}\n" + "    def export(rows): ... " * 12 for i in range(25))
    + "\n" + "tool: run pytest -q\n" + "....... " * 40 + "\n"
    + """Done.
```build-result
{"status": "done", "summary": "Guarded empty datasets in export(); /export still returns CSV (header only). Added test.",
 "files_changed": ["app/export.py", "tests/test_export.py"],
 "tests": {"command": "pytest -q", "passed": 41, "failed": 0},
 "acceptance": [{"criterion": "pytest passes", "met": true}, {"criterion": "empty dataset returns header-only CSV", "met": true}],
 "open_questions": [], "needs_human": false, "next_step": "Review the diff and merge when happy."}
```"""
)


def main() -> int:
    home = Path(tempfile.mkdtemp(prefix="jevgb-demo-"))
    os.environ["JGB_HOME"] = str(home)
    cfg = load_config(ROOT / "config.example.yaml", {"classifier": "local"})
    tok = resolve(cfg, cfg["tokens"]["log_path"])

    hist_long = home / "chat_long.txt"
    hist_long.write_text(synthetic_chat(120))
    hist_short = home / "chat_short.txt"
    hist_short.write_text(synthetic_chat(2))

    def r(state):
        return route_task(state, cfg, simulated=True)

    # 1-2: coding work -> handoff_build (long vs short chat)
    r({"task_id": "sim-01", "goal": "Fix the crash in app/export.py when the dataset is empty", "repo": "~/code/shop",
       "files": ["app/export.py", "tests/test_export.py"], "acceptance": ["pytest passes", "empty dataset returns header-only CSV"],
       "do_not_touch": ["billing/", ".env"], "history_path": str(hist_long)})
    r({"task_id": "sim-02", "goal": "Rename the helper in utils/dates.py and update imports", "repo": "~/code/shop",
       "files": ["utils/dates.py"], "history_path": str(hist_short)})

    # 3-4: research, then the same goal again -> reuse_cache
    r({"task_id": "sim-03", "goal": "Research the latest coding agent pricing", "kind": "research", "planned_sources": 12})
    pages = "\n".join(synthetic_page(i) for i in range(5))
    brief = "[simulated research brief] Five sources compared; summary table and three caveats."
    ArtifactCache(resolve(cfg, cfg["cache"]["path"]), cfg["cache"]["ttl_minutes"]).put(
        "Research the latest coding agent pricing", brief, cost_tokens=count_tokens(pages) + count_tokens(brief))
    r({"task_id": "sim-04", "goal": "research the latest coding agent pricing", "kind": "research"})

    # 5-6: same approach fails twice -> stop_retry
    fail = {"goal": "Scrape the price table", "kind": "browser", "approach": "css selector .price",
            "prior_error": "TimeoutError: selector .price not found after 30000ms", "attempt_tokens": 2400}
    r({**fail, "task_id": "sim-05"})
    r({**fail, "task_id": "sim-06", "prior_error": "TimeoutError: selector .price not found after 30012ms"})

    # 7: identical tool call -> skip_duplicate_call
    ToolCallDeduper(resolve(cfg, cfg["dedupe"]["path"]), 30).store_result(
        "web_fetch", {"url": "https://example.com/changelog"}, synthetic_page(99), result_ref="cache/changelog.html")
    r({"task_id": "sim-07", "goal": "read the changelog", "tool_call": {"tool": "web_fetch", "args": {"url": "https://example.com/changelog"}}})

    # 8-9: no cheaper path: pure router overhead is recorded too
    r({"task_id": "sim-08", "goal": "What does HTTP 418 mean?"})
    r({"task_id": "sim-09", "goal": "Send the invoice email to the client"})

    # 10: Grok Build reports back; the bot relays the short result instead of re-reading the session
    parsed = parse_build_result(BUILD_TRANSCRIPT)
    relay = relay_message(parsed["result"])
    ledger.record(tok, task_id="sim-01", action="build_result_relay", baseline_tokens=count_tokens(BUILD_TRANSCRIPT),
                  actual_tokens=count_tokens(relay), baseline_basis="full_build_output_vs_relay(measured)",
                  goal="Relay Grok Build result for sim-01", simulated=True, extra={"relay": relay})

    # Collect outputs
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "handoffs").mkdir(parents=True)
    shutil.copy(tok, OUT / "tokens.SIMULATED.jsonl")
    briefs = {}
    for f in sorted((home / "handoffs").glob("*.md")):
        shutil.copy(f, OUT / "handoffs" / f.name)
        briefs[f.stem] = f.read_text()
    recs, errors = ledger.read(tok)
    # Make paths in the shipped sample relative and machine-independent.
    for rec in recs:
        if rec.get("extra", {}).get("handoff_path"):
            rec["extra"]["handoff_path"] = f"examples/demo/handoffs/{Path(rec['extra']['handoff_path']).name}"
    (OUT / "tokens.SIMULATED.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in recs))
    report = ledger.format_report(ledger.summarize(recs), errors)
    (OUT / "report.SIMULATED.txt").write_text(report + "\n")
    (ROOT / "jevgb" / "dashboard_static" / "demo-data.js").write_text(
        "// SIMULATED demo data generated by scripts/demo_savings.py. Not real usage.\n"
        "window.JGB_DEMO = " + json.dumps({"simulated": True, "estimator": estimator_label(),
                                                 "records": recs, "briefs": briefs}, ensure_ascii=False) + ";\n")
    print(report)
    print(f"\nwrote {OUT.relative_to(ROOT)}/ and jevgb/dashboard_static/demo-data.js")
    shutil.rmtree(home, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
