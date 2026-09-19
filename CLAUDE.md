# Standing rules — Displacement Observatory

These apply to every session working in this repo, without needing to be
restated. They exist because discipline leaks between sessions if it only
lives in one conversation's memory.

1. **No statistic is ever produced by a language model.** All estimation
   is tested Python. If you (the assistant) catch yourself writing a
   number in prose that did not come from code you ran in this session,
   stop and go run the code.
2. **Any choice that could be tuned after seeing results — control pools,
   destination groups, windows, thresholds — must be committed to git
   BEFORE estimating, with the reasoning in the commit message.** If you
   estimate first and commit the "pre-registered" choice afterward, the
   result is worthless; redo it in the right order.
3. **Limitations are written in the same commit as the result that
   created them, and appear BEFORE results in every document.** Never
   append a limitation after the fact in a later commit — that is how
   caveats quietly disappear from the record.
4. **Notified quantity is never called "quantity."** Export-notification
   tonnages (e.g. from FOI-obtained PIC regulation notifications) and
   customs-recorded trade quantities are different instruments with
   different biases; conflating their names conflates the data.
5. **Event counts are reported as treatment packages, never as
   substances.** See `analysis/packages.py` and `decisions/0001-*.md` for
   why: companion regulations sharing an HS6/date/package are one
   experiment, not one per substance named in it.
6. **The forward watchlist is append-only.** Never edit or delete a
   timestamped forecast in `data/watchlist/forecasts.jsonl`, including a
   wrong one — *especially* a wrong one. The enforcement mechanism is in
   `watchlist/forecasts.py` (`append_forecast` refuses duplicate IDs and
   there is no update/delete function); do not work around it.
7. **Before claiming anything is novel, run `/priorwork`.** Default to
   assuming someone has already done it.
8. **State when you are uncertain.** A flagged unknown is useful to the
   next person; a confident guess is damage. If reasoning for a past
   decision can't be established from the repo or git history, say
   `UNKNOWN` — do not invent a plausible-sounding rationale to fill the
   gap. This applies to you (the assistant) as much as to any human
   contributor.

## Where things live

- `analysis/` — estimation code (twfe.py, ppml.py, packages.py, overlap.py,
  diD.py, competing_explanations.py). No statistic outside this directory
  (and its tests) should be treated as authoritative.
- `register/`, `data/register/` — the restriction register and its schema.
  Citations are load-bearing; an uncited field is dropped, not guessed.
- `testability/` — the audit protocol and its register. Any official
  justification quoted there must be verbatim, sourced and dated, and is
  checked against the stored source text by `tests/test_testability.py`.
  Candidates stay unworked until audited.
- `decisions/` — one file per methodological decision. Use `/decide` to
  add one.
- `falsification.md` — what would refute each live claim. Use `/falsify`
  to add or sharpen an entry. A claim in the README with no entry here
  fails the test suite (`tests/test_falsification_coverage.py`) — this is
  mechanical, not a reminder.
- `.claude/commands/` — `/attack`, `/review`, `/priorwork`, `/premortem`,
  `/statecheck`, `/decide`, `/falsify`.

## Slash commands, one line each

- `/decide` — record a methodological decision through the template.
- `/falsify <claim>` — propose what would refute a claim; refuses vague
  criteria.
- `/attack <claim>` — build the strongest case against a claim using this
  repo's own data and code. No hedging.
- `/review` — three hostile referees (trade economist, chemicals-policy
  specialist, journalist) review the README and results. No softening.
- `/priorwork <claim>` — search for existing work before claiming novelty.
- `/premortem` — assume the project produced nothing useful in 12 months;
  say why, ranked, with earliest warning signs.
- `/statecheck` — established / provisional / assumed-unverified /
  blocked-and-on-whom. Position, not a status update.
