"""Human-readable summaries of EventDiDResult, shared by the CLI and dashboard."""

from __future__ import annotations

from displacement_observatory.analysis.diD import EventDiDResult


def summarize_event(r: EventDiDResult) -> str:
    lines = [f"{r.event.event_id}: {r.event.substance} ({r.event.jurisdiction}), HS6={r.hs6}"]
    if r.status != "ok":
        lines.append(f"  SKIPPED: {r.reason}")
        return "\n".join(lines)

    s = r.study
    post_ks = sorted(k for k in s.relative_years if k >= 0)
    headline_k = max(post_ks) if post_ks else None
    if headline_k is not None:
        b, lo, hi = s.coef[headline_k], s.ci_low[headline_k], s.ci_high[headline_k]
        sig = "significant" if lo > 0 or hi < 0 else "not significant at 95%"
        lines.append(
            f"  effect at k=+{headline_k} (last available post-period year): "
            f"{b:+.3f} log points [{lo:+.3f}, {hi:+.3f}] -- {sig}"
        )
    lines.append(f"  pre-trend: {'FLAGGED' if s.pretrend_flagged else 'clean'} -- {s.pretrend_detail}")
    if r.same_hs6_contaminating_events:
        lines.append(
            f"  CAUTION: shares HS6 {r.hs6} with other register events within the window: "
            f"{r.same_hs6_contaminating_events} -- effect cannot be attributed to this substance alone"
        )
    lines.append(f"  n_control_units={r.n_control_units}, exporter_codes={len(r.exporter_codes)}")
    return "\n".join(lines)


def headline_eligible(r: EventDiDResult) -> tuple[bool, str]:
    """Per STEP 3: events with a failed pre-trend check are excluded from
    headline claims. Same-HS6 contamination is an additional, project-
    specific exclusion criterion for the same reason (can't attribute the
    effect to one substance).
    """
    if r.status != "ok":
        return False, r.reason or "skipped"
    if r.study.pretrend_flagged:
        return False, f"pre-trend check failed: {r.study.pretrend_detail}"
    if r.same_hs6_contaminating_events:
        return False, f"HS6 {r.hs6} shared with concurrent event(s) {r.same_hs6_contaminating_events}"
    return True, "eligible"
