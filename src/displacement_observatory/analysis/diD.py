"""Per-event difference-in-differences, wiring the register and trade panel
to the twfe event-study estimator (STEP 3).

Design (see README for the full rationale):
  - exporter set: BACI country codes for the event's jurisdiction, resolved
    as of the event's decision_date (EU membership changes over time).
  - "destinations with no equivalent restriction": every importer NOT in
    the exporter set (i.e. not bound by the same restriction). This is a
    simplification -- a destination could independently restrict the same
    substance under its own law, which this project does not yet track.
  - treated unit: the event's HS6 code.
  - control units: every other HS6 code in the panel's chemical scope that
    is never an hs6_candidate for ANY event in the register (so controls
    are never-restricted, same broad industry, same exporter, same period,
    as the project brief requires) -- excludes not just this event's code
    but every other registered substance's code too, even if unrelated to
    this specific event, so a later finding about one event can't secretly
    leak into another event's control pool.
  - unit of analysis for the regression is (HS6 product, year); value is
    log1p(total value_kusd) summed over exporter x unrestricted-importer
    flows for that product-year.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import duckdb
import numpy as np

from displacement_observatory.analysis.country_groups import jurisdiction_exporter_codes
from displacement_observatory.analysis.twfe import EventStudyResult, run_event_study
from displacement_observatory.config import CHEMICAL_HS2_CHAPTERS
from displacement_observatory.register.schema import RestrictionEvent
from displacement_observatory.register.store import RegisterLoadResult


@dataclass
class EventDiDResult:
    event: RestrictionEvent
    hs6: str
    status: str  # "ok", "skipped"
    reason: str | None = None
    exporter_codes: list[int] = field(default_factory=list)
    n_control_units: int = 0
    study: EventStudyResult | None = None
    same_hs6_contaminating_events: list[str] = field(default_factory=list)


def _contaminating_events(target: RestrictionEvent, all_events: list[RestrictionEvent], hs6: str, window_years: int) -> list[str]:
    target_year = target.effective_date.year
    out = []
    for e in all_events:
        if e.event_id == target.event_id:
            continue
        if not any(c.hs6 == hs6 for c in e.hs6_candidates):
            continue
        if abs(e.effective_date.year - target_year) <= window_years:
            out.append(e.event_id)
    return out


def run_event_did(
    con: duckdb.DuckDBPyConnection,
    event: RestrictionEvent,
    register: RegisterLoadResult,
    window_years: int = 5,
    source: str = "BACI",
    source_version: str = "202601",
) -> EventDiDResult:
    if len(event.hs6_candidates) != 1:
        return EventDiDResult(
            event=event, hs6="", status="skipped",
            reason=f"expected exactly one hs6_candidate for a v1 DiD run, got {len(event.hs6_candidates)}",
        )
    hs6 = event.hs6_candidates[0].hs6

    exporter_codes = jurisdiction_exporter_codes(con, event.jurisdiction, event.decision_date, source, source_version)
    if exporter_codes is None:
        return EventDiDResult(
            event=event, hs6=hs6, status="skipped",
            reason=(
                f"jurisdiction {event.jurisdiction!r} does not resolve to a single well-defined "
                "exporter bloc (e.g. a global treaty with no one restricting exporter) -- see the "
                "event's own notes for why an exporter-based DiD is not meaningful here."
            ),
        )
    if not exporter_codes:
        return EventDiDResult(event=event, hs6=hs6, status="skipped", reason="no BACI country codes resolved for this jurisdiction")

    restricted_hs6 = {c.hs6 for e in register.events for c in e.hs6_candidates}
    control_hs6_rows = con.execute(
        f"""
        SELECT DISTINCT hs6 FROM trade_flows
        WHERE substr(hs6,1,2) IN ({", ".join(f"'{c}'" for c in CHEMICAL_HS2_CHAPTERS)})
        """
    ).fetchall()
    control_hs6 = sorted({r[0] for r in control_hs6_rows} - restricted_hs6)

    effective_year = event.effective_date.year
    panel_min_year, panel_max_year = con.execute("SELECT min(year), max(year) FROM trade_flows").fetchone()
    y0 = max(effective_year - window_years, panel_min_year)
    y1 = min(effective_year + window_years, panel_max_year)
    if y1 - effective_year < 1 or effective_year - y0 < 1:
        return EventDiDResult(
            event=event, hs6=hs6, status="skipped",
            reason=(
                f"event window [{effective_year - window_years}, {effective_year + window_years}] barely "
                f"overlaps the panel's actual coverage [{panel_min_year}, {panel_max_year}]; too few years "
                "on one side of the event to estimate anything meaningful."
            ),
        )

    exporter_list = ", ".join(str(c) for c in exporter_codes)
    hs6_list = ", ".join(f"'{h}'" for h in [hs6, *control_hs6])
    query = f"""
        SELECT hs6, year, sum(value_kusd) AS value
        FROM trade_flows
        WHERE exporter IN ({exporter_list})
          AND importer NOT IN ({exporter_list})
          AND hs6 IN ({hs6_list})
          AND year BETWEEN {y0} AND {y1}
        GROUP BY hs6, year
    """
    db_rows = con.execute(query).fetchall()

    value_by_hs6_year: dict[tuple[str, int], float] = {(r[0], r[1]): r[2] or 0.0 for r in db_rows}
    all_years = list(range(y0, y1 + 1))
    all_units = [hs6, *control_hs6]
    rows = [
        (u, t, float(np.log1p(value_by_hs6_year.get((u, t), 0.0))))
        for u in all_units
        for t in all_years
    ]

    study = run_event_study(rows, treated_unit=hs6, effective_year=effective_year, window_years=window_years)

    return EventDiDResult(
        event=event,
        hs6=hs6,
        status="ok",
        exporter_codes=exporter_codes,
        n_control_units=len(control_hs6),
        study=study,
        same_hs6_contaminating_events=_contaminating_events(event, register.events, hs6, window_years),
    )


def run_all(
    con: duckdb.DuckDBPyConnection, register: RegisterLoadResult, window_years: int = 5
) -> list[EventDiDResult]:
    return [run_event_did(con, event, register, window_years=window_years) for event in register.events]
