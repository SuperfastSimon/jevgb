"""Deterministic, offline classifier used when Jev is unavailable.

Zero network, zero cost. It is a keyword/heuristic fallback, so it is less
nuanced than Jev; it is tuned to be conservative (irreversible verbs win, and
an unclear request falls back to normal full work).
Returns the same signal shape the Jev path produces.
"""
from __future__ import annotations

import re
from typing import Any

INTENTS = ("chat", "lookup", "research", "browser", "coding", "write", "account")

# English + Dutch cues. Patterns are matched on word boundaries, lowercase.
RULES: dict[str, list[str]] = {
    "account": [
        r"send", r"e-?mail (it|them|the)", r"publish", r"post (it|this|to)", r"tweet", r"pay", r"purchase",
        r"buy", r"delete", r"remove (the )?(account|repo|file)s?", r"permissions?", r"share (it|with|the)",
        r"git push", r"push to", r"merge (to|into) main", r"deploy to prod\w*", r"transfer",
        r"verstuur", r"versturen", r"stuur", r"publiceer", r"betaal", r"koop", r"verwijder", r"deel (het|met)",
    ],
    "coding": [
        r"code", r"bug", r"fix", r"refactor", r"implement\w*", r"unit ?tests?", r"pytest", r"tests?",
        r"function", r"class", r"repo(sitory)?", r"pull request", r"pr", r"compile", r"stack ?trace",
        r"endpoint", r"api", r"script", r"cli", r"module", r"lint", r"type ?errors?", r"build (a|the|an)",
        r"python", r"typescript", r"javascript", r"fastapi", r"react", r"sql", r"\w+\.(py|ts|tsx|js|go|rs|java|rb|sh|yaml|toml)",
        r"bouw", r"programmeer", r"repareer", r"herschrijf de code",
    ],
    "browser": [
        r"click", r"open the (site|page|website)", r"log ?in", r"fill (in|out)", r"checkout", r"form",
        r"scroll", r"screenshot", r"klik", r"inloggen", r"formulier",
    ],
    "research": [
        r"research", r"compare", r"latest", r"news", r"sources", r"find out", r"look up online", r"survey",
        r"what are the best", r"benchmark", r"summari[sz]e .*(news|articles|reports)",
        r"onderzoek", r"zoek uit", r"vergelijk", r"nieuws", r"bronnen",
    ],
    "lookup": [
        r"status", r"check (the|if|whether)", r"which version", r"read (the )?file", r"show (me )?the",
        r"how many", r"list (the|all)", r"value of", r"bekijk", r"controleer", r"welke versie",
    ],
    "write": [
        r"draft", r"write (a|an|the)", r"letter", r"essay", r"cover letter", r"cv", r"blog", r"rewrite",
        r"schrijf", r"brief", r"motivatie", r"tekst",
    ],
}
_COMPILED = {k: [re.compile(rf"\b(?:{p})\b") for p in v] for k, v in RULES.items()}


def _hits(text: str) -> dict[str, int]:
    return {k: sum(1 for p in pats if p.search(text)) for k, pats in _COMPILED.items()}


def classify(jstate: dict[str, Any], max_retries_same_error: int = 1) -> dict[str, Any]:
    goal = str(jstate.get("goal") or "")
    text = " ".join([goal, str(jstate.get("constraints") or "")]).lower()
    hits = _hits(text)
    if jstate.get("repo") or jstate.get("files"):
        hits["coding"] += 2

    hint = str(jstate.get("kind_hint") or "unknown").lower()
    words = len(goal.split())
    if not any(hits.values()):
        hits["chat"] = 1 if (words <= 15) else 0

    total = sum(hits.values())
    probs = {k: (hits.get(k, 0) / total if total else 0.0) for k in INTENTS}
    intent = max(INTENTS, key=lambda k: (probs[k], -INTENTS.index(k))) if total else "write"
    confidence = probs.get(intent, 0.0)

    # A valid caller hint is strong evidence, but irreversible cues still win (safety).
    if hint in INTENTS and not (hits["account"] and hint != "account"):
        if hint != intent:
            confidence = 0.8
        intent, confidence = hint, max(confidence, 0.8)
    if hits["account"]:
        intent, confidence = "account", max(confidence, 0.9)
    if not total and hint not in INTENTS:
        confidence = 0.3  # unclear → router falls back to proceed_full

    same_err = int(jstate.get("same_error_count") or 0)
    complexity = 0.0 if intent in ("chat", "lookup") else 0.5
    if intent in ("coding", "research", "browser") and (words > 25 or jstate.get("files")):
        complexity = 1.0

    return {
        "classifier": "local-rules",
        "intent": intent,
        "intent_confidence": round(confidence, 4),
        "intent_probs": {k: round(v, 4) for k, v in probs.items()},
        "reuse_cache": 0.8 if jstate.get("has_cached_artifact") else 0.0,
        "needs_subagent": 0.8 if complexity >= 1.0 else 0.2,
        "stop_retry": 0.9 if same_err >= max_retries_same_error and jstate.get("prior_error") else 0.0,
        "complexity_0_1": complexity,
        "keyword_hits": {k: v for k, v in hits.items() if v},
    }
