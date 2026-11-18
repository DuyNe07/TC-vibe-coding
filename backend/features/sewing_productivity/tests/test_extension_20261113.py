"""Mở rộng 2026-11-13: Matching by the line strengths (BR-86), Changeover by code (BR-87), %Efficiency and SMV on Line
Detail (BR-83, BR-88), the two new Sewing metrics figures (BR-89). AC-117 to AC-121, AC-123."""

from datetime import date

import pytest

from backend.core.current_user import CurrentUser, set_current_user
from backend.features.sewing_productivity.business.changeover_business import ChangeoverBusiness
from backend.features.sewing_productivity.dto.changeover_dto import ChangeoverRequest
from backend.features.sewing_productivity.dto.display_names import TOTAL_COLUMN
from backend.features.sewing_productivity.dto.line_detail_dto import Factory, LineDetailRequest
from backend.features.sewing_productivity.dto.monthly_dto import (
    CHANGEOVER_PER_LINE_DAY,
    MonthlyReportRequest,
    PeriodKind,
)
from backend.features.sewing_productivity.dto.overview_dto import OverviewRequest
from backend.features.sewing_productivity.dto.upload_dto import SaveUploadRequest
from backend.features.sewing_productivity.services.get_changeover_service import GetChangeoverService
from backend.features.sewing_productivity.services.get_line_detail_service import GetLineDetailService
from backend.features.sewing_productivity.services.get_monthly_report_service import GetMonthlyReportService
from backend.features.sewing_productivity.services.get_overview_service import GetOverviewService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.tests.test_line_strength import strength_file
from backend.features.sewing_productivity.tests.workbook_factory import FAC2, clean_row, data_file, production, worker

D23, D24, D25, D26, D27, D28 = (date(2026, 10, day) for day in (23, 24, 25, 26, 27, 28))
WEEK = (D24, date(2026, 10, 30))  # W44 (24.10–30.10)
MATCH_KEY = "Tỷ lệ đúng sở trường"


@pytest.fixture(autouse=True)
def _updater():
    set_current_user(CurrentUser(username="an", is_admin=True))
    yield
    set_current_user(None)


def _save(rows: list[list[object]], days: tuple[date, ...] = (D23, D24, D25, D26, D27, D28)) -> None:
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, [], [worker(day, sf2=30) for day in days])))


def _strengths() -> None:
    rows = [["XM2", 14, "Pants", "T-Shirt", None, None, "MCC", "Medium", None]]  # LINE 3 of Fac 2 has none
    SaveUploadService().handle(SaveUploadRequest(file=strength_file(rows)))


def _detail(customer_groups: list[str] | None = None):
    return GetLineDetailService().handle(
        LineDetailRequest(
            from_date=WEEK[0], to_date=WEEK[1], factory=Factory.FAC_2, customer_groups=customer_groups or []
        )
    )


def _match_rows() -> list[list[object]]:
    return [
        production(D24, FAC2, line="LINE 14", qty=300, name="PANTS", po="PO-A.1", style="SA"),
        production(D24, FAC2, line="LINE 14", qty=100, name="POLO", po="PO-B.1", style="SB", customer="MCC"),
        production(D25, FAC2, line="LINE 14", qty=50, name="ZZZ UNKNOWN", po="PO-C.1", style="SC"),
        production(D25, FAC2, line="LINE 3", qty=80, name="PANTS", po="PO-D.1", style="SD"),
    ]


def test_ac117_br86_matching_follows_the_line_strengths_and_matches_the_orders():
    _strengths()
    _save(_match_rows())
    detail = _detail()
    lines = {row.line: row for row in detail.line_overview}
    assert lines["LINE 14"].matching_ratio == pytest.approx(75)  # 300 / (300 + 100); the unclassified 50 left out
    assert lines["LINE 3"].matching_ratio is None  # no strength saved for LINE 3
    assert lines["Tổng"].matching_ratio == pytest.approx(75)
    orders = {order.base_po: order.matches for order in detail.line_orders if order.line == "LINE 14"}
    assert orders == {"PO-A": True, "PO-B": False, "PO-C": None}


def test_br86_a_line_whose_orders_all_match_is_100_percent():
    _strengths()
    _save([production(D24, FAC2, line="LINE 14", qty=300, name="PANTS", po="PO-A.1", match="Trái sở trường")])
    line = {row.line: row for row in _detail().line_overview}["LINE 14"]
    assert line.matching_ratio == pytest.approx(100)  # the `Match line strength` column is not read any more
    assert [order.matches for order in _detail().line_orders] == [True]


def test_ac118_overview_and_sewing_metrics_show_the_same_match():
    _strengths()
    _save(_match_rows())
    overview = GetOverviewService().handle(
        OverviewRequest(from_date=WEEK[0], to_date=WEEK[1], factories=[Factory.FAC_2])
    )
    row = next(metric for metric in overview.metrics if metric.metric == MATCH_KEY)
    assert row.values["Fac 2"] == pytest.approx(75)
    filtered = GetOverviewService().handle(
        OverviewRequest(from_date=WEEK[0], to_date=WEEK[1], factories=[Factory.FAC_2], customer_groups=["MCC"])
    )
    assert next(m for m in filtered.metrics if m.metric == MATCH_KEY).values["Fac 2"] == pytest.approx(0)  # BR-29
    metrics = GetMonthlyReportService().handle(
        MonthlyReportRequest(from_date=WEEK[0], to_date=WEEK[1], factories=[Factory.FAC_2], period_kind=PeriodKind.WEEK)
    )
    match = next(metric for metric in metrics.period_metrics if metric.metric == MATCH_KEY)
    assert match.rows[-1].values["Fac 2"] == pytest.approx(75)
    assert match.rising_is_good is True  # BR-70: a rise is green


def _changeover_rows() -> list[list[object]]:
    def x(day: date) -> list[object]:
        return production(day, FAC2, line="LINE 5", smv=10.5, price=1.2, po="PO-X.1", style="SX")

    def y(day: date, style: str = "SY-A", po: str = "PO-Y.1") -> list[object]:
        return production(day, FAC2, line="LINE 5", smv=8, price=0.9, customer="MCC", po=po, style=style)

    return [
        x(D23),
        x(D24),
        y(D24),
        y(D25),
        y(D25, style="SY-B", po="PO-Y2.1"),  # another style, same customer + SMV + CM: the same code
        y(D27),  # 26/10 the line does not work: not a gap
        x(D28),  # back after a working day away: counts again
        production(D28, FAC2, line="LINE 5", smv=None, price=3, customer="NEW", po="PO-N.1", style="SN"),
    ]


def test_ac119_br87_changeover_counts_new_codes_per_working_day():
    _save(_changeover_rows(), days=(D23, D24, D25, D27, D28))
    lines = {row.line: row for row in _detail().line_overview}
    assert lines["LINE 5"].changeover == 2  # Y on 24/10, X back on 28/10
    assert lines["Tổng"].changeover == 2
    assert {row.line: row.changeover for row in _detail(["MCC"]).line_overview}["LINE 5"] == 1  # BR-29: Y only


def test_br87_first_time_counts_and_a_gap_needs_a_working_day_away():
    business = ChangeoverBusiness()
    rows = [clean_row(D23, smv="10"), clean_row(D25, smv="10"), clean_row(D27, smv="11"), clean_row(D28, smv="10")]
    days = business.code_days(rows)[(Factory.FAC_2, "LINE 1")]
    assert business.style_changeovers(days, D23, D28) == 3  # 23/10 first, 27/10 new SMV, 28/10 back after 27/10
    assert business.style_changeovers(days, D24, D26) == 0  # 25/10: the previous working day (23/10) ran it


def test_ac120_br88_order_smv_and_efficiency():
    _save(
        [
            production(D24, FAC2, line="LINE 7", qty=200, smv=10, standard=250, po="PO-Z.1"),
            production(D25, FAC2, line="LINE 7", qty=100, smv=13, standard=90, po="PO-Z.1"),
            production(D25, FAC2, line="LINE 7", qty=40, standard=None, po="PO-W.1", style="SW"),
        ]
    )
    orders = {order.base_po: order for order in _detail().line_orders}
    assert orders["PO-Z"].smv == pytest.approx(11)
    assert orders["PO-Z"].efficiency == pytest.approx(300 / 340 * 100)
    assert orders["PO-W"].efficiency is None


def test_ac121_line_efficiency_is_the_line_performance_ratio():
    _save(_match_rows())
    lines = {row.line: row for row in _detail().line_overview}
    request = ChangeoverRequest(from_date=WEEK[0], to_date=WEEK[1], factories=[Factory.FAC_2], line_performance=True)
    performance = {row.line: row for row in GetChangeoverService().handle(request).line_performance}
    for line in ("LINE 3", "LINE 14"):
        assert lines[line].efficiency == pytest.approx(performance[line].output_ratio)
    assert lines["LINE 14"].efficiency == pytest.approx(450 / 300 * 100)  # standard 100 per row
    overview = GetOverviewService().handle(
        OverviewRequest(from_date=WEEK[0], to_date=WEEK[1], factories=[Factory.FAC_2])
    )
    efficiency = next(metric for metric in overview.metrics if metric.metric == "Hiệu suất B")
    assert lines["Tổng"].efficiency == pytest.approx(efficiency.values["Fac 2"])
    low = _detail_with_low_efficiency()
    assert low.efficiency_below is True  # 50% < the 90% threshold of Fac 2


def _detail_with_low_efficiency():
    _save([production(D24, FAC2, line="LINE 9", qty=50, standard=100, po="PO-L.1", style="SL")])
    return {row.line: row for row in _detail().line_overview}["LINE 9"]


def test_ac123_br89_sewing_metrics_has_matching_and_changeover_per_line_day():
    def code(day: date, line: str, smv: float) -> list[object]:
        return production(day, FAC2, line=line, smv=smv, po=f"PO-{line[-1]}{smv}.1", style=f"S{smv}")

    _save(
        [code(D24, "LINE 1", 10), code(D25, "LINE 1", 10), code(D26, "LINE 1", 10)]
        + [code(D24, "LINE 2", 10), code(D25, "LINE 2", 12), code(D26, "LINE 2", 12)],
        days=(D24, D25, D26),
    )
    report = GetMonthlyReportService().handle(
        MonthlyReportRequest(from_date=WEEK[0], to_date=WEEK[1], factories=[Factory.FAC_2], period_kind=PeriodKind.WEEK)
    )
    names = [metric.metric for metric in report.period_metrics]
    assert names[-2:] == [MATCH_KEY, CHANGEOVER_PER_LINE_DAY]
    changeover = report.period_metrics[-1]
    assert changeover.decimals == 3
    assert changeover.rising_is_good is None  # BR-70: arrow not coloured
    # LINE 1: 1 (first day); LINE 2: 1 + 1 (new SMV on 25/10) -> 3 changeovers / 3 working days / 2 lines
    assert changeover.rows[-1].values["Fac 2"] == pytest.approx(0.5)
    assert changeover.rows[-1].values[TOTAL_COLUMN] == pytest.approx(0.5)
