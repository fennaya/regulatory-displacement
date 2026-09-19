"""PART 1: hostile tests of the staggered basket-level estimate.
Writes data/attack/basket_attack_results.json; every number quoted in
decisions/0009-*.md comes from that file."""

from __future__ import annotations

import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from displacement_observatory.analysis.basket_attack import (
    build_hs6_year_bloc_panel, placebo_distribution, placebo_two_sided_p, to_outcome_frame, twfe_att_balanced,
)
from displacement_observatory.analysis.staggered import first_restriction_year, fit_staggered
from displacement_observatory.config import CHEMICAL_HS2_CHAPTERS
from displacement_observatory.db import connect
from displacement_observatory.register.store import load_events

warnings.filterwarnings("ignore")
OUT = Path(__file__).resolve().parents[1] / "data" / "attack" / "basket_attack_results.json"
Y0, Y1 = 1995, 2024
N_DRAWS = 2000


def main() -> None:
    con = connect(read_only=True)
    register = load_events(version=1)
    gmap = first_restriction_year(register.events)
    all_hs6 = sorted(r[0] for r in con.execute(
        f"SELECT DISTINCT hs6 FROM trade_flows WHERE substr(hs6,1,2) IN ({', '.join(repr(c) for c in CHEMICAL_HS2_CHAPTERS)})"
    ).fetchall())
    treated = sorted(gmap)
    never = [h for h in all_hs6 if h not in gmap]
    never38 = [h for h in never if h.startswith("38")]
    res: dict = {"gname": gmap, "n_never_treated": len(never), "n_never_treated_ch38": len(never38)}

    val = build_hs6_year_bloc_panel(con, all_hs6, gmap, Y0, Y1)
    qty = build_hs6_year_bloc_panel(con, all_hs6, gmap, Y0, Y1, measure="quantity_tons")

    def did2s(df):
        r = fit_staggered(df, estimator="did2s")
        return {"coef": r.coef, "se": r.se, "ci": [r.ci_low, r.ci_high]}

    def pct(x):
        return float(np.expm1(x))

    # 1. TRIPLE DIFFERENCE CHECK ---------------------------------------
    eu, row, tri = (to_outcome_frame(val, m) for m in ("eu", "row", "triple"))
    res["1_triple"] = {
        "eu_only_did2s (the original spec)": did2s(eu),
        "eu_only_twfe_balanced": twfe_att_balanced(eu),
        "row_only_did2s (rest-of-world exports of the SAME codes, same destinations)": did2s(row),
        "row_only_twfe_balanced": twfe_att_balanced(row),
        "triple_did2s (EU minus RoW)": did2s(tri),
        "triple_twfe_balanced": twfe_att_balanced(tri),
    }
    res["1_triple"]["share_of_eu_only_effect_removed_by_triple"] = 1 - res["1_triple"]["triple_twfe_balanced"] / res["1_triple"]["eu_only_twfe_balanced"]

    # 2. WHO DRIVES IT ---------------------------------------------------
    loo = {}
    for drop in treated:
        keep = [h for h in all_hs6 if h != drop]
        for name, frame in (("eu", eu), ("triple", tri)):
            f = frame[frame["hs6"].isin(keep)]
            loo[f"drop_{drop}_{name}"] = {"did2s": did2s(f), "twfe_balanced": twfe_att_balanced(f)}
    res["2_leave_one_code_out"] = loo
    # sub-period: end each cohort's panel before the next same-code event
    sub = {}
    for code, cutoff in (("380810", 2017), ("380830", 2006)):
        keep = [h for h in all_hs6 if h == code or h not in gmap]
        for name, frame in (("eu", eu), ("triple", tri)):
            f = frame[frame["hs6"].isin(keep) & (frame["year"] <= cutoff)]
            sub[f"{code}_alone_through_{cutoff}_{name}"] = twfe_att_balanced(f)
    res["2_sub_period_before_next_same_code_event"] = sub

    # dynamic (event-time) profile, each treated code vs never-treated ----
    from displacement_observatory.analysis.twfe import run_event_study
    dyn = {}
    for code in treated:
        for name, frame in (("eu", eu), ("triple", tri)):
            f = frame[(frame["hs6"] == code) | (frame["hs6"].isin(never))]
            rows = [(r.hs6, int(r.year), float(r.value)) for r in f.itertuples()]
            st = run_event_study(rows, treated_unit=code, effective_year=gmap[code], window_years=40)
            ks = sorted(st.relative_years)
            pre = [k for k in ks if k < -1]
            post = [k for k in ks if k >= 0]
            dyn[f"{code}_{name}"] = {
                "coef_by_k": {str(k): st.coef[k] for k in ks},
                "mean_pre_k_lt_minus1": float(np.mean([st.coef[k] for k in pre])),
                "pre_slope_per_year": float(np.polyfit(pre, [st.coef[k] for k in pre], 1)[0]),
                "mean_post_k0_to_4": float(np.mean([st.coef[k] for k in post if k <= 4])),
                "mean_post_k10_plus": float(np.mean([st.coef[k] for k in post if k >= 10])) if any(k >= 10 for k in post) else None,
                "n_pre_years": len(pre) + 1, "n_post_years": len(post),
            }
    res["2_dynamic_event_time"] = dyn

    # placebo / randomization inference -----------------------------------
    cohorts = [gmap[c] for c in treated]
    placebo = {}
    for name, frame in (("eu", eu), ("triple", tri)):
        real = twfe_att_balanced(frame)
        for pool_name, pool in (("all_never_treated", never), ("chapter38_never_treated", never38)):
            d = placebo_distribution(frame, pool, cohorts, N_DRAWS, seed=7)
            placebo[f"{name}__{pool_name}"] = {
                "real": real, "placebo_mean": float(d.mean()), "placebo_sd": float(d.std()),
                "placebo_p05_p95": [float(np.percentile(d, 5)), float(np.percentile(d, 95))],
                "two_sided_p": placebo_two_sided_p(real, d), "n_draws": N_DRAWS,
            }
    res["placebo"] = placebo

    # 3. COMPOSITION: what BACI can and cannot say -------------------------
    q_eu, q_tri = to_outcome_frame(qty, "eu"), to_outcome_frame(qty, "triple")
    unit = val[["hs6", "year", "gname"]].copy()
    with np.errstate(divide="ignore", invalid="ignore"):
        unit["value"] = np.log1p(val["eu"]) - np.log1p(qty["eu"])   # log unit-value proxy (log1p convention)
    miss = con.execute(
        f"SELECT hs6, count(*), sum(CASE WHEN quantity_tons IS NULL THEN 1 ELSE 0 END) FROM trade_flows "
        f"WHERE hs6 IN ({', '.join(repr(h) for h in treated)}) GROUP BY hs6"
    ).fetchall()
    res["3_composition"] = {
        "log_quantity_eu_only_did2s": did2s(q_eu),
        "log_quantity_triple_twfe_balanced": twfe_att_balanced(q_tri),
        "log_unit_value_eu_only_twfe_balanced": twfe_att_balanced(unit),
        "missing_quantity_share_treated_codes": {r[0]: r[2] / r[1] for r in miss},
    }

    # 5. MAGNITUDE ---------------------------------------------------------
    main_c = res["1_triple"]["eu_only_did2s (the original spec)"]
    res["5_magnitude"] = {
        "coef": main_c["coef"], "pct_increase": pct(main_c["coef"]),
        "pct_ci": [pct(main_c["ci"][0]), pct(main_c["ci"][1])],
        "implied_min_basket_share_for_full_displacement": 1 - np.exp(-main_c["coef"]),
        "implied_share_at_ci_low": 1 - np.exp(-main_c["ci"][0]),
        "implied_share_at_ci_high": 1 - np.exp(-main_c["ci"][1]),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2, default=float), encoding="utf-8")
    print(json.dumps(res, indent=2, default=float))


if __name__ == "__main__":
    main()
