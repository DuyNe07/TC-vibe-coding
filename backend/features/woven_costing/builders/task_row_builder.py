"""UC-30 rows of "Việc chờ tôi" (2026-11-27: the "Chờ tôi duyệt" columns that let a leader approve from outside)."""

from datetime import datetime
from decimal import Decimal

from backend.core.base import BaseBuilder
from backend.features.woven_costing.builders.demand_chain_builder import DemandChainBuilder
from backend.features.woven_costing.dto.list_dto import TaskRowDTO
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.dyeing_job import DyeingJob

ZERO = Decimal(0)
CHAIN_COSTS = {"Chi phí Sợi": "yarn_per_m", "Chi phí Dệt": "weaving_per_m", "Chi phí Nhuộm": "dyeing_per_m"}


def _text(value: object) -> str | None:
    return str(value) if value is not None else None


class TaskRowBuilder(BaseBuilder[TaskRowDTO]):
    """A costsheet row; the full approval columns only when ``detail`` (group "Chờ tôi duyệt")."""

    def __init__(self, sheet: Costsheet, reason: str = "", *, detail: bool = False, attention: str = "",
                 previous: Costsheet | None = None, submitted_at: datetime | None = None) -> None:  # fmt: skip
        self.sheet = sheet
        self.reason = reason
        self.detail = detail
        self.attention = attention
        self.previous = previous
        self.submitted_at = submitted_at

    def build(self) -> TaskRowDTO:
        s, r = self.sheet, self.sheet.result
        row = TaskRowDTO(
            costsheet_id=s.id, costsheet_no=s.costsheet_no, version=s.version, customer_name=s.customer_name,
            tcfno=s.tcfno, sales_name=s.sales_name, costing_date=s.costing_date, gp_pct=r.gp_pct, op_pct=r.op_pct,
            reason=self.reason or None,
        )  # fmt: skip
        if not self.detail:
            return row
        price = s.price
        costs = {
            CHAIN_COSTS[step.step]: step.cost_per_m
            for step in DemandChainBuilder(s).build()
            if step.step in CHAIN_COSTS
        }
        prev = self.previous
        return row.model_copy(
            update={
                "team": s.team,
                "fabric_name": s.fabric_snapshot.fabric_name,
                "market": _text(s.market),
                "dye_plant": _text(s.dye_plant),
                "sale_form": _text(s.sale_form),
                "order_type": _text(s.order_type),
                "price_type": _text(s.price_type),
                "order_meters": s.order_meters,
                "submitted_at": self.submitted_at,
                "delivery_date": s.delivery_date,
                "sell_price": price.sell_price_input,
                "sell_currency": _text(price.sell_price_currency),
                "cogs_vnd": r.cogs_vnd if r.calculated else None,
                "gp_vnd": r.gp if r.calculated else None,
                "price_with_vat": r.price_with_vat if r.calculated else None,
                **costs,
                "shrinkage": r.shrinkage if r.calculated else None,
                "prev_sell_price": prev.price.sell_price_input if prev else None,
                "prev_gp_pct": prev.result.gp_pct if prev else None,
                "attention": self.attention,
                "gp_below": r.gp_below,
                "op_below": r.op_below,
                "note": s.note or None,
            }
        )


class JobTaskRowBuilder(BaseBuilder[TaskRowDTO]):
    """A dyeing job order row (2026-11-25); 2026-11-27 + contract, plant, totals and "Cần chú ý"."""

    def __init__(self, job: DyeingJob, reason: str = "", attention: str = "") -> None:
        self.job = job
        self.reason = reason
        self.attention = attention

    def build(self) -> TaskRowDTO:
        j, r = self.job, self.job.result
        return TaskRowDTO(
            costsheet_id=j.id, costsheet_no=j.job_no, customer_name=j.customer_name, sales_name=j.sales_name,
            costing_date=j.costing_date, gp_pct=r.gp_pct, reason=self.reason or None, contract_no=j.contract_no or None,
            dye_plant=_text(j.dye_plant), total_quantity=r.total_quantity if r.calculated else None,
            total_revenue=r.total_revenue if r.calculated else None, attention=self.attention, gp_below=r.gp_below,
        )  # fmt: skip
