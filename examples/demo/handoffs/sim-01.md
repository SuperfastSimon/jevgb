# Grok Build handoff sim-01

## Goal
Fix the crash in app/export.py when the dataset is empty

## Repo
- path/url: ~/code/shop

## Files in scope
- app/export.py
- tests/test_export.py

## Constraints
- (none given)

## Acceptance criteria
- pytest passes
- empty dataset returns header-only CSV

## Do not touch
- billing/
- .env

## Context (summarized from chat; ask if something is missing)
- user: For the API: the /export endpoint must keep returning CSV, do not touch billing/.
- user: Tests must pass with pytest; add a test for the empty-dataset case.
- user: Can you fix the crash in app/export.py when the dataset is empty?

## Report back (required)
End your final message with exactly one fenced block tagged `build-result` containing JSON:
```build-result
{"status": "done | partial | blocked | failed", "summary": "what changed and why, <600 chars", "files_changed": ["path/one.py"], "tests": {"command": "pytest -q", "passed": 0, "failed": 0}, "acceptance": [{"criterion": "...", "met": true}], "open_questions": [], "needs_human": false, "next_step": ""}
```
Keep `summary` under 600 characters. Do not paste diffs or logs into it; list files instead.