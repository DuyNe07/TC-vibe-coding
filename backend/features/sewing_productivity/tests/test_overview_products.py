"""Mở rộng 2026-11-13 lần 4: Overview "Products & customers" (BR-93 to BR-96), past-year files with only Production
data (BR-97) and the closed factory (BR-98). AC-133 to AC-139."""

from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from backend.core.base import EmptyRequest, UploadedFileDTO
from backend.core.current_user import CurrentUser, set_current_user
from backend.core.exceptions import AppError
from backend.features.sewing_productivity.dto.monthly_dto import MonthlyReportRequest, PeriodKind
from backend.features.sewing_productivity.dto.overview_dto import ChartsRequest, Factory, OverviewRequest
from backend.features.sewing_productivity.dto.upload_dto import SaveUploadRequest
from backend.features.sewing_productivity.repositories.source_repositories import (
    ProductionRecordRepository,
    UploadLogRepository,
    WorkerRecordRepository,
)
from backend.features.sewing_productivity.services.get_charts_service import GetChartsService
from backend.features.sewing_productivity.services.get_filter_options_service import GetFilterOptionsService
from backend.features.sewing_productivity.services.get_monthly_report_service import GetMonthlyReportService
from backend.features.sewing_productivity.services.get_overview_service import GetOverviewService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.tests.workbook_factory import FAC1, FAC2, FAC3, data_file, production, worker

DAY = date(2026, 10, 24)
WEEK = (DAY, date(2026, 10, 30))


@pytest.fixture(autouse=True)
def _updater():
    set_current_user(CurrentUser(username="an", is_admin=True))
    yield
    set_current_user(None)


def _save(rows: list[list[object]], days: tuple[date, ...] = (DAY,)) -> None:
    workers = [worker(day, sf2=30, sf3=30, sfvl=30) for day in days]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, [], workers)))


def _charts(**options):
    return GetChartsService().handle(ChartsRequest(from_date=WEEK[0], to_date=WEEK[1], products=True, **options))


def _mix_rows() -> list[list[object]]:
    return [
        production(DAY, FAC2, qty=600, name="T-SHIRT", po="PO-T.1", style="ST"),
        production(DAY, FAC2, qty=300, name="PANTS", po="PO-P.1", style="SP", customer="MCC"),
        production(DAY, FAC2, qty=100, name="POLO", po="PO-O.1", style="SO", customer="MCC"),
    ]


def test_ac133_br93_product_mix_by_factory_and_table():
    _save(_mix_rows())
    charts = _charts(factories=[Factory.FAC_2])
    fac2 = {item.group: item.share for item in charts.product_shares if item.column == "Fac 2"}
    assert fac2 == pytest.approx({"T-Shirt": 60, "Pants": 30, "Polo": 10})
    table = {(item.group, item.column): item for item in charts.product_table}
    assert table[("T-Shirt", "Fac 2")].output == 600
    assert table[("T-Shirt", "Total")].share == pytest.approx(60)
    filtered = _charts(factories=[Factory.FAC_2], customer_groups=["MCC"])  # BR-29: only the MCC rows
    assert {item.group: item.share for item in filtered.product_shares if item.column == "Fac 2"} == pytest.approx(
        {"Pants": 75, "Polo": 25}
    )


def test_br93_only_five_groups_then_other():
    names = ["T-SHIRT", "POLO", "PANTS", "JACKET", "HOODIE", "DRESS", "SWIMSUIT", "ZZZ NEW"]
    _save([production(DAY, FAC2, qty=100 * (10 - i), name=name, po=f"PO-{i}.1") for i, name in enumerate(names)])
    groups = [item.group for item in _charts().product_shares if item.column == "Total"]
    assert groups == ["T-Shirt", "Polo", "Pants", "Jacket", "Hoodie", "Other"]
    assert len([item for item in _charts().product_table if item.column == "Total"]) == len(names)


def test_ac134_br94_top_ten_customers_split_by_factory():
    rows = [production(DAY, FAC2, qty=100 + i, customer=f"CUST {i:02d}", po=f"PO-{i}.1") for i in range(12)]
    rows.append(production(DAY, FAC3, qty=50, customer="CUST 11", po="PO-X.1"))
    _save(rows)
    customers = _charts().top_customers
    names = list(dict.fromkeys(item.customer for item in customers))
    assert len(names) == 10
    assert names[0] == "CUST 11"  # 111 in Fac 2 + 50 in Fac 3
    assert {item.factory: item.output for item in customers if item.customer == "CUST 11"} == {
        "Fac 2": 111,
        "Fac 3": 50,
    }


def test_ac135_br95_average_cm_price_by_product_group():
    _save(
        [
            production(DAY, FAC2, qty=200, price=1.5, name="POLO", po="PO-A.1"),
            production(DAY, FAC2, qty=100, price=2.1, name="POLO", po="PO-B.1"),
        ]
    )
    prices = {item.group: item.cm_price for item in _charts().cm_by_group}
    assert prices["Polo"] == pytest.approx(1.7)


def test_ac136_br96_months_from_first_january():
    days = (date(2026, 8, 3), date(2026, 9, 4), DAY)
    _save([production(day, FAC2, qty=100, po=f"PO-{day.month}.1") for day in days], days=days)
    months = _charts().monthly_mix
    assert [item.month for item in months] == ["Aug 2026", "Sep 2026", "Oct 2026 (01.10–30.10)"]
    assert [item.output for item in months] == [100, 100, 100]


def _production_only(rows: list[list[object]]) -> UploadedFileDTO:
    """A workbook with the Production data sheet only (the 2025 file)."""
    book = load_workbook(BytesIO(data_file(rows).content))
    for name in ("Target system", "Worker"):
        del book[name]
    stream = BytesIO()
    book.save(stream)
    return UploadedFileDTO(filename="Data sewing 2025 (format 2026).xlsx", content=stream.getvalue())


DAY_2025 = date(2025, 1, 2)


def test_ac137_br97_past_year_file_derives_the_sewers_of_each_day():
    _save(_mix_rows(), days=(DAY,))
    rows = [
        production(DAY_2025, FAC2, line="LINE 1", sewers=20, po="PO-1.1"),
        production(DAY_2025, FAC2, line="LINE 1", sewers=22, po="PO-2.1", color="RED"),  # line average 21
        production(DAY_2025, FAC2, line="LINE 2", sewers=30, po="PO-3.1"),
    ]
    SaveUploadService().handle(SaveUploadRequest(file=_production_only(rows)))
    workers = {(w.work_date, w.factory): w for w in WorkerRecordRepository().list_all()}
    derived = workers[(DAY_2025, Factory.FAC_2)]
    assert (float(derived.direct_sewers), derived.derived) == (51, True)
    assert workers[(DAY, Factory.FAC_2)].derived is False  # 2026 untouched
    report = GetMonthlyReportService().handle(
        MonthlyReportRequest(
            from_date=DAY_2025, to_date=date(2025, 1, 31), factories=[Factory.FAC_2], period_kind=PeriodKind.MONTH
        )
    )
    values = {metric.metric: metric.rows[0].values["Fac 2"] for metric in report.period_metrics}
    assert values["MO 8h"] is not None
    assert values["%Direct labor"] is None
    sheets = [count.sheet for count in UploadLogRepository().list_all()[-1].sheet_counts]
    assert "Worker (tính từ Production data)" in sheets
    assert len([r for r in ProductionRecordRepository().list_all() if r.production_date == DAY]) == 3


def test_ac138_br97_a_2026_day_still_needs_every_sheet():
    rows = [production(DAY_2025, FAC2, po="PO-1.1"), production(date(2026, 1, 5), FAC2, po="PO-2.1")]
    with pytest.raises(AppError) as error:
        SaveUploadService().handle(SaveUploadRequest(file=_production_only(rows)))
    assert error.value.message == "File thiếu sheet: Target system, Worker. Hãy dùng đúng file Data sewing."
    assert ProductionRecordRepository().list_all() == []


def test_ac139_br98_closed_factory_is_stored_but_never_shown():
    rows = [
        production(DAY_2025, FAC2, qty=100, po="PO-1.1"),
        production(DAY_2025, "SHCM-Factory 1", qty=500, po="PO-9.1"),
        production(DAY_2025, FAC1, qty=100, po="PO-2.1"),
    ]
    SaveUploadService().handle(SaveUploadRequest(file=_production_only(rows)))
    stored = {record.factory for record in ProductionRecordRepository().list_all()}
    assert Factory.FAC_1_HCM in stored
    options = GetFilterOptionsService().handle(EmptyRequest())
    assert Factory.FAC_1_HCM.value not in options.lines_by_factory
    overview = GetOverviewService().handle(OverviewRequest(from_date=DAY_2025, to_date=DAY_2025))
    output = next(metric for metric in overview.metrics if metric.metric == "Sản lượng")
    assert Factory.FAC_1_HCM.value not in output.values
    assert sum(value or 0 for key, value in output.values.items() if key.startswith("Fac")) == 200
