"""PART 1 of the attack-and-reframe task: hostile tests of the one
estimate that cleared conventional significance in the staggered
basket-level specification (analysis/staggered.py).

Everything here is deterministic numpy/pandas on the BACI panel; no
statistic is produced by a model. Pieces:

  build_hs6_year_bloc_panel  EU-bloc and rest-of-world exports per
                             HS6-year, to destinations outside the EU that
                             year (EU membership varies by year).
  to_outcome_frame           "eu" (the original spec), "row", or "triple"
                             (log EU minus log RoW, per HS6-year).
  twfe_att_balanced          exact two-way-FE ATT on a balanced panel
                             (unit + year demeaning); used where thousands
                             of refits are needed (placebos). Cross-checked
                             against pyfixest's twfe in the tests.
  placebo_distribution       randomization inference: assign the real
                             cohort structure to randomly chosen
                             NEVER-treated codes and re-estimate. With one
                             treated unit per cohort, asymptotic cluster SEs
                             are not reliable; this is the honest yardstick.
"""

from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd

from displacement_observatory.analysis.staggered import build_eu_membership_by_year


def build_hs6_year_bloc_panel(
    con: duckdb.DuckDBPyConnection,
    all_hs6: list[str],
    gname_by_hs6: dict[str, int],
    y0: int,
    y1: int,
    source: str = "BACI",
    source_version: str = "202601",
    measure: str = "value_kusd",
) -> pd.DataFrame:
    if measure not in ("value_kusd", "quantity_tons"):
        raise ValueError(f"unsupported measure {measure!r}")
    years = list(range(y0, y1 + 1))
    membership = build_eu_membership_by_year(con, years, source, source_version)
    con.register("_eu_membership_attack", membership)
    hs6_list = ", ".join(f"'{h}'" for h in all_hs6)
    rows = con.execute(
        f"""
        SELECT tf.hs6, tf.year,
               CASE WHEN exp.country_code IS NOT NULL THEN 'EU' ELSE 'RoW' END AS bloc,
               sum(tf.{measure}) AS v
        FROM trade_flows tf
        LEFT JOIN _eu_membership_attack exp ON tf.exporter = exp.country_code AND tf.year = exp.year
        LEFT JOIN _eu_membership_attack imp ON tf.importer = imp.country_code AND tf.year = imp.year
        WHERE tf.hs6 IN ({hs6_list}) AND tf.year BETWEEN {y0} AND {y1}
          AND imp.country_code IS NULL
        GROUP BY tf.hs6, tf.year, bloc
        """
    ).fetchall()
    con.unregister("_eu_membership_attack")

    vmap = {(r[0], r[1], r[2]): (r[3] or 0.0) for r in rows}
    grid = [
        (h, y, vmap.get((h, y, "EU"), 0.0), vmap.get((h, y, "RoW"), 0.0), gname_by_hs6.get(h, 0))
        for h in all_hs6 for y in years
    ]
    return pd.DataFrame(grid, columns=["hs6", "year", "eu", "row", "gname"])


def to_outcome_frame(bloc_df: pd.DataFrame, mode: str) -> pd.DataFrame:
    out = bloc_df[["hs6", "year", "gname"]].copy()
    if mode == "eu":
        out["value"] = np.log1p(bloc_df["eu"])
    elif mode == "row":
        out["value"] = np.log1p(bloc_df["row"])
    elif mode == "triple":
        out["value"] = np.log1p(bloc_df["eu"]) - np.log1p(bloc_df["row"])
    else:
        raise ValueError(f"unknown mode {mode!r}")
    return out


def twfe_att_balanced(df: pd.DataFrame) -> float:
    """Pooled ATT of D = 1[year >= gname > 0] under unit + year fixed
    effects, exact for a balanced panel (Frisch-Waugh via double
    demeaning)."""
    y = df.pivot(index="hs6", columns="year", values="value")
    g = df.groupby("hs6")["gname"].first().reindex(y.index).to_numpy()
    years = y.columns.to_numpy()
    D = ((g[:, None] > 0) & (years[None, :] >= g[:, None])).astype(float)
    Y = y.to_numpy()

    def dd(M):
        return M - M.mean(axis=1, keepdims=True) - M.mean(axis=0, keepdims=True) + M.mean()

    Dd, Yd = dd(D), dd(Y)
    denom = float((Dd ** 2).sum())
    if denom == 0:
        raise ValueError("no treatment variation")
    return float((Dd * Yd).sum() / denom)


def placebo_distribution(
    df: pd.DataFrame,
    candidate_hs6: list[str],
    cohorts: list[int],
    n_draws: int,
    seed: int = 0,
) -> np.ndarray:
    """Re-estimate the pooled ATT n_draws times, each time assigning the
    real cohort years (one code per cohort) to distinct randomly drawn
    codes from candidate_hs6 (which must be never-treated in the real
    data), with all real treated codes removed from the panel."""
    rng = np.random.default_rng(seed)
    base = df[df["hs6"].isin(candidate_hs6)].copy()
    coefs = np.empty(n_draws)
    for i in range(n_draws):
        picks = rng.choice(candidate_hs6, size=len(cohorts), replace=False)
        assign = dict(zip(picks, cohorts))
        work = base.copy()
        work["gname"] = work["hs6"].map(assign).fillna(0).astype(int)
        coefs[i] = twfe_att_balanced(work)
    return coefs


def placebo_two_sided_p(real: float, placebos: np.ndarray) -> float:
    """Share of placebo draws at least as extreme in absolute value, with
    the +1 correction so p is never reported as exactly zero."""
    return float((np.sum(np.abs(placebos) >= abs(real)) + 1) / (len(placebos) + 1))
