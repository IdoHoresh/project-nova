from nova_agent.memory.semantic import SemanticStore


def test_add_rule_returns_id_and_persists(tmp_path):
    store = SemanticStore(tmp_path / "sem.db")
    rid = store.add_rule(
        rule="protect the corner",
        citations=["ep_a", "ep_b"],
        confidence=7,
    )
    assert rid >= 1
    rules = store.all_rules()
    assert any(r["rule"] == "protect the corner" for r in rules)


def test_citations_round_trip_as_list(tmp_path):
    store = SemanticStore(tmp_path / "sem.db")
    store.add_rule(rule="merge mid-tier early", citations=["ep_1"], confidence=5)
    rules = store.all_rules()
    assert rules[0]["citations"] == ["ep_1"]


def test_all_rules_orders_newest_first(tmp_path):
    store = SemanticStore(tmp_path / "sem.db")
    store.add_rule(rule="first", citations=[])
    store.add_rule(rule="second", citations=[])
    rules = store.all_rules()
    assert rules[0]["rule"] == "second"
    assert rules[1]["rule"] == "first"


def test_default_confidence_is_5(tmp_path):
    store = SemanticStore(tmp_path / "sem.db")
    store.add_rule(rule="default-confidence-rule", citations=[])
    rules = store.all_rules()
    assert rules[0]["confidence"] == 5
