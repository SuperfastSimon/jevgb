"""Optional TypeSafe Jev path. Imported lazily; never required for offline use."""
from __future__ import annotations

import os
from typing import Any


def jev_available() -> bool:
    if not os.environ.get("TYPESAFE_API_KEY"):
        return False
    try:
        import typesafe_sdk  # noqa: F401
    except ImportError:
        return False
    return True


def jev_signals(jstate: dict[str, Any], model: str) -> dict[str, Any]:
    """One system_one call -> the same signal shape as local_classifier.classify."""
    from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

    from jevgb.secrets import ensure_typesafe_api_key

    ensure_typesafe_api_key()
    questions = {
        "intent": Choice(
            instructions="What kind of work does this request mainly need?",
            criteria={
                "chat": "Short answer or conversation; no tools needed",
                "lookup": "Known file/API/status check; mostly deterministic",
                "research": "Need web/search and synthesis",
                "browser": "Need interactive browser clicks",
                "coding": "Edit code / tests / repo work",
                "write": "Draft long prose/email/doc",
                "account": "Send, publish, pay, delete, change permissions",
            },
        ),
        "reuse_cache": Noul(instructions="Is there already a fresh enough cached result that should be reused instead of doing new heavy work?"),
        "needs_subagent": Noul(instructions="Does this clearly need an extra specialized bot (research/browser/coding) beyond one Grok Bot turn?"),
        "stop_retry": Noul(instructions="Given prior_error and same_error_count, should we STOP retrying the same approach?"),
        "complexity": Score(
            instructions="How much Grok Bot effort is justified?",
            criteria=["Trivial — one step or cached", "Normal — short tool use", "Heavy — multi-step research/browser/coding"],
        ),
    }
    with TypeSafeClient(model=model) as client:
        r = client.system_one(state=jstate, questions=questions)
    intent = r.choices["intent"]
    return {
        "classifier": f"jev:{model}",
        "intent": intent.choice,
        "intent_confidence": round(float(intent.confidence), 4),
        "intent_probs": {k: round(float(v), 4) for k, v in (intent.probabilities or {}).items()},
        "reuse_cache": round(float(r.nouls["reuse_cache"].noul), 4),
        "needs_subagent": round(float(r.nouls["needs_subagent"].noul), 4),
        "stop_retry": round(float(r.nouls["stop_retry"].noul), 4),
        "complexity_0_1": round(float(r.scores["complexity"].score) / 2.0, 4),
    }
