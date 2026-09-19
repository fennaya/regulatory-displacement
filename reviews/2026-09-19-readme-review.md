# /review of README.md — 2026-09-19

Three hostile referees on the README as it stood at commit `7b3a516`.
Objections that could be checked against code or data were checked before
being attributed; the checks are noted.

## (a) Applied trade economist — identification

1. **Treatment varies at the HS6 level; the clustered SEs cluster below it.**
   Stage E clusters at exporter-product, but every EU exporter of a treated
   code shares the same product-level shock, so those clusters are not
   independent. With one treated code per package no analytic SE is reliable.
   *Checked:* the placebo in `decisions/0009-*.md` gives a placebo SD of ~1.4
   against a did2s SE of 0.145. The README's Stage E row presented the
   clustered SE as the fix. **Correct; README and METHODS.md amended.**
2. **"0 of 5 CLEAN" is a function of a window you chose.** *Checked:*
   rerunning the overlap audit at ±4, ±3, ±2: EU endosulfan is CLEAN at ±4 or
   narrower; the other four are contaminated at every window. The headline
   "0 clean" was stated without the qualifier. **Correct; amended.**
3. **Stage F compares noisy point estimates across groups.** Every group CI
   spans about ±2 to ±3 log points; "opposite pattern, sharply for atrazine"
   reads a sign into differences of noise. **Correct; reworded to "not
   supported, not refuted."**
4. Directional recall of 100% (Step 5) cannot discriminate when all five
   original estimates were positive. **Correct; added.**

Verdict: **major revision.** Identification of any substance-level effect is
not achieved; the README now says so, but the estimator table still leads
with specifications whose SEs cannot be trusted.

## (b) Chemicals-policy specialist — misstatements of the law

1. **The 2018 neonicotinoid regulations are not non-renewals.** Implementing
   Regulations (EU) 2018/783, /784, /785 amend the conditions of approval
   (permanent greenhouses only); the register labelled all three
   `non-renewal`, and the README described the register as "EU
   non-renewals/withdrawals." *Checked against the register's own cited
   title.* **Correct; register type changed to `severe_restriction` for the
   three records, README reworded, test added.**
2. **Atrazine and endosulfan are Directive 91/414/EEC non-inclusion
   decisions**, which the enum labels `non-renewal`. Not identical legal
   objects. The enum has no non-inclusion value. **Left as is; README now says
   "non-renewal and non-inclusion decisions."** Adding an enum value would
   change the schema for a labelling refinement that no estimate depends on.
3. **A Rotterdam PIC listing is a consent procedure, not a restriction of
   the substance's trade.** The register notes already say so; the README
   summary did not. **Amended.**
4. "Heading 3808 has exactly five subheadings" is true of the HS92
   nomenclature BACI uses, not of later HS revisions. **Qualified.**

Verdict: **major revision** until the register labels were fixed; **accept on
legal characterisation** after the changes above, with item 2 disclosed.

## (c) Journalist — is the headline supported by the table

1. **"60-93% of every package's estimate is explained by rest-of-world
   growth"** treats noisy, non-significant point estimates as if they were
   precisely measured quantities that were then explained away. **Correct;
   reworded to say the point estimates shrink and the originals were not
   significant.**
2. **"Flips sign (+0.407 to -0.017)"** for atrazine: both intervals span zero.
   A flip of an unknown sign is not a finding. **Correct; reworded.**
3. **"This is arithmetic, not a hedge"** (Stage G) while the effect-size half
   rests on basket shares that are mostly unverified. **Correct; now
   "conditional on the stated shares."**
4. "59-61% genuine zero flows": BACI records only positive flows, so an empty
   cell may be an unreported flow. **Correct; reworded.**

Verdict: **major revision**; after the changes, **accept** for the top-line
numbers that are stated with their conditions.

## What was deliberately NOT changed

- **The Stage G conclusion itself** (4 of 5 packages not detectable): the
  referees object to its certainty, not to the arithmetic, and the amended
  wording carries the condition. Softening it further would be hedging the
  README does not need: the assumptions are already listed with confidence.
- **The "6 treatment packages" unit.** No referee produced a case that
  companion regulations are independent experiments.
- **The strength of the attack result on +0.664** (`decisions/0009-*.md`).
- **The `non-renewal` label on atrazine/endosulfan** (see (b)2).
- **The dashboard's Stage 3 event-time numbers**, kept for continuity and
  already labelled as unrepaired.
- Nothing was added to the README that is not a correction of a checked
  error or overstatement.
