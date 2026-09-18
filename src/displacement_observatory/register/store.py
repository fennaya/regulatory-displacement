"""Load and validate the restriction event register.

A record that fails schema validation (most importantly: missing citation)
is dropped rather than raising, and reported back to the caller -- per
project rule, an uncited record is not part of the register.
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from displacement_observatory.register.schema import RestrictionEvent

EVENTS_DIR = Path(__file__).resolve().parents[3] / "data" / "register" / "events"


class RegisterLoadResult:
    def __init__(self, events: list[RestrictionEvent], dropped: list[tuple[dict, str]]):
        self.events = events
        self.dropped = dropped  # (raw_record, reason)


def load_events(version: int = 1) -> RegisterLoadResult:
    path = EVENTS_DIR / f"events_v{version}.yaml"
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    events: list[RestrictionEvent] = []
    dropped: list[tuple[dict, str]] = []
    for record in raw.get("events", []):
        try:
            events.append(RestrictionEvent.model_validate(record))
        except ValidationError as e:
            dropped.append((record, str(e)))

    return RegisterLoadResult(events=events, dropped=dropped)


def events_by_hs6(result: RegisterLoadResult) -> dict[str, list[RestrictionEvent]]:
    by_hs6: dict[str, list[RestrictionEvent]] = {}
    for event in result.events:
        for cand in event.hs6_candidates:
            by_hs6.setdefault(cand.hs6, []).append(event)
    return by_hs6
