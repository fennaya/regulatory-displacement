"""Close-out check: per register event, the dates the register holds, the dates the package builder produced, and the
effective date the overlap audit actually consumed (PackageWindow.effective_date), then the clean count at each window.
Re-runs the existing overlap audit only; no estimation beyond what the audit already needs."""
import warnings

from displacement_observatory.analysis.diD import run_all
from displacement_observatory.analysis.overlap import build_overlap_matrix, classify_packages, compute_windows
from displacement_observatory.analysis.packages import build_treatment_packages
from displacement_observatory.db import connect
from displacement_observatory.register.store import load_events

warnings.filterwarnings("ignore")
reg = load_events(version=1)
pk = build_treatment_packages(reg)
by_event = {e: p for p in pk for e in p.event_ids}
con = connect(read_only=True)
did5 = {r.event.event_id: r for r in run_all(con, reg, window_years=5)}
w5 = {w.package_id: w for w in compute_windows(pk, did5)}
print(f"{'event':30} {'reg decision':12} {'reg effective':13} {'pkg effective':13} {'audit consumed':14}")
for e in reg.events:
    p = by_event[e.event_id]
    print(f"{e.event_id:30} {e.decision_date!s:12} {e.effective_date!s:13} {p.effective_date!s:13} {w5[p.package_id].effective_date!s:14}")
print()
for wy in (5, 4, 3, 2):
    did = {r.event.event_id: r for r in run_all(con, reg, window_years=wy)}
    ws = compute_windows(pk, did)
    aud = classify_packages(ws, build_overlap_matrix(pk, ws, did))
    tested = [a for a in aud if a.window.tested]
    clean = [a.package_id for a in tested if a.classification.value == "CLEAN"]
    print(f"window +-{wy}: tested={len(tested)} clean={len(clean)} {clean}")
    for a in aud:
        if a.overlaps and "endosulfan" in a.package_id:
            for f in a.overlaps: print("   ", a.package_id, a.classification.value, "overlap years", f.contaminated_years, "with", f.later_package_id)
