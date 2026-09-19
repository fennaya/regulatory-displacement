import numpy as np
import pytest

from displacement_observatory.analysis.power import BasketShareAssumption
from displacement_observatory.analysis.power_placebo import PlacebosResult, placebo_se, recompute_power

EXPORTERS = [251, 276]
IMPORTER = 842
YEARS = list(range(2005, 2016))
EFF = 2010
TREATED = "380810"
CONTROLS = [f"38089{i}" for i in range(8)]


def _seed(con, control_noise, bump=0.6, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for exp in EXPORTERS:
        for code in [TREATED, *CONTROLS]:
            base = rng.uniform(80, 150)
            level = 0.0
            for y in YEARS:
                # controls carry a persistent random-walk shock of size control_noise; the treated code is quiet
                if code != TREATED:
                    level += rng.normal(0, control_noise)
                v = base * np.exp(level + rng.normal(0, 0.01))
                if code == TREATED and y >= EFF:
                    v *= (1 + bump)
                rows.append((y, code, exp, IMPORTER, float(v), None, "BACI", "t", "2026-09-19 00:00:00"))
    con.executemany("INSERT INTO trade_flows VALUES (?,?,?,?,?,?,?,?,?)", rows)


def test_one_placebo_per_pool_member_and_real_effect_recovered(con):
    _seed(con, control_noise=0.02, bump=0.6)
    res = placebo_se(con, TREATED, CONTROLS, EXPORTERS, YEARS[0], YEARS[-1], EFF)
    assert res.n_placebos == len(CONTROLS) == len(res.placebo_atts)
    assert abs(res.real_att - np.log(1.6)) < 0.08
    assert abs(np.mean(res.placebo_atts)) < 0.15  # placebos centre near zero


def test_placebo_se_grows_with_control_volatility(con):
    _seed(con, control_noise=0.02, seed=1)
    quiet = placebo_se(con, TREATED, CONTROLS, EXPORTERS, YEARS[0], YEARS[-1], EFF).se
    con.execute("DELETE FROM trade_flows")
    _seed(con, control_noise=0.30, seed=1)
    loud = placebo_se(con, TREATED, CONTROLS, EXPORTERS, YEARS[0], YEARS[-1], EFF).se
    assert loud > 5 * quiet


def test_real_att_is_dropped_out_of_the_placebo_pool(con):
    _seed(con, control_noise=0.02, bump=2.0)  # a huge real effect must not leak into any placebo
    res = placebo_se(con, TREATED, CONTROLS, EXPORTERS, YEARS[0], YEARS[-1], EFF)
    assert max(abs(x) for x in res.placebo_atts) < 0.3
    assert res.real_att > 0.8


def test_needs_enough_controls(con):
    with pytest.raises(ValueError, match="at least 3"):
        placebo_se(con, TREATED, CONTROLS[:2], EXPORTERS, YEARS[0], YEARS[-1], EFF)


def test_recompute_power_direction_and_verdicts():
    a = BasketShareAssumption("p", "X", share_low=0.10, share_high=0.30, basis="t", confidence="t")
    narrow_stage_e = 0.10   # MDE ~ 0.28: detectable when share_high implies 0.357
    wide_placebo = PlacebosResult("380810", 0.2, [0.0] * 3, se=0.50, n_placebos=3)  # MDE ~ 1.4
    r = recompute_power("p", narrow_stage_e, wide_placebo, a)
    assert r.placebo_se_is_wider is True
    assert r.placebo_mde > r.stage_e_mde
    assert "BORDERLINE" in r.stage_e_verdict.verdict
    assert "NOT DETECTABLE" in r.placebo_verdict.verdict


def test_recompute_power_flags_when_placebo_is_narrower():
    a = BasketShareAssumption("p", "X", share_low=0.10, share_high=0.30, basis="t", confidence="t")
    r = recompute_power("p", 0.5, PlacebosResult("x", 0.0, [0.0] * 3, se=0.1, n_placebos=3), a)
    assert r.placebo_se_is_wider is False   # the direction claim is checked, not assumed
