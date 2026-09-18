# 0004 — Treat rest-of-world exporter growth as the counterfactual (triple-difference control), not a rival explanation to be reported alongside the estimate

**Date:** 2026-09-18
**Status:** proposed — reasoning established, NOT YET IMPLEMENTED as of this entry. `analysis/competing_explanations.py`'s `check_destination_demand_growth` currently reports rest-of-world growth as a caveat alongside the DiD estimate; it does not yet subtract it out as a triple-difference term. No code exists for the restructured design in the repo.

## The decision

Restructure the estimate as a triple difference:
`(EU exports to unrestricted destinations, after vs before)` minus
`(non-EU exports of the same product to the same destinations, same
window)` minus `(the same contrast for never-restricted control
products)`. Currently, Stage 4's `check_destination_demand_growth`
computes rest-of-world growth (26-50% across every tested package) and
reports it as a competing explanation *next to* the DiD point estimate,
implicitly treating it as a rival story that might explain the result
away rather than as the counterfactual the DiD design should be
differencing against directly.

## Alternatives considered

- **Keep reporting it as a caveat (current state).** This is honest as
  far as it goes — Step 4's whole point was "report competing
  explanations alongside every finding, not used to suppress it" — but
  the user's framing is sharper: if rest-of-world growth is genuinely the
  counterfactual (what would have happened to EU exports absent the
  restriction, proxied by what happened to everyone else's exports of the
  same product into the same destinations), then it belongs INSIDE the
  estimator as a third difference, not beside it as a footnote. A caveat
  that isn't subtracted out is not currently affecting the reported point
  estimate at all.

## Why this one

Reasoning is the user's, not independently re-derived or verified against
literature in this session: rest-of-world exporters of the *same* HS6
code into the *same* destinations are a more specific counterfactual than
"never-restricted control products from the same exporter," because they
control for product-specific global demand shocks that a same-exporter,
different-product control cannot. Whether this triple-difference
identification is actually cleaner than the current double-difference
design (it introduces its own assumption — that non-EU exporters of the
same product are not themselves substituting into the vacated EU
export share, which would bias the triple-difference in the opposite
direction) has not yet been checked in this repo.

## What would make it wrong

If non-EU exporters of the treated HS6 code are themselves gaining share
specifically because the EU exporter is retreating from ANY market
(not just the destinations losing the restriction), the triple-difference
control is contaminated by the very displacement being measured, biasing
the estimate toward zero. This is checkable once implemented: compare
non-EU exporters' growth into destinations that DID have an equivalent
restriction (where no EU displacement effect should exist) against their
growth into destinations that didn't — if the two differ, the "control"
is not clean.

## Who or what prompted it

The user's Stage C instruction, verbatim: "Rest-of-world exporters grew
26-50% into the same destinations over the same windows. The current
design treats that as a rival explanation. It is the counterfactual."
