from jevgb.local_classifier import classify


def c(goal, **kw):
    return classify({"goal": goal, **kw})


def test_coding_detected():
    assert c("Fix the failing test in router.py")["intent"] == "coding"


def test_repo_files_boost_coding():
    assert c("make it faster", files=["app/main.py"])["intent"] == "coding"


def test_account_wins_over_hint():
    s = c("Send the email to the customer now", kind_hint="write")
    assert s["intent"] == "account"


def test_dutch_account_and_research():
    assert c("Stuur de mail naar Mark")["intent"] == "account"
    assert c("Onderzoek en vergelijk de nieuwste bronnen")["intent"] == "research"


def test_short_question_is_chat():
    assert c("What is 2+2?")["intent"] == "chat"


def test_valid_hint_used():
    s = c("the quarterly thing", kind_hint="lookup")
    assert s["intent"] == "lookup" and s["intent_confidence"] >= 0.8


def test_stop_retry_signal():
    s = c("scrape page", prior_error="timeout", same_error_count=2)
    assert s["stop_retry"] >= 0.55


def test_no_network_needed(cfg):
    from jevgb.router import route_task
    out = route_task({"goal": "What is 2+2?"}, cfg)
    assert out["classifier"] == "local-rules" and out["action"] == "chat_only"
