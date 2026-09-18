from datetime import datetime

from displacement_observatory.panel_stats import compute_panel_stats

ROWS = [
    # year, hs6,      exporter, importer, value, quantity
    (2018, "380810", 1, 2, 100.0, 5.0),
    (2018, "380810", 1, 3, 50.0, None),
    (2019, "290110", 2, 1, 200.0, 10.0),
    (2019, "290110", 4, 1, 75.0, None),
]


def _insert_rows(con, rows, source="BACI", version="v1"):
    now = datetime(2026, 1, 1)
    for year, hs6, exp, imp, value, qty in rows:
        con.execute(
            "INSERT INTO trade_flows VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [year, hs6, exp, imp, value, qty, source, version, now],
        )


def test_compute_panel_stats_basic(con):
    _insert_rows(con, ROWS)
    stats = compute_panel_stats(con)

    assert stats.year_min == 2018
    assert stats.year_max == 2019
    assert stats.total_rows == 4
    assert stats.hs6_count == 2
    # distinct country codes across exporter+importer: {1,2,3,4}
    assert stats.country_count == 4
    assert stats.missing_quantity_rows == 2
    assert stats.missing_quantity_share == 0.5
    assert stats.rows_by_source == {"BACI": 4}


def test_compute_panel_stats_empty(con):
    stats = compute_panel_stats(con)
    assert stats.total_rows == 0
    assert stats.missing_quantity_share == 0.0
    assert "empty" in stats.report().lower()


def test_report_is_readable_string(con):
    _insert_rows(con, ROWS)
    stats = compute_panel_stats(con)
    text = stats.report()
    assert "2018-2019" in text
    assert "50.0%" in text
