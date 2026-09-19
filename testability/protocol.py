"""Testability audit protocol: the data model and the checks that make it
repeatable, not advocacy.

An audit takes an institution's stated justification and returns a
structured verdict on whether the empirical claim inside it can be tested
with public data. Six steps (see METHOD.md):

  1 claim extraction   2 test specification   3 evidence inventory
  4 power verdict      5 disclosure gap       6 verdict

Design constraints enforced in code, not left to good intentions:
  - A quote is verbatim, with a source and a date; the model refuses an
    empty quote or a missing source/date, and `verify_quote_in_source`
    checks a quote against stored source text.
  - A claim that is not empirical never proceeds to steps 2-5.
  - "TESTABLE AND TESTED" must carry an evidence direction, and that
    direction may be CLAIM_PROBABLY_CORRECT. The protocol can vindicate an
    institution; if it could only ever find fault it would be advocacy.
  - "UNTESTABLE WITH PUBLIC DATA" must carry a concrete disclosure request,
    so an untestable verdict is never a dead end.
No statistic is computed by a model: arithmetic here is deterministic and
imported from analysis/power.py.
"""

from __future__ import annotations

import math
from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, model_validator

from displacement_observatory.analysis.power import compute_mde


class ClaimKind(str, Enum):
    EMPIRICAL = "empirical"
    VALUE_JUDGEMENT = "value_judgement"
    PREDICTION = "prediction"  # empirical in form, about a counterfactual or the future


class Verdict(str, Enum):
    TESTABLE_AND_TESTED = "TESTABLE AND TESTED"
    TESTABLE_BUT_UNTESTED = "TESTABLE BUT UNTESTED"
    UNTESTABLE_WITH_PUBLIC_DATA = "UNTESTABLE WITH PUBLIC DATA"
    NOT_AN_EMPIRICAL_CLAIM = "NOT AN EMPIRICAL CLAIM"


class EvidenceDirection(str, Enum):
    CLAIM_PROBABLY_CORRECT = "claim probably correct"
    CLAIM_PROBABLY_WRONG = "claim probably wrong"
    INCONCLUSIVE = "inconclusive"


class SourcedQuote(BaseModel):
    text: str = Field(min_length=1)
    speaker: str = Field(min_length=1)
    source: str = Field(min_length=1)
    source_date: date
    url: str | None = None
    retrieved_at: date
    note: str | None = None  # e.g. "statement date not given in the source"


class DisclosureRequest(BaseModel):
    holder: str
    fields: list[str] = Field(min_length=1)
    granularity: str
    period: str


class Audit(BaseModel):
    claim_id: str
    status: str = "worked"  # "worked" | "candidate"
    quote: SourcedQuote
    kind: ClaimKind
    kind_reason: str
    test_specification: str | None = None
    decision_relevant_effect: str | None = None
    evidence_inventory: str | None = None
    power_verdict: str | None = None
    disclosure_request: DisclosureRequest | None = None
    verdict: Verdict | None = None
    evidence_direction: EvidenceDirection | None = None
    verdict_reason: str | None = None

    @model_validator(mode="after")
    def _enforce_protocol(self):
        if self.status == "candidate":
            if any([self.test_specification, self.power_verdict, self.verdict, self.evidence_direction]):
                raise ValueError("a candidate is unworked: no test spec, power verdict, or verdict yet")
            return self
        if self.verdict is None:
            raise ValueError("a worked audit needs a verdict")
        if self.kind == ClaimKind.VALUE_JUDGEMENT and self.verdict != Verdict.NOT_AN_EMPIRICAL_CLAIM:
            raise ValueError("a value judgement can only receive NOT AN EMPIRICAL CLAIM")
        if self.verdict == Verdict.NOT_AN_EMPIRICAL_CLAIM:
            if any([self.test_specification, self.evidence_inventory, self.power_verdict, self.disclosure_request]):
                raise ValueError("a non-empirical claim does not proceed to steps 2-5")
        else:
            if not self.test_specification:
                raise ValueError("an empirical claim needs a test specification (step 2)")
            if not self.evidence_inventory:
                raise ValueError("an empirical claim needs an evidence inventory (step 3)")
        if self.verdict == Verdict.TESTABLE_AND_TESTED and self.evidence_direction is None:
            raise ValueError("TESTABLE AND TESTED must state the direction of the evidence")
        if self.verdict != Verdict.TESTABLE_AND_TESTED and self.evidence_direction is not None:
            raise ValueError("only a tested claim has an evidence direction")
        if self.verdict == Verdict.UNTESTABLE_WITH_PUBLIC_DATA and self.disclosure_request is None:
            raise ValueError("UNTESTABLE WITH PUBLIC DATA must name the disclosure that would make it testable")
        return self


def normalise(s: str) -> str:
    return " ".join(s.split())


def verify_quote_in_source(quote: str, source_text: str) -> bool:
    """True if the quote appears verbatim in the stored source text
    (whitespace-normalised; nothing else is forgiven)."""
    return normalise(quote) in normalise(source_text)


# --- step 4 arithmetic (deterministic) ---------------------------------

def notified_share(notified_tonnes: float, customs_tonnes: float) -> float:
    """Notified tonnage as a share of customs-recorded tonnage. The two are
    different instruments (intended exports of mixtures vs recorded
    shipments); the ratio is an order-of-magnitude anchor, not an
    identity."""
    if customs_tonnes <= 0:
        raise ValueError("customs_tonnes must be positive")
    return notified_tonnes / customs_tonnes


def elimination_effect(share: float) -> float:
    """Log-point change in a basket if `share` of it disappears entirely:
    log(1 - share). Negative."""
    if not 0 <= share < 1:
        raise ValueError("share must be in [0, 1)")
    return math.log(1 - share)


def detectable(effect_log_points: float, se: float, alpha: float = 0.05, power: float = 0.80) -> bool:
    return abs(effect_log_points) > compute_mde(se, alpha, power)


def share_needed_for_detection(se: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """Smallest share of a basket whose full elimination (or full
    displacement) an estimator with standard error `se` detects at the
    stated power."""
    return 1 - math.exp(-compute_mde(se, alpha, power))
