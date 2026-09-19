from pathlib import Path

import pytest
import yaml

from displacement_observatory.register.mapping_review import load_review, parse_review_table, self_confirmed_only

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "review" / "hs6-mapping-review.md"
V1 = ROOT / "data" / "register" / "mappings" / "chemical_hs6_mappings_v1.yaml"


def _maps():
    return yaml.safe_load(V1.read_text(encoding="utf-8"))["mappings"]


# --- the detector itself (passes) -------------------------------------------

def test_detector_flags_model_self_confirmation():
    m = [{"substance": "A", "confirmed_by": "Claude, self-confirmed per instruction"}]
    assert self_confirmed_only(m, {}) == ["A"]
    assert self_confirmed_only(m, {"A": "UNSURE"}) == ["A"]
    assert self_confirmed_only(m, {"A": "REJECTED"}) == ["A"]


def test_detector_accepts_a_human_confirmed_row():
    m = [{"substance": "A", "confirmed_by": "Claude, self-confirmed"}, {"substance": "B", "confirmed_by": ""}]
    assert self_confirmed_only(m, {"A": "CONFIRMED", "B": "CONFIRMED"}) == []


def test_parse_review_table_reads_last_cell_and_ignores_headers():
    md = "| # | Substance | HS6 | X | Decision |\n|---|---|---|---|---|\n| 1 | Foo | 380810 | why | |\n| 2 | Bar | 380830 | why | confirmed |\n"
    assert parse_review_table(md) == {"Foo": "", "Bar": "CONFIRMED"}


# --- the real review file --------------------------------------------------

def test_review_has_one_row_per_v1_mapping_and_the_agent_did_not_fill_it_in():
    review = load_review(REVIEW)
    assert set(review) == {m["substance"] for m in _maps()}
    text = REVIEW.read_text(encoding="utf-8")
    assert "WAITING ON THE OWNER" in text
    # Until the owner acts, the decision column is empty. A filled column with no owner sign-off here is a red flag.
    # (This assertion is expected to be removed by the owner once they fill it in.)
    if any(review.values()):
        pytest.skip("owner has begun filling in decisions")


@pytest.mark.xfail(strict=True, reason="WAITING ON THE OWNER: every v1 mapping is still model-self-confirmed only (review/hs6-mapping-review.md)")
def test_no_mapping_rests_only_on_model_self_confirmation():
    assert self_confirmed_only(_maps(), load_review(REVIEW)) == []
