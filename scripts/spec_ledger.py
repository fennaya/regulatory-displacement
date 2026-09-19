"""Recompute the Stage A-H specification ledger from the repo's own code.
Writes data/attack/spec_ledger.json."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np

from displacement_observatory.analysis.basket_attack import (
    build_hs6_year_bloc_panel, to_outcome_frame,
)
from displacement_observatory.analysis.destination_groups import (
    load_destination_groups, resolve_iso3_to_codes, run_event_study_for_destination_group,
)
from displacement_observatory.analysis.ppml import build_importer_product_year_panel, fit_flowlevel_log_ols_att
from displacement_observatory.analysis.spec_ledger import DISCARDED_ENTRIES, LedgerEntry, summarize
from displacement_observatory.analysis.staggered import first_restriction_year, fit_staggered
from displacement_observatory.config import CHEMICAL_HS2_CHAPTERS
from displacement_observatory.db import connect
from displacement_observatory.pipeline import run_pipeline

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parents[1] / "data" / "attack" / "spec_ledger.json"


def excludes_zero(lo, hi):
    return bool(lo > 0 or hi < 0)


def main() -> None:
    con = connect(read_only=True)
    bundle = run_pipeline(con)
    entries: list[LedgerEntry] = list(DISCARDED_ENTRIES)
    detail: dict = {}

    # Stage 3 / B.4 / C / D / B.1 (PPML) / E from the pipeline's own comparison rows
    by_method: dict[str, list] = {}
    for comp in bundle.package_comparisons.values():
        for r in comp.rows:
            key = r.method.split(" (")[0].split(" at ")[0]
            by_method.setdefault(key, []).append((comp.package_id, r))
    labels = {
        "OLD OLS-TWFE": "Stage 3 original OLS-TWFE, one per package",
        "TRUNCATED": "Stage B.4 truncated window",
        "TRIPLE-DIFF": "Stage C triple difference",
        "MATCHED CONTROLS": "Stage D matched controls",
        "PPML": "Stage B.1 PPML (levels, keeps zeros)",
        "CLUSTERED SE": "Stage E exporter-product clustered SE",
    }
    for key, label in labels.items():
        rows = by_method.get(key, [])
        clears = [(p, r) for p, r in rows if excludes_zero(r.ci_low, r.ci_high)]
        entries.append(LedgerEntry(label.split(" ")[0] + " " + label.split(" ")[1], label, len(rows), len(clears), "live",
                                   "clears: " + (", ".join(f"{p} ({r.coef:+.3f})" for p, r in clears) or "none")))
        detail[key] = [{"package": p, "coef": r.coef, "ci": [r.ci_low, r.ci_high]} for p, r in rows]

    # Stage B.1 flow-level log-OLS comparison (zeros dropped)
    restricted = {c.hs6 for e in bundle.register.events for c in e.hs6_candidates}
    ctl_rows = con.execute(
        f"SELECT DISTINCT hs6 FROM trade_flows WHERE substr(hs6,1,2) IN ({', '.join(repr(c) for c in CHEMICAL_HS2_CHAPTERS)})"
    ).fetchall()
    control_hs6 = sorted({r[0] for r in ctl_rows} - restricted)
    did_by_id = bundle.did_by_id()
    flow_rows = []
    for p in bundle.packages:
        r = did_by_id.get(p.event_ids[0])
        if r is None or r.status != "ok":
            continue
        eff = p.effective_date.year
        ks = sorted(r.study.relative_years)
        panel = build_importer_product_year_panel(con, p, r.exporter_codes, control_hs6, eff + ks[0], eff + ks[-1])
        est = fit_flowlevel_log_ols_att(panel)
        flow_rows.append((p.package_id, est))
    clears = [(p, e) for p, e in flow_rows if excludes_zero(e.ci_low, e.ci_high)]
    entries.append(LedgerEntry("Stage B.1", "flow-level log-OLS (zeros dropped)", len(flow_rows), len(clears), "live",
                               "clears: " + (", ".join(f"{p} ({e.coef:+.3f})" for p, e in clears) or "none")))
    detail["flow_level_log_ols"] = [{"package": p, "coef": e.coef, "ci": [e.ci_low, e.ci_high]} for p, e in flow_rows]

    # Stage B.2/B.3 staggered, log scale (naive pooled TWFE and did2s)
    gmap = first_restriction_year(bundle.register.events)
    all_hs6 = sorted({r[0] for r in ctl_rows})
    val = build_hs6_year_bloc_panel(con, all_hs6, gmap, 1995, 2024)
    eu = to_outcome_frame(val, "eu")
    st = [fit_staggered(eu, estimator=e) for e in ("twfe", "did2s")]
    st_clears = [s for s in st if excludes_zero(s.ci_low, s.ci_high)]
    entries.append(LedgerEntry("Stage B.2/B.3", "staggered pooled TWFE and did2s, log scale (same estimand)", 2, len(st_clears), "live",
                               f"coefs {[round(s.coef, 3) for s in st]}"))

    # Stage F destination heterogeneity: 5 packages x 2 groups
    groups = load_destination_groups()
    hi = resolve_iso3_to_codes(con, groups.high_exposure_iso3, "BACI", "202601")
    lo = resolve_iso3_to_codes(con, groups.low_exposure_iso3, "BACI", "202601")
    f_rows = []
    for p in bundle.packages:
        r = did_by_id.get(p.event_ids[0])
        if r is None or r.status != "ok":
            continue
        eff = p.effective_date.year
        ks = sorted(r.study.relative_years)
        k = max(x for x in ks if x >= 0)
        for gname_, codes in (("high", hi), ("low", lo)):
            s = run_event_study_for_destination_group(con, p.hs6, control_hs6, r.exporter_codes, codes,
                                                     eff + ks[0], eff + ks[-1], eff, window_years=5)
            f_rows.append((p.package_id, gname_, s.coef[k], s.ci_low[k], s.ci_high[k]))
    f_clears = [x for x in f_rows if excludes_zero(x[3], x[4])]
    entries.append(LedgerEntry("Stage F", "destination heterogeneity, 5 packages x {high, low}", len(f_rows), len(f_clears), "live",
                               "clears: " + (", ".join(f"{p}/{g} ({c:+.3f})" for p, g, c, _, _ in f_clears) or "none")))

    summary = summarize(entries)
    out = {
        "entries": [e.__dict__ for e in entries],
        "summary": summary,
        "detail": detail,
        "notes": [
            "Counts are per (package x specification) estimate; substance-level duplicates (3 neonicotinoids, 2 chlorpyrifos) are NOT counted separately.",
            "Chance arithmetic assumes independent tests; the tests share one BACI panel, so it is a rough guide, not a p-value.",
            "Discarded entries are reconstructed by hand from the working history; anything tried and not recorded is missing, so n is a lower bound.",
            "Stage A (overlap audit), Stage G (power) and Stage 4 (competing explanations) produce no significance test and are not counted.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    print(json.dumps({"entries": out["entries"], "summary": summary}, indent=2, default=float))


if __name__ == "__main__":
    main()
