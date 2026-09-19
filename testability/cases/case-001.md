# Case 001 — the European Commission's rationale for not proposing an export ban

Machine-checked version: `testability/register.yaml` (quotes verified verbatim against `testability/sources/`). Arithmetic: `testability/cases/case-001-arithmetic.json`, produced by `scripts/case001_arithmetic.py`.

> **SOURCE STATUS: this case rests on a SECONDARY TRANSCRIPTION; the primary is UNRETRIEVED.** The quoted statement is Corporate Europe Observatory's transcription (29.06.2026) of a written Commission statement to Danwatch. Retrieval of the primary was attempted on 2026-09-19 (`testability/sources/case-001-primary-source-attempts.txt`): the Danwatch article of 18 May 2026 was found but does not reproduce the statement; the Commission's own statement and the Danwatch follow-up were not found. **Limits:** the statement's date is unknown (between 13 May and 29 June 2026); its context and any omitted parts are unverified; the wording could differ from the original. Do not cite the quote as the Commission's without checking the primary.

**Verdict: UNTESTABLE WITH PUBLIC DATA** (claim 001-C1), sharpened: **testable in principle; the test the wording implies (supplier substitution) has not been attempted by anyone we could find; the tests that have been attempted, including this repository's, address a different claim** (whether EU use restrictions relocated trade), not the Commission's. One sub-claim (001-C2) is **NOT AN EMPIRICAL CLAIM** as worded. What is supported: the feasibility premise. A disclosure request is below.

## Limits stated first

- The quoted text is a **secondary transcription** (Corporate Europe Observatory, 29.06.2026, of a written Commission statement to Danwatch). The Danwatch original and the Commission's own document were not retrieved. The statement's own date is not given: it opens "As already answered to you on 13 May", so it falls between 13 May 2026 and 29 June 2026.
- The **brief paraphrased** the rationale as a ban that "might shift production outside the EU." The verbatim claim differs: importing countries "may … buy the same or worse chemical pesticides from companies outside of the EU." That is supplier substitution, not production relocation, and the audit is of the verbatim claim.
- **Notified tonnage** (81,600 t in 2018; 122,000 t in 2024) is intended exports of *mixtures*, obtained by freedom-of-information request (Unearthed, 22.09.2025). It is not recorded shipments and not tonnes of active substance. It is compared below with customs-recorded tonnes, a different instrument; the ratio is an order-of-magnitude anchor.
- National export-ban dates (France January 2022, Belgium Royal Decree June 2023 with effect reported as May 2025, Switzerland 2021) come from search summaries and are not checked against legal texts.
- No EU-wide unilateral export ban has been in force. This project studied domestic *use* restrictions, under which EU exports continued; it never observed the counterfactual the claim is about.

## 1. Claim extraction

Source: Corporate Europe Observatory, "European Commission backtracks on promise to end EU exports of banned and dangerous pesticides", 29.06.2026, "Full written statement by the EC to Danwatch" (speaker: an unnamed Commission spokesperson).

> "However, a unilateral production and export ban in the EU would not guarantee an improvement in health and environmental protection in affected countries, as it may push these countries to buy the same or worse chemical pesticides from companies outside of the EU. Consequently, this would only penalise the EU chemical industry that is already suffering in the current economic climate."

| Id | Text (verbatim fragment) | Kind |
|---|---|---|
| 001-C1 | "it may push these countries to buy the same or worse chemical pesticides from companies outside of the EU" | prediction about a counterfactual policy |
| 001-C2 | "would not guarantee an improvement in health and environmental protection in affected countries" | empirical in form, hedged to unfalsifiable |
| (C3, dependent) | "Consequently, this would only penalise the EU chemical industry" | incidence claim that follows from C1 only if substitution is near-total; its premise about the industry is candidate 003 |

The rest of the statement is commitment and policy choice ("The Commission is committed to addressing this important issue"; "Ensuring a high level of protection … is paramount"): value judgements or plans, not audited.

## 2. Test specification (C1)

Unit: importing country × banned active substance × year. Outcome: tonnes imported from suppliers in the banning jurisdiction versus elsewhere. Comparison: the same destinations' imports of substances not subject to a ban, and exporters not subject to it. Natural experiments: the national bans above. Quantity of interest: leakage L, the increase in non-banning-supplier tonnage over the decrease in banning-supplier tonnage, plus a hazard comparison for "same or worse." **The threshold for what matters is a value judgement of the decision-maker; as an illustration only:** L near 1 supports the claim in tonnage terms, L below about 0.5 means a ban removes at least half of the exports.

C2 as worded is true of almost any policy and no observation could contradict it, so it stops at this step.

## 3. Evidence inventory

- **Public:** CEPII BACI bilateral trade at HS6 (this repository, 1995-2024). Heading 3808 has five HS92 subheadings; a banned substance is never observed separately.
- **Public, EU side only, notified not shipped:** Public Eye published the full dataset of its 2018 investigation (substance, exporting EU country, destination, notified quantity, year; the page states the full dataset is published; column names not verified here); Unearthed publish 2024 country aggregates. Correction 2026-09-19 (`decisions/0006-*.md`): an earlier version of this section said these notifications were not public as a dataset, which was wrong. They are still tonnes of mixtures, intended exports, and say nothing about which suppliers importing countries then buy from.
- **Unverified lead (not checked):** Eurostat Comext 8-digit CN lines split heading 3808 by chemical family.
- **Missing:** realised exports by substance and destination; importers' purchases by supplier origin; hazard classification of substitutes.
- **Checkable now, and supports the Commission:** non-EU suppliers exist at scale. Non-EU exporters ship 4.7× (2018) and 7.2× (2024) the EU's customs-recorded tonnage of heading 3808 into non-EU destinations. That supports the *feasibility* of substitution. It says nothing about how much would occur or how hazardous it would be.

## 4. Power verdict

| | 2018 | 2024 |
|---|---|---|
| Notified banned-pesticide tonnage | 81,600 t | 122,000 t |
| EU customs-recorded exports of heading 3808 to non-EU destinations | 720,665 t | 686,266 t |
| Notified as a share of customs tonnes | 11.3% | 17.8% |
| Log-point change in the heading if all of it vanished | −0.120 | −0.196 |

A design like this repository's, applied to the EU-minus-rest-of-world contrast for these codes, has a randomization-based standard error of 0.33 (chapter 38 placebo) to 0.54 (all codes) log points (`data/attack/basket_attack_results.json`), so an 80%-power detection threshold of 0.93 to 1.51 log points, or 60% to 78% of the basket vanishing. **The effect that would matter is about 5 to 13 times smaller than the threshold: even 100% elimination of the banned-substance trade would not be visible in public HS6 data.** The same arithmetic is why this project's own displacement test was null (`decisions/0009-*.md`, `PAPER.md` section 5).

## 5. Disclosure gap

Holder: ECHA and Member State designated authorities (PIC export notifications); customs authorities of France, Belgium, Switzerland; Eurostat (Comext, CN8). Fields: exporting country; importing country; active substance (CAS number) and mixture concentration; tonnes notified; tonnes actually exported (customs export declaration); month; flag distinguishing notified from shipped; for importing countries, tonnes imported by active substance and supplier country. Granularity: active substance × exporting country × importing country × month. Period: 2015 to present, covering the Swiss, French and Belgian measures. The sibling repository's FOI pack is described as doing this for one case; it was not inspected here.

## 6. Verdict

**UNTESTABLE WITH PUBLIC DATA (HS6 trade), sharpened.** (1) The claim is testable in principle. (2) The test its wording implies, that importing countries would buy the same or worse pesticides from non-EU companies, needs importer-side purchases by substance and supplier origin; we know of no one who has run it (our search was limited). (3) Tests that have been attempted, including this repository's, address a different claim: whether EU use restrictions moved trade in the restricted product to unrestricted destinations. They neither support nor refute the Commission. (4) The size of the effect that would matter is 5 to 13 times below what public HS6 data can detect; that range comes from basket-level placebo SEs and was not changed by the Stage G recomputation. Nothing in this repository supports or contradicts the *size* of substitution; the *feasibility* premise is supported. A reader should not take this as the Commission being wrong, or right. The Commission has asserted, as the reason for not acting, something that neither it nor anyone outside it can currently check.
