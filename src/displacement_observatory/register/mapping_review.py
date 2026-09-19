"""Provenance gate for the substance -> HS6 mappings (close-out step 6).

A mapping's provenance is sound only if a HUMAN decision of CONFIRMED is
recorded for it in review/hs6-mapping-review.md. A `confirmed: true` written
by the model that proposed the mapping is model self-confirmation and does not
count. This module reads the review table; it never writes a decision.
"""

from __future__ import annotations

import re
from pathlib import Path

VALID = {"CONFIRMED", "REJECTED", "UNSURE"}
SELF_CONFIRM_MARKERS = ("claude", "self-confirmed", "model", "llm")


def parse_review_table(md_text: str) -> dict[str, str]:
    """substance -> decision ('' if the column is empty). Rows look like
    | n | Substance | HS6 | ... | DECISION |, decision is the last cell."""
    out: dict[str, str] = {}
    for line in md_text.splitlines():
        if not line.startswith("|") or set(line.replace("|", "").strip()) <= set("-: "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not cells[0].isdigit():
            continue
        out[cells[1]] = cells[-1].upper()
    return out


def self_confirmed_only(mappings: list[dict], review: dict[str, str]) -> list[str]:
    """Substances whose only provenance is model self-confirmation: no human
    CONFIRMED decision in the review, and any confirmed_by that names the model."""
    bad = []
    for m in mappings:
        human_ok = review.get(m["substance"], "") == "CONFIRMED"
        by = str(m.get("confirmed_by", "")).lower()
        model_only = (not by) or any(k in by for k in SELF_CONFIRM_MARKERS)
        if model_only and not human_ok:
            bad.append(m["substance"])
    return bad


def load_review(path: Path) -> dict[str, str]:
    return parse_review_table(path.read_text(encoding="utf-8"))
