---
description: Assume this project produced nothing anyone used in 12 months — say why, ranked
---

Assume it is twelve months from now and this project produced nothing
anyone used. Not "nothing was finished" — nothing anyone actually used,
which is a harder and more specific failure than an incomplete repo.

Write the five most likely reasons, ranked by probability given the
ACTUAL current state of this repo (read `README.md`, `falsification.md`,
`decisions/*.md`, and the git log before writing this — do not write a
generic list that could apply to any project). For each reason:

1. **The failure**, stated as a specific, concrete scenario, not a
   category ("no one reads the dashboard because the scorecard is empty
   for another 3 months and there's nothing to check in the meantime" —
   not "lack of engagement").
2. **The earliest warning sign** — something observable well before month
   12 that, if seen, should trigger a correction. Be specific about what
   it would look like in THIS repo (a particular metric, a particular
   file going stale, a particular commit pattern).
3. **What could be done this month** to reduce this specific risk — one
   concrete action, not "communicate better" or "prioritize this."

Rank by actual probability given this project's current state, not by
which is most interesting to write about — if the most boring failure
mode (e.g. "the two watchlist forecasts resolve and nobody checks the
scorecard") is also the most likely, rank it first and say so.

Do not soften any of the five into something encouraging. This command's
entire value is in being the pessimistic read no one volunteers.

Do not modify any file. This command produces analysis, not action.
