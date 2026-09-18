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
overlap audit, zero of the five testable treatment packages are CLEAN —
every one is CONTAMINATED by a same-HS6 neighbor package. Every point
estimate produced so far (Stage 3's OLS-TWFE, Stage B's PPML re-estimate)
answers "did this HS6 basket move," not "did this substance's flows
displace," and neither confirms nor refutes the substance-level claim.
Treat any headline number reported before a CLEAN package exists, or
before the staggered-adoption-robust re-estimate (`decisions/0003-*.md`,
not yet implemented) lands, as not evidence either way.

**Falsified by:** Once (a) the staggered-adoption-robust estimator is
implemented and run, and (b) Stage G's power analysis is done for each
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
plausible size, even though it's mixed with other products. Not yet
computed as of this entry (Stage G is not yet run).

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
