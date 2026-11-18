"""BR-64 the weekly report in the layout of the weekly meeting workbook (AC-72 to AC-74)."""

from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from backend.features.sewing_productivity.dto.export_dto import ExportWeeklyRequest
from backend.features.sewing_productivity.dto.overview_dto import Factory
from backend.features.sewing_productivity.dto.upload_dto import SaveUploadRequest
from backend.features.sewing_productivity.services.export_weekly_report_service import ExportWeeklyReportService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.tests.workbook_factory import (
    FAC2,
    FAC3,
    data_file,
    production,
    target,
    worker,
)

DAY_1 = date(2026, 10, 24)
DAY_2 = date(2026, 10, 26)


def _load() -> None:
    """Fac 2: LINE 1 on two days (target A 500 each), LINE 2 on day 1. Fac 3: LINE 1 on day 1."""
    rows = [
        production(DAY_1, FAC2, line="LINE 1", qty=400, price=1, sewers=10, hours=8),
        production(DAY_2, FAC2, line="LINE 1", qty=450, price=1, sewers=10, hours=8),
        production(DAY_1, FAC2, line="LINE 2", qty=100, price=2, sewers=5, hours=8),
        production(DAY_1, FAC3, line="LINE 1", qty=300, price=3, sewers=20, hours=10),
    ]
    targets = [
        target(DAY_1, line="SF2 - Sewing Line 01", qty=500),
        target(DAY_2, line="SF2 - Sewing Line 01", qty=500),
        target(DAY_1, line="SF3 - Sewing Line 01", qty=300),
    ]
    workers = [worker(DAY_1, sf2=15, sf3=20), worker(DAY_2, sf2=10)]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, targets, workers)))


def _file(**values):
    request = ExportWeeklyRequest(from_date=DAY_1, to_date=DAY_2, english=True, meeting_format=True, **values)
    return ExportWeeklyReportService().handle(request)


def _row(sheet, label: str, column: str = "B", start: int = 1) -> int:
    for row in range(start, sheet.max_row + 1):
        if sheet[f"{column}{row}"].value == label:
            return row
    raise AssertionError(f"{label} not found")


def test_overall_sheet_like_the_meeting_workbook():  # AC-72
    _load()
    file = _file()
    assert file.filename == "Sewing - Weekly Fac report - 24.10 to 26.10.xlsx"
    book = load_workbook(BytesIO(file.content))
    assert book.sheetnames == [
        "Overall",
        "Fac Vinh Long-detailed",
        "Fac 2-detailed",
        "Fac 3-detailed",
        "Fac 5-detailed",
    ]
    overall = book["Overall"]
    assert overall["A1"].value == "Sewing Weekly performance (24.10 to 26.10)"
    assert overall["A1"].font.color.rgb.endswith("FF0000")
    assert [overall.cell(2, column).value for column in range(3, 8)] == [
        "Fac Vinh Long", "Fac 2", "Fac 3", "Fac 5", "HCM",
    ]  # fmt: skip
    assert (overall["A3"].value, overall["B3"].value, overall["D3"].value) == ("Efficiency", "Target", 1000)
    assert overall["D4"].value == 950  # Fac 2 output: 400 + 450 + 100
    assert overall["D6"].value == pytest.approx(0.85)  # efficiency A: (400 + 450) / 1000
    assert overall["D7"].font.color.rgb.endswith("FF0000")
    assert overall["C3"].value == "-"  # Fac Vinh Long has no data
    cm_row = _row(overall, "CM earning", "A")
    assert overall[f"D{cm_row}"].value == 1050
    assert "$" in overall[f"D{cm_row}"].number_format
    assert overall[f"G{cm_row}"].value == 1950  # HCM: 1 050 + 900


def test_factory_sheet_has_the_three_blocks():  # AC-73
    _load()
    sheet = load_workbook(BytesIO(_file().content))["Fac 2-detailed"]
    assert (sheet["A1"].value, sheet["A3"].value, sheet["B3"].value, sheet["C3"].value) == (
        "Start of week",
        24,
        10,
        2026,
    )
    assert sheet["A5"].value == "Output (pcs)"
    assert sheet["A6"].value == "SF2"
    line_1 = _row(sheet, "LINE 1", "A")
    # day 1: target 500, actual 400, efficiency 80%; day 2: 500, 450, 90%; period: 1000, 850, 85%
    assert [sheet.cell(line_1, column).value for column in range(2, 8)] == [500, 400, pytest.approx(0.8), 500, 450, 0.9]
    assert [sheet.cell(line_1, column).value for column in range(8, 11)] == [1000, 850, pytest.approx(0.85)]
    total = _row(sheet, "Total", "A")
    assert sheet.cell(total, 9).value == 950
    titles = [cell.value for cell in sheet[3]]
    assert "Earning ($)" in titles and "MO 8h ($/8h)" in titles
    labour = [cell.value for row in sheet.iter_rows() for cell in row if cell.value in ("LABOR", "HOUR")]
    assert labour == ["LABOR", "HOUR"]


def test_line_detail_downloads_one_factory():  # AC-74
    _load()
    book = load_workbook(BytesIO(_file(factories=[Factory.FAC_2]).content))
    assert book.sheetnames == ["Overall", "Fac 2-detailed"]
    assert book["Overall"]["E3"].value == "-"  # Fac 3 not chosen


def test_the_old_weekly_file_is_unchanged_without_the_meeting_format():  # regression of UC-11
    _load()
    request = ExportWeeklyRequest(from_date=DAY_1, to_date=DAY_2, english=True)
    assert load_workbook(BytesIO(ExportWeeklyReportService().handle(request).content)).sheetnames[0] == "Overview"
