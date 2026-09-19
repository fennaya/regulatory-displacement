import numpy as np
import pandas as pd
import pytest

from displacement_observatory.analysis.basket_attack import (
    build_hs6_year_bloc_panel,
    placebo_distribution,
    placebo_two_sided_p,
    to_outcome_frame,
    twfe_att_balanced,
)
from displacement_observatory.analysis.staggered import fit_staggered

YEARS = list(range(1995, 2025))


def _bloc_frame(seed, eu_specific=0.5, common=0.3, n_never=40, noise=0.1):
    """Two treated codes (cohorts 2004, 2006). Treated codes get a shared
    product-specific shock `common` in BOTH blocs plus `eu_specific` in the
    EU bloc only. Never-treated codes are flat."""
    rng = np.random.default_rng(seed)
    rows = []
    year_fe = {t: rng.normal(0, 0.2) for t in YEARS}
    spec = [(f"never_{i}", 0) for i in range(n_never)] + [("t_a", 2004), ("t_b", 2006)]
    for h, g in spec:
        base_eu, base_row = rng.normal(5, 1), rng.normal(5, 1)
        for t in YEARS:
            eu = base_eu + year_fe[t] + rng.normal(0, noise)
            rw = base_row + year_fe[t] + rng.normal(0, noise)
            if g and t >= g:
                eu += common + eu_specific
                rw += common
            rows.append((h, t, np.expm1(eu), np.expm1(rw), g))
    return pd.DataFrame(rows, columns=["hs6", "year", "eu", "row", "gname"])


def test_twfe_att_balanced_matches_pyfixest_twfe():
    bloc = _bloc_frame(0)
    df = to_outcome_frame(bloc, "eu")
    mine = twfe_att_balanced(df)
    theirs = fit_staggered(df, estimator="twfe").coef
    assert mine == pytest.approx(theirs, abs=1e-6)


def test_eu_only_outcome_includes_common_shock_triple_removes_it():
    eu_only, triple = [], []
    for s in range(6):
        b = _bloc_frame(s)
        eu_only.append(twfe_att_balanced(to_outcome_frame(b, "eu")))
        triple.append(twfe_att_balanced(to_outcome_frame(b, "triple")))
    assert abs(np.mean(eu_only) - 0.8) < 0.12     # common 0.3 + EU-specific 0.5
    assert abs(np.mean(triple) - 0.5) < 0.12      # EU-specific only


def test_row_outcome_recovers_only_the_common_shock():
    est = np.mean([twfe_att_balanced(to_outcome_frame(_bloc_frame(s), "row")) for s in range(6)])
    assert abs(est - 0.3) < 0.1


def test_placebo_distribution_is_centered_and_real_effect_is_extreme():
    b = _bloc_frame(1)
    df = to_outcome_frame(b, "eu")
    never = [h for h in df["hs6"].unique() if h.startswith("never_")]
    placebos = placebo_distribution(df, never, cohorts=[2004, 2006], n_draws=300, seed=1)
    assert abs(placebos.mean()) < 0.05
    real = twfe_att_balanced(df)
    assert placebo_two_sided_p(real, placebos) < 0.02


def test_placebo_p_is_unremarkable_under_a_true_null():
    b = _bloc_frame(2, eu_specific=0.0, common=0.0)
    df = to_outcome_frame(b, "eu")
    never = [h for h in df["hs6"].unique() if h.startswith("never_")]
    placebos = placebo_distribution(df, never, cohorts=[2004, 2006], n_draws=300, seed=2)
    real = twfe_att_balanced(df)
    assert placebo_two_sided_p(real, placebos) > 0.05


def test_placebo_p_never_zero():
    assert placebo_two_sided_p(100.0, np.zeros(99)) == pytest.approx(1 / 100)


def test_unknown_mode_and_measure_raise(con):
    with pytest.raises(ValueError):
        to_outcome_frame(pd.DataFrame({"hs6": [], "year": [], "gname": [], "eu": [], "row": []}), "bogus")
    with pytest.raises(ValueError):
        build_hs6_year_bloc_panel(con, ["380810"], {}, 2010, 2011, measure="bogus")


def test_build_bloc_panel_splits_eu_and_row_and_zero_fills(con):
    con.executemany(
        "INSERT INTO countries (country_code, country_name, country_iso3, source, source_version) VALUES (?,?,?,?,?)",
        [(251, "France", "FRA", "BACI", "t"), (276, "Germany", "DEU", "BACI", "t"),
         (156, "China", "CHN", "BACI", "t"), (842, "USA", "USA", "BACI", "t")],
    )
    rows = [
        (2010, "380810", 251, 842, 100.0, 5.0, "BACI", "t", "2026-01-01 00:00:00"),   # EU -> USA
        (2010, "380810", 251, 276, 999.0, 9.0, "BACI", "t", "2026-01-01 00:00:00"),   # EU -> EU: excluded
        (2010, "380810", 156, 842, 40.0, 2.0, "BACI", "t", "2026-01-01 00:00:00"),    # RoW -> USA
        (2010, "380810", 156, 276, 7.0, 1.0, "BACI", "t", "2026-01-01 00:00:00"),     # RoW -> EU: excluded
    ]
    con.executemany("INSERT INTO trade_flows VALUES (?,?,?,?,?,?,?,?,?)", rows)
    df = build_hs6_year_bloc_panel(con, ["380810", "380820"], {"380810": 2010}, 2010, 2011, "BACI", "t")
    r = df[(df.hs6 == "380810") & (df.year == 2010)].iloc[0]
    assert (r.eu, r.row, r.gname) == (100.0, 40.0, 2010)
    assert df[(df.hs6 == "380810") & (df.year == 2011)].iloc[0].eu == 0.0
    assert (df[df.hs6 == "380820"][["eu", "row"]] == 0).all().all()
    q = build_hs6_year_bloc_panel(con, ["380810"], {}, 2010, 2010, "BACI", "t", measure="quantity_tons")
    assert (q.iloc[0].eu, q.iloc[0].row) == (5.0, 2.0)
