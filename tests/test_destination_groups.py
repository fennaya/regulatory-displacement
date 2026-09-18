import pytest

from displacement_observatory.analysis.destination_groups import (
    DESTINATION_GROUPS_PATH,
    load_destination_groups,
    resolve_iso3_to_codes,
    run_event_study_for_destination_group,
)

EXPORTER = 251  # France
HIGH_EXPOSURE_DEST = 76  # Brazil
LOW_EXPOSURE_DEST = 36  # Australia


def test_load_destination_groups_from_real_committed_file():
    groups = load_destination_groups()
    assert groups.version == 1
    assert "BRA" in groups.high_exposure_iso3
    assert "UKR" in groups.high_exposure_iso3
    assert "CHE" in groups.low_exposure_iso3
    assert set(groups.high_exposure_iso3).isdisjoint(groups.low_exposure_iso3)


def test_resolve_iso3_to_codes(con):
    con.execute(
        "INSERT INTO countries (country_code, country_name, country_iso3, source, source_version) VALUES "
        "(76,'Brazil','BRA','BACI','t'), (36,'Australia','AUS','BACI','t')"
    )
    codes = resolve_iso3_to_codes(con, ["BRA", "AUS"], "BACI", "t")
    assert set(codes) == {76, 36}


def test_resolve_iso3_to_codes_empty_list_returns_empty(con):
    assert resolve_iso3_to_codes(con, [], "BACI", "t") == []


def _seed_group_flows(con, years, control_hs6_list, treated_hs6, effective_year, high_bump, low_bump):
    import numpy as np
    rng = np.random.default_rng(0)
    rows = []
    for hs6 in [treated_hs6, *control_hs6_list]:
        base_high = rng.uniform(80, 150)
        base_low = rng.uniform(80, 150)
        for y in years:
            hv = base_high * (1 + rng.normal(0, 0.03))
            lv = base_low * (1 + rng.normal(0, 0.03))
            if hs6 == treated_hs6 and y >= effective_year:
                hv *= (1 + high_bump)
                lv *= (1 + low_bump)
            rows.append((y, hs6, EXPORTER, HIGH_EXPOSURE_DEST, hv, None, "BACI", "t", "2026-09-18 00:00:00"))
            rows.append((y, hs6, EXPORTER, LOW_EXPOSURE_DEST, lv, None, "BACI", "t", "2026-09-18 00:00:00"))
    con.executemany("INSERT INTO trade_flows VALUES (?,?,?,?,?,?,?,?,?)", rows)


def test_high_exposure_group_shows_larger_effect_than_low_exposure(con):
    years = list(range(2010, 2021))
    control_hs6 = [f"38089{i}" for i in range(5)]
    treated_hs6 = "380810"
    _seed_group_flows(con, years, control_hs6, treated_hs6, effective_year=2015, high_bump=1.0, low_bump=0.0)

    high_study = run_event_study_for_destination_group(
        con, treated_hs6, control_hs6, [EXPORTER], [HIGH_EXPOSURE_DEST], 2010, 2020, 2015, window_years=5,
    )
    low_study = run_event_study_for_destination_group(
        con, treated_hs6, control_hs6, [EXPORTER], [LOW_EXPOSURE_DEST], 2010, 2020, 2015, window_years=5,
    )
    assert high_study.coef[5] > low_study.coef[5]
    assert high_study.coef[5] > 0.3
    assert abs(low_study.coef[5]) < 0.3


def test_empty_destination_codes_raises(con):
    with pytest.raises(ValueError, match="empty destination_codes"):
        run_event_study_for_destination_group(con, "380810", [], [EXPORTER], [], 2010, 2020, 2015, 5)
