from datetime import date

import numpy as np
import pandas as pd
import pytest

from displacement_observatory.analysis.staggered import fit_staggered, first_restriction_year
from displacement_observatory.register.schema import Citation, HS6Candidate, RestrictionEvent


def _event(event_id, hs6, effective_year, jurisdiction="EU"):
    return RestrictionEvent(
        event_id=event_id, substance="X", jurisdiction=jurisdiction, restriction_type="non-renewal", scope="all",
        decision_date=date(effective_year - 1, 1, 1), effective_date=date(effective_year, 1, 1),
        citation=Citation(source_document="d", source_clause="c", retrieved_at=date(2026, 9, 18)),
        hs6_candidates=[HS6Candidate(hs6=hs6, confidence=0.5, reasoning="r", imprecision="i")],
    )


def test_first_restriction_year_takes_the_earliest():
    events = [
        _event("a", "999999", 2018),
        _event("b", "999999", 2006),  # earlier -- should win
        _event("c", "999999", 2020),
        _event("d", "888888", 2004),
    ]
    result = first_restriction_year(events)
    assert result == {"999999": 2006, "888888": 2004}


def test_first_restriction_year_ignores_non_eu_jurisdiction():
    events = [_event("a", "999999", 2011, jurisdiction="Global")]
    result = first_restriction_year(events)
    assert result == {}


def _synthetic_hs6_panel(true_effect=0.5, seed=0, n_never=40, years=range(1995, 2025)):
    rng = np.random.default_rng(seed)
    rows = []
    year_fe = {t: rng.normal(0, 0.2) for t in years}
    for i in range(n_never):
        base = rng.normal(5, 1)
        for t in years:
            rows.append((f"never_{i}", t, base + year_fe[t] + rng.normal(0, 0.15), 0))
    base_a = rng.normal(5, 1)
    for t in years:
        v = base_a + year_fe[t] + rng.normal(0, 0.15)
        if t >= 2004:
            v += true_effect
        rows.append(("treated_a", t, v, 2004))
    base_b = rng.normal(5, 1)
    for t in years:
        v = base_b + year_fe[t] + rng.normal(0, 0.15)
        if t >= 2006:
            v += true_effect
        rows.append(("treated_b", t, v, 2006))
    return pd.DataFrame(rows, columns=["hs6", "year", "value", "gname"])


def test_did2s_recovers_known_effect_on_synthetic_two_cohort_panel():
    df = _synthetic_hs6_panel(true_effect=0.5, seed=1)
    result = fit_staggered(df, estimator="did2s")
    assert abs(result.coef - 0.5) < 0.15, result.coef
    assert result.n_treated_cohorts == 2
    assert result.n_never_treated == 40


def test_did2s_near_zero_effect():
    df = _synthetic_hs6_panel(true_effect=0.0, seed=2)
    result = fit_staggered(df, estimator="did2s")
    assert abs(result.coef) < 0.15, result.coef
