"""BR-32 to BR-38, BR-41: style changeovers, with hand-checked counts (AC-33 logic, AC-34, AC-35, AC-36)."""

from datetime import date
from decimal import Decimal

from backend.features.sewing_productivity.business.changeover_business import ChangeoverBusiness
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.models.settings_records import WeeklyChangeover
from backend.features.sewing_productivity.tests.workbook_factory import clean_row

business = ChangeoverBusiness()
OCT_1, OCT_31 = date(2026, 10, 1), date(2026, 10, 31)


def test_br32_order_first_seen_before_the_period_is_not_counted() -> None:
    rows = [clean_row(date(2026, 9, 30), po="OLD"), clean_row(date(2026, 10, 2), po="OLD")]
    assert business.kpi_rows(rows, OCT_1, OCT_31) == []


def test_br32_order_first_seen_in_the_period_counts_each_pair_once() -> None:
    rows = [
        clean_row(date(2026, 10, 2), po="A", smv="10", price="1"),
        clean_row(date(2026, 10, 3), po="A", smv="10", price="1"),  # same pair, same order
        clean_row(date(2026, 10, 4), po="B", smv="10", price="1"),  # same pair, another order
        clean_row(date(2026, 10, 5), po="D", smv="10", price="2"),  # new pair
        clean_row(date(2026, 10, 6), po="C", smv="12", price="1"),  # new pair
    ]
    counted = business.kpi_rows(rows, OCT_1, OCT_31)
    assert [(row.production_date.day, row.base_po) for row in counted] == [(2, "A"), (5, "D"), (6, "C")]


def test_br32_only_the_first_day_of_an_order_counts() -> None:
    # regression: the KPI file reads the pair on the order's first day, so a later SMV correction is no changeover
    rows = [
        clean_row(date(2026, 10, 2), po="A", smv="5.51", price="0.62"),
        clean_row(date(2026, 10, 3), po="A", smv="5.5088", price="0.62"),
    ]
    assert [row.production_date.day for row in business.kpi_rows(rows, OCT_1, OCT_31)] == [2]


def test_br32_first_day_is_read_per_line_in_the_whole_history() -> None:
    # the same order on another line is a new order for this line
    history_line_2 = [clean_row(date(2026, 10, 2), line="LINE 2", po="OLD")]
    assert len(business.kpi_rows(history_line_2, OCT_1, OCT_31)) == 1


def test_br32_rows_after_the_period_do_not_count() -> None:
    rows = [clean_row(date(2026, 10, 30), po="A", smv="10"), clean_row(date(2026, 11, 2), po="A", smv="11")]
    assert len(business.kpi_rows(rows, OCT_1, OCT_31)) == 1


def test_br32_excel_noise_does_not_make_a_new_pair() -> None:
    rows = [clean_row(date(2026, 10, 2), smv="10.79"), clean_row(date(2026, 10, 3), smv="10.790000000000001")]
    assert len(business.kpi_rows(rows, OCT_1, OCT_31)) == 1


def test_ac33_logic_br33_br34_br35_kpi() -> None:
    assert business.kpi(68, 27, 14) == Decimal(68) / Decimal(27) / Decimal(14)
    assert business.kpi(1, 0, 14) is None
    rows = [
        clean_row(date(2026, 10, 2), "LINE 1"),
        clean_row(date(2026, 10, 2), "LINE 2"),
        clean_row(date(2026, 10, 3), "LINE 1"),
        clean_row(date(2026, 10, 4), "LINE 3", qty="0"),  # no output: neither the day nor the line count
    ]
    assert business.working_days(rows) == 2
    assert business.line_count(rows) == 2


def test_ac33_logic_report_by_factory_with_hand_checked_kpi() -> None:
    rows = [
        clean_row(date(2026, 10, 2), "LINE 1", po="A", smv="10"),
        clean_row(date(2026, 10, 3), "LINE 1", po="B", smv="11"),
        clean_row(date(2026, 10, 2), "LINE 2", po="A", smv="10"),
        clean_row(date(2026, 10, 5), "LINE 2", po="C", smv=None),  # BR-37 not counted, but it is output (BR-33)
    ]
    report = business.report(rows, [], OCT_1, OCT_31)
    fac2 = report.by_factory[0]
    assert (fac2.factory, fac2.kpi_count, fac2.working_days, fac2.line_count) == (Factory.FAC_2, 3, 3, 2)
    assert fac2.kpi == Decimal(3) / Decimal(3) / Decimal(2)
    assert fac2.rerun_count == 3
    assert (report.total_kpi_count, report.total_rerun_count) == (3, 3)
    assert report.has_data is True
    assert [(item.line, item.kpi_count, item.rerun_count) for item in report.by_line] == [
        ("LINE 1", 2, 2),
        ("LINE 2", 1, 1),
    ]
    assert [(item.day.day, item.line, item.base_po) for item in report.details] == [
        (2, "LINE 1", "A"),
        (2, "LINE 2", "A"),
        (3, "LINE 1", "B"),
    ]


def test_ac35_rerun_counts_again_and_kpi_does_not() -> None:
    a = {"po": "A", "smv": "10"}
    b = {"po": "B", "smv": "20"}
    rows = [
        clean_row(date(2026, 10, 5), **a),
        clean_row(date(2026, 10, 6), **b),
        clean_row(date(2026, 10, 7), **b),
        clean_row(date(2026, 10, 8), **a),
    ]
    pair_a_only = [row for row in rows if row.base_po == "A"]
    # alone on the line, pair A has no gap; with pair B on the days between it comes back on day 4
    assert business.rerun_count(pair_a_only, OCT_1, OCT_31) == 1
    assert business.rerun_count(rows, OCT_1, OCT_31) == 3  # A day 1, B day 2, A again day 4
    kpi = business.kpi_rows(rows, OCT_1, OCT_31)
    assert [row.base_po for row in kpi] == ["A", "B"]


def test_ac36_day_off_is_not_a_gap() -> None:
    saturday, monday = date(2026, 10, 24), date(2026, 10, 26)
    rows = [clean_row(saturday), clean_row(monday)]
    assert business.rerun_count(rows, OCT_1, OCT_31) == 1


def test_br36_previous_working_day_is_read_before_the_period() -> None:
    rows = [clean_row(date(2026, 9, 30)), clean_row(date(2026, 10, 1))]
    assert business.rerun_count(rows, OCT_1, OCT_31) == 0  # already running on the last day of September
    other = [clean_row(date(2026, 9, 30), smv="11"), clean_row(date(2026, 10, 1), smv="10")]
    assert business.rerun_count(other, OCT_1, OCT_31) == 1


def test_ac34_rerun_ignores_days_after_the_period() -> None:
    rows = [clean_row(date(2026, 10, 31)), clean_row(date(2026, 11, 1), smv="11")]
    assert business.rerun_count(rows, OCT_1, OCT_31) == 1


def test_br37_rows_without_smv_are_left_out() -> None:
    rows = [clean_row(date(2026, 10, 2), smv=None), clean_row(date(2026, 10, 3), po="B", smv="10")]
    assert len(business.usable_rows(rows)) == 1
    report = business.report(rows, [], OCT_1, OCT_31)
    assert (report.by_factory[0].kpi_count, report.by_factory[0].rerun_count) == (1, 1)


def test_monthly_table_counts_each_month_separately() -> None:
    rows = [clean_row(date(2026, 10, 30), po="A"), clean_row(date(2026, 11, 2), po="B")]
    report = business.report(rows, [], date(2026, 10, 1), date(2026, 11, 30))
    assert [(item.month, item.kpi_count) for item in report.by_month] == [("10/2026", 1), ("11/2026", 1)]
    assert report.by_factory[0].kpi_count == 1  # same pair over the whole period counts once
    ranges = business.month_ranges(date(2026, 12, 15), date(2027, 1, 10))
    assert ranges == [
        ("12/2026", date(2026, 12, 15), date(2026, 12, 31)),
        ("01/2027", date(2027, 1, 1), date(2027, 1, 10)),
    ]


def test_br38_br41_weekly_number_only_for_the_exact_period() -> None:
    entry = WeeklyChangeover(
        factory=Factory.FAC_2,
        from_date=date(2026, 10, 24),
        to_date=date(2026, 10, 30),
        changeover_count=17,
        updated_by="x",
    )
    assert business.weekly_count([entry], Factory.FAC_2, date(2026, 10, 24), date(2026, 10, 30)) == 17
    assert business.weekly_count([entry], Factory.FAC_2, date(2026, 10, 24), date(2026, 10, 29)) is None
    assert business.weekly_count([entry], Factory.FAC_1, date(2026, 10, 24), date(2026, 10, 30)) is None
    assert business.weekly_per_line(17, 14) == Decimal(17) / Decimal(14)
    assert business.weekly_per_line(None, 14) is None
    assert business.weekly_per_line(17, 0) is None


def test_line_filter_narrows_the_report() -> None:
    rows = [clean_row(date(2026, 10, 2), "LINE 1", po="A"), clean_row(date(2026, 10, 2), "LINE 2", po="B", smv="11")]
    report = business.report(rows, [], OCT_1, OCT_31, lines=["LINE 2"])
    assert report.by_factory[0].kpi_count == 1
    assert report.by_factory[0].line_count == 1
    assert [item.line for item in report.by_line] == ["LINE 2"]
    assert business.report(rows, [], OCT_1, OCT_31, factories=(Factory.FAC_1,)).has_data is False
