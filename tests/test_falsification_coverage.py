"""Mechanical CI enforcement: every claim tagged in README.md must have a
falsification.md entry, and vice versa. See CLAUDE.md rule 3 and
scripts/check_falsification_coverage.py.
"""

from scripts.check_falsification_coverage import check


def test_every_readme_claim_has_a_falsification_entry_and_vice_versa():
    errors = check()
    assert errors == [], "\n".join(errors)
