"""STEP 1 entrypoint: build the trade panel and report its statistics."""

from __future__ import annotations

from displacement_observatory.config import BACI_ZIP_PATH, CHEMICAL_HS2_CHAPTERS
from displacement_observatory.db import connect
from displacement_observatory.ingest.baci import build_panel
from displacement_observatory.ingest.comtrade import fetch_recent_years
from displacement_observatory.panel_stats import compute_panel_stats


def main() -> None:
    con = connect()
    try:
        print(f"Loading BACI from {BACI_ZIP_PATH} (chapters {CHEMICAL_HS2_CHAPTERS})...")
        summary = build_panel(zip_path=BACI_ZIP_PATH, chapters=CHEMICAL_HS2_CHAPTERS, con=con)
        print(
            f"Loaded {summary['total_rows']:,} rows across "
            f"{len(summary['years_loaded'])} years; "
            f"{summary['countries_loaded']} country codes, "
            f"{summary['products_loaded']} HS6 product codes in metadata."
        )

        comtrade_years = [max(summary["years_loaded"]) + 1] if summary["years_loaded"] else []
        comtrade_result = fetch_recent_years(con, comtrade_years, chapters=CHEMICAL_HS2_CHAPTERS)
        if comtrade_result.get("skipped"):
            print(f"Comtrade fill-in skipped: {comtrade_result['reason']}")
        else:
            print(f"Comtrade fill-in loaded: {comtrade_result['rows_per_year']}")

        print()
        print("=== PANEL STATISTICS ===")
        stats = compute_panel_stats(con)
        print(stats.report())
    finally:
        con.close()


if __name__ == "__main__":
    main()
