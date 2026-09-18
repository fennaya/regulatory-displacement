"""DuckDB connection helper."""

from __future__ import annotations

import duckdb

from displacement_observatory.config import DUCKDB_PATH, PROCESSED_DIR

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS trade_flows (
    year            INTEGER NOT NULL,
    hs6             VARCHAR NOT NULL,
    exporter        INTEGER NOT NULL,
    importer        INTEGER NOT NULL,
    value_kusd      DOUBLE,
    quantity_tons   DOUBLE,
    source          VARCHAR NOT NULL,
    source_version  VARCHAR NOT NULL,
    retrieved_at    TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS countries (
    country_code    INTEGER NOT NULL,
    country_name    VARCHAR,
    country_iso3    VARCHAR,
    source          VARCHAR NOT NULL,
    source_version  VARCHAR NOT NULL,
    PRIMARY KEY (country_code, source, source_version)
);

CREATE TABLE IF NOT EXISTS hs6_products (
    hs6             VARCHAR NOT NULL,
    description     VARCHAR,
    source          VARCHAR NOT NULL,
    source_version  VARCHAR NOT NULL,
    PRIMARY KEY (hs6, source, source_version)
);
"""


def connect(path=None, read_only: bool = False) -> duckdb.DuckDBPyConnection:
    """Open the observatory DuckDB database, creating the schema if needed."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(path or DUCKDB_PATH), read_only=read_only)
    if not read_only:
        con.execute(SCHEMA_SQL)
    return con
