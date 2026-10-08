# Contributing

Thanks for helping improve this reference integration.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[tokens,dev]"
cp config.example.yaml config.yaml
```

Offline by default (`classifier: local` or no `TYPESAFE_API_KEY`). Set `TYPESAFE_API_KEY` only to try the optional Jev path.

## Checks before a PR

```bash
.venv/bin/python -m compileall jevgb scripts
.venv/bin/python -m pytest -q
.venv/bin/python scripts/demo_savings.py   # regenerates SIMULATED demo data
```

Live dry-runs against TypeSafe are optional and use your own key. Do not commit keys, `.env`, `config.yaml`, or logs.

## Pull requests

- Keep changes focused.
- Prefer small diffs with a clear why.
- Update README or docs when behavior changes.
- Do not claim universal Grok Bot token savings; keep A/B notes as local proxy measurements.

## Scope

This project is a skill + script decision layer. It is not a Grok Bot middleware or pre-wake interceptor. Please keep PRs aligned with that boundary.
