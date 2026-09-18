"""FIX 1 (causal-spec repair): the unit of treatment is (regulatory package
x HS6), not substance.

Three of the register's nine events (imidacloprid, clothianidin,
thiamethoxam) are companion regulations adopted the same day, banning the
same functional class, converging on the same HS6 code, taking effect the
same day -- they are not three independent natural experiments, they are
one experiment observed through three citation records. Same story for
chlorpyrifos and chlorpyrifos-methyl. Treating them as 8 independent
"events" silently triples/doubles their weight in any ranking or recall
count and manufactures false precision.

This module does NOT touch the register (data/register/events/*.yaml stays
exactly as it is -- the per-substance citations are real and worth keeping
individually) or the dashboard. It only builds a derived grouping, purely
in memory, for use by the analysis layer.

Grouping key: (jurisdiction, hs6, decision_date, effective_date). All four
matching is what "same regulatory package" means operationally here --
distinct decisions on the same HS6 (e.g. atrazine 2004 vs paraquat 2007,
both HS6 380830) are NOT collapsed, because they differ on date and were
not adopted as a joint package.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from displacement_observatory.register.schema import RestrictionEvent
from displacement_observatory.register.store import RegisterLoadResult


@dataclass(frozen=True)
class TreatmentPackage:
    package_id: str
    jurisdiction: str
    hs6: str
    decision_date: date
    effective_date: date
    substances: tuple[str, ...]
    event_ids: tuple[str, ...]
    restriction_types: tuple[str, ...]

    @property
    def decision_to_effective_days(self) -> int:
        return (self.effective_date - self.decision_date).days

    @property
    def is_multi_substance(self) -> bool:
        return len(self.substances) > 1


def _event_hs6(event: RestrictionEvent) -> str | None:
    """FIX 1 groups on a single HS6 per event, matching the current DiD
    engine's own assumption (diD.run_event_did rejects events with != 1
    hs6_candidate). An event with 0 or >1 candidates cannot be placed in a
    single-HS6 package and is returned as None so the caller can decide
    what to do with it, rather than silently guessing.
    """
    if len(event.hs6_candidates) != 1:
        return None
    return event.hs6_candidates[0].hs6


def build_treatment_packages(register: RegisterLoadResult) -> list[TreatmentPackage]:
    groups: dict[tuple[str, str, date, date], list[RestrictionEvent]] = {}
    unplaceable: list[RestrictionEvent] = []

    for event in register.events:
        hs6 = _event_hs6(event)
        if hs6 is None:
            unplaceable.append(event)
            continue
        key = (event.jurisdiction, hs6, event.decision_date, event.effective_date)
        groups.setdefault(key, []).append(event)

    if unplaceable:
        raise ValueError(
            f"{len(unplaceable)} register event(s) have != 1 hs6_candidate and cannot be placed in a "
            f"single-HS6 treatment package: {[e.event_id for e in unplaceable]}"
        )

    packages: list[TreatmentPackage] = []
    for (jurisdiction, hs6, decision_date, effective_date), events in sorted(
        groups.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][2])
    ):
        events_sorted = sorted(events, key=lambda e: e.event_id)
        package_id = (
            events_sorted[0].event_id
            if len(events_sorted) == 1
            else f"pkg-{jurisdiction.lower().replace(' ', '-')}-{hs6}-{decision_date.isoformat()}"
        )
        packages.append(
            TreatmentPackage(
                package_id=package_id,
                jurisdiction=jurisdiction,
                hs6=hs6,
                decision_date=decision_date,
                effective_date=effective_date,
                substances=tuple(e.substance for e in events_sorted),
                event_ids=tuple(e.event_id for e in events_sorted),
                restriction_types=tuple(sorted({e.restriction_type.value for e in events_sorted})),
            )
        )

    _assert_no_hs6_date_collision(packages)
    return packages


def _assert_no_hs6_date_collision(packages: list[TreatmentPackage]) -> None:
    """Two DISTINCT packages sharing both an HS6 and an effective_date would
    mean either a grouping bug in this module, or two genuinely independent
    regulatory actions that coincidentally landed on the same HS6 on the
    same day -- either way it needs a human, not a silent pass-through.
    """
    seen: dict[tuple[str, date], str] = {}
    for pkg in packages:
        key = (pkg.hs6, pkg.effective_date)
        if key in seen:
            raise AssertionError(
                f"packages {seen[key]!r} and {pkg.package_id!r} share HS6 {pkg.hs6} and effective_date "
                f"{pkg.effective_date} but were not collapsed into one package -- investigate before trusting "
                f"either as independent."
            )
        seen[key] = pkg.package_id
