from datetime import date

from displacement_observatory.analysis.competing_explanations import (
    check_currency_effect,
    check_destination_demand_growth,
    check_hs_code_switching,
    check_price_vs_quantity,
)
from displacement_observatory.analysis.diD import EventDiDResult
from displacement_observatory.analysis.twfe import run_event_study
from displacement_observatory.register.schema import Citation, HS6Candidate, RestrictionEvent

EXPORTER = 251  # France
NON_EU_IMPORTER = 842  # USA
OTHER_EXPORTER = 156  # China (rest-of-world, not in exporter bloc)


def _make_result(hs6, effective_year, exporter_codes=(EXPORTER,)):
    event = RestrictionEvent(
        event_id="ev1",
        substance="Testicide",
        jurisdiction="EU",
        restriction_type="ban",
        scope="all",
        decision_date=date(effective_year - 1, 1, 1),
        effective_date=date(effective_year, 6, 1),
        citation=Citation(source_document="d", source_clause="c", retrieved_at=date(2026, 9, 18)),
        hs6_candidates=[HS6Candidate(hs6=hs6, confidence=0.5, reasoning="r", imprecision="i")],
    )
    years = range(effective_year - 5, effective_year + 6)  # inclusive of +5
    rows = [(f"c{i}", t, 1.0) for i in range(3) for t in years] + [("treated", t, 1.0) for t in years]
    study = run_event_study(rows, treated_unit="treated", effective_year=effective_year, window_years=5)
    return EventDiDResult(
        event=event, hs6=hs6, status="ok", exporter_codes=list(exporter_codes),
        n_control_units=0, study=study,
    )


def test_destination_demand_growth_detects_rest_of_world_rise(con):
    hs6 = "380810"
    result = _make_result(hs6, 2015)
    pre_years = [2012, 2013, 2014]
    post_years = [2015, 2016, 2017]
    rows = []
    for y in pre_years:
        rows.append((y, hs6, OTHER_EXPORTER, NON_EU_IMPORTER, 100.0, None, "BACI", "t", "2026-09-18 00:00:00"))
    for y in post_years:
        rows.append((y, hs6, OTHER_EXPORTER, NON_EU_IMPORTER, 200.0, None, "BACI", "t", "2026-09-18 00:00:00"))
    con.executemany("INSERT INTO trade_flows VALUES (?,?,?,?,?,?,?,?,?)", rows)

    growth, note = check_destination_demand_growth(con, result)
    assert growth is not None
    assert growth == 100.0  # doubled
    assert "general demand growth" in note


def test_destination_demand_growth_none_when_no_rest_of_world_trade(con):
    result = _make_result("380810", 2015)
    growth, note = check_destination_demand_growth(con, result)
    assert growth is None
    assert "no rest-of-world" in note


def test_currency_effect_flags_large_depreciation(con):
    result = _make_result("380810", 2020)
    change, note = check_currency_effect(result)
    assert change is not None
    # Real ECB data: EUR/USD in 2019 (decision_date.year-1=2019) to 2020 (no post-k since study is None -> end_year=eff_year)
    assert "EUR" in note


def test_hs_code_switching_flags_sibling_growth(con):
    hs6 = "380810"
    result = _make_result(hs6, 2015)
    pre_years = [2012, 2013, 2014]
    post_years = [2015, 2016, 2017]
    rows = []
    for y in pre_years:
        rows.append((y, "380830", EXPORTER, NON_EU_IMPORTER, 100.0, None, "BACI", "t", "2026-09-18 00:00:00"))
    for y in post_years:
        rows.append((y, "380830", EXPORTER, NON_EU_IMPORTER, 300.0, None, "BACI", "t", "2026-09-18 00:00:00"))
    con.executemany("INSERT INTO trade_flows VALUES (?,?,?,?,?,?,?,?,?)", rows)

    moves, note = check_hs_code_switching(con, result)
    assert moves["380830"] == 200.0
    assert "380830" in note


def test_price_vs_quantity_detects_price_driven_rise(con):
    hs6 = "380810"
    result = _make_result(hs6, 2015)
    result.study.coef[5] = 1.0  # pretend value effect at the headline k=+5 is large (log points)
    years = list(range(2010, 2021))
    rows = []
    for y in years:
        # control units: flat quantity
        for c in ["380891", "380892", "380893"]:
            rows.append((y, c, EXPORTER, NON_EU_IMPORTER, 100.0, 50.0, "BACI", "t", "2026-09-18 00:00:00"))
        # treated: quantity stays flat even though (hypothetically) value rose
        rows.append((y, hs6, EXPORTER, NON_EU_IMPORTER, 100.0, 50.0, "BACI", "t", "2026-09-18 00:00:00"))
    con.executemany("INSERT INTO trade_flows VALUES (?,?,?,?,?,?,?,?,?)", rows)

    avail, qty_coef, qty_ci, note = check_price_vs_quantity(con, result, ["380891", "380892", "380893"])
    assert avail is True
    assert abs(qty_coef) < 0.05  # flat quantity -> near-zero coefficient
    assert "price" in note or "not primarily a price story" in note
