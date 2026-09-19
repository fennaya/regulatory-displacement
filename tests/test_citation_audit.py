import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "PAPER.md"
AUDIT = ROOT / "reviews" / "citation-audit.md"

NAME = r"[A-Z][A-Za-z'’\-]+"
# "Copeland and Taylor (1994)", "Ederington, Levinson and Minier (2005)", "Santos Silva and Tenreyro (2006)"
CITE_RE = re.compile(rf"((?:{NAME})(?:(?:,\s*|\s+and\s+|\s+){NAME})*)\s*\(((?:19|20)\d\d)\)")


def paper_citation_keys(text: str) -> set[str]:
    # drop code spans so a path or a function name is not read as a citation
    text = re.sub(r"`[^`]*`", "", text)
    keys = set()
    for names, year in CITE_RE.findall(text):
        # the first capitalised word of the citation is its first author; strip lead-in words like "Copeland"
        first = re.findall(NAME, names)
        keys.add((tuple(first), year))
    return keys


def _first_author(words: list[str]) -> str:
    # a match can begin with a sentence-initial word ("On", "Bown"); use the words as written and
    # compare against the audit's keys, which are surname-year. Try each word as a candidate surname.
    return words[0]


def verified_keys() -> set[str]:
    out = set()
    for line in AUDIT.read_text(encoding="utf-8").splitlines():
        m = re.match(r"CITE:\s*(\S+)-(\d{4})\s*\|\s*FINAL:\s*(\w+)", line)
        if m and m.group(3) == "VERIFIED":
            out.add(f"{m.group(1)}-{m.group(2)}")
    return out


def test_every_citation_in_paper_has_a_verified_audit_entry():
    ver = verified_keys()
    cites = paper_citation_keys(PAPER.read_text(encoding="utf-8"))
    assert cites, "no citations detected in PAPER.md; the detector is broken or the paper lost its literature section"
    missing = []
    for words, year in cites:
        # any word of the matched author list may be the audit key's surname (a sentence can start "On Bown ...")
        if not any(f"{w}-{year}" in ver for w in words):
            missing.append((" ".join(words), year))
    assert not missing, f"citations with no VERIFIED audit entry: {missing}"


def test_detector_catches_an_unaudited_citation():
    fake = "As shown by Nonexistent and Author (2019), effects are large."
    cites = paper_citation_keys(fake)
    assert cites and not any(f"{w}-{y}" in verified_keys() for ws, y in cites for w in ws)


def test_the_eight_audited_citations_are_all_detected_in_the_paper():
    text = PAPER.read_text(encoding="utf-8")
    found = {f"{w}-{y}" for ws, y in paper_citation_keys(text) for w in ws}
    for k in ["Copeland-1994", "Ederington-2005", "Levinson-2008", "Bown-2007", "Gardner-2022", "Santos-2006", "Callaway-2021", "Borusyak-2024"]:
        assert k in found, k
