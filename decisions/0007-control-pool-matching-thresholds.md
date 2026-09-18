# 0007 — Control-pool matching thresholds (pre-registered before estimation)

**Date:** 2026-09-18
**Status:** decided, code implemented, committed BEFORE running against real data (this is the point of this entry — see CLAUDE.md rule 2)

## The decision

For Stage D's matched control pool: a candidate never-restricted HS6 code
qualifies as a control for a treated product only if (a) it shares the
treated product's HS2 chapter, (b) its pre-period mean trade value is
within one order of magnitude (`log10` difference ≤ 1.0) of the treated
product's, and (c) its pre-period trend (OLS slope of `log1p(value)` on
year, pre-period years only) is within 0.15 log points/year of the
treated product's own trend. Implemented in `analysis/matching.py` as
`MATCHING_LOG10_VOLUME_TOLERANCE = 1.0` and
`MATCHING_TREND_TOLERANCE = 0.15`.

## Alternatives considered

- **Tighter volume band (e.g. factor of 3, log10 tolerance ≈ 0.5).**
  Rejected for the initial run: with ~540 candidates already filtered to
  one HS2 chapter and one order of magnitude, a tighter band risks
  leaving too few control units for the residual-variance-based standard
  errors this project's estimator relies on (see `analysis/twfe.py`) to
  mean anything. If the factor-of-10 band still leaves a healthy control
  count once run, a tighter band becomes worth trying as a robustness
  check — but that would be a SECOND, separately reported specification,
  not a replacement chosen after seeing which one narrows the CI more.
- **No trend filter, volume only.** Rejected: "comparable... same period"
  (the project brief's own words) plausibly means matching the
  trajectory, not just the level. Volume-only matching would still allow
  a control that happened to be on a steep unrelated growth path to
  distort the post-period comparison.
- **Percentile-based matching (e.g. nearest 10 by some distance metric)
  instead of a fixed tolerance band.** Rejected: a fixed, named tolerance
  is auditable and was decided before any candidate's specific numbers
  were computed; a "nearest N" rule implicitly changes its effective
  tolerance depending on how many candidates happen to be nearby, which
  is harder to defend as pre-registered in the same sense.

## Why this one

The 1.0 log10 tolerance is the literal, standard meaning of "same order
of magnitude" as instructed — not derived from this dataset. The 0.15
trend tolerance was set by looking at what a plausible TRUE effect size
would be (Stage 3's point estimates cluster 0.3-0.7 log points over a
multi-year post-period, roughly 0.05-0.15 log points/year) and picking a
matching band no wider than that — a trend-matching tolerance wider than
the effect being hunted for would not actually restrict anything
meaningfully.

## What would make it wrong

If, once run, either filter leaves fewer than roughly 10-15 controls for
some treated product, the resulting standard errors would likely be
unstable regardless of how well-matched those few controls are — that
would be evidence the tolerances are too tight for this dataset's control
pool size, not that matching itself was the wrong idea. Conversely, if
confidence intervals under matching turn out no tighter than the
unmatched full-pool intervals, that would suggest control-pool
heterogeneity wasn't the actual source of Stage 3/4's wide CIs (see
decisions/0005's own falsification criterion, which this entry
implements the numbers for).

## Who or what prompted it

The user's Stage D instruction ("select controls matched on pre-period
trade volume (same order of magnitude) and pre-period trend, within the
same HS chapter") and CLAUDE.md rule 2 (any tunable choice committed to
git before estimating, with reasoning) — this entry and the commit
containing `analysis/matching.py` and its tests happen together, before
`select_matched_controls` is ever run against `data/processed/observatory.duckdb`.
