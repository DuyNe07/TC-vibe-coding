"""BR-55, BR-56: the efficiency without ratio beside the two with-ratio kinds (AC-59 to AC-63)."""

from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from backend.features.sewing_productivity.dto.display_names import english_name
from backend.features.sewing_productivity.dto.export_dto import ExportWeeklyRequest
from backend.features.sewing_productivity.dto.line_detail_dto import LineDetailRequest
from backend.features.sewing_productivity.dto.line_mo_dto import LineMoRequest
from backend.features.sewing_productivity.dto.monthly_dto import MonthlyReportRequest
from backend.features.sewing_productivity.dto.overview_dto import (
    ChartsRequest,
    Factory,
    OverviewRequest,
    RankingMetric,
)
from backend.features.sewing_productivity.dto.upload_dto import SaveUploadRequest
from backend.features.sewing_productivity.services.export_line_mo_service import ExportLineMoService
from backend.features.sewing_productivity.services.export_weekly_report_service import ExportWeeklyReportService
from backend.features.sewing_productivity.services.get_charts_service import GetChartsService
from backend.features.sewing_productivity.services.get_line_detail_service import GetLineDetailService
from backend.features.sewing_productivity.services.get_line_mo_service import GetLineMoService
from backend.features.sewing_productivity.services.get_monthly_report_service import GetMonthlyReportService
from backend.features.sewing_productivity.services.get_overview_service import GetOverviewService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.tests.workbook_factory import (
    FAC2,
    FAC3,
    PRODUCTION_HEADERS,
    data_file,
    production,
    target,
    worker,
)

DAY = date(2026, 10, 24)
NO_RATIO_HEADER = "Standard output of SMV (no efficiency ratio)"
NO_RATIO_METRIC = "Hiệu suất (không tỉ lệ)"


def _load(no_ratio_fac2: object = 800, no_ratio_fac3: object = 200) -> None:
    """Fac 2: output 400, with ratio 500, no ratio 800. Fac 3: output 100, with ratio 100, no ratio 200."""
    rows = [
        [*production(DAY, FAC2, qty=400, standard=500), no_ratio_fac2],
        [*production(DAY, FAC3, qty=100, standard=100), no_ratio_fac3],
    ]
    file = data_file(
        rows,
        [target(DAY, line="SF2 - Sewing Line 01", qty=1000)],
        [worker(DAY, sf2=10, sf3=10)],
        production_headers=[*PRODUCTION_HEADERS, NO_RATIO_HEADER],
    )
    SaveUploadService().handle(SaveUploadRequest(file=file))


def _overview(**filters):
    response = GetOverviewService().handle(OverviewRequest(from_date=DAY, to_date=DAY, **filters))
    return {row.metric: row for row in response.metrics}


def test_the_three_kinds_use_their_own_target():  # AC-59
    _load()
    metrics = _overview()
    assert metrics["Hiệu suất A"].values["Fac 2"] == pytest.approx(40)  # system: 400 / 1000
    assert metrics["Hiệu suất B"].values["Fac 2"] == pytest.approx(80)  # sum with ratio: 400 / 500
    assert metrics[NO_RATIO_METRIC].values["Fac 2"] == pytest.approx(50)  # sum without ratio: 400 / 800
    assert metrics["Mục tiêu (không tỉ lệ)"].values["Fac 2"] == 800


def test_no_ratio_in_the_hcm_column():  # AC-60
    _load()
    metrics = _overview()
    assert metrics[NO_RATIO_METRIC].values["HCM"] == pytest.approx(500 * 100 / 1000)
    assert metrics["Mục tiêu (không tỉ lệ)"].values["HCM"] == 1000


def test_no_ratio_has_no_threshold_mark():  # AC-61
    _load()  # 50% is far under the 90% threshold of the with-ratio kinds
    assert _overview()[NO_RATIO_METRIC].below["Fac 2"] is False


def test_no_ratio_on_the_other_reports():  # AC-62
    _load()
    charts = GetChartsService().handle(ChartsRequest(from_date=DAY, to_date=DAY, ranking_metric=RankingMetric.NO_RATIO))
    assert {point.factory: point.value for point in charts.efficiency_no_ratio} == {"Fac 2": 50, "Fac 3": 50}
    assert charts.hcm_efficiency_no_ratio[0].value == pytest.approx(50)
    assert charts.top_lines[0].value == pytest.approx(50)
    detail = GetLineDetailService().handle(LineDetailRequest(from_date=DAY, to_date=DAY, factory=Factory.FAC_2))
    assert (detail.rows[0].target_no_ratio, detail.rows[0].efficiency_no_ratio) == (800, 50)
    monthly = GetMonthlyReportService().handle(MonthlyReportRequest(from_date=DAY, to_date=DAY))
    fac2 = next(item for item in monthly.factories if item.factory == "Fac 2")
    assert (fac2.rows[0].efficiency_no_ratio, fac2.rows[-1].efficiency_no_ratio) == (50, 50)
    line_mo = GetLineMoService().handle(LineMoRequest(from_date=DAY, to_date=DAY, factory=Factory.FAC_2))
    assert line_mo.no_ratio_table.rows[0].period.value == pytest.approx(50)
    assert line_mo.no_ratio_table.rows[-1].is_total is True


def test_no_ratio_in_excel():  # AC-62
    _load()
    weekly = ExportWeeklyReportService().handle(ExportWeeklyRequest(from_date=DAY, to_date=DAY, english=True))
    book = load_workbook(BytesIO(weekly.content))
    labels = {row[0].value: row for row in book["Overview"].iter_rows(min_row=2)}
    assert "%Efficiency (no ratio)" in labels
    assert "%Efficiency (no ratio)" in [cell.value for cell in book["Fac 2"][1]]
    line_mo = ExportLineMoService().handle(
        LineMoRequest(from_date=DAY, to_date=DAY, factory=Factory.FAC_2, english=True)
    )
    assert "%Efficiency (no ratio)" in load_workbook(BytesIO(line_mo.content)).sheetnames


def test_a_file_without_the_column_shows_a_dash():  # AC-63
    rows = [production(DAY, FAC2, qty=400, standard=500)]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, [], [worker(DAY, sf2=10)])))
    metrics = _overview()
    assert metrics[NO_RATIO_METRIC].values["Fac 2"] is None
    assert metrics["Hiệu suất B"].values["Fac 2"] == pytest.approx(80)


def test_names_of_the_kinds():  # AC-59
    assert english_name("Hiệu suất A") == "%Efficiency (with ratio - system)"
    assert english_name("Hiệu suất B") == "%Efficiency (with ratio)"
    assert english_name(NO_RATIO_METRIC) == "%Efficiency (no ratio)"
