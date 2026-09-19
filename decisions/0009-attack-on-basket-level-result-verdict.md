# 0009 — Attack on the surviving basket-level result: it does not survive

**Date:** 2026-09-19
**Status:** decided. Verdict: **FAILS.** The staggered-robust +0.664 log points is not evidence that EU restrictions moved trade in the affected basket.

All numbers below come from `data/attack/basket_attack_results.json` (produced by `scripts/attack_basket.py`, code in `analysis/basket_attack.py`, 8 tests on synthetic data with known answers written and passing first) and `data/attack/spec_ledger.json` (`scripts/spec_ledger.py`). None was typed from memory.

## The target

"+0.664 log points, 95% CI [0.381, 0.948], staggered-robust (did2s), HS6 basket level, is evidence that EU restrictions moved trade in the affected basket." Cohorts: HS6 380810 (first EU restriction 2006) and 380830 (2004) against 542 never-treated chemical HS6 codes, 1995-2024.

## 1. Triple difference check — the original spec did NOT use it

`analysis/staggered.py` used EU-bloc exports to non-EU destinations only, against never-treated codes: a simple control, no rest-of-world comparison. Rerun on the same panel, same estimator:

| Outcome (same codes, same destinations, same estimator) | ATT (did2s) | 95% CI |
|---|---|---|
| EU exports (the original) | +0.664 | [+0.381, +0.948] |
| **Rest-of-world exports** of the same codes | **+0.789** | [+0.571, +1.007] |
| **Triple difference** (EU minus RoW) | **-0.124** | [-0.239, -0.010] |

Rest-of-world exporters' shipments of the same HS6 codes to the same destinations rose MORE than the EU's. The EU-specific component is slightly negative. The whole effect is common to exporters not bound by any EU restriction, so it is not an EU-restriction effect. This is the same pattern as Stage C (60-93% of every per-package estimate removed), here at 117%.

## 2. Who drives it

- Leave-one-code-out (did2s, EU-only outcome): 380810 alone +0.841 [0.674, 1.008]; 380830 alone +0.505 [0.346, 0.664]. Both positive, 380810 carries more. On the triple-difference outcome: 380810 alone -0.051 [-0.114, +0.011]; 380830 alone -0.191 [-0.253, -0.129].
- **The +0.664 versus old +0.662 endosulfan coincidence is real overlap in rows, not just a number.** 380810 through 2017 only (the endosulfan-era window, before neonicotinoids) gives EU-only +0.629, close to the old +0.662, and +0.039 on the triple difference. The pooled figure is an average over two different post-lengths of two different estimands that happens to land on the old number.
- **Timing: there is no jump at the effective date.** Event-time (each treated code vs never-treated, `analysis/twfe.py`): 380810 EU-only is flat before (mean -0.001), ~0 at k=0..1, mean +0.213 for k=0..4, then ramps to +1.152 (mean, k>=10). 380830 EU-only: pre-mean -0.151, post k=0..4 -0.144, k>=10 +0.663. A restriction effect should appear near the effective date; this appears 3-15 years later, as a slow divergence. On the triple-difference outcome the late values are negative (380810 k>=10 mean -0.099; 380830 -0.458).

## 3. Composition artifact

**Cannot be tested with the data in this repo.** BACI/Comtrade report HS6 totals only; the restricted substance's share of its own basket is not observed, so "its share fell while others rose" is untestable here. The one indirect check available is unit value: EU-only log-quantity ATT is +0.663 [0.445, 0.881] (same size as value, +0.664), and the log unit-value ATT is +0.030, essentially zero. So the rise is volume, not price. A mix shift among substances with similar unit values would be invisible to this test; it weakly argues against a large shift toward cheaper or dearer products and nothing more. Missing quantity is small on these codes (1.6% and 0.6%). **Unverified lead, not checked in this session:** Eurostat Comext reports EU exports at 8-digit CN level, and heading 3808 is split by chemical family there; that could allow a partial composition test on the exporter side. Not confirmed.

## 4. Multiple comparisons

Ledger of Stage A-H specifications (`analysis/spec_ledger.py`, `scripts/spec_ledger.py`): **48 estimates** (45 re-estimated live, 3 discarded and recorded by hand: the chlorpyrifos window bug, and the two levels-scale staggered fits). **7 have a 95% CI excluding zero**; expected by chance at 5% with 48 independent nulls: 2.4; probability of at least one clear if all were independent nulls: 91%. Of the 7: 3 are artifacts or discarded (window bug, two levels fits). Live: 4 clears (3 distinct estimands: neonicotinoid clustered ATT +0.270, chlorpyrifos flow-level log-OLS -0.205, staggered pooled +0.664 which appears twice as TWFE and did2s). Live-only: 4 clears of 45 vs 2.25 expected, P(>=4) = 0.19 under independence. **They point in both directions.** The README's claim that the staggered result was "the only effect in this whole project that doesn't cross zero" was factually wrong and is corrected in the same commit as this entry. Caveats: the tests are not independent (one panel), and the discarded count is a reconstruction from history, so n is a lower bound.

## Placebo (randomization inference) — the estimate is unremarkable

With one treated code per cohort, asymptotic clustered SEs are not reliable. Assigning the real cohort years (2004, 2006) to randomly chosen never-treated codes, 2000 draws: placebo SD of the pooled ATT is 1.46 (all 542 codes) and 1.43 (55 chapter-38 codes), against a did2s SE of 0.145. **The analytic SE is roughly ten times too small.** The real EU-only ATT (+0.681, TWFE) has two-sided placebo p = 0.585 (all codes) and 0.276 (chapter 38). The triple-difference ATT (-0.117): p = 0.805 and 0.682. Nothing here is distinguishable from a randomly picked code.

## 5. Magnitude plausibility

+0.664 log points = +94.3% (CI +46.3% to +158.1%). For substance-specific displacement to produce that, with 100% of the restricted substance's exports appearing as new exports, the substance would have to be about 48.5% of the code's whole basket (CI 31.7% to 61.3%). Against `analysis/power.py`'s assumed shares (mostly unverified, only imidacloprid anchored): 380830 (atrazine 5-20% + paraquat 5-20%, combined 10-40%) tops out at an implied 0.51, below the pooled 0.664; 380810 (neonicotinoids 10-30% + chlorpyrifos 5-20% + endosulfan 3-15%, combined 18-65%) reaches it only at the very top of every range at once. And "100% displaced as new exports" is generous: EU exports to non-EU destinations already existed before the bans, so the incremental volume is bounded by domestic EU use that could be redirected. **Direct answer: not credible as a substance-specific effect.**

## 6. Causal story

The one account that fits all of the above: heading 3808 formulated agrochemicals grew faster than the industrial chemicals (chapters 28/29/38) used as controls, for all exporters, over decades; rest-of-world exports of the same codes rose more than the EU's, the divergence begins years after the effective dates and keeps growing to 2024, and unit values did not move. That is a product-type trend, not an EU-restriction effect. No story survives that is not composition (untestable here), coincidence (placebo p 0.28-0.59; 3 live clears among 44 estimands vs 2.2 expected), or a secular product-type trend.

## Verdict

**FAILS.** What made it fail: (1) rest-of-world rose more than the EU (+0.789 vs +0.664) and the EU-specific component is -0.124; (2) the estimate is not distinguishable from random codes given the same cohort structure (placebo p 0.28-0.81), and the reported SE overstated precision about tenfold; (3) no discontinuity at the effective date; (4) the magnitude needs about half the basket fully displaced. What it could not be tested on: composition (data absent).

## What would make this verdict wrong

Substance-level export data (customs 8-10 digit lines, or export notifications) showing the restricted substances' shares rising while a rest-of-world comparison stayed flat; or a placebo design whose control codes are matched on trend and it still rejects.

## Who or what prompted it

The user's Part 1 attack instruction, citing that +0.664 versus +0.662 was "too close to ignore."
