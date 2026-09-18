# 0002 — Switch from log-linear OLS to Poisson pseudo-maximum likelihood (PPML) in levels

**Date:** 2026-09-18
**Status:** implemented, not yet the reported headline (`analysis/ppml.py`, committed at checkpoint `ed178d9`; full 5-package comparison run but not yet written into README/dashboard as of this entry)

## The decision

Replace log(1+value) two-way-fixed-effects OLS with Poisson
pseudo-maximum likelihood on trade values in levels, fixed effects on
importer + product + year (exporter dimension pooled — see "What would
make it wrong" below), fit via `pyfixest.fepois` with heteroskedasticity-
robust covariance (cluster-robust once Stage E lands). Panel granularity
changed at the same time, from (product, year) — value summed across the
whole non-restricting-destination set before any transformation — to
(importer, product, year), with genuine zero flows filled in rather than
summed away.

## Alternatives considered

- **Keep log-linear OLS, aggregate at (product, year).** This is what
  Step 3 originally did. Rejected: aggregating over ~150-200 destinations
  before logging makes a true collective zero rare, which hides exactly
  the observations where displacement shows up first — one destination
  going from zero imports to positive. Measured directly: at
  (importer, product, year) granularity, 59-61% of cells across the 5
  testable packages are genuine zeros.
- **Log-linear OLS at the correct (importer, product, year) granularity,
  dropping zero cells.** Implemented as the explicit comparison point in
  `fit_flowlevel_log_ols_att` rather than rejected outright — it shows
  concretely what the original design avoided facing: ~650,000-746,000
  of ~1.07-1.25 million cells (59-61%) get dropped outright because
  log(0) is undefined. Not used as the primary estimator because
  discarding that much of the panel, non-randomly (zeros are not missing
  at random — a destination with zero imports is informative), is the
  textbook case PPML exists to avoid (Silva & Tenreyro 2006).
- **Poisson via statsmodels GLM with manually-built dummy fixed effects**
  (matching the from-scratch style of `analysis/twfe.py`, to avoid an
  external dependency). Rejected on scale grounds: a dense dummy-variable
  design matrix for ~540 products x ~150-200 importers x ~11 years is
  intractable; `pyfixest` implements the standard sparse/demeaned HDFE
  algorithm this scale requires (Correia, Guimarães & Portugal), and its
  simple case was checked against `analysis/twfe.py`'s own OLS output on
  synthetic data as a sanity cross-check before trusting it on real data.

## Why this one

PPML is standard in the gravity/trade literature specifically because
trade flows are heteroskedastic and contain many structural zeros;
log-linear OLS under heteroskedasticity is a biased estimator of the
mean effect, not just a less efficient one (Silva & Tenreyro 2006) — this
is textbook, not a judgment call. Verified on synthetic data with a known
injected multiplicative effect before touching real data
(`tests/test_ppml.py`): the mean recovered coefficient across 6 seeds was
within 0.02 of the true 0.5 log-point effect.

## What would make it wrong

- If the true generating process were closer to log-normal than Poisson
  (a specific concern with PPML when data are extremely over-dispersed),
  PPML's standard errors could understate uncertainty; this is why
  Stage E's cluster-robust covariance (exporter-product level) is a
  planned, not optional, follow-up.
- Pooling the exporter dimension (rather than including exporter-level
  fixed effects, which the user's Stage B instructions literally named
  as one of the four requested FE dimensions) was a compute-tractability
  and research-question decision, not a limitation discovered after the
  fact: the treatment is defined at the EU-bloc level throughout this
  project, so an exporter-level FE (distinguishing France from Malta)
  doesn't serve the causal question being asked. If a future version asks
  a within-EU question (e.g. "did large vs small EU exporters respond
  differently"), this pooling would need revisiting.

## Who or what prompted it

The user's Stage B instruction, verbatim: "Current estimates use
log-linear OLS with two-way fixed effects. Both choices are wrong here
... Trade data is heteroskedastic and full of zeros; log-linear OLS is
biased under heteroskedasticity. PPML retains zero flows."
