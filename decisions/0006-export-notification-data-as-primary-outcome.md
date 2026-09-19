# 0006 — Move toward export-notification data as the primary outcome measure

**Date:** 2026-09-18
**Status:** CONSIDERED AND NOT ADOPTED. Resolved 2026-09-19; see the Resolution section at the bottom. The paragraphs between here and the Resolution record what the repository could establish on 2026-09-18, when the reasoning was unknown, and are kept as history.

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

## Resolution, 2026-09-19

**The decision:** to move to export-notification data as the project's primary outcome measure was **considered and not adopted**. BACI bilateral trade remains the outcome throughout.

**Source of this resolution:** the project owner, on 2026-09-19. No record of the original proposal exists in the repository or its git history, which is why the entry read REASONING: UNKNOWN on 2026-09-18. This entry records what the owner supplied and what this session could and could not check; it does not reconstruct the original discussion.

**Reason it was proposed:** on the premise that no structured dataset of export notifications existed.

**Correction of that premise:** the premise was wrong. Per the owner, Public Eye published the full dataset for its 2018 investigation (substance, exporting EU country, destination country, notified quantity, year), and Unearthed publish country-level aggregates for 2024.

**What this session verified (2026-09-19):**
- Verified: the Public Eye page https://www.publiceye.ch/en/topics/pesticides/banned-in-europe states "We are publishing the full dataset used for this investigation" and links a spreadsheet, `EU-banned-pesticide-exports_dataset.xlsx`, covering 2018 EU export notifications.
- **Not verified:** the spreadsheet's column names (the page does not list them, and the file was not downloaded), so the field list above is the owner's, not confirmed here.
- **Not verified:** any Unearthed 2024 country-level aggregate. The Unearthed article retrieved (22.09.2025) gives totals (122,000 tonnes notified for 2024, about 81,600 for 2018) and names its source as notifications obtained by freedom-of-information request; it was not checked for a published country table.

**Why not adopted, given that the data exists:** stated by the owner as the premise being wrong, not as a judgement that notification data is worse. Two limits remain regardless: notifications are intended exports of mixtures, not recorded shipments, and they cover only the EU side (no importer-side origin mix), so they cannot on their own test either the displacement claim or the supplier-substitution claim (see `PAPER.md` and `testability/cases/case-001.md`).

**Consequence for other documents:** `testability/register.yaml` and `case-001.md` said EU notification records "exist but are not public as a dataset." For 2018 that was wrong; corrected in the same commit as this resolution.

**What would make this resolution wrong:** if the 2018 dataset turns out not to contain destination country or exporting country at the record level, or if a fuller notification dataset exists that would make it a viable primary outcome.
