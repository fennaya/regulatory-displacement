"""STAGE A: treatment overlap audit.

FIX 1 collapsed 9 register events into 6 treatment packages (5 testable).
That fixed double/triple-counting the same experiment. It did NOT fix a
separate problem: packages that share an HS6 code have their estimation
windows built from the SAME trade series, so if two same-HS6 packages'
windows overlap in calendar time, each one's "control-vs-treated gap" is
partly explained by the OTHER event, not by itself. This module makes that
overlap explicit rather than leaving it implicit in the DiD output.

A package's window is read off its own already-computed EventStudyResult
(the actual, panel-coverage-clipped relative years), not re-derived from
window_years, so this audit can never silently disagree with what the
estimator actually used.

An UNTESTABLE package (no DiD result at all, e.g. no single exporter bloc)
has no window of its own -- but its effective_date is still a real
calendar event, and can still land inside ANOTHER package's window. That
is checked too (as a single-point, not an interval), because a real
regulatory shock does not stop existing just because this project could
not build an exporter-side estimate of it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from displacement_observatory.analysis.diD import EventDiDResult
from displacement_observatory.analysis.packages import TreatmentPackage


class Classification(str, Enum):
    CLEAN = "CLEAN"
    CONTAMINATED = "CONTAMINATED"
    UNTESTABLE = "UNTESTABLE"


@dataclass
class PackageWindow:
    package_id: str
    hs6: str
    effective_date: date
    tested: bool
    y0: int | None  # None if untestable
    y1: int | None


@dataclass
class OverlapFlag:
    earlier_package_id: str
    later_package_id: str
    hs6: str
    earlier_window: tuple[int, int]
    later_effective_year: int
    contaminated_years: list[int]  # earlier package's post-period (k>=0) years >= later's effective year
    contaminated_post_period_ks: list[int]
    total_post_period_ks: int

    @property
    def contamination_share(self) -> float:
        return len(self.contaminated_post_period_ks) / self.total_post_period_ks if self.total_post_period_ks else 0.0


@dataclass
class PackageAudit:
    package_id: str
    classification: Classification
    window: PackageWindow
    overlaps: list[OverlapFlag]


def compute_windows(packages: list[TreatmentPackage], did_by_event_id: dict[str, EventDiDResult]) -> list[PackageWindow]:
    windows = []
    for p in packages:
        rep = did_by_event_id[p.event_ids[0]]
        if rep.status != "ok" or rep.study is None:
            windows.append(PackageWindow(p.package_id, p.hs6, p.effective_date, tested=False, y0=None, y1=None))
            continue
        ks = sorted(rep.study.relative_years)
        y0 = p.effective_date.year + ks[0]
        y1 = p.effective_date.year + ks[-1]
        windows.append(PackageWindow(p.package_id, p.hs6, p.effective_date, tested=True, y0=y0, y1=y1))
    return windows


def _post_period_ks(did_by_event_id: dict[str, EventDiDResult], event_id: str) -> list[int]:
    result = did_by_event_id[event_id]
    return sorted(k for k in result.study.relative_years if k >= 0)


def build_overlap_matrix(
    packages: list[TreatmentPackage],
    windows: list[PackageWindow],
    did_by_event_id: dict[str, EventDiDResult],
) -> list[OverlapFlag]:
    by_id = {p.package_id: p for p in packages}
    flags: list[OverlapFlag] = []

    for i, a in enumerate(windows):
        for b in windows[i + 1:]:
            if a.hs6 != b.hs6:
                continue

            # Order by effective_date: "earlier" is whichever's effective_date comes first.
            earlier, later = (a, b) if a.effective_date <= b.effective_date else (b, a)

            if not earlier.tested:
                continue  # can't compute post-period contamination for an untestable "earlier" package

            overlaps = False
            if later.tested:
                overlaps = earlier.y0 <= later.y1 and later.y0 <= earlier.y1
            else:
                # untestable "later" package: treat its effective_date year as a single point
                overlaps = earlier.y0 <= later.effective_date.year <= earlier.y1

            if not overlaps:
                continue

            earlier_pkg = by_id[earlier.package_id]
            post_ks = _post_period_ks(did_by_event_id, earlier_pkg.event_ids[0])
            later_year = later.effective_date.year
            contaminated_ks = [k for k in post_ks if (earlier.effective_date.year + k) >= later_year]
            contaminated_years = [earlier.effective_date.year + k for k in contaminated_ks]

            flags.append(
                OverlapFlag(
                    earlier_package_id=earlier.package_id,
                    later_package_id=later.package_id,
                    hs6=a.hs6,
                    earlier_window=(earlier.y0, earlier.y1),
                    later_effective_year=later_year,
                    contaminated_years=contaminated_years,
                    contaminated_post_period_ks=contaminated_ks,
                    total_post_period_ks=len(post_ks),
                )
            )
    return flags


def classify_packages(windows: list[PackageWindow], flags: list[OverlapFlag]) -> list[PackageAudit]:
    involved = {f.earlier_package_id for f in flags} | {f.later_package_id for f in flags}
    audits = []
    for w in windows:
        pkg_flags = [f for f in flags if w.package_id in (f.earlier_package_id, f.later_package_id)]
        if not w.tested:
            classification = Classification.UNTESTABLE
        elif w.package_id in involved:
            classification = Classification.CONTAMINATED
        else:
            classification = Classification.CLEAN
        audits.append(PackageAudit(package_id=w.package_id, classification=classification, window=w, overlaps=pkg_flags))

    _assert_clean_has_no_overlap(audits)
    return audits


def _assert_clean_has_no_overlap(audits: list[PackageAudit]) -> None:
    for a in audits:
        if a.classification == Classification.CLEAN and a.overlaps:
            raise AssertionError(
                f"package {a.package_id!r} is classified CLEAN but has {len(a.overlaps)} recorded overlap(s) -- "
                "classification logic is inconsistent with the overlap matrix."
            )
