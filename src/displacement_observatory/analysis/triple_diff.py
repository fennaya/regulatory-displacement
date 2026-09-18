"""STAGE C: triple difference, using rest-of-world exporters as the
counterfactual rather than reporting their growth as a side-caveat
(decisions/0004).

  (EU exports to unrestricted destinations, after vs before)
  minus (non-EU exports of the same product to the same destinations,
         same window)
  minus (the same contrast for never-restricted control products)

Implementation note (see the design check in this module's tests): naively
pooling EU and RoW rows as "just more units" in the existing two-way-FE
estimator does NOT recover the triple difference -- a product-specific
shock shared by both EU and RoW exporters (e.g. the rest-of-world demand
growth Stage 4 already found, 26-50% across every event) gets diluted
across the whole control pool rather than differenced out, and the
estimate barely moves from the plain double-difference. Verified
empirically before writing this docstring: a synthetic scenario with a
0.3 common product-specific shock (both EU and RoW) plus a 0.5 EU-specific
increment recovered ~0.85-0.88 (close to the double-diff's 0.8-0.5=no
netting) from naive pooling, vs. ~0.5-0.57 (correct) from the design below.

The correct reduction: for every (product, year), compute
d = log1p(EU value) - log1p(RoW value) -- literally EU-minus-RoW, exactly
implementing the second difference -- and run the SAME event-study
estimator (analysis/twfe.py) on this differenced series with product as
the unit. Because both EU and RoW carry any shared product-year shock
with the same sign, the shock cancels in the subtraction; only the
EU-specific deviation survives. Unit and year fixed effects then implement
the double-difference over products/time on top of that, i.e. the
triple-difference as a whole.
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb
import numpy as np

from displacement_observatory.analysis.diD import EventDiDResult
from displacement_observatory.analysis.twfe import EventStudyResult, run_event_study


@dataclass
class TripleDiffResult:
    study: EventStudyResult
    n_products: int


def _bloc_value_map(
    con: duckdb.DuckDBPyConnection,
    all_hs6: list[str],
    eu_exporter_codes: list[int],
    y0: int,
    y1: int,
) -> dict[tuple[str, str, int], float]:
    eu_list = ", ".join(str(c) for c in eu_exporter_codes)
    hs6_list = ", ".join(f"'{h}'" for h in all_hs6)
    db_rows = con.execute(
        f"""
        SELECT
            CASE WHEN exporter IN ({eu_list}) THEN 'EU' ELSE 'RoW' END AS bloc,
            hs6, year, sum(value_kusd) AS value
        FROM trade_flows
        WHERE importer NOT IN ({eu_list})
          AND hs6 IN ({hs6_list})
          AND year BETWEEN {y0} AND {y1}
        GROUP BY bloc, hs6, year
        """
    ).fetchall()
    return {(r[0], r[1], r[2]): r[3] for r in db_rows}


def build_triple_diff_rows(
    con: duckdb.DuckDBPyConnection,
    treated_hs6: str,
    control_hs6: list[str],
    eu_exporter_codes: list[int],
    y0: int,
    y1: int,
) -> list[tuple[str, int, float]]:
    all_hs6 = [treated_hs6, *control_hs6]
    value_map = _bloc_value_map(con, all_hs6, eu_exporter_codes, y0, y1)
    years = list(range(y0, y1 + 1))

    rows = []
    for hs6 in all_hs6:
        for t in years:
            eu_v = value_map.get(("EU", hs6, t), 0.0)
            row_v = value_map.get(("RoW", hs6, t), 0.0)
            d = float(np.log1p(eu_v) - np.log1p(row_v))
            rows.append((hs6, t, d))
    return rows


def run_triple_diff(
    con: duckdb.DuckDBPyConnection,
    result: EventDiDResult,
    control_hs6: list[str],
    window_years: int = 5,
) -> TripleDiffResult:
    if result.status != "ok" or result.study is None:
        raise ValueError(f"cannot run triple-diff on a non-ok DiD result ({result.status}: {result.reason})")

    effective_year = result.event.effective_date.year
    ks = sorted(result.study.relative_years)
    y0, y1 = effective_year + ks[0], effective_year + ks[-1]

    rows = build_triple_diff_rows(con, result.hs6, control_hs6, result.exporter_codes, y0, y1)
    study = run_event_study(rows, treated_unit=result.hs6, effective_year=effective_year, window_years=window_years)

    return TripleDiffResult(study=study, n_products=len(control_hs6) + 1)
