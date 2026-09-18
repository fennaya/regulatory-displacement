"""STAGE E: cluster-robust standard errors at the exporter-product level.

Every prior estimate in this repo (Stage 3's OLS-TWFE, Stage B's PPML,
Stage D's matched-pool OLS) used classical (homoskedastic, independent-
errors) standard errors on a panel aggregated across all EU exporters into
one series per product. That aggregation makes "cluster by exporter-
product" structurally impossible -- there is only one "exporter" (the
pooled bloc) per product in that panel. This module disaggregates back
to (exporter, product, year) and clusters residuals within each
exporter-product pair across years, which classical SEs assume away
(independent errors) but which is a standard concern in panel data: an
exporter-product's deviations from its own fixed effect are plausibly
correlated year to year (a persistent shock doesn't reset every January).

This is a correctness fix, not a power fix, and it is not expected to
narrow anything -- per the user's own instruction: "expect the CIs to get
WIDER, not narrower."

Implemented as a self-contained OLS + cluster-robust sandwich estimator
(not reusing analysis/twfe.py directly) because the treated group here is
a SET of units (every EU-exporter x treated-product cell shares the same
interaction dummy), not the single treated_unit analysis/twfe.py assumes
-- extending that module's API was judged riskier than a small, separately
tested implementation for this one stage.
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import numpy as np


@dataclass
class ClusteredEstimate:
    coef: float
    se_classical: float
    se_clustered: float
    ci_classical: tuple[float, float]
    ci_clustered: tuple[float, float]
    n_obs: int
    n_clusters: int
    n_params: int


def fit_ols_with_cluster_robust_se(
    rows: list[tuple[str, int, float, bool]],
    effective_year: int,
) -> ClusteredEstimate:
    """rows: (cluster_id, year, value, is_treated_group). value should
    already be on the scale you want the coefficient in (e.g.
    log1p(trade value)). The single estimated coefficient is the average
    post-vs-pre gap for is_treated_group=True cells relative to
    is_treated_group=False cells (an ATT-style single dummy, not a full
    event-time spec -- Stage E's ask is about the SE correction, not a
    new dynamic specification).
    """
    clusters = sorted({c for c, _, _, _ in rows})
    years = sorted({t for _, t, _, _ in rows})
    cluster_index = {c: i for i, c in enumerate(clusters)}
    year_index = {t: i for i, t in enumerate(years)}

    n_clusters = len(clusters)
    n_years = len(years)
    n_obs = len(rows)
    year_ref_idx = 0
    n_year_cols = n_years - 1
    n_cols = n_clusters + n_year_cols + 1  # +1 for the treated-post dummy

    X = np.zeros((n_obs, n_cols))
    y = np.zeros(n_obs)
    cluster_of_row = np.zeros(n_obs, dtype=int)

    for i, (c, t, v, treated) in enumerate(rows):
        ci = cluster_index[c]
        X[i, ci] = 1.0
        ti = year_index[t]
        if ti != year_ref_idx:
            X[i, n_clusters + (ti - 1 if ti > year_ref_idx else ti)] = 1.0
        if treated and t >= effective_year:
            X[i, -1] = 1.0
        y[i] = v
        cluster_of_row[i] = ci

    beta, _, rank, _ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    df_resid = n_obs - rank
    if df_resid <= 0:
        raise ValueError("no residual degrees of freedom")

    xtx_inv = np.linalg.pinv(X.T @ X)

    sigma2 = float(resid @ resid) / df_resid
    cov_classical = sigma2 * xtx_inv
    se_classical = float(np.sqrt(max(cov_classical[-1, -1], 0.0)))

    meat = np.zeros((n_cols, n_cols))
    for ci in range(n_clusters):
        mask = cluster_of_row == ci
        Xg = X[mask]
        eg = resid[mask]
        score = Xg.T @ eg
        meat += np.outer(score, score)
    G = n_clusters
    correction = (G / (G - 1)) * ((n_obs - 1) / df_resid) if G > 1 else 1.0
    cov_clustered = correction * xtx_inv @ meat @ xtx_inv
    se_clustered = float(np.sqrt(max(cov_clustered[-1, -1], 0.0)))

    coef = float(beta[-1])
    return ClusteredEstimate(
        coef=coef,
        se_classical=se_classical, se_clustered=se_clustered,
        ci_classical=(coef - 1.96 * se_classical, coef + 1.96 * se_classical),
        ci_clustered=(coef - 1.96 * se_clustered, coef + 1.96 * se_clustered),
        n_obs=n_obs, n_clusters=n_clusters, n_params=int(rank),
    )


def build_exporter_product_year_rows(
    con: duckdb.DuckDBPyConnection,
    treated_hs6: str,
    control_hs6: list[str],
    exporter_codes: list[int],
    y0: int,
    y1: int,
) -> list[tuple[str, int, float, bool]]:
    exp_list = ", ".join(str(c) for c in exporter_codes)
    hs6_list = ", ".join(f"'{h}'" for h in [treated_hs6, *control_hs6])
    db_rows = con.execute(
        f"""
        SELECT exporter, hs6, year, sum(value_kusd) AS value
        FROM trade_flows
        WHERE exporter IN ({exp_list}) AND importer NOT IN ({exp_list})
          AND hs6 IN ({hs6_list}) AND year BETWEEN {y0} AND {y1}
        GROUP BY exporter, hs6, year
        """
    ).fetchall()
    value_map = {(r[0], r[1], r[2]): r[3] for r in db_rows}
    years = list(range(y0, y1 + 1))
    all_hs6 = [treated_hs6, *control_hs6]

    rows = []
    for exp in exporter_codes:
        for hs6 in all_hs6:
            for t in years:
                v = value_map.get((exp, hs6, t), 0.0)
                cluster_id = f"{exp}::{hs6}"
                rows.append((cluster_id, t, float(np.log1p(v)), hs6 == treated_hs6))
    return rows
