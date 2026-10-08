import json

from jevgb import ledger
from jevgb.cli import main
from jevgb.tokens import cap_text, count_tokens, estimator_label


def test_chars4_estimator():
    assert count_tokens("abcd" * 10) == 10
    assert "chars/4" in estimator_label()


def test_cap_text():
    capped = cap_text("x" * 10000, 100)
    assert count_tokens(capped) <= 100 and "trimmed" in capped


def test_ledger_record_and_summary(tmp_path):
    p = tmp_path / "t.jsonl"
    ledger.record(p, task_id="a", action="handoff_build", baseline_tokens=1000, actual_tokens=200,
                  overhead_tokens=50, baseline_basis="test")
    ledger.record(p, task_id="b", action="chat_only", baseline_tokens=None, actual_tokens=0,
                  overhead_tokens=40, baseline_basis="not_measurable")
    recs, errs = ledger.read(p)
    s = ledger.summarize(recs)
    assert s["tasks"] == 2 and s["measured_tasks"] == 1
    assert s["net_saved_tokens"] == 1000 - 200 - 50 - 40  # unmeasured overhead still counts
    assert s["by_action"]["chat_only"]["net_saved"] == -40
    assert "ESTIMATES" in ledger.format_report(s)


def test_report_flags_simulated_and_bad_lines(tmp_path, capsys):
    p = tmp_path / "t.jsonl"
    ledger.record(p, task_id="a", action="reuse_cache", baseline_tokens=500, actual_tokens=100,
                  baseline_basis="x", simulated=True)
    with p.open("a") as f:
        f.write("not json\n")
    assert main(["report", "--log", str(p)]) == 0
    out = capsys.readouterr().out
    assert "SIMULATED" in out and "invalid JSON" in out


def test_report_empty(tmp_path, capsys):
    assert main(["report", "--log", str(tmp_path / "none.jsonl")]) == 0
    assert "No records" in capsys.readouterr().out


def test_no_hardcoded_savings_in_router(cfg):
    from jevgb.router import route_task
    out = route_task({"goal": "What is 2+2?"}, cfg)
    assert out["tokens"]["baseline_tokens"] is None  # nothing claimed when nothing is measurable
