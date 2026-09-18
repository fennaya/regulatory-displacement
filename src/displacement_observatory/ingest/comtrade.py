"""UN Comtrade ingest for years not yet covered by a BACI release.

Requires a free UN Comtrade API subscription key
(https://comtradedeveloper.un.org/) in the COMTRADE_API_KEY environment
variable. Not configured yet: `fetch_recent_years` is a no-op until a key is
set, so it is safe to call unconditionally from the pipeline.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

import duckdb

from displacement_observatory.config import CHEMICAL_HS2_CHAPTERS, COMTRADE_API_KEY_ENV

SOURCE = "COMTRADE"


def fetch_recent_years(
    con: duckdb.DuckDBPyConnection,
    years: list[int],
    chapters: tuple[str, ...] = CHEMICAL_HS2_CHAPTERS,
    reporters: list[str] | None = None,
) -> dict:
    """Fetch bilateral flows for `years` via comtradeapicall and load them into trade_flows.

    Returns a dict with what was (or wasn't) loaded. If no API key is
    configured this is a deliberate no-op, not an error, since Comtrade is
    only meant to fill the gap after the latest BACI release.
    """
    api_key = os.environ.get(COMTRADE_API_KEY_ENV)
    if not api_key:
        return {
            "skipped": True,
            "reason": f"{COMTRADE_API_KEY_ENV} not set; see ingest/comtrade.py docstring",
            "years_requested": years,
        }

    import comtradeapicall  # imported lazily: optional dependency path

    retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    loaded_per_year: dict[int, int] = {}
    for year in years:
        for chapter in chapters:
            df = comtradeapicall.previewFinalData(
                typeCode="C",
                freqCode="A",
                clCode="HS",
                period=str(year),
                reporterCode=None,
                cmdCode=chapter,
                flowCode="X",
                partnerCode=None,
                partner2Code=None,
                customsCode=None,
                motCode=None,
                maxRecords=250000,
                format_output="JSON",
                countOnly=None,
                includeDesc=True,
                subscription_key=api_key,
            )
            if df is None or df.empty:
                continue
            con.register("_comtrade_chunk", df)
            con.execute(
                f"""
                INSERT INTO trade_flows
                SELECT
                    CAST(period AS INTEGER)               AS year,
                    cmdCode                                AS hs6,
                    CAST(reporterCode AS INTEGER)          AS exporter,
                    CAST(partnerCode AS INTEGER)           AS importer,
                    TRY_CAST(primaryValue AS DOUBLE)       AS value_kusd,
                    TRY_CAST(netWgt AS DOUBLE) / 1000.0    AS quantity_tons,
                    '{SOURCE}'                             AS source,
                    'live'                                 AS source_version,
                    TIMESTAMP '{retrieved_at}'              AS retrieved_at
                FROM _comtrade_chunk
                WHERE length(cmdCode) = 6
                """
            )
            con.unregister("_comtrade_chunk")
            loaded_per_year[year] = loaded_per_year.get(year, 0) + len(df)

    return {"skipped": False, "rows_per_year": loaded_per_year}
