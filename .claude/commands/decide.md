---
description: Record a methodological decision through the standing template
---

Walk the user through recording a methodological decision in `decisions/`,
using `decisions/TEMPLATE.md` as the structure. Do this conversationally,
one section at a time — don't dump the whole template as a form.

Steps:

1. Find the next decision number: list `decisions/*.md` (excluding
   TEMPLATE.md), take the highest `NNNN-*` prefix, add one, zero-pad to 4
   digits.
2. Ask the user for a one-sentence statement of the decision if not
   already given in `$ARGUMENTS`. Propose a short kebab-case slug from it
   and confirm before creating the file.
3. Ask for (or infer from the conversation and confirm): alternatives
   considered, why this one, what would make it wrong, who or what
   prompted it. If the user gives a rushed or vague answer to "why this
   one" or "what would make it wrong," push back once — these two
   sections are the point of the exercise; a decision log entry that
   just restates the decision in the "why" section is not useful. Don't
   accept "best practice" as a reason without asking what makes it apply
   here specifically.
4. If, at any point, you cannot establish real reasoning for part of the
   decision (e.g. you're backfilling something from before this
   conversation and the evidence isn't in the repo), write that section
   as `REASONING: UNKNOWN` with what you looked for and didn't find — per
   `CLAUDE.md` rule 8. Do not paper over a gap with a plausible-sounding
   guess.
5. Write `decisions/NNNN-slug.md` following TEMPLATE.md's structure
   exactly (same headings, same order).
6. Show the user the finished file and ask if it's ready to commit. If
   yes, stage and commit it with a message naming the decision — do not
   bundle it into an unrelated commit.

This command does not touch analysis code, the register, or results. It
only writes to `decisions/`.
