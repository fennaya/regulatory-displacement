# Falsification Register

For each live claim in this project: what result would make us abandon
it, decided before the next estimation run that touches it — not after
seeing something inconvenient. A claim with no entry here, referenced in
the README, fails `tests/test_falsification_coverage.py` mechanically.
Vague criteria ("if the evidence doesn't hold up") are refused; see
`/falsify` for the standard this file is held to.

---

## displacement-hypothesis

**Claim:** When jurisdiction A restricts a product, flows of that product
into jurisdictions without the restriction rise after the effective date,
relative to control products that were never restricted.

**Current status: UNTESTED, not "weakly supported."** As of Stage A's
overlap audit, zero of the five testable treatment packages are CLEAN at
the pre-set ±5-year window (four are contaminated at every window; EU
endosulfan is clean at ±4 or narrower, and a single clean package is far
too underpowered to test the hypothesis). Every point
estimate produced so far (Stage 3's OLS-TWFE, Stage B's PPML re-estimate)
answers "did this HS6 basket move," not "did this substance's flows
displace," and neither confirms nor refutes the substance-level claim.
The staggered-adoption-robust re-estimate (`decisions/0003-*.md`) has since
been run and attacked (`decisions/0009-*.md`): it does not support the
hypothesis either. Treat every basket-level number as not evidence either way.

**Falsified by:** Once (a) the staggered-adoption-robust estimator is
implemented and run (done), and (b) Stage G's power analysis is done for each
package — a plurality of CLEAN or staggered-robust-corrected packages
returning a point estimate indistinguishable from zero (95% CI containing
zero) **at a specification with minimum detectable effect (MDE) smaller
than the plausible basket-share-implied true effect** (i.e. the null is
informative, not just underpowered) falsifies the hypothesis for the
substances tested. A single null package does not; the hypothesis is
about the mechanism in general, tested package-by-package.

**Refuses:** "the estimate wasn't significant" alone — see
`hs6-too-coarse` below; an underpowered null is not evidence against the
hypothesis, only evidence the instrument can't see it. Also refuses
"rest-of-world grew too, so nothing happened" as a standalone
falsification — that is exactly the confound `decisions/0004-*.md`'s
triple-difference restructuring exists to net out, not a reason to
declare the claim dead by inspection.

---

## hs6-too-coarse

**Claim:** HS6-level trade data is too coarse to detect a
substance-specific displacement effect, because the restricted substance
is diluted inside a basket of every other product sharing the same
6-digit code (5 subheadings total in heading 3808; the register's 8
substances collapse onto just 2 of them — 380810 and 380830).

**Falsified by:** Stage G's minimum-detectable-effect (MDE) at 80% power,
computed under the final specification, being SMALLER than the
basket-share arithmetic's implied effect size — i.e. if a plausible
export-share-weighted displacement of the restricted substance would
plausibly move the whole HS6 basket by more than the MDE, the coarseness
claim is falsified for that package: the instrument CAN see an effect of
plausible size, even though it's mixed with other products.

**RESOLVED, 2026-09-18 (`analysis/power.py`, Stage G):** NOT falsified for
4 of 5 testable packages — chlorpyrifos, endosulfan, atrazine, and
paraquat are all NOT DETECTABLE even at 100% displacement, high end of
the assumed basket-share range (MDE exceeds the maximum plausible implied
effect in every case). Neonicotinoids is BORDERLINE (detectable only if
the true basket share is toward the high end of its assumed 10-30%
range). Basket-share assumptions are stated per-substance with confidence
levels in `analysis/power.py`'s `BASKET_SHARE_ASSUMPTIONS` — only
imidacloprid's is anchored to a real (if inconsistent-across-vendors) web
search; the rest are explicitly unverified. **This instrument cannot see
a plausible-sized substance-specific effect for 4 of the 5 packages this
project can test, and this is arithmetic, not a vibe.**

**Refuses:** "the confidence interval is wide" as sufficient evidence —
width alone conflates low power (a real problem, separately diagnosed by
the MDE) with genuine coarseness-driven dilution (a different, specific
mechanism: the restricted substance being a small share of a basket
dominated by unrelated, unrestricted products). The two need to be told
apart with the actual arithmetic, not asserted from the CI width.

---

## forecast-buprofezin-2026

**Claim (STEP 6 watchlist, forecast `2026-buprofezin-eu-nonapproval`,
made 2026-09-18):** EU non-approval of buprofezin, predicted effective by
2026-12-31, will show elevated HS6 380810 exports from EU-bloc countries
to Brazil, Viet Nam, and Thailand.

**Falsified by:** Once panel data covers at least 2 full years after the
substance's ACTUAL (not predicted) effective date: EU-sourced HS6 380810
export value into the three predicted destinations, combined, growing by
LESS than 10 percentage points more than rest-of-world exporters'
growth into the same three destinations over the same window, in 2 or
more of the first 3 post-effective years. (The 10-point margin over
rest-of-world, not raw growth, is the bar, because Stage 4 already
established rest-of-world growth of 26-50% is pervasive and
substance-independent across every tested package — raw growth alone is
not informative here.) Also falsified, independent of the trade-flow test
above, if the actual non-approval decision does not happen within 2026 at
all, or is resolved as a renewed/extended approval rather than a
non-approval — the effective-date basis explicitly flagged this as the
least certain part of the forecast.

**Refuses:** Scoring this against a single year's data, or against raw
growth without the rest-of-world comparison. Also refuses moving the
predicted destination list after the fact — Brazil/Viet Nam/Thailand was
fixed at forecast time (`data/watchlist/forecasts.jsonl`, append-only,
2026-09-18) and cannot be edited to better fit whatever destinations
actually show movement.

---

## forecast-flufenacet-2026

**Claim (STEP 6 watchlist, forecast `2026-flufenacet-eu-stock-clearance`,
made 2026-09-18):** EU flufenacet stock-clearance deadline (2026-12-10)
will show elevated HS6 380830 exports from EU-bloc countries to Ukraine
and Brazil.

**Falsified by:** Same construction as `forecast-buprofezin-2026`, ported
to this substance/HS6/destination set: EU-sourced HS6 380830 export value
into Ukraine and Brazil combined growing by less than 10 percentage
points more than rest-of-world exporters' growth into the same two
destinations, in 2 or more of the first 3 post-effective years
(2026-2028 data).

**Refuses:** Same refusals as `forecast-buprofezin-2026`. Additionally
refuses treating this forecast as already resolved by the fact that
flufenacet's EU withdrawal deadline (2025-12-10) has already passed as of
this entry's date (2026-09-18) — the forecast is specifically about the
STOCK-CLEARANCE deadline (2026-12-10, when even grandfathered stock must
be gone), not the withdrawal date, and trade-flow data for the relevant
window is not yet fully available.

---

## basket-level-eu-restrictions-moved-trade

**Claim (staggered-robust basket result, Stage B.2/B.3):** the pooled did2s
estimate of +0.664 log points [0.381, 0.948] for HS6 380810/380830 versus
542 never-restricted chemical codes, 1995-2024, is evidence that EU
restrictions moved trade in the affected baskets.

**Status: FALSIFIED as an EU-restriction effect, 2026-09-19**
(`decisions/0009-attack-on-basket-level-result-verdict.md`; numbers in
`data/attack/basket_attack_results.json`).

**Would have been abandoned if (criteria applied, all met):** (a) the same
estimate on rest-of-world exporters of the same codes into the same
destinations was as large or larger — it was larger (+0.789 vs +0.664) and
the EU-minus-RoW triple difference was -0.124; (b) assigning the same cohort
years to randomly chosen never-restricted codes reproduced an ATT this large
at a rate above 5% — two-sided placebo p was 0.28-0.59 (EU-only) and
0.68-0.81 (triple difference); (c) event-time coefficients showed no
movement near the effective date — the divergence began 3-15 years after it.

**Refuses:** re-litigating with a different control pool or window chosen
after seeing this result; that would be tuning, not a new test (CLAUDE.md
rule 2). Also refuses reading this as "no displacement occurred": it says
this basket-level evidence does not support one, and composition (the
substance's share within its own basket) remains untestable with BACI.
