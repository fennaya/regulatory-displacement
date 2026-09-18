"""STAGE H: one comparison table across every specification tried in the
causal-specification repair, per treatment package.

This module orchestrates (does not re-implement) every prior stage's
estimator against the same 5 testable packages, so the dashboard and any
report can show one table instead of five separate ad hoc scripts. Two
estimands appear, labeled, not silently conflated:
  - "event-time k=+N": the treated-vs-control gap at a specific relative
    year, relative to k=-1 (Stage 3's original convention, kept by
    old-OLS-TWFE, truncated, triple-diff, and matched-pool).
  - "average post-period ATT": a single treated-post dummy averaged over
    the whole post window (PPML and clustered-SE, for reasons specific to
    those estimators -- see their own modules).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import duckdb

from displacement_observatory.analysis.clustered import build_exporter_product_year_rows, fit_ols_with_cluster_robust_se
from displacement_observatory.analysis.diD import EventDiDResult, run_event_did
from displacement_observatory.analysis.matching import select_matched_controls
from displacement_observatory.analysis.overlap import OverlapFlag, PackageAudit
from displacement_observatory.analysis.packages import TreatmentPackage
from displacement_observatory.analysis.ppml import build_importer_product_year_panel, fit_ppml_att
from displacement_observatory.analysis.power import BASKET_SHARE_ASSUMPTIONS, evaluate_package
from displacement_observatory.analysis.triple_diff import run_triple_diff
from displacement_observatory.register.store import RegisterLoadResult


@dataclass
class SpecRow:
    package_id: str
    method: str
    estimand: str
    coef: float | None
    ci_low: float | None
    ci_high: float | None
    n_obs: int | None
    n_dropped_zeros: int | None
    note: str = ""


@dataclass
class PackageComparison:
    package_id: str
    substances: tuple[str, ...]
    hs6: str
    classification: str
    rows: list[SpecRow] = field(default_factory=list)
    power_verdict: str | None = None


def _headline_k(study) -> int:
    return max(k for k in study.relative_years if k >= 0)


def build_package_comparison(
    con: duckdb.DuckDBPyConnection,
    package: TreatmentPackage,
    audit: PackageAudit,
    register: RegisterLoadResult,
    original_result: EventDiDResult,
    control_hs6: list[str],
    overlap_flags: list[OverlapFlag],
    source: str = "BACI",
    source_version: str = "202601",
) -> PackageComparison:
    event = next(e for e in register.events if e.event_id == package.event_ids[0])
    comparison = PackageComparison(
        package_id=package.package_id, substances=package.substances, hs6=package.hs6,
        classification=audit.classification.value,
    )

    if original_result.status != "ok" or original_result.study is None:
        return comparison

    s = original_result.study
    k = _headline_k(s)
    comparison.rows.append(SpecRow(
        package.package_id, "OLD OLS-TWFE (Stage 3, unrepaired)", f"event-time k=+{k}",
        s.coef[k], s.ci_low[k], s.ci_high[k], s.n_obs, None,
        "log(1+value) aggregated over all EU exporters and ~150-200 non-EU importers, 542 unmatched controls",
    ))

    eff_year = event.effective_date.year
    ks = sorted(s.relative_years)
    y0, y1 = eff_year + ks[0], eff_year + ks[-1]

    truncating = [f for f in overlap_flags if f.earlier_package_id == package.package_id]
    if truncating:
        cutoff = min(f.later_effective_year for f in truncating) - 1
        trunc = run_event_did(con, event, register, window_years=5, max_post_year=cutoff, source=source, source_version=source_version)
        if trunc.status == "ok":
            tk = _headline_k(trunc.study)
            comparison.rows.append(SpecRow(
                package.package_id, f"TRUNCATED at {cutoff} (Stage B.4)", f"event-time k=+{tk}",
                trunc.study.coef[tk], trunc.study.ci_low[tk], trunc.study.ci_high[tk], trunc.study.n_obs, None,
                f"post-period cut before {truncating[0].later_package_id}'s effective date",
            ))

    triple = run_triple_diff(con, original_result, control_hs6, window_years=5)
    tk2 = _headline_k(triple.study)
    comparison.rows.append(SpecRow(
        package.package_id, "TRIPLE-DIFF (Stage C, RoW-netted)", f"event-time k=+{tk2}",
        triple.study.coef[tk2], triple.study.ci_low[tk2], triple.study.ci_high[tk2], triple.study.n_obs, None,
        "EU-minus-RoW log-value difference per product-year, nets out shared product-specific shocks",
    ))

    pre_years = [k_ + eff_year for k_ in ks if k_ < 0]
    match_stats = select_matched_controls(con, package.hs6, control_hs6, original_result.exporter_codes, pre_years)
    matched = run_event_did(con, event, register, window_years=5, control_hs6_override=match_stats.matched_hs6, source=source, source_version=source_version)
    if matched.status == "ok":
        mk = _headline_k(matched.study)
        comparison.rows.append(SpecRow(
            package.package_id, "MATCHED CONTROLS (Stage D)", f"event-time k=+{mk}",
            matched.study.coef[mk], matched.study.ci_low[mk], matched.study.ci_high[mk], matched.study.n_obs, None,
            f"{len(match_stats.matched_hs6)} controls (same chapter, order-of-magnitude volume, trend-matched), vs {len(control_hs6)} unmatched",
        ))

    panel = build_importer_product_year_panel(con, package, original_result.exporter_codes, control_hs6, y0, y1)
    ppml = fit_ppml_att(panel)
    comparison.rows.append(SpecRow(
        package.package_id, "PPML (Stage B.1, levels, keeps zeros)", "average post-period ATT",
        ppml.coef, ppml.ci_low, ppml.ci_high, ppml.n_obs, panel.n_zero_cells,
        ppml.note,
    ))

    cluster_rows = build_exporter_product_year_rows(con, package.hs6, match_stats.matched_hs6, original_result.exporter_codes, y0, y1)
    clustered = fit_ols_with_cluster_robust_se(cluster_rows, effective_year=eff_year)
    comparison.rows.append(SpecRow(
        package.package_id, "CLUSTERED SE (Stage E, exporter-product)", "average post-period ATT",
        clustered.coef, clustered.ci_clustered[0], clustered.ci_clustered[1], clustered.n_obs, None,
        f"classical SE={clustered.se_classical:.3f} vs clustered SE={clustered.se_clustered:.3f} ({clustered.se_clustered/clustered.se_classical:.2f}x)",
    ))

    assumption = next((a for a in BASKET_SHARE_ASSUMPTIONS if a.package_id == package.package_id), None)
    if assumption:
        verdict = evaluate_package(package.package_id, clustered.se_clustered, assumption)
        comparison.power_verdict = verdict.verdict

    return comparison
