# Displacement Observatory

**This repository contains a testability audit protocol, and its first
application is regulatory displacement in hazardous pesticides.**

Institutions justify decisions with empirical claims (*it would just move
elsewhere; it would harm competitiveness; it would be circumvented*) and
almost nobody asks whether those claims can be checked at all. The protocol
in [`testability/METHOD.md`](testability/METHOD.md) does: quote the claim
verbatim, specify the test, inventory the evidence, run the power
arithmetic, name the disclosure that would make it testable, and return one
of four verdicts. It can return "the institution's claim is probably
correct"; the code enforces that it can, so it is a method and not
advocacy. **Case 001**
([`testability/cases/case-001.md`](testability/cases/case-001.md)) audits the
European Commission's stated reason for not proposing an export ban on
EU-banned pesticides. Verdict: **untestable with public data** (even total
elimination of the banned-substance trade is about 5 to 13 times below what
public HS6 trade data can detect), with the feasibility premise supported
and a concrete data request attached. The displacement analysis below is
the work that produced that arithmetic, and is the reason the protocol
exists: it tried to test the claim and found it cannot be tested at the
granularity available to the public. The main paper, on the detection-
threshold arithmetic, is `PAPER.md`; the protocol and Case 001 write-up is a
separate, unfinished piece, `PAPER-testability.md`. Case 001 rests on two
secondary transcriptions of the Commission's statement; the primary is
unretrieved.

## The displacement study

Tests one falsifiable claim: when jurisdiction A restricts a product, flows
of that product into jurisdictions *without* the restriction rise after the
effective date, relative to control products that were never restricted.
<!-- falsifiable: displacement-hypothesis -->
See `falsification.md` for what would make us abandon this claim, and its
current status (**untested**, not "weakly supported" — see that file).

Scope, deliberately narrow: **pesticides and hazardous chemicals only** (HS
chapters 28, 29, 38). Nothing here generalises beyond that until it works
end to end. The register holds 9 cited events across 8 substances, but the
correct unit of treatment is neither: it is **6 treatment packages**
(companion regulations sharing an HS6, a decision date and an effective
date collapse to one package — see `analysis/packages.py`), of which only
**5 are testable**. How many are CLEAN (no overlap with another package's
estimation window in the same HS6 code) **is a band, not a number: 0 of 5 at
the ±5-year window, 1 of 5 (EU endosulfan) at ±4, ±3 and ±2.** No single window
is chosen, on purpose (`METHODS.md`, "Why no single window was chosen"). The
window-independent part is that four of the five packages overlap at every
window from ±2 to ±5; endosulfan's only overlap at ±5 is the last, partial year
with the untestable Rotterdam listing. State the project's size as **"6
packages, 5 testable, 0-1 clean depending on the window (0 at ±5, 1 at ±4 to
±2),"** not "9 events" or "8 substances": both overstate what this version can
speak to independently.

Everything below Step 3 went through a full causal-specification repair
after the first version's estimates turned out to be uninformative (every
point estimate positive, every 95% CI roughly ±2 log points, nothing
significant). That repair is Steps A-H below the original seven steps —
read it before trusting any single number on the dashboard.

## Limitations (read this before the results below)

**The panel and the register (mirrors `PAPER.md` section 2; read these first):**

- **The panel is a backward conversion, and a basket may not be the same
  object across years.** The panel is the HS92 file of BACI 202601 for all
  years 1995-2024. CEPII says trade reported in newer nomenclature
  revisions is converted to older ones, that this "reduces the number of
  products present in the data" and "leads to some inaccuracies", and its
  pages do not describe the conversion procedure. Heading 3808 was
  restructured in **HS2007** (3808.50 for goods containing substances named
  in Subheading Note 1, plus 3808.91-.99 by function); goods in 3808.50
  span several functions, so converting them back to HS92 requires an
  allocation CEPII does not document. Endosulfan is an instance (the
  WCO's HS2017 notes name it in a substance-based subheading; the other
  seven substances are not named). The composition of basket 380810 in
  2018 is therefore not guaranteed to match 2004, and every long-window
  estimate assumes it does. This threatens the panel, not only the
  register. Nothing here corrects for it.
- **Mappings await owner sign-off.** The eight substance-to-HS6 mappings
  were proposed and self-confirmed by Claude. External evidence has since
  been attached (`review/hs6-mapping-review.md`): 6 agree with the
  function-to-subheading mapping, 2 are unclear (chlorpyrifos-methyl,
  endosulfan), none contradict it. Sign-off by the owner is still pending
  and the provenance test is an expected failure until then.
- **Analysis history.** The repairs (PPML, staggered estimator, triple
  difference, matched controls, clustering) were chosen after the first
  estimates were uninformative and were **not pre-registered**; only the
  matching thresholds and destination groups were committed before
  estimation. 48 specifications were tried, 7 with a CI excluding zero, in
  both signs (2.4 expected by chance).
- **This null must not be cited for or against the European Commission.**
  The Commission's stated mechanism is supplier substitution by importing
  countries; this study tested whether EU use restrictions moved trade to
  unrestricted destinations, a different claim. Case 001's quote comes from
  two secondary sources; the primary is unretrieved. Published notified
  tonnage is intended exports of mixtures, not customs quantity.
- **No systematic literature search** was run; citations in `PAPER.md` are
  audited (`reviews/citation-audit.md`) but few.

**On the repaired specification:**

- **The one basket-level estimate that cleared significance does not survive an attack.**
  <!-- falsifiable: basket-level-eu-restrictions-moved-trade -->
  The staggered-robust +0.664 log points (HS6 380810/380830 vs. never-restricted
  codes, 1995-2024) is not evidence that EU restrictions moved trade in those
  baskets (`decisions/0009-*.md`, numbers in `data/attack/`): (1) the original
  specification had no rest-of-world comparison; adding it, rest-of-world
  exporters of the same codes to the same destinations rose *more* (+0.789)
  and the EU-specific triple difference is -0.124; (2) assigning the same cohort
  years to randomly chosen never-restricted codes gives a placebo SD of about 1.4
  against a reported SE of 0.145, so the real estimate is unremarkable (two-sided
  placebo p = 0.28-0.59, and 0.68-0.81 for the triple difference); (3) there is
  no jump at the effective date, the divergence appears 3-15 years later; (4) the
  size would need about half of each basket fully displaced. Composition (the
  restricted substance's share of its own basket) cannot be tested with the data
  here. This is not "the only effect that doesn't cross zero": across Stages A-H,
  7 of 48 specifications have a CI excluding zero (2.4 expected by chance if all
  were independent nulls), in both signs, three of them artifacts of discarded
  runs.

- **Given the basket-share assumptions below, this instrument cannot see a
  plausible-sized substance-specific effect for 5 of the 5 testable
  packages (at least 4 of 5 under either standard error).** The MDE half is computed from a standard error; the effect-size
  half depends on assumed shares, so the conclusion is conditional on them.
  Stage G's power analysis, **recomputed 2026-09-19 from placebo-derived
  standard errors** (`decisions/0010-*.md`): Stage E's cluster-robust SEs
  were too narrow, the placebo SEs are 2.3-3.7x wider, and the minimum
  detectable effect at 80% power rises from 0.31-0.60 to 0.72-1.93 log
  points, so the restricted substance would have to be 51-86% of its HS6
  basket (was 27-45%), fully displaced, to be seen. It exceeds the maximum
  plausible effect implied by *100% displacement* of the assumed share for
  all five packages; neonicotinoids, borderline under Stage E's SE, is now
  not detectable either. **Our original detection thresholds were too generous to the instrument: they implied more detection power than existed. Correcting the standard errors raises the thresholds and strengthens the conclusion.** The placebo SE is a proxy (it
  may overstate a smooth treated code's own noise), so the truth lies
  between the two; both are reported. The "5 to 13 times" figure for Case
  001 was already basket-level placebo-derived and is unchanged.
  Basket-share assumptions are stated with confidence levels in
  `analysis/power.py` — only imidacloprid's is anchored to an (imprecise,
  vendor-inconsistent) web search; the rest are explicitly unverified.
  **A null result here means "this instrument cannot see this," not "no
  displacement occurred."**
- **Most of the original "displacement" signal was general market growth,
  not an EU-restriction-specific effect.** Once rest-of-world exporters of
  the *same product* into the *same destinations* are used as the
  counterfactual (triple difference, Stage C) instead of being reported as
  a side caveat, **every package's original double-difference point
  estimate shrinks by 60-93%** (paraquat: +0.620 → +0.078; chlorpyrifos:
  +0.051 → +0.004). The original estimates were themselves not significant
  (CIs about ±2 log points), so this says the apparent signal is mostly
  common to all exporters, not that a precisely measured effect was
  explained away.
- **Every testable package is window-contaminated by another package in the
  same HS6 code at the pre-set ±5-year window; four of five are at every
  window tried (±2 to ±5), and endosulfan is clean at ±4 or narrower.**
  Stage A's overlap audit: neonicotinoids (window
  2013-2023) overlap chlorpyrifos (effective 2020) for 4 of 6 post-period
  years (67%); atrazine (window 1999-2009) overlaps paraquat (effective
  2007) for 3 of 6 years (50%); EU endosulfan overlaps the Rotterdam
  Convention's 2011 global PIC listing of the same substance for the
  window's final year (17%, partial-year). Truncating the window at the
  contaminating event's start moves the point estimates sharply: atrazine's
  falls from +0.407 to -0.017 once the paraquat-contaminated years are
  removed (both intervals span zero, so this shows the estimate is not
  stable, not that the sign is known).
- **Classical standard errors understate uncertainty, sometimes badly
  enough to manufacture a false significant result.** Cluster-robust SEs
  (exporter-product level, Stage E) run 1.04-1.69x wider than classical.
  Endosulfan's classical 95% CI excluded zero ([-0.528, -0.033], looks
  significant); its cluster-robust CI does not ([-0.699, +0.137]).
- **Destination heterogeneity does not confirm the "concentrates in
  weak-regulation destinations" hypothesis.** Stage F, pre-registered
  before estimating (`data/destination_groups_v1.yaml`): only endosulfan
  shows the predicted high-exposure > low-exposure pattern; two packages
  show essentially no difference; two (chlorpyrifos, atrazine) have the
  **opposite** ordering of point estimates (atrazine +0.114 high vs. +0.764
  low). Every group interval spans about ±2 to ±3 log points, so none of the
  between-group differences is distinguishable from zero: the hypothesis is
  not supported, and it is not refuted either.
- **HS6 is coarser than a single substance.**
  <!-- falsifiable: hs6-too-coarse -->
  In the HS92 nomenclature BACI uses here, heading 3808 has exactly five
  subheadings (insecticides / fungicides / herbicides / disinfectants /
  rodenticides). Every substance shares its
  HS6 code with every *other* active ingredient in the same functional
  class, restricted or not, and with other restricted substances in this
  same register. This is *why* Stage G's power analysis matters more than
  a confidence interval's width alone — see `falsification.md`, now
  resolved (not falsified): 5 of 5 packages not detectable with
  placebo-derived standard errors, at least 4 of 5 under either.

**Inherited and structural limitations:**

- **The Stage 3 log-linear design silently discarded exactly the
  observations where displacement lives.** Aggregating trade value over
  ~150-200 destinations before taking logs makes a true collective zero
  rare (59-61% of individual importer-product-year cells have no recorded
  flow in Stage B.1's disaggregated panel; BACI records only positive flows,
  so these are true zeros or unreported flows, and the data cannot say
  which) — a destination going from
  zero imports to positive imports is the first place a displacement
  signal would show up, and the old design couldn't see it. PPML in
  levels (`analysis/ppml.py`) fixes this but is not yet the dashboard's
  headline estimator (see `decisions/0002-*.md`).
- **Validation coverage is incomplete by construction.** Step 5 can only
  test the "EU banned-pesticide exports" episode type named in the brief.
  China's plastic-waste leakage (HS39) and used-vehicle flows (HS87) are
  structurally out of reach of this chemicals-only panel and were **not
  tested** — stated plainly, not silently skipped.
- **EU membership, treated as a single bloc**, is resolved by
  accession/exit date from a hand-maintained table
  (`analysis/country_groups.py`), not a live registry. The exporter
  dimension is pooled across all EU member states rather than given its
  own fixed effect (`decisions/0002-*.md`) — a deliberate scope choice
  given the treatment is defined at the bloc level, not a limitation
  discovered after the fact.
- **Missing quantity** (3.0% of panel rows) and BACI's own CIF→FOB
  reconciliation are inherited limitations of the source data.
- **Two of nine register events (the 2018 neonicotinoid companions) were
  sourced from secondary reporting**, not independently re-fetched from
  EUR-Lex text, flagged as such in the register itself.
- **The endosulfan Rotterdam event's citation was corrected** (2026-09-20):
  it pointed to a COP-4 (2008) draft proposal that was not adopted. The
  register dates (24 June and 24 October 2011, decisions RC-5/3 to RC-5/5)
  were right, and a test now asserts that register dates equal the dates
  the overlap audit uses, for every event.
- **Decision 0006** (export-notification data as primary outcome) is
  resolved: considered and not adopted, because a structured dataset does
  exist (Public Eye 2018; Unearthed 2024 aggregates). It is EU-side only,
  notified not shipped, so it cannot test importer-side substitution.

## The causal-specification repair (Stages A-H)

Triggered when the original Step 3 estimates turned out uninformative:
every point estimate positive, every CI ±2 log points, nothing
significant, pre-trends clean. The question was whether that's the
specification or the world. See `decisions/000*.md` for the full
reasoning behind each stage, `falsification.md` for what's now resolved.

| Stage | What it did | Headline result |
|---|---|---|
| A — overlap audit | Windows each package actually used, checked pairwise for same-HS6 overlap | Clean packages: a band of 0-1 of 5 (0 at ±5 years; 1, endosulfan, at ±4, ±3 and ±2 years); 4 of 5 contaminated at every window |
| B.1 — PPML | Levels, importer×product×year FE, keeps zero flows (`analysis/ppml.py`) | 59-61% of cells have no recorded flow (zero or unreported), which the old log spec never saw |
| B.2/B.3 — staggered-robust | Cumulative-treatment HS6 panel, did2s vs naive pooled TWFE (`analysis/staggered.py`) | +0.664 log pts, CI [+0.381, +0.948], with staggered-adoption bias tiny (0.017). **Then attacked (2026-09-19, `decisions/0009-*.md`) and it FAILS as an EU-restriction effect**: rest-of-world exports of the same codes rose more (+0.789), the EU-specific triple difference is -0.124, and a placebo with random codes gives p = 0.28-0.81 |
| B.4 — truncated windows | Cut post-period before the contaminating event (`diD.py`'s `max_post_year`) | Atrazine's effect flips sign (+0.407 → -0.017) |
| C — triple difference | EU-minus-RoW value, differenced before estimating (`analysis/triple_diff.py`) | 60-93% of every package's estimate explained by rest-of-world growth |
| D — matched controls | Same chapter, order-of-magnitude volume, trend-matched, pre-registered (`analysis/matching.py`, `decisions/0007-*.md`) | Standard errors down 42-61% |
| E — clustered SEs | Exporter-product level (`analysis/clustered.py`) | 1.04-1.69x wider than classical; one false-positive-looking result corrected. Still too narrow: treatment varies at the HS6 level, so exporter-product clusters within one treated code share its common shock; with one treated code per package no analytic SE is reliable (placebo in `decisions/0009-*.md`) |
| F — destination heterogeneity | Pre-registered high/low exposure groups (`data/destination_groups_v1.yaml`, `decisions/0008-*.md`) | Mixed/negative — concentration hypothesis not confirmed |
| G — power analysis | MDE vs. basket-share arithmetic (`analysis/power.py`) | **5 of 5** NOT DETECTABLE even at 100% displacement under placebo-derived SEs (4 of 5 under Stage E's SEs); MDE 0.72-1.93 log pts (`decisions/0010-*.md`) |
| H — this table + dashboard | `analysis/comparison.py`, `/specifications` view | — |

Full per-package numbers: `/specifications` on the dashboard, or
`analysis/comparison.py`'s `build_package_comparison`.

## The seven steps (original pipeline, pre-repair)

### STEP 1 — the trade panel
CEPII BACI (HS92 revision, version 202601, 1995-2024), filtered to HS
chapters 28/29/38. 15,448,188 rows, 234 countries, 544 HS6 codes, 3.0%
missing quantity. UN Comtrade fill-in for post-BACI years is wired in
(`ingest/comtrade.py`) but inactive — no API key configured.
Run: `uv run python scripts/build_panel.py`

### STEP 2 — the restriction register
9 events, 8 substances: EU non-renewal and non-inclusion decisions, a
court-annulment withdrawal (paraquat), the 2018 neonicotinoid restrictions
of approval conditions (not non-renewals), plus one Rotterdam Convention
PIC listing (a prior-informed-consent procedure, not a ban), every field
citing a real primary source.
decision_date and effective_date are always separate fields. Records
without a citation are dropped by the loader, not guessed.
Register: `data/register/events/events_v1.yaml`
Mapping: `data/register/mappings/chemical_hs6_mappings_v1.yaml`

### STEP 3 — the test (original, see the repair above for what replaced it)
Two-way fixed-effects event-study estimator (`analysis/twfe.py`), tested
on synthetic data with a known injected effect. This is the specification
the causal-spec repair (Stages A-H) was built to fix.

### STEP 4 — competing explanations
Price-vs-quantity, rest-of-world demand growth, EUR/USD currency, HS-code
switching, per event (`analysis/competing_explanations.py`).

### STEP 5 — validation by rediscovery
3 documented cases (Unearthed/Public Eye "Banned in Europe" 2020) plus 2
explicitly out-of-scope reference cases. **Directional recall: 100%.
Significant recall: 0%.** The directional figure discriminates nothing: all
five original package estimates were positive, so any estimator with a
positive bias would score 100%.

### STEP 6 — forward watchlist
2 real, dated forecasts, append-only (`data/watchlist/forecasts.jsonl`):
buprofezin
<!-- falsifiable: forecast-buprofezin-2026 -->
and flufenacet.
<!-- falsifiable: forecast-flufenacet-2026 -->
Both pending. **Untouched by the causal-spec repair.**

### STEP 7 — dashboard
FastAPI + Jinja2 + HTMX + Plotly (no React). Six views: Ranked Findings,
**Specifications** (added in Stage H — every estimator per package, side
by side, plus the power verdict), event detail, Watchlist, Scorecard,
Register browser.
Run: `uv run python scripts/run_dashboard.py` → http://127.0.0.1:8420
(pipeline computation on startup takes roughly 90 seconds — it runs six
estimators per testable package.)

## Running it

```bash
uv sync
uv run pytest              # tests, no network required
uv run python scripts/build_panel.py
uv run python scripts/run_dashboard.py
```

See `METHODS.md` to reproduce this design on a different hazard family.

## Project layout

```
src/displacement_observatory/
  config.py, db.py, panel_stats.py, pipeline.py
  ingest/            baci.py, comtrade.py
  register/          schema.py, store.py, mappings.py
  analysis/
    twfe.py, diD.py                        original event-study estimator
    packages.py                            STAGE A: substance -> treatment package collapse
    overlap.py                             STAGE A: contamination audit
    ppml.py                                STAGE B.1: Poisson, levels, keeps zeros
    staggered.py                           STAGE B.2/B.3: staggered-adoption-robust
    triple_diff.py                         STAGE C: RoW-netted triple difference
    matching.py                            STAGE D: matched control pools
    clustered.py                           STAGE E: cluster-robust SEs
    destination_groups.py                  STAGE F: pre-registered exposure groups
    power.py                               STAGE G: MDE + basket-share arithmetic
    comparison.py                          STAGE H: per-package comparison table
    competing_explanations.py, country_groups.py, fx.py, report.py
  validation/        rediscovery.py
  watchlist/         forecasts.py           (untouched by the repair)
  dashboard/         app.py, templates/      (includes STAGE H's /specifications view)
data/
  register/          events_v1.yaml, chemical_hs6_mappings_v1.yaml, eur_usd_annual.csv
  validation/         known_cases.yaml
  watchlist/          forecasts.jsonl (append-only, untouched by the repair)
  destination_groups_v1.yaml               STAGE F pre-registration
  raw/, processed/    gitignored (BACI zip, DuckDB file)
testability/          the audit protocol: METHOD.md, protocol.py (schema + checks),
                       register.yaml (Case 001 + 2 candidates), cases/, sources/
reviews/              hostile-referee reviews of the README
PAPER.md              main paper: public HS6 data cannot answer substance-level displacement questions
PAPER-testability.md  separate, unfinished piece: the audit protocol and Case 001
decisions/            one file per methodological decision (use /decide)
falsification.md      what would refute each live claim (use /falsify)
CLAUDE.md             standing rules for every session in this repo
scripts/              download_baci.py, build_panel.py, run_dashboard.py,
                       check_falsification_coverage.py
tests/                all synthetic-data, no network
```
