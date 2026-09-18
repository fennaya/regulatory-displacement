"""Project-wide paths and constants for the Displacement Observatory."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

DUCKDB_PATH = PROCESSED_DIR / "observatory.duckdb"

# --- BACI (CEPII) -----------------------------------------------------------
# HS92 is the revision with the longest, most consistent coverage (1995-2024):
# CEPII converts every later HS revision back to HS92 codes for comparability,
# which is what an event study spanning many years needs.
BACI_VERSION = "202601"
BACI_REVISION = "HS92"
BACI_ZIP_URL = (
    "https://www.cepii.fr/DATA_DOWNLOAD/baci/data/"
    f"BACI_{BACI_REVISION}_V{BACI_VERSION}.zip"
)
BACI_ZIP_PATH = RAW_DIR / f"BACI_{BACI_REVISION}_V{BACI_VERSION}.zip"

# Scope, deliberately narrow (see project brief): pesticides live in HS
# chapter 38 (heading 3808 specifically). Hazardous industrial chemicals
# more broadly are concentrated in chapters 28 (inorganic chemicals, e.g.
# mercury/lead compounds) and 29 (organic chemicals, e.g. PCBs, ozone-
# depleting substances, POPs precursors). Restricting the panel to these
# three HS2 chapters keeps ingest/storage proportionate to the stated scope
# while still giving the difference-in-differences step a pool of
# never-restricted "comparable products, same exporter, same period"
# control goods drawn from the same broad industry rather than the whole
# economy.
#
# This is a known simplification: a handful of Rotterdam Convention PIC
# substances sit outside these chapters (e.g. asbestos in chapters 25/68,
# tributyltin compounds are in 29 so those are fine). Step 2's substance ->
# HS6 mapping will surface any candidate code that falls outside this scope
# so the gap is visible rather than silently dropped.
CHEMICAL_HS2_CHAPTERS: tuple[str, ...] = ("28", "29", "38")

COMTRADE_API_KEY_ENV = "COMTRADE_API_KEY"
