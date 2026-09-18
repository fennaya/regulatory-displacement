# Displacement Observatory

Tests one falsifiable claim: when jurisdiction A restricts a product, flows
of that product into jurisdictions *without* the restriction rise after the
effective date, relative to control products that were never restricted.

Scope, deliberately narrow: **pesticides and hazardous chemicals only** (HS
chapters 28, 29, 38). Nothing here generalises beyond that until it works
end to end. The register holds 9 cited events across 8 substances, but the
correct unit of treatment is neither: it is 6 **treatment packages**
(companion regulations sharing an HS6, a decision date and an effective
date collapse to one package — see `analysis/packages.py`), of which only
5 are testable at all, and **as of the causal-specification repair below,
zero of those 5 are CLEAN** — every one overlaps, within the same HS6 code,
with at least one other package's estimation window. State the project's
size as "6 packages (5 testable, 0 clean)," not "9 events" or "8
substances" — both of the latter overstate what this version can actually
speak to independently.

## Limitations (read this before the results below)

- **Every testable package is window-contaminated by another package in
  the same HS6 code — this is currently the single biggest threat to every
  finding in this project, ahead even of HS6 coarseness below.** The
  overlap audit (`analysis/overlap.py`, STAGE A of the causal-spec repair)
  checks every pair of same-HS6 packages for calendar overlap between one
  package's estimation window and another's effective date, using the
  windows the estimator actually used (post panel-coverage clipping), not
  a nominal ±5 years. Result: neonicotinoids (window 2013-2023) overlap
  chlorpyrifos (effective 2020) for 4 of 6 post-period years (67% of the
  neonicotinoid package's post-period is really "neonicotinoids AND
  chlorpyrifos-ban years" indistinguishably); atrazine (window 1999-2009)
  overlaps paraquat (effective 2007) for 3 of 6 years (50%); EU endosulfan
  (window 2001-2011) overlaps the Rotterdam Convention's 2011 global PIC
  listing of the same substance for the window's final year (17%, and only
  the last ~2 months of it). **Every point estimate reported anywhere in
  this project prior to STAGE B's staggered-adoption-robust and
  truncated-window estimates should be read as "this HS6 code's basket
  moved, for reasons that include but are not limited to this specific
  package," not as a clean single-event effect.**
- **HS6 is coarser than a single substance — the second-biggest threat to
  every finding in this project.** BACI/Comtrade report trade at
  6-digit HS codes; HS heading 3808 has exactly five subheadings
  (insecticides / fungicides / herbicides / disinfectants / rodenticides).
  Every substance in the register shares its HS6 code with every *other*
  active ingredient in the same functional class — restricted or not — and,
  in six of nine register events, with *another restricted substance from
  this same register*. No event-level finding here can be attributed to one
  substance with confidence from trade data alone. See
  `data/register/mappings/chemical_hs6_mappings_v1.yaml` for the full
  per-mapping discussion.
- **Statistical power is low.** Classical (non-clustered) OLS standard
  errors on a two-way fixed-effects event study, with ~540 control products
  of wildly different scale, are wide — roughly ±1 to ±1.8 log points at
  95%. Every event's confidence interval crosses zero. Point estimates are
  directionally right on 100% of the independently-documented cases this
  pipeline was checked against (STEP 5), but zero of them are statistically
  significant. **"Right direction, not significant" is this version's
  honest ceiling — not "displacement confirmed."**
- **Rest-of-world demand growth is large and pervasive.** For nearly every
  event, non-EU exporters' shipments of the *same* HS6 code to the *same*
  destinations grew 26-50% over the event window, unrelated to any single
  restriction. This is a first-class competing explanation for most of the
  positive point estimates above and is reported per-event, not folded away.
- **Validation coverage is incomplete by construction.** STEP 5 can only
  test the "EU banned-pesticide exports" episode type named in the brief.
  China's plastic-waste leakage (HS39) and used-vehicle flows (HS87) are
  structurally out of reach of this project's chemicals-only panel and were
  **not tested** — this is stated plainly rather than silently skipped.
  If the instrument can't be checked on those, it can't be trusted on them.
- **EU membership, treated as a single bloc**, is resolved by accession/exit
  date from a hand-maintained table (`analysis/country_groups.py`), not a
  live registry. Pre-2002 legacy currencies are proxied by EUR/USD alone for
  the currency check, which understates member-state variation.
- **Missing quantity** (3.0% of panel rows) and BACI's own CIF→FOB
  reconciliation are inherited limitations of the source data, not of this
  pipeline; see the panel-stats output for the exact share.
- **Two of nine register events (the 2018 neonicotinoid companions) were
  sourced from secondary reporting**, not independently re-fetched from
  EUR-Lex text, and are flagged as such in the register itself.
- **HS6 mappings are self-confirmed by Claude**, not individually reviewed
  by a human, under the user's "do all steps needed" instruction — see the
  mapping file's header for exactly what "confirmed: true" means here.

## The seven steps

### STEP 1 — the trade panel
CEPII BACI (HS92 revision, version 202601, 1995-2024), filtered to HS
chapters 28/29/38. 15,448,188 rows, 234 countries, 544 HS6 codes, 3.0%
missing quantity. UN Comtrade fill-in for post-BACI years is wired in
(`ingest/comtrade.py`) but inactive — no API key configured; the gap is
currently small since BACI already covers through 2024.
Run: `uv run python scripts/build_panel.py`

### STEP 2 — the restriction register
9 events, 8 substances, EU non-renewals/withdrawals plus one Rotterdam
Convention PIC listing, every field citing a real primary source (EUR-Lex
regulation/decision text or a Court judgment) fetched and verified against
this project's own loaded BACI product metadata. decision_date and
effective_date are always separate fields; several events record a genuine
multi-month gap (e.g. imidacloprid: 204 days). Records without a citation
are dropped by the loader, not guessed — none were dropped in this version.
Register: `data/register/events/events_v1.yaml`
Mapping: `data/register/mappings/chemical_hs6_mappings_v1.yaml`

### STEP 3 — the test
Pure-Python (numpy, no ML/LLM) two-way fixed-effects event-study estimator
(`analysis/twfe.py`), unit-tested against synthetic data with a known
injected effect. Per event: treated = the event's HS6 code exported from
resolved EU-member countries to non-EU destinations; control = every HS6
code in chapters 28/29/38 never restricted by any register event, same
exporters, same destinations, same period. Pre-trend check flags any
pre-period coefficient significant at 95%. Event windows are clipped to the
panel's actual year coverage (a real bug, since fixed: a window that ran
past 2024 was silently reading "no data" as "zero trade").

### STEP 4 — competing explanations
For every event: price-vs-quantity decomposition (is the value effect a
volume effect or a price effect?), rest-of-world destination demand growth,
EUR/USD currency effect (ECB reference rate, fetched live and cached with
provenance), and HS-code-switching among sibling codes in the same heading.
Reported alongside every finding, not used to suppress it.

### STEP 5 — validation by rediscovery
Checked against 3 documented, independently-sourced cases (Unearthed/Public
Eye "Banned in Europe" 2020 investigation: atrazine, paraquat, chlorpyrifos)
plus 2 explicitly out-of-scope reference cases from the brief. **Directional
recall: 100%. Significant recall: 0%.** See Limitations above.

### STEP 6 — forward watchlist
2 real, dated forecasts, timestamped 2026-09-18, append-only
(`data/watchlist/forecasts.jsonl`, enforced in code — no update/delete
function exists): buprofezin (EU non-approval expected within 2026,
predicted destinations Brazil/Viet Nam/Thailand) and flufenacet (EU stock
grace period ends 2026-12-10, predicted destinations Ukraine/Brazil). Both
still pending as of today.

### STEP 7 — dashboard
FastAPI + Jinja2 + HTMX + Plotly (no React). Five views: Ranked Findings,
event detail (with Plotly event-time chart), Watchlist, Scorecard
(rediscovery + forecast track record — the credibility page), Register
browser.
Run: `uv run python scripts/run_dashboard.py` → http://127.0.0.1:8420

## Running it

```bash
uv sync
uv run pytest              # 39 tests, no network required
uv run python scripts/build_panel.py
uv run python scripts/run_dashboard.py
```

Optional: set `COMTRADE_API_KEY` in `.env` (see `.env.example`) to enable
the post-BACI Comtrade fill-in.

## Project layout

```
src/displacement_observatory/
  config.py, db.py, panel_stats.py, pipeline.py
  ingest/            baci.py, comtrade.py
  register/          schema.py, store.py, mappings.py
  analysis/          twfe.py, diD.py, competing_explanations.py,
                      country_groups.py, fx.py, report.py
  validation/        rediscovery.py
  watchlist/         forecasts.py
  dashboard/         app.py, templates/
data/
  register/          events_v1.yaml, chemical_hs6_mappings_v1.yaml, eur_usd_annual.csv
  validation/         known_cases.yaml
  watchlist/          forecasts.jsonl (append-only)
  raw/, processed/    gitignored (BACI zip, DuckDB file)
scripts/              download_baci.py, build_panel.py, run_dashboard.py
tests/                39 tests, all synthetic-data, no network
```
