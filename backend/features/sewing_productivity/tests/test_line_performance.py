"""UC-31, BR-78, BR-79, BR-80: Screen 6 Line performance (AC-106 to AC-108)."""

from datetime import date

import pytest

from backend.features.sewing_productivity.dto.changeover_dto import ChangeoverRequest, Factory, LinePerformanceDTO
from backend.features.sewing_productivity.dto.overview_dto import OverviewRequest
from backend.features.sewing_productivity.dto.upload_dto import SaveUploadRequest
from backend.features.sewing_productivity.services.get_changeover_service import GetChangeoverService
from backend.features.sewing_productivity.services.get_overview_service import GetOverviewService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.tests.workbook_factory import FAC2, data_file, production, worker

DAY_1, DAY_2 = date(2026, 10, 24), date(2026, 10, 26)


def _load() -> None:
    rows = [
        production(DAY_1, FAC2, line="LINE 1", qty=100, standard=120, price=1.5, sewers=20, hours=8),
        production(DAY_2, FAC2, line="LINE 1", qty=50, standard=40, price=2, sewers=30, hours=8, color="BLUE"),
        production(DAY_2, FAC2, line="LINE 1", qty=30, standard=None, price=1, sewers=30, hours=8, color="RED"),
        production(DAY_1, FAC2, line="LINE 2", qty=200, standard=250, price=1, sewers=25, hours=9, po="PO-2.1"),
    ]
    workers = [worker(DAY_1, sf2=45), worker(DAY_2, sf2=30)]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, [], workers)))


def _table() -> dict[str, LinePerformanceDTO]:
    request = ChangeoverRequest(from_date=DAY_1, to_date=DAY_2, factories=[Factory.FAC_2], line_performance=True)
    response = GetChangeoverService().handle(request)
    assert response.has_data
    return {row.line: row for row in response.line_performance}


def test_ac106_br78_one_line():
    _load()
    line = _table()["LINE 1"]
    assert line.operators == pytest.approx(25)
    assert (line.target_output, line.output) == (160, 180)
    assert line.output_ratio == pytest.approx(150 / 160 * 100)
    assert (line.target_value, line.value) == (pytest.approx(260), pytest.approx(280))
    assert line.value_ratio == pytest.approx(250 / 260 * 100)


def test_ac107_br79_total_matches_screen_1_and_lines_are_sorted():
    _load()
    table = _table()
    assert list(table) == ["LINE 1", "LINE 2", "Tổng"]
    total = table["Tổng"]
    assert total.is_total
    assert total.operators == pytest.approx(table["LINE 1"].operators + table["LINE 2"].operators)
    assert total.target_value == pytest.approx(260 + 250)
    overview = GetOverviewService().handle(OverviewRequest(from_date=DAY_1, to_date=DAY_2, factories=[Factory.FAC_2]))
    values = {metric.metric: metric.values["Fac 2"] for metric in overview.metrics}
    assert total.output == pytest.approx(values["Sản lượng"])
    assert total.output_ratio == pytest.approx(values["Hiệu suất B"])
    assert total.value == pytest.approx(values["Tiền CM"])
    assert total.mo8h == pytest.approx(values["MO 8h"])


def test_ac108_br80_below_threshold_flags_follow_br28():
    _load()
    table = _table()
    line_2 = table["LINE 2"]  # 200 / 250 = 80 %: below the seeded efficiency threshold
    assert line_2.output_ratio == pytest.approx(80)
    assert line_2.output_ratio_below is True
    assert isinstance(line_2.mo8h_below, bool)


def test_no_data_gives_an_empty_table():
    request = ChangeoverRequest(from_date=DAY_1, to_date=DAY_2, factories=[Factory.FAC_2], line_performance=True)
    response = GetChangeoverService().handle(request)
    assert (response.has_data, response.line_performance) == (False, [])
