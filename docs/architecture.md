# Architecture

JevGB is an external decision layer that Grok Bot calls through a skill. It does not change Grok Bot or Grok Build.

```text
user request
   │
   ▼
Grok Bot wakes, loads skill/jevgb-router.SKILL.md
   │
   ├─ kill switch / "bypass jevgb"?──yes──▶ normal Grok Bot path
   ▼
jevgb route <state>                                  (jevgb/router.py)
   │  1. classify: local rules (default, offline)  │ or TypeSafe Jev (if key; falls back to rules)
   │  2. guards:  retry tracker · tool-call dedupe · artifact cache (TTL, normalized goal)
   │  3. policy:  ask_human > stop_retry > skip_duplicate_call > reuse_cache > handoff_build
   │              > run_deterministic > chat_only > allow_subagent > research_capped > proceed_full
   │  4. ledger:  baseline / actual / overhead → logs/tokens.jsonl
   ▼
compact decision JSON ──▶ Grok Bot honors it (active) or notes it (shadow)
                              │
                 handoff_build│ grok -p "$(cat handoffs/<id>.md)"
                              ▼
                          Grok Build ──build-result──▶ jevgb result ──▶ short relay to the user
```

## Modules

| module | role |
| --- | --- |
| `router.py` | normalizes state, runs classifier + guards, picks the action, writes ledger and decision log |
| `local_classifier.py` | deterministic EN/NL keyword rules, same signal shape as the Jev path |
| `jev_client.py` | optional TypeSafe `system_one` call (lazy import) |
| `handoff.py` | extractive history summary, brief rendering with token caps, `build-result` parser, relay text |
| `tokens.py` | token estimates (tiktoken proxy or chars/4), head+tail context cap |
| `ledger.py` | JSONL records, summary, text report, basis-quality split |
| `cache.py`, `guards.py`, `normalize.py`, `store.py` | artifact cache, retry tracker, dedupe, keys, atomic JSON state |
| `dashboard.py` + `dashboard_static/` | local read-only UI on 127.0.0.1 |

## Safety properties

- `ask_human` has the highest priority. Irreversible keyword cues override the caller's `kind` hint.
- The router never executes actions. It reads files only through `history_path`, which the caller provides.
- Secrets: only `TYPESAFE_API_KEY` is read, from the environment. It is never logged. The dashboard serves only its static files and `.md` briefs from the handoff/examples directories, bound to localhost.
- Failure of the Jev path never blocks: it falls back to local rules and notes this in `reason`.

## What it does not do

- It isn't a pre-wake hook or a middleware. The bot must call it.
- It doesn't measure Grok Build's internal work or Grok Bot's real metered usage.
