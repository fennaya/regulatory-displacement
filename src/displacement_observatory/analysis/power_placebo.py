"""STEP 3 (close-out): Stage G's minimum detectable effects recomputed from
placebo-derived standard errors instead of Stage E's cluster-robust ones.

Why: with one treated HS6 code per package, no analytic standard error is
reliable (decisions/0009-*.md: a placebo SD of about 1.4 against a reported SE
of 0.145 at the basket level). Stage E's SE clusters at exporter-product, but
the exporter-product clusters inside one treated code share that code's common
shock, so it is too narrow.

Direction of the error (stated before computing): a too-narrow SE understates
the real uncertainty, so the real MDE is larger, so MORE packages are
undetectable at a given assumed effect size, not fewer. The error makes the
conclusion more robust while invalidating its specific figures. This module
checks that direction per package rather than assuming it.

Placebo design (in-space, deterministic): for each package, take its
pre-registered matched control pool (Stage D, decisions/0007). Each pool member
in turn is treated as if it were the restricted code (same effective year, same
exporters, same window), the real treated code is dropped, and the remaining
pool members are the controls. The Stage E estimator (single average post
effect, unit x year fixed effects on the exporter x product panel) is applied
to each. The standard deviation of these placebo estimates is the SE. Nothing is
random; there is nothing to seed.
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd

from displacement_observatory.analysis.basket_attack import twfe_att_balanced
from displacement_observatory.analysis.clustered import build_exporter_product_year_rows
from displacement_observatory.analysis.power import BasketShareAssumption, PowerVerdict, compute_mde, evaluate_package


@dataclass
class PlacebosResult:
    treated_hs6: str
    real_att: float
    placebo_atts: list[float]
    se: float            # SD of placebo ATTs (ddof=1)
    n_placebos: int


def placebo_se(
    con: duckdb.DuckDBPyConnection,
    treated_hs6: str,
    matched_controls: list[str],
    exporter_codes: list[int],
    y0: int,
    y1: int,
    effective_year: int,
) -> PlacebosResult:
    if len(matched_controls) < 3:
        raise ValueError("need at least 3 matched controls for a placebo distribution")
    rows = build_exporter_product_year_rows(con, treated_hs6, matched_controls, exporter_codes, y0, y1)
    df = pd.DataFrame(rows, columns=["hs6", "year", "value", "is_treated"])
    df["code"] = df["hs6"].str.split("::").str[1]

    def att(frame: pd.DataFrame, treated_code: str) -> float:
        f = frame[["hs6", "year", "value", "code"]].copy()
        f["gname"] = np.where(f["code"] == treated_code, effective_year, 0)
        return twfe_att_balanced(f[["hs6", "year", "value", "gname"]])

    real = att(df, treated_hs6)
    pool_only = df[df["code"] != treated_hs6]
    # each pool member in turn plays the restricted code; the rest of the pool are its controls
    placebos = [att(pool_only, c) for c in matched_controls]
    return PlacebosResult(
        treated_hs6=treated_hs6, real_att=real, placebo_atts=placebos,
        se=float(np.std(placebos, ddof=1)), n_placebos=len(placebos),
    )


@dataclass
class PowerRecomputation:
    package_id: str
    stage_e_se: float
    placebo_se: float
    n_placebos: int
    stage_e_mde: float
    placebo_mde: float
    placebo_se_is_wider: bool
    stage_e_verdict: PowerVerdict
    placebo_verdict: PowerVerdict


def recompute_power(package_id: str, stage_e_se: float, placebo: PlacebosResult, assumption: BasketShareAssumption) -> PowerRecomputation:
    return PowerRecomputation(
        package_id=package_id, stage_e_se=stage_e_se, placebo_se=placebo.se, n_placebos=placebo.n_placebos,
        stage_e_mde=compute_mde(stage_e_se), placebo_mde=compute_mde(placebo.se),
        placebo_se_is_wider=placebo.se > stage_e_se,
        stage_e_verdict=evaluate_package(package_id, stage_e_se, assumption),
        placebo_verdict=evaluate_package(package_id, placebo.se, assumption),
    )
