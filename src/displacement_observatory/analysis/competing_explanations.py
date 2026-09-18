"""STEP 4: competing explanations for a Step 3 effect, run alongside every
event, not just the ones with a headline finding.

Four checks, each answering a distinct alternative story for a rise in
treated-product export value to non-restricting destinations:

  1. price vs quantity -- is the value effect actually a volume effect, or
     mostly a unit-price effect? (re-runs the same event-study estimator on
     log1p(quantity_tons) instead of log1p(value_kusd))
  2. destination demand growth -- are the same destinations importing more
     of this HS6 code from EVERYONE, not just from the restricting
     exporter? (world-minus-exporter-bloc trend into the same importers)
  3. currency -- did EUR depreciate against USD over the event window?
     (BACI values are USD; a weaker EUR mechanically favours a value rise
     from EU exporters independent of any regulatory story)
  4. HS-code switching -- did a sibling HS6 code in the same 4-digit
     heading move in a way suggestive of relabelling, over the same window?

None of these "explain away" a finding on their own -- they are reported
alongside it, per project rules, not used to suppress it.
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import numpy as np

from displacement_observatory.analysis.diD import EventDiDResult
from displacement_observatory.analysis.fx import load_eur_usd_annual
from displacement_observatory.analysis.twfe import run_event_study


@dataclass
class CompetingExplanationsResult:
    event_id: str
    quantity_effect_available: bool
    quantity_headline_coef: float | None
    quantity_headline_ci: tuple[float, float] | None
    value_quantity_divergence_note: str

    rest_of_world_growth_pct: float | None
    demand_growth_note: str

    eur_usd_change_pct: float | None
    currency_note: str

    sibling_hs6_moves: dict[str, float]
    hs_switching_note: str


def _headline_k(study) -> int | None:
    post_ks = sorted(k for k in study.relative_years if k >= 0)
    return max(post_ks) if post_ks else None


def check_price_vs_quantity(
    con: duckdb.DuckDBPyConnection, result: EventDiDResult, control_hs6: list[str]
) -> tuple[bool, float | None, tuple[float, float] | None, str]:
    exporter_list = ", ".join(str(c) for c in result.exporter_codes)
    y0 = result.event.effective_date.year - 5
    y1 = result.event.effective_date.year + 5
    hs6_list = ", ".join(f"'{h}'" for h in [result.hs6, *control_hs6])
    rows = con.execute(
        f"""
        SELECT hs6, year, sum(quantity_tons) AS qty, sum(CASE WHEN quantity_tons IS NULL THEN 1 ELSE 0 END) AS n_missing, count(*) AS n
        FROM trade_flows
        WHERE exporter IN ({exporter_list}) AND importer NOT IN ({exporter_list})
          AND hs6 IN ({hs6_list}) AND year BETWEEN {y0} AND {y1}
        GROUP BY hs6, year
        """
    ).fetchall()
    if not rows:
        return False, None, None, "no quantity data available for this exporter/importer/product combination"

    value_by_key = {(r[0], r[1]): (r[2] or 0.0) for r in rows}
    all_years = sorted({r[1] for r in rows})
    all_units = [result.hs6, *control_hs6]
    panel_rows = [
        (u, t, float(np.log1p(value_by_key.get((u, t), 0.0))))
        for u in all_units
        for t in all_years
    ]
    try:
        qty_study = run_event_study(
            panel_rows, treated_unit=result.hs6, effective_year=result.event.effective_date.year, window_years=5
        )
    except ValueError as e:
        return False, None, None, f"could not fit quantity event-study: {e}"

    k = _headline_k(qty_study)
    if k is None:
        return False, None, None, "no post-period years available for quantity comparison"

    qty_coef = qty_study.coef[k]
    qty_ci = (qty_study.ci_low[k], qty_study.ci_high[k])

    if result.study is None:
        note = "value-side event study unavailable for comparison"
    else:
        val_coef = result.study.coef.get(k)
        if val_coef is None:
            note = f"value study has no coefficient at matching k={k}"
        elif val_coef > 0.1 and qty_coef < 0.3 * val_coef:
            note = (
                f"value effect ({val_coef:+.3f}) is much larger than the quantity effect ({qty_coef:+.3f}) at "
                f"the same relative year -- consistent with a unit-price rise rather than a real volume increase"
            )
        elif val_coef > 0.1 and qty_coef >= 0.3 * val_coef:
            note = f"quantity effect ({qty_coef:+.3f}) tracks the value effect ({val_coef:+.3f}) reasonably closely -- not primarily a price story"
        else:
            note = f"value effect ({val_coef:+.3f}) is not large enough at k={k} for this check to be informative"

    return True, qty_coef, qty_ci, note


def check_destination_demand_growth(
    con: duckdb.DuckDBPyConnection, result: EventDiDResult
) -> tuple[float | None, str]:
    exporter_list = ", ".join(str(c) for c in result.exporter_codes)
    eff_year = result.event.effective_date.year
    pre_years = (eff_year - 3, eff_year - 1)
    post_years = (eff_year, eff_year + 2)

    def rest_of_world_total(y_lo: int, y_hi: int) -> float:
        row = con.execute(
            f"""
            SELECT sum(value_kusd) FROM trade_flows
            WHERE hs6 = ? AND exporter NOT IN ({exporter_list}) AND importer NOT IN ({exporter_list})
              AND year BETWEEN ? AND ?
            """,
            [result.hs6, y_lo, y_hi],
        ).fetchone()
        return row[0] or 0.0

    pre_total = rest_of_world_total(*pre_years)
    post_total = rest_of_world_total(*post_years)
    if pre_total <= 0:
        return None, "no rest-of-world (non-restricting-exporter) trade in this HS6 to compare against"

    growth_pct = 100.0 * (post_total - pre_total) / pre_total
    note = (
        f"rest-of-world exporters' shipments of {result.hs6} to the same non-restricting destinations "
        f"changed {growth_pct:+.1f}% from {pre_years[0]}-{pre_years[1]} to {post_years[0]}-{post_years[1]} "
        "-- a large positive number here would suggest general demand growth rather than an "
        "EU-restriction-specific shift"
    )
    return growth_pct, note


def check_currency_effect(result: EventDiDResult) -> tuple[float | None, str]:
    if result.event.jurisdiction != "EU":
        return None, "currency check only implemented for EU-jurisdiction events"
    rates = load_eur_usd_annual()
    eff_year = result.event.effective_date.year
    k = _headline_k(result.study) if result.study else None
    end_year = eff_year + k if k is not None else eff_year
    start_year = result.event.decision_date.year - 1

    if start_year not in rates or end_year not in rates:
        return None, f"EUR/USD rate not cached for {start_year} or {end_year}"

    start_rate, end_rate = rates[start_year], rates[end_year]
    change_pct = 100.0 * (end_rate - start_rate) / start_rate
    direction = "depreciated" if change_pct < 0 else "appreciated"
    note = (
        f"EUR {direction} {abs(change_pct):.1f}% against USD from {start_year} to {end_year} "
        f"(ECB reference rate, USD per EUR: {start_rate:.3f} -> {end_rate:.3f}). "
        + (
            "A weaker EUR makes EU-sourced exports cheaper for foreign buyers and can mechanically raise "
            "USD-denominated trade VALUE independent of any regulatory effect -- worth weighing against a "
            "value-only finding."
            if change_pct < -3
            else "Not a large enough move to be a likely primary driver on its own."
        )
    )
    return change_pct, note


def check_hs_code_switching(
    con: duckdb.DuckDBPyConnection, result: EventDiDResult
) -> tuple[dict[str, float], str]:
    heading = result.hs6[:4]
    exporter_list = ", ".join(str(c) for c in result.exporter_codes)
    eff_year = result.event.effective_date.year
    pre_years = (eff_year - 3, eff_year - 1)
    post_years = (eff_year, eff_year + 2)

    siblings = con.execute(
        "SELECT DISTINCT hs6 FROM trade_flows WHERE substr(hs6,1,4) = ? AND hs6 != ?", [heading, result.hs6]
    ).fetchall()
    sibling_codes = [r[0] for r in siblings]
    if not sibling_codes:
        return {}, f"no sibling HS6 codes found under heading {heading}"

    moves: dict[str, float] = {}
    for sib in sibling_codes:
        def total(y_lo, y_hi):
            row = con.execute(
                f"""
                SELECT sum(value_kusd) FROM trade_flows
                WHERE hs6 = ? AND exporter IN ({exporter_list}) AND importer NOT IN ({exporter_list})
                  AND year BETWEEN ? AND ?
                """,
                [sib, y_lo, y_hi],
            ).fetchone()
            return row[0] or 0.0

        pre_v, post_v = total(*pre_years), total(*post_years)
        if pre_v > 0:
            moves[sib] = 100.0 * (post_v - pre_v) / pre_v

    if not moves:
        note = f"no sibling code under heading {heading} had nonzero pre-period trade to compare"
    else:
        risers = {k: v for k, v in moves.items() if v > 20}
        note = (
            f"sibling code(s) with >20% growth over the same window: {risers}"
            if risers
            else f"no sibling code under heading {heading} grew >20% over the same window (moves: {moves})"
        )
    return moves, note


def run_competing_explanations(
    con: duckdb.DuckDBPyConnection, result: EventDiDResult, control_hs6: list[str]
) -> CompetingExplanationsResult:
    qty_avail, qty_coef, qty_ci, qty_note = check_price_vs_quantity(con, result, control_hs6)
    demand_growth, demand_note = check_destination_demand_growth(con, result)
    fx_change, fx_note = check_currency_effect(result)
    sibling_moves, hs_note = check_hs_code_switching(con, result)

    return CompetingExplanationsResult(
        event_id=result.event.event_id,
        quantity_effect_available=qty_avail,
        quantity_headline_coef=qty_coef,
        quantity_headline_ci=qty_ci,
        value_quantity_divergence_note=qty_note,
        rest_of_world_growth_pct=demand_growth,
        demand_growth_note=demand_note,
        eur_usd_change_pct=fx_change,
        currency_note=fx_note,
        sibling_hs6_moves=sibling_moves,
        hs_switching_note=hs_note,
    )
