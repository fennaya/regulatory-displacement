from datetime import date

import numpy as np

from displacement_observatory.analysis.comparison import build_package_comparison
from displacement_observatory.analysis.diD import run_event_did
from displacement_observatory.analysis.overlap import build_overlap_matrix, classify_packages, compute_windows
from displacement_observatory.analysis.packages import build_treatment_packages
from displacement_observatory.register.schema import Citation, HS6Candidate, RestrictionEvent
from displacement_observatory.register.store import RegisterLoadResult

EU_EXPORTER = 251
ROW_EXPORTER = 156
IMPORTER = 842


def _seed_full_panel(con, years, control_hs6_list, treated_hs6, effective_year):
    rng = np.random.default_rng(3)
    rows = []
    for hs6 in [treated_hs6, *control_hs6_list]:
        eu_base = rng.uniform(80, 150)
        row_base = rng.uniform(80, 150)
        for y in years:
            eu_v = eu_base * (1 + rng.normal(0, 0.03))
            row_v = row_base * (1 + rng.normal(0, 0.03))
            if hs6 == treated_hs6 and y >= effective_year:
                eu_v *= 1.5
            rows.append((y, hs6, EU_EXPORTER, IMPORTER, eu_v, None, "BACI", "t", "2026-09-18 00:00:00"))
            rows.append((y, hs6, ROW_EXPORTER, IMPORTER, row_v, None, "BACI", "t", "2026-09-18 00:00:00"))
    con.executemany("INSERT INTO trade_flows VALUES (?,?,?,?,?,?,?,?,?)", rows)
    con.executemany(
        "INSERT INTO countries (country_code, country_name, country_iso3, source, source_version) VALUES (?,?,?,?,?)",
        [(EU_EXPORTER, "France", "FRA", "BACI", "t"), (ROW_EXPORTER, "China", "CHN", "BACI", "t"),
         (IMPORTER, "USA", "USA", "BACI", "t")],
    )


def test_build_package_comparison_smoke(con):
    years = list(range(2010, 2021))
    control_hs6 = [f"38089{i}" for i in range(6)]
    treated_hs6 = "380810"
    _seed_full_panel(con, years, control_hs6, treated_hs6, effective_year=2015)

    event = RestrictionEvent(
        event_id="ev1", substance="X", jurisdiction="EU", restriction_type="ban", scope="all",
        decision_date=date(2014, 1, 1), effective_date=date(2015, 1, 1),
        citation=Citation(source_document="d", source_clause="c", retrieved_at=date(2026, 9, 18)),
        hs6_candidates=[HS6Candidate(hs6=treated_hs6, confidence=0.5, reasoning="r", imprecision="i")],
    )
    register = RegisterLoadResult(events=[event], dropped=[])
    packages = build_treatment_packages(register)
    pkg = packages[0]

    result = run_event_did(con, event, register, window_years=5, source="BACI", source_version="t")
    windows = compute_windows(packages, {"ev1": result})
    flags = build_overlap_matrix(packages, windows, {"ev1": result})
    audits = {a.package_id: a for a in classify_packages(windows, flags)}

    comparison = build_package_comparison(
        con, pkg, audits[pkg.package_id], register, result, control_hs6, flags,
        source="BACI", source_version="t",
    )

    methods = {row.method for row in comparison.rows}
    assert "OLD OLS-TWFE (Stage 3, unrepaired)" in methods
    assert "TRIPLE-DIFF (Stage C, RoW-netted)" in methods
    assert "MATCHED CONTROLS (Stage D)" in methods
    assert "PPML (Stage B.1, levels, keeps zeros)" in methods
    assert "CLUSTERED SE (Stage E, exporter-product)" in methods
    assert all(row.coef is not None for row in comparison.rows)
