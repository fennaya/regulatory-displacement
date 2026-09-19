"""Generate review/hs6-mapping-review.md from the frozen v1 mappings.
The decision column is written EMPTY. This script never fills it; the owner does.
Re-running it would blank the owner's decisions, so it refuses if any is filled."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "review" / "hs6-mapping-review.md"
SRC = ROOT / "data" / "register" / "mappings" / "chemical_hs6_mappings_v1.yaml"

# Strongest argument AGAINST each mapping. Written from the model's general knowledge of customs
# classification, NOT checked against the HS explanatory notes or any tariff schedule.
AGAINST = {
    "Imidacloprid": "A large part of neonicotinoid use is as seed treatment, and treated seed is classified as seed (chapter 12), not under 3808. Technical-grade active ingredient is a chemical-chapter product (chapter 29, heterocyclic compounds), not 3808. So 380810 may miss much of the real trade and include unrelated formulations.",
    "Clothianidin": "Same as imidacloprid (treated seed and technical grade outside 3808), and additionally clothianidin is a metabolite/relative of thiamethoxam, so the two may be sold in overlapping products. 380810 also holds thousands of other insecticides.",
    "Thiamethoxam": "Same as imidacloprid. It is used heavily in seed treatments that do not appear in 3808; the 3808 line captures only a minority of its trade, and an unknown one.",
    "Chlorpyrifos": "Chlorpyrifos is also a non-agricultural insecticide (household, termite control) and technical grade is a chapter 29 organophosphorus product. Its HS6 home for formulated product is 380810 but the substance is a small and shrinking share of that basket.",
    "Chlorpyrifos-methyl": "A much smaller product than chlorpyrifos, used mainly as a grain-storage protectant. Its trade could sit outside 380810 (technical grade in chapter 29) and is likely negligible against the basket; the mapping may be right and still be uninformative.",
    "Endosulfan": "Endosulfan was banned globally under the Stockholm Convention (listed 2011), so most of its post-2011 trade is illegal or unrecorded; formulated product may be declared under generic or other codes. Technical grade is a chapter 29 product. The HS6 code may not contain the substance's trade at all.",
    "Paraquat": "Paraquat is sold as a liquid concentrate, and 380830 (herbicides, anti-sprouting, growth regulators) is dominated by glyphosate and other herbicides. Technical paraquat salt is a chapter 29 product. A restriction on one herbicide among hundreds should barely move the code.",
    "Atrazine": "Atrazine's global trade is small relative to 380830 (glyphosate dominates), and technical grade is a chapter 29 triazine. It is also used in mixtures whose declared classification can vary by customs authority.",
}
REASON_HEAD = 220


def main() -> None:
    if OUT.exists():
        from displacement_observatory.register.mapping_review import load_review
        if any(v for v in load_review(OUT).values()):
            sys.exit("review already has owner decisions; refusing to overwrite")
    maps = yaml.safe_load(SRC.read_text(encoding="utf-8"))["mappings"]
    lines = [
        "# HS6 mapping review, for the project owner",
        "",
        "**STATUS: WAITING ON THE OWNER. Nothing in this file has been confirmed.**",
        "",
        "Each row is one substance-to-HS6 mapping from `data/register/mappings/chemical_hs6_mappings_v1.yaml` (frozen). "
        "Those mappings were proposed by Claude and self-confirmed by Claude on 2026-09-18, which is not independent review. "
        "Write CONFIRMED, REJECTED or UNSURE in the last column of each row. Claude has not filled and will not fill that column.",
        "",
        "Limits: the proposed reasoning and the arguments against are from the model's general knowledge of customs classification. "
        "They were NOT checked against the WCO explanatory notes or any tariff schedule. The confidence values are the model's own "
        "figures, not calibrated probabilities. The dominant issue for every row is that HS6 380810/380830 are baskets of thousands of "
        "products, so even a correct mapping does not make the substance observable (see `decisions/0010-*.md`).",
        "",
        "| # | Substance | Proposed HS6 | Reasoning (proposed) | Confidence (model's own) | Strongest argument AGAINST | Decision |",
        "|---|---|---|---|---|---|---|",
    ]
    for i, m in enumerate(maps, 1):
        reason = " ".join(m["reasoning"].split())
        against = AGAINST[m["substance"]]
        lines.append(f"| {i} | {m['substance']} | {m['hs6']} | {reason} | {m['confidence']} | {against} |  |")
    lines += ["", "When every row is filled, the test `tests/test_mapping_provenance.py::test_no_mapping_rests_only_on_model_self_confirmation` "
              "will start passing and the strict xfail will turn into a failure telling you to remove the marker.", ""]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {OUT} with {len(maps)} rows, all decisions empty")


if __name__ == "__main__":
    main()
