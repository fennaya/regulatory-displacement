"""Load the BACI bilateral trade panel, filtered to the project's chemical
scope, into DuckDB directly from the downloaded zip (no full extraction).
"""

from __future__ import annotations

import re
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import duckdb

from displacement_observatory.config import (
    BACI_REVISION,
    BACI_VERSION,
    BACI_ZIP_PATH,
    CHEMICAL_HS2_CHAPTERS,
)
from displacement_observatory.db import connect

SOURCE = "BACI"

_YEAR_FILE_RE = re.compile(rf"BACI_{BACI_REVISION}_Y(\d{{4}})_V\d+\.csv$", re.IGNORECASE)
_COUNTRY_FILE_RE = re.compile(r"country_codes.*\.csv$", re.IGNORECASE)
_PRODUCT_FILE_RE = re.compile(rf"product_codes_{BACI_REVISION}.*\.csv$", re.IGNORECASE)


def find_members(zf: zipfile.ZipFile) -> tuple[dict[int, str], str | None, str | None]:
    """Locate the per-year trade files and the two metadata files inside the zip."""
    year_members: dict[int, str] = {}
    country_member: str | None = None
    product_member: str | None = None
    for name in zf.namelist():
        base = name.rsplit("/", 1)[-1]
        m = _YEAR_FILE_RE.match(base)
        if m:
            year_members[int(m.group(1))] = name
            continue
        if _COUNTRY_FILE_RE.match(base):
            country_member = name
        elif _PRODUCT_FILE_RE.match(base):
            product_member = name
    return year_members, country_member, product_member


def _pick_column(columns: list[str], *candidates: str) -> str | None:
    lowered = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand in lowered:
            return lowered[cand]
    for cand in candidates:
        for lc, orig in lowered.items():
            if cand in lc:
                return orig
    return None


def load_country_metadata(zf: zipfile.ZipFile, member: str | None, con: duckdb.DuckDBPyConnection) -> int:
    if member is None:
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(zf.extract(member, path=tmp))
        cols = [r[0] for r in con.execute(
            "DESCRIBE SELECT * FROM read_csv_auto(?, ALL_VARCHAR=TRUE)", [str(path)]
        ).fetchall()]
        code_col = _pick_column(cols, "country_code", "code")
        name_col = _pick_column(cols, "country_name", "name")
        iso3_col = _pick_column(cols, "country_iso3", "iso3", "iso_3")
        if code_col is None:
            raise RuntimeError(f"Could not find a country code column among {cols} in {member}")

        con.execute("DELETE FROM countries WHERE source = ? AND source_version = ?", [SOURCE, BACI_VERSION])
        select_parts = [f'CAST("{code_col}" AS INTEGER) AS country_code']
        select_parts.append(f'"{name_col}" AS country_name' if name_col else "NULL AS country_name")
        select_parts.append(f'"{iso3_col}" AS country_iso3' if iso3_col else "NULL AS country_iso3")
        con.execute(
            f"""
            INSERT INTO countries (country_code, country_name, country_iso3, source, source_version)
            SELECT {", ".join(select_parts)}, '{SOURCE}', '{BACI_VERSION}'
            FROM read_csv_auto(?, ALL_VARCHAR=TRUE)
            """,
            [str(path)],
        )
        return con.execute(
            "SELECT count(*) FROM countries WHERE source = ? AND source_version = ?", [SOURCE, BACI_VERSION]
        ).fetchone()[0]


def load_product_metadata(zf: zipfile.ZipFile, member: str | None, con: duckdb.DuckDBPyConnection) -> int:
    if member is None:
        return 0
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(zf.extract(member, path=tmp))
        cols = [r[0] for r in con.execute(
            "DESCRIBE SELECT * FROM read_csv_auto(?, ALL_VARCHAR=TRUE)", [str(path)]
        ).fetchall()]
        code_col = _pick_column(cols, "code", "hs6", "product_code")
        desc_col = _pick_column(cols, "description", "product_name", "name")
        if code_col is None:
            raise RuntimeError(f"Could not find a product code column among {cols} in {member}")

        con.execute("DELETE FROM hs6_products WHERE source = ? AND source_version = ?", [SOURCE, BACI_VERSION])
        desc_expr = f'"{desc_col}" AS description' if desc_col else "NULL AS description"
        con.execute(
            f"""
            INSERT INTO hs6_products (hs6, description, source, source_version)
            SELECT "{code_col}" AS hs6, {desc_expr}, '{SOURCE}', '{BACI_VERSION}'
            FROM read_csv_auto(?, ALL_VARCHAR=TRUE)
            """,
            [str(path)],
        )
        return con.execute(
            "SELECT count(*) FROM hs6_products WHERE source = ? AND source_version = ?", [SOURCE, BACI_VERSION]
        ).fetchone()[0]


def load_year(
    zf: zipfile.ZipFile,
    member: str,
    year: int,
    con: duckdb.DuckDBPyConnection,
    chapters: tuple[str, ...],
) -> int:
    """Extract one year's CSV to a scratch file, filter+load it, then discard the scratch file."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(zf.extract(member, path=tmp))
        retrieved_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        chapter_list = ", ".join(f"'{c}'" for c in chapters)

        con.execute(
            "DELETE FROM trade_flows WHERE year = ? AND source = ? AND source_version = ?",
            [year, SOURCE, BACI_VERSION],
        )
        con.execute(
            f"""
            INSERT INTO trade_flows
                (year, hs6, exporter, importer, value_kusd, quantity_tons, source, source_version, retrieved_at)
            SELECT
                CAST(t AS INTEGER)                     AS year,
                k                                       AS hs6,
                CAST(i AS INTEGER)                      AS exporter,
                CAST(j AS INTEGER)                      AS importer,
                TRY_CAST(v AS DOUBLE)                   AS value_kusd,
                TRY_CAST(NULLIF(q, 'NA') AS DOUBLE)     AS quantity_tons,
                '{SOURCE}'                              AS source,
                '{BACI_VERSION}'                        AS source_version,
                TIMESTAMP '{retrieved_at}'               AS retrieved_at
            FROM read_csv_auto(?, ALL_VARCHAR=TRUE)
            WHERE substr(k, 1, 2) IN ({chapter_list})
            """,
            [str(path)],
        )
    return con.execute(
        "SELECT count(*) FROM trade_flows WHERE year = ? AND source = ? AND source_version = ?",
        [year, SOURCE, BACI_VERSION],
    ).fetchone()[0]


def build_panel(
    zip_path: Path = BACI_ZIP_PATH,
    chapters: tuple[str, ...] = CHEMICAL_HS2_CHAPTERS,
    con: duckdb.DuckDBPyConnection | None = None,
    years: Iterable[int] | None = None,
    progress: bool = True,
) -> dict:
    """Load BACI, filtered to `chapters`, into the trade_flows/countries/hs6_products tables."""
    own_con = con is None
    if own_con:
        con = connect()
    try:
        with zipfile.ZipFile(zip_path) as zf:
            year_members, country_member, product_member = find_members(zf)
            if not year_members:
                raise RuntimeError(f"No BACI year files found in {zip_path}")

            n_countries = load_country_metadata(zf, country_member, con)
            n_products = load_product_metadata(zf, product_member, con)

            target_years = sorted(years) if years is not None else sorted(year_members)
            per_year_rows: dict[int, int] = {}
            for year in target_years:
                member = year_members.get(year)
                if member is None:
                    continue
                n = load_year(zf, member, year, con, chapters)
                per_year_rows[year] = n
                if progress:
                    print(f"  {year}: {n:,} rows kept (chapters {chapters})", flush=True)

        return {
            "countries_loaded": n_countries,
            "products_loaded": n_products,
            "years_loaded": target_years,
            "rows_per_year": per_year_rows,
            "total_rows": sum(per_year_rows.values()),
        }
    finally:
        if own_con:
            con.close()
