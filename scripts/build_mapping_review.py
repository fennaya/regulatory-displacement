"""Generate review/hs6-mapping-review.md from the frozen v1 mappings plus external evidence.

The owner-decision column is written EMPTY. This script never fills it; the owner does.
Re-running would blank the owner's decisions, so it refuses if any is filled.

Every fact in EVIDENCE was retrieved from the cited external source on 2026-09-20 (see the
per-row URLs). The "strongest argument against" column mixes retrieved facts with model reasoning; reasoning that was not checked is labelled unverified in the cell. Where a source could not be reached
the cell says so and the verdict is UNCLEAR.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "review" / "hs6-mapping-review.md"
SRC = ROOT / "data" / "register" / "mappings" / "chemical_hs6_mappings_v1.yaml"
HS3808 = ROOT / "review" / "evidence" / "hs3808_by_revision.json"

EUR = "https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:"
R540 = f"{EUR}32011R0540"
COMTRADE = "https://comtrade.un.org/data/cache/classificationH0.json"
EPA = "https://www.epa.gov/ingredients-used-pesticide-products/"
PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
ROT = "https://www.pic.int/Portals/5/COPS/COP4/i9)/English/K0763331%20COP-4-9.pdf"

# cas, function, code (HS92, the panel's revision), verdict, why
EVIDENCE = {
    "Imidacloprid": (
        f"138261-41-3 ([EU Reg 540/2011 Annex Part A]({R540}))",
        f"insecticide ([EU Reg 2018/783, Annex: \"Only uses as insecticide ...\"]({EUR}32018R0783))",
        f"380810 Insecticides ([UN Comtrade HS1992 file]({COMTRADE}))", "MATCH",
        "A large part of neonicotinoid use is seed treatment; the EU regulation itself covers \"the treatment of seeds\". Treated seed is classified with seeds, not under 3808 (this classification point is NOT verified from a tariff source here). Technical-grade active ingredient is probably a chapter 29 product (also unverified). So 380810 may miss much of the real trade and contain thousands of unrelated insecticides."),
    "Clothianidin": (
        f"210880-92-5 ([EU Reg 540/2011]({R540}))",
        f"insecticide ([EU Reg 2018/784]({EUR}32018R0784))",
        f"380810 ([UN Comtrade HS1992]({COMTRADE}))", "MATCH",
        "Same as imidacloprid, and it shares 380810 and an effective date with two other neonicotinoids, so it cannot be separated from them."),
    "Thiamethoxam": (
        f"153719-23-4 ([EU Reg 540/2011]({R540}))",
        f"insecticide ([EU Reg 2018/785]({EUR}32018R0785))",
        f"380810 ([UN Comtrade HS1992]({COMTRADE}))", "MATCH",
        "Same as imidacloprid and clothianidin; the three neonicotinoids are one treatment package, not three."),
    "Chlorpyrifos": (
        f"2921-88-2 ([EU Reg 540/2011]({R540}))",
        f"insecticide (also acaricide, miticide) ([US EPA]({EPA}chlorpyrifos); the EU texts fetched do not state a function, so this is a US regulator's statement, not the EU database)",
        f"380810 ([UN Comtrade HS1992]({COMTRADE}))", "MATCH",
        "Function evidence is from a US regulator only. Chlorpyrifos is also a non-agricultural insecticide and technical grade is probably a chapter 29 product (unverified). It is a shrinking share of a very large basket."),
    "Chlorpyrifos-methyl": (
        f"5598-13-0 ([EU Reg 540/2011]({R540}))",
        "NOT ESTABLISHED: the EU texts fetched (Reg 2020/17 and 540/2011) do not state a function and no other authoritative source was reached in this session",
        f"would be 380810 if it is an insecticide ([UN Comtrade HS1992]({COMTRADE}))", "UNCLEAR",
        "The mapping rests on the model's belief that it is an insecticide, which this pass could not confirm from an external source. Even if right, it is a much smaller product than chlorpyrifos and co-timed with it (same effective date)."),
    "Endosulfan": (
        f"115-29-7, category Pesticide ([Rotterdam Convention COP-4/9]({ROT}))",
        f"insecticide ([Rotterdam Convention COP-4/9, notification summary: \"Insecticide used against a variety of insects ...\"]({ROT}))",
        f"380810 by function ([UN Comtrade HS1992]({COMTRADE})). BUT see the endosulfan flag below", "UNCLEAR",
        "In the HS2017 nomenclature, Chapter 38 Subheading Note 1 lists endosulfan, so goods containing it are classified in 3808.52/3808.59 by substance, not by function ([WCO HS2017 Chapter 38 notes](https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2017/2017/0638_2017e.pdf?la=en)). Whether Note 1 already named endosulfan in HS2007/HS2012 was NOT checked, and how BACI converts 3808.50-series flows back to HS92 is not documented on its pages. So the share of endosulfan trade that lands in 380810 in this panel is unknown."),
    "Paraquat": (
        f"1910-42-5 for paraquat dichloride ([PubChem, NLM]({PUBCHEM}paraquat%20dichloride/synonyms/JSON); the cation is 4685-14-7). Not from the EU database or ECHA, which could not be reached",
        f"herbicide (\"a non-selective herbicide\", [EU General Court, T-229/04]({EUR}62004TJ0229))",
        f"380830 Herbicides ... ([UN Comtrade HS1992]({COMTRADE}))", "MATCH",
        "380830 is dominated by other herbicides, so a restriction on one of them barely moves the code. Technical paraquat salt is probably a chapter 29 product (unverified)."),
    "Atrazine": (
        f"1912-24-9 ([PubChem, NLM]({PUBCHEM}atrazine/synonyms/JSON); not from the EU database or ECHA, which could not be reached)",
        f"herbicide (\"a chlorinated triazine systemic herbicide\", [US EPA]({EPA}atrazine); the EU non-inclusion decision 2004/248 fetched does not state a function)",
        f"380830 ([UN Comtrade HS1992]({COMTRADE}))", "MATCH",
        "Function evidence is a US regulator, not an EU source. Atrazine's trade is small against 380830 and technical grade is probably a chapter 29 triazine (unverified)."),
}


def _revision_table() -> str:
    d = json.loads(HS3808.read_text(encoding="utf-8"))
    lines = ["| Revision | 3808 subheadings (from the UN Comtrade classification file for that revision) |", "|---|---|"]
    for rev, rows in d.items():
        codes = "; ".join(f"{k} {v[:70]}" for k, v in rows.items() if k != "3808")
        lines.append(f"| {rev} | {codes} |")
    return "\n".join(lines)


def main() -> None:
    if OUT.exists():
        from displacement_observatory.register.mapping_review import load_review
        if any(v for v in load_review(OUT).values()):
            sys.exit("review already has owner decisions; refusing to overwrite")
    maps = yaml.safe_load(SRC.read_text(encoding="utf-8"))["mappings"]
    assert {m["substance"] for m in maps} == set(EVIDENCE)
    L = [
        "# HS6 mapping review, for the project owner",
        "",
        "**STATUS: WAITING ON THE OWNER. Nothing in this file has been confirmed. The last column is empty on purpose.**",
        "",
        "The eight mappings in `data/register/mappings/chemical_hs6_mappings_v1.yaml` (frozen) were proposed by Claude and self-confirmed by Claude on 2026-09-18, which is not independent review. "
        "This file attaches external evidence to each row so that your sign-off is a judgement on evidence. The MATCH / MISMATCH / UNCLEAR column reports whether the external evidence agrees with the proposed code; it is not a confirmation. "
        "Retrieved 2026-09-20. Where a source could not be reached, the cell says so. The \"strongest argument against\" column is the model's reasoning built on those facts; any point not checked against a source is labelled unverified in the cell.",
        "",
        "## A. Which HS version is the panel in (checked from CEPII's own documentation)",
        "",
        "The panel is the **HS92** file of BACI version 202601 (`data/raw/BACI_HS92_V202601.zip`, files `BACI_HS92_Y1995..Y2024_V202601.csv`, product list `product_codes_HS92_V202601.csv`). "
        "CEPII's description page (https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/DescriptionBACI.html) says BACI is provided in each HS revision, HS92 covering 1995 onward, and that trade reported in a newer revision is converted to older ones (\"Conversions from newer to older revisions are possible, but not the reverse\"), a conversion that \"reduces the number of products\" and \"leads to some inaccuracies\". "
        "Its release page (https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/baci_webpage.html) gives this as the 202601 version, last updated 22 January 2026. "
        "So every year 1995-2024, including 2018 and 2020, is in **HS1992 codes**. The conversion procedure itself is not described on either page, so how flows reported in later-revision codes are allocated back to HS92 subheadings is UNKNOWN here.",
        "",
        "## B. What heading 3808 looked like in each revision (from UN Comtrade's classification files, not from memory)",
        "",
        _revision_table(),
        "",
        "Source: `https://comtrade.un.org/data/cache/classificationH0.json` (HS1992), `H3` (HS2007), `H4` (HS2012), `H5` (HS2017), `H6` (HS2022); extract stored at `review/evidence/hs3808_by_revision.json`.",
        "",
        "**Correction to the premise that the restructuring happened in HS2012.** These files show it happened in **HS2007**: the five HS1992 subheadings (380810-380890) were replaced by 3808.50 (goods containing substances named in Subheading Note 1) and 3808.91-3808.99 (the other goods, by function). HS2012 keeps that structure with reworded titles. HS2017 then split further (3808.52, .59, .61, .62, .69, .91-.99). "
        "The functional subheadings correspond as: insecticides 380810 (HS92) = 380891 (HS2007 and later); fungicides 380820 = 380892; herbicides etc. 380830 = 380893.",
        "",
        "### Anachronism check",
        "",
        "- **No mapping uses a post-HS92 code, and none mixes revisions.** All eight use 380810 or 380830, which are HS92 codes, applied to a panel that is entirely HS92. No event is dated after a revision in a way that puts a later-revision code on it. No anachronism by code.",
        "- **A real problem of a different kind: substance-named subheadings.** In HS2007 and later, goods containing substances named in Subheading Note 1 leave the functional subheadings for 3808.50 (HS2007/2012) or 3808.52/3808.59 (HS2017). The WCO HS2017 Chapter 38 notes (https://www.wcoomd.org/-/media/wco/public/global/pdf/topics/nomenclature/instruments-and-tools/hs-nomenclature-2017/2017/0638_2017e.pdf, retrieved 2026-09-20) name **endosulfan** in that Note 1. The other seven substances are **not** named in Note 1 or in Note 2 (checked by reading the note text). So for endosulfan a finer, substance-based code exists in later revisions, its HS92-equivalent allocation in BACI is undocumented, and the mapping to 380810 may not capture all endosulfan-containing goods after 2007. Whether Note 1 named endosulfan in HS2007/HS2012 was not checked (only the 2017 text was read), and Note 1 is therefore the only place where the analysis can be affected by the revision structure. This is reported, not analysed.",
        "- For the other seven substances, no substance-specific customs code exists in any revision (per the notes above), which is the HS6 dilution problem already reported in `PAPER.md`.",
        "",
        "## C. The eight mappings",
        "",
        "Verdicts: **MATCH** = external evidence gives the function and the HS92 subheading for that function agrees with the proposed code. **MISMATCH** = it does not. **UNCLEAR** = evidence missing or contradictory. **No MISMATCH was found.** Two rows are UNCLEAR and the reasons are in their cells. CAS numbers for paraquat and atrazine come from PubChem (US National Library of Medicine), a government database, because the EU pesticides database and ECHA pages could not be read by the tools available (JavaScript applications); this is weaker than an EU source and is flagged in the cells.",
        "",
        "| # | Substance | CAS (source) | Function (source) | Proposed HS6 | HS92 code for that function (source) | Match? | Strongest argument against | Owner decision |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for i, m in enumerate(maps, 1):
        cas, fn, code, verdict, against = EVIDENCE[m["substance"]]
        L.append(f"| {i} | {m['substance']} | {cas} | {fn} | {m['hs6']} | {code} | {verdict} | {against} |  |")
    L += ["", "The confidence values in the frozen v1 file (0.5-0.55) are the model's own figures, not calibrated probabilities, and are not repeated here.",
          "The test `tests/test_mapping_provenance.py::test_no_mapping_rests_only_on_model_self_confirmation` is a strict expected failure until every row has your decision; it will then start passing and ask you to remove the marker.", ""]
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {OUT} with {len(maps)} rows, all decisions empty")


if __name__ == "__main__":
    main()
