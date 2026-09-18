import numpy as np
import pytest

from displacement_observatory.analysis.twfe import run_event_study

YEARS = list(range(2010, 2021))  # 11 years
EFFECTIVE_YEAR = 2015
WINDOW = 5


def _make_rows(n_control=60, true_effect=0.4, pretrend_slope=0.0, seed=0, noise_sd=0.01):
    rng = np.random.default_rng(seed)
    rows = []

    year_effect = {t: rng.normal(0, 0.05) for t in YEARS}

    for c in range(n_control):
        base = rng.normal(5.0, 1.0)
        for t in YEARS:
            v = base + year_effect[t] + rng.normal(0, noise_sd)
            rows.append((f"control_{c}", t, v))

    treated_base = rng.normal(5.0, 1.0)
    for t in YEARS:
        rel = t - EFFECTIVE_YEAR
        v = treated_base + year_effect[t] + rng.normal(0, noise_sd)
        if rel >= 0:
            v += true_effect
        if rel < 0:
            v += pretrend_slope * rel  # a slope here means values were already diverging pre-event
        rows.append(("treated", t, v))

    return rows


def test_recovers_known_injected_effect():
    rows = _make_rows(true_effect=0.4, pretrend_slope=0.0, seed=1)
    result = run_event_study(rows, treated_unit="treated", effective_year=EFFECTIVE_YEAR, window_years=WINDOW)

    post_coefs = [result.coef[k] for k in result.relative_years if k >= 0]
    assert all(abs(c - 0.4) < 0.1 for c in post_coefs), post_coefs

    pre_coefs = [result.coef[k] for k in result.relative_years if k < -1]
    assert all(abs(c) < 0.1 for c in pre_coefs), pre_coefs

    assert result.pretrend_flagged is False


def test_zero_effect_recovers_near_zero_coefficients():
    # Note: pretrend_flagged is a per-coefficient 5% significance test over
    # several pre-period coefficients, so it is *expected* to trip on some
    # fraction of true nulls by chance -- that's not asserted here. What
    # must hold regardless of that draw is that the estimated effect size
    # itself is small.
    rows = _make_rows(true_effect=0.0, pretrend_slope=0.0, seed=2)
    result = run_event_study(rows, treated_unit="treated", effective_year=EFFECTIVE_YEAR, window_years=WINDOW)

    all_coefs = [result.coef[k] for k in result.relative_years if k != -1]
    assert all(abs(c) < 0.1 for c in all_coefs), all_coefs


def test_pretrend_violation_is_flagged():
    # A strong pre-existing linear divergence between treated and control
    # before the event should trip the pre-trend flag.
    rows = _make_rows(true_effect=0.4, pretrend_slope=0.5, seed=3, noise_sd=0.005)
    result = run_event_study(rows, treated_unit="treated", effective_year=EFFECTIVE_YEAR, window_years=WINDOW)

    assert result.pretrend_flagged is True
    assert "significant" in result.pretrend_detail


def test_missing_treated_unit_raises():
    rows = [("control_0", 2015, 1.0), ("control_0", 2016, 1.0)]
    with pytest.raises(ValueError, match="not present"):
        run_event_study(rows, treated_unit="nope", effective_year=2015, window_years=2)


def test_duplicate_unit_year_raises():
    rows = [("treated", 2015, 1.0), ("treated", 2015, 2.0), ("control_0", 2015, 1.0), ("control_0", 2016, 1.0)]
    with pytest.raises(ValueError, match="duplicate"):
        run_event_study(rows, treated_unit="treated", effective_year=2015, window_years=1)


def test_relative_year_minus_one_is_the_zero_reference():
    rows = _make_rows(true_effect=0.4, seed=4)
    result = run_event_study(rows, treated_unit="treated", effective_year=EFFECTIVE_YEAR, window_years=WINDOW)
    assert result.coef[-1] == 0.0
    assert result.se[-1] == 0.0
