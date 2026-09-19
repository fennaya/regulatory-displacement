"""Close-out step 3: recompute Stage G from placebo-derived SEs.
Writes data/attack/stage_g_placebo.json. Stage E's SE is re-derived here
through the same code path, not copied from earlier output."""

from __future__ import annotations

import json
import math
import warnings
from pathlib import Path

from displacement_observatory.analysis.clustered import build_exporter_product_year_rows, fit_ols_with_cluster_robust_se
from displacement_observatory.analysis.diD import run_all
from displacement_observatory.analysis.matching import select_matched_controls
from displacement_observatory.analysis.overlap import compute_windows
from displacement_observatory.analysis.packages import build_treatment_packages
from displacement_observatory.analysis.power import BASKET_SHARE_ASSUMPTIONS
from displacement_observatory.analysis.power_placebo import placebo_se, recompute_power
from displacement_observatory.config import CHEMICAL_HS2_CHAPTERS
from displacement_observatory.db import connect
from displacement_observatory.register.store import load_events

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parents[1] / "data" / "attack" / "stage_g_placebo.json"


def main() -> None:
    con = connect(read_only=True)
    register = load_events(version=1)
    packages = build_treatment_packages(register)
    did = {r.event.event_id: r for r in run_all(con, register, window_years=5)}
    windows = {w.package_id: w for w in compute_windows(packages, did)}
    restricted = {c.hs6 for e in register.events for c in e.hs6_candidates}
    ctl = sorted({r[0] for r in con.execute(
        f"SELECT DISTINCT hs6 FROM trade_flows WHERE substr(hs6,1,2) IN ({', '.join(repr(c) for c in CHEMICAL_HS2_CHAPTERS)})"
    ).fetchall()} - restricted)
    assumptions = {a.package_id: a for a in BASKET_SHARE_ASSUMPTIONS}

    out = {"method": "in-space placebo over the pre-registered matched pool; see analysis/power_placebo.py", "packages": {}}
    for p in packages:
        w = windows[p.package_id]
        if not w.tested:
            continue
        r = did[p.event_ids[0]]
        eff = p.effective_date.year
        pre = [eff + k for k in sorted(r.study.relative_years) if k < 0]
        matched = select_matched_controls(con, p.hs6, ctl, r.exporter_codes, pre).matched_hs6
        rows = build_exporter_product_year_rows(con, p.hs6, matched, r.exporter_codes, w.y0, w.y1)
        e = fit_ols_with_cluster_robust_se(rows, effective_year=eff)
        pl = placebo_se(con, p.hs6, matched, r.exporter_codes, w.y0, w.y1, eff)
        assert abs(pl.real_att - e.coef) < 1e-6, (p.package_id, pl.real_att, e.coef)  # same estimator as Stage E
        rc = recompute_power(p.package_id, e.se_clustered, pl, assumptions[p.package_id])
        a = assumptions[p.package_id]
        out["packages"][p.package_id] = {
            "substances": list(p.substances), "n_matched_controls": len(matched), "n_placebos": pl.n_placebos,
            "real_att": pl.real_att,
            "stage_e_classical_se": e.se_classical, "stage_e_clustered_se": e.se_clustered,
            "placebo_se": pl.se, "placebo_se_over_stage_e_se": pl.se / e.se_clustered,
            "stage_e_mde": rc.stage_e_mde, "placebo_mde": rc.placebo_mde,
            "placebo_se_is_wider": rc.placebo_se_is_wider,
            "assumed_share_range": [a.share_low, a.share_high],
            "max_plausible_implied_effect": rc.placebo_verdict.implied_effect_high,
            "share_needed_stage_e": 1 - math.exp(-rc.stage_e_mde),
            "share_needed_placebo": 1 - math.exp(-rc.placebo_mde),
            "verdict_stage_e": rc.stage_e_verdict.verdict.split(":")[0],
            "verdict_placebo": rc.placebo_verdict.verdict.split(":")[0],
        }
    OUT.write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
    print(json.dumps(out, indent=2, default=float))


if __name__ == "__main__":
    main()
