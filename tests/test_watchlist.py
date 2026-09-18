from datetime import date, datetime, timezone

import pytest

from displacement_observatory.watchlist import forecasts as fmod
from displacement_observatory.watchlist.forecasts import Forecast, append_forecast, load_forecasts, score_forecast


def _make_forecast(forecast_id, effective_date, made_at_year=2026, hs6="380810", destinations=None):
    return Forecast(
        forecast_id=forecast_id,
        made_at=f"{made_at_year}-01-01T00:00:00Z",
        substance="Testicide",
        jurisdiction="EU",
        hs6=hs6,
        predicted_effective_date=effective_date,
        effective_date_basis="test",
        predicted_destinations=destinations or ["Brazil"],
        destination_reasoning="test",
        confidence=0.5,
        citation_url="https://example.org",
    )


@pytest.fixture(autouse=True)
def _isolate_forecasts_file(tmp_path, monkeypatch):
    monkeypatch.setattr(fmod, "FORECASTS_PATH", tmp_path / "forecasts.jsonl")


def test_append_and_load_roundtrip():
    f = _make_forecast("f1", "2030-01-01")
    append_forecast(f)
    loaded = load_forecasts()
    assert len(loaded) == 1
    assert loaded[0] == f


def test_append_is_immutable_no_duplicate_ids():
    f = _make_forecast("f1", "2030-01-01")
    append_forecast(f)
    with pytest.raises(ValueError, match="append-only"):
        append_forecast(f)


def test_load_forecasts_empty_when_no_file():
    assert load_forecasts() == []


def test_score_forecast_pending_before_effective_date():
    f = _make_forecast("f1", "2099-01-01")
    result = score_forecast(con=None, forecast=f, as_of=date(2026, 1, 1))
    assert result.status == "pending"
    assert "has not arrived" in result.detail


def test_score_forecast_pending_when_panel_lags(con):
    con.execute(
        "INSERT INTO trade_flows VALUES (2020, '380810', 251, 76, 100.0, 10.0, 'BACI', 't', '2026-09-18 00:00:00')"
    )
    f = _make_forecast("f1", "2025-01-01")
    result = score_forecast(con, f, as_of=date(2026, 6, 1))
    assert result.status == "pending"
    assert "does not yet cover" in result.detail


def test_score_forecast_scores_when_data_available(con):
    con.execute(
        "INSERT INTO countries (country_code, country_name, country_iso3, source, source_version) VALUES (76, 'Brazil', 'BRA', 'BACI', 't')"
    )
    rows = []
    for y in [2022, 2023, 2024]:
        rows.append((y, "380810", 251, 76, 100.0, 10.0, "BACI", "t", "2026-09-18 00:00:00"))
    for y in [2025, 2026]:
        rows.append((y, "380810", 251, 76, 300.0, 10.0, "BACI", "t", "2026-09-18 00:00:00"))
    con.executemany("INSERT INTO trade_flows VALUES (?,?,?,?,?,?,?,?,?)", rows)

    f = _make_forecast("f1", "2025-01-01", made_at_year=2025, destinations=["Brazil"])
    result = score_forecast(con, f, as_of=date(2026, 12, 1))
    assert result.status == "scored"
    # baseline = 2022-2024 (3 years @ 100) = 300; post = 2025-2026 (2 years @ 300) = 600 -> +100%
    assert result.destination_growth_pct["Brazil"] == pytest.approx(100.0)
