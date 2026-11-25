"""DTOs of the dyeing job order ("phiếu gia công nhuộm", Screen 8, UC-40..UC-46, 2026-11-25)."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseDTO, BaseRequestDTO, BaseResponseDTO
from backend.features.woven_costing.dto.common_dto import WarningDTO
from backend.features.woven_costing.dto.costsheet_dto import DyeingLineDTO, HcmDyeingInputDTO, TcdnDyeingInputDTO
from backend.features.woven_costing.models.enums import CostsheetAction, CostsheetStatus, DyePlant

ZERO = Decimal(0)


class CostItemsDTO(BaseDTO):
    """7 cost items (đ/m)."""

    chemical: Decimal = ZERO
    labor: Decimal = ZERO
    depreciation: Decimal = ZERO
    power: Decimal = ZERO
    fuel: Decimal = ZERO
    material: Decimal = ZERO
    overhead: Decimal = ZERO


class DyeingJobLineDTO(BaseDTO):
    """4.22 one line as typed."""

    finished_bc_rate: Decimal = ZERO
    item_code: str = ""
    style: str = ""
    oc_no: str = ""
    odno: str = ""
    g_per_m: Decimal | None = None
    g_per_m2: Decimal | None = None
    shrinkage: Decimal = ZERO
    quantity_m: Decimal | None = None
    job_price_vnd: Decimal | None = None
    tcdn_dyeing: TcdnDyeingInputDTO = Field(default_factory=TcdnDyeingInputDTO)
    hcm_dyeing: HcmDyeingInputDTO = Field(default_factory=HcmDyeingInputDTO)
    quoted_items: CostItemsDTO = Field(default_factory=CostItemsDTO)


class DyeingJobLineResultDTO(BaseDTO):
    """4.23 one line."""

    cost_lines: list[DyeingLineDTO] = Field(default_factory=list)
    items: CostItemsDTO = Field(default_factory=CostItemsDTO)
    factor: Decimal = Decimal(1)
    quoted: bool = False
    cost_per_m: Decimal = ZERO
    cost_per_m_finished: Decimal = ZERO
    total_cost: Decimal = ZERO
    revenue: Decimal = ZERO
    gp: Decimal = ZERO
    gp_pct: Decimal = ZERO
    gp_below: bool = False
    process_text: str = ""


class DyeingJobInputDTO(BaseDTO):
    """4.21 header + 4.22 lines as typed on Screen 8."""

    contract_no: str = ""
    customer_name: str = ""
    dye_plant: DyePlant = DyePlant.TCDN
    costing_date: date | None = None
    note: str = ""
    lines: list[DyeingJobLineDTO] = Field(default_factory=list)


class DyeingJobInputRequest(BaseRequestDTO, DyeingJobInputDTO):
    """UC-41 / UC-42 / UC-43 (submit): the job order and the cells typed on screen (None = keep the stored ones)."""

    job_id: str


class CreateDyeingJobRequest(BaseRequestDTO):
    customer_name: str
    contract_no: str = ""
    dye_plant: DyePlant = DyePlant.TCDN
    costing_date: date | None = None


class DyeingJobActionRequest(BaseRequestDTO):
    job_id: str
    reason: str = ""
    input: DyeingJobInputDTO | None = None  # submit: the typed cells are saved first


class GetDyeingJobRequest(BaseRequestDTO):
    job_id: str


class DyeingJobResponse(BaseResponseDTO):
    id: str = ""
    job_no: str = ""
    status: CostsheetStatus = CostsheetStatus.NHAP
    editable: bool = False
    allowed_actions: list[CostsheetAction] = Field(default_factory=list)
    input: DyeingJobInputDTO = Field(default_factory=DyeingJobInputDTO)
    exchange_rate: Decimal = ZERO
    norm_set_code: str = ""
    parameter_set_date: date | None = None
    sales_name: str = ""
    team: str = ""
    approved_by_name: str = ""
    approved_at: datetime | None = None
    return_reason: str = ""
    cancel_reason: str = ""
    copied_from: str = ""
    calculated: bool = False
    lines: list[DyeingJobLineResultDTO] = Field(default_factory=list)
    total_quantity: Decimal = ZERO
    total_cost: Decimal = ZERO
    total_revenue: Decimal = ZERO
    gp: Decimal = ZERO
    gp_pct: Decimal = ZERO
    gp_threshold: Decimal = ZERO
    gp_below: bool = False
    warnings: list[WarningDTO] = Field(default_factory=list)
    message: str = ""


class ListDyeingJobsRequest(BaseRequestDTO):
    keyword: str = ""
    statuses: list[CostsheetStatus] = Field(default_factory=list)
    customer_name: str = ""
    date_from: date | None = None
    date_to: date | None = None


class DyeingJobRowDTO(BaseDTO):
    id: str
    job_no: str
    status: CostsheetStatus
    costing_date: date
    customer_name: str = ""
    contract_no: str = ""
    dye_plant: DyePlant = DyePlant.TCDN
    line_count: int = 0
    total_quantity: Decimal = ZERO
    total_revenue: Decimal = ZERO
    gp: Decimal = ZERO
    gp_pct: Decimal = ZERO
    gp_below: bool = False
    sales_name: str = ""
    approved_by_name: str = ""


class DyeingJobListResponse(BaseResponseDTO):
    rows: list[DyeingJobRowDTO] = Field(default_factory=list)
