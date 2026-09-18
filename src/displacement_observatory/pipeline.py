"""Runs the full analysis pipeline once and bundles the results, so the
dashboard (and any CLI report) doesn't recompute ~9 two-way-FE regressions
per request.
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb

from displacement_observatory.analysis.competing_explanations import (
    CompetingExplanationsResult,
    run_competing_explanations,
)
from displacement_observatory.analysis.diD import EventDiDResult, run_all
from displacement_observatory.config import CHEMICAL_HS2_CHAPTERS
from displacement_observatory.panel_stats import PanelStats, compute_panel_stats
from displacement_observatory.register.mappings import MappingFile, load_latest_mappings
from displacement_observatory.register.store import RegisterLoadResult, load_events
from displacement_observatory.validation.rediscovery import RediscoverySummary, run_rediscovery
from displacement_observatory.watchlist.forecasts import Forecast, ScoreResult, load_forecasts, score_forecast


@dataclass
class PipelineBundle:
    panel_stats: PanelStats
    register: RegisterLoadResult
    mappings: MappingFile
    did_results: list[EventDiDResult]
    competing: dict[str, CompetingExplanationsResult]
    rediscovery: RediscoverySummary
    forecasts: list[Forecast]
    forecast_scores: list[ScoreResult]

    def did_by_id(self) -> dict[str, EventDiDResult]:
        return {r.event.event_id: r for r in self.did_results}


def run_pipeline(con: duckdb.DuckDBPyConnection, register_version: int = 1, window_years: int = 5) -> PipelineBundle:
    panel_stats = compute_panel_stats(con)
    register = load_events(version=register_version)
    mappings = load_latest_mappings()

    did_results = run_all(con, register, window_years=window_years)

    restricted_hs6 = {c.hs6 for e in register.events for c in e.hs6_candidates}
    control_hs6_rows = con.execute(
        f"SELECT DISTINCT hs6 FROM trade_flows WHERE substr(hs6,1,2) IN "
        f"({', '.join(repr(c) for c in CHEMICAL_HS2_CHAPTERS)})"
    ).fetchall()
    control_hs6 = sorted({r[0] for r in control_hs6_rows} - restricted_hs6)

    competing = {
        r.event.event_id: run_competing_explanations(con, r, control_hs6)
        for r in did_results
        if r.status == "ok"
    }

    rediscovery = run_rediscovery(did_results)

    forecasts = load_forecasts()
    forecast_scores = [score_forecast(con, f) for f in forecasts]

    return PipelineBundle(
        panel_stats=panel_stats,
        register=register,
        mappings=mappings,
        did_results=did_results,
        competing=competing,
        rediscovery=rediscovery,
        forecasts=forecasts,
        forecast_scores=forecast_scores,
    )
