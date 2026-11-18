"""BR-65, BR-66 (cards Avg SMV and %Direct labor) and the TOTAL block of sheet Worker (AC-75 to AC-78, AC-80)."""

from datetime import date
from io import BytesIO

import pytest
from openpyxl import load_workbook

from backend.core.base import UploadedFileDTO
from backend.features.sewing_productivity.dto.display_names import HCM_COLUMN, TOTAL_COLUMN
from backend.features.sewing_productivity.dto.overview_dto import Factory, OverviewRequest
from backend.features.sewing_productivity.dto.upload_dto import SaveUploadRequest
from backend.features.sewing_productivity.repositories.source_repositories import WorkerRecordRepository
from backend.features.sewing_productivity.services.get_overview_service import GetOverviewService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.tests.workbook_factory import FAC2, FAC3, data_file, production, worker

DAY = date(2026, 1, 2)
SMV_CARD = "SMV bình quân"
DIRECT_CARD = "%Direct labor"
# Row 2 of the real sheet Worker: TOTAL block, DIRECT block, an empty block, then % INDIRECT with the same titles
REAL_WORKER_HEADERS = [
    "YEAR", "MONTH", None, "Fac.2", "Fac.3", "Fac.5", "Fac.1(VL)", None, "SF2", "SF3", "SF5", "SFVL",
    None, "SF2", "SF3", "SF5", "SFVL", None, None, "Fac.2", "Fac.3", "Fac.5", "Fac.1(VL)",
]  # fmt: skip


def _real_worker_row(day: date, totals: tuple, directs: tuple) -> list[object]:
    """totals and directs in the order Fac 2, Fac 3, Fac 5, Fac 1; the % INDIRECT block holds ratios, not people."""
    return [2026, 1, day, *totals, None, *directs, None, None, None, None, None, None, None, 0.42, 0.43, 0.41, 0.48]


def _with_real_worker_sheet(file: UploadedFileDTO, rows: list[list[object]]) -> UploadedFileDTO:
    workbook = load_workbook(BytesIO(file.content))
    del workbook["Worker"]
    sheet = workbook.create_sheet("Worker")
    sheet.append([None, None, None, "TOTAL", None, None, None, None, "DIRECT"])
    sheet.append(REAL_WORKER_HEADERS)
    for row in rows:
        sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return UploadedFileDTO(filename=file.filename, content=buffer.getvalue())


def _save(production_rows: list[list[object]], worker_rows: list[list[object]] | None = None) -> None:
    file = data_file(production_rows, [], [worker(DAY, sf2=345, sf3=382)])
    if worker_rows is not None:
        file = _with_real_worker_sheet(file, worker_rows)
    SaveUploadService().handle(SaveUploadRequest(file=file))


def _cards(**filters) -> dict[str, dict[str, float | None]]:
    response = GetOverviewService().handle(OverviewRequest(from_date=DAY, to_date=DAY, **filters))
    return {card.metric: card.values for card in response.cards}


def test_total_block_is_stored_with_the_direct_sewers():
    _save([production(DAY, FAC2)], [_real_worker_row(DAY, (599, 670, 616, 1296), (345, 382, 361, 676))])
    stored = {record.factory.value: record for record in WorkerRecordRepository().list_all()}
    assert stored["Fac 2"].direct_sewers == 345
    assert stored["Fac 2"].total_workers == 599
    assert stored["Fac 1"].total_workers == 1296


def test_ac75_direct_labor_of_one_factory():
    _save([production(DAY, FAC2)], [_real_worker_row(DAY, (599, 670, 616, 1296), (345, 382, 361, 676))])
    cards = _cards(factories=[Factory.FAC_2])
    assert cards[DIRECT_CARD]["Fac 2"] == pytest.approx(345 / 599 * 100)
    assert round(cards[DIRECT_CARD]["Fac 2"], 1) == 57.6


def test_ac76_direct_labor_of_groups_adds_people_before_dividing():
    _save(
        [production(DAY, FAC2), production(DAY, FAC3)],
        [_real_worker_row(DAY, (599, 670, None, None), (345, 382, None, None))],
    )
    cards = _cards(factories=[Factory.FAC_2, Factory.FAC_3])
    expected = (345 + 382) / (599 + 670) * 100
    assert cards[DIRECT_CARD][TOTAL_COLUMN] == pytest.approx(expected)
    assert cards[DIRECT_CARD][HCM_COLUMN] == pytest.approx(expected)
    assert (
        _cards(factories=[Factory.FAC_2, Factory.FAC_3], customer_groups=["ELAND"])[DIRECT_CARD][TOTAL_COLUMN] is None
    )


def test_ac77_average_smv_is_weighted_by_output_and_follows_the_product_filter():
    _save(
        [
            production(DAY, FAC2, qty=100, smv=10, name="T-SHIRT"),
            production(DAY, FAC2, qty=300, smv=20, name="POLO", po="PO-2.1", style="S2"),
            production(DAY, FAC2, qty=50, smv=None, name="POLO", po="PO-3.1", style="S3"),
        ]
    )
    assert _cards(factories=[Factory.FAC_2])[SMV_CARD]["Fac 2"] == pytest.approx(17.5)
    filtered = _cards(factories=[Factory.FAC_2], product_groups=["T-Shirt"])
    assert filtered[SMV_CARD]["Fac 2"] == pytest.approx(10)


def test_ac78_file_without_total_block_shows_no_direct_labor_and_keeps_mo8h():
    _save([production(DAY, FAC2)])  # sheet Worker of an older file: no TOTAL block
    assert all(record.total_workers is None for record in WorkerRecordRepository().list_all())
    response = GetOverviewService().handle(OverviewRequest(from_date=DAY, to_date=DAY, factories=[Factory.FAC_2]))
    assert {card.metric: card.values for card in response.cards}[DIRECT_CARD]["Fac 2"] is None
    assert {metric.metric: metric.values for metric in response.metrics}["MO 8h"]["Fac 2"] is not None


def test_ac80_new_figures_stay_out_of_the_metrics_table():
    _save([production(DAY, FAC2)], [_real_worker_row(DAY, (599, 670, 616, 1296), (345, 382, 361, 676))])
    response = GetOverviewService().handle(OverviewRequest(from_date=DAY, to_date=DAY))
    names = {metric.metric for metric in response.metrics}
    assert SMV_CARD not in names
    assert DIRECT_CARD not in names
