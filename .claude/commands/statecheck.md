---
description: Established / provisional / assumed-unverified / blocked-and-on-whom — the position, not a status update
---

Read the repo fresh — `README.md`, `falsification.md`, every file in
`decisions/`, the git log, the test suite results (`uv run pytest`), and
the actual contents of `data/register/`, `data/watchlist/forecasts.jsonl`
— and report the current position in exactly four categories. No
progress framing ("great progress on X"), no encouragement, no "next
steps" section unless a category explicitly needs a name for who's
blocking.

**Established.** What is actually verified: code that runs, tests that
pass with a known-answer check (not just "doesn't crash"), a finding with
a stated confidence interval and the caveats that apply to it already
attached. Cite the file/test/commit for each item — "established" without
a pointer to why isn't established, it's asserted.

**Provisional.** What has a result but a known, named reason to doubt it
— e.g. anything computed before a decision in `decisions/*.md` with
status "proposed" (not yet implemented) is provisional by definition;
anything flagged CONTAMINATED in the overlap audit is provisional. Say
what would need to happen to promote each item to Established.

**Assumed but unverified.** Choices made without evidence checked in this
repo — pooling the exporter FE dimension, the EU-membership-by-date
table, the mapping confidence scores, anything a `decisions/*.md` entry
marks REASONING: UNKNOWN. Distinguish this from Provisional: Provisional
has a result that might be wrong; Assumed-unverified has no result
checking it at all yet.

**Blocked, and on whom.** What cannot proceed without a decision, data,
or action from a specific person (usually the user) — e.g. Stage F's
destination-heterogeneity groups need to be written and committed BEFORE
estimation (`CLAUDE.md` rule 2) and that hasn't happened; export-
notification data's status is genuinely unclear (`decisions/0006-*.md`)
and needs the user to say what was meant. Name the blocker specifically,
not "needs more work."

End with one line: how many of the project's live claims
(`falsification.md`) currently have a status better than "untested."
That number is the actual state of the project; everything else is
detail.
