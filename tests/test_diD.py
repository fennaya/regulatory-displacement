from datetime import date

import numpy as np

from displacement_observatory.analysis.diD import run_event_did
from displacement_observatory.register.schema import Citation, HS6Candidate, RestrictionEvent
from displacement_observatory.register.store import RegisterLoadResult

EXPORTER_EU = 251  # France (BACI code)
IMPORTER_NON_EU = 842  # USA
IMPORTER_EU = 276  # Germany


def _make_event(event_id, hs6, effective_year, jurisdiction="EU"):
    return RestrictionEvent(
        event_id=event_id,
        substance="Testicide",
        jurisdiction=jurisdiction,
        restriction_type="ban",
        scope="all uses",
        decision_date=date(effective_year - 1, 1, 1),
        effective_date=date(effective_year, 6, 1),
        citation=Citation(source_document="Test Reg", source_clause="Art 1", retrieved_at=date(2026, 9, 18)),
        hs6_candidates=[HS6Candidate(hs6=hs6, confidence=0.5, reasoning="t", imprecision="t")],
    )


def _seed_trade_flows(con, years, control_hs6_list, treated_hs6, effective_year, post_bump=0.6):
    rng = np.random.default_rng(42)
    rows = []
    for hs6 in [treated_hs6, *control_hs6_list]:
        base = rng.uniform(50, 200)
        for y in years:
            v = base * (1 + rng.normal(0, 0.05))
            if hs6 == treated_hs6 and y >= effective_year:
                v *= (1 + post_bump)
            rows.append((y, hs6, EXPORTER_EU, IMPORTER_NON_EU, v, None, "BACI", "test", "2026-09-18 00:00:00"))
            # also add some intra-EU trade that must be excluded from the DiD
            rows.append((y, hs6, EXPORTER_EU, IMPORTER_EU, v * 3, None, "BACI", "test", "2026-09-18 00:00:00"))
    con.executemany(
        "INSERT INTO trade_flows VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", rows
    )
    con.executemany(
        "INSERT INTO countries (country_code, country_name, country_iso3, source, source_version) VALUES (?, ?, ?, ?, ?)",
        [
            (EXPORTER_EU, "France", "FRA", "BACI", "test"),
            (IMPORTER_EU, "Germany", "DEU", "BACI", "test"),
            (IMPORTER_NON_EU, "USA", "USA", "BACI", "test"),
        ],
    )


def test_run_event_did_excludes_intra_eu_flows_and_recovers_bump(con):
    years = list(range(2010, 2021))
    control_hs6 = [f"38089{i}" for i in range(5)]
    treated_hs6 = "380810"
    _seed_trade_flows(con, years, control_hs6, treated_hs6, effective_year=2015, post_bump=0.8)

    event = _make_event("test-event", treated_hs6, 2015)
    register = RegisterLoadResult(events=[event], dropped=[])

    result = run_event_did(con, event, register, window_years=4, source="BACI", source_version="test")

    assert result.status == "ok"
    assert EXPORTER_EU in result.exporter_codes
    assert IMPORTER_EU in result.exporter_codes  # Germany is also EU -- both should resolve as exporters
    post_coefs = [result.study.coef[k] for k in result.study.relative_years if k >= 0]
    assert all(c > 0 for c in post_coefs), post_coefs


def test_run_event_did_clips_window_to_panel_coverage(con):
    years = list(range(2010, 2019))  # panel stops at 2018
    control_hs6 = [f"38089{i}" for i in range(5)]
    treated_hs6 = "380810"
    _seed_trade_flows(con, years, control_hs6, treated_hs6, effective_year=2017, post_bump=0.5)

    event = _make_event("test-event-2", treated_hs6, 2017)
    register = RegisterLoadResult(events=[event], dropped=[])

    # window_years=5 would ask for 2012-2022, but the panel only has 2010-2018.
    result = run_event_did(con, event, register, window_years=5, source="BACI", source_version="test")

    assert result.status == "ok"
    assert max(result.study.relative_years) == 1  # 2018 - 2017, not 5
    assert min(result.study.relative_years) == -5  # 2012 - 2017 is available


def test_run_event_did_skips_undefined_jurisdiction(con):
    event = _make_event("test-event-3", "380810", 2015, jurisdiction="Global (some treaty)")
    register = RegisterLoadResult(events=[event], dropped=[])
    result = run_event_did(con, event, register, window_years=4)
    assert result.status == "skipped"
    assert "does not resolve" in result.reason


def test_run_event_did_flags_same_hs6_contamination(con):
    years = list(range(2010, 2021))
    control_hs6 = [f"38089{i}" for i in range(5)]
    treated_hs6 = "380810"
    _seed_trade_flows(con, years, control_hs6, treated_hs6, effective_year=2015, post_bump=0.5)

    event_a = _make_event("event-a", treated_hs6, 2015)
    event_b = _make_event("event-b", treated_hs6, 2016)  # same hs6, 1 year later -- contaminates
    register = RegisterLoadResult(events=[event_a, event_b], dropped=[])

    result = run_event_did(con, event_a, register, window_years=4, source="BACI", source_version="test")
    assert result.same_hs6_contaminating_events == ["event-b"]
