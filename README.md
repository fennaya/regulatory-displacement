# Displacement Observatory

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
**5 are testable**, and **0 of those 5 are CLEAN** — every one overlaps
another package's estimation window in the same HS6 code. State the
project's size as **"6 packages (5 testable, 0 clean),"** not "9 events" or
"8 substances" — both overstate what this version can speak to
independently.

Everything below Step 3 went through a full causal-specification repair
after the first version's estimates turned out to be uninformative (every
point estimate positive, every 95% CI roughly ±2 log points, nothing
significant). That repair is Steps A-H below the original seven steps —
read it before trusting any single number on the dashboard.

## Limitations (read this before the results below)

**On the repaired specification (read these first):**

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

- **This instrument cannot see a plausible-sized substance-specific effect
  for 4 of the 5 testable packages, and this is arithmetic, not a hedge.**
  Stage G's power analysis: at 80% power, the minimum detectable effect
  (from Stage E's cluster-robust standard errors) exceeds the maximum
  plausible effect implied by *100% displacement* of the restricted
  substance's assumed share of its HS6 basket, for chlorpyrifos,
  endosulfan, atrazine, and paraquat. Neonicotinoids is borderline
  (detectable only toward the high end of its assumed 10-30% share).
  Basket-share assumptions are stated with confidence levels in
  `analysis/power.py` — only imidacloprid's is anchored to an (imprecise,
  vendor-inconsistent) web search; the rest are explicitly unverified.
  **A null result here means "this instrument cannot see this," not "no
  displacement occurred."**
- **Most of the original "displacement" signal was general market growth,
  not an EU-restriction-specific effect.** Once rest-of-world exporters of
  the *same product* into the *same destinations* are used as the
  counterfactual (triple difference, Stage C) instead of being reported as
  a side caveat, **60-93% of every package's original double-difference
  estimate disappears** (paraquat: +0.620 → +0.078, 87% eaten; chlorpyrifos:
  +0.051 → +0.004, 93% eaten, effectively zero).
- **Every testable package is window-contaminated by another package in the
  same HS6 code.** Stage A's overlap audit: neonicotinoids (window
  2013-2023) overlap chlorpyrifos (effective 2020) for 4 of 6 post-period
  years (67%); atrazine (window 1999-2009) overlaps paraquat (effective
  2007) for 3 of 6 years (50%); EU endosulfan overlaps the Rotterdam
  Convention's 2011 global PIC listing of the same substance for the
  window's final year (17%, partial-year). Truncating the window at the
  contaminating event's start changes answers sharply: atrazine's effect
  **flips from +0.407 to -0.017** once the paraquat-contaminated years are
  removed.
- **Classical standard errors understate uncertainty, sometimes badly
  enough to manufacture a false significant result.** Cluster-robust SEs
  (exporter-product level, Stage E) run 1.04-1.69x wider than classical.
  Endosulfan's classical 95% CI excluded zero ([-0.528, -0.033], looks
  significant); its cluster-robust CI does not ([-0.699, +0.137]).
- **Destination heterogeneity does not confirm the "concentrates in
  weak-regulation destinations" hypothesis.** Stage F, pre-registered
  before estimating (`data/destination_groups_v1.yaml`): only endosulfan
  shows the predicted high-exposure > low-exposure pattern; two packages
  show essentially no difference; two (chlorpyrifos, atrazine) show the
  **opposite** pattern, sharply for atrazine (+0.114 high vs. +0.764 low).
  Reported as a genuine mixed/negative finding, not reconciled.
- **HS6 is coarser than a single substance.**
  <!-- falsifiable: hs6-too-coarse -->
  HS heading 3808 has exactly five subheadings (insecticides / fungicides
  / herbicides / disinfectants / rodenticides). Every substance shares its
  HS6 code with every *other* active ingredient in the same functional
  class, restricted or not, and with other restricted substances in this
  same register. This is *why* Stage G's power analysis matters more than
  a confidence interval's width alone — see `falsification.md`, now
  resolved (not falsified) for 4 of 5 packages.

**Inherited and structural limitations:**

- **The Stage 3 log-linear design silently discarded exactly the
  observations where displacement lives.** Aggregating trade value over
  ~150-200 destinations before taking logs makes a true collective zero
  rare (59-61% of individual importer-product-year cells are genuine zero
  flows, per Stage B.1's disaggregated panel) — a destination going from
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
- **HS6 mappings are self-confirmed by Claude**, not individually reviewed
  by a human — see the mapping file's header.
- **One decision in `decisions/` (0006, export-notification data as
  primary outcome) has REASONING: UNKNOWN** — no evidence it was ever
  actually decided was found in the repo. Flagged, not silently dropped.

## The causal-specification repair (Stages A-H)

Triggered when the original Step 3 estimates turned out uninformative:
every point estimate positive, every CI ±2 log points, nothing
significant, pre-trends clean. The question was whether that's the
specification or the world. See `decisions/000*.md` for the full
reasoning behind each stage, `falsification.md` for what's now resolved.

| Stage | What it did | Headline result |
|---|---|---|
| A — overlap audit | Windows each package actually used, checked pairwise for same-HS6 overlap | 0 of 5 testable packages are CLEAN |
| B.1 — PPML | Levels, importer×product×year FE, keeps zero flows (`analysis/ppml.py`) | 59-61% of cells are genuine zeros the old log spec never saw |
| B.2/B.3 — staggered-robust | Cumulative-treatment HS6 panel, did2s vs naive pooled TWFE (`analysis/staggered.py`) | +0.664 log pts, CI [+0.381, +0.948], with staggered-adoption bias tiny (0.017). **Then attacked (2026-09-19, `decisions/0009-*.md`) and it FAILS as an EU-restriction effect**: rest-of-world exports of the same codes rose more (+0.789), the EU-specific triple difference is -0.124, and a placebo with random codes gives p = 0.28-0.81 |
| B.4 — truncated windows | Cut post-period before the contaminating event (`diD.py`'s `max_post_year`) | Atrazine's effect flips sign (+0.407 → -0.017) |
| C — triple difference | EU-minus-RoW value, differenced before estimating (`analysis/triple_diff.py`) | 60-93% of every package's estimate explained by rest-of-world growth |
| D — matched controls | Same chapter, order-of-magnitude volume, trend-matched, pre-registered (`analysis/matching.py`, `decisions/0007-*.md`) | Standard errors down 40-61% |
| E — clustered SEs | Exporter-product level (`analysis/clustered.py`) | 1.04-1.69x wider than classical; one false-positive-looking result corrected |
| F — destination heterogeneity | Pre-registered high/low exposure groups (`data/destination_groups_v1.yaml`, `decisions/0008-*.md`) | Mixed/negative — concentration hypothesis not confirmed |
| G — power analysis | MDE vs. basket-share arithmetic (`analysis/power.py`) | 4 of 5 packages NOT DETECTABLE even at 100% displacement |
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
9 events, 8 substances, EU non-renewals/withdrawals plus one Rotterdam
Convention PIC listing, every field citing a real primary source.
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
Significant recall: 0%.**

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
decisions/            one file per methodological decision (use /decide)
falsification.md      what would refute each live claim (use /falsify)
CLAUDE.md             standing rules for every session in this repo
scripts/              download_baci.py, build_panel.py, run_dashboard.py,
                       check_falsification_coverage.py
tests/                all synthetic-data, no network
```
