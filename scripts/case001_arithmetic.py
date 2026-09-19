"""Case 001 step-4 arithmetic. Inputs: BACI tonnes (data/attack/
case001_basket_tonnes.json, from the panel), notified tonnage (Unearthed,
stored in testability/sources), placebo SDs (data/attack/
basket_attack_results.json). Output: testability/cases/case-001-arithmetic.json.
Deterministic; nothing here is typed by hand except the two published
notified-tonnage figures."""

from __future__ import annotations

import json
from pathlib import Path

from displacement_observatory.analysis.power import compute_mde
from testability.protocol import elimination_effect, notified_share, share_needed_for_detection

ROOT = Path(__file__).resolve().parents[1]
NOTIFIED_T = {2018: 81_600.0, 2024: 122_000.0}  # Unearthed 22.09.2025; tonnes of mixtures, notified


def main() -> None:
    bt = json.loads((ROOT / "data/attack/case001_basket_tonnes.json").read_text())
    at = json.loads((ROOT / "data/attack/basket_attack_results.json").read_text())
    sd = {k: at["placebo"][f"triple__{k}"]["placebo_sd"] for k in ("chapter38_never_treated", "all_never_treated")}
    out: dict = {"notified_tonnes": NOTIFIED_T, "placebo_sd_triple_difference": sd, "years": {}}
    for y in (2018, 2024):
        eu = bt[f"quantity_tons_{y}"]["eu_to_nonEU_all3808"]
        row = bt[f"quantity_tons_{y}"]["row_all3808"]
        s = notified_share(NOTIFIED_T[y], eu)
        out["years"][str(y)] = {
            "customs_tonnes_eu_to_non_eu_heading_3808": eu,
            "customs_tonnes_row_to_non_eu_heading_3808": row,
            "row_over_eu_tonnage_ratio": row / eu,
            "notified_share_of_eu_customs_tonnes": s,
            "log_point_change_if_all_notified_tonnage_vanished": elimination_effect(s),
        }
    out["detection"] = {
        name: {
            "se_proxy": v,
            "mde_80pct_power_log_points": compute_mde(v),
            "share_needed_for_detection": share_needed_for_detection(v),
        }
        for name, v in sd.items()
    }
    p = ROOT / "testability/cases/case-001-arithmetic.json"
    p.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
