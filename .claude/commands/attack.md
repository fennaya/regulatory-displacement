---
description: Build the strongest case AGAINST a claim, using this repo's actual data and code
argument-hint: <claim>
---

Attack the claim in `$ARGUMENTS` (ask if not given). This is adversarial
by design — no hedging, no balanced perspective, no compliments on the
existing work. The job is to find the specification that overturns the
claim, not to summarize both sides.

1. State the claim precisely, and name exactly which code/data in this
   repo it rests on (which package(s), which estimator, which window).
2. Find the confound not controlled for. Check, in order, the things this
   project's own `README.md` limitations section and `decisions/*.md`
   already admit are weak points (contamination — `analysis/overlap.py`;
   HS6 coarseness; rest-of-world demand growth; control-pool
   heterogeneity; classical vs. clustered SEs) — an attack that ignores
   the project's own documented weaknesses and invents a new one instead
   is not trying hard enough.
3. Find the sample restriction doing the work. Actually re-run the
   relevant estimation with a defensible alternative sample/window/control
   choice (not a hypothetical one — run real code) and report what
   changes. If you can't run it, say exactly what you'd run and why you
   expect it would change the result, and flag that this is unverified.
4. Go for the joint test, not just individual coefficients: is there a
   single alternative specification, using only choices as defensible as
   the ones already made, that flips the sign or erases the significance
   of the claim?
5. Deliver a verdict: SURVIVES, WEAKENED, or FALLS — with the strongest
   attack that was actually tried, not the strongest attack imaginable.
   If the claim survives, say so plainly and say specifically what made
   it survive (e.g. "the effect is robust to X because Y," not "it seems
   okay").

Do not modify analysis code, the register, the dashboard, or the forward
watchlist as a side effect of this command — if testing an alternative
specification requires new code, write it as a new, separate script or
module, not an edit to the existing estimator, unless the user
subsequently asks you to keep the change.
