# Can public trade data detect regulatory displacement? A null result, its detection threshold, and an audit instrument

*Full draft, 2026-09-19. Every figure has a pointer to the repository file that produced it, and every statistic was computed by tested code, not by a language model. Every academic citation was checked against the published record on 2026-09-20 (`reviews/citation-audit.md`; a test fails if a citation has no verified audit entry). The paper states its limitations before its results; sections 2 and 3 come first on purpose.*

## Abstract

When the EU bans or restricts a pesticide for use inside the EU, does trade in that product relocate to destinations without the restriction? We build a register of nine cited restrictions (six independent treatment packages, five testable), a 30-year bilateral trade panel (CEPII BACI, HS chapters 28/29/38, 15.4 million rows), and a pre-specified difference-in-differences test. Every pre-specified test is null, and we do not read those nulls as evidence of no displacement. The reason is arithmetic. At HS6 resolution the restricted substance is one product among many in its basket; recomputed with placebo-derived standard errors, the minimum detectable effect at 80% power is 0.72 to 1.93 log points, so the substance would have to be roughly 51-86% of its basket, and fully displaced, before a package-level test could see it. Under our stated (mostly unverified) share assumptions none of the five packages is detectable. Public HS6 trade data therefore cannot confirm or refute substance-level displacement. Our contribution is a reproducible instrument, a catalogue of the design traps we fell into, and this detection-threshold arithmetic. We also apply the instrument to one institutional claim and report that the claim is testable in principle but that the test its wording implies has not, to our knowledge, been run, and that ours addresses a different claim.

## 1. Question and claim under test

The claim: when jurisdiction A restricts a product, flows of that product into jurisdictions without the restriction rise after the effective date, relative to never-restricted control products (`README.md`, `falsification.md#displacement-hypothesis`). Status: **untested**, not weakly supported. The scope is pesticides and hazardous chemicals only.

## 2. Limitations (stated before results)

1. **Resolution.** BACI reports HS6 totals; heading 3808 has five subheadings in the HS92 nomenclature used. The restricted substance's share of its own basket is not observed (`decisions/0009-*.md`; `falsification.md#hs6-too-coarse`).
2. **Contamination, reported as a band, not a count.** Whether a package is free of another same-code restriction inside its estimation window depends on the window. At the pre-set ±5-year window 0 of 5 packages are clean; at ±4, ±3 and ±2, 1 of 5 (EU endosulfan) is clean. The other four are contaminated at every window from ±2 to ±5. We did not choose a window: choosing after seeing which count is more favourable would be selecting on the outcome, and the difference is one package and one partial year (`METHODS.md`, "Why no single window was chosen"; `analysis/overlap.py`; `reviews/2026-09-19-readme-review.md`).
3. **Inference.** With one treated HS6 code per package no analytic standard error is reliable. Randomization inference over never-restricted codes gives a placebo SD of about 1.4 log points against a reported did2s SE of 0.145 (`data/attack/basket_attack_results.json`). Other standard errors here should be read as too small, which is why the detection thresholds in section 5 were recomputed.
4. **Basket-share assumptions** in the power arithmetic are mostly unverified; only imidacloprid's is anchored to a (vendor-inconsistent) market figure (`analysis/power.py`). Every "not detectable" verdict below is conditional on them.
5. **Zero cells.** BACI records only positive flows, so 59-61% of importer-product-year cells are zero-or-unreported and the data cannot say which.
6. **Register mappings are not independently reviewed.** The substance-to-HS6 mappings were proposed and self-confirmed by the model that built the pipeline; a review file for the project owner exists and is unanswered (`review/hs6-mapping-review.md`, `tests/test_mapping_provenance.py`, which is an expected failure until a human decides). External evidence attached on 2026-09-20 agrees with the function-to-subheading mapping for 6 of 8 substances (no mismatch found); 2 are unclear: chlorpyrifos-methyl (function not confirmed from a source) and endosulfan, which the WCO's HS2017 notes name in a substance-based subheading (3808.52/.59), so how much of its trade lands in 380810 in this HS92-converted panel is unknown. The panel is entirely in HS92 codes (CEPII documentation), and the 3808 restructuring occurred in HS2007, not HS2012 (UN Comtrade classification files). Two of nine events (2018 clothianidin, thiamethoxam) were sourced from secondary reporting; atrazine and endosulfan are Directive 91/414/EEC non-inclusion decisions labelled non-renewal.
7. **Validation coverage.** Only the "EU banned-pesticide exports" episode type can be tested with a chemicals panel.
8. **Analysis history.** The original specification came from the brief; the repairs that followed (PPML, staggered estimator, triple difference, matched controls, clustering) were chosen after the first estimates were uninformative and were **not pre-registered**. Only the matching thresholds and the destination groups were committed before estimation (`decisions/0007-*.md`, `0008-*.md`). 48 specifications were estimated, 7 with a CI excluding zero, in both signs; 2.4 would be expected by chance if all were independent nulls (`data/attack/spec_ledger.json`).
9. **The test we ran is not the test the Commission's wording implies.** The European Commission's official rationale for not proposing an export ban says a unilateral ban "may push these countries to buy the same or worse chemical pesticides from companies outside of the EU." That is a claim about **supplier substitution by importing countries**. Testing it needs importer-side purchases by substance and supplier origin, before and after an export ban. This study never ran that test. It examined whether EU *use* restrictions were followed by trade relocating to unrestricted destinations, in a setting where no EU-wide export ban was in force. Its null therefore says nothing for or against the Commission's claim, and must not be cited as if it did. The quote is reproduced by two secondary sources, not the primary; see section 6.1 for the source status.
10. **Notified quantity is not customs quantity.** Published notification tonnage (81,600 t in 2018, 122,000 t in 2024) is intended exports of mixtures, not shipments and not tonnes of active substance. It is used only as an order-of-magnitude anchor.
11. **No systematic literature search was run for this paper.** The citations in section 8 were each verified to exist and to say what we cite them for (`reviews/citation-audit.md`), but they are a short list, not a review, and `/priorwork` was not run. No novelty claim is made beyond the three items in section 8.

## 3. Data and register

- Panel: CEPII BACI HS92 v202601, 1995-2024, HS 28/29/38: 15,448,188 rows, 234 countries, 544 HS6 codes, 3.0% missing quantity (`scripts/build_panel.py`).
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

*What is established and what is not.* Established by recomputation: the direction and size of the SE correction, and the MDEs. Not established: the basket-share assumptions, which stay flagged as unverified. The placebo SE is a proxy: it assumes the treated code's noise resembles the pool's, and if the treated code is smoother it overstates its own noise, so the truth lies between the two SEs (both are reported). It rests on 20-29 placebos, about 13-16% sampling error, well inside the 2.3-3.7 times gap. The share the substance would need (51-86% of an HS6 basket) is a threshold that holds whatever the assumed shares are, and we judge, without verification, that no single active ingredient plausibly holds that share.

**Put in words: the restricted substance would have to make up more than half of its HS6 basket, and all of it would have to be displaced, before this instrument could reliably see it. Therefore any claim that EU restrictions did, or did not, cause trade displacement at the level of a single restricted substance is currently unfalsifiable with public HS6 trade data.**

## 6. Applying the instrument: Case 001

### 6.1 The claim, verbatim

The Commission's written statement to Danwatch (as transcribed by Corporate Europe Observatory, 29.06.2026): a unilateral production and export ban in the EU "would not guarantee an improvement in health and environmental protection in affected countries, as it may push these countries to buy the same or worse chemical pesticides from companies outside of the EU" (`testability/cases/case-001.md`, `testability/register.yaml`).

**Source status: two independent secondary sources; the primary is unretrieved.** The same statement is reproduced by Corporate Europe Observatory and by PAN Europe (both 29 June 2026; `testability/sources/case-001-ec-statement-to-danwatch.txt`, `case-001-pan-europe.txt`; the PAN Europe passages were matched character for character on 2026-09-20), which is better provenance than a single transcription. We searched for the Commission's own statement and for the Danwatch follow-up carrying it and did not find either. The Danwatch article of 18 May 2026 was found and does not reproduce the statement (`testability/sources/case-001-primary-source-attempts.txt`). The statement's date is unknown (between 13 May and 29 June 2026), and its context and any omissions are unverified.

### 6.2 Two framings of one position

The Commission's sentence opens with "a unilateral production and export ban in the EU", so production is explicitly in scope. It then gives its **mechanism** for why such a ban would fail: importing countries "may … buy the same or worse chemical pesticides from companies outside of the EU", that is, **supplier substitution by importing countries**. PAN Europe's press release also reports a shorter paraphrase, in quotation marks, of a Commission spokesperson's argument: an export ban "could simply shift production outside the EU while penalising European companies", that is, **production relocation**. Both passages were matched character for character on the page on 2026-09-20 (`testability/sources/case-001-pan-europe.txt`). The page does not say which Commission document the shorter phrase comes from, and we did not establish that.

An earlier draft of this paper said the relocation wording was not the Commission's. That was too strong and is withdrawn. The accurate finding is narrower: the public debate is not arguing about a fabrication. It amplifies the less specific of two framings, and the testable mechanism, substitution by importing countries, is the one that gets dropped. The two are tested with different data (importer purchases by supplier origin, versus the location of production and investment), and neither implies the other. Older secondary evidence shows the substitution form in industry argument: Euronews, 30 August 2023, reports that pesticide producers argue that banning exports will have no impact on developing countries, as they will continue to ship the chemicals from elsewhere.

### 6.3 Verdict

**Testable in principle. The test the wording implies (supplier substitution) has not been attempted by anyone we could find, and our search was limited. The tests that have been attempted, including this paper's, address a different claim.** With public HS6 data the effect that would matter (full elimination of notified banned-pesticide trade, about 11-18% of customs tonnes of heading 3808, 0.12-0.20 log points) is roughly 5 to 13 times below the detection threshold. That range comes from basket-level randomization SEs (0.33-0.54) and was already placebo-derived; the Stage G recomputation does not change it. The feasibility premise is supported: non-EU exporters ship 4.7 times (2018) and 7.2 times (2024) the EU's customs tonnage of heading 3808 into non-EU destinations. That supports the *possibility* of substitution, not its size or hazard.

The public evidence is better than we first wrote. Public Eye published the full dataset of its 2018 investigation (substance, exporting EU country, destination, notified quantity, year), and Unearthed publish 2024 country aggregates (`decisions/0006-*.md`, resolved 2026-09-19, considered and not adopted). It is EU-side only, notified not shipped, and has no importer-side supplier mix, so it cannot test substitution. A concrete disclosure request is in `testability/cases/case-001.md`.

Nothing here shows the Commission is right or wrong.

## 7. What can and cannot be claimed

- **Cannot be supported or refuted with public HS6 data:** "a ban would only shift trade or production abroad"; "restrictions did not change trade in the restricted substance."
- **Can be said:** at the HS6 basket level nothing distinguishes EU exports from rest-of-world exports after the restrictions; an apparent effect in a pooled basket regression was a product-type trend shared by all exporters.
- **What would make the question testable:** substance-level data: export notifications under the EU PIC Regulation with shipped quantities, importer-side purchases by supplier origin, or 8-digit customs lines. The Eurostat Comext CN8 split of heading 3808 is an **unverified lead**, not checked.

## 8. Contribution, and what is not new

**What we contribute.** (1) A reproducible instrument: a register, a panel, and a set of estimators, all in tested code, with decisions and falsification criteria committed in the repository. (2) A catalogue of design traps we fell into and documented: unit of treatment (events versus packages), contamination that depends on the window, standard errors that are too narrow with one treated code, an apparent basket effect that was rest-of-world growth, and mappings self-confirmed by the builder. (3) The arithmetic that HS6 aggregation cannot see substance-level displacement at realistic effect sizes. (4) A testability audit protocol (`testability/METHOD.md`) and one worked case.

**What is not new.** The pollution-haven question, whether stricter environmental regulation shifts trade or production toward jurisdictions with weaker rules, is established. Copeland and Taylor (1994) give the theory: a model of North-South trade in which the higher-income country chooses stronger environmental protection and specializes in cleaner goods. Ederington, Levinson and Minier (2005) show that pollution-abatement costs are unrelated to trade flows for most industries, that the industries with the largest abatement costs are the least geographically mobile, and that after accounting for this there is a significant effect on imports from developing countries in pollution-intensive, mobile industries. Levinson and Taylor (2008) find that US industries whose abatement costs rose most saw the largest increases in net imports from Canada and Mexico. A related mechanism, trade deflection, is studied for trade-policy restrictions by Bown and Crowley (2007), who find that US antidumping and safeguard restrictions deflected and depressed Japanese exports to third markets. On methods, we use the two-stage difference-in-differences estimator of Gardner (2022), a preprint, and Poisson pseudo-maximum-likelihood estimation following Santos Silva and Tenreyro (2006). Callaway and Sant'Anna (2021) and Borusyak, Jaravel and Spiess (2024) are related staggered-adoption estimators that we did not run. Investigative work by Public Eye, Unearthed and Danwatch on EU exports of banned pesticides is the empirical foundation for the question. We claim none of that. We make no novelty claim beyond the three contributions above, and even those rest on a short, non-systematic literature check (limitation 11).

## 9. To verify before this leaves the repository

The primary text of the Commission's statement; the Public Eye dataset's columns and the Unearthed 2024 aggregates; the basket-share assumptions; the substance-to-HS6 mappings (`review/hs6-mapping-review.md`); and a proper literature search (`/priorwork`). The academic citations themselves are audited in `reviews/citation-audit.md`.

## Provenance of numbers

| Figure | Source |
|---|---|
| 15,448,188 rows; 234 countries; 544 HS6 | `scripts/build_panel.py` output; README |
| Five packages, placebo SEs, MDEs, shares | `data/attack/stage_g_placebo.json`, `analysis/power_placebo.py`, `decisions/0010-*.md` |
| Basket attack, placebo, ledger | `data/attack/*.json` |
| Overlap at ±2 to ±5 | `analysis/overlap.py`, `reviews/2026-09-19-readme-review.md` |
| Case 001 arithmetic | `testability/cases/case-001-arithmetic.json`, `scripts/case001_arithmetic.py` |
