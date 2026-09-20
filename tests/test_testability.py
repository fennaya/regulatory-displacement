import json
from datetime import date
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from testability.protocol import (
    Audit,
    ClaimKind,
    DisclosureRequest,
    EvidenceDirection,
    SourcedQuote,
    Verdict,
    detectable,
    elimination_effect,
    normalise,
    notified_share,
    share_needed_for_detection,
    verify_quote_in_source,
)

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "testability"


def _quote(text="q"):
    return SourcedQuote(text=text, speaker="s", source="src", source_date=date(2026, 1, 1), retrieved_at=date(2026, 1, 2))


def _empirical(**kw):
    base = dict(claim_id="x", quote=_quote(), kind=ClaimKind.EMPIRICAL, kind_reason="r",
                test_specification="spec", evidence_inventory="inv")
    base.update(kw)
    return Audit(**base)


# --- the real register ---------------------------------------------------

def _register():
    return yaml.safe_load((T / "register.yaml").read_text(encoding="utf-8"))


def test_real_register_validates_and_quotes_are_verbatim_in_stored_source():
    reg = _register()
    source = (T / "sources" / "case-001-ec-statement-to-danwatch.txt").read_text(encoding="utf-8")
    entries = reg["audits"] + reg["candidates"]
    assert len(reg["candidates"]) == 2 and len(reg["audits"]) == 2
    for e in entries:
        a = Audit.model_validate(e)
        assert verify_quote_in_source(a.quote.text, source), a.claim_id


def test_the_brief_paraphrase_is_not_verbatim_but_its_quoted_fragment_is():
    source = (T / "sources" / "case-001-ec-statement-to-danwatch.txt").read_text(encoding="utf-8")
    # the brief's quoted fragment is a genuine fragment of the statement
    assert verify_quote_in_source("would only penalise the EU chemical industry", source)
    # its gloss ("might shift production outside the EU") is not the Commission's wording
    assert not verify_quote_in_source("might shift production outside the EU", source)
    assert not verify_quote_in_source("shift production", source)


def test_pan_europe_reproduces_the_same_statement_and_the_relocation_paraphrase_verbatim():
    pan = (T / "sources" / "case-001-pan-europe.txt").read_text(encoding="utf-8")
    ceo = (T / "sources" / "case-001-ec-statement-to-danwatch.txt").read_text(encoding="utf-8")
    mechanism = ("a unilateral production and export ban in the EU would not guarantee an improvement in health and "
                 "environmental protection in affected countries, as it may push these countries to buy the same or worse "
                 "chemical pesticides from companies outside of the EU")
    assert verify_quote_in_source(mechanism, pan) and verify_quote_in_source(mechanism, ceo)  # two independent sources
    assert verify_quote_in_source("simply shift production outside the EU while penalising European companies", pan)
    # the relocation paraphrase is PAN's report; the CEO transcription of the full statement does not contain it
    assert not verify_quote_in_source("simply shift production", ceo)
    case = " ".join((T / "cases" / "case-001.md").read_text(encoding="utf-8").split())
    assert "TWO independent secondary sources" in case.split("## 1.")[0]
    assert "production is explicitly in scope" in case


def test_croplife_relocation_sentence_is_verbatim_in_stored_source_and_euronews_is_no_longer_cited():
    s = (T / "sources" / "case-001-croplife-europe-2023.txt").read_text(encoding="utf-8")
    assert verify_quote_in_source("Such a ban would likely result in manufacturing being exported from Europe to other regions in the world", s)
    assert "8, 2023" in s
    for f in ("PAPER.md", "PAPER-testability.md"):
        assert "Euronews" not in (ROOT / f).read_text(encoding="utf-8"), f
    assert "CropLife Europe" in (ROOT / "PAPER-testability.md").read_text(encoding="utf-8")


def test_published_notified_tonnage_figures_are_in_stored_source():
    s = (T / "sources" / "case-001-notified-tonnage-unearthed.txt").read_text(encoding="utf-8")
    assert "122,000 tonnes" in s and "81,600 tonnes" in s and "mixtures" in s


def test_case_001_verdict_and_disclosure_request_present():
    a = {e["claim_id"]: Audit.model_validate(e) for e in _register()["audits"]}
    c1 = a["001-C1-substitution"]
    assert c1.verdict == Verdict.UNTESTABLE_WITH_PUBLIC_DATA
    assert c1.disclosure_request and "tonnes actually exported (customs export declaration)" in c1.disclosure_request.fields
    assert a["001-C2-no-guarantee"].verdict == Verdict.NOT_AN_EMPIRICAL_CLAIM


def test_case_001_verdict_is_sharpened_and_source_status_is_prominent():
    reg = _register()
    c1 = next(e for e in reg["audits"] if e["claim_id"] == "001-C1-substitution")
    reason = " ".join(c1["verdict_reason"].split())
    assert "testable in principle" in reason.lower()
    assert "we know of no attempt" in reason
    assert "address a different claim" in reason
    assert "reversed" not in reason
    case = (T / "cases" / "case-001.md").read_text(encoding="utf-8")
    head = case.split("## 1.")[0]
    assert "SECONDARY TRANSCRIPTION" in head and "UNRETRIEVED" in head
    assert "address a different claim" in head
    # the stale premise that the notification data are not public must not survive
    assert "not public as a dataset" not in " ".join(c1["evidence_inventory"].split()).replace("'are not public as a dataset'", "")


def test_unretrieved_leads_are_labelled_and_not_candidates():
    reg = _register()
    assert reg["unretrieved_leads"] and all(x.startswith("UNRETRIEVED") for x in reg["unretrieved_leads"])
    assert not any("E-9-2023" in e["claim_id"] for e in reg["candidates"])
    assert (T / "sources" / "case-001-primary-source-attempts.txt").exists()


def test_arithmetic_json_matches_the_functions():
    j = json.loads((T / "cases" / "case-001-arithmetic.json").read_text())
    y = j["years"]["2018"]
    assert y["notified_share_of_eu_customs_tonnes"] == pytest.approx(notified_share(81_600, y["customs_tonnes_eu_to_non_eu_heading_3808"]))
    assert y["log_point_change_if_all_notified_tonnage_vanished"] == pytest.approx(elimination_effect(y["notified_share_of_eu_customs_tonnes"]))
    d = j["detection"]["chapter38_never_treated"]
    assert d["share_needed_for_detection"] == pytest.approx(share_needed_for_detection(d["se_proxy"]))
    # the claim in register.yaml: full elimination is below the detection threshold
    assert not detectable(y["log_point_change_if_all_notified_tonnage_vanished"], d["se_proxy"])


# --- the protocol's own guarantees ------------------------------------------

def test_protocol_can_vindicate_an_institution():
    a = _empirical(verdict=Verdict.TESTABLE_AND_TESTED, evidence_direction=EvidenceDirection.CLAIM_PROBABLY_CORRECT)
    assert a.evidence_direction == EvidenceDirection.CLAIM_PROBABLY_CORRECT


def test_tested_claim_must_state_direction_and_untested_must_not():
    with pytest.raises(ValidationError, match="direction"):
        _empirical(verdict=Verdict.TESTABLE_AND_TESTED)
    with pytest.raises(ValidationError, match="only a tested claim"):
        _empirical(verdict=Verdict.TESTABLE_BUT_UNTESTED, evidence_direction=EvidenceDirection.INCONCLUSIVE)


def test_untestable_needs_a_disclosure_request():
    with pytest.raises(ValidationError, match="disclosure"):
        _empirical(verdict=Verdict.UNTESTABLE_WITH_PUBLIC_DATA)
    ok = _empirical(
        verdict=Verdict.UNTESTABLE_WITH_PUBLIC_DATA,
        disclosure_request=DisclosureRequest(holder="h", fields=["f"], granularity="g", period="p"),
    )
    assert ok.verdict == Verdict.UNTESTABLE_WITH_PUBLIC_DATA


def test_value_judgement_only_gets_not_an_empirical_claim_and_skips_steps_2_to_5():
    with pytest.raises(ValidationError, match="value judgement"):
        _empirical(kind=ClaimKind.VALUE_JUDGEMENT, verdict=Verdict.TESTABLE_BUT_UNTESTED)
    with pytest.raises(ValidationError, match="does not proceed"):
        _empirical(kind=ClaimKind.VALUE_JUDGEMENT, verdict=Verdict.NOT_AN_EMPIRICAL_CLAIM)
    ok = Audit(claim_id="v", quote=_quote(), kind=ClaimKind.VALUE_JUDGEMENT, kind_reason="r",
               verdict=Verdict.NOT_AN_EMPIRICAL_CLAIM)
    assert ok.verdict == Verdict.NOT_AN_EMPIRICAL_CLAIM


def test_candidate_is_unworked():
    with pytest.raises(ValidationError, match="unworked"):
        Audit(claim_id="c", status="candidate", quote=_quote(), kind=ClaimKind.EMPIRICAL, kind_reason="r",
              verdict=Verdict.TESTABLE_BUT_UNTESTED)


def test_quote_needs_text_source_and_dates():
    with pytest.raises(ValidationError):
        SourcedQuote(text="", speaker="s", source="x", source_date=date(2026, 1, 1), retrieved_at=date(2026, 1, 1))
    with pytest.raises(ValidationError):
        SourcedQuote(text="t", speaker="s", source="x", retrieved_at=date(2026, 1, 1))


def test_verify_quote_normalises_whitespace_only():
    assert verify_quote_in_source("a  b\nc", "x a b c y")
    assert not verify_quote_in_source("a b d", "x a b c y")
    assert normalise(" a \n b ") == "a b"


def test_arithmetic_guards():
    with pytest.raises(ValueError):
        notified_share(1, 0)
    with pytest.raises(ValueError):
        elimination_effect(1.0)
    assert elimination_effect(0.5) == pytest.approx(-0.6931471805599453)
    assert detectable(-1.0, 0.1) and not detectable(-0.1, 0.1)
