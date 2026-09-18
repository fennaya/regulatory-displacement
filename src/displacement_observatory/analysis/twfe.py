"""Two-way fixed-effects event-study estimator.

Pure numpy OLS -- no statistics library, no ML model, fully inspectable and
unit-testable against synthetic data with a known injected effect (see
tests/test_twfe.py). This is deliberately the only place in the project
that produces an estimated effect size; STEP 3 requires that no statistic
ever come from an LLM, only from tested, deterministic code.

Model, for unit u (a product) observed in year t within an event window:

    y[u,t] = sum_u' 1(u=u') * alpha_u'          (unit fixed effects)
           + sum_{t' != t_ref} 1(t=t') * lambda_t'   (year fixed effects, one omitted reference year)
           + sum_{k in window, k != -1} 1(u=treated, rel_year(t)=k) * beta_k  (event-time effect, on the treated unit only)
           + epsilon[u,t]

beta_k is the treated-vs-control gap at relative year k, normalised to
zero at k=-1 (the year immediately before the event's effective year) --
the standard event-study normalisation. Estimated by plain OLS
(numpy.linalg.lstsq); standard errors are classical (homoskedastic) OLS
standard errors from the residual variance, not clustered -- see
limitations in the project README.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np


@dataclass
class EventStudyResult:
    relative_years: list[int]
    coef: dict[int, float]
    se: dict[int, float]
    ci_low: dict[int, float]
    ci_high: dict[int, float]
    n_obs: int
    n_units: int
    n_years: int
    residual_df: int
    pretrend_max_abs_z: float
    pretrend_flagged: bool
    pretrend_detail: str


def _normal_two_sided_pvalue(z: float) -> float:
    return 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0))))


def run_event_study(
    rows: list[tuple[str, int, float]],
    treated_unit: str,
    effective_year: int,
    window_years: int,
    pretrend_z_threshold: float = 1.96,
) -> EventStudyResult:
    """rows: list of (unit_id, year, value). value should already be on the
    scale you want beta_k interpreted in (e.g. log(1+trade value)) -- this
    function does not transform it.
    """
    units = sorted({u for u, _, _ in rows})
    years = sorted({t for _, t, _ in rows})
    if treated_unit not in units:
        raise ValueError(f"treated_unit {treated_unit!r} not present in rows")

    unit_index = {u: i for i, u in enumerate(units)}
    year_index = {t: i for i, t in enumerate(years)}
    value_grid = np.zeros((len(units), len(years)))
    seen = set()
    for u, t, v in rows:
        if (u, t) in seen:
            raise ValueError(f"duplicate (unit, year) row: ({u}, {t})")
        seen.add((u, t))
        value_grid[unit_index[u], year_index[t]] = v

    rel_years_all = [t - effective_year for t in years]
    in_window = [k for k in rel_years_all if -window_years <= k <= window_years]
    event_coef_years = [k for k in in_window if k != -1]

    n_units, n_years = len(units), len(years)
    n_obs = n_units * n_years

    year_ref_idx = 0  # first year in the sorted list is the omitted year-FE reference
    n_year_cols = n_years - 1
    n_event_cols = len(event_coef_years)
    n_cols = n_units + n_year_cols + n_event_cols

    X = np.zeros((n_obs, n_cols))
    y = np.zeros(n_obs)

    treated_row = unit_index[treated_unit]
    row = 0
    obs_meta = []
    for ui, u in enumerate(units):
        for ti, t in enumerate(years):
            X[row, ui] = 1.0  # unit FE
            if ti != year_ref_idx:
                X[row, n_units + (ti - 1 if ti > year_ref_idx else ti)] = 1.0
            rel = t - effective_year
            if ui == treated_row and rel in event_coef_years:
                col = n_units + n_year_cols + event_coef_years.index(rel)
                X[row, col] = 1.0
            y[row] = value_grid[ui, ti]
            obs_meta.append((u, t))
            row += 1

    beta, residuals_sum, rank, _ = np.linalg.lstsq(X, y, rcond=None)
    fitted = X @ beta
    resid = y - fitted
    residual_df = n_obs - rank
    if residual_df <= 0:
        raise ValueError(
            f"No residual degrees of freedom (n_obs={n_obs}, rank={rank}); "
            "need more control units or a smaller window."
        )
    sigma2 = float(resid @ resid) / residual_df

    xtx_inv = np.linalg.pinv(X.T @ X)
    cov = sigma2 * xtx_inv
    se_all = np.sqrt(np.clip(np.diag(cov), 0, None))

    coef: dict[int, float] = {-1: 0.0}
    se: dict[int, float] = {-1: 0.0}
    ci_low: dict[int, float] = {-1: 0.0}
    ci_high: dict[int, float] = {-1: 0.0}
    for k in event_coef_years:
        col = n_units + n_year_cols + event_coef_years.index(k)
        b = float(beta[col])
        s = float(se_all[col])
        coef[k] = b
        se[k] = s
        ci_low[k] = b - 1.96 * s
        ci_high[k] = b + 1.96 * s

    pre_period_ks = [k for k in event_coef_years if k < -1]
    if pre_period_ks:
        zs = [abs(coef[k] / se[k]) if se[k] > 0 else 0.0 for k in pre_period_ks]
        max_abs_z = max(zs)
        flagged_ks = [k for k, z in zip(pre_period_ks, zs) if z > pretrend_z_threshold]
        flagged = len(flagged_ks) > 0
        detail = (
            f"pre-period relative years {flagged_ks} individually significant at |z|>{pretrend_z_threshold} "
            f"(max |z|={max_abs_z:.2f})"
            if flagged
            else f"no pre-period relative year exceeds |z|>{pretrend_z_threshold} (max |z|={max_abs_z:.2f})"
        )
    else:
        max_abs_z = 0.0
        flagged = False
        detail = "no pre-period years in window to test"

    return EventStudyResult(
        relative_years=sorted(set(event_coef_years) | {-1}),
        coef=coef,
        se=se,
        ci_low=ci_low,
        ci_high=ci_high,
        n_obs=n_obs,
        n_units=n_units,
        n_years=n_years,
        residual_df=residual_df,
        pretrend_max_abs_z=max_abs_z,
        pretrend_flagged=flagged,
        pretrend_detail=detail,
    )
