"""STAGE G: power analysis -- the decisive stage.

Two pure, independently testable pieces:

1. compute_mde: minimum detectable effect at a given power, from a
   standard error, using the textbook two-sided-test formula. No
   estimation happens here; it's arithmetic on an SE this project already
   computed (Stage E's cluster-robust SE, the most defensible one
   produced so far).

2. implied_log_effect_if_fully_displaced: given an assumed share of a
   treated HS6 basket's trade value that the restricted substance
   represents, the log-point change the WHOLE basket would show if 100%
   of that substance's EU exports were displaced (added to the
   non-restricted-destination series that previously didn't contain
   them). Closed form: if the substance is share s of the basket and its
   full value shifts onto the observed series, the observed series
   scales by 1/(1-s), i.e. a log-point effect of -log(1-s). For small s
   this is approximately s itself.

Basket-share ASSUMPTIONS are recorded in BASKET_SHARE_ASSUMPTIONS below,
each with a stated confidence and basis -- some anchored to a real (if
inconsistent across sources) web search for global market value, most
NOT independently verified for this project and flagged as such. This is
exactly the "stating assumptions explicitly where not [available]" the
brief asks for, not hidden behind false precision.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def compute_mde(se: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """Two-sided test, standard textbook MDE formula: MDE = (z_{1-alpha/2}
    + z_{1-power}) * SE. Uses the same normal-quantile approach as
    analysis/twfe.py's own p-value calculation (math.erf-based inverse via
    a small lookup for the two power levels this project actually uses,
    rather than pulling in scipy.stats.norm.ppf for two constants).
    """
    z_alpha = _norm_ppf(1 - alpha / 2)
    z_power = _norm_ppf(power)
    return (z_alpha + z_power) * se


_Z_TABLE = {
    0.800: 0.8416212335729143,
    0.900: 1.2815515655446004,
    0.950: 1.6448536269514722,
    0.975: 1.9599639845400545,
    0.990: 2.3263478740408408,
}


def _norm_ppf(p: float) -> float:
    if p in _Z_TABLE:
        return _Z_TABLE[p]
    # Fallback: bisection on the erf-based CDF (analysis/twfe.py already
    # uses math.erf for the CDF direction; this inverts it) -- only
    # reached for a power/alpha combination outside the two this project
    # actually uses, so precision here matters less than not silently
    # returning a wrong table value.
    lo, hi = -10.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2
        cdf = 0.5 * (1 + math.erf(mid / math.sqrt(2)))
        if cdf < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def implied_log_effect_if_fully_displaced(substance_share: float) -> float:
    if not 0 <= substance_share < 1:
        raise ValueError(f"substance_share must be in [0, 1), got {substance_share}")
    return -math.log(1 - substance_share)


@dataclass
class BasketShareAssumption:
    package_id: str
    substance_label: str
    share_low: float
    share_high: float
    basis: str
    confidence: str


BASKET_SHARE_ASSUMPTIONS: list[BasketShareAssumption] = [
    BasketShareAssumption(
        package_id="pkg-eu-380810-2018-05-29",
        substance_label="Imidacloprid + Clothianidin + Thiamethoxam (combined)",
        share_low=0.10, share_high=0.30,
        basis=(
            "Imidacloprid alone: web search found global market value estimates ranging "
            "$1.07-1.55B (2024-2025) and $1.09B (2009) across market-research vendors whose "
            "methodologies were not reconciled here -- treated as an order-of-magnitude anchor, "
            "not a precise figure. Compared against this project's own computed world HS6 380810 "
            "trade value ($8.9B in 2017, $10.7B in 2019), imidacloprid alone implies roughly 10-15% "
            "of world HS6 380810 trade. The low-high range widens this to include clothianidin and "
            "thiamethoxam, the other two neonicotinoids in this package, without a separately "
            "verified figure for either."
        ),
        confidence="low-medium: one real anchor (imidacloprid), extrapolated for the other two without verification",
    ),
    BasketShareAssumption(
        package_id="pkg-eu-380810-2020-01-10",
        substance_label="Chlorpyrifos + Chlorpyrifos-methyl (combined)",
        share_low=0.05, share_high=0.20,
        basis="UNVERIFIED ASSUMPTION: no web search performed for this substance in this session. Range chosen as a generic 'major but not dominant organophosphate insecticide' placeholder based on general knowledge that chlorpyrifos was historically one of the most widely used organophosphates before its EU non-renewal, without a specific market-value figure.",
        confidence="low: no verification attempted",
    ),
    BasketShareAssumption(
        package_id="eu-2005-endosulfan",
        substance_label="Endosulfan",
        share_low=0.03, share_high=0.15,
        basis="UNVERIFIED ASSUMPTION: no web search performed. Range set lower than the other insecticides on the general (unverified) basis that endosulfan's global use was already declining by the mid-2000s ahead of its eventual Stockholm Convention POP listing in 2011.",
        confidence="low: no verification attempted",
    ),
    BasketShareAssumption(
        package_id="eu-2004-atrazine",
        substance_label="Atrazine",
        share_low=0.05, share_high=0.20,
        basis="UNVERIFIED ASSUMPTION: no web search performed for this session's power analysis specifically (though atrazine's EU export documentation is real, see the register). General knowledge that atrazine has historically been among the most widely used herbicides globally (particularly in the Americas) supports a non-trivial share, without a specific market-value figure.",
        confidence="low: no verification attempted",
    ),
    BasketShareAssumption(
        package_id="eu-2007-paraquat",
        substance_label="Paraquat",
        share_low=0.05, share_high=0.20,
        basis="UNVERIFIED ASSUMPTION: no web search performed for this session's power analysis specifically. General knowledge that paraquat has historically been among the world's top-selling herbicides by volume supports a non-trivial share, without a specific market-value figure.",
        confidence="low: no verification attempted",
    ),
]


@dataclass
class PowerVerdict:
    package_id: str
    se_used: float
    mde: float
    implied_effect_low: float
    implied_effect_high: float
    detectable_at_low_share: bool
    detectable_at_high_share: bool
    verdict: str


def evaluate_package(package_id: str, clustered_se: float, assumption: BasketShareAssumption) -> PowerVerdict:
    mde = compute_mde(clustered_se)
    eff_low = implied_log_effect_if_fully_displaced(assumption.share_low)
    eff_high = implied_log_effect_if_fully_displaced(assumption.share_high)
    det_low = eff_low > mde
    det_high = eff_high > mde

    if det_low and det_high:
        verdict = "DETECTABLE across the full assumed share range: even at the low end of the assumed basket share, full displacement would move the basket by more than the MDE."
    elif not det_low and not det_high:
        verdict = "NOT DETECTABLE across the full assumed share range: even 100% displacement at the high end of the assumed basket share would not move the basket by more than the MDE. This instrument cannot see an effect of this plausible size for this package."
    else:
        verdict = "BORDERLINE: detectable only if the true basket share is toward the high end of the assumed range -- the assumption's uncertainty, not just the estimator's, determines the answer here."

    return PowerVerdict(
        package_id=package_id, se_used=clustered_se, mde=mde,
        implied_effect_low=eff_low, implied_effect_high=eff_high,
        detectable_at_low_share=det_low, detectable_at_high_share=det_high,
        verdict=verdict,
    )
