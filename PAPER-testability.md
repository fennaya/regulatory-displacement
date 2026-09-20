# Can an institution's empirical justification be tested? A protocol and one worked case

*Separate, unfinished piece, split out of `PAPER.md` on 2026-09-20 so that the main paper makes one claim. The code and data stay where they are (`testability/`). This file holds only the write-up. Status: a full draft of the argument, not a submission. It depends on the detection-threshold arithmetic in `PAPER.md`, section 5, and on the panel limitations there.*

## 1. The idea

Institutions justify decisions with empirical claims (*it would just move elsewhere; it would harm competitiveness; it would be circumvented*) and rarely ask whether the claim can be checked at all. The protocol (`testability/METHOD.md`) does six things: quote the claim verbatim with speaker, source and date; specify the test the wording implies; inventory the evidence that exists; run the power arithmetic for what public data could detect; name the disclosure that would make the claim testable; and return one of four verdicts. One verdict is "the institution's claim is probably correct", and the code enforces that the protocol can return it (`testability/protocol.py`, `tests/test_testability.py`), so it is a method and not advocacy. Quotes must be verbatim in a stored copy of the source, and the register checks this.

## 2. Limitations (stated before the case)

1. **Secondary sources only.** The claim is reproduced by two independent secondary sources, Corporate Europe Observatory and PAN Europe (both 29 June 2026). The Commission's own statement and the Danwatch follow-up carrying it were searched for and not found; the Danwatch article of 18 May 2026 was found and does not reproduce it (`testability/sources/case-001-primary-source-attempts.txt`). The statement's date is unknown (between 13 May and 29 June 2026), and its context and any omissions are unverified.
2. **Notified quantity is not customs quantity.** Published notification tonnage (81,600 t in 2018, 122,000 t in 2024) is intended exports of mixtures, not shipments and not tonnes of active substance. It is an order-of-magnitude anchor against customs-recorded tonnes, a different instrument.
3. **National export-ban dates** (France January 2022, Belgium June 2023 with effect reported as May 2025, Switzerland 2021) come from search summaries and are not checked against legal texts.
4. **No EU-wide unilateral export ban has been in force**, so the counterfactual the claim is about has not been observed.
5. **The power arithmetic inherits the main paper's limitations**, including the HS92 back-conversion (`PAPER.md`, limitation 2) and the standard-error issues in its section 5.
6. **One worked case, no second institution.** The protocol has been applied once. Its generality is a claim we cannot yet support.

## 3. Case 001: the Commission's rationale for not proposing an export ban

### 3.1 The claim, verbatim

The Commission's written statement to Danwatch: a unilateral production and export ban in the EU "would not guarantee an improvement in health and environmental protection in affected countries, as it may push these countries to buy the same or worse chemical pesticides from companies outside of the EU" (`testability/cases/case-001.md`, `testability/register.yaml`). Two sub-claims: 001-C1 (substitution, a prediction about a counterfactual policy) and 001-C2 ("would not guarantee an improvement", which is true of almost any policy and no observation could contradict it, so it is not an empirical claim as worded).

### 3.2 Two framings of one position

The Commission's sentence opens with "a unilateral production and export ban in the EU", so production is explicitly in scope. It then gives its **mechanism** for why such a ban would fail: importing countries "may … buy the same or worse chemical pesticides from companies outside of the EU", that is, **supplier substitution by importing countries**. PAN Europe's press release also reports a shorter paraphrase, in quotation marks, of a Commission spokesperson's argument: an export ban "could simply shift production outside the EU while penalising European companies", that is, **production relocation**. Both passages were matched character for character on the page on 2026-09-20 (`testability/sources/case-001-pan-europe.txt`). The page does not say which Commission document the shorter phrase comes from, and we did not establish that.

The relocation framing also has an industry source. CropLife Europe's comment on the Commission's 2023 public consultation on prohibiting the production of hazardous chemicals for export (page dated 8 May 2023) says: "Such a ban would likely result in manufacturing being exported from Europe to other regions in the world" (`testability/sources/case-001-croplife-europe-2023.txt`, matched on the raw page, 2026-09-20). That comment does not state the importer-substitution mechanism in the Commission's form; it argues, among other things, that a ban would increase the risk of illegal and counterfeit pesticides.

An earlier draft said the relocation wording was not the Commission's; that was too strong and is withdrawn. The accurate finding is narrower: the public debate is not arguing about a fabrication. It amplifies the less specific of two framings, and the testable mechanism, substitution by importing countries, is the one that gets dropped. The two are tested with different data (importer purchases by supplier origin, versus the location of production and investment), and neither implies the other.

### 3.3 The test and the evidence

The test the wording implies: for importing countries, after an export ban, do purchases of the same or worse pesticides shift to non-banning suppliers? Unit: importing country × banned active substance × year; outcome: tonnes imported from suppliers in the banning jurisdiction versus elsewhere; quantity of interest: leakage, the increase in non-banning-supplier tonnage over the decrease in banning-supplier tonnage, plus a hazard comparison for "same or worse". The threshold for what matters is a value judgement of the decision-maker; as an illustration only, leakage near 1 supports the claim in tonnage terms and below about 0.5 means a ban removes at least half of the exports.

Evidence: CEPII BACI bilateral trade at HS6 is public, but a banned substance is never observed separately in heading 3808. Public Eye published the full dataset of its 2018 investigation (substance, exporting EU country, destination, notified quantity, year), and Unearthed publish 2024 country aggregates (`decisions/0006-*.md`); these are EU-side only, notified not shipped, with no importer-side supplier mix, so they cannot test substitution. Missing: substance-level realised exports by destination, importing countries' purchases by supplier origin, and hazard classification of substitutes. The feasibility premise can be checked from public data: non-EU exporters ship 4.7 times (2018) and 7.2 times (2024) the EU's customs tonnage of heading 3808 into non-EU destinations (`testability/cases/case-001-arithmetic.json`). That supports the possibility of substitution, not its size or hazard.

### 3.4 Power and verdict

Notified banned-pesticide tonnage is about 11-18% of customs tonnes of heading 3808 exported to non-EU destinations; if all of it vanished the heading total would fall by 0.12-0.20 log points. A design like ours has a randomization-based standard error of 0.33 to 0.54 log points for the EU-minus-rest-of-world contrast, so the detection threshold is 0.93 to 1.51 log points: the effect that would matter is about 5 to 13 times too small for public HS6 data to see, even at 100% elimination. That range comes from basket-level placebo standard errors and was already placebo-derived when the main paper's Stage G was recomputed, so it did not change (`decisions/0010-*.md`).

**Verdict: untestable with public data. Testable in principle. The test the wording implies (supplier substitution) has not been attempted by anyone we could find, and our search was limited. The tests that have been attempted, including the displacement study in `PAPER.md`, address a different claim.** Nothing here shows the Commission is right or wrong: it has asserted, as the reason for not acting, something that neither it nor anyone outside it can currently check. A concrete disclosure request is in `testability/cases/case-001.md`.

## 4. What this piece still needs

A second case, ideally one where the protocol returns "probably correct"; the primary text of the Commission's statement; a check of the national export-ban dates against legal texts; and a proper literature search on testability of policy justifications (`/priorwork`), which has not been run.
