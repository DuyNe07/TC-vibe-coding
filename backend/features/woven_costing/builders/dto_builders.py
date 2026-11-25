"""Models -> response DTOs of the lists (costsheets, fabrics, master data)."""

from decimal import Decimal

from backend.core.base import BaseBuilder
from backend.features.woven_costing.constants import NORM_GROUP_LISTS, NORM_SHEET_GROUPS, NORM_SHEET_TITLES
from backend.features.woven_costing.dto.fabric_dto import FabricDetailDTO, FabricRowDTO, FabricYarnDTO
from backend.features.woven_costing.dto.list_dto import CostsheetListRowDTO
from backend.features.woven_costing.dto.master_dto import (
    CustomerDTO,
    ExchangeRateDTO,
    FabricFactorDTO,
    HolidayDTO,
    NormSetRowDTO,
    NormTableDTO,
)
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.fabric import Fabric
from backend.features.woven_costing.models.master import Customer, ExchangeRate, FabricFactor, Holiday
from backend.features.woven_costing.models.norm_file import NormWorkbook
from backend.features.woven_costing.models.norm_set import NormSet

ZERO = Decimal(0)


class CostsheetRowsBuilder(BaseBuilder[list[CostsheetListRowDTO]]):
    def __init__(self, sheets: list[Costsheet], warnings: dict[str, str]) -> None:
        self.sheets = sheets
        self.warnings = warnings

    def build(self) -> list[CostsheetListRowDTO]:
        rows = []
        for s in self.sheets:
            r = s.result
            rate = r.exchange_rate or s.exchange_rate
            rows.append(
                CostsheetListRowDTO(
                    id=s.id,
                    costsheet_no=s.costsheet_no,
                    version=s.version,
                    status=s.status,
                    costing_date=s.costing_date,
                    sales_name=s.sales_name,
                    team=s.team,
                    customer_name=s.customer_name,
                    market=s.market,
                    order_type=s.order_type,
                    oc_no=s.oc_no,
                    tcfno=s.tcfno,
                    sale_form=s.sale_form,
                    dye_plant=s.dye_plant,
                    price_type=s.price_type,
                    order_meters=s.order_meters,
                    sell_price_vnd=r.sell_price_vnd,
                    sell_price_usd=r.sell_price_vnd / rate if rate else ZERO,
                    cogs_vnd=r.cogs_vnd,
                    freight_insurance=r.freight_insurance,
                    gp_pct=r.gp_pct,
                    op_pct=r.op_pct,
                    warning_text=self.warnings.get(s.id, ""),
                    approved_by_name=s.approved_by_name,
                    approved_at=s.approved_at,
                )  # fmt: skip
            )
        return rows


def fabric_shrinkage(fabric: Fabric) -> Decimal | None:
    """Display only: (weft TP - weft greige) / weft TP of the master data."""
    finished = fabric.specs.finished_weft_density
    if not finished:
        return None
    return (finished - (fabric.specs.greige_weft_density or ZERO)) / finished


class FabricRowsBuilder(BaseBuilder[list[FabricRowDTO]]):
    def __init__(self, fabrics: list[Fabric]) -> None:
        self.fabrics = fabrics

    def build(self) -> list[FabricRowDTO]:
        return [
            FabricRowDTO(
                tcfno=f.tcfno,
                fabric_name=f.fabric_name,
                source=f.source,
                greige_width_cm=f.specs.greige_width_cm,
                greige_warp_density=f.specs.greige_warp_density,
                greige_weft_density=f.specs.greige_weft_density,
                greige_g_per_m=f.specs.greige_g_per_m,
                finished_width_cm=f.specs.finished_width_cm,
                finished_g_per_m=f.specs.finished_g_per_m,
                shrinkage=fabric_shrinkage(f),
                warping_loss_rate=f.specs.warping_loss_rate,
                created_date=f.created_date,
                updated_at=f.updated_at,
            )  # fmt: skip
            for f in self.fabrics
        ]


class FabricDetailBuilder(BaseBuilder[FabricDetailDTO]):
    def __init__(self, fabric: Fabric) -> None:
        self.fabric = fabric

    def build(self) -> FabricDetailDTO:
        f = self.fabric
        return FabricDetailDTO(
            tcfno=f.tcfno, tcfno_raw=f.tcfno_raw, sy_item=f.sy_item, fabric_name=f.fabric_name, structure=f.structure,
            fabric_kind=f.fabric_kind, tcfno_status=f.tcfno_status, created_date=f.created_date,
            in_charge=f.in_charge, source=f.source, remark=f.remark, updated_at=f.updated_at, updated_by=f.updated_by,
            yarns=[FabricYarnDTO(**y.model_dump()) for y in f.yarns], **f.specs.model_dump(),
        )  # fmt: skip


class NormTablesDtoBuilder(BaseBuilder[list[NormTableDTO]]):
    def __init__(self, book: NormWorkbook) -> None:
        self.book = book

    def build(self) -> list[NormTableDTO]:
        tables = []
        for sheet in self.book.sheets:
            columns = [c or " " for c in sheet.columns]
            rows = [dict(zip(columns, row, strict=False)) for row in sheet.rows]
            tables.append(NormTableDTO(sheet=sheet.name, title=NORM_SHEET_TITLES.get(sheet.name, sheet.name),
                                       group=NORM_SHEET_GROUPS.get(sheet.name, NORM_GROUP_LISTS),
                                       columns=columns, rows=rows))  # fmt: skip
        return tables


class MasterRowsBuilder(BaseBuilder[None]):
    """Small conversions of the Phòng SO lists (one method per list)."""

    def build(self) -> None:
        return None

    def rates(self, rates: list[ExchangeRate]) -> list[ExchangeRateDTO]:
        return [ExchangeRateDTO(month=r.month, year=r.year, rate=r.rate, updated_by=r.updated_by,
                                updated_at=r.updated_at) for r in rates]  # fmt: skip

    def factors(self, factors: list[FabricFactor]) -> list[FabricFactorDTO]:
        return [FabricFactorDTO(**f.model_dump(include=set(FabricFactorDTO.model_fields))) for f in factors]

    def holidays(self, holidays: list[Holiday]) -> list[HolidayDTO]:
        return [HolidayDTO(date=h.date, name=h.name) for h in sorted(holidays, key=lambda h: h.date)]

    def customers(self, customers: list[Customer]) -> list[CustomerDTO]:
        return [CustomerDTO(**c.model_dump(include=set(CustomerDTO.model_fields))) for c in customers]

    def norm_sets(self, sets: list[NormSet], current_code: str) -> list[NormSetRowDTO]:
        return [
            NormSetRowDTO(norm_set_code=s.norm_set_code, effective_from=s.effective_from, note=s.note,
                          uploaded_by=s.uploaded_by, uploaded_at=s.created_at, is_current=s.norm_set_code == current_code)
            for s in sets
        ]  # fmt: skip
