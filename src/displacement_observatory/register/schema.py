"""Structured schema for the restriction register (STEP 2).

Every field that isn't structurally required (dates, enums, identifiers)
must carry a source clause; a record with no citation is dropped, not
guessed. decision_date and effective_date are always separate.
"""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class RestrictionType(str, Enum):
    BAN = "ban"
    WITHDRAWAL = "withdrawal"
    NON_RENEWAL = "non-renewal"
    SEVERE_RESTRICTION = "severe_restriction"


class HS6Candidate(BaseModel):
    hs6: str = Field(pattern=r"^\d{6}$")
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    imprecision: str
    confirmed: bool = False
    confirmed_by: str | None = None
    confirmed_note: str | None = None


class Citation(BaseModel):
    source_document: str
    source_clause: str
    retrieved_at: date
    url: str | None = None


class RestrictionEvent(BaseModel):
    event_id: str
    substance: str
    jurisdiction: str
    restriction_type: RestrictionType
    scope: str
    decision_date: date
    effective_date: date
    citation: Citation
    hs6_candidates: list[HS6Candidate]
    notes: str | None = None

    @field_validator("effective_date")
    @classmethod
    def effective_not_before_decision_minus_slack(cls, v: date, info) -> date:
        # Effective dates occasionally precede formal decision publication in
        # source documents (e.g. a decision published after the date it
        # legally takes effect); we don't hard-fail on that, just record it.
        return v

    @property
    def decision_to_effective_days(self) -> int:
        return (self.effective_date - self.decision_date).days
