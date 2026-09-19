"""Multiple-comparisons ledger for Stages A-H (and Part 1 of the attack).

Two kinds of entries:
  - LIVE: re-estimated by scripts/spec_ledger.py from the repo's own code,
    so whether the 95% CI excludes zero is computed, not remembered.
  - DISCARDED: specifications that were run during the session and then
    thrown away (a scale error, a window bug). They cannot be re-run from
    the final code by construction; they are recorded by hand with the
    reason, and the ledger says so. The count is therefore a reconstruction
    from the working history, not an audit log, and is a lower bound if
    anything was tried and not recorded.

The chance arithmetic treats tests as independent, which they are not (all
draw on the same BACI panel and overlapping rows). Independence overstates
the effective number of tests, so this is an upper-side bound on the
number of chance clears, reported as such.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class LedgerEntry:
    stage: str
    description: str
    n_estimates: int
    n_ci_excludes_zero: int
    kind: str  # "live" | "discarded"
    note: str = ""


def expected_chance_clears(n_tests: int, alpha: float = 0.05) -> float:
    return n_tests * alpha


def prob_at_least_k_clears(n_tests: int, k: int, alpha: float = 0.05) -> float:
    """P(X >= k), X ~ Binomial(n_tests, alpha)."""
    if k <= 0:
        return 1.0
    return sum(math.comb(n_tests, i) * alpha ** i * (1 - alpha) ** (n_tests - i) for i in range(k, n_tests + 1))


def summarize(entries: list[LedgerEntry], alpha: float = 0.05) -> dict:
    n = sum(e.n_estimates for e in entries)
    k = sum(e.n_ci_excludes_zero for e in entries)
    return {
        "n_estimates": n,
        "n_ci_excludes_zero": k,
        "share_clearing": k / n if n else 0.0,
        "expected_chance_clears": expected_chance_clears(n, alpha),
        "prob_at_least_observed_if_all_null_independent": prob_at_least_k_clears(n, k, alpha),
        "prob_at_least_one_clear_if_all_null_independent": 1 - (1 - alpha) ** n,
        "n_live": sum(e.n_estimates for e in entries if e.kind == "live"),
        "n_discarded": sum(e.n_estimates for e in entries if e.kind == "discarded"),
    }


DISCARDED_ENTRIES: list[LedgerEntry] = [
    LedgerEntry(
        "Stage 3 (bug)", "chlorpyrifos k=+5 in a window that ran past the panel's last year (2025 read as zero trade)",
        1, 1, "discarded",
        "coef -4.51, CI [-7.99, -1.03]; a data artifact, fixed by clipping windows to panel coverage",
    ),
    LedgerEntry(
        "Stage B.2 (scale error)", "pooled staggered TWFE and did2s on RAW value_kusd (levels), not log",
        2, 2, "discarded",
        "coef ~ +4.7e5 (thousand USD); not comparable to the log-point specs, redone on log1p",
    ),
]
