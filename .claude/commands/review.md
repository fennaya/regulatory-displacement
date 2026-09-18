---
description: Three hostile referees review the current README and results — no softening
---

Read the current `README.md` and the latest results (dashboard data,
`falsification.md`, `decisions/*.md`) and simulate three referees. Each
must give their three strongest objections and a verdict. Do not let any
referee soften into agreement with the others, and do not let your own
narration soften what they say — report their objections as written, even
the ones that land on your own prior work in this session.

**(a) An applied trade economist, who cares about identification.**
Expected angles (use these as a floor, not a ceiling — find the ones this
project's specifics actually invite): is the DiD design's parallel-trends
assumption remotely plausible given documented contamination
(`analysis/overlap.py`)? Is PPML actually correctly specified (right FE
structure, right clustering)? Is the control pool comparable or just
convenient? Is "displacement" identified or just "the basket moved"?

**(b) A chemicals-policy specialist who knows the PIC regime and will
catch any misstatement of the law.** Check every register citation and
every claim about what a regulation actually does — non-renewal vs. ban
vs. withdrawal are legally different things (see `register/schema.py`'s
`RestrictionType`), and this referee should be checking whether the
project respects that distinction throughout, not just in the schema. Is
the Rotterdam Convention PIC mechanism (prior informed CONSENT, not an
export ban) being correctly characterized everywhere it's mentioned, not
just in the one place that spells it out?

**(c) A journalist who will ask whether the headline is actually
supported by the table underneath it.** This referee doesn't care about
econometric technique — they care whether "displacement" in a headline or
dashboard card would survive them reading the actual confidence interval,
the actual N of clean packages, and the actual power analysis out loud to
their editor. Flag any place language is stronger than the numbers
support.

For each referee: three objections (specific, citing a file/line/number
where possible, not generic), then a verdict — **accept**, **major
revision**, or **reject**. Then one combined summary: what would have to
change for all three to move to accept.

Do not modify any file as part of this command unless the user asks you
to act on a specific finding afterward.
