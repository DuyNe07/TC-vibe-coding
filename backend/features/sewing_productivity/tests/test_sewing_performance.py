"""BR-51 the HCM column and BR-52 the English names of the Excel files (UC-27, AC-53 to AC-58)."""

from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from backend.features.sewing_productivity.dto.daily_dto import DailyReportRequest
from backend.features.sewing_productivity.dto.display_names import english_name, english_terms
from backend.features.sewing_productivity.dto.export_dto import ExportDailyRequest, ExportWeeklyRequest
from backend.features.sewing_productivity.dto.overview_dto import ChartsRequest, Factory, OverviewRequest
from backend.features.sewing_productivity.dto.upload_dto import SaveUploadRequest
from backend.features.sewing_productivity.services.export_daily_report_service import ExportDailyReportService
from backend.features.sewing_productivity.services.export_weekly_report_service import ExportWeeklyReportService
from backend.features.sewing_productivity.services.get_charts_service import GetChartsService
from backend.features.sewing_productivity.services.get_daily_report_service import GetDailyReportService
from backend.features.sewing_productivity.services.get_overview_service import GetOverviewService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.tests.workbook_factory import data_file, production, target, worker

DAY = date(2026, 10, 24)
FAC2 = "SHCM-Factory 2"
FAC3 = "SHCM-Factory 3"


def _load() -> None:
    """Fac 2: output 400, CM 400, target B 500, 10 sewers. Fac 3: output 100, CM 300, target B 100, 30 sewers."""
    rows = [
        production(DAY, FAC2, qty=400, price=1, standard=500, sewers=10, hours=8),
        production(DAY, FAC3, qty=100, price=3, standard=100, sewers=30, hours=10),
    ]
    targets = [target(DAY, line="SF2 - Sewing Line 01", qty=500), target(DAY, line="SF3 - Sewing Line 01", qty=200)]
    workers = [worker(DAY, sf2=10, sf3=30)]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, targets, workers)))


def _values(response, column="HCM"):
    return {row.metric: row.values.get(column) for row in response.metrics}


def _overview(**filters):
    return GetOverviewService().handle(OverviewRequest(from_date=DAY, to_date=DAY, **filters))


def test_hcm_is_calculated_from_totals_not_from_an_average_of_percentages():  # AC-53
    _load()
    values = _values(_overview())
    assert values["Sản lượng"] == 500
    assert values["Mục tiêu A"] == 700
    assert values["Hiệu suất A"] == pytest.approx(500 * 100 / 700)
    assert values["Hiệu suất B"] == pytest.approx(500 * 100 / 600)
    assert values["Tiền CM"] == 700
    # MO 8h: 700 CM x 8 / (40 sewers x average hours (8 + 10) / 2)
    assert values["MO 8h"] == pytest.approx(700 * 8 / (40 * 9))
    assert values["Mục tiêu MO 8h"] == 43  # the same level on the 3 factories
    assert values["Mục tiêu hiệu suất"] == 100


def test_factory_columns_are_unchanged_by_the_hcm_column():  # AC-54
    _load()
    values = _values(_overview(), "Fac 2")
    assert values["Hiệu suất B"] == pytest.approx(80)
    assert values["MO 8h"] == pytest.approx(400 * 8 / (10 * 8))


def test_hcm_needs_two_chosen_hcm_factories():  # AC-55
    _load()
    assert "HCM" not in _overview(factories=[Factory.FAC_2]).metrics[0].values
    assert "HCM" not in _overview(factories=[Factory.FAC_1, Factory.FAC_3]).metrics[0].values
    assert "HCM" in _overview(factories=[Factory.FAC_2, Factory.FAC_3]).metrics[0].values


def test_total_of_the_cards_adds_every_chosen_factory():  # AC-64
    _load()
    values = _values(_overview(), "Total")
    assert values["Tiền CM"] == 700
    assert values["Sản lượng"] == 500
    assert values["Giá CM trung bình"] == pytest.approx(700 / 500)
    assert values["MO 8h"] == pytest.approx(700 * 8 / (40 * 9))
    assert values["Hiệu suất B"] == pytest.approx(500 * 100 / 600)
    assert _values(_overview(factories=[Factory.FAC_2]), "Total")["Sản lượng"] == 400


def test_hcm_is_in_the_daily_table_and_the_charts():  # AC-56
    _load()
    daily = GetDailyReportService().handle(DailyReportRequest(report_date=DAY, factory=Factory.FAC_2))
    values = _values(daily)
    assert values["Sản lượng"] == 500
    assert values["Số thợ"] == 40
    assert values["Hiệu suất B"] == pytest.approx(500 * 100 / 600)
    charts = GetChartsService().handle(ChartsRequest(from_date=DAY, to_date=DAY))
    assert {point.factory for point in charts.efficiency_b} == {"Fac 2", "Fac 3"}
    assert [point.factory for point in charts.hcm_efficiency_b] == ["HCM"]
    assert charts.hcm_efficiency_a[0].value == pytest.approx(500 * 100 / 700)
    assert charts.hcm_mo8h[0].value == pytest.approx(700 * 8 / (40 * 9))
    assert (charts.hcm_output.output, charts.hcm_output.target_a) == (500, 700)


def _sheets(content: bytes) -> dict[str, list[dict[str, object]]]:
    book = load_workbook(BytesIO(content))
    result = {}
    for sheet in book.worksheets:
        rows = list(sheet.iter_rows(values_only=True))
        result[sheet.title] = [dict(zip(rows[0], row, strict=True)) for row in rows[1:]]
    return result


def test_weekly_excel_in_english():  # AC-57
    _load()
    file = ExportWeeklyReportService().handle(ExportWeeklyRequest(from_date=DAY, to_date=DAY, english=True))
    sheets = _sheets(file.content)
    assert list(sheets) == ["Overview", "Fac Vinh Long", "Fac 2", "Fac 3", "Fac 5"]
    overview = {row["Metric"]: row for row in sheets["Overview"]}
    assert overview["%Efficiency (with ratio)"]["Fac 2"] == 80
    assert overview["%Efficiency (with ratio)"]["HCM"] == pytest.approx(83.3)
    assert overview["%Efficiency (with ratio)"]["Fac Vinh Long"] == "-"
    assert overview["%Efficiency (with ratio) assessment"]["Fac 2"] == "Below threshold"
    assert overview["%Efficiency (with ratio) assessment"]["HCM"] == "Below threshold"
    assert {
        "Line",
        "Date",
        "%Efficiency (with ratio - system)",
        "%Efficiency (with ratio)",
        "CM earning",
    } <= set(sheets["Fac 2"][0])


def test_daily_excel_in_english():  # AC-57
    _load()
    file = ExportDailyReportService().handle(ExportDailyRequest(report_date=DAY, english=True))
    sheets = _sheets(file.content)
    assert list(sheets) == ["Factories", "Lines"]
    assert {row["Metric"]: row for row in sheets["Factories"]}["Output"]["HCM"] == 500
    assert sheets["Lines"][0]["Factory"] == "Fac 2"


def test_names_of_stored_values_are_only_translated_for_display():  # AC-58
    assert Factory.FAC_1.value == "Fac 1"
    assert english_name("Fac 1") == "Fac Vinh Long"
    assert english_name("Hiệu suất B") == "%Efficiency (with ratio)"
    assert english_name("Đổi mã hàng tuần") == "Weekly changeover"
    assert english_name("LINE 7") == "LINE 7"
    assert (
        english_terms("Hiệu suất A chỉ tính từ 24/10/2026.")
        == "%Efficiency (with ratio - system) chỉ tính từ 24/10/2026."
    )
    assert english_terms("Đã lưu số đổi mã hàng từ 24/10/2026.") == "Đã lưu số Changeover từ 24/10/2026."
