# 0006 — Move toward export-notification data as the primary outcome measure

**Date:** 2026-09-18
**Status:** REASONING: UNKNOWN — see below. This entry is backfilled at the
user's explicit request to record this decision, but no evidence for it
was found. Read this entry as a flag, not a record of something that
happened.

## The decision

Unclear. As of this commit, BACI bilateral trade data (import/export
values and quantities) is the sole outcome measure used everywhere in
this repo: the trade panel (Step 1), the DiD estimator (`analysis/twfe.py`,
`analysis/diD.py`), the PPML re-estimation (`analysis/ppml.py`), and the
competing-explanations checks all operate on BACI `trade_flows`. There is
no code path, data file, ingest module, or register field anywhere in the
repository that reads, references, or is structured around
export-notification data (e.g. the tonnage figures obtained via
freedom-of-information requests that Unearthed/Public Eye's "Banned in
Europe" investigation used, or the EU PIC Regulation's own export
notification system).

## Alternatives considered

Cannot be established — see below.

## Why this one

**REASONING: UNKNOWN.** I looked for evidence of this decision in:
- The full git log (3 commits as of this entry: baseline, Stage A, and
  the pre-tooling checkpoint) — no commit touches notification data.
- Every file under `src/`, `data/`, and `tests/` — none reference
  "notification," "PIC Regulation," "FOI," or a tonnage-based data
  source. The word "notification" appears exactly once in the whole
  repo, in a register citation's prose describing what Unearthed/Public
  Eye's investigation was *based on* (their FOI-obtained shipment
  notifications) — this describes the METHOD of an investigation this
  project validates against (STAGE 5 / rediscovery), not a data source
  this project itself ingests.
- The README's limitations and Stage G's own instructions, which
  reference "export-notification tonnages where available" only as an
  input to the STAGE G power/basket-share arithmetic (estimating what
  share of a treated HS6 code the restricted substance represents) — a
  one-time use for a specific calculation, not a wholesale switch of the
  project's primary outcome measure.

If this decision was made in a conversation or document outside this
repository, it has not reached the code, data, or commit history, and
this entry cannot respond to reasoning it was never given. If it *should*
be made, that is a new decision to propose via `/decide`, with its own
alternatives-considered and why-this-one sections filled in honestly —
not backfilled from a decision that, as far as this repo can tell, has
not actually occurred.

## What would make it wrong

Not applicable until the decision itself is substantiated or made.

## Who or what prompted it

The user's STEP 0 tooling request listed this among "decisions already
made" to backfill. It is recorded here as requested, flagged rather than
fabricated, per this repo's own standing rule (`CLAUDE.md` rule 8: "if
reasoning for a past decision can't be established from the repo or git
history, say UNKNOWN — do not invent a plausible-sounding rationale to
fill the gap").
