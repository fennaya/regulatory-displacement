"""STAGE F: pre-registered destination heterogeneity.

Loads data/destination_groups_v1.yaml (written and committed BEFORE any
estimation using it -- see that file's header and decisions/0008-*.md)
and runs the event-study estimator separately for each group, restricting
the "unrestricted destinations" set to the group's countries instead of
every non-EU country.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import duckdb
import numpy as np
import yaml

from displacement_observatory.analysis.twfe import EventStudyResult, run_event_study

DESTINATION_GROUPS_PATH = Path(__file__).resolve().parents[3] / "data" / "destination_groups_v1.yaml"


@dataclass
class DestinationGroups:
    version: int
    high_exposure_iso3: list[str]
    low_exposure_iso3: list[str]


def load_destination_groups(path: Path = DESTINATION_GROUPS_PATH) -> DestinationGroups:
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return DestinationGroups(
        version=raw["version"],
        high_exposure_iso3=[c["iso3"] for c in raw["high_exposure"]],
        low_exposure_iso3=[c["iso3"] for c in raw["low_exposure"]],
    )


def resolve_iso3_to_codes(con: duckdb.DuckDBPyConnection, iso3_list: list[str], source: str, source_version: str) -> list[int]:
    if not iso3_list:
        return []
    placeholders = ", ".join("?" for _ in iso3_list)
    rows = con.execute(
        f"SELECT DISTINCT country_code FROM countries WHERE country_iso3 IN ({placeholders}) AND source = ? AND source_version = ?",
        [*iso3_list, source, source_version],
    ).fetchall()
    return [r[0] for r in rows]


def run_event_study_for_destination_group(
    con: duckdb.DuckDBPyConnection,
    treated_hs6: str,
    control_hs6: list[str],
    exporter_codes: list[int],
    destination_codes: list[int],
    y0: int,
    y1: int,
    effective_year: int,
    window_years: int,
) -> EventStudyResult:
    if not destination_codes:
        raise ValueError("empty destination_codes -- nothing resolved for this group")

    exp_list = ", ".join(str(c) for c in exporter_codes)
    dest_list = ", ".join(str(c) for c in destination_codes)
    hs6_list = ", ".join(f"'{h}'" for h in [treated_hs6, *control_hs6])
    db_rows = con.execute(
        f"""
        SELECT hs6, year, sum(value_kusd) AS value
        FROM trade_flows
        WHERE exporter IN ({exp_list}) AND importer IN ({dest_list})
          AND hs6 IN ({hs6_list}) AND year BETWEEN {y0} AND {y1}
        GROUP BY hs6, year
        """
    ).fetchall()
    value_map = {(r[0], r[1]): r[2] for r in db_rows}
    years = list(range(y0, y1 + 1))
    all_units = [treated_hs6, *control_hs6]

    rows = [
        (u, t, float(np.log1p(value_map.get((u, t), 0.0))))
        for u in all_units
        for t in years
    ]
    return run_event_study(rows, treated_unit=treated_hs6, effective_year=effective_year, window_years=window_years)
