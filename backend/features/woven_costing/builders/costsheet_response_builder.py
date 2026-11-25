"""Costsheet entity (+ versions, history, buttons) -> CostsheetResponse (Screen 2)."""

from decimal import Decimal

from backend.core.base import BaseBuilder
from backend.features.woven_costing.builders.demand_chain_builder import DemandChainBuilder, warning_section
from backend.features.woven_costing.builders.parameter_builders import parameter_rows
from backend.features.woven_costing.dto.common_dto import WarningDTO
from backend.features.woven_costing.dto.costsheet_dto import (
    CostItemRowDTO,
    CostsheetInputDTO,
    CostsheetResponse,
    CostsheetResultDTO,
    DyeingLineDTO,
    ExtraCostDTO,
    FabricSnapshotDTO,
    HistoryDTO,
    ParameterOverrideDTO,
    ProfitRowDTO,
    StageCostDTO,
    TwistLineResultDTO,
    VersionDTO,
    YarnLineInputDTO,
    YarnLineViewDTO,
)
from backend.features.woven_costing.dto.fabric_dto import FabricYarnDTO
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.costsheet_input import ExtraCost
from backend.features.woven_costing.models.costsheet_result import StageCost
from backend.features.woven_costing.models.costsheet_view import CostsheetView
from backend.features.woven_costing.models.enums import NO_WEAVING_FORMS, CostsheetAction, OrderType

ZERO = Decimal(0)
# BR-23: stages multiplied by the quantity factor (Cone 1 / Cone 2 are the Cone stage)
QUANTITY_FACTOR_STAGES = ("Mắc Hồ", "Mắc phân băng", "Cone 1", "Cone 2", "Dệt", "Kiểm")


def stage_dto(stage: StageCost) -> StageCostDTO:
    """Stored stage amount already includes the quantity factor (BR-23): show it before and after."""
    applies = stage.stage in QUANTITY_FACTOR_STAGES
    before = stage.quantity * stage.norm if applies else stage.amount
    return StageCostDTO(**stage.model_dump(exclude={"amount"}), amount=before, applies_quantity_factor=applies,
                        amount_after_factor=stage.amount)  # fmt: skip


def quantity_factor_reason(sheet: Costsheet) -> str:
    """BR-23 why the factor: Vải Nhuộm (not applied), Thí Nghiệm, otherwise the greige meters."""
    if not sheet.result.calculated:
        return ""
    if sheet.sale_form in NO_WEAVING_FORMS:
        return f"{sheet.sale_form.value}: không áp dụng"
    if sheet.order_type == OrderType.TRIAL:
        return OrderType.TRIAL.value
    meters = f"{sheet.result.greige_meters:,.0f}".replace(",", ".")
    return f"{meters} m mộc"


def _div(value: Decimal, rate: Decimal) -> Decimal:
    return value / rate if rate else ZERO


def _extra(extra: ExtraCost | None) -> ExtraCostDTO | None:
    if extra is None:
        return None
    return ExtraCostDTO(name=extra.name, **extra.items.as_dict())


def input_dto(sheet: Costsheet) -> CostsheetInputDTO:
    hcm = sheet.hcm_dyeing.model_dump()
    hcm["extra_cost"] = _extra(sheet.hcm_dyeing.extra_cost)
    tcdn = sheet.tcdn_dyeing.model_dump()
    tcdn["extra_cost"] = _extra(sheet.tcdn_dyeing.extra_cost)
    return CostsheetInputDTO(
        dye_plant=sheet.dye_plant,
        customer_name=sheet.customer_name,
        market=sheet.market,
        order_type=sheet.order_type,
        style=sheet.style,
        sale_form=sheet.sale_form,
        greige_buy_price=sheet.greige_buy_price,
        delivery_date=sheet.delivery_date,
        costing_date=sheet.costing_date,
        tcfno=sheet.tcfno,
        order_meters=sheet.order_meters,
        price_type=sheet.price_type,
        oc_no=sheet.oc_no,
        shrinkage_exception=sheet.shrinkage_exception,
        shrinkage_reason=sheet.shrinkage_reason,
        note=sheet.note,
        yarn_lines=[
            YarnLineInputDTO(
                direction=y.direction,
                seq=y.seq,
                price_currency=y.price_currency,
                price_input=y.price_input,
                waste_rate=y.waste_rate,
                is_twisted=y.is_twisted,
                is_sized=y.is_sized,
            )  # fmt: skip
            for y in sheet.yarn_lines
        ],
        twist_lines=[t.model_dump() for t in sheet.twist_lines],
        twist_lines_suggested=sheet.twist_lines_suggested,
        twist_lines_live=sheet.twist_lines_live,
        twist_suggestions=[t.model_dump() for t in sheet.twist_suggestions],
        twist_suggestion_skips=sheet.twist_suggestion_skips,
        weaving=sheet.weaving.model_dump(),
        hcm_dyeing=hcm,
        tcdn_dyeing=tcdn,
        price=sheet.price.model_dump(),
        parameter_overrides=[
            ParameterOverrideDTO(code=o.parameter, used_value=o.used_value) for o in sheet.parameter_overrides
        ],
    )


class CostsheetResponseBuilder(BaseBuilder[CostsheetResponse]):
    def __init__(
        self,
        sheet: Costsheet,
        view: CostsheetView,
        *,
        actions: list[CostsheetAction] | None = None,
        editable: bool = False,
        message: str = "",
        auto_approved: bool = False,
        saved: bool = True,
    ) -> None:
        self.sheet = sheet
        self.defaults = view.defaults
        self.versions = view.versions or [sheet]
        self.history = view.history
        self.actions = actions or []
        self.editable = editable
        self.message = message
        self.auto_approved = auto_approved
        self.saved = saved

    def fabric(self) -> FabricSnapshotDTO:
        snap = self.sheet.fabric_snapshot
        specs = snap.specs.model_dump(exclude={"greige_shrink_warp", "greige_shrink_weft", "finished_shrink_warp",
                                                "finished_shrink_weft"})  # fmt: skip
        result = self.sheet.result
        return FabricSnapshotDTO(
            tcfno=snap.tcfno, fabric_name=snap.fabric_name, source=snap.source, greige_m_per_kg=result.greige_m_per_kg,
            finished_m_per_kg=result.finished_m_per_kg, overridden_fields=snap.overridden_fields,
            yarns=[FabricYarnDTO(**y.model_dump()) for y in snap.yarns], **specs,
        )  # fmt: skip

    def yarn_lines(self) -> list[YarnLineViewDTO]:
        results = {(r.direction, r.seq): r for r in self.sheet.result.yarn_lines}
        expired = {w.message for w in self.sheet.result.warnings if w.code == "BR-44"}
        rows = []
        for y in self.sheet.yarn_lines:
            r = results.get((y.direction, y.seq))
            rows.append(
                YarnLineViewDTO(
                    direction=y.direction,
                    seq=y.seq,
                    yarn_name=y.yarn_name,
                    twist_tpm=y.twist_tpm,
                    ratio=y.ratio,
                    price_currency=y.price_currency,
                    price_input=y.price_input,
                    price_vnd=y.price_vnd,
                    price_entered_on=y.price_entered_on,
                    price_expired=any(y.yarn_name in m for m in expired),
                    waste_rate=y.waste_rate,
                    is_twisted=y.is_twisted,
                    is_sized=y.is_sized,
                    size_suggest_reason=y.size_suggest_reason,
                    loss_rate=r.loss_rate if r else ZERO,
                    yarn_kg=r.yarn_kg if r else ZERO,
                    amount=r.amount if r else ZERO,
                )  # fmt: skip
            )
        return rows

    def result(self) -> CostsheetResultDTO:
        r = self.sheet.result
        rate = r.exchange_rate or self.sheet.exchange_rate
        simple = {name: getattr(r, name) for name in CostsheetResultDTO.model_fields if hasattr(r, name)}
        for name in ("twist_lines", "weaving_stages", "cost_items", "dyeing_lines"):
            simple.pop(name, None)

        def money(label: str, vnd: Decimal, below: bool = False) -> ProfitRowDTO:
            return ProfitRowDTO(label=label, vnd=vnd, usd=_div(vnd, rate), below_threshold=below)

        profit = [
            money("Giá bán", r.sell_price_vnd),
            money("Giá vốn", r.cogs_vnd),
            money("GP", r.gp),
            ProfitRowDTO(label="GP%", vnd=r.gp_pct, usd=r.gp_pct, is_percent=True, below_threshold=r.gp_below),
            money("S&A", r.sa),
            money("Commission", r.commission),
            money("F&I", r.freight_insurance),
            money("Lãi vay", r.interest_cost),
            money("OP", r.op),
            ProfitRowDTO(label="OP%", vnd=r.op_pct, usd=r.op_pct, is_percent=True, below_threshold=r.op_below),
            money("Giá có VAT", r.price_with_vat),
        ]
        return CostsheetResultDTO(
            **simple,
            twist_difference_kg=r.twist_estimated_kg - r.twist_entered_kg,
            unit_cost_usd=_div(r.unit_cost_vnd, rate),
            cogs_usd=_div(r.cogs_vnd, rate),
            sell_price_usd=_div(r.sell_price_vnd, rate),
            twist_lines=[TwistLineResultDTO(direction=t.direction, count=t.count, quantity_kg=t.quantity_kg,
                                            norm=t.norm.total, amount=t.amount, error=t.error) for t in r.twist_lines],
            quantity_factor_reason=quantity_factor_reason(self.sheet),
            weaving_stages=[stage_dto(s) for s in r.weaving_stages],
            cost_items=[CostItemRowDTO(stage=c.stage, total=c.items.total, **c.items.as_dict()) for c in r.cost_items],
            dyeing_lines=[DyeingLineDTO(group=d.group, name=d.name, factor=d.factor, loss_rate=d.loss_rate,
                                        per_kg=d.per_kg, per_m=d.per_m, note=d.note, **d.items.as_dict())
                          for d in r.dyeing_lines],
            profit_rows=profit,
            demand_chain=DemandChainBuilder(self.sheet).build(),
        )  # fmt: skip

    def build(self) -> CostsheetResponse:
        s = self.sheet
        warnings = [
            WarningDTO(code=w.code, message=w.message, blocking=w.blocking, section=warning_section(w.code, w.message))
            for w in s.result.warnings
        ]
        return CostsheetResponse(
            id=s.id,
            costsheet_no=s.costsheet_no,
            version=s.version,
            status=s.status,
            editable=self.editable,
            allowed_actions=self.actions,
            message=self.message,
            warnings=warnings,
            warning_texts=[w.message for w in warnings],
            auto_approved=self.auto_approved,
            saved=self.saved,
            sales_username=s.sales_username,
            sales_name=s.sales_name,
            team=s.team,
            approved_by_name=s.approved_by_name,
            approved_at=s.approved_at,
            return_reason=s.return_reason,
            cancel_reason=s.cancel_reason,
            copied_from=s.copied_from,
            exchange_rate=s.exchange_rate,
            norm_set_code=s.norm_set_code,
            parameter_set_date=s.parameter_set_date,
            fabric_overridden=s.fabric_overridden,
            size_suggest_reason=next((y.size_suggest_reason for y in s.yarn_lines if y.size_suggest_reason), ""),
            input=input_dto(s),
            fabric=self.fabric(),
            yarn_lines=self.yarn_lines(),
            result=self.result(),
            parameters=parameter_rows(self.defaults, s),
            versions=[
                VersionDTO(id=v.id, version=v.version, status=v.status, costing_date=v.costing_date,
                           sell_price_vnd=v.result.sell_price_vnd, cogs_vnd=v.result.cogs_vnd, gp_pct=v.result.gp_pct,
                           approved_by_name=v.approved_by_name, approved_at=v.approved_at)
                for v in sorted(self.versions, key=lambda v: v.version)
            ],
            history=[HistoryDTO(version=h.version, action=h.action, by_name=h.by_name, at=h.created_at,
                                comment=h.comment) for h in self.history],
        )  # fmt: skip
