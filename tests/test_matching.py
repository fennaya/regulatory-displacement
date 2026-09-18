from displacement_observatory.analysis.matching import select_matched_controls

EXPORTER = 251  # France
IMPORTER = 842  # USA

PRE_YEARS = [2010, 2011, 2012, 2013, 2014]


def _insert(con, hs6, values_by_year):
    rows = [
        (y, hs6, EXPORTER, IMPORTER, v, None, "BACI", "t", "2026-09-18 00:00:00")
        for y, v in values_by_year.items()
    ]
    con.executemany("INSERT INTO trade_flows VALUES (?,?,?,?,?,?,?,?,?)", rows)


def test_volume_filter_excludes_wrong_order_of_magnitude(con):
    treated = "380810"
    _insert(con, treated, {y: 1000.0 for y in PRE_YEARS})  # ~1e3 scale
    close_control = "380820"
    _insert(con, close_control, {y: 3000.0 for y in PRE_YEARS})  # same order of magnitude
    far_control = "380830"
    _insert(con, far_control, {y: 100_000_000.0 for y in PRE_YEARS})  # 5 orders of magnitude bigger

    stats = select_matched_controls(con, treated, [close_control, far_control], [EXPORTER], PRE_YEARS)

    assert close_control in stats.matched_hs6
    assert far_control not in stats.matched_hs6
    assert stats.n_after_volume_filter == 1


def test_trend_filter_excludes_diverging_pretrend(con):
    treated = "380810"
    _insert(con, treated, {y: 1000.0 for y in PRE_YEARS})  # flat
    flat_control = "380820"
    _insert(con, flat_control, {y: 1000.0 for y in PRE_YEARS})  # flat, matches
    growing_control = "380830"
    _insert(con, growing_control, {2010: 200.0, 2011: 500.0, 2012: 1200.0, 2013: 3000.0, 2014: 8000.0})  # steep growth

    stats = select_matched_controls(con, treated, [flat_control, growing_control], [EXPORTER], PRE_YEARS)

    assert flat_control in stats.matched_hs6
    assert growing_control not in stats.matched_hs6


def test_different_chapter_never_considered(con):
    treated = "380810"  # chapter 38
    _insert(con, treated, {y: 1000.0 for y in PRE_YEARS})
    other_chapter = "290110"  # chapter 29, same volume/trend otherwise
    _insert(con, other_chapter, {y: 1000.0 for y in PRE_YEARS})

    stats = select_matched_controls(con, treated, [other_chapter], [EXPORTER], PRE_YEARS)

    assert stats.n_candidates_same_chapter == 0
    assert other_chapter not in stats.matched_hs6


def test_balance_stats_close_to_treated(con):
    treated = "380810"
    _insert(con, treated, {y: 1000.0 for y in PRE_YEARS})
    for i, v in enumerate([900.0, 1100.0, 950.0, 1050.0]):
        _insert(con, f"38089{i}", {y: v for y in PRE_YEARS})

    stats = select_matched_controls(con, treated, [f"38089{i}" for i in range(4)], [EXPORTER], PRE_YEARS)

    assert len(stats.matched_hs6) == 4
    assert abs(stats.matched_mean_log10_volume - stats.treated_log10_volume) < 0.1
