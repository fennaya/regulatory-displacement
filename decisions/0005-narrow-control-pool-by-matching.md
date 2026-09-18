# 0005 — Narrow the control pool by pre-period volume and trend matching, instead of using all 540+ chemical HS6 codes

**Date:** 2026-09-18
**Status:** implemented (`analysis/matching.py`, thresholds pre-registered in `decisions/0007-*.md` before this run). Result: matching cut every package's control pool from 542 to 20-29 units (same HS2 chapter, ~55 candidates before volume/trend filtering), and standard errors dropped 40-61% across all 5 packages (e.g. neonicotinoids: SE 1.101 -> 0.428; endosulfan: 1.214 -> 0.646). This confirms the mechanism hypothesized below: control-pool heterogeneity was a real, measurable contributor to Stage 3/4's wide confidence intervals, not an inherent property of the data. No package reaches significance even with the tighter matched-pool CIs, but neonicotinoids [-0.521, +1.155] and chlorpyrifos [-1.008, +1.239] are now visibly closer to it than their unmatched counterparts.

## The decision

For each treated product, select controls matched on pre-period trade
volume (same order of magnitude) and pre-period trend, within the same
HS chapter, never-treated only. Report how many controls survive
matching per treated product and what got excluded.

## Alternatives considered

- **Keep the full ~540-code control pool (current state).** Rejected as
  the sole design, not because it's invalid, but because it mixes
  products differing by orders of magnitude in trade scale into one
  pooled fixed-effects regression, which is a plausible contributor to
  the very wide confidence intervals reported throughout Stage 3 and
  Stage 4 (roughly ±1 to ±1.8 log points at 95% under OLS-TWFE). A
  control pool dominated by products with wildly different scale and
  trend than the treated product is not obviously "comparable... same
  period" in the sense the original project brief asked for.
- **Match on product description similarity (e.g. same 4-digit heading)
  instead of trade statistics.** Not selected as the primary criterion:
  within chapter 38 heading 3808 alone there are only 4-5 sibling codes
  per treated product (see `mappings/chemical_hs6_mappings_v1.yaml`'s own
  discussion of HS6 coarseness), too few to support a control group with
  useful residual variance for standard-error estimation. Volume/trend
  matching across the full three-chapter scope keeps enough control units
  while still restricting to genuinely comparable-scale products.

## Why this one

Not yet empirically verified in this repo — this entry records the
reasoning given for the decision, not a result confirming it improves
inference. The mechanism is plausible (unit fixed effects should in
principle absorb level differences regardless of scale, but if
scale-driven heteroskedasticity or differential pre-trend volatility
across the 540 controls is inflating the residual variance used for
standard errors, narrowing to a matched, more homogeneous pool should
tighten — not just relabel — the confidence intervals). This needs to be
checked once implemented, not assumed.

## What would make it wrong

If confidence intervals under the matched, narrower control pool turn out
similar to or wider than the unmatched full-pool intervals, that would
be direct evidence against the mechanism above, and would suggest the
wide CIs come from a different source (e.g. genuinely low treatment-
period variance, or the small number of years in each event window)
rather than control-pool heterogeneity.

## Who or what prompted it

The user's Stage D instruction, verbatim: "Stop using all 540+ chemical
HS6 codes as controls; they differ by orders of magnitude in trade
scale."
