"""`jevgb dashboard`: serve the static dashboard and the local JSONL log on 127.0.0.1 only."""
from __future__ import annotations

import json
import mimetypes
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from jevgb import ledger
from jevgb.config import ROOT, resolve

STATIC = Path(__file__).resolve().parent / "dashboard_static"


def _brief_path(cfg: dict[str, Any], records: list[dict[str, Any]], task_id: str) -> Path | None:
    allowed = [resolve(cfg, cfg["handoff"]["out_dir"] + "/x").parent.resolve(), (ROOT / "examples").resolve()]
    candidates = [resolve(cfg, f"{cfg['handoff']['out_dir']}/{task_id}.md")]
    for r in records:
        hp = (r.get("extra") or {}).get("handoff_path")
        if r.get("task_id") == task_id and hp:
            p = Path(hp)
            candidates.insert(0, p if p.is_absolute() else ROOT / p)
    for p in candidates:
        p = p.resolve()
        if p.suffix == ".md" and p.is_file() and any(a in p.parents for a in allowed):
            return p
    return None


def make_handler(cfg: dict[str, Any], log_path: Path):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):  # keep the terminal quiet
            pass

        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, code: int, obj: Any) -> None:
            self._send(code, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8")

        def do_GET(self) -> None:
            u = urlparse(self.path)
            if u.path == "/api/tokens":
                recs, errors = ledger.read(log_path)
                if not log_path.exists():
                    errors = []  # missing log = empty state, not an error
                return self._json(200, {"records": recs, "errors": errors, "source": str(log_path)})
            if u.path == "/api/brief":
                tid = (parse_qs(u.query).get("task_id") or [""])[0]
                recs, _ = ledger.read(log_path)
                p = _brief_path(cfg, recs, tid) if tid else None
                if not p:
                    return self._json(404, {"error": f"no brief file found for {tid or '(missing task_id)'}"})
                return self._json(200, {"task_id": tid, "markdown": p.read_text(encoding="utf-8")})
            name = "index.html" if u.path in ("/", "") else u.path.lstrip("/")
            f = (STATIC / name).resolve()
            if STATIC not in f.parents or not f.is_file():
                return self._send(404, b"not found", "text/plain")
            ctype = mimetypes.guess_type(f.name)[0] or "application/octet-stream"
            self._send(200, f.read_bytes(), ctype + ("; charset=utf-8" if ctype.startswith(("text/", "application/javascript")) else ""))

    return H


def serve(cfg: dict[str, Any], log_path: Path, port: int = 8765, open_browser: bool = True) -> int:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(cfg, log_path))
    url = f"http://127.0.0.1:{port}/"
    print(f"JevGB dashboard on {url} (log: {log_path}). Ctrl+C to stop.")
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0
