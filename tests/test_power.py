import math

import pytest

from displacement_observatory.analysis.power import (
    BasketShareAssumption,
    compute_mde,
    evaluate_package,
    implied_log_effect_if_fully_displaced,
)


def test_compute_mde_matches_textbook_2point8_rule():
    # The well-known approximation: at alpha=0.05, power=0.80, the
    # multiplier (z_0.975 + z_0.80) is approximately 2.8.
    se = 1.0
    mde = compute_mde(se, alpha=0.05, power=0.80)
    assert abs(mde - 2.8014) < 0.01


def test_compute_mde_scales_linearly_with_se():
    assert compute_mde(2.0) == pytest.approx(2 * compute_mde(1.0))


def test_compute_mde_higher_power_needs_larger_mde():
    assert compute_mde(1.0, power=0.90) > compute_mde(1.0, power=0.80)


def test_implied_effect_small_share_approximates_share_itself():
    # -log(1-s) ~= s for small s
    s = 0.02
    assert abs(implied_log_effect_if_fully_displaced(s) - s) < 0.001


def test_implied_effect_larger_share_exceeds_linear_approximation():
    s = 0.5
    exact = implied_log_effect_if_fully_displaced(s)
    assert exact > s  # -log(0.5) = 0.693 > 0.5
    assert abs(exact - math.log(2)) < 1e-9


def test_implied_effect_rejects_invalid_share():
    with pytest.raises(ValueError):
        implied_log_effect_if_fully_displaced(1.0)
    with pytest.raises(ValueError):
        implied_log_effect_if_fully_displaced(-0.1)


def test_evaluate_package_not_detectable_when_se_large_and_share_small():
    assumption = BasketShareAssumption("p1", "X", share_low=0.02, share_high=0.05, basis="test", confidence="test")
    result = evaluate_package("p1", clustered_se=0.5, assumption=assumption)  # MDE ~= 1.4
    assert result.detectable_at_low_share is False
    assert result.detectable_at_high_share is False
    assert "NOT DETECTABLE" in result.verdict


def test_evaluate_package_detectable_when_se_small_and_share_large():
    assumption = BasketShareAssumption("p1", "X", share_low=0.3, share_high=0.6, basis="test", confidence="test")
    result = evaluate_package("p1", clustered_se=0.05, assumption=assumption)  # MDE ~= 0.14
    assert result.detectable_at_low_share is True
    assert result.detectable_at_high_share is True
    assert "DETECTABLE" in result.verdict and "NOT" not in result.verdict


def test_evaluate_package_borderline():
    # MDE ~= 2.8 * 0.1 = 0.28; implied at share_low=0.1 -> 0.105 (below),
    # implied at share_high=0.35 -> 0.431 (above)
    assumption = BasketShareAssumption("p1", "X", share_low=0.10, share_high=0.35, basis="test", confidence="test")
    result = evaluate_package("p1", clustered_se=0.10, assumption=assumption)
    assert result.detectable_at_low_share is False
    assert result.detectable_at_high_share is True
    assert "BORDERLINE" in result.verdict
