"""STAGE B.2/B.3: staggered-adoption-robust estimation + Bacon-style
decomposition of the naive pooled TWFE.

Per decisions/0003: HS6 380810 is treated three times (endosulfan 2006,
neonicotinoids 2018, chlorpyrifos 2020) and 380830 twice (atrazine 2004,
paraquat 2007). Stage A already proved these sub-events cannot be
separated from each other within the same HS6 code. The honest question
this data can answer is not "what was the neonicotinoid-specific effect"
but "did HS6 380810/380830, as a whole basket, move after it FIRST became
subject to ANY EU restriction, relative to HS6 codes that were never
restricted" -- a cumulative-treatment, staggered-adoption design with
exactly 2 treated cohorts (gname=2006 for 380810, gname=2004 for 380830)
and ~540 never-treated codes (gname=0).

The panel spans the FULL 1995-2024 window (not a per-package clipped
window), because Callaway-Sant'Anna/Sun-Abraham/did2s need pre-period data
for every cohort to identify cohort-specific dynamics. EU membership is
resolved per calendar year (not frozen at one decision date), since this
panel runs across three decades of EU enlargement.
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import pandas as pd
import pyfixest as pf

from displacement_observatory.analysis.country_groups import eu_members_iso3, resolve_country_codes
from displacement_observatory.register.schema import RestrictionEvent


def build_eu_membership_by_year(con: duckdb.DuckDBPyConnection, years: list[int], source: str, source_version: str) -> pd.DataFrame:
    from datetime import date

    rows = []
    for y in years:
        iso3 = eu_members_iso3(date(y, 1, 1))
        codes = resolve_country_codes(con, iso3, source, source_version)
        rows.extend((c, y) for c in codes)
    return pd.DataFrame(rows, columns=["country_code", "year"])


def first_restriction_year(events: list[RestrictionEvent], jurisdiction_filter: str = "EU") -> dict[str, int]:
    """hs6 -> earliest effective_date.year among EU-jurisdiction register
    events touching it. Only EU events count as "gname" cohorts here,
    because the staggered design needs a single, well-defined exporter
    bloc (see decisions/0003) -- the Rotterdam Convention event is a
    different kind of instrument and is deliberately excluded from cohort
    assignment, exactly as it was excluded from the per-package DiD.
    """
    out: dict[str, int] = {}
    for e in events:
        if e.jurisdiction != jurisdiction_filter:
            continue
        for c in e.hs6_candidates:
            y = e.effective_date.year
            if c.hs6 not in out or y < out[c.hs6]:
                out[c.hs6] = y
    return out


def build_hs6_year_panel(
    con: duckdb.DuckDBPyConnection,
    all_hs6: list[str],
    gname_by_hs6: dict[str, int],
    y0: int,
    y1: int,
    source: str = "BACI",
    source_version: str = "202601",
) -> pd.DataFrame:
    years = list(range(y0, y1 + 1))
    membership = build_eu_membership_by_year(con, years, source, source_version)
    con.register("_eu_membership", membership)

    hs6_list = ", ".join(f"'{h}'" for h in all_hs6)
    rows = con.execute(
        f"""
        SELECT tf.hs6, tf.year, sum(tf.value_kusd) AS value
        FROM trade_flows tf
        JOIN _eu_membership exp ON tf.exporter = exp.country_code AND tf.year = exp.year
        LEFT JOIN _eu_membership imp ON tf.importer = imp.country_code AND tf.year = imp.year
        WHERE tf.hs6 IN ({hs6_list})
          AND tf.year BETWEEN {y0} AND {y1}
          AND imp.country_code IS NULL
        GROUP BY tf.hs6, tf.year
        """
    ).fetchall()
    con.unregister("_eu_membership")

    value_map = {(r[0], r[1]): r[2] for r in rows}
    grid = [
        (hs6, y, value_map.get((hs6, y), 0.0), gname_by_hs6.get(hs6, 0))
        for hs6 in all_hs6
        for y in years
    ]
    df = pd.DataFrame(grid, columns=["hs6", "year", "value", "gname"])
    return df


@dataclass
class StaggeredResult:
    method: str
    coef: float
    se: float
    ci_low: float
    ci_high: float
    n_obs: int
    n_treated_cohorts: int
    n_never_treated: int


def fit_staggered(df: pd.DataFrame, estimator: str = "did2s", att: bool = True) -> StaggeredResult:
    work = df.copy()
    work["hs6"] = work["hs6"].astype(str)
    fit = pf.event_study(work, yname="value", idname="hs6", tname="year", gname="gname", estimator=estimator, att=att)
    tidy = fit.tidy()
    row = tidy.iloc[0]
    return StaggeredResult(
        method=f"{estimator} (staggered-robust, cumulative-treatment HS6 panel)",
        coef=float(row["Estimate"]), se=float(row["Std. Error"]),
        ci_low=float(row["2.5%"]), ci_high=float(row["97.5%"]),
        n_obs=len(work),
        n_treated_cohorts=int((df["gname"] > 0).groupby(df["hs6"]).any().sum()),
        n_never_treated=int((df["gname"] == 0).groupby(df["hs6"]).any().sum()),
    )
