"""jevgb CLI.

  jevgb route '<json state>'          route a task (legacy: jevgb '<json>')
  jevgb handoff '<json state>'        print a Grok Build brief (no routing)
  jevgb result FILE|- [--transcript F] [--task-id ID]   parse Grok Build's build-result block
  jevgb cache put --goal G --file F [--kind K] [--cost-tokens N] [--note T]
  jevgb cache get --goal G [--kind K]
  jevgb dedupe store --tool T --args JSON --file F [--ref REF]
  jevgb log --action A --actual N [--baseline N] --basis TEXT [--task-id ID] [--goal G]
  jevgb report [--log PATH] [--json]
  jevgb estimate FILE|-
  jevgb dashboard [--log PATH] [--port 8765] [--no-open]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jevgb import ledger
from jevgb.cache import ArtifactCache
from jevgb.config import load_config, resolve
from jevgb.guards import ToolCallDeduper
from jevgb.handoff import build_brief, parse_build_result, relay_message
from jevgb.router import _load_history, route_task
from jevgb.tokens import count_tokens, estimator_label


def _read(src: str) -> str:
    return sys.stdin.read() if src == "-" else Path(src).read_text(encoding="utf-8")


def _state(raw: str) -> dict[str, Any]:
    return json.loads(_read(raw[1:]) if raw.startswith("@") else raw)


def _print(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0].lstrip().startswith("{"):
        argv = ["route", *argv]  # upstream-compatible: python -m jevgb.cli '<json>'
    p = argparse.ArgumentParser(prog="jevgb", description="Cheap routing + compact Grok Build handoffs + measured token savings.")
    p.add_argument("--config", help="path to config.yaml")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("route"); s.add_argument("state", help="JSON, or @file")
    s.add_argument("--pretty", action="store_true", help="indent output (default is one compact line: fewer tokens)")
    s.add_argument("--verbose", action="store_true", help="include all classifier signals")
    s = sub.add_parser("handoff"); s.add_argument("state", help="JSON, or @file")
    s = sub.add_parser("result"); s.add_argument("src"); s.add_argument("--transcript"); s.add_argument("--task-id")
    s.add_argument("--full", action="store_true", help="also print the parsed result object")
    s = sub.add_parser("cache"); s.add_argument("op", choices=["put", "get"]); s.add_argument("--goal", required=True)
    s.add_argument("--kind"); s.add_argument("--file"); s.add_argument("--cost-tokens", type=int); s.add_argument("--note", default="")
    s = sub.add_parser("dedupe"); s.add_argument("op", choices=["store", "check"]); s.add_argument("--tool", required=True)
    s.add_argument("--args", default="{}"); s.add_argument("--file"); s.add_argument("--ref", default="")
    s = sub.add_parser("log"); s.add_argument("--action", required=True); s.add_argument("--actual", type=int, required=True)
    s.add_argument("--baseline", type=int); s.add_argument("--basis", required=True); s.add_argument("--task-id")
    s.add_argument("--goal", default="")
    s = sub.add_parser("report"); s.add_argument("--log"); s.add_argument("--json", action="store_true")
    s = sub.add_parser("estimate"); s.add_argument("src")
    s = sub.add_parser("dashboard"); s.add_argument("--log"); s.add_argument("--port", type=int, default=8765)
    s.add_argument("--no-open", action="store_true")

    a = p.parse_args(argv)
    cfg = load_config(a.config)
    tok_path = resolve(cfg, cfg["tokens"]["log_path"])

    if a.cmd == "route":
        out = route_task(_state(a.state), cfg, verbose=a.verbose or None)
        print(json.dumps(out, ensure_ascii=False, indent=2 if a.pretty else None))
    elif a.cmd == "handoff":
        st = _state(a.state)
        hist, _ = _load_history(st)
        hb = build_brief(st, hist, max_brief_tokens=int(cfg["handoff"]["max_brief_tokens"]),
                         max_summary_tokens=int(cfg["handoff"]["max_summary_tokens"]), task_id=st.get("task_id", ""))
        print(hb["markdown"])
        print(f"\n<!-- ~{hb['tokens']} tokens ({estimator_label()}) -->", file=sys.stderr)
    elif a.cmd == "result":
        text = _read(a.src)
        parsed = parse_build_result(text)
        if parsed["result"] is None:
            _print(parsed)
            return 1
        relay = relay_message(parsed["result"])
        parsed["relay"] = relay
        if a.transcript or a.task_id:
            full = _read(a.transcript) if a.transcript else text
            ledger.record(tok_path, task_id=a.task_id or ledger.new_task_id(), action="build_result_relay",
                          baseline_tokens=count_tokens(full), actual_tokens=count_tokens(relay),
                          baseline_basis="full_build_output_vs_relay(measured)", goal="relay Grok Build result")
        _print(parsed if a.full else {"ok": parsed["ok"], "errors": parsed["errors"], "relay": relay})
        return 0 if parsed["ok"] else 1
    elif a.cmd == "cache":
        c = ArtifactCache(resolve(cfg, cfg["cache"]["path"]), cfg["cache"]["ttl_minutes"], cfg["cache"]["max_entries"])
        if a.op == "put":
            if not a.file:
                p.error("cache put needs --file")
            e = c.put(a.goal, _read(a.file), kind=a.kind, cost_tokens=a.cost_tokens, note=a.note)
            _print({k: v for k, v in e.items() if k != "content"})
        else:
            e = c.get(a.goal, kind=a.kind)
            _print(e or {"hit": False})
            return 0 if e else 3
    elif a.cmd == "dedupe":
        d = ToolCallDeduper(resolve(cfg, cfg["dedupe"]["path"]), cfg["dedupe"]["ttl_minutes"])
        args = json.loads(a.args)
        if a.op == "store":
            d.store_result(a.tool, args, _read(a.file) if a.file else "", result_ref=a.ref or (a.file or ""))
            _print({"stored": True})
        else:
            _print(d.check(a.tool, args))
    elif a.cmd == "log":
        _print(ledger.record(tok_path, task_id=a.task_id or ledger.new_task_id(), action=a.action,
                             baseline_tokens=a.baseline, actual_tokens=a.actual,
                             baseline_basis=f"caller_reported: {a.basis}", goal=a.goal))
    elif a.cmd == "report":
        path = Path(a.log) if a.log else tok_path
        recs, errors = ledger.read(path)
        s_ = ledger.summarize(recs)
        if a.json:
            _print({**s_, "warnings": errors})
        else:
            print(ledger.format_report(s_, errors))
    elif a.cmd == "estimate":
        _print({"tokens": count_tokens(_read(a.src)), "estimator": estimator_label()})
    elif a.cmd == "dashboard":
        from jevgb.dashboard import serve
        return serve(cfg, Path(a.log) if a.log else tok_path, port=a.port, open_browser=not a.no_open)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
