"""STEP 6: forward watchlist -- append-only, timestamped forecasts.

Forecasts are written to a JSONL file and NEVER edited or deleted after
being made; the whole point is that a forecast made 2026-09-18 must be
checkable later against what actually happened without anyone being able
to quietly revise it after the fact. This module intentionally exposes no
update/delete function -- only append_forecast (write) and load_forecasts
(read) and score_forecast (read-only comparison against the trade panel).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path

import duckdb

FORECASTS_PATH = Path(__file__).resolve().parents[3] / "data" / "watchlist" / "forecasts.jsonl"


@dataclass(frozen=True)
class Forecast:
    forecast_id: str
    made_at: str  # ISO timestamp, set once, never changed
    substance: str
    jurisdiction: str
    hs6: str
    predicted_effective_date: str  # best current estimate; may itself be uncertain -- see basis
    effective_date_basis: str
    predicted_destinations: list[str]
    destination_reasoning: str
    confidence: float
    citation_url: str


def append_forecast(forecast: Forecast) -> None:
    FORECASTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing_ids = {f.forecast_id for f in load_forecasts()}
    if forecast.forecast_id in existing_ids:
        raise ValueError(f"forecast_id {forecast.forecast_id!r} already exists -- forecasts are append-only, never edited")
    with open(FORECASTS_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(forecast)) + "\n")


def load_forecasts() -> list[Forecast]:
    if not FORECASTS_PATH.exists():
        return []
    out = []
    with open(FORECASTS_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(Forecast(**json.loads(line)))
    return out


@dataclass
class ScoreResult:
    forecast: Forecast
    status: str  # "pending", "scored"
    detail: str
    destination_growth_pct: dict[str, float] | None = None


def score_forecast(con: duckdb.DuckDBPyConnection, forecast: Forecast, as_of: date | None = None) -> ScoreResult:
    """Read-only: compares predicted destinations' import growth of the
    forecasted HS6 against a pre-forecast baseline, using whatever panel
    data is available as of `as_of` (defaults to today). Does not touch
    the forecast record itself.
    """
    as_of = as_of or date.today()
    eff_date = date.fromisoformat(forecast.predicted_effective_date)
    if as_of < eff_date:
        return ScoreResult(
            forecast=forecast, status="pending",
            detail=f"predicted effective date {eff_date} has not arrived yet (as of {as_of})",
        )

    panel_max_year = con.execute("SELECT max(year) FROM trade_flows").fetchone()[0]
    if panel_max_year is None or panel_max_year < eff_date.year:
        return ScoreResult(
            forecast=forecast, status="pending",
            detail=f"effective date has passed but the trade panel does not yet cover {eff_date.year} (max year: {panel_max_year})",
        )

    made_year = datetime.fromisoformat(forecast.made_at).year
    baseline_years = (made_year - 3, made_year - 1)
    post_years = (eff_date.year, min(eff_date.year + 2, panel_max_year))

    growth: dict[str, float] = {}
    for dest_name in forecast.predicted_destinations:
        row = con.execute(
            """
            SELECT c.country_code FROM countries c
            WHERE c.country_name = ? AND c.source = 'BACI'
            LIMIT 1
            """,
            [dest_name],
        ).fetchone()
        if row is None:
            growth[dest_name] = float("nan")
            continue
        dest_code = row[0]

        def total(y_lo, y_hi):
            r = con.execute(
                "SELECT sum(value_kusd) FROM trade_flows WHERE hs6 = ? AND importer = ? AND year BETWEEN ? AND ?",
                [forecast.hs6, dest_code, y_lo, y_hi],
            ).fetchone()
            return r[0] or 0.0

        pre = total(*baseline_years)
        post = total(*post_years)
        growth[dest_name] = (100.0 * (post - pre) / pre) if pre > 0 else float("nan")

    return ScoreResult(
        forecast=forecast, status="scored",
        detail=f"import growth of HS6 {forecast.hs6} into predicted destinations, {baseline_years} baseline vs {post_years} post-period",
        destination_growth_pct=growth,
    )
