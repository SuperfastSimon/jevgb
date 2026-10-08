import json

from jevgb.handoff import build_brief, parse_build_result, relay_message, summarize_history
from jevgb.router import route_task
from jevgb.tokens import count_tokens

HISTORY = "\n".join(
    [f"user: random chit-chat about the weather number {i}, unrelated to the task" for i in range(200)]
    + ["user: tests must pass and do not touch the payments module", "user: please fix router.py"]
)


def test_summary_keeps_requirements_and_respects_budget():
    s = summarize_history(HISTORY, 120)
    assert "do not touch the payments module" in s
    assert count_tokens(s) <= 120


def test_brief_has_all_sections_and_cap():
    hb = build_brief({"goal": "Fix router", "repo": "app", "files": ["router.py"],
                      "acceptance": ["pytest passes"], "do_not_touch": ["payments/"]}, HISTORY,
                     max_brief_tokens=600, max_summary_tokens=150)
    md = hb["markdown"]
    for section in ("## Goal", "## Files in scope", "## Acceptance criteria", "## Do not touch", "build-result"):
        assert section in md
    assert hb["tokens"] <= 600


def test_route_handoff_writes_brief_and_measures(cfg, tmp_path):
    hp = tmp_path / "hist.txt"
    hp.write_text(HISTORY)
    out = route_task({"goal": "Fix the failing pytest in router.py", "repo": "app",
                      "files": ["router.py"], "history_path": str(hp)}, cfg)
    assert out["action"] == "handoff_build"
    brief = open(out["handoff"]["path"]).read()
    assert "Fix the failing pytest" in brief
    t = out["tokens"]
    assert t["baseline_tokens"] == count_tokens(HISTORY + "\n\nFix the failing pytest in router.py")
    assert t["actual_tokens"] < t["baseline_tokens"]
    assert t["net_saved_tokens"] == t["baseline_tokens"] - t["actual_tokens"] - t["overhead_tokens"]


def test_handoff_without_history_is_reported_honestly(cfg):
    out = route_task({"goal": "Refactor utils.py"}, cfg)
    assert out["action"] == "handoff_build"
    assert out["tokens"]["baseline_basis"].startswith("goal_only")
    assert out["tokens"]["net_saved_tokens"] < 0  # brief costs more than a bare goal; we show it


RESULT = """Done.
```build-result
{"status": "done", "summary": "Fixed off-by-one in router", "files_changed": ["router.py", "tests/test_router.py"],
 "tests": {"command": "pytest -q", "passed": 12, "failed": 0},
 "acceptance": [{"criterion": "pytest passes", "met": true}, {"criterion": "docs", "met": false}],
 "open_questions": ["Bump version?"], "needs_human": false, "next_step": "review diff"}
```"""


def test_parse_and_relay():
    p = parse_build_result(RESULT)
    assert p["ok"], p["errors"]
    r = relay_message(p["result"])
    assert "done" in r and "12 passed" in r and "Not met: docs" in r and "Bump version?" in r


def test_parse_errors():
    assert not parse_build_result("no block")["ok"]
    bad = parse_build_result("```build-result\n{\"status\": \"meh\"}\n```")
    assert not bad["ok"] and len(bad["errors"]) >= 2
