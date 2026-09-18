"""EUR/USD annual reference rate, for the currency-effects competing
explanation in STEP 4.

Fetched live from the ECB's own statistics API (the official source for
this series) and cached to a local CSV with a retrieval timestamp, so
results are reproducible without hitting the network every run while
keeping real provenance on the data.

This is a simplification flagged in the README: our exporter bloc is
"EU member states", but not every member used the euro in every event
year (pre-2002 legacy currencies; several 2004+ accession states adopted
the euro years after joining). EUR/USD is used as a single proxy for
"the EU exporter bloc's currency vs the trade-invoicing currency" rather
than a member-state-weighted true effective rate.
"""

from __future__ import annotations

import csv
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

FX_CACHE_PATH = Path(__file__).resolve().parents[3] / "data" / "register" / "eur_usd_annual.csv"
ECB_API_URL = "https://data-api.ecb.europa.eu/service/data/EXR/A.USD.EUR.SP00.A"


def fetch_and_cache(start_year: int = 1999, end_year: int | None = None) -> Path:
    end_year = end_year or date.today().year
    url = f"{ECB_API_URL}?format=csvdata&startPeriod={start_year}&endPeriod={end_year}"
    # requests/urllib3 reliably read-timed-out against this host in this
    # environment while curl succeeded instantly; shell out rather than
    # chase a TLS/negotiation mismatch.
    proc = subprocess.run(["curl", "-sS", "--max-time", "30", url], capture_output=True, text=True, check=True)
    reader = csv.DictReader(proc.stdout.splitlines())
    rows = [(int(r["TIME_PERIOD"]), float(r["OBS_VALUE"])) for r in reader]

    retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    FX_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(FX_CACHE_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["year", "usd_per_eur", "source", "source_series", "retrieved_at"])
        for year, rate in rows:
            w.writerow([year, rate, "ECB Statistical Data Warehouse", "EXR.A.USD.EUR.SP00.A", retrieved_at])
    return FX_CACHE_PATH


def load_eur_usd_annual() -> dict[int, float]:
    if not FX_CACHE_PATH.exists():
        fetch_and_cache()
    with open(FX_CACHE_PATH, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {int(r["year"]): float(r["usd_per_eur"]) for r in reader}
