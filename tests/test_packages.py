from datetime import date

import pytest

from displacement_observatory.analysis.packages import build_treatment_packages
from displacement_observatory.register.schema import Citation, HS6Candidate, RestrictionEvent
from displacement_observatory.register.store import RegisterLoadResult, load_events


def _event(event_id, substance, hs6, decision, effective, jurisdiction="EU"):
    return RestrictionEvent(
        event_id=event_id, substance=substance, jurisdiction=jurisdiction, restriction_type="non-renewal",
        scope="all", decision_date=decision, effective_date=effective,
        citation=Citation(source_document="d", source_clause="c", retrieved_at=date(2026, 9, 18)),
        hs6_candidates=[HS6Candidate(hs6=hs6, confidence=0.5, reasoning="r", imprecision="i")],
    )


def test_real_register_collapses_to_five_or_six_packages():
    register = load_events(version=1)
    packages = build_treatment_packages(register)
    # 9 register events -> 3 neonicotinoids collapse to 1, 2 chlorpyrifos collapse
    # to 1, leaving: neonic pkg, chlorpyrifos pkg, paraquat, atrazine, endosulfan(EU),
    # endosulfan(Rotterdam) = 6 packages total (5 within the EU jurisdiction alone).
    assert len(packages) == 6
    multi = [p for p in packages if p.is_multi_substance]
    assert len(multi) == 2
    neonic = next(p for p in multi if "Imidacloprid" in p.substances)
    assert set(neonic.substances) == {"Imidacloprid", "Clothianidin", "Thiamethoxam"}
    chlorpyrifos = next(p for p in multi if p is not neonic)
    assert set(chlorpyrifos.substances) == {"Chlorpyrifos", "Chlorpyrifos-methyl"}


def test_real_register_does_not_collapse_paraquat_and_atrazine():
    # Same HS6 (380830), different dates -- must stay separate packages.
    register = load_events(version=1)
    packages = build_treatment_packages(register)
    single_substance = {p.substances[0]: p for p in packages if not p.is_multi_substance}
    assert "Paraquat" in single_substance
    assert "Atrazine" in single_substance
    assert single_substance["Paraquat"].package_id != single_substance["Atrazine"].package_id


def test_collapse_by_key_ignores_substance_name():
    events = [
        _event("a", "SubA", "999999", date(2020, 1, 1), date(2020, 6, 1)),
        _event("b", "SubB", "999999", date(2020, 1, 1), date(2020, 6, 1)),
    ]
    register = RegisterLoadResult(events=events, dropped=[])
    packages = build_treatment_packages(register)
    assert len(packages) == 1
    assert set(packages[0].substances) == {"SubA", "SubB"}
    assert packages[0].event_ids == ("a", "b")


def test_different_hs6_not_collapsed():
    events = [
        _event("a", "SubA", "999999", date(2020, 1, 1), date(2020, 6, 1)),
        _event("b", "SubB", "888888", date(2020, 1, 1), date(2020, 6, 1)),
    ]
    register = RegisterLoadResult(events=events, dropped=[])
    packages = build_treatment_packages(register)
    assert len(packages) == 2


def test_different_effective_date_not_collapsed():
    events = [
        _event("a", "SubA", "999999", date(2020, 1, 1), date(2020, 6, 1)),
        _event("b", "SubB", "999999", date(2020, 1, 1), date(2020, 6, 2)),
    ]
    register = RegisterLoadResult(events=events, dropped=[])
    packages = build_treatment_packages(register)
    assert len(packages) == 2


def test_multi_hs6_event_raises():
    bad = RestrictionEvent(
        event_id="bad", substance="X", jurisdiction="EU", restriction_type="ban", scope="all",
        decision_date=date(2020, 1, 1), effective_date=date(2020, 6, 1),
        citation=Citation(source_document="d", source_clause="c", retrieved_at=date(2026, 9, 18)),
        hs6_candidates=[
            HS6Candidate(hs6="999999", confidence=0.5, reasoning="r", imprecision="i"),
            HS6Candidate(hs6="888888", confidence=0.5, reasoning="r", imprecision="i"),
        ],
    )
    register = RegisterLoadResult(events=[bad], dropped=[])
    with pytest.raises(ValueError, match="!= 1 hs6_candidate"):
        build_treatment_packages(register)


def test_hs6_date_collision_across_distinct_packages_raises(monkeypatch):
    # Force a collision that the grouping key itself would normally prevent,
    # to prove the standalone safety-net assertion actually fires.
    import displacement_observatory.analysis.packages as pkg_module

    events = [
        _event("a", "SubA", "999999", date(2020, 1, 1), date(2020, 6, 1), jurisdiction="EU"),
        _event("b", "SubB", "999999", date(2020, 1, 1), date(2020, 6, 1), jurisdiction="Non-EU"),
    ]
    register = RegisterLoadResult(events=events, dropped=[])
    with pytest.raises(AssertionError, match="share HS6"):
        pkg_module._assert_no_hs6_date_collision(
            [
                pkg_module.TreatmentPackage("a", "EU", "999999", date(2020, 1, 1), date(2020, 6, 1), ("SubA",), ("a",), ("ban",)),
                pkg_module.TreatmentPackage("b", "Non-EU", "999999", date(2020, 1, 1), date(2020, 6, 1), ("SubB",), ("b",), ("ban",)),
            ]
        )
