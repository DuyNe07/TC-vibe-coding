"""UC-62 Tính giá báo khách và lưu (đợt 2; BR-89, BR-92..BR-97)."""

import re
from decimal import Decimal

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.material_dto_builders import quote_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.material_price_business import MaterialPriceBusiness, month_text
from backend.features.yarn_costing.business.material_stock_business import MaterialStockBusiness
from backend.features.yarn_costing.business.quote_business import (
    MSG_NO_SUPIMA_GROUP,
    SUPIMA_LOSS_GROUP,
    QuoteBusiness,
)
from backend.features.yarn_costing.dto.material_dto import CalculateQuoteRequest, QuoteResponse
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.enums import Incoterm
from backend.features.yarn_costing.models.material_price import (
    COTTON_PLAN_ID,
    CottonShare,
    GroupAverage,
    MaterialPriceGroup,
    MonthlyMaterialSetting,
    Quote,
    SupimaMix,
)
from backend.features.yarn_costing.models.yarn import Yarn
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.material_price_repository import QuoteRepository, load_month_inputs
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

USE_CASE = "UC-62"
PERIOD = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
MSG_PERIOD = "Vui lòng chọn tháng tính."


def usd_text(value: object) -> str:
    return f"{float(value):,.4f}".replace(",", " ").replace(".", ",").replace(" ", ".")  # type: ignore[arg-type]


class CalculateQuoteService(BaseService[CalculateQuoteRequest, QuoteResponse]):
    def execute(self, request: CalculateQuoteRequest) -> QuoteResponse:
        access = AccessBusiness()
        access.ensure_material_access(self.current_user, USE_CASE)
        if not PERIOD.match(request.period):
            raise YarnValidationError(MSG_PERIOD)
        business = QuoteBusiness()
        yarn = next((y for y in YarnRepository().list_all() if request.line_code and y.line(request.line_code)), None)
        line = business.price_line(yarn, request.price_kind) if yarn else None
        accounting_code = "".join(request.accounting_code.split()).upper()
        customer = " ".join(request.customer_name.split())
        components = yarn.components if yarn else []
        business.ensure_valid(
            yarn,
            line,
            request.market,
            request.order_qty,
            request.norm_factor,
            request.gp_percent,
            request.commission_percent,
            request.incoterm,
            request.fi_usd,
            [(c.material_label, request.groups.get(c.material_label, "")) for c in components],
            accounting_code,
            customer,
            request.note.strip(),
        )
        if yarn is None or line is None:  # already refused by BR-96 (keeps the types narrow)
            raise YarnValidationError(MSG_PERIOD)
        inputs = load_month_inputs(request.period)
        prices = MaterialPriceBusiness()
        rate, monthly, averages, problem = prices.month_view(inputs, MaterialStockBusiness().mapping_key)
        if problem:
            raise YarnValidationError(problem)
        if rate is None:
            raise YarnValidationError(MSG_PERIOD)
        # BR-110 / BR-111 (bổ sung 2026-11-13): phương án bông riêng của lần tính + pha Supima
        uses_cotton = any(request.groups.get(c.material_label) == COTTON_PLAN_ID for c in yarn.components)
        plan = (
            [CottonShare(origin=s.origin, percent=s.percent) for s in request.cotton_plan]
            if request.cotton_plan is not None
            else list(monthly.cotton_plan)
        )
        cotton, supima, coin_fee = None, None, Decimal(0)
        if uses_cotton:
            if request.cotton_plan is not None:
                business.ensure_plan(plan)
            cotton = prices.plan_average(request.market, averages, inputs.groups, monthly, plan, request.period)
            business.ensure_supima_ratio(request.supima_percent)
            if request.supima_percent > 0:
                supima, coin_fee = self._supima(yarn, request, monthly, averages, inputs.groups, business)
        priced, missing = business.material_components(
            yarn, request.groups, averages, request.market, cotton=cotton, supima=supima
        )
        if missing:
            raise YarnValidationError(missing[0])
        stock_qty, stock_cost = business.yarn_stock(accounting_code, inputs.stock_lines, rate)
        label = access.user_label(self.current_user)
        base = Quote(
            quote_no="",
            period=request.period,
            line_code=line.line_code,
            base_code=yarn.base_code,
            price_kind=request.price_kind,
            yarn_name=yarn.yarn_name,
            accounting_code=accounting_code,
            customer_name=customer,
            market=request.market,
            order_qty=request.order_qty,
            norm_factor=request.norm_factor,
            gp_percent=request.gp_percent,
            commission_percent=request.commission_percent,
            incoterm=request.incoterm,
            fi_usd=request.fi_usd if request.incoterm == Incoterm.CIF else Decimal(0),
            exchange_rate=rate,
            note=request.note.strip(),
            created_by=label,
            created_username=self.current_user.username if self.current_user else "",
            cotton_plan=plan if uses_cotton else [],
            supima_percent=request.supima_percent if uses_cotton else Decimal(0),
            supima_coin=bool(supima is not None and request.supima_coin),
            coin_fee_usd=coin_fee,
        )
        quote = business.calculate(base, priced, line.total_vnd, stock_qty, stock_cost)
        if not request.commit:
            return QuoteResponse(message="", quote=quote_dto(quote))
        repo = QuoteRepository()
        quote = quote.model_copy(update={"quote_no": business.next_number(repo.all_numbers(), utc_now().date())})
        repo.add(quote)
        price_text = f"FOB {usd_text(quote.fob_usd)} USD/kg"
        if quote.cif_usd is not None:
            price_text += f", CIF {usd_text(quote.cif_usd)} USD/kg"
        AuditLogRepository().add(
            access.audit_entry(
                self.current_user,
                USE_CASE,
                quote.quote_no,
                f"{quote.line_code} {quote.yarn_name}; {quote.customer_name or '-'}; {price_text}",
            )
        )
        self.logger.info("Quote %s saved for %s", quote.quote_no, quote.line_code)
        return QuoteResponse(
            message=f"Đã lưu báo giá {quote.quote_no} cho sợi {quote.yarn_name}: {price_text}.",
            saved=True,
            quote=quote_dto(quote),
        )

    def _supima(
        self,
        yarn: Yarn,
        request: CalculateQuoteRequest,
        monthly: MonthlyMaterialSetting,
        averages: list[GroupAverage],
        groups: dict[str, MaterialPriceGroup],
        business: QuoteBusiness,
    ) -> tuple[SupimaMix, Decimal]:
        """BR-111: giá tính Supima (BQ − hồi phế nhóm Supima tháng M), phí coin, tiêu hao Supima và bông thường."""
        if monthly.supima_group_id not in groups:
            raise YarnValidationError(MSG_NO_SUPIMA_GROUP.format(month=month_text(request.period)))
        found = next(
            (a for a in averages if a.group_id == monthly.supima_group_id and a.market == request.market), None
        )
        if found is None or found.net is None:
            raise YarnValidationError(found.note if found is not None and found.note else MSG_PERIOD)
        fee = monthly.coin_usd * (1 + monthly.coin_tax) if request.supima_coin else Decimal(0)
        factory = yarn.factory_code.value
        loss_groups = LossGroupRepository().list_all()
        partial = request.supima_percent < 1
        mix = SupimaMix(
            ratio=request.supima_percent,
            net=found.net,
            coin_fee=fee,
            loss=business.group_loss(loss_groups, SUPIMA_LOSS_GROUP, factory) if partial else Decimal(0),
            normal_loss=business.group_loss(loss_groups, business.normal_loss_key(yarn), factory)
            if partial
            else Decimal(0),
        )
        return mix, fee
