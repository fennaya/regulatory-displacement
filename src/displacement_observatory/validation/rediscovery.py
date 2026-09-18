"""STEP 5: validation by rediscovery.

Cross-references a held-out set of already-documented displacement
episodes (data/validation/known_cases.yaml -- sourced from investigative
journalism/NGO reporting, NOT from this project's own statistics) against
this project's own DiD results, and reports two distinct recall metrics:

  - directional recall: does the pipeline's post-period point estimate have
    the expected (positive) sign?
  - significant recall: is that point estimate also statistically
    significant at 95%?

These are reported separately and honestly, per STEP 5: "if the instrument
cannot rediscover what is already known, it cannot be trusted on what is
not." A pipeline that gets the direction right but lacks the statistical
power to call it significant is a different (better) failure than getting
the direction wrong, and the two should not be collapsed into one number.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from displacement_observatory.analysis.diD import EventDiDResult

KNOWN_CASES_PATH = Path(__file__).resolve().parents[3] / "data" / "validation" / "known_cases.yaml"


@dataclass
class CaseCheck:
    case_id: str
    substance: str | None
    in_scope: bool
    matched_event_id: str | None
    headline_k: int | None
    headline_coef: float | None
    headline_ci: tuple[float, float] | None
    directional_hit: bool | None
    significant_hit: bool | None
    note: str


def _headline_k(study) -> int | None:
    post_ks = sorted(k for k in study.relative_years if k >= 0)
    return max(post_ks) if post_ks else None


def load_known_cases() -> list[dict]:
    with open(KNOWN_CASES_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)["cases"]


def check_case(case: dict, did_results_by_event_id: dict[str, EventDiDResult]) -> CaseCheck:
    in_scope = case["matches_register_event_id"] is not None
    if not in_scope:
        return CaseCheck(
            case_id=case["case_id"], substance=case["substance"], in_scope=False,
            matched_event_id=None, headline_k=None, headline_coef=None, headline_ci=None,
            directional_hit=None, significant_hit=None,
            note="out of scope for this project's chapters 28/29/38 panel -- see known_cases.yaml",
        )

    event_id = case["matches_register_event_id"]
    result = did_results_by_event_id.get(event_id)
    if result is None or result.status != "ok" or result.study is None:
        return CaseCheck(
            case_id=case["case_id"], substance=case["substance"], in_scope=True,
            matched_event_id=event_id, headline_k=None, headline_coef=None, headline_ci=None,
            directional_hit=None, significant_hit=None,
            note=f"register event {event_id} has no usable DiD result (status={getattr(result, 'status', 'missing')})",
        )

    k = _headline_k(result.study)
    if k is None:
        return CaseCheck(
            case_id=case["case_id"], substance=case["substance"], in_scope=True,
            matched_event_id=event_id, headline_k=None, headline_coef=None, headline_ci=None,
            directional_hit=None, significant_hit=None,
            note="no post-period relative year available in the event window",
        )

    coef, lo, hi = result.study.coef[k], result.study.ci_low[k], result.study.ci_high[k]
    expected_positive = case["expected_direction"] == "positive"
    directional_hit = (coef > 0) == expected_positive
    significant_hit = directional_hit and (lo > 0 or hi < 0)

    return CaseCheck(
        case_id=case["case_id"], substance=case["substance"], in_scope=True,
        matched_event_id=event_id, headline_k=k, headline_coef=coef, headline_ci=(lo, hi),
        directional_hit=directional_hit, significant_hit=significant_hit,
        note=(
            f"pipeline estimate at k=+{k}: {coef:+.3f} [{lo:+.3f}, {hi:+.3f}] -- "
            f"{'direction matches' if directional_hit else 'direction DOES NOT match'} the documented finding, "
            f"{'and is statistically significant' if significant_hit else 'but is not statistically significant at 95%'}"
        ),
    )


@dataclass
class RediscoverySummary:
    checks: list[CaseCheck]

    @property
    def in_scope_checks(self) -> list[CaseCheck]:
        return [c for c in self.checks if c.in_scope]

    @property
    def directional_recall(self) -> float | None:
        scored = [c for c in self.in_scope_checks if c.directional_hit is not None]
        if not scored:
            return None
        return sum(1 for c in scored if c.directional_hit) / len(scored)

    @property
    def significant_recall(self) -> float | None:
        scored = [c for c in self.in_scope_checks if c.significant_hit is not None]
        if not scored:
            return None
        return sum(1 for c in scored if c.significant_hit) / len(scored)

    def report(self) -> str:
        lines = ["=== STEP 5: Validation by rediscovery ==="]
        out_of_scope = [c for c in self.checks if not c.in_scope]
        if out_of_scope:
            lines.append(
                f"{len(out_of_scope)} documented episode type(s) in the brief are structurally out of scope "
                "for this project's chapters 28/29/38 panel and were NOT tested "
                f"({', '.join(c.case_id for c in out_of_scope)})."
            )
        lines.append(
            f"Directional recall (right sign): "
            f"{self.directional_recall:.0%}" if self.directional_recall is not None else "Directional recall: n/a"
        )
        lines.append(
            f"Significant recall (right sign AND 95% significant): "
            f"{self.significant_recall:.0%}" if self.significant_recall is not None else "Significant recall: n/a"
        )
        for c in self.checks:
            lines.append(f"  - {c.case_id}: {c.note}")
        return "\n".join(lines)


def run_rediscovery(did_results: list[EventDiDResult]) -> RediscoverySummary:
    by_id = {r.event.event_id: r for r in did_results}
    cases = load_known_cases()
    checks = [check_case(c, by_id) for c in cases]
    return RediscoverySummary(checks=checks)
