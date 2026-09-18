from datetime import date

import numpy as np

from displacement_observatory.analysis.diD import EventDiDResult
from displacement_observatory.analysis.twfe import run_event_study
from displacement_observatory.register.schema import Citation, HS6Candidate, RestrictionEvent
from displacement_observatory.validation.rediscovery import CaseCheck, RediscoverySummary, check_case, load_known_cases


def _fake_result(event_id, hs6, effective_year, bump, seed=0):
    rng = np.random.default_rng(seed)
    event = RestrictionEvent(
        event_id=event_id, substance="X", jurisdiction="EU", restriction_type="ban", scope="all",
        decision_date=date(effective_year - 1, 1, 1), effective_date=date(effective_year, 6, 1),
        citation=Citation(source_document="d", source_clause="c", retrieved_at=date(2026, 9, 18)),
        hs6_candidates=[HS6Candidate(hs6=hs6, confidence=0.5, reasoning="r", imprecision="i")],
    )
    years = range(effective_year - 3, effective_year + 4)
    rows = [(f"c{i}", t, 1.0 + rng.normal(0, 0.3)) for i in range(20) for t in years]
    rows += [("treated", t, 1.0 + (bump if t >= effective_year else 0.0) + rng.normal(0, 0.3)) for t in years]
    study = run_event_study(rows, treated_unit="treated", effective_year=effective_year, window_years=3)
    return EventDiDResult(event=event, hs6=hs6, status="ok", exporter_codes=[251], n_control_units=20, study=study)


def test_load_known_cases_has_expected_structure():
    cases = load_known_cases()
    assert len(cases) >= 3
    in_scope = [c for c in cases if c["matches_register_event_id"] is not None]
    out_of_scope = [c for c in cases if c["matches_register_event_id"] is None]
    assert len(in_scope) >= 3
    assert len(out_of_scope) >= 2


def test_check_case_directional_hit_no_significance():
    case = {
        "case_id": "test-case", "substance": "X", "expected_direction": "positive",
        "matches_register_event_id": "ev1",
    }
    result = _fake_result("ev1", "380810", 2015, bump=0.3, seed=1)  # positive but within noise -> not significant
    check = check_case(case, {"ev1": result})
    assert check.in_scope is True
    assert check.directional_hit is True
    assert check.significant_hit is False


def test_check_case_wrong_direction():
    case = {
        "case_id": "test-case", "substance": "X", "expected_direction": "positive",
        "matches_register_event_id": "ev1",
    }
    result = _fake_result("ev1", "380810", 2015, bump=-2.0)  # large negative bump
    check = check_case(case, {"ev1": result})
    assert check.directional_hit is False
    assert check.significant_hit is False


def test_check_case_out_of_scope():
    case = {"case_id": "oos", "substance": None, "expected_direction": None, "matches_register_event_id": None}
    check = check_case(case, {})
    assert check.in_scope is False
    assert check.directional_hit is None


def test_summary_recall_excludes_out_of_scope():
    checks = [
        CaseCheck("a", "X", True, "ev1", 3, 0.5, (0.1, 0.9), True, True, "hit"),
        CaseCheck("b", "Y", True, "ev2", 3, 0.5, (-0.1, 0.9), True, False, "directional only"),
        CaseCheck("c", None, False, None, None, None, None, None, None, "out of scope"),
    ]
    summary = RediscoverySummary(checks=checks)
    assert summary.directional_recall == 1.0
    assert summary.significant_recall == 0.5
    assert "out of scope" in summary.report()
