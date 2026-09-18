from datetime import date

import numpy as np
import pytest

from displacement_observatory.analysis.diD import EventDiDResult
from displacement_observatory.analysis.triple_diff import build_triple_diff_rows, run_triple_diff
from displacement_observatory.analysis.twfe import run_event_study
from displacement_observatory.register.schema import Citation, HS6Candidate, RestrictionEvent

EU_EXPORTER = 251  # France
ROW_EXPORTER = 156  # China
IMPORTER = 842  # USA -- "unrestricted destination"


def _synthetic_diff_rows(common_shock=0.3, eu_specific=0.5, seed=0, n_control=60, years=range(2010, 2021), eff_year=2015):
    rng = np.random.default_rng(seed)
    data = {}
    for bloc in ["EU", "RoW"]:
        for c in range(n_control):
            base = rng.normal(5, 1)
            for t in years:
                data[(bloc, f"control_{c}", t)] = base + rng.normal(0, 0.1)
        base = rng.normal(5, 1)
        for t in years:
            v = base + rng.normal(0, 0.1)
            if t >= eff_year:
                v += common_shock
                if bloc == "EU":
                    v += eu_specific
            data[(bloc, "treated", t)] = v

    products = [f"control_{c}" for c in range(n_control)] + ["treated"]
    return [(p, t, data[("EU", p, t)] - data[("RoW", p, t)]) for p in products for t in years]


def test_differenced_design_recovers_eu_specific_effect_netting_out_common_shock():
    # Average over seeds: a single draw carries real sampling noise (see
    # analysis/triple_diff.py's module docstring for the empirical check
    # that motivated this design over naive pooling).
    avg_posts = []
    for seed in range(8):
        rows = _synthetic_diff_rows(common_shock=0.3, eu_specific=0.5, seed=seed)
        study = run_event_study(rows, treated_unit="treated", effective_year=2015, window_years=5)
        post_ks = [k for k in study.relative_years if k >= 0]
        avg_posts.append(sum(study.coef[k] for k in post_ks) / len(post_ks))
    mean_effect = sum(avg_posts) / len(avg_posts)
    assert abs(mean_effect - 0.5) < 0.15, avg_posts


def test_naive_pooled_design_does_NOT_net_out_the_common_shock():
    # Documents the failure mode this module's design deliberately avoids:
    # pooling EU+RoW rows as plain units (not differencing first) leaves
    # the common product-specific shock largely intact in the recovered
    # coefficient, because it gets diluted across dozens of unaffected
    # control units rather than differenced against the one series that
    # actually shares it (RoW::treated).
    years = range(2010, 2021)
    eff_year = 2015
    n_control = 30

    def naive_coef_at_5(seed):
        rng = np.random.default_rng(seed)
        data = {}
        for bloc in ["EU", "RoW"]:
            for c in range(n_control):
                base = rng.normal(5, 1)
                for t in years:
                    data[(bloc, f"control_{c}", t)] = base + rng.normal(0, 0.1)
            base = rng.normal(5, 1)
            for t in years:
                v = base + rng.normal(0, 0.1)
                if t >= eff_year:
                    v += 0.3
                    if bloc == "EU":
                        v += 0.5
                data[(bloc, "treated", t)] = v
        pooled_rows = [(f"{bloc}::{p}", t, v) for (bloc, p, t), v in data.items()]
        naive = run_event_study(pooled_rows, treated_unit="EU::treated", effective_year=eff_year, window_years=5)
        return naive.coef[5]

    # naive pooling should land much closer to the UN-netted 0.8 (0.3 common
    # + 0.5 EU-specific) than to the true EU-specific 0.5 -- this is the
    # failure this test documents, not a design goal. Averaged over seeds
    # for the same reason as the "correct design" test above.
    mean_naive = sum(naive_coef_at_5(s) for s in range(8)) / 8
    assert mean_naive > 0.65, mean_naive


def _seed_bloc_trade_flows(con, years, control_hs6_list, treated_hs6, effective_year, common_shock, eu_specific):
    rng = np.random.default_rng(7)
    rows = []
    for hs6 in [treated_hs6, *control_hs6_list]:
        eu_base = rng.uniform(80, 150)
        row_base = rng.uniform(80, 150)
        for y in years:
            eu_v = eu_base * (1 + rng.normal(0, 0.03))
            row_v = row_base * (1 + rng.normal(0, 0.03))
            if hs6 == treated_hs6 and y >= effective_year:
                eu_v *= (1 + common_shock + eu_specific)
                row_v *= (1 + common_shock)
            rows.append((y, hs6, EU_EXPORTER, IMPORTER, eu_v, None, "BACI", "test", "2026-09-18 00:00:00"))
            rows.append((y, hs6, ROW_EXPORTER, IMPORTER, row_v, None, "BACI", "test", "2026-09-18 00:00:00"))
    con.executemany("INSERT INTO trade_flows VALUES (?,?,?,?,?,?,?,?,?)", rows)
    con.executemany(
        "INSERT INTO countries (country_code, country_name, country_iso3, source, source_version) VALUES (?,?,?,?,?)",
        [
            (EU_EXPORTER, "France", "FRA", "BACI", "test"),
            (ROW_EXPORTER, "China", "CHN", "BACI", "test"),
            (IMPORTER, "USA", "USA", "BACI", "test"),
        ],
    )


def _make_event(hs6, effective_year):
    return RestrictionEvent(
        event_id="ev1", substance="X", jurisdiction="EU", restriction_type="ban", scope="all",
        decision_date=date(effective_year - 1, 1, 1), effective_date=date(effective_year, 1, 1),
        citation=Citation(source_document="d", source_clause="c", retrieved_at=date(2026, 9, 18)),
        hs6_candidates=[HS6Candidate(hs6=hs6, confidence=0.5, reasoning="r", imprecision="i")],
    )


def test_run_triple_diff_on_db_backed_panel_nets_out_common_growth(con):
    years = list(range(2010, 2021))
    control_hs6 = [f"38089{i}" for i in range(5)]
    treated_hs6 = "380810"
    _seed_bloc_trade_flows(con, years, control_hs6, treated_hs6, effective_year=2015, common_shock=0.5, eu_specific=0.6)

    event = _make_event(treated_hs6, 2015)
    result = EventDiDResult(
        event=event, hs6=treated_hs6, status="ok", exporter_codes=[EU_EXPORTER], n_control_units=len(control_hs6),
        study=run_event_study(
            [(h, y, 1.0) for h in [treated_hs6, *control_hs6] for y in years], treated_unit=treated_hs6,
            effective_year=2015, window_years=5,
        ),
    )

    triple = run_triple_diff(con, result, control_hs6, window_years=5)
    post_ks = [k for k in triple.study.relative_years if k >= 0]
    avg_post = sum(triple.study.coef[k] for k in post_ks) / len(post_ks)
    # true EU-specific log effect is log(1.6/1.5) - ish, not the full common+specific
    # bump -- just check it's well below the naive combined magnitude and positive.
    assert 0 < avg_post < 0.5, avg_post


def test_run_triple_diff_raises_on_non_ok_result(con):
    event = _make_event("380810", 2015)
    bad_result = EventDiDResult(event=event, hs6="380810", status="skipped", reason="test", study=None)
    with pytest.raises(ValueError, match="non-ok"):
        run_triple_diff(con, bad_result, [])
