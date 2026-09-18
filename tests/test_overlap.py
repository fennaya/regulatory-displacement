from datetime import date

import pytest

from displacement_observatory.analysis.diD import EventDiDResult
from displacement_observatory.analysis.overlap import (
    Classification,
    build_overlap_matrix,
    classify_packages,
    compute_windows,
)
from displacement_observatory.analysis.packages import TreatmentPackage
from displacement_observatory.analysis.twfe import run_event_study
from displacement_observatory.register.schema import Citation, HS6Candidate, RestrictionEvent


def _study(effective_year, window_years=5):
    years = range(effective_year - window_years, effective_year + window_years + 1)
    rows = [(f"c{i}", t, 1.0) for i in range(10) for t in years] + [("treated", t, 1.0) for t in years]
    return run_event_study(rows, treated_unit="treated", effective_year=effective_year, window_years=window_years)


def _tested_result(event_id, hs6, effective_year, window_years=5):
    event = RestrictionEvent(
        event_id=event_id, substance="X", jurisdiction="EU", restriction_type="ban", scope="all",
        decision_date=date(effective_year - 1, 1, 1), effective_date=date(effective_year, 1, 1),
        citation=Citation(source_document="d", source_clause="c", retrieved_at=date(2026, 9, 18)),
        hs6_candidates=[HS6Candidate(hs6=hs6, confidence=0.5, reasoning="r", imprecision="i")],
    )
    return EventDiDResult(
        event=event, hs6=hs6, status="ok", exporter_codes=[251], n_control_units=10,
        study=_study(effective_year, window_years),
    )


def _untestable_result(event_id, hs6, effective_year):
    event = RestrictionEvent(
        event_id=event_id, substance="Y", jurisdiction="Global", restriction_type="ban", scope="all",
        decision_date=date(effective_year - 1, 1, 1), effective_date=date(effective_year, 1, 1),
        citation=Citation(source_document="d", source_clause="c", retrieved_at=date(2026, 9, 18)),
        hs6_candidates=[HS6Candidate(hs6=hs6, confidence=0.5, reasoning="r", imprecision="i")],
    )
    return EventDiDResult(event=event, hs6=hs6, status="skipped", reason="no exporter bloc", study=None)


def _pkg(package_id, hs6, effective_year, event_ids):
    return TreatmentPackage(
        package_id=package_id, jurisdiction="EU", hs6=hs6,
        decision_date=date(effective_year - 1, 1, 1), effective_date=date(effective_year, 1, 1),
        substances=("X",), event_ids=tuple(event_ids), restriction_types=("ban",),
    )


def test_overlapping_same_hs6_packages_are_flagged_and_sized():
    # earlier: effective 2010, window_years=5 -> [2005,2015]; later: effective 2013 -> overlap
    r_early = _tested_result("early", "999999", 2010, window_years=5)
    r_late = _tested_result("late", "999999", 2013, window_years=5)
    packages = [_pkg("early", "999999", 2010, ["early"]), _pkg("late", "999999", 2013, ["late"])]
    did_by_id = {"early": r_early, "late": r_late}

    windows = compute_windows(packages, did_by_id)
    flags = build_overlap_matrix(packages, windows, did_by_id)

    assert len(flags) == 1
    f = flags[0]
    assert f.earlier_package_id == "early"
    assert f.later_package_id == "late"
    # earlier post-period years: 2010..2015 (k=0..5); later effective year 2013
    # contaminated: years >= 2013 -> 2013,2014,2015 -> 3 of 6
    assert f.contaminated_years == [2013, 2014, 2015]
    assert f.total_post_period_ks == 6
    assert f.contamination_share == pytest.approx(0.5)


def test_non_overlapping_same_hs6_packages_are_clean():
    r_a = _tested_result("a", "999999", 2000, window_years=3)  # [1997,2003]
    r_b = _tested_result("b", "999999", 2010, window_years=3)  # [2007,2013]
    packages = [_pkg("a", "999999", 2000, ["a"]), _pkg("b", "999999", 2010, ["b"])]
    did_by_id = {"a": r_a, "b": r_b}

    windows = compute_windows(packages, did_by_id)
    flags = build_overlap_matrix(packages, windows, did_by_id)
    assert flags == []

    audits = classify_packages(windows, flags)
    assert {a.package_id: a.classification for a in audits} == {"a": Classification.CLEAN, "b": Classification.CLEAN}


def test_different_hs6_never_flagged_even_if_dates_overlap():
    r_a = _tested_result("a", "111111", 2010, window_years=5)
    r_b = _tested_result("b", "222222", 2011, window_years=5)
    packages = [_pkg("a", "111111", 2010, ["a"]), _pkg("b", "222222", 2011, ["b"])]
    did_by_id = {"a": r_a, "b": r_b}

    windows = compute_windows(packages, did_by_id)
    flags = build_overlap_matrix(packages, windows, did_by_id)
    assert flags == []


def test_untestable_later_package_flags_earlier_via_effective_date_point():
    r_early = _tested_result("early", "999999", 2006, window_years=5)  # [2001,2011]
    r_untestable = _untestable_result("late", "999999", 2011)  # effective year 2011, in [2001,2011]

    packages = [_pkg("early", "999999", 2006, ["early"]), _pkg("late", "999999", 2011, ["late"])]
    did_by_id = {"early": r_early, "late": r_untestable}

    windows = compute_windows(packages, did_by_id)
    flags = build_overlap_matrix(packages, windows, did_by_id)
    assert len(flags) == 1
    assert flags[0].earlier_package_id == "early"
    assert flags[0].later_package_id == "late"
    assert flags[0].contaminated_years == [2011]  # only the last year of the window

    audits = classify_packages(windows, flags)
    by_id = {a.package_id: a.classification for a in audits}
    assert by_id["early"] == Classification.CONTAMINATED
    assert by_id["late"] == Classification.UNTESTABLE  # untestable overrides even though it "caused" an overlap


def test_assert_clean_has_no_overlap_catches_inconsistency():
    from displacement_observatory.analysis.overlap import PackageWindow, _assert_clean_has_no_overlap, OverlapFlag, PackageAudit

    w = PackageWindow("p1", "999999", date(2010, 1, 1), tested=True, y0=2005, y1=2015)
    bogus_flag = OverlapFlag("p1", "p2", "999999", (2005, 2015), 2013, [2013], [3, 4, 5], 6)
    audits = [PackageAudit(package_id="p1", classification=Classification.CLEAN, window=w, overlaps=[bogus_flag])]
    with pytest.raises(AssertionError, match="classified CLEAN"):
        _assert_clean_has_no_overlap(audits)
