"""Jurisdiction membership, resolved to BACI country codes as of a date.

Only "EU" is needed for the current register (see data/register/events).
Membership dates are accession dates for the European Communities/EU;
this is a real, sourced table, not a placeholder, because it directly
defines the treated exporter set and the excluded ("still restricted")
destination set for every EU event in the register.
"""

from __future__ import annotations

from datetime import date

import duckdb

# (ISO3, accession_date, exit_date-or-None). UK left 31 Jan 2020 but EU law
# continued to apply during the transition period to 31 Dec 2020; we use
# the transition end as the effective exit date for trade-law purposes.
_EU_MEMBERS: list[tuple[str, date, date | None]] = [
    ("BEL", date(1958, 1, 1), None), ("FRA", date(1958, 1, 1), None),
    ("DEU", date(1958, 1, 1), None), ("ITA", date(1958, 1, 1), None),
    ("LUX", date(1958, 1, 1), None), ("NLD", date(1958, 1, 1), None),
    ("DNK", date(1973, 1, 1), None), ("IRL", date(1973, 1, 1), None),
    ("GBR", date(1973, 1, 1), date(2020, 12, 31)),
    ("GRC", date(1981, 1, 1), None),
    ("ESP", date(1986, 1, 1), None), ("PRT", date(1986, 1, 1), None),
    ("AUT", date(1995, 1, 1), None), ("FIN", date(1995, 1, 1), None), ("SWE", date(1995, 1, 1), None),
    ("CYP", date(2004, 5, 1), None), ("CZE", date(2004, 5, 1), None), ("EST", date(2004, 5, 1), None),
    ("HUN", date(2004, 5, 1), None), ("LVA", date(2004, 5, 1), None), ("LTU", date(2004, 5, 1), None),
    ("MLT", date(2004, 5, 1), None), ("POL", date(2004, 5, 1), None), ("SVK", date(2004, 5, 1), None),
    ("SVN", date(2004, 5, 1), None),
    ("BGR", date(2007, 1, 1), None), ("ROU", date(2007, 1, 1), None),
    ("HRV", date(2013, 7, 1), None),
]


def eu_members_iso3(as_of: date) -> list[str]:
    return [iso3 for iso3, joined, left in _EU_MEMBERS if joined <= as_of and (left is None or as_of <= left)]


def resolve_country_codes(con: duckdb.DuckDBPyConnection, iso3_list: list[str], source: str, source_version: str) -> list[int]:
    if not iso3_list:
        return []
    placeholders = ", ".join("?" for _ in iso3_list)
    rows = con.execute(
        f"""
        SELECT DISTINCT country_code FROM countries
        WHERE country_iso3 IN ({placeholders}) AND source = ? AND source_version = ?
        """,
        [*iso3_list, source, source_version],
    ).fetchall()
    return [r[0] for r in rows]


def jurisdiction_exporter_codes(
    con: duckdb.DuckDBPyConnection, jurisdiction: str, as_of: date, source: str, source_version: str
) -> list[int] | None:
    """Return BACI country codes for a register `jurisdiction` string as of a date.

    Returns None if the jurisdiction doesn't resolve to a well-defined,
    single exporter bloc (e.g. a global treaty with no one exporting party) --
    callers should treat None as "cannot run an exporter-based DiD for this
    event", not as an empty set.
    """
    if jurisdiction == "EU":
        return resolve_country_codes(con, eu_members_iso3(as_of), source, source_version)
    return None
