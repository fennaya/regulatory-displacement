import math

import pytest

from displacement_observatory.analysis.spec_ledger import (
    LedgerEntry,
    expected_chance_clears,
    prob_at_least_k_clears,
    summarize,
)


def test_expected_chance_clears():
    assert expected_chance_clears(40, 0.05) == pytest.approx(2.0)


def test_prob_at_least_k_known_values():
    # P(X>=1), n=20, p=.05 = 1 - .95^20
    assert prob_at_least_k_clears(20, 1) == pytest.approx(1 - 0.95 ** 20)
    assert prob_at_least_k_clears(10, 0) == 1.0
    # sums to 1 over all k for a tiny n
    assert sum(math.comb(3, i) * 0.05 ** i * 0.95 ** (3 - i) for i in range(4)) == pytest.approx(1.0)
    assert prob_at_least_k_clears(3, 4) == 0.0


def test_summarize_totals_and_split():
    entries = [
        LedgerEntry("a", "x", 10, 1, "live"),
        LedgerEntry("b", "y", 5, 2, "discarded"),
    ]
    s = summarize(entries)
    assert s["n_estimates"] == 15 and s["n_ci_excludes_zero"] == 3
    assert s["n_live"] == 10 and s["n_discarded"] == 5
    assert s["expected_chance_clears"] == pytest.approx(0.75)
    assert s["prob_at_least_one_clear_if_all_null_independent"] == pytest.approx(1 - 0.95 ** 15)
