# 0010 — Stage G recomputed with placebo-derived standard errors

**Date:** 2026-09-19
**Status:** implemented. Numbers in `data/attack/stage_g_placebo.json` (`scripts/stage_g_placebo.py`, `analysis/power_placebo.py`, 6 tests written and passing before the real-data run).

## What was wrong, and which way

Stage G's minimum detectable effects (MDEs) used Stage E's cluster-robust standard errors. The placebo tests (`decisions/0009-*.md`) show analytic SEs are too narrow when one code is treated: Stage E clusters at exporter-product, but the exporter-product clusters inside one treated HS6 code share that code's common shock.

**Direction, stated before the recomputation:** too-narrow standard errors mean the true intervals are WIDER, so the true MDE is LARGER, so MORE packages are undetectable at a given assumed effect size, not fewer. The error made the conclusion look *less* robust than it is, while invalidating its specific figures.

## Method

For each of the 5 testable packages, in-space placebo over the package's pre-registered matched control pool (`decisions/0007-*.md`; 20-29 codes): each pool member in turn plays the restricted code (same effective year, exporters and window), the real treated code is dropped, and the rest of the pool are its controls. The Stage E estimator is applied to each. The SD of the placebo estimates is the SE. Deterministic (nothing random). As a check that it is the same estimator, the real-code estimate from this code path reproduces Stage E's coefficient to 1e-6 for every package (asserted in the script).

## Result

| Package | Stage E SE | Placebo SE | Ratio | MDE (Stage E → placebo) | Share of basket needed to detect at full displacement (Stage E → placebo) | Max plausible implied effect (assumed shares) | Verdict (Stage E → placebo) |
|---|---|---|---|---|---|---|---|
| Endosulfan | 0.213 | 0.539 | 2.5x | 0.60 → 1.51 | 45% → 78% | 0.16 | not detectable → not detectable |
| Neonicotinoids | 0.112 | 0.255 | 2.3x | 0.31 → 0.72 | 27% → 51% | 0.36 | **borderline → not detectable** |
| Chlorpyrifos | 0.130 | 0.475 | 3.7x | 0.36 → 1.33 | 30% → 74% | 0.22 | not detectable → not detectable |
| Atrazine | 0.155 | 0.479 | 3.1x | 0.43 → 1.34 | 35% → 74% | 0.22 | not detectable → not detectable |
| Paraquat | 0.202 | 0.690 | 3.4x | 0.57 → 1.93 | 43% → 86% | 0.22 | not detectable → not detectable |

**Direction check:** the placebo SE is wider than Stage E's for every package (2.3x to 3.7x). The direction predicted above holds for all five; it was checked, not assumed.

**Updated claim:** 5 of 5 testable packages are not detectable under the placebo SEs, given the assumed basket shares. Under Stage E's SEs it was 4 of 5 with neonicotinoids borderline. Robust to which SE is used: **at least 4 of 5**; neonicotinoids is the only package whose verdict depends on the choice. The MDE range moves from 0.31-0.60 to 0.72-1.93 log points; the share of its basket a restricted substance would need to be, fully displaced, for a package-level test to reach 80% power moves from 27-45% to 51-86%.

**Case 001's "roughly 5 to 13 times below the detection threshold" is unchanged.** It was never based on Stage E: it uses the basket-level randomization SEs (placebo SD 0.33 and 0.54, `data/attack/basket_attack_results.json`), so it was already placebo-derived. The brief's premise that it rested on Stage E SEs was mistaken; it is left as is and its basis is now stated in `testability/cases/case-001.md`.

## The sentence

*Our original detection thresholds were too generous to the instrument: they implied more detection power than existed. Correcting the standard errors raises the thresholds and strengthens the conclusion.*

(Amended 2026-09-20: an earlier wording, "conservative in the wrong direction", was wrong and is withdrawn everywhere; this is the sentence used in PAPER.md section 5 and the README.)

## What this moves toward Established, and what it does not

**Now supported by the recomputation (Established):** the direction and size of the SE correction; the placebo-derived MDEs above; that the assumed maximum implied effects (0.16-0.36 log points) are below every package's placebo MDE.

**Still unverified, and stays flagged:**
- **The basket-share assumptions.** Only imidacloprid's is anchored to a market figure (vendor-inconsistent); the rest are explicitly unverified (`analysis/power.py`). The verdict "not detectable" is conditional on them. Independent of those assumptions, the required share (51-86%) is more than half of the whole HS6 basket; in our judgement, not verified, no single active ingredient plausibly makes up that share of global formulated-insecticide or herbicide trade.
- **"100% displacement adds the whole share"** to the observed series is generous to the instrument (EU exports to non-EU destinations already existed before the restrictions).
- **The placebo SE is a proxy.** It assumes the treated code's noise resembles the pool members'. If the treated code is smoother (it is a large aggregate), the placebo SE overstates its true SE, and the truth lies between the Stage E and placebo figures. Both are reported; at both, at least 4 of 5 are undetectable. The placebo SD is estimated from 20-29 units, so it carries roughly 13-16% sampling error of its own; the 2.3x-3.7x gap is well outside that.

## What would make it wrong

Substance-level data showing a restricted substance to be more than half of its HS6 basket; or a design in which the treated code's own noise is demonstrably far below the pool's, which would pull the true SE toward Stage E's.

## Who or what prompted it

The project owner's close-out instruction (step 3), following the placebo results in `decisions/0009-*.md`.
