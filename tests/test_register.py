import yaml

from displacement_observatory.register.schema import RestrictionEvent
from displacement_observatory.register.store import EVENTS_DIR, events_by_hs6, load_events

VALID_EVENT = {
    "event_id": "test-1",
    "substance": "Testicide",
    "jurisdiction": "Testland",
    "restriction_type": "ban",
    "scope": "All uses",
    "decision_date": "2020-01-01",
    "effective_date": "2020-06-01",
    "citation": {
        "source_document": "Test Regulation 1/2020",
        "source_clause": "Article 1",
        "retrieved_at": "2026-09-18",
    },
    "hs6_candidates": [
        {
            "hs6": "380810",
            "confidence": 0.5,
            "reasoning": "test",
            "imprecision": "test",
        }
    ],
}


def test_valid_event_parses():
    event = RestrictionEvent.model_validate(VALID_EVENT)
    assert event.decision_to_effective_days == 152


def test_missing_citation_is_rejected():
    bad = {k: v for k, v in VALID_EVENT.items() if k != "citation"}
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        RestrictionEvent.model_validate(bad)


def test_real_register_loads_with_no_drops():
    result = load_events(version=1)
    assert len(result.events) == 9
    assert result.dropped == []
    event_ids = {e.event_id for e in result.events}
    assert "eu-2018-imidacloprid" in event_ids
    assert "rotterdam-2011-endosulfan" in event_ids


def test_real_register_all_have_hs6_380810_or_380830():
    result = load_events(version=1)
    hs6s = {c.hs6 for e in result.events for c in e.hs6_candidates}
    assert hs6s == {"380810", "380830"}


def test_dropped_record_when_yaml_malformed(tmp_path, monkeypatch):
    import displacement_observatory.register.store as store_module

    bad_events = {"events": [VALID_EVENT, {"event_id": "no-citation", "substance": "X"}]}
    events_dir = tmp_path
    (events_dir / "events_v99.yaml").write_text(yaml.dump(bad_events), encoding="utf-8")
    monkeypatch.setattr(store_module, "EVENTS_DIR", events_dir)

    result = store_module.load_events(version=99)
    assert len(result.events) == 1
    assert len(result.dropped) == 1
    assert result.dropped[0][0]["event_id"] == "no-citation"


def test_events_by_hs6_groups_correctly():
    result = load_events(version=1)
    grouped = events_by_hs6(result)
    assert len(grouped["380810"]) == 7  # neonicotinoids x3, chlorpyrifos x2, endosulfan x2 (EU + Rotterdam)
    assert len(grouped["380830"]) == 2  # paraquat, atrazine


def test_2018_neonicotinoid_regulations_are_restrictions_of_approval_not_non_renewals():
    # Implementing Regulations (EU) 2018/783-785 amend the *conditions of
    # approval* (permanent-greenhouse use only); they do not decline renewal.
    result = load_events(version=1)
    by_id = {e.event_id: e for e in result.events}
    for eid in ("eu-2018-imidacloprid", "eu-2018-clothianidin", "eu-2018-thiamethoxam"):
        assert by_id[eid].restriction_type.value == "severe_restriction", eid
    # the 2020 chlorpyrifos regulations are titled "non-renewal of the approval"
    assert by_id["eu-2020-chlorpyrifos"].restriction_type.value == "non-renewal"
