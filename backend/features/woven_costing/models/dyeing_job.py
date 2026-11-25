"""4.21-4.23 (2026-11-25) dyeing job order ("phiếu gia công nhuộm", file NGC): many item lines approved at once."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import Field

from backend.core.base import BaseEntity, BaseValueObject
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.costsheet import EDITABLE_STATUSES
from backend.features.woven_costing.models.costsheet_input import HcmDyeingInput, TcdnDyeingInput
from backend.features.woven_costing.models.costsheet_result import CostWarning, DyeingLine
from backend.features.woven_costing.models.enums import CostsheetStatus, DyePlant

ZERO = Decimal(0)
MAX_JOB_LINES = 30


class DyeingJobLine(BaseValueObject):
    """4.22 one item / OC of the job order."""

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
    tcdn_dyeing: TcdnDyeingInput = Field(default_factory=TcdnDyeingInput)
    hcm_dyeing: HcmDyeingInput = Field(default_factory=HcmDyeingInput)
    quoted_items: CostItems = Field(default_factory=CostItems)

    @property
    def has_data(self) -> bool:
        """Any typed cell keeps the line (fix 2026-11-25: a line with only g/m typed was dropped)."""
        texts = (self.item_code, self.style, self.oc_no, self.odno)
        numbers = (self.g_per_m, self.g_per_m2, self.quantity_m, self.job_price_vnd)
        return any(t.strip() for t in texts) or any(n for n in numbers) or bool(self.shrinkage or self.finished_bc_rate)


class DyeingJobLineResult(BaseValueObject):
    """4.23 one line: cost lines, đ/m, amounts, GP."""

    cost_lines: list[DyeingLine] = Field(default_factory=list)
    items: CostItems = Field(default_factory=CostItems)
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
    warnings: list[CostWarning] = Field(default_factory=list)


class DyeingJobResult(BaseValueObject):
    """4.23 totals of the job order (BR-95)."""

    calculated: bool = False
    lines: list[DyeingJobLineResult] = Field(default_factory=list)
    total_quantity: Decimal = ZERO
    total_cost: Decimal = ZERO
    total_revenue: Decimal = ZERO
    gp: Decimal = ZERO
    gp_pct: Decimal = ZERO
    gp_threshold: Decimal = ZERO
    gp_below: bool = False
    warnings: list[CostWarning] = Field(default_factory=list)


class DyeingJob(BaseEntity):
    """4.21 header + 4.22 lines + 4.23 stored result."""

    job_no: str
    status: CostsheetStatus = CostsheetStatus.NHAP
    copied_from: str = ""
    created_by: str = ""
    contract_no: str = Field(default="", max_length=60)
    customer_name: str = ""
    dye_plant: DyePlant = DyePlant.TCDN
    costing_date: date
    exchange_rate: Decimal = ZERO
    norm_set_code: str = ""
    parameter_set_date: date | None = None
    note: str = Field(default="", max_length=1000)
    sales_username: str = ""
    sales_name: str = ""
    team: str = ""
    approved_by: str = ""
    approved_by_name: str = ""
    approved_at: datetime | None = None
    return_reason: str = ""
    cancel_reason: str = ""
    lines: list[DyeingJobLine] = Field(default_factory=list)
    result: DyeingJobResult = Field(default_factory=DyeingJobResult)

    @property
    def is_editable_status(self) -> bool:
        return self.status in EDITABLE_STATUSES

    @property
    def label(self) -> str:
        return self.job_no
