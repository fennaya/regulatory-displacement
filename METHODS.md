# METHODS

How to reproduce this design on a different hazard family (a different
product category, a different set of restrictions, a different trade
panel). Written after the causal-specification repair (see README's
"causal-specification repair" section and `decisions/*.md`), so it
reflects the repaired design, not the original one that turned out
uninformative.

## 1. Get a trade panel with a scope you can defend

Pick a product scope narrow enough that "control products" are genuinely
comparable (same order of magnitude, same broad industry) — see
`config.py`'s `CHEMICAL_HS2_CHAPTERS` and its own documented rationale.
Load into DuckDB with provenance on every row (`ingest/baci.py`'s
pattern: source, source_version, retrieved_at columns). Report the
panel's actual coverage (year range, country count, product count,
missing-data share) before doing anything else — `panel_stats.py`.

**Trap to avoid:** don't aggregate away the dimension where your effect
would actually show up before you've decided what that dimension is. The
original version of this project summed trade value across every
destination before taking logs, which hid the fact that 59-61% of
individual (destination, product, year) cells have no recorded flow (zero or unreported; BACI records only positive flows) — exactly
where a "destination went from zero to positive" signal would live. See
`analysis/ppml.py`'s module docstring.

## 2. Build a register, not a dataset

Structured events, one per restriction, each with:
- A **substance**, a **jurisdiction**, a **restriction type** (be precise
  about the legal mechanism — a non-renewal, a withdrawal, and a Prior
  Informed Consent listing are not the same instrument and don't produce
  the same expected trade signature; see `register/schema.py`'s
  `RestrictionType` and the Rotterdam Convention event's own notes in
  `data/register/events/events_v1.yaml` for why).
- **decision_date and effective_date as separate fields, always.** The
  gap between them is itself a finding (anticipatory stockpiling), not
  noise to average away.
- A **citation** (source document, source clause, retrieval date). No
  citation, no record — `register/store.py`'s loader drops uncited
  records rather than guessing.
- A proposed, then human-confirmed, **HS6 mapping** with the imprecision
  stated per mapping, not asserted once in a README paragraph
  (`register/mappings.py`).

## 3. Before estimating anything: collapse to the real unit of treatment

Check whether your "events" are actually independent. Companion
instruments — regulations adopted together, covering the same product
code, taking effect the same day — are one experiment, not one per named
substance. `analysis/packages.py`'s grouping key
`(jurisdiction, hs6, decision_date, effective_date)` is deliberately
mechanical (an assertion, not a judgment call) precisely so it can't be
tuned. **Verify the collapse is right**, don't assume it: check that
collapsed constituents actually produce identical downstream estimates
before trusting the grouping (this project did, and found bit-identical
output, confirming the events truly weren't independent).

## 4. Audit for contamination before running a single regression

If any two treated units share a comparison code (the same HS6, the same
matched-control criterion, whatever your panel's version of "same
basket" is) and their estimation windows overlap in calendar time, every
affected estimate is contaminated by the other event, not just noisy.
`analysis/overlap.py`'s pattern: read the window the estimator actually
used (post any coverage clipping) off its own output, not a nominal
parameter; check every same-code pair for overlap; classify CLEAN /
CONTAMINATED / UNTESTABLE as a first-class column, not a footnote;
assert a CLEAN classification never coexists with a recorded overlap (a
consistency check on your own audit code, not an extra finding).

**If zero of your units come out CLEAN, say so before presenting a single
result** — and say how the count moves with the window, because it is a
function of that choice (here: 0 of 5 at the pre-set ±5 years, 1 of 5 at ±4).

## 5. Match the estimator to what the data actually looks like

- **Heteroskedastic, zero-heavy count/value data** (most trade, most
  count outcomes): PPML in levels, not log-linear OLS. Silva & Tenreyro
  (2006) is the citation, not a vibe; verify it on synthetic data with a
  known injected multiplicative effect before trusting it on real data
  (`analysis/ppml.py`'s tests).
- **A unit treated more than once at different times** (a product
  restricted repeatedly, each time by a different sub-event you've
  already shown you can't separate): reframe as a cumulative-treatment,
  staggered-adoption design (treatment cohort = first restriction date)
  with a proper never-treated comparison group, and use an estimator
  robust to staggered timing (did2s, Callaway-Sant'Anna, Sun-Abraham —
  `pyfixest.did.event_study` implements several). Compare against naive
  pooled TWFE on the *same* panel to see how much staggered-adoption bias
  actually matters for your specific data, rather than asserting a
  correction is needed and stopping there.
- **A plausible confound that's *the same shape* as your treatment
  effect** (e.g. a product-specific demand shock hitting every exporter,
  not just the restricted one): don't report it as a caveat next to the
  headline number — make it a difference term. Two designs are not
  equivalent: naively adding the confound's own series as "one more
  control unit" in a fixed-effects panel does NOT net it out (it gets
  diluted across every other control unit); you have to literally
  difference the treatment series against the confound's series *first*,
  per unit-period, and estimate on the differenced series. Verify this
  distinction on synthetic data before trusting it — `analysis/
  triple_diff.py`'s tests document the naive version's failure mode
  explicitly, not just the correct version's success.
- **A control pool spanning orders of magnitude in scale**: match on
  pre-period level and trend, same broad category, never-treated only —
  and **pre-register the matching tolerances in git before running the
  match**, with the actual reasoning for each threshold, not just the
  numbers. `analysis/matching.py` + `decisions/0007-*.md`.
- **Standard errors**: classical (i.i.d.-error) SEs on panel data
  systematically understate uncertainty when a unit's residuals are
  correlated over time, which they usually are. Cluster at the level treatment
  is *assigned* (here that is the HS6 code, not the exporter-product pair:
  this project clustered at exporter-product, `analysis/clustered.py`, and
  that was too narrow, because exporter-product clusters inside one treated
  code share its common shock). With one or two treated units, no analytic
  SE is reliable; use randomization inference over never-treated units
  (`analysis/basket_attack.py`'s placebo) as the yardstick. Expect wider
  intervals; that is the fix working, not a regression.

## 6. Pre-register anything you could tune after seeing results

Destination/subgroup heterogeneity, matching thresholds, sample
restrictions — anything where a different choice would give a different
answer must be written down, with reasoning, and **committed to git
before the estimation that uses it runs**. `decisions/0007-*.md` and
`decisions/0008-*.md` plus `data/destination_groups_v1.yaml` are the
templates: the git history itself is the proof the choice wasn't tuned
after the fact. State confidence per assumption, not just per headline
number — some destination/basket-share assumptions in this project are
directly documented, most are explicitly unverified, and the README says
which is which rather than presenting a uniform-looking list.

## 7. Run the power analysis before believing a null

A null result is only informative if you could have detected the effect
you're looking for. Compute the minimum detectable effect (MDE) at a
stated power from your final specification's standard error (the
textbook two-sided formula, `analysis/power.py`'s `compute_mde` — no new
estimation needed, just arithmetic on an SE you already trust). Then
separately estimate, with stated assumptions, what share of your
aggregated outcome the specific thing you're studying could plausibly
represent, and what effect 100% of it moving would imply
(`implied_log_effect_if_fully_displaced`). If the MDE exceeds that
implied effect, your instrument cannot see this, and that is a stronger,
more useful statement than "not significant" — say so in plain words,
not just in a table.

## 8. Validate against what's already known, honestly

Hold out documented cases from independent sources (investigative
journalism, NGO reports, prior academic work) and check whether your
pipeline's *direction* and *significance* match, reported as two separate
recall numbers, not one blended score. Getting the direction right with
low power is a different, better result than getting the direction
wrong — don't let a summary statistic erase that distinction
(`validation/rediscovery.py`).

## 9. Write limitations before results, every time, in the same commit

Not as a section that exists once at the top of a README and gets stale.
Every commit that produces a new result should update the limitations
section in the same commit, before the result would otherwise stand
alone (`CLAUDE.md` rule 3). A limitations section written after the fact,
in a separate commit, is not the same discipline — it's retrospective
cleanup, and it drifts.
