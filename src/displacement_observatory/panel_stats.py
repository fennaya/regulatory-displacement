"""Summary statistics for the trade panel (STEP 1 deliverable)."""

from __future__ import annotations

from dataclasses import dataclass

import duckdb


@dataclass
class PanelStats:
    year_min: int | None
    year_max: int | None
    country_count: int
    hs6_count: int
    total_rows: int
    missing_quantity_rows: int
    missing_quantity_share: float
    rows_by_source: dict[str, int]

    def report(self) -> str:
        if self.total_rows == 0:
            return "Panel is empty."
        lines = [
            f"Year range:        {self.year_min}-{self.year_max}",
            f"Country count:     {self.country_count:,} (distinct reporters, as exporter or importer)",
            f"HS6 product count: {self.hs6_count:,}",
            f"Total rows:        {self.total_rows:,}",
            f"Missing quantity:  {self.missing_quantity_rows:,} rows "
            f"({self.missing_quantity_share:.1%} of total)",
            "Rows by source:    "
            + ", ".join(f"{k}={v:,}" for k, v in sorted(self.rows_by_source.items())),
        ]
        return "\n".join(lines)


def compute_panel_stats(con: duckdb.DuckDBPyConnection) -> PanelStats:
    row = con.execute(
        """
        SELECT
            min(year),
            max(year),
            count(*),
            sum(CASE WHEN quantity_tons IS NULL THEN 1 ELSE 0 END),
            count(DISTINCT hs6)
        FROM trade_flows
        """
    ).fetchone()
    year_min, year_max, total_rows, missing_qty, hs6_count = row

    country_count = con.execute(
        """
        SELECT count(DISTINCT c) FROM (
            SELECT exporter AS c FROM trade_flows
            UNION
            SELECT importer AS c FROM trade_flows
        )
        """
    ).fetchone()[0]

    rows_by_source = dict(
        con.execute("SELECT source, count(*) FROM trade_flows GROUP BY source").fetchall()
    )

    total_rows = total_rows or 0
    missing_qty = missing_qty or 0
    share = (missing_qty / total_rows) if total_rows else 0.0

    return PanelStats(
        year_min=year_min,
        year_max=year_max,
        country_count=country_count or 0,
        hs6_count=hs6_count or 0,
        total_rows=total_rows,
        missing_quantity_rows=missing_qty,
        missing_quantity_share=share,
        rows_by_source=rows_by_source,
    )
