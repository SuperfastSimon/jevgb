from jevgb.cache import ArtifactCache
from jevgb.guards import RetryTracker, ToolCallDeduper
from jevgb.normalize import error_signature, goal_key
from jevgb.router import route_task


def test_goal_key_normalizes():
    assert goal_key("Please summarize the AI news!") == goal_key("summarize   AI news")
    assert goal_key("summarize AI news") != goal_key("summarize EU news")


def test_cache_ttl(tmp_path):
    c = ArtifactCache(tmp_path / "a.json", ttl_minutes=10)
    c.put("AI news brief", "content", cost_tokens=900, now=1000)
    assert c.get("ai news brief", now=1000 + 60)["cost_tokens"] == 900
    assert c.get("ai news brief", now=1000 + 11 * 60) is None


def test_router_reuse_cache(cfg):
    from jevgb.config import resolve
    c = ArtifactCache(resolve(cfg, cfg["cache"]["path"]), 120)
    c.put("Summarize AI agent news", "Brief: three items...", cost_tokens=5000)
    out = route_task({"goal": "summarize AI agent news please", "kind": "research"}, cfg)
    assert out["action"] == "reuse_cache"
    assert out["tokens"]["baseline_tokens"] == 5000
    assert out["artifact"]["content"].startswith("Brief")


def test_error_signature_ignores_numbers():
    assert error_signature("Timeout after 30s at 0xdeadbeef") == error_signature("timeout after 45s at 0xabcdef12")


def test_retry_stop_after_n(tmp_path):
    r = RetryTracker(tmp_path / "r.json", max_failures=2)
    assert not r.record_failure("scrape", "selenium", "timeout 30s", attempt_tokens=800, now=1)["stop"]
    s = r.record_failure("scrape", "selenium", "timeout 31s", attempt_tokens=1200, now=2)
    assert s["stop"] and s["avg_attempt_tokens"] == 1000
    assert not r.status("scrape", "playwright", "timeout", now=3)["stop"]  # different approach is allowed


def test_router_stop_retry(cfg):
    st = {"goal": "scrape prices", "kind": "browser", "approach": "css selector",
          "prior_error": "timeout on selector", "attempt_tokens": 700}
    assert route_task(st, cfg)["action"] != "stop_retry"
    out = route_task(st, cfg)
    assert out["action"] == "stop_retry"
    assert out["tokens"]["baseline_tokens"] == 700


def test_dedupe(tmp_path, cfg):
    d = ToolCallDeduper(tmp_path / "d.json", ttl_minutes=5)
    assert not d.check("web_fetch", {"url": "x"}, now=0)["duplicate"]
    d.store_result("web_fetch", {"url": "x"}, "y" * 4000, result_ref="cache/x.html", now=0)
    assert d.check("web_fetch", {"url": "x"}, now=60)["duplicate"]
    assert not d.check("web_fetch", {"url": "x"}, now=400)["duplicate"]

    from jevgb.config import resolve
    rd = ToolCallDeduper(resolve(cfg, cfg["dedupe"]["path"]), 30)
    rd.store_result("web_fetch", {"url": "https://a"}, "z" * 4000, result_ref="a.html")
    out = route_task({"goal": "read the page", "tool_call": {"tool": "web_fetch", "args": {"url": "https://a"}}}, cfg)
    assert out["action"] == "skip_duplicate_call" and out["tokens"]["baseline_tokens"] == 1000


def test_account_beats_everything(cfg):
    out = route_task({"goal": "send the invoice email", "prior_error": "x", "same_error_count": 5}, cfg)
    assert out["action"] == "ask_human"


def test_kill_switch(cfg):
    out = route_task({"goal": "bypass jgb: fix bug"}, cfg)
    assert out["action"] == "proceed_full"


def test_caller_cached_artifact_upstream_compat(cfg):
    out = route_task({"goal": "Summarize AI agent news", "kind": "research", "cached_artifact": True}, cfg)
    assert out["action"] == "reuse_cache" and out["tokens"]["baseline_tokens"] is None
