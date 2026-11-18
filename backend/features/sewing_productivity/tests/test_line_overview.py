"""BR-83, BR-84 (Line Detail, sửa 2026-11-12) and BR-85 (Line performance Excel): AC-112 to AC-114, AC-116."""

from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from backend.core.current_user import CurrentUser, set_current_user
from backend.features.sewing_productivity.dto.changeover_dto import ChangeoverRequest
from backend.features.sewing_productivity.dto.line_detail_dto import Factory, LineDetailRequest
from backend.features.sewing_productivity.dto.upload_dto import SaveUploadRequest
from backend.features.sewing_productivity.services.export_changeover_service import ExportChangeoverService
from backend.features.sewing_productivity.services.get_line_detail_service import GetLineDetailService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.tests.test_line_strength import strength_file
from backend.features.sewing_productivity.tests.workbook_factory import FAC2, data_file, production, worker

D20, D24, D25, D26, D27 = (date(2026, 10, day) for day in (20, 24, 25, 26, 27))
WEEK = (D24, date(2026, 10, 30))


def _load() -> None:
    rows = [
        # LINE 2: PO-7 first on 20/10 (before the week), PO-8 new on 25/10, PO-9 since 20/10
        production(D20, FAC2, line="LINE 2", po="PO-7.1", qty=10, style="S7"),
        production(D20, FAC2, line="LINE 2", po="PO-9.1", qty=10, style="S9"),
        production(D25, FAC2, line="LINE 2", po="PO-7.2", qty=100, style="S7", name="PANTS"),
        production(D25, FAC2, line="LINE 2", po="PO-8.1", qty=200, style="S8", name="POLO", price=2),
        production(D25, FAC2, line="LINE 2", po="PO-9.1", qty=50, style="S9", name="PANTS", color="RED"),
        # LINE 14: 3 days with MO 8h 30, 33, 36 (cm / sewers x 8 / hours), hours 8, 9, 10; 100 of 600 mismatched
        production(D24, FAC2, line="LINE 14", qty=150, price=1.5, sewers=10, hours=8, po="PO-1.1"),
        production(D24, FAC2, line="LINE 14", qty=100, price=0.75, sewers=10, hours=8, po="PO-1.1", color="RED",
                   match="Trái sở trường"),
        production(D26, FAC2, line="LINE 14", qty=100, price=3.7125, sewers=10, hours=9, po="PO-1.1"),
        production(D27, FAC2, line="LINE 14", qty=250, price=1.8, sewers=10, hours=10, po="PO-1.1"),
    ]  # fmt: skip
    workers = [worker(day, sf2=30) for day in (D20, D24, D25, D26, D27)]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, [], workers)))


@pytest.fixture(autouse=True)
def _updater():
    set_current_user(CurrentUser(username="an", is_admin=True))
    yield
    set_current_user(None)


def _detail():
    return GetLineDetailService().handle(LineDetailRequest(from_date=WEEK[0], to_date=WEEK[1], factory=Factory.FAC_2))


def test_ac113_changeover_counts_base_orders_new_on_the_line():
    _load()
    rows = {row.line: row for row in _detail().line_overview}
    assert rows["LINE 2"].changeover == 1  # PO-8 only: PO-7 started on 20/10 (its .2 part does not count)
    assert rows["Tổng"].changeover == sum(row.changeover for row in rows.values() if not row.is_total)


def test_ac112_br83_mo8h_hours_and_matching_ratio_of_a_line():
    _load()
    line = {row.line: row for row in _detail().line_overview}["LINE 14"]
    assert line.output == 600
    assert line.hours == pytest.approx(9)
    # AC-112 (sửa 2026-11-13): Matching ratio follows the saved line strengths (BR-86, AC-117), no longer the
    # `Match line strength` column: LINE 14 has no strength saved here, so "-"
    assert line.matching_ratio is None
    assert line.mo8h == pytest.approx(33, abs=0.01)


def test_ac114_br84_orders_of_a_line_with_its_strength():
    SaveUploadService().handle(SaveUploadRequest(file=strength_file()))
    _load()
    detail = _detail()
    assert [(s.line, s.strong_groups) for s in detail.strengths] == [("LINE 14", ["Pants", "T-Shirt"])]
    orders = [order for order in detail.line_orders if order.line == "LINE 2"]
    assert [order.base_po for order in orders] == ["PO-7", "PO-9", "PO-8"]  # by first day on the line
    po8 = orders[-1]
    assert (po8.first_day, po8.output, po8.cm_price, po8.product_types) == (D25, 200, 2, "Polo")
    assert all(order.matches is None for order in orders)  # LINE 2 of Fac 2 has no strength saved
    line14 = [order for order in detail.line_orders if order.line == "LINE 14"]
    assert line14[0].matches is True  # T-SHIRT -> T-Shirt, a strong group of LINE 14


def test_ac116_br85_line_performance_excel_in_the_user_layout():
    _load()
    request = ChangeoverRequest(from_date=WEEK[0], to_date=WEEK[1], factories=[Factory.FAC_2], line_performance=True)
    file = ExportChangeoverService().handle(request)
    assert file.filename == "Line performance - 24.10 to 30.10.xlsx"  # AC-116 (sửa 2026-11-13): one sheet per factory
    book = load_workbook(BytesIO(file.content))
    assert book.sheetnames == ["Fac Vinh Long", "Fac 2", "Fac 3", "Fac 5"]
    assert book["Fac 3"].cell(row=4, column=1).value == "No data in this period."
    sheet = book["Fac 2"]
    assert [sheet.cell(row=2, column=c).value for c in (1, 2, 3, 6, 9)] == [
        "Line", "Number of Operators", "Production Output (pcs)", "Production Value ($)", "MO $\n(Convert to 8h)",
    ]  # fmt: skip
    assert [sheet.cell(row=3, column=c).value for c in (3, 4, 5)] == ["Target", "Actual", "ratio"]
    lines = [sheet.cell(row=row, column=1).value for row in range(4, sheet.max_row + 1)]
    assert lines == ["LINE 2", "LINE 14", "Total"]
    assert sheet.cell(row=5, column=4).value == 600
