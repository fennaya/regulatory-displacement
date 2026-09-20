"""The register's event dates and the dates consumed by the overlap audit must be the same value for every event.
A silent mismatch (e.g. 2008 in the register, 2011 in the analysis) is invisible without this test."""
from types import SimpleNamespace

from displacement_observatory.analysis.overlap import compute_windows
from displacement_observatory.analysis.packages import build_treatment_packages
from displacement_observatory.register.store import load_events


def test_register_dates_equal_package_dates_equal_overlap_audit_dates_for_every_event():
    reg = load_events(version=1)
    packages = build_treatment_packages(reg)
    by_event = {eid: p for p in packages for eid in p.event_ids}
    assert set(by_event) == {e.event_id for e in reg.events}
    # stub "untestable" results: compute_windows then takes each window's date from the package it was handed
    stub = {e.event_id: SimpleNamespace(status="untestable", study=None) for e in reg.events}
    windows = {w.package_id: w for w in compute_windows(packages, stub)}
    for e in reg.events:
        p = by_event[e.event_id]
        assert p.effective_date == e.effective_date and p.decision_date == e.decision_date, e.event_id
        assert windows[p.package_id].effective_date == e.effective_date, e.event_id


def test_rotterdam_endosulfan_is_dated_2011_not_2008():
    reg = load_events(version=1)
    e = next(x for x in reg.events if x.event_id == "rotterdam-2011-endosulfan")
    assert (e.decision_date.isoformat(), e.effective_date.isoformat()) == ("2011-06-24", "2011-10-24")
    assert "COP-4-9" not in e.citation.url and "RC-5/5" in e.citation.source_document
