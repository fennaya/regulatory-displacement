# Public HS6 trade data cannot answer substance-level displacement questions: a detection-threshold analysis of EU pesticide restrictions

*Full draft, 2026-09-20. One claim: public HS6 trade data cannot answer substance-level displacement questions, and here is the arithmetic. Every figure has a pointer to the repository file that produced it, and every statistic was computed by tested code, not by a language model. Every academic citation was checked against the published record (`reviews/citation-audit.md`; a test fails if a citation has no verified audit entry). Limitations come before results on purpose. A separate piece on the testability protocol and its worked case is in `PAPER-testability.md`.*

## Abstract

When the EU bans or restricts a pesticide for use inside the EU, does trade in that product relocate to destinations without the restriction? We build a register of nine cited restrictions (six independent treatment packages, five testable), a 30-year bilateral trade panel (CEPII BACI, HS chapters 28/29/38, 15.4 million rows), and a pre-specified difference-in-differences test. Every pre-specified test is null, and we do not read those nulls as evidence of no displacement. The reason is arithmetic. At HS6 resolution the restricted substance is one product among many in its basket. With standard errors derived from placebo estimates, the minimum detectable effect at 80% power is 0.72 to 1.93 log points, so the substance would have to be roughly 51-86% of its basket, and fully displaced, before a package-level test could see it. Under our stated (mostly unverified) share assumptions, none of the five packages is detectable with the placebo-derived standard errors, and at least four of the five are undetectable under either those or the earlier, narrower cluster-robust standard errors. Public HS6 trade data therefore cannot confirm or refute substance-level displacement. We also report the design traps we fell into on the way, including a panel limitation (the HS92 series is converted backward from later nomenclature revisions) that affects every long-window estimate.

## 1. Question and claim under test

The claim: when jurisdiction A restricts a product, flows of that product into jurisdictions without the restriction rise after the effective date, relative to never-restricted control products (`README.md`, `falsification.md#displacement-hypothesis`). Status: **untested**, not weakly supported. The scope is pesticides and hazardous chemicals only.

## 2. Limitations (stated before results)

1. **Resolution.** BACI reports HS6 totals; heading 3808 has five subheadings in the HS92 nomenclature used. The restricted substance's share of its own basket is not observed (`decisions/0009-*.md`; `falsification.md#hs6-too-coarse`).
2. **The panel is a backward conversion, and the basket may not be the same object across years.** The panel is the HS92 file of BACI 202601 for all years 1995-2024. CEPII's documentation (https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/DescriptionBACI.html, read 2026-09-20) says trade reported in newer nomenclature revisions is converted to older ones, that the conversion "reduces the number of products present in the data", and that using an old revision for data originally reported in a recent one "leads to some inaccuracies". Neither that page nor the BACI release page (https://www.cepii.fr/DATA_DOWNLOAD/baci/doc/baci_webpage.html) describes the conversion procedure or tables, so how it works is undocumented in what we read. Heading 3808 was restructured in HS2007, not later: the five HS1992 subheadings (380810-380890) became 3808.50, for goods containing substances named in Subheading Note 1, plus 3808.91-3808.99 by function (UN Comtrade classification files, `review/evidence/hs3808_by_revision.json`); HS2017 split it further. Goods in 3808.50 span several functions, so converting them back to HS92 requires allocating them across 380810/380820/380830/380840/380890, and we do not know how CEPII does that. Endosulfan is an instance: the WCO's HS2017 Chapter 38 notes name it in a substance-based subheading (3808.52/3808.59), and the other seven substances are not named there. Where endosulfan-containing goods land in 380810 after back-conversion is a CEPII choice we did not inspect. **Consequence: the composition of basket 380810 in 2018 is not guaranteed to be the same object as in 2004, and every long-window estimate assumes it is.** This threatens the panel, not only the register. No analysis here corrects for it.
3. **Contamination, reported as a band, not a count.** Whether a package is free of another same-code restriction inside its estimation window depends on the window. At the pre-set ±5-year window 0 of 5 packages are clean; at ±4, ±3 and ±2, 1 of 5 (EU endosulfan) is clean. The other four are contaminated at every window from ±2 to ±5. We did not choose a window: choosing after seeing which count is more favourable would be selecting on the outcome, and the difference is one package and one partial year (`METHODS.md`, "Why no single window was chosen"; `analysis/overlap.py`; `reviews/2026-09-19-readme-review.md`). The dates the audit consumes were checked against the register for every event (`tests/test_date_consistency.py`, `scripts/date_consistency.py`, 2026-09-20).
4. **Inference.** With one treated HS6 code per package no analytic standard error is reliable. Randomization inference over never-restricted codes gives a placebo SD of about 1.4 log points against a reported did2s SE of 0.145 (`data/attack/basket_attack_results.json`). Other standard errors here should be read as too small, which is why the detection thresholds in section 5 were recomputed.
5. **Basket-share assumptions** in the power arithmetic are mostly unverified; only imidacloprid's is anchored to a (vendor-inconsistent) market figure (`analysis/power.py`). Every "not detectable" verdict below is conditional on them.
6. **Zero cells.** BACI records only positive flows, so 59-61% of importer-product-year cells are zero-or-unreported and the data cannot say which.
7. **Register mappings await owner sign-off.** The substance-to-HS6 mappings were proposed and self-confirmed by the model that built the pipeline. External evidence has since been attached to each (`review/hs6-mapping-review.md`, 2026-09-20): 6 of 8 agree with the function-to-subheading mapping, 2 are unclear (chlorpyrifos-methyl, whose function could not be confirmed from a source, and endosulfan, see limitation 2), none contradict it. The project owner has not yet signed off, and `tests/test_mapping_provenance.py` is an expected failure until they do. Two of nine events (2018 clothianidin, thiamethoxam) were sourced from secondary reporting. Atrazine and endosulfan are Directive 91/414/EEC non-inclusion decisions labelled non-renewal. One register citation was wrong and is corrected: the Rotterdam endosulfan event cited a Secretariat draft proposal from COP-4 (2008) that was not adopted; the dates in the register (24 June and 24 October 2011) were right and rest on the Secretariat's text of decisions RC-5/3, RC-5/4 and RC-5/5.
8. **Validation coverage.** Only the "EU banned-pesticide exports" episode type can be tested with a chemicals panel.
9. **Analysis history.** The original specification came from the brief; the repairs that followed (PPML, staggered estimator, triple difference, matched controls, clustering) were chosen after the first estimates were uninformative and were **not pre-registered**. Only the matching thresholds and the destination groups were committed before estimation (`decisions/0007-*.md`, `0008-*.md`). 48 specifications were estimated, 7 with a CI excluding zero, in both signs; 2.4 would be expected by chance if all were independent nulls (`data/attack/spec_ledger.json`).
10. **The test we ran is not the test the Commission's wording implies, so this null must not be cited for or against the Commission.** The European Commission's stated rationale for not proposing an export ban says a unilateral ban "may push these countries to buy the same or worse chemical pesticides from companies outside of the EU." That is a claim about **supplier substitution by importing countries**. Testing it needs importer-side purchases by substance and supplier origin, before and after an export ban. This study never ran that test. It examined whether EU *use* restrictions were followed by trade relocating to unrestricted destinations, in a setting where no EU-wide export ban was in force. The quote is reproduced by two secondary sources, not the primary (`PAPER-testability.md`).
11. **No systematic literature search was run for this paper.** The citations in section 8 were each verified to exist and to say what we cite them for (`reviews/citation-audit.md`), but they are a short list, not a review, and `/priorwork` was not run. No novelty claim is made beyond what section 8 states.

## 3. Data and register

- Panel: CEPII BACI HS92 v202601, 1995-2024, HS 28/29/38: 15,448,188 rows, 234 countries, 544 HS6 codes, 3.0% missing quantity (`scripts/build_panel.py`). See limitation 2 for what "HS92" means for years after 2007.
- Register: nine cited events, eight substances, collapsed to six treatment packages by (jurisdiction, HS6, decision date, effective date); five testable, one (the Rotterdam endosulfan listing) untestable. Unit-of-treatment argument: `decisions/0001-*.md`. Event counts are treatment packages, never substances.

## 4. Pre-specified design and results

**4.1 Original specification** (two-way fixed effects event study, ~542 controls): all five package estimates positive, every 95% CI roughly ±2 log points, none significant (`analysis/comparison.py`).

**4.2 Pre-registered choices, both null.** Matched control pools cut SEs 42-61%; no package significant (`decisions/0007-*.md`, `0005-*.md`). Destination groups fixed before estimation: the high-exposure versus low-exposure difference is neither supported nor refuted; group CIs are about ±2-3 log points (`data/destination_groups_v1.yaml`; `decisions/0008-*.md`, with its 2026-09-19 amendment).

**4.3 Repairs, labelled post hoc.** PPML keeping zero cells: none significant (`analysis/ppml.py`). Triple difference against rest-of-world exporters of the same product: point estimates shrink 60-93%, and the originals were not significant to begin with (`analysis/triple_diff.py`; `decisions/0004-*.md` amendment). Truncated windows: unstable (atrazine +0.407 to -0.017, both spanning zero).

**4.4 One check that failed.** After the package-level tests were null, a pooled staggered-robust basket estimate was tried and initially looked positive. It failed as an EU-restriction effect: rest-of-world exports of the same codes rose more, the EU-specific triple difference is negative, placebo p-values are 0.28-0.81, and there is no discontinuity at the effective dates (`decisions/0009-*.md`). It is reported here as a failed check only, and it is not part of the paper's findings.

**4.5 Rediscovery.** Three documented cases (Unearthed and Public Eye, investigation published 10 September 2020, https://unearthed.greenpeace.org/2020/09/10/banned-pesticides-eu-export-poor-countries/): directional recall 100%, significant recall 0%. Uninformative on direction, since every original estimate was positive.

**How to read these nulls.** They are null under a design that, by section 5, could not have seen an effect of plausible size. They are not evidence of absence.

## 5. The arithmetic: detection thresholds

The minimum detectable effect (MDE) at 80% power and 5% significance is (1.96 + 0.84) times the standard error. Stage G first used the cluster-robust SEs of Stage E. Those are too narrow: exporter-product clusters within one treated code share its common shock. We recomputed from placebo-derived SEs: each of the 20-29 members of a package's pre-registered matched pool in turn plays the restricted code, and the SD of those placebo estimates is the SE (`analysis/power_placebo.py`, `scripts/stage_g_placebo.py`, `data/attack/stage_g_placebo.json`, `decisions/0010-*.md`; the same code path reproduces Stage E's coefficient to 1e-6).

| Package | Stage E SE | Placebo SE | MDE (Stage E → placebo) | Share of basket needed, fully displaced (Stage E → placebo) |
|---|---|---|---|---|
| Endosulfan | 0.213 | 0.539 | 0.60 → 1.51 | 45% → 78% |
| Neonicotinoids | 0.112 | 0.255 | 0.31 → 0.72 | 27% → 51% |
| Chlorpyrifos | 0.130 | 0.475 | 0.36 → 1.33 | 30% → 74% |
| Atrazine | 0.155 | 0.479 | 0.43 → 1.34 | 35% → 74% |
| Paraquat | 0.202 | 0.690 | 0.57 → 1.93 | 43% → 86% |

The placebo SE is wider than Stage E's for every package (2.3 to 3.7 times), which is the direction we predicted before computing: too-narrow SEs mean wider true intervals, a larger true MDE, and therefore more undetectable packages, not fewer. Under our share assumptions (10-30% for neonicotinoids, 3-20% for the rest), full displacement would move a basket by at most 0.16-0.36 log points. **Before the correction 4 of 5 packages were undetectable (neonicotinoids borderline); after it, 5 of 5 are; at least 4 of 5 under either SE.**

**Our original detection thresholds were too generous to the instrument: they implied more detection power than existed. Correcting the standard errors raises the thresholds and strengthens the conclusion.**

*What is established and what is not.* Established by recomputation: the direction and size of the SE correction, and the MDEs. Not established: the basket-share assumptions, which stay flagged as unverified. The placebo SE is a proxy: it assumes the treated code's noise resembles the pool's, and if the treated code is smoother it overstates its own noise, so the truth lies between the two SEs (both are reported). It rests on 20-29 placebos, about 13-16% sampling error, well inside the 2.3-3.7 times gap. The share the substance would need (51-86% of an HS6 basket) is a threshold that holds whatever the assumed shares are, and we judge, without verification, that no single active ingredient plausibly holds that share. All of this also inherits limitation 2: the "basket" is the HS92-converted 380810 or 380830.

**Put in words: the restricted substance would have to make up more than half of its HS6 basket, and all of it would have to be displaced, before this instrument could reliably see it. Therefore any claim that EU restrictions did, or did not, cause trade displacement at the level of a single restricted substance is currently unfalsifiable with public HS6 trade data.**

## 6. A catalogue of design traps

These are not a separate contribution. They are what the arithmetic above is built on, listed so that the next study of this kind does not repeat them.

1. **Events are not treatment units.** Nine events and eight substances collapse to six packages, of which five are testable, because companion measures share an HS6 code and dates (`decisions/0001-*.md`).
2. **Contamination depends on the window.** The clean count is 0 or 1 of 5 depending on a choice of years (limitation 3).
3. **One treated code means no analytic standard error is trustworthy.** Placebo SD about 1.4 against a reported 0.145 at the basket level; 2.3-3.7 times at the package level (`decisions/0009-*.md`, `0010-*.md`).
4. **A significant pooled result can be a product-type trend.** The basket estimate was positive because rest-of-world exporters' shipments of the same codes rose more (`decisions/0009-*.md`).
5. **The nomenclature is not fixed.** A long HS92 series converted backward from later revisions may not describe one basket throughout (limitation 2).
6. **Builder-confirmed mappings, and a citation that did not support its claim.** The mappings were self-confirmed, and one register citation pointed to a rejected draft; the dates were right but the link was wrong, and only a check against primary documents found it. A test now asserts that register dates equal the dates the analysis consumes (`tests/test_date_consistency.py`).
7. **Forking paths.** 48 specifications, 7 with a CI excluding zero in both directions, against 2.4 expected by chance (limitation 9).
8. **The test run may not be the claim's test.** Limitation 10.

## 7. What can and cannot be claimed

- **Cannot be supported or refuted with public HS6 data:** "a ban would only shift trade or production abroad"; "restrictions did not change trade in the restricted substance."
- **Can be said:** at the HS6 basket level nothing distinguishes EU exports from rest-of-world exports after the restrictions; an apparent effect in a pooled basket regression was a product-type trend shared by all exporters.
- **What would make the question testable:** substance-level data: export notifications under the EU PIC Regulation with shipped quantities, importer-side purchases by supplier origin, or 8-digit customs lines. The Eurostat Comext CN8 split of heading 3808 is an **unverified lead**, not checked.

A companion piece, `PAPER-testability.md`, applies the same arithmetic to one institutional claim (the European Commission's stated reason for not proposing an export ban) using a general audit protocol (`testability/METHOD.md`). It is a separate, unfinished piece. This paper depends on none of it, except that limitation 10 records what this paper's null cannot be cited for.

## 8. Contribution, and what is not new

**What we contribute.** The arithmetic: at HS6 resolution, package-level tests could not see substance-level displacement at plausible effect sizes, with the standard errors recomputed from placebos. It comes with a reproducible instrument (a register, a panel and estimators, all in tested code, with decisions and falsification criteria committed in the repository) and the catalogue of traps in section 6.

**What is not new.** The pollution-haven question, whether stricter environmental regulation shifts trade or production toward jurisdictions with weaker rules, is established. Copeland and Taylor (1994) give the theory: a model of North-South trade in which the higher-income country chooses stronger environmental protection and specializes in cleaner goods. Ederington, Levinson and Minier (2005) show that pollution-abatement costs are unrelated to trade flows for most industries, that the industries with the largest abatement costs are the least geographically mobile, and that after accounting for this there is a significant effect on imports from developing countries in pollution-intensive, mobile industries. Levinson and Taylor (2008) find that US industries whose abatement costs rose most saw the largest increases in net imports from Canada and Mexico. A related mechanism, trade deflection, is studied for trade-policy restrictions by Bown and Crowley (2007), who find that US antidumping and safeguard restrictions deflected and depressed Japanese exports to third markets. On methods, we use the two-stage difference-in-differences estimator of Gardner (2022), a preprint, and Poisson pseudo-maximum-likelihood estimation following Santos Silva and Tenreyro (2006). Callaway and Sant'Anna (2021) and Borusyak, Jaravel and Spiess (2024) are related staggered-adoption estimators that we did not run. Investigative work by Public Eye, Unearthed and Danwatch on EU exports of banned pesticides is the empirical foundation for the question. We claim none of that, and no novelty beyond the arithmetic and instrument above, which themselves rest on a short, non-systematic literature check (limitation 11).

## 9. To verify before this leaves the repository

The basket-share assumptions; the substance-to-HS6 mappings (owner sign-off, `review/hs6-mapping-review.md`); how CEPII converts substance-named subheadings back to HS92; the Public Eye dataset's columns and the Unearthed 2024 aggregates; and a proper literature search (`/priorwork`). The academic citations are audited in `reviews/citation-audit.md`.

## Provenance of numbers

| Figure | Source |
|---|---|
| 15,448,188 rows; 234 countries; 544 HS6 | `scripts/build_panel.py` output; README |
| Five packages, placebo SEs, MDEs, shares | `data/attack/stage_g_placebo.json`, `analysis/power_placebo.py`, `decisions/0010-*.md` |
| Basket attack, placebo, ledger | `data/attack/*.json` |
| Overlap at ±2 to ±5; date consistency | `analysis/overlap.py`, `scripts/date_consistency.py`, `reviews/2026-09-19-readme-review.md` |
| 3808 by HS revision | `review/evidence/hs3808_by_revision.json` (UN Comtrade classification files) |
