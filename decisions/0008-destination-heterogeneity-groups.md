# 0008 — Pre-registered high/low pesticide-exposure destination groups (Stage F)

**Date:** 2026-09-18
**Status:** implemented and estimated. **Result contradicts the concentration hypothesis this stage was built to test.** Of 5 testable packages, only endosulfan shows high-exposure > low-exposure as predicted (+1.034 vs +0.377); neonicotinoids and paraquat show essentially no difference between groups; chlorpyrifos (+0.184 high vs +0.397 low) and atrazine (+0.114 high vs +0.764 low) show the OPPOSITE pattern, sharply for atrazine. Confidence intervals are extremely wide for every group (restricting to 7-8 destinations sharply cuts the data each estimate rests on). This is reported as a genuine, mixed/negative finding per the "what would make it wrong" section below — not reconciled or explained away.

## The decision

Two destination groups, fixed before estimating anything with them:
- **High-exposure** (8 countries): Brazil, Ukraine, South Africa, Viet Nam,
  Thailand, India, Indonesia, Pakistan — large agricultural economies
  where none of the register's 8 substances face an independent import
  restriction.
- **Low-exposure** (7 countries): Switzerland, Norway, Japan, Korea,
  Canada, Australia, New Zealand — high-income OECD members whose own
  pesticide review regimes are broadly comparable in stringency to the
  EU's.

Confidence is stated per country in the data file, not uniformly claimed:
3 of the 8 high-exposure countries (Brazil, Ukraine, South Africa) are
directly documented by the Unearthed/Public Eye "Banned in Europe"
investigation as actual recipients of EU-banned pesticides; the other 5
are included on weaker, unverified-per-substance reasoning, and the data
file says so.

## Alternatives considered

- **Use every non-EU country pooled (current default in `analysis/diD.py`
  and everywhere else in this repo).** This is what every prior stage
  did; Stage F exists specifically because pooling ~150-200 destinations
  of wildly different exposure plausibly dilutes a signal that should
  concentrate in a few, per the user's framing.
- **Rank destinations by a continuous exposure score (e.g. a pesticide-
  regulation-stringency index) instead of a binary high/low split.**
  Rejected for this stage: no such index was found or verified in this
  session (a `/priorwork`-style search for one wasn't run), and
  fabricating a continuous score's weights would be exactly the kind of
  unverifiable precision this project's register avoids elsewhere (see
  the mapping confidence scores' own honesty about uncertainty). A binary
  split with per-country reasoning and stated confidence is more
  auditable than an unverified composite score would be.
- **Base the high-exposure group solely on the 3 directly-documented
  countries, omitting the 5 weaker-confidence ones.** Considered, but
  3 destinations plausibly has too little combined trade volume to
  support meaningful residual variance for standard errors in a
  fixed-effects design; the 5 additional countries are included with
  their weaker basis stated explicitly rather than silently omitted or
  silently equated in confidence to the documented three.

## What would make it wrong

If the low-exposure group (OECD members) shows an effect similar in size
to the high-exposure group, that would undercut the "concentration"
hypothesis motivating this stage — either displacement isn't
destination-selective in the way theorized, or the grouping itself
doesn't capture the real exposure gradient (e.g. if Australia, a large
agricultural economy despite strict regulation, behaves more like the
high-exposure group for reasons unrelated to regulatory stringency, that
would be a specific, checkable confound in this group's own construction
— it was included partly as an agricultural-scale contrast for exactly
this reason, see the data file).

## Who or what prompted it

The user's Stage F instruction, verbatim: "Pooling all destinations
dilutes a signal that should concentrate in a few. Pre-specify, in
writing, before running: a high-exposure group ... and a low-exposure
group ... Commit the list to git BEFORE estimating so it cannot be tuned
afterwards."

## Amendment, 2026-09-19 (the entry above is left as written; this note corrects its wording)

**Wording corrected:** the Status line says the result "contradicts the concentration hypothesis" and that two packages show "the OPPOSITE pattern, sharply for atrazine." The accurate statement is: **the hypothesis is not supported, and it is not refuted.** Chlorpyrifos and atrazine have the opposite *ordering of point estimates* (atrazine +0.114 high-exposure vs +0.764 low-exposure), but every group interval spans about ±2 to ±3 log points, so none of the between-group differences is distinguishable from zero.

**Why it changed:** the hostile README review (trade-economist objection 3) pointed out that reading a sign into differences of noisy point estimates overstates what was found; confirmed against the group intervals.

**Where:** `reviews/2026-09-19-readme-review.md` (trade-economist objection 3). The README and `PAPER.md` carry the corrected wording.
