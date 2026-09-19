from scripts.check_window_band import check, documents, find_bare_counts


def test_bare_counts_are_flagged():
    for s in [
        "0 of 5 testable packages are CLEAN.",
        "Zero of the five packages are clean.",
        "State the size as 6 packages (5 testable, 0 clean).",
        "There is 1 clean package.",
        "| A | overlap audit | 0 of 5 are CLEAN |",
    ]:
        assert find_bare_counts(s), s


def test_counts_with_a_window_are_accepted():
    for s in [
        "0 of 5 packages are CLEAN at the ±5-year window.",
        "1 clean at ±4 (endosulfan), 0 clean at ±5.",
        "Zero of the five are CLEAN under the pre-set window.",
    ]:
        assert not find_bare_counts(s), s


def test_a_table_row_cannot_borrow_a_window_from_another_row():
    table = "| A | 0 of 5 are CLEAN |\n| B | results at ±5 years |"
    assert find_bare_counts(table)


def test_classification_labels_and_prose_are_not_counts():
    for s in [
        "Classify CLEAN / CONTAMINATED / UNTESTABLE as a first-class column.",
        "assert a CLEAN classification never coexists with a recorded overlap",
        "A CLEAN package is far too underpowered to test the hypothesis.",
    ]:
        assert not find_bare_counts(s), s


def test_documents_are_actually_scanned():
    names = {p.name for p in documents()}
    assert {"README.md", "PAPER.md", "METHODS.md", "falsification.md", "findings.html"} <= names


def test_no_document_states_a_bare_clean_count():
    assert check() == []
