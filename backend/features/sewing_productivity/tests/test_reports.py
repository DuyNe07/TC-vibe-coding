"""UC-04 to UC-15, UC-26 through the services, on a small stored data set with hand-checked numbers."""

from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from backend.core.base import EmptyRequest
from backend.core.exceptions import BusinessRuleViolation
from backend.features.sewing_productivity.dto.changeover_dto import ChangeoverRequest
from backend.features.sewing_productivity.dto.daily_dto import DailyReportRequest
from backend.features.sewing_productivity.dto.export_dto import ExportDailyRequest, ExportWeeklyRequest
from backend.features.sewing_productivity.dto.goal_dto import SaveGoalRequest
from backend.features.sewing_productivity.dto.line_detail_dto import LineDetailRequest, RowType
from backend.features.sewing_productivity.dto.line_mo_dto import LineMoRequest
from backend.features.sewing_productivity.dto.monthly_dto import MonthlyReportRequest
from backend.features.sewing_productivity.dto.overview_dto import ChartsRequest, OverviewRequest, RankingMetric
from backend.features.sewing_productivity.dto.upload_dto import SaveUploadRequest
from backend.features.sewing_productivity.dto.weekly_changeover_dto import SaveWeeklyChangeoversRequest
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.services.export_changeover_service import ExportChangeoverService
from backend.features.sewing_productivity.services.export_daily_report_service import ExportDailyReportService
from backend.features.sewing_productivity.services.export_line_mo_service import ExportLineMoService
from backend.features.sewing_productivity.services.export_monthly_report_service import ExportMonthlyReportService
from backend.features.sewing_productivity.services.export_weekly_report_service import ExportWeeklyReportService
from backend.features.sewing_productivity.services.get_changeover_service import GetChangeoverService
from backend.features.sewing_productivity.services.get_charts_service import GetChartsService
from backend.features.sewing_productivity.services.get_daily_report_service import GetDailyReportService
from backend.features.sewing_productivity.services.get_filter_options_service import GetFilterOptionsService
from backend.features.sewing_productivity.services.get_line_detail_service import GetLineDetailService
from backend.features.sewing_productivity.services.get_line_mo_service import GetLineMoService
from backend.features.sewing_productivity.services.get_monthly_report_service import GetMonthlyReportService
from backend.features.sewing_productivity.services.get_overview_service import GetOverviewService
from backend.features.sewing_productivity.services.save_goal_service import SaveGoalService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.services.save_weekly_changeovers_service import SaveWeeklyChangeoversService
from backend.features.sewing_productivity.tests.workbook_factory import (
    FAC1,
    FAC2,
    data_file,
    production,
    target,
    worker,
)

DAY_1 = date(2026, 10, 24)  # a Saturday
DAY_2 = date(2026, 10, 26)
WEEK_END = date(2026, 10, 30)


def store_fac2() -> None:
    """Fac 2: DAY_1 LINE 1 and LINE 2 with target A, target B and workers; DAY_2 LINE 1 with none of them.

    Hand-checked: target A 500, output 600, efficiency A (100+300)/500 = 80%, target B 425,
    efficiency B (100+300)/425 = 94.1176%, CM 100+300+400 = 800, average price 800/600 = 1.3333,
    hours day 1 (8+10)/2 = 9, day 2 8, period 8.5, MO 8h 400/40*8/9 = 8.8889 (day 2 has no workers),
    strength match 1-300/500 = 40%."""
    rows = [
        production(DAY_1, FAC2, "LINE 1", qty=100, price=1, sewers=10, hours=8, standard=125, customer="ELAND WORLD"),
        production(DAY_1, FAC2, "Line 2", qty=300, price=1, sewers=20, hours=10, standard=300, customer="MI HUB LIMITED", po="PO-2.1", style="S2"),
        production(DAY_2, FAC2, "LINE 1", qty=200, price=2, sewers=10, hours=8, smv=None, standard=None, customer="ELAND SPORT"),
    ]  # fmt: skip
    targets = [
        target(DAY_1, "SF2 - Sewing Line 01", qty=200, cm=100),
        target(DAY_1, "SF2 - Sewing Line 02", qty=300, cm=300, expertise="Mismatched Strength", style="S2", po="PO-2"),
    ]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, targets, [worker(DAY_1, sf2=40)])))


def overview(**changes: object) -> dict[str, object]:
    values = {"from_date": DAY_1, "to_date": WEEK_END, **changes}
    return GetOverviewService().handle(OverviewRequest(**values))


def metric_values(response: object, factory: str = "Fac 2") -> dict[str, float | None]:
    return {row.metric: row.values[factory] for row in response.metrics}


def metric_flags(response: object, factory: str = "Fac 2") -> dict[str, bool]:
    return {row.metric: row.below[factory] for row in response.metrics}


def sheet_rows(content: bytes, sheet: str) -> list[dict[str, object]]:
    worksheet = load_workbook(BytesIO(content))[sheet]
    rows = list(worksheet.iter_rows(values_only=True))
    return [dict(zip(rows[0], row, strict=True)) for row in rows[1:]]


def test_overview_numbers_are_hand_checked() -> None:
    store_fac2()
    response = overview()
    values = metric_values(response)
    assert response.has_data is True
    assert [row.metric for row in response.metrics][:4] == [
        "Mục tiêu A",
        "Sản lượng",
        "Mục tiêu hiệu suất",
        "Hiệu suất A",
    ]
    assert values["Mục tiêu A"] == 500
    assert values["Sản lượng"] == 600
    assert values["Mục tiêu hiệu suất"] == 100
    assert values["Hiệu suất A"] == pytest.approx(80)
    assert values["% so với mục tiêu của hiệu suất A"] == pytest.approx(80)
    assert values["Mục tiêu B"] == 425
    assert values["Hiệu suất B"] == pytest.approx(94.1176, abs=0.001)
    assert values["Tiền CM"] == 800
    assert values["Mục tiêu MO 8h"] == 43
    assert values["MO 8h"] == pytest.approx(8.8889, abs=0.001)
    assert values["Giá CM trung bình"] == pytest.approx(800 / 600)  # AC-51
    assert values["Giờ làm trung bình"] == 8.5
    assert values["Tỷ lệ đúng sở trường"] == pytest.approx(40)
    assert values["Đổi mã hàng tuần"] is None
    flags = metric_flags(response)
    assert flags["Hiệu suất A"] is True  # 80 < 90
    assert flags["Hiệu suất B"] is False  # 94.1 >= 90
    assert flags["MO 8h"] is True  # 8.89 < 40
    assert metric_values(response, "Fac 1")["Sản lượng"] is None


def test_ac23_note_when_some_days_have_no_target() -> None:
    store_fac2()
    response = overview()  # DAY_2 has output and no target A
    assert response.note == "Hiệu suất A chỉ tính từ 24/10/2026."


def test_ac23_no_target_at_all_efficiency_a_is_dash_and_b_stays() -> None:
    september = date(2026, 9, 10)
    rows = [production(september, FAC2, qty=80, standard=100)]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, target_rows=[], worker_rows=[])))
    response = overview(from_date=date(2026, 9, 1), to_date=date(2026, 9, 30))
    values = metric_values(response)
    assert values["Hiệu suất A"] is None
    assert values["Mục tiêu A"] is None
    assert values["Hiệu suất B"] == pytest.approx(80)
    assert response.note == ""


def test_ac24_customer_filter_applies_br29() -> None:
    store_fac2()
    values = metric_values(overview(customer_groups=["ELAND"]))
    assert values["Sản lượng"] == 300  # LINE 1 only: 100 + 200
    assert values["Tiền CM"] == 500
    assert values["Giá CM trung bình"] == pytest.approx(500 / 300)
    assert values["Mục tiêu B"] == 125
    assert values["Hiệu suất B"] == pytest.approx(80)
    assert values["Mục tiêu A"] is None
    assert values["Hiệu suất A"] is None
    assert values["MO 8h"] is None
    assert values["Tỷ lệ đúng sở trường"] is None
    assert values["Giờ làm trung bình"] == 8.5  # hours are not filtered


def test_empty_filter_lists_do_not_apply_br29() -> None:
    store_fac2()
    assert metric_values(overview(customer_groups=[], product_groups=[]))["Hiệu suất A"] == pytest.approx(80)


def test_product_filter_applies_br29() -> None:
    store_fac2()
    values = metric_values(overview(product_groups=["Polo"]))
    assert values["Hiệu suất A"] is None
    response = overview(product_groups=["Polo"])
    assert response.has_data is False


def test_ac26_period_mo8h_uses_only_days_with_workers() -> None:
    rows = [
        production(DAY_1, FAC2, qty=100, sewers=10, hours=10),
        production(DAY_2, FAC2, qty=100, sewers=10, hours=8, price=3),
    ]
    workers = [worker(DAY_1, sf2=10), worker(DAY_2)]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, [target(DAY_1)], workers)))
    # only day 1 counts: 100 / 10 * 8 / 10 = 8
    assert metric_values(overview())["MO 8h"] == 8


def test_ac27_period_compares_with_level_of_the_last_day() -> None:
    days = (date(2026, 11, 30), date(2026, 12, 1))
    rows = [production(day, FAC1, line="LINE 1") for day in days]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, target_rows=[], worker_rows=[])))
    SaveGoalService().handle(
        SaveGoalRequest(
            factory=Factory.FAC_1,
            effective_from=days[1],
            efficiency_target=95,
            mo8h_target=40,
            efficiency_threshold=85,
            mo8h_threshold=30,
        )
    )
    before = metric_values(overview(from_date=days[0], to_date=days[0]), "Fac 1")
    after = metric_values(overview(from_date=days[1], to_date=days[1]), "Fac 1")
    assert (before["Mục tiêu MO 8h"], after["Mục tiêu MO 8h"]) == (38, 40)


def test_ac31_weekly_number_only_on_the_exact_period() -> None:
    rows = [production(DAY_1, FAC2, line=f"LINE {number}") for number in range(1, 15)]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows)))
    SaveWeeklyChangeoversService().handle(
        SaveWeeklyChangeoversRequest(from_date=DAY_1, to_date=WEEK_END, counts={"Fac 2": 17, "Fac 1": None})
    )
    values = metric_values(overview())
    assert values["Đổi mã hàng tuần"] == 17
    assert values["Đổi mã hàng tuần trên chuyền"] == pytest.approx(17 / 14)
    other = metric_values(overview(to_date=date(2026, 10, 29)))
    assert other["Đổi mã hàng tuần"] is None
    assert other["Đổi mã hàng tuần trên chuyền"] is None


def test_ac14_ac25_line_detail_rows() -> None:
    store_fac2()
    response = GetLineDetailService().handle(
        LineDetailRequest(from_date=DAY_1, to_date=WEEK_END, factory=Factory.FAC_2)
    )
    labels = [(row.line, row.work_date, row.row_type) for row in response.rows]
    assert labels == [
        ("LINE 1", DAY_1, RowType.DAY),
        ("LINE 1", DAY_2, RowType.DAY),
        ("LINE 1", None, RowType.PERIOD),
        ("LINE 2", DAY_1, RowType.DAY),
        ("LINE 2", None, RowType.PERIOD),
        ("Tổng", None, RowType.TOTAL),
    ]
    line1_day1, line1_day2, line1_period, line2_day, _line2_period, total = response.rows
    assert line1_day1.mo8h == 10  # 100 / 10 * 8 / 8
    assert line1_day1.efficiency_a == 50  # 100 / 200
    assert line1_day1.efficiency_a_below is True
    assert line1_day2.mo8h == 40  # 400 / 10 * 8 / 8
    assert line1_day2.mo8h_below is False  # threshold 40
    assert line1_period.mo8h == 25  # average of the days
    assert line1_period.efficiency_a == 50  # the day without a target stays out of both sides
    assert line1_period.output == 300
    assert line2_day.hours == 10
    assert total.output == 600
    assert total.mo8h == pytest.approx(8.8889, abs=0.001)
    assert [(day.work_date, day.workers, day.hours) for day in response.factory_days] == [
        (DAY_1, 40, 9),
        (DAY_2, None, 8),
    ]
    assert response.note == "Hiệu suất A chỉ tính từ 24/10/2026."


def test_ac14_line_names_are_merged_after_standardising() -> None:
    day = date(2026, 8, 3)
    rows = [production(day, FAC1, "Line 1", qty=10), production(day, FAC1, "LINE 1", qty=20)]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, target_rows=[], worker_rows=[])))
    response = GetLineDetailService().handle(LineDetailRequest(from_date=day, to_date=day, factory=Factory.FAC_1))
    assert {row.line for row in response.rows if row.row_type == RowType.DAY} == {"LINE 1"}


def test_ac15_report_uses_the_current_line_name() -> None:
    rows = [production(date(2026, 7, 6), FAC1, "LINE 1"), production(date(2026, 7, 7), FAC1, "LINE 1")]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, target_rows=[], worker_rows=[])))
    response = GetLineDetailService().handle(
        LineDetailRequest(from_date=date(2026, 7, 6), to_date=date(2026, 7, 7), factory=Factory.FAC_1)
    )
    day_rows = {(row.line, row.work_date) for row in response.rows if row.row_type == RowType.DAY}
    assert day_rows == {("LINE 30", date(2026, 7, 6)), ("LINE 1", date(2026, 7, 7))}


def test_line_filter_keeps_the_factory_total() -> None:
    store_fac2()
    response = GetLineDetailService().handle(
        LineDetailRequest(from_date=DAY_1, to_date=WEEK_END, factory=Factory.FAC_2, lines=["LINE 2"])
    )
    assert {row.line for row in response.rows} == {"LINE 2", "Tổng"}
    assert response.rows[-1].output == 600


def test_ac37_ac38_daily_report() -> None:
    store_fac2()
    response = GetDailyReportService().handle(DailyReportRequest(report_date=DAY_1, factory=Factory.FAC_2))
    values = metric_values(response)
    assert response.has_data is True
    assert values["Mục tiêu sản lượng"] == 500
    assert values["Target MO 8h"] == pytest.approx(400 * 8 / (40 * 9))  # 400 CM / 40 sewers * 8 / 9 hours
    assert values["MO"] == 10
    assert values["MO 8h"] == pytest.approx(8.8889, abs=0.001)
    assert values["% so với Target MO 8h"] == pytest.approx(100)
    assert values["Số thợ"] == 40
    assert values["Hiệu suất A"] == pytest.approx(80)
    assert metric_flags(response)["MO 8h"] is True
    assert [row.line for row in response.lines] == ["LINE 1", "LINE 2", "Tổng"]
    total = response.lines[-1]
    assert (total.output, total.cm_earning, total.sewers, total.hours) == (400, 400, 30, 9)
    assert total.mo == pytest.approx(400 / 30)
    assert total.mo8h == pytest.approx(400 * 8 / (30 * 9))


def test_daily_report_mismatched_output() -> None:
    rows = [production(DAY_1, FAC2, qty=70, match="Trái sở trường"), production(DAY_1, FAC2, qty=30, color="RED")]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows)))
    response = GetDailyReportService().handle(DailyReportRequest(report_date=DAY_1, factory=Factory.FAC_2))
    assert response.lines[0].mismatched_output == 70


def test_daily_report_without_data() -> None:
    assert GetDailyReportService().handle(DailyReportRequest(report_date=DAY_1)).has_data is False


def test_ac39_monthly_report_with_total_row() -> None:
    store_fac2()
    response = GetMonthlyReportService().handle(
        MonthlyReportRequest(from_date=date(2026, 10, 1), to_date=date(2026, 10, 31), factories=[Factory.FAC_2])
    )
    table = response.factories[0]
    assert table.factory == "Fac 2"
    day_1, day_2, total = table.rows
    assert (day_1.work_date, day_1.mo, day_1.workers) == (DAY_1, 10, 40)
    assert (day_2.mo, day_2.mo8h, day_2.efficiency_b) == (None, None, None)
    assert total.row_type == RowType.TOTAL
    assert (total.output, total.cm_earning, total.target_b) == (600, 800, 425)
    assert total.efficiency_b == pytest.approx(94.1176, abs=0.001)
    assert total.mo8h == pytest.approx(8.8889, abs=0.001)


def test_ac40_line_mo_tables() -> None:
    store_fac2()
    response = GetLineMoService().handle(LineMoRequest(from_date=DAY_1, to_date=WEEK_END, factory=Factory.FAC_2))
    assert response.dates == [DAY_1, DAY_2]
    assert [table.title for table in response.tables] == ["MO 8h", "Tiền CM", "Giờ làm", "Số người", "Hiệu suất B"]
    mo8h = response.tables[0]
    assert [row.line for row in mo8h.rows] == ["LINE 1", "LINE 2", "Tổng"]
    assert mo8h.rows[0].cells[DAY_1].value == 10
    assert mo8h.rows[0].cells[DAY_1].below is True
    assert mo8h.rows[0].period.value == 25
    assert DAY_2 not in mo8h.rows[1].cells
    total = mo8h.rows[2]
    assert total.is_total is True
    # BR-48 day 1: 400 / 30 people * 8 / 9 hours; period: 800 / 40 people * 8 / 8.5 hours
    assert total.cells[DAY_1].value == pytest.approx(400 * 8 / (30 * 9))
    assert total.period.value == pytest.approx(800 * 8 / (40 * 8.5))
    cm = response.tables[1]
    assert cm.rows[2].period.value == 800
    assert cm.rows[2].cells[DAY_1].below is False
    assert response.tables[3].rows[2].cells[DAY_1].value == 30
    assert response.tables[4].rows[2].period.value == pytest.approx(94.1176, abs=0.001)


def test_line_mo_without_data() -> None:
    response = GetLineMoService().handle(LineMoRequest(from_date=DAY_1, to_date=WEEK_END))
    assert response.has_data is False


def test_ac41_charts_and_ranking() -> None:
    store_fac2()
    charts = GetChartsService().handle(ChartsRequest(from_date=DAY_1, to_date=WEEK_END))
    assert [(point.day, point.factory) for point in charts.efficiency_a] == [(DAY_1, "Fac 2")]  # day 2 has no target A
    assert charts.efficiency_a[0].value == pytest.approx(80)
    assert charts.efficiency_b[0].value == pytest.approx(400 * 100 / 425)
    assert charts.mo8h[0].value == pytest.approx(8.8889, abs=0.001)
    assert (
        charts.output_vs_target[0].factory,
        charts.output_vs_target[0].output,
        charts.output_vs_target[0].target_a,
    ) == ("Fac 2", 600, 500)
    assert [(line.factory, line.line) for line in charts.top_lines] == [("Fac 2", "LINE 2"), ("Fac 2", "LINE 1")]
    assert [(line.factory, line.line) for line in charts.bottom_lines] == [("Fac 2", "LINE 1"), ("Fac 2", "LINE 2")]
    assert charts.not_applicable_message == ""
    by_mo = GetChartsService().handle(
        ChartsRequest(from_date=DAY_1, to_date=WEEK_END, ranking_metric=RankingMetric.MO8H)
    )
    assert by_mo.top_lines[0].line == "LINE 1"  # period 25, LINE 2: 300 / 20 * 8 / 10 = 12
    by_a = GetChartsService().handle(
        ChartsRequest(from_date=DAY_1, to_date=WEEK_END, ranking_metric=RankingMetric.EFFICIENCY_A)
    )
    assert by_a.top_lines[0].line == "LINE 2"


def test_ac41_charts_under_a_customer_filter() -> None:
    store_fac2()
    charts = GetChartsService().handle(ChartsRequest(from_date=DAY_1, to_date=WEEK_END, customer_groups=["ELAND"]))
    assert charts.not_applicable_message == "Không áp dụng khi lọc theo khách hàng hoặc sản phẩm."
    assert (charts.efficiency_a, charts.mo8h, charts.output_vs_target) == ([], [], [])
    assert charts.efficiency_b[0].value == pytest.approx(80)
    filtered_mo = GetChartsService().handle(
        ChartsRequest(from_date=DAY_1, to_date=WEEK_END, customer_groups=["ELAND"], ranking_metric=RankingMetric.MO8H)
    )
    assert filtered_mo.top_lines == []


def test_br44_ranking_keeps_ten_lines_and_drops_dashes() -> None:
    rows = [production(DAY_1, FAC2, f"LINE {n}", qty=n, standard=100) for n in range(1, 13)]
    rows.append(production(DAY_1, FAC2, "LINE 99", standard=None))
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows)))
    charts = GetChartsService().handle(ChartsRequest(from_date=DAY_1, to_date=DAY_1))
    assert [line.line for line in charts.top_lines][:2] == ["LINE 12", "LINE 11"]
    assert len(charts.top_lines) == 10 and len(charts.bottom_lines) == 10
    assert charts.bottom_lines[0].line == "LINE 1"
    assert all(line.line != "LINE 99" for line in charts.top_lines + charts.bottom_lines)


@pytest.mark.parametrize(
    "call",
    [
        lambda start, end: GetOverviewService().handle(OverviewRequest(from_date=start, to_date=end)),
        lambda start, end: GetChartsService().handle(ChartsRequest(from_date=start, to_date=end)),
        lambda start, end: GetLineDetailService().handle(LineDetailRequest(from_date=start, to_date=end)),
        lambda start, end: GetMonthlyReportService().handle(MonthlyReportRequest(from_date=start, to_date=end)),
        lambda start, end: GetLineMoService().handle(LineMoRequest(from_date=start, to_date=end)),
        lambda start, end: GetChangeoverService().handle(ChangeoverRequest(from_date=start, to_date=end)),
        lambda start, end: ExportWeeklyReportService().handle(ExportWeeklyRequest(from_date=start, to_date=end)),
        lambda start, end: ExportMonthlyReportService().handle(MonthlyReportRequest(from_date=start, to_date=end)),
        lambda start, end: ExportLineMoService().handle(LineMoRequest(from_date=start, to_date=end)),
        lambda start, end: ExportChangeoverService().handle(ChangeoverRequest(from_date=start, to_date=end)),
    ],
)
def test_ac42_wrong_period_shows_br30(call: object) -> None:
    with pytest.raises(BusinessRuleViolation) as error:
        call(WEEK_END, DAY_1)
    assert error.value.message == "Từ ngày không được sau đến ngày. Hãy chọn lại khoảng thời gian."


def test_ac43_weekly_excel_file() -> None:
    store_fac2()
    file = ExportWeeklyReportService().handle(ExportWeeklyRequest(from_date=DAY_1, to_date=WEEK_END))
    assert file.filename == "bao-cao-tuan_2026-10-24_2026-10-30.xlsx"
    workbook = load_workbook(BytesIO(file.content))
    assert workbook.sheetnames == ["Tong quan", "Fac 1", "Fac 2", "Fac 3", "Fac 5"]
    header = workbook["Fac 2"]["A1"]
    assert header.font.bold is True and header.fill.fgColor.rgb.endswith("0F62FE")
    assert workbook["Fac 2"].freeze_panes == "A2"
    overview_rows = {row["Chỉ số"]: row for row in sheet_rows(file.content, "Tong quan")}
    assert overview_rows["Hiệu suất A"]["Fac 2"] == 80
    assert overview_rows["Hiệu suất B"]["Fac 2"] == 94.1  # BR-50 one decimal
    assert overview_rows["MO 8h"]["Fac 2"] == 8.89
    assert overview_rows["Hiệu suất A"]["Fac 1"] == "-"
    assert overview_rows["Đánh giá hiệu suất A"]["Fac 2"] == "Dưới ngưỡng"
    assert overview_rows["Đánh giá hiệu suất B"]["Fac 2"] == "Đạt"
    assert overview_rows["Đánh giá MO 8h"]["Fac 2"] == "Dưới ngưỡng"
    rows = sheet_rows(file.content, "Fac 2")
    assert (rows[0]["Chuyền"], rows[0]["Ngày"], rows[0]["MO 8h"]) == ("LINE 1", "24/10/2026", 10)
    assert (rows[2]["Ngày"], rows[2]["MO 8h"]) == ("Cả kỳ", 25)
    assert rows[-1]["Chuyền"] == "Tổng"
    assert list(rows[0])[-3:] == ["Đánh giá hiệu suất A", "Đánh giá hiệu suất B", "Đánh giá MO 8h"]
    assert load_workbook(BytesIO(file.content))["Fac 1"]["A1"].value == "Chuyền"  # an empty factory keeps its header


def test_ac29_ac30_excel_and_flags_at_the_boundaries() -> None:
    rows = [
        production(DAY_1, FAC2, "LINE 1", qty=899, standard=1000, sewers=10, hours=8, price=1),
        production(DAY_1, FAC2, "LINE 2", qty=399, standard=399, sewers=10, hours=8, price=1),
        production(DAY_1, FAC1, "LINE 1", qty=850, standard=1000, sewers=10, hours=8, price=1),
        production(DAY_1, FAC1, "LINE 2", qty=300, standard=300, sewers=10, hours=8, price=1),
    ]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, target_rows=[], worker_rows=[])))
    file = ExportWeeklyReportService().handle(ExportWeeklyRequest(from_date=DAY_1, to_date=DAY_1))
    fac2 = {row["Chuyền"]: row for row in sheet_rows(file.content, "Fac 2") if row["Ngày"] != "Cả kỳ"}
    fac1 = {row["Chuyền"]: row for row in sheet_rows(file.content, "Fac 1") if row["Ngày"] != "Cả kỳ"}
    assert fac2["LINE 1"]["Hiệu suất B (%)"] == 89.9
    assert fac2["LINE 1"]["Đánh giá hiệu suất B"] == "Dưới ngưỡng"
    assert fac1["LINE 1"]["Hiệu suất B (%)"] == 85
    assert fac1["LINE 1"]["Đánh giá hiệu suất B"] == "Đạt"
    assert fac2["LINE 2"]["MO 8h"] == 39.9
    assert fac2["LINE 2"]["Đánh giá MO 8h"] == "Dưới ngưỡng"
    assert fac1["LINE 2"]["MO 8h"] == 30
    assert fac1["LINE 2"]["Đánh giá MO 8h"] == "Đạt"
    detail = GetLineDetailService().handle(LineDetailRequest(from_date=DAY_1, to_date=DAY_1, factory=Factory.FAC_2))
    assert detail.rows[0].efficiency_b_below is True
    assert next(row for row in detail.rows if row.line == "LINE 2").mo8h_below is True
    fac1_detail = GetLineDetailService().handle(
        LineDetailRequest(from_date=DAY_1, to_date=DAY_1, factory=Factory.FAC_1)
    )
    assert fac1_detail.rows[0].efficiency_b_below is False
    assert next(row for row in fac1_detail.rows if row.line == "LINE 2").mo8h_below is False


def test_ac44_daily_monthly_mo_changeover_files_have_the_right_sheets() -> None:
    store_fac2()
    daily = ExportDailyReportService().handle(ExportDailyRequest(report_date=DAY_1))
    assert daily.filename == "bao-cao-ngay_2026-10-24.xlsx"
    assert load_workbook(BytesIO(daily.content)).sheetnames == ["Xuong", "Chuyen"]
    factories = {row["Chỉ số"]: row for row in sheet_rows(daily.content, "Xuong")}
    assert factories["MO"]["Fac 2"] == 10
    assert factories["Đánh giá MO 8h"]["Fac 2"] == "Dưới ngưỡng"
    assert sheet_rows(daily.content, "Chuyen")[0]["Xưởng"] == "Fac 2"

    monthly = ExportMonthlyReportService().handle(
        MonthlyReportRequest(from_date=date(2026, 10, 1), to_date=date(2026, 10, 31))
    )
    assert monthly.filename == "bao-cao-thang_2026-10-01_2026-10-31.xlsx"
    assert load_workbook(BytesIO(monthly.content)).sheetnames == ["Fac 1", "Fac 2", "Fac 3", "Fac 5"]
    rows = sheet_rows(monthly.content, "Fac 2")
    assert (rows[0]["Ngày"], rows[0]["MO"]) == ("24/10/2026", 10)
    assert (rows[1]["MO"], rows[1]["Đánh giá MO 8h"]) == ("-", "-")
    assert rows[-1]["Ngày"] == "Tổng"

    mo = ExportLineMoService().handle(LineMoRequest(from_date=DAY_1, to_date=WEEK_END, factory=Factory.FAC_2))
    assert mo.filename == "mo-theo-chuyen_Fac 2_2026-10-24_2026-10-30.xlsx"
    assert load_workbook(BytesIO(mo.content)).sheetnames == ["MO 8h", "Tien CM", "Gio lam", "So nguoi", "Hieu suat B"]
    mo_rows = sheet_rows(mo.content, "MO 8h")
    assert list(mo_rows[0]) == ["Chuyền", "24/10/2026", "26/10/2026", "Cả kỳ"]
    assert (mo_rows[0]["24/10/2026"], mo_rows[0]["Cả kỳ"]) == (10, 25)
    assert mo_rows[1]["26/10/2026"] == "-"
    assert mo_rows[-1]["Chuyền"] == "Tổng"

    changeover = ExportChangeoverService().handle(
        ChangeoverRequest(from_date=date(2026, 10, 1), to_date=date(2026, 10, 31))
    )
    assert changeover.filename == "doi-ma-hang_2026-10-01_2026-10-31.xlsx"
    assert load_workbook(BytesIO(changeover.content)).sheetnames == [
        "Theo xuong",
        "Theo thang",
        "Theo chuyen",
        "Chi tiet",
    ]
    by_factory = sheet_rows(changeover.content, "Theo xuong")
    assert by_factory[-1]["Xưởng"] == "Tổng"
    assert by_factory[-1]["Số chuyền"] == "-"


def test_changeover_service_uses_the_whole_stored_history() -> None:
    rows = [
        production(date(2026, 9, 28), FAC2, "LINE 1", po="OLD.1", smv=10, price=1),
        production(date(2026, 10, 2), FAC2, "LINE 1", po="OLD.2", smv=10, price=1),
        production(date(2026, 10, 3), FAC2, "LINE 1", po="NEW.1", smv=12, price=1),
    ]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, target_rows=[], worker_rows=[])))
    response = GetChangeoverService().handle(ChangeoverRequest(from_date=date(2026, 10, 1), to_date=date(2026, 10, 31)))
    fac2, total = response.by_factory
    assert (fac2.factory, fac2.kpi_count, fac2.working_days, fac2.line_count, fac2.rerun_count) == ("Fac 2", 1, 2, 1, 1)
    assert (total.is_total, total.kpi_count, total.rerun_count, total.kpi, total.working_days) == (
        True,
        1,
        1,
        None,
        None,
    )
    assert response.details[0].base_po == "NEW"
    assert response.by_month[0].month == "10/2026"
    assert response.has_data is True


def test_ac45_no_data_at_all() -> None:
    options = GetFilterOptionsService().handle(EmptyRequest())
    assert options.has_data is False
    assert options.latest_date is None
    assert options.factories == []
    assert overview().has_data is False


def test_ac46_ac52_ac19_filter_options() -> None:
    rows = [
        production(date(2026, 11, 4), FAC2, "LINE 10", customer="ELAND WORLD", name="POLO"),
        production(date(2026, 11, 4), FAC2, "LINE 2", customer="ELAND SPORT", color="RED"),
        production(date(2026, 11, 3), FAC1, "LINE 1", customer="ELAND WORLD/SPAO (QR)", name="VITRIOL"),
        production(date(2026, 11, 3), FAC1, "LINE 2", customer="MI HUB LIMITED", name=None, style="S9", po="PO-9"),
    ]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, target_rows=[], worker_rows=[])))
    options = GetFilterOptionsService().handle(EmptyRequest())
    assert options.has_data is True
    assert options.factories == ["Fac 1", "Fac 2"]
    assert options.lines_by_factory["Fac 2"] == ["LINE 2", "LINE 10"]
    assert options.customer_groups == ["ELAND", "MIHUB"]
    assert options.product_groups == ["Chưa phân nhóm", "Polo", "T-Shirt"]
    assert options.latest_date == date(2026, 11, 4)
    assert options.last_upload_at is not None
    assert (options.default_week_from, options.default_week_to) == (date(2026, 10, 24), date(2026, 10, 30))
    assert options.default_month_from == date(2026, 11, 1)
