# 0003 — Use a staggered-adoption-robust estimator (Callaway-Sant'Anna / Sun-Abraham / did2s), not plain TWFE, for the repeated-treatment HS6 codes

**Date:** 2026-09-18
**Status:** proposed — reasoning established, NOT YET IMPLEMENTED as of this entry. No code exists for this in the repo. Do not cite a result for it until this status changes.

## The decision

For HS6 codes that are restricted more than once at different dates
(380810: endosulfan 2006, neonicotinoids 2018, chlorpyrifos 2020; 380830:
atrazine 2004, paraquat 2007 — see Stage A's overlap audit,
`analysis/overlap.py`, which found every one of these 5 testable packages
CONTAMINATED by a same-HS6 neighbor), plain two-way fixed effects is
known to be biased when treatment timing is staggered and effects are not
constant over time, because it can use already-treated units/periods as
the implicit control for later treatments. The plan is to re-estimate
using a design robust to this — `pyfixest.did.event_study` with
`estimator="did2s"` or `"saturated"` (Sun & Abraham-style), reframing the
unit as the HS6 code itself with treatment-cohort = its *first* recorded
restriction year, and the ~540 never-restricted HS6 codes as the
never-treated comparison group.

## Alternatives considered

- **Keep per-package plain TWFE, just note the contamination in prose.**
  This is the current (pre-repair) state and is exactly what Stage A's
  audit was built to stop doing silently — every finding prior to this
  repair should be read with that caveat, per the README's limitations
  section, but a caveat is not a fix.
- **Estimate each sub-event (endosulfan, neonicotinoids, chlorpyrifos)
  with a truncated window that stops at the next treatment date** (this
  is Stage B.4, done in addition to this, not instead of it — it answers
  a different question: "what can we say before contamination starts,"
  at a real power cost, versus this decision's question: "what is the
  correctly-identified average effect given that HS6 380810 is treated
  more than once.")

## Why this one

Reasoning is the standard staggered-DiD literature result (Goodman-Bacon
2021; Callaway & Sant'Anna 2021; Sun & Abraham 2021): TWFE's single
treatment coefficient is a variance-weighted average of all pairwise 2x2
comparisons implied by the design, including comparisons that use an
already-treated unit's post-treatment periods as a control for a
later-treated unit — a "forbidden comparison" whose bias direction is not
guaranteed to be small when treatment effects evolve over time. This is
not this project's own finding; it's cited literature the user's Stage B
instruction pointed to, and the codebase does not yet contain independent
verification of its magnitude for this specific dataset (that
verification, a Goodman-Bacon-style decomposition, is decision 0003's
companion piece and is also not yet implemented as of this entry).

## What would make it wrong

If the staggered-robust estimate and the plain per-package TWFE estimate
turn out close to each other once computed, that would be evidence the
contamination bias is small in practice here (plausible given each
"already-treated" comparison group is a single HS6 code out of ~540
controls — see the Goodman-Bacon weight argument sketched in Stage A's
discussion, not yet formalized in code). That would not make the
staggered-robust estimator the wrong CHOICE (it would still be the
correct default), but it would change how much this decision matters for
the headline numbers.

## Who or what prompted it

The user's Stage B instruction, verbatim: "Because units are treated more
than once at different times, plain TWFE is biased. Use Callaway and
Sant'Anna or Sun and Abraham, with never-treated or not-yet-treated units
as comparisons, and explicitly exclude already-treated units from the
control pool."
