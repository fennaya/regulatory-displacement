import io
import zipfile
from pathlib import Path

from displacement_observatory.ingest.baci import build_panel

YEAR_CSV = """t,k,i,j,v,q
1995,380810,4,8,123.45,10.5
1995,380810,4,12,50.0,NA
1995,290110,4,8,75.0,3.2
1995,010121,4,8,999.0,1.0
1995,847130,4,8,200.0,7.0
"""

COUNTRY_CSV = """country_code,country_name,country_iso3
4,Afghanistan,AFG
8,Albania,ALB
12,Algeria,DZA
"""

PRODUCT_CSV = """code,description
380810,Insecticides etc.
290110,Acyclic hydrocarbons
010121,Horses
847130,Computers
"""


def _make_fake_baci_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("BACI_HS92_Y1995_V202601.csv", YEAR_CSV)
        zf.writestr("country_codes_V202601.csv", COUNTRY_CSV)
        zf.writestr("product_codes_HS92_V202601.csv", PRODUCT_CSV)


def test_build_panel_filters_to_chemical_chapters(con, tmp_path):
    zip_path = tmp_path / "fake_baci.zip"
    _make_fake_baci_zip(zip_path)

    summary = build_panel(zip_path=zip_path, chapters=("28", "29", "38"), con=con, progress=False)

    assert summary["total_rows"] == 3  # two 380810 flows (chapter 38) + one 290110 flow (chapter 29)
    assert summary["countries_loaded"] == 3
    assert summary["products_loaded"] == 4

    rows = con.execute("SELECT hs6, quantity_tons FROM trade_flows ORDER BY hs6, importer").fetchall()
    assert rows == [("290110", 3.2), ("380810", 10.5), ("380810", None)]


def test_build_panel_keeps_na_quantity_as_null(con, tmp_path):
    zip_path = tmp_path / "fake_baci2.zip"
    _make_fake_baci_zip(zip_path)

    build_panel(zip_path=zip_path, chapters=("38",), con=con, progress=False)

    rows = con.execute(
        "SELECT importer, quantity_tons FROM trade_flows WHERE hs6 = '380810' ORDER BY importer"
    ).fetchall()
    assert rows == [(8, 10.5), (12, None)]


def test_build_panel_excludes_non_chemical_chapters(con, tmp_path):
    zip_path = tmp_path / "fake_baci3.zip"
    _make_fake_baci_zip(zip_path)

    build_panel(zip_path=zip_path, chapters=("28", "29", "38"), con=con, progress=False)

    hs6_present = {r[0] for r in con.execute("SELECT DISTINCT hs6 FROM trade_flows").fetchall()}
    assert "010121" not in hs6_present  # chapter 01, live animals
    assert "847130" not in hs6_present  # chapter 84, machinery


def test_country_metadata_columns_are_not_swapped(con, tmp_path):
    # Regression test: INSERT INTO ... SELECT matches columns positionally,
    # not by alias, so a SELECT column order that doesn't match the target
    # table's declared column order silently swaps values into the wrong
    # columns. country_name and country_iso3 look enough alike (both short
    # strings) that this swap produced no error, only wrong data.
    zip_path = tmp_path / "fake_baci4.zip"
    _make_fake_baci_zip(zip_path)

    build_panel(zip_path=zip_path, chapters=("38",), con=con, progress=False)

    row = con.execute("SELECT country_name, country_iso3 FROM countries WHERE country_code = 4").fetchone()
    assert row == ("Afghanistan", "AFG")
