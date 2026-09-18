"""STAGE D: narrow the control pool by pre-period volume and trend
matching, instead of using every never-restricted HS6 code in chapters
28/29/38 (~540 codes spanning many orders of magnitude in trade scale).

Thresholds below are fixed BEFORE this module is run against real data
(see decisions/0007-*.md and the commit that introduces this file) --
per CLAUDE.md rule 2, a choice this easy to tune after seeing results
must be pre-registered, not picked after looking at which threshold
gives the tightest confidence interval.

MATCHING_LOG10_VOLUME_TOLERANCE = 1.0
  A candidate control must have pre-period average trade value within one
  order of magnitude (factor of 10) of the treated product's pre-period
  average, i.e. |log10(candidate) - log10(treated)| <= 1.0. Reasoning:
  "same order of magnitude" is the literal instruction; a factor of 10 is
  the standard meaning of that phrase and is symmetric (allows candidates
  both larger and smaller than the treated product).

MATCHING_TREND_TOLERANCE = 0.15
  A candidate's pre-period trend (OLS slope of log1p(value) on year,
  pre-period years only) must be within 0.15 log points/year of the
  treated product's own pre-period trend. Reasoning: this is half of the
  smallest true effect size this project has looked for meaningfully
  (Stage 3's typical point estimates cluster 0.3-0.7 log points over a
  multi-year post-period, i.e. roughly 0.05-0.15 log points/year) -- a
  trend-matching band wider than the effect being estimated would defeat
  the point of matching on trend at all.

Same-chapter (first 2 digits of the HS6 code) and never-treated are hard
requirements, not tolerances -- inherited unchanged from the existing
control-pool definition (restricted_hs6 exclusion).
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import numpy as np

MATCHING_LOG10_VOLUME_TOLERANCE = 1.0
MATCHING_TREND_TOLERANCE = 0.15


@dataclass
class MatchStats:
    treated_hs6: str
    treated_log10_volume: float
    treated_trend: float
    n_candidates_same_chapter: int
    n_after_volume_filter: int
    n_after_trend_filter: int
    matched_hs6: list[str]
    matched_mean_log10_volume: float
    matched_mean_trend: float


def _pre_period_stats(con: duckdb.DuckDBPyConnection, hs6: str, exporter_codes: list[int], pre_years: list[int]) -> tuple[float, float]:
    """Returns (log10 of mean annual value, OLS trend slope of log1p(value) on year), pre-period only."""
    exp_list = ", ".join(str(c) for c in exporter_codes)
    rows = con.execute(
        f"""
        SELECT year, sum(value_kusd) AS value
        FROM trade_flows
        WHERE hs6 = ? AND exporter IN ({exp_list}) AND importer NOT IN ({exp_list})
          AND year = ANY(?)
        GROUP BY year
        """,
        [hs6, pre_years],
    ).fetchall()
    value_by_year = {r[0]: r[1] for r in rows}
    values = np.array([value_by_year.get(y, 0.0) for y in pre_years])
    mean_value = values.mean()
    log10_volume = np.log10(mean_value) if mean_value > 0 else -np.inf

    log1p_values = np.log1p(values)
    years_arr = np.array(pre_years, dtype=float)
    if len(pre_years) >= 2 and np.std(years_arr) > 0:
        slope = float(np.polyfit(years_arr, log1p_values, 1)[0])
    else:
        slope = 0.0
    return log10_volume, slope


def select_matched_controls(
    con: duckdb.DuckDBPyConnection,
    treated_hs6: str,
    candidate_hs6: list[str],
    exporter_codes: list[int],
    pre_years: list[int],
    log10_volume_tolerance: float = MATCHING_LOG10_VOLUME_TOLERANCE,
    trend_tolerance: float = MATCHING_TREND_TOLERANCE,
) -> MatchStats:
    chapter = treated_hs6[:2]
    same_chapter = [h for h in candidate_hs6 if h[:2] == chapter]

    treated_log10_vol, treated_trend = _pre_period_stats(con, treated_hs6, exporter_codes, pre_years)

    after_volume = []
    for h in same_chapter:
        log10_vol, _ = _pre_period_stats(con, h, exporter_codes, pre_years)
        if log10_vol == -np.inf and treated_log10_vol == -np.inf:
            after_volume.append(h)
        elif abs(log10_vol - treated_log10_vol) <= log10_volume_tolerance:
            after_volume.append(h)

    matched = []
    trends = []
    vols = []
    for h in after_volume:
        log10_vol, trend = _pre_period_stats(con, h, exporter_codes, pre_years)
        if abs(trend - treated_trend) <= trend_tolerance:
            matched.append(h)
            trends.append(trend)
            vols.append(log10_vol)

    return MatchStats(
        treated_hs6=treated_hs6,
        treated_log10_volume=treated_log10_vol,
        treated_trend=treated_trend,
        n_candidates_same_chapter=len(same_chapter),
        n_after_volume_filter=len(after_volume),
        n_after_trend_filter=len(matched),
        matched_hs6=matched,
        matched_mean_log10_volume=float(np.mean(vols)) if vols else float("nan"),
        matched_mean_trend=float(np.mean(trends)) if trends else float("nan"),
    )
