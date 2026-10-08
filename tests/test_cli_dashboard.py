import json

from jevgb.cli import main
from jevgb.dashboard import _brief_path

RESULT = '```build-result\n{"status":"done","summary":"ok","files_changed":["a.py"],"tests":{"passed":1,"failed":0}}\n```'


def test_cli_route_compact_and_legacy(cfg, capsys):
    assert main(['{"goal":"What is 2+2?"}']) == 0  # upstream-style bare JSON
    out = capsys.readouterr().out.strip()
    assert "\n" not in out and json.loads(out)["action"] == "chat_only"


def test_cli_result_logs_relay(cfg, tmp_path, capsys):
    f = tmp_path / "out.txt"
    f.write_text("lots of session output\n" * 200 + RESULT)
    assert main(["result", str(f), "--task-id", "t1"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] and data["relay"].startswith("Grok Build: done")
    assert main(["report", "--json"]) == 0
    rep = json.loads(capsys.readouterr().out)
    assert rep["by_action"]["build_result_relay"]["net_saved"] > 0


def test_cli_cache_roundtrip(cfg, tmp_path, capsys):
    f = tmp_path / "a.md"
    f.write_text("artifact")
    assert main(["cache", "put", "--goal", "G one", "--file", str(f), "--cost-tokens", "50"]) == 0
    assert main(["cache", "get", "--goal", "g one"]) == 0
    assert main(["cache", "get", "--goal", "other"]) == 3


def test_dashboard_brief_path_is_confined(cfg, tmp_path):
    from jevgb.config import resolve
    good = resolve(cfg, "handoffs/t-1.md")
    good.write_text("# brief")
    assert _brief_path(cfg, [], "t-1") == good.resolve()
    outside = tmp_path.parent / "evil.md"
    outside.write_text("x")
    recs = [{"task_id": "t-2", "extra": {"handoff_path": str(outside)}}]
    assert _brief_path(cfg, recs, "t-2") is None
    assert _brief_path(cfg, [], "../../etc/passwd") is None
