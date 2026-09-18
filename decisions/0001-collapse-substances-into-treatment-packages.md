# 0001 — Collapse substances into treatment packages; the unit of treatment is (regulatory package x HS6), not substance

**Date:** 2026-09-18
**Status:** implemented (`analysis/packages.py`, commit `a8f28bd`)

## The decision

The restriction register's 9 cited events are not 9 independent natural
experiments. Three (imidacloprid, clothianidin, thiamethoxam) are
companion EU regulations adopted the same day, converging on the same
HS6 code (380810), taking effect the same day. Two more (chlorpyrifos,
chlorpyrifos-methyl) are the same pattern. `analysis/packages.py` groups
register events into `TreatmentPackage`s keyed on
`(jurisdiction, hs6, decision_date, effective_date)` — all four matching
is what "same package" means operationally here. 9 events collapse to 6
packages, 5 independently testable (the 6th, the Rotterdam Convention's
2011 endosulfan listing, was never testable — no single exporter bloc).
Every downstream count, ranking, and recall statistic uses packages, not
substances or register events.

## Alternatives considered

- **Keep substance-level events, note the correlation in prose.** Rejected:
  a prose footnote doesn't stop the count from silently tripling/doubling
  the weight of two experiments in any ranking, recall calculation, or
  "N events tested" claim. The Stage-5 rediscovery recall, for instance,
  would have counted the neonicotinoid package's single result three
  times had this not been fixed.
- **Merge on substance similarity (e.g. "all neonicotinoids") rather than
  regulatory co-incidence.** Rejected: similarity is a judgment call that
  invites exactly the kind of after-the-fact tuning Rule 2 in `CLAUDE.md`
  exists to prevent. Grouping on the objective, already-cited
  `(jurisdiction, hs6, decision_date, effective_date)` tuple requires no
  judgment and is checkable by an assertion.

## Why this one

Verified computationally, not assumed: every constituent substance within
a package produced bit-identical DiD output before collapsing (same
exporter set, same window, same treated HS6 — there was no way for them
to differ). The grouping key is also self-auditing: `packages.py` asserts
that no two *distinct* collapsed packages share both an HS6 and an
effective_date, which would indicate either a grouping bug or a
coincidental independent action needing a human, not a silent pass. That
assertion passed on the real register on the first run.

## What would make it wrong

If a future register addition has two events that share an HS6 and
effective_date but are demonstrably NOT a joint regulatory package (e.g.
two unrelated jurisdictions independently restricting the same substance
on the same calendar date by coincidence), the current grouping key would
wrongly merge them. The `_assert_no_hs6_date_collision` check would not
catch this case (it only catches events that *should* have collapsed but
didn't) — it would need a companion check for false merges if that
scenario ever occurs.

## Who or what prompted it

The user, reviewing the Step 3 causal results, noticed that 3 of 8 tested
"events" returned bit-identical point estimates and confidence intervals
and asked why — "the three neonicotinoids share an HS6, a regulatory
package and a date, and return identical estimates. Same for the two
chlorpyrifos compounds. They are not independent events."
