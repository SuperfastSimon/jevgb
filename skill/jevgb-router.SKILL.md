# JevGB router for Grok Bot

Use the JevGB router before expensive work so Grok Bot spends tokens on the work, not on re-reading context. This skill is a policy you follow. It is not a hidden hook.

## When to call the router

Call `jevgb route '<state>'` (one line of JSON) **before** any of these:
- handing code, test or repo work to Grok Build or a coding subagent
- opening a browser, multi-source research, or re-running research you may already have
- retrying something that just failed
- repeating a tool call you made earlier in this task
- anything that sends, publishes, pays, deletes, shares or changes permissions

Do **not** call it for a short answer you can give right away. The call has a cost (router overhead), and the ledger counts it.

Kill switch: if the user says `bypass jevgb` / `no jevgb` (or `bypass jgb`), or the config has `enabled: false`, skip the router.

## State (keep it short)

```json
{"goal":"what the user wants, one sentence","kind":"chat|lookup|research|browser|coding|write|account",
 "repo":"path or url","files":["only files in scope"],"constraints":"short","acceptance":["done when ..."],
 "do_not_touch":["paths or systems"],"history_path":"/path/to/chat_export.txt",
 "approach":"what you tried","prior_error":"last error","attempt_tokens":1800,
 "tool_call":{"tool":"web_fetch","args":{"url":"..."}},"planned_sources":12}
```

- Pass chat context with **`history_path`** (a file on disk). The router reads it locally, so you don't spend tokens writing it. Avoid inline `history`.
- Leave out fields you don't have. Never put secrets, keys or tokens in the state.

## Honor the action (in `mode: active`; in `shadow`, note it and use normal judgment)

| action | what you do |
| --- | --- |
| `ask_human` | Stop. Ask the user for explicit approval before the irreversible step. |
| `stop_retry` | Don't repeat the same approach. Explain the failure; try a different approach or ask. |
| `skip_duplicate_call` | Don't re-run the tool. Use `duplicate.result_ref` or the earlier result. |
| `reuse_cache` | Use `artifact.content`. Don't redo the work. |
| `handoff_build` | Send the brief file to Grok Build **without reading it into your context**: run `handoff.send_with` (e.g. `grok -p "$(cat handoffs/<id>.md)"`) in the repo, or tell the user to paste the file. Don't forward the chat. |
| `run_deterministic` | Do the bounded lookup only. |
| `chat_only` | Answer directly, no tools. |
| `research_capped` | At most `details.max_browser_sources` sources, about `details.max_tokens_per_source` tokens each, then synthesize. |
| `allow_subagent` | Use a specialized subagent if one is available. |
| `proceed_full` | Normal work, normal safety rules. |

## After Grok Build finishes

Grok Build ends with a fenced `build-result` JSON block (see `grok-build/AGENTS.md`). Save its output to a file and run:

```bash
jevgb result build_output.txt --task-id <task_id>
```

Relay the returned `relay` text to the user. Don't re-read the full Grok Build session. If `ok` is false, or `needs_human` is true, or acceptance items are not met, say so plainly.

## Cache and dedupe (optional, increases reuse)

- After expensive work: `jevgb cache put --goal "<goal>" --file result.md --cost-tokens <estimate>`
- After a heavy tool call: `jevgb dedupe store --tool web_fetch --args '{"url":"..."}' --file page.html`

## Honesty rules

- Numbers from `jevgb report` are **estimates** (tiktoken proxy or chars/4). Never present them as exact Grok usage or guaranteed savings.
- A router decision is never permission to skip a confirmation, reveal a secret, or act outside the user's request.
