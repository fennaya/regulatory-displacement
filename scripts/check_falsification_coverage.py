"""Mechanical check: every `<!-- falsifiable: id -->` marker in README.md
must have a matching `## id` heading in falsification.md, and vice versa.

This is the enforcement for CLAUDE.md's falsification-register rule. It is
deliberately dumb (regex, not NLP): the convention is that a claim isn't
"in the falsification register" unless someone explicitly tagged it in
the README, and every tag must resolve. Mechanical, not a good intention.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
FALSIFICATION = ROOT / "falsification.md"

MARKER_RE = re.compile(r"<!--\s*falsifiable:\s*([a-z0-9][a-z0-9-]*)\s*-->")
HEADING_RE = re.compile(r"^##\s+([a-z0-9][a-z0-9-]*)\s*$", re.MULTILINE)


def check() -> list[str]:
    errors: list[str] = []

    if not README.exists():
        return [f"README not found at {README}"]
    if not FALSIFICATION.exists():
        return [f"falsification.md not found at {FALSIFICATION}"]

    readme_text = README.read_text(encoding="utf-8")
    falsification_text = FALSIFICATION.read_text(encoding="utf-8")

    marked_claims = MARKER_RE.findall(readme_text)
    registered_claims = set(HEADING_RE.findall(falsification_text))

    if not marked_claims:
        errors.append(
            "No <!-- falsifiable: <id> --> markers found in README.md. If the README makes any "
            "claims, they should be tagged; if it genuinely makes none, this check should be "
            "revisited, not silently left empty."
        )

    seen = set()
    for claim_id in marked_claims:
        if claim_id in seen:
            continue
        seen.add(claim_id)
        if claim_id not in registered_claims:
            errors.append(
                f"README.md marks claim '{claim_id}' as falsifiable, but falsification.md has no "
                f"'## {claim_id}' entry."
            )

    orphaned = registered_claims - seen
    for claim_id in sorted(orphaned):
        errors.append(
            f"falsification.md has an entry for '{claim_id}' that no README.md marker references -- "
            "either the claim was removed from the README without removing its entry, or the marker "
            "was never added."
        )

    return errors


def main() -> int:
    errors = check()
    if errors:
        print("Falsification coverage check FAILED:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("Falsification coverage check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
