"""Mechanical check: no document may state a clean-package count without
naming the estimation window it applies to.

The count of CLEAN treatment packages depends on the window (0 of 5 at
+-5 years, 1 of 5 at +-4 to +-2). Reporting a bare count would select a
window by the headline it gives. A "block" (paragraph, or one table row)
that contains a count-of-clean statement must also contain a window
reference (a "+-N" or the word "window").

Historical records (decisions/, reviews/) are exempt: they are dated
records of what was said at the time.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CHECKED = [
    "README.md", "PAPER.md", "PAPER-testability.md", "METHODS.md", "falsification.md", "CLAUDE.md",
]
CHECKED_GLOBS = ["src/displacement_observatory/dashboard/templates/*.html", "testability/*.md", "testability/cases/*.md"]

NUMBER = r"(?:\d+|zero|no|none|one|two|three|four|five)"
# "0 of 5 ... CLEAN", "zero clean", "1 clean", "no CLEAN package", "0 clean at"
COUNT_RE = re.compile(
    rf"\b{NUMBER}\b(?:\s+of\s+(?:the\s+|those\s+|these\s+)?{NUMBER})?(?:\s+\w+){{0,4}}?\s+(?:are\s+|is\s+)?clean\b",
    re.IGNORECASE,
)
WINDOW_RE = re.compile(r"±\s*\d|\+-\s*\d|\bwindow", re.IGNORECASE)


def blocks(text: str) -> list[str]:
    out: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        lines = para.split("\n")
        if any(l.lstrip().startswith("|") for l in lines):
            out.extend(l for l in lines if l.strip())
        else:
            out.append(para)
    return out


def find_bare_counts(text: str) -> list[str]:
    bad = []
    for b in blocks(text):
        if COUNT_RE.search(b) and not WINDOW_RE.search(b):
            bad.append(" ".join(b.split())[:160])
    return bad


def documents() -> list[Path]:
    paths = [ROOT / p for p in CHECKED if (ROOT / p).exists()]
    for g in CHECKED_GLOBS:
        paths.extend(sorted(ROOT.glob(g)))
    return paths


def check() -> list[str]:
    errors = []
    for p in documents():
        for snippet in find_bare_counts(p.read_text(encoding="utf-8")):
            errors.append(f"{p.relative_to(ROOT)}: clean count without a window: {snippet!r}")
    return errors


def main() -> int:
    errs = check()
    if errs:
        print("Window-band check FAILED:", *errs, sep="\n  - ", file=sys.stderr)
        return 1
    print("Window-band check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
