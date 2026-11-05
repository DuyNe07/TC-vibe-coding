"""Builds small data files in memory (never the real file) and small clean rows for the tests."""

from datetime import date
from decimal import Decimal
from io import BytesIO

from openpyxl import Workbook

from backend.core.base import UploadedFileDTO
from backend.features.sewing_productivity.models.clean_values import CleanRow
from backend.features.sewing_productivity.models.enums import Factory

FAC1 = "SVL-Factory 2"
FAC2 = "SHCM-Factory 2"
FAC3 = "SHCM-Factory 3"
FAC5 = "SHCM-Factory 5"

PRODUCTION_HEADERS = [
    "adj Date",
    "Factory",
    "Factory",
    "Customer Name",
    "Style",
    "PO#",
    "Product Name",
    "Color",
    "Line",
    "Product Inline Quantiy",
    "Price",
    "REVISE MO",
    "Revised OT 2",
    "SMV",
    "Standard output of SMV (have efficiency ratio)",
    "Match line strength",
]
TARGET_HEADERS = ["Line", "Date", "Items", "Style", "PO", "Daily Target (SMV)", "Daily Target (CM)", "Expertise"]
WORKER_HEADERS = ["No", "Week", None, "SF2", "SF3", "SF5", "SFVL", "SF2"]


def production(
    day: object = date(2026, 10, 24),
    factory: object = FAC2,
    line: object = "LINE 1",
    qty: object = 100,
    price: object = 1,
    sewers: object = 10,
    hours: object = 8,
    smv: object = 10,
    standard: object = 100,
    customer: object = "ELAND WORLD",
    style: object = "S1",
    po: object = "PO-1.1",
    name: object = "T-SHIRT",
    color: object = "NAVY",
    match: object = "",
) -> list[object]:
    return [
        day,
        factory,
        "other",
        customer,
        style,
        po,
        name,
        color,
        line,
        qty,
        price,
        sewers,
        hours,
        smv,
        standard,
        match,
    ]


def target(
    day: object = date(2026, 10, 24),
    line: object = "SF2 - Sewing Line 01",
    qty: object = 100,
    cm: object = 50,
    expertise: object = "",
    item: object = "T-SHIRT",
    style: object = "S1",
    po: object = "PO-1",
) -> list[object]:
    return [line, day, item, style, po, qty, cm, expertise]


def worker(
    day: object = date(2026, 10, 24), sf2: object = None, sf3: object = None, sf5: object = None, sfvl: object = None
) -> list[object]:
    return [1, 1, day, sf2, sf3, sf5, sfvl, 999]


def data_file(
    production_rows: list[list[object]] | None = None,
    target_rows: list[list[object]] | None = None,
    worker_rows: list[list[object]] | None = None,
    production_headers: list[object] | None = None,
    skip_sheet: str | None = None,
    filename: str = "Data sewing 2026.xlsx",
) -> UploadedFileDTO:
    workbook = Workbook()
    workbook.remove(workbook.active)
    if skip_sheet != "Production data":
        sheet = workbook.create_sheet("Production data")
        sheet.append(["subtotal", None, None, 12345])  # row 1 holds subtotals
        sheet.append(production_headers or PRODUCTION_HEADERS)
        for row in production_rows if production_rows is not None else [production()]:
            sheet.append(row)
    if skip_sheet != "Target system":
        sheet = workbook.create_sheet("Target system")
        sheet.append(TARGET_HEADERS)
        for row in target_rows if target_rows is not None else [target()]:
            sheet.append(row)
    if skip_sheet != "Worker":
        sheet = workbook.create_sheet("Worker")
        sheet.append(["top"])
        sheet.append(WORKER_HEADERS)
        for row in worker_rows if worker_rows is not None else [worker(sf2=20)]:
            sheet.append(row)
    buffer = BytesIO()
    workbook.save(buffer)
    return UploadedFileDTO(filename=filename, content=buffer.getvalue())


def clean_row(
    day: date,
    line: str = "LINE 1",
    po: str = "PO-1",
    smv: str | None = "10",
    price: str = "1",
    qty: str = "100",
    factory: Factory = Factory.FAC_2,
    style: str = "S1",
) -> CleanRow:
    quantity = Decimal(qty)
    cm_price = Decimal(price)
    return CleanRow.model_construct(
        production_date=day,
        factory=factory,
        customer_name="C",
        customer_group="C",
        style=style,
        po_number=po,
        base_po=po,
        product_name="T-SHIRT",
        product_group="T-Shirt",
        line=line,
        quantity=quantity,
        cm_price=cm_price,
        cm_earning=quantity * cm_price,
        working_hours=Decimal(8),
        sewers=Decimal(10),
        smv=None if smv is None else Decimal(smv),
        standard_output=Decimal(100),
        is_mismatched=False,
    )
