# Can public trade data detect regulatory displacement? A null result and an instrument

*Argument skeleton. Every figure has a pointer to the repo file that produced it. Sections marked TO WRITE are prose still to be drafted; nothing in this file is a claim the repo does not support. References are cited author-year and are not yet checked against the originals.*

## Abstract (draft)

When the EU bans or restricts a pesticide for use inside the EU, does trade in that product relocate to destinations without the restriction? We build a register of nine cited EU and international restrictions (six independent treatment packages, five testable), a 30-year bilateral trade panel (CEPII BACI, HS chapters 28/29/38, 15.4 million rows), and a pre-specified difference-in-differences test. Every pre-specified test is null. We then show why: at HS6 resolution the restricted substance is one product among many in its basket, and under stated assumptions the substance would have to be roughly 27-45% of its basket, and 100% displaced, before a package-level test reaches 80% power. Public trade data at this resolution therefore cannot confirm or refute substance-level displacement, and claims that a regulatory ban "would only move production elsewhere" are, at this granularity, not falsifiable either way. We report the arithmetic, the disclosure that would make the question testable, and a reusable audit protocol for whether an institution's empirical justification can be tested at all.

## 1. Question and claim under test (TO WRITE)

The claim: when jurisdiction A restricts a product, flows of that product into jurisdictions without the restriction rise after the effective date, relative to never-restricted control products (`README.md`, `falsification.md#displacement-hypothesis`). Status in the repo: **untested**, not weakly supported.

## 2. Limitations (stated before results)

1. **Resolution.** BACI reports HS6 totals; heading 3808 has five subheadings in the HS92 nomenclature used. The restricted substance's share of its own basket is not observed (`decisions/0009-*.md` section 3; `falsification.md#hs6-too-coarse`).
2. **Contamination.** At the pre-set ±5-year window no package is CLEAN; four of five are contaminated at every window from ±2 to ±5, endosulfan is clean at ±4 or narrower (`analysis/overlap.py`; `reviews/2026-09-19-readme-review.md`).
3. **Inference.** With one treated HS6 code per package, no analytic standard error is reliable. Randomization inference over never-restricted codes gives a placebo SD of about 1.4 log points against a reported did2s SE of 0.145 (`data/attack/basket_attack_results.json`). All standard errors elsewhere in this paper should be read as too small; every MDE below is therefore optimistic.
4. **Basket-share assumptions** used in the power arithmetic are mostly unverified; only imidacloprid's is anchored to a (vendor-inconsistent) market figure (`analysis/power.py`).
5. **BACI records only positive flows**, so 59-61% of importer-product-year cells are zero-or-unreported and the data cannot say which.
6. **Register.** HS6 mappings are self-confirmed, not human-reviewed; two of nine events (2018 clothianidin, thiamethoxam) were sourced from secondary reporting; atrazine and endosulfan are Directive 91/414/EEC non-inclusion decisions labelled non-renewal (`data/register/`).
7. **Validation coverage.** Only the "EU banned-pesticide exports" episode type can be tested with a chemicals panel; plastic-waste and used-vehicle episodes cannot.
8. **Analysis history.** The original specification came from the brief; the repairs that followed (PPML, staggered estimator, triple difference, matched controls, clustering) were chosen after the first estimates were uninformative and were **not pre-registered**. Only the matching thresholds and the destination groups were committed before estimation (`decisions/0007-*.md`, `0008-*.md`). 48 specifications were estimated across the work (`data/attack/spec_ledger.json`), 7 with a CI excluding zero, in both signs; 2.4 would be expected by chance if all were independent nulls.

## 3. Data and register (TO WRITE)

- Panel: CEPII BACI HS92 v202601, 1995-2024, HS 28/29/38: 15,448,188 rows, 234 countries, 544 HS6 codes, 3.0% missing quantity (`scripts/build_panel.py`).
- Register: nine cited events, eight substances, collapsed to six treatment packages by (jurisdiction, HS6, decision date, effective date); five testable. Unit-of-treatment argument: `decisions/0001-*.md`.

## 4. Pre-specified design and results

**4.1 Original specification** (two-way fixed effects event study, ~542 controls): all five package estimates positive, every 95% CI roughly ±2 log points, none significant (`analysis/comparison.py`, dashboard `/specifications`).

**4.2 Pre-registered choices, both null.** Matched control pools cut SEs 42-61%, no package significant (`decisions/0007-*.md`, `0005-*.md`). Destination groups fixed before estimation (high-exposure vs low-exposure): no between-group difference distinguishable from zero (`data/destination_groups_v1.yaml`, `decisions/0008-*.md`).

**4.3 Repairs, labelled post hoc.** PPML keeping zero cells: none significant (`analysis/ppml.py`). Triple difference against rest-of-world exporters of the same product: point estimates shrink 60-93% (`analysis/triple_diff.py`). Truncated windows: unstable (atrazine +0.407 to -0.017, both spanning zero).

**4.4 One exploratory result that did not survive.** A pooled, staggered-robust basket estimate (+0.664 log points, CI [0.381, 0.948]) was found after the package-level tests were null. It is reported here only as a failed check, not as a finding: rest-of-world exports of the same codes rose more (+0.789), the EU-specific triple difference is -0.124, the placebo p-values are 0.28-0.81, and there is no discontinuity at the effective dates (`decisions/0009-*.md`).

**4.5 Rediscovery.** Three documented cases (Unearthed/Public Eye 2020): directional recall 100%, significant recall 0%. Uninformative on direction, since every original estimate was positive.

## 5. The arithmetic (the sentence that matters)

*What a package-level test at 80% power can and cannot see.* The minimum detectable effect at 80% power and 5% significance is 0.31 to 0.60 log points across the five packages (`analysis/power.py`, computed from Stage E's clustered SEs, which understate the true SE, so the true MDE is larger). Under stated share assumptions, full displacement of a restricted substance that is 10-30% of its basket would move the basket by 0.11-0.36 log points at most; for four of five packages the maximum plausible implied effect lies below the MDE, and the fifth (neonicotinoids) is borderline. **Put in words: the restricted substance would have to make up roughly 27-45% of its HS6 basket, and all of it would have to be displaced, before this instrument could reliably see it; at the shares we can plausibly assume, it cannot. Therefore any claim that EU restrictions did, or did not, cause trade displacement at the level of a single restricted substance is currently unfalsifiable with public HS6 trade data.**

Package-level shares needed for 80% power under full displacement: endosulfan 45%, paraquat 43%, atrazine 35%, chlorpyrifos 31%, neonicotinoids 27% (computed from the MDEs above; `analysis/power.py`).

## 6. What can and cannot be claimed (TO WRITE)

- **Cannot be supported or refuted with public HS6 data:** "a ban would only shift production abroad"; "restrictions did not change trade in the restricted substance."
- **Can be said:** at the HS6 basket level, nothing distinguishes EU exports from rest-of-world exports after restrictions; an apparent effect in a pooled basket regression is a product-type trend shared by all exporters.
- **What would make the question testable:** substance-level export data: export notifications under the EU PIC Regulation, or 8-digit customs lines. The Eurostat Comext CN8 split of heading 3808 by chemical family is an **unverified lead**, not checked here.

## 7. A method that travels (TO WRITE, links to Part 4)

The transferable contribution is the testability audit protocol (`testability/METHOD.md`): extract the empirical claim, specify the test, inventory the evidence, run the power arithmetic, state the disclosure gap, return one of four verdicts including "probably correct." Case 001 applies it to the European Commission's June 2026 rationale for not proposing an export ban.

## 8. Discussion and next steps (TO WRITE)

Notes for the draft: the paper's honesty about its own path (section 2.8) is part of the argument, not an aside; a null with a stated detection threshold is a stronger claim than "no significant effect."

## Provenance of numbers

| Figure | Source |
|---|---|
| 15,448,188 rows; 234 countries; 544 HS6 | `scripts/build_panel.py` output; README |
| Five packages, MDEs, shares | `analysis/power.py`, `analysis/comparison.py` |
| Basket attack, placebo, ledger | `data/attack/*.json` |
| Overlap at ±2 to ±5 | `analysis/overlap.py`, `reviews/2026-09-19-readme-review.md` |
