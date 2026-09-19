# Testability audit: a protocol for asking whether an institution's justification can be checked at all

Institutions justify decisions with empirical claims constantly: *it would just move elsewhere; it would harm competitiveness; it would be circumvented; the data does not support intervention.* Almost nobody asks whether such a claim is checkable with the evidence that exists. This protocol asks that, and only that. It does not decide whether the institution is right.

**It is a method, not advocacy.** The protocol must be able to return "the institution's claim is probably correct," and the code enforces that it can (`testability/protocol.py`: a tested claim carries an evidence direction, one value of which is `claim probably correct`; `tests/test_testability.py::test_protocol_can_vindicate_an_institution`). A protocol that could only ever find fault would be advocacy with a checklist. Two more things guard against that: a claim that is not empirical is never audited as if it were (so value judgements are not "refuted"), and an "untestable" verdict is never a dead end because it must name the disclosure that would make the claim testable.

## The six steps

**1. Claim extraction.** Quote the justification verbatim, with speaker, source, and the date of the statement. Never paraphrase an official rationale; if you must summarise, say so and keep the quote beside it. Record when the source's own date differs from the page's date, and whether you read the original or a transcription. Then classify each sentence: *empirical* (about how the world is or was), *prediction* (empirical in form but about a counterfactual or future), *value judgement* (about what matters). Only the first two proceed. Split compound sentences: a hedge ("would not guarantee") and a magnitude ("would only penalise") are different claims with different testability. Code check: the quote must appear in a stored copy of the source (`verify_quote_in_source`).

**2. Test specification.** State what observation would confirm or refute it: the unit, the outcome, the comparison, and the effect size that would matter for the decision. The decision-relevant effect size is a value judgement of the decision-maker; if you propose thresholds, label them assumptions. If no observation could contradict the claim as worded, say so here and stop: verdict `NOT AN EMPIRICAL CLAIM`, and continue the audit on the testable claim inside it.

**3. Evidence inventory.** Name the data that exists at that unit and granularity, and who holds it; or name what is missing. Distinguish public datasets, datasets that exist but are not public, and leads you have not verified (mark those unverified; do not promote them). Separate instruments that sound alike (a notified quantity is not a recorded shipment).

**4. Power verdict.** If data at that granularity exists, could it detect an effect of the size that matters? Compute the minimum detectable effect from the estimator's real uncertainty (prefer randomization inference over analytic standard errors when few units are treated), then compare it to the effect the claim implies. Two quantities decide it: `elimination_effect(share)` (what the outcome does if the thing studied disappears entirely) and `share_needed_for_detection(se)` (how large a share of the outcome would have to move to be seen). If even the whole thing moving is below the threshold, the data cannot test the claim.

**5. Disclosure gap.** If the claim is untestable with public data, state the specific disclosure that would make it testable: holder, fields, granularity, period. It is a concrete data request, not a complaint.

**6. Verdict.** Exactly one of:
- **TESTABLE AND TESTED**, with an evidence direction: `claim probably correct`, `claim probably wrong`, or `inconclusive`.
- **TESTABLE BUT UNTESTED**: the data exists and can detect the effect; nobody has run the test.
- **UNTESTABLE WITH PUBLIC DATA**: cannot be tested at the granularity available; a disclosure request is attached.
- **NOT AN EMPIRICAL CLAIM**: a value judgement, or so hedged that no observation could contradict it.

## Rules that keep the audit honest

1. No statistic is produced by a model. Arithmetic is deterministic code with tests.
2. Every official statement is quoted verbatim with source and date. A gap in what you retrieved (the original not read, a page that did not load) is recorded as a gap.
3. A candidate claim is unworked until it is worked; do not put a verdict on a claim you have not audited.
4. Report what supports the institution as plainly as what does not. Case 001 records that the feasibility premise of the Commission's claim (non-EU suppliers exist at scale) is supported by the data, alongside the verdict that its magnitude cannot be tested.
5. Do not treat "untestable with public data" as "false", or as "true." It means the institution has asserted something that neither it nor anyone else can currently check from outside, and that a specific disclosure would change that.

## Applying it to a different institution and domain

1. Pick a justification the institution has published, with a date. Store the source text (`testability/sources/`) with retrieval metadata and what you did not verify.
2. Write the claims in `testability/register.yaml` (validated by the tests).
3. For step 4 you need: a measurable outcome, its variance in your data, and a defensible share of that outcome the thing studied could plausibly be. If your domain has few treated units, use placebo/randomization inference as the standard error. This repository's `analysis/basket_attack.py` shows one.
4. Write the disclosure request as fields a records officer could act on.
5. Publish the audit whichever verdict it returns.

## What this protocol does not do

It does not establish that a policy is good or bad, it does not weigh the institution's values, and it does not replace the empirical work when the claim is testable. It tells you whether that work is possible with what is public, and what to ask for if not.
