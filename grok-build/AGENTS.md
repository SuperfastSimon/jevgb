# Instructions for Grok Build: receiving a JevGB handoff

Copy this file into the target repository as `AGENTS.md` (or append it to an existing one). Grok Build reads `AGENTS.md` from the repo. The handoff brief arrives as your prompt, for example `grok -p "$(cat handoffs/<task_id>.md)"`.

## Working from a brief

1. Treat the brief as the full task spec. Its sections are Goal, Repo, Files in scope, Constraints, Acceptance criteria, Do not touch, and a short Context summary.
2. Stay inside **Files in scope** unless you need a small, directly related change (a test file, an import). Mention any extra file in `files_changed`.
3. Never modify anything under **Do not touch**. Never push, publish, deploy, change git remotes, or touch secrets/`.env`, unless the brief explicitly asks.
4. If the brief is missing something you need to proceed safely, stop and report `status: "blocked"` with `open_questions`. Don't guess at product decisions.
5. Prefer plan mode for anything larger than a few lines.
6. Run the tests named in the acceptance criteria (or the project's default test command) before reporting.

## Report back: required format

End your final message with exactly one fenced block tagged `build-result`, containing valid JSON:

```build-result
{"status": "done", "summary": "What changed and why, under 600 characters.",
 "files_changed": ["app/export.py", "tests/test_export.py"],
 "tests": {"command": "pytest -q", "passed": 41, "failed": 0},
 "acceptance": [{"criterion": "pytest passes", "met": true}],
 "open_questions": [], "needs_human": false, "next_step": "Review the diff."}
```

- `status`: `done` | `partial` | `blocked` | `failed`.
- Keep `summary` short. List files instead of pasting diffs or logs. The bot relays this block, not your whole session.
- Be honest in `acceptance`: mark anything not verified as `"met": false`.
- Set `needs_human: true` when a decision or an irreversible step is needed.
