"""STAGE B.1: PPML on trade values in levels, importer x product x year fixed
effects, keeping zero flows.

The Stage 3 log-linear OLS spec aggregated value across the whole
non-restricting-destination set before taking logs, at (product, year)
granularity. That made a true collective zero rare (60%+ of individual
destinations can be at zero while the SUM across ~150-200 destinations is
still positive), which silently erases exactly the observations where
displacement shows up first: a specific destination going from zero
imports to positive imports. This module rebuilds the panel at
(importer, product, year) granularity, fills genuine zeros (no EU-bloc
exporter shipped that product to that importer that year), and fits
Poisson pseudo-maximum likelihood in levels via pyfixest, which handles
zeros natively (no log(0) problem) and is the standard estimator in the
trade literature for exactly this heteroskedasticity-and-zeros reason
(Silva & Tenreyro 2006).
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd
import pyfixest as pf

from displacement_observatory.analysis.packages import TreatmentPackage


@dataclass
class FlowPanel:
    df: pd.DataFrame
    treated_hs6: str
    effective_year: int
    n_importers: int
    n_products: int
    n_years: int
    n_total_cells: int
    n_zero_cells: int
    n_positive_cells: int


def build_importer_product_year_panel(
    con: duckdb.DuckDBPyConnection,
    package: TreatmentPackage,
    exporter_codes: list[int],
    control_hs6: list[str],
    y0: int,
    y1: int,
) -> FlowPanel:
    exp_list = ", ".join(str(c) for c in exporter_codes)
    hs6_list = ", ".join(f"'{h}'" for h in [package.hs6, *control_hs6])
    rows = con.execute(
        f"""
        SELECT importer, hs6, year, sum(value_kusd) AS value
        FROM trade_flows
        WHERE exporter IN ({exp_list}) AND importer NOT IN ({exp_list})
          AND hs6 IN ({hs6_list}) AND year BETWEEN {y0} AND {y1}
        GROUP BY importer, hs6, year
        """
    ).fetchall()

    value_map = {(r[0], r[1], r[2]): r[3] for r in rows}
    importers = sorted({r[0] for r in rows})
    years = list(range(y0, y1 + 1))
    units = [package.hs6, *control_hs6]

    grid = [
        (imp, u, t, value_map.get((imp, u, t), 0.0))
        for imp in importers
        for u in units
        for t in years
    ]
    df = pd.DataFrame(grid, columns=["importer", "hs6", "year", "value"])
    df["importer"] = df["importer"].astype(str)
    df["treated_post"] = ((df["hs6"] == package.hs6) & (df["year"] >= package.effective_date.year)).astype(int)

    n_total = len(df)
    n_zero = int((df["value"] == 0).sum())

    return FlowPanel(
        df=df, treated_hs6=package.hs6, effective_year=package.effective_date.year,
        n_importers=len(importers), n_products=len(units), n_years=len(years),
        n_total_cells=n_total, n_zero_cells=n_zero, n_positive_cells=n_total - n_zero,
    )


@dataclass
class EstimateResult:
    method: str
    coef: float
    se: float
    ci_low: float
    ci_high: float
    n_obs: int
    n_dropped: int
    note: str


def fit_ppml_att(panel: FlowPanel, vcov: str = "hetero") -> EstimateResult:
    m = pf.fepois("value ~ treated_post | hs6 + importer + year", data=panel.df, vcov=vcov)
    tidy = m.tidy()
    row = tidy.loc["treated_post"]
    n_used = int(m._N)
    n_dropped = panel.n_total_cells - n_used
    return EstimateResult(
        method="PPML (levels, importer+product+year FE)",
        coef=float(row["Estimate"]), se=float(row["Std. Error"]),
        ci_low=float(row["2.5%"]), ci_high=float(row["97.5%"]),
        n_obs=n_used, n_dropped=n_dropped,
        note=f"{panel.n_zero_cells:,}/{panel.n_total_cells:,} cells ({panel.n_zero_cells/panel.n_total_cells:.0%}) are genuine zero flows, kept; "
             f"{n_dropped:,} dropped by the ML fit itself (perfect-separation groups: an importer/product/year fixed-effect "
             f"group that is always zero carries no information for a multiplicative model).",
    )


def fit_flowlevel_log_ols_att(panel: FlowPanel) -> EstimateResult:
    """The comparison the log spec would have needed if run at the SAME
    (importer, product, year) granularity instead of pre-aggregating over
    importers: log(0) is undefined, so a naive log-linear approach has to
    drop every zero-value row outright. This function does exactly that,
    to make the information loss visible and numeric rather than asserted.
    """
    positive = panel.df[panel.df["value"] > 0].copy()
    positive["logv"] = np.log(positive["value"])
    m = pf.feols("logv ~ treated_post | hs6 + importer + year", data=positive, vcov="hetero")
    tidy = m.tidy()
    row = tidy.loc["treated_post"]
    n_dropped = panel.n_total_cells - len(positive)
    return EstimateResult(
        method="log-linear OLS at flow level (zeros dropped)",
        coef=float(row["Estimate"]), se=float(row["Std. Error"]),
        ci_low=float(row["2.5%"]), ci_high=float(row["97.5%"]),
        n_obs=len(positive), n_dropped=n_dropped,
        note=f"{n_dropped:,}/{panel.n_total_cells:,} cells ({n_dropped/panel.n_total_cells:.0%}) dropped because value=0 "
             "(log undefined) -- this is what the Stage 3 aggregate-over-importers design avoided facing, by summing "
             "away the very zeros that would have forced this drop.",
    )
