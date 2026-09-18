from datetime import date

import numpy as np
import pandas as pd
import pytest

from displacement_observatory.analysis.packages import TreatmentPackage
from displacement_observatory.analysis.ppml import (
    FlowPanel,
    fit_flowlevel_log_ols_att,
    fit_ppml_att,
)


def _synthetic_panel(true_log_effect=0.5, seed=0, n_importers=25, n_control_products=8, years=range(2010, 2021), effective_year=2015):
    rng = np.random.default_rng(seed)
    treated_hs6 = "999999"
    control_products = [f"88888{i}" for i in range(n_control_products)]
    importers = [f"imp{i}" for i in range(n_importers)]

    rows = []
    for imp_i, imp in enumerate(importers):
        importer_scale = rng.uniform(0.5, 2.0)
        for prod in [treated_hs6, *control_products]:
            product_scale = rng.uniform(0.5, 2.0)
            for t in years:
                base_rate = 3.0 * importer_scale * product_scale
                if prod == treated_hs6 and t >= effective_year:
                    base_rate *= np.exp(true_log_effect)
                # Many importer-product pairs never trade at all (sparse, like real BACI).
                if rng.random() < 0.4:
                    value = 0.0
                else:
                    value = float(rng.poisson(base_rate))
                rows.append((imp, prod, t, value))

    df = pd.DataFrame(rows, columns=["importer", "hs6", "year", "value"])
    df["treated_post"] = ((df["hs6"] == treated_hs6) & (df["year"] >= effective_year)).astype(int)
    n_total = len(df)
    n_zero = int((df["value"] == 0).sum())
    panel = FlowPanel(
        df=df, treated_hs6=treated_hs6, effective_year=effective_year,
        n_importers=n_importers, n_products=n_control_products + 1, n_years=len(list(years)),
        n_total_cells=n_total, n_zero_cells=n_zero, n_positive_cells=n_total - n_zero,
    )
    return panel


def test_ppml_recovers_known_injected_log_effect():
    # Average the recovered coefficient over several seeds rather than
    # asserting on one draw: Poisson noise at these sample sizes means a
    # single seed can land ~1.5-2 SE from the truth by chance (verified:
    # per-seed estimates ranged 0.26-0.61 across 8 seeds, mean 0.48) even
    # though the estimator is unbiased. The mean over seeds is the stable,
    # testable quantity.
    coefs = [fit_ppml_att(_synthetic_panel(true_log_effect=0.5, seed=s)).coef for s in range(6)]
    mean_coef = sum(coefs) / len(coefs)
    assert abs(mean_coef - 0.5) < 0.1, coefs


def test_ppml_near_zero_effect_recovers_near_zero():
    panel = _synthetic_panel(true_log_effect=0.0, seed=2)
    result = fit_ppml_att(panel)
    assert abs(result.coef) < 0.15, result.coef


def test_ppml_reports_zero_cell_count_correctly():
    panel = _synthetic_panel(seed=3)
    result = fit_ppml_att(panel)
    assert panel.n_zero_cells > 0
    assert panel.n_zero_cells + panel.n_positive_cells == panel.n_total_cells
    assert str(panel.n_zero_cells) in result.note or f"{panel.n_zero_cells:,}" in result.note


def test_flowlevel_log_ols_drops_all_zero_rows():
    panel = _synthetic_panel(seed=4)
    result = fit_flowlevel_log_ols_att(panel)
    assert result.n_obs == panel.n_positive_cells
    assert result.n_dropped == panel.n_zero_cells
    assert result.n_dropped > 0


def test_flowlevel_log_ols_also_recovers_known_effect_on_positive_subset():
    # Sanity: on the surviving positive-only subset, log-OLS should still
    # roughly recover the injected multiplicative effect for cells that
    # DID trade -- the point of the comparison is the *dropped n*, not that
    # log-OLS gives a wrong number on what's left.
    panel = _synthetic_panel(true_log_effect=0.5, seed=5)
    result = fit_flowlevel_log_ols_att(panel)
    assert abs(result.coef - 0.5) < 0.25, result.coef
