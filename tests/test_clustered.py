import numpy as np
import pytest

from displacement_observatory.analysis.clustered import fit_ols_with_cluster_robust_se

YEARS = range(2010, 2021)
EFF_YEAR = 2015


def _make_rows(seed, true_effect=0.5, n_treated=25, n_control=200, rho=0.8, iid=False):
    rng = np.random.default_rng(seed)
    rows = []
    for group, n, treated in [("treated", n_treated, True), ("control", n_control, False)]:
        for c in range(n):
            base = rng.normal(5, 1)
            persistent = 0.0
            for t in YEARS:
                if iid:
                    shock = rng.normal(0, 0.3)
                else:
                    persistent = rho * persistent + rng.normal(0, 0.3)
                    shock = persistent
                v = base + shock
                if treated and t >= EFF_YEAR:
                    v += true_effect
                rows.append((f"{group}_{c}", t, v, treated))
    return rows


def test_recovers_known_effect_with_multiple_treated_clusters():
    coefs = [fit_ols_with_cluster_robust_se(_make_rows(s), effective_year=EFF_YEAR).coef for s in range(5)]
    assert abs(sum(coefs) / len(coefs) - 0.5) < 0.1, coefs


def test_clustered_se_wider_than_classical_under_serial_correlation():
    # With genuine AR(1) within-cluster correlation and many treated
    # clusters, cluster-robust SEs should exceed classical SEs -- this is
    # the whole point of Stage E, not an incidental property.
    results = [fit_ols_with_cluster_robust_se(_make_rows(s, rho=0.8), effective_year=EFF_YEAR) for s in range(5)]
    ratios = [r.se_clustered / r.se_classical for r in results]
    assert all(ratio > 1.2 for ratio in ratios), ratios


def test_clustered_se_close_to_classical_when_errors_are_iid():
    # Sanity check: clustering shouldn't spuriously inflate SEs when there
    # is no actual within-cluster correlation to correct for.
    results = [fit_ols_with_cluster_robust_se(_make_rows(s, iid=True), effective_year=EFF_YEAR) for s in range(5)]
    ratios = [r.se_clustered / r.se_classical for r in results]
    mean_ratio = sum(ratios) / len(ratios)
    assert 0.6 < mean_ratio < 1.5, ratios


def test_single_cluster_degenerate_case_documented():
    # A single treated cluster makes cluster-robust SEs unreliable (the
    # "meat" matrix's treated-coefficient entry is driven by one cluster's
    # residual sum alone, not averaged across many) -- this is a known
    # limitation of cluster-robust inference with few treated clusters,
    # not a bug. Documented here so it isn't silently rediscovered later.
    rng = np.random.default_rng(0)
    rows = []
    for c in range(40):
        base = rng.normal(5, 1)
        treated = c == 0
        for t in YEARS:
            v = base + rng.normal(0, 0.3)
            if treated and t >= EFF_YEAR:
                v += 0.5
            rows.append((f"c{c}", t, v, treated))
    result = fit_ols_with_cluster_robust_se(rows, effective_year=EFF_YEAR)
    # not asserting a specific relationship -- just that it runs and
    # produces a finite (if unreliable) number, for the record.
    assert result.se_clustered >= 0 and result.n_clusters == 40


def test_too_few_clusters_for_residual_df_raises():
    rows = [("only_cluster", t, 1.0, True) for t in YEARS]
    with pytest.raises(ValueError, match="residual degrees of freedom"):
        fit_ols_with_cluster_robust_se(rows, effective_year=EFF_YEAR)
