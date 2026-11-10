"""UC-62 Tính giá báo khách và lưu (đợt 2; BR-89, BR-92..BR-97)."""

import re
from decimal import Decimal

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.material_dto_builders import quote_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.material_price_business import MaterialPriceBusiness
from backend.features.yarn_costing.business.material_stock_business import MaterialStockBusiness
from backend.features.yarn_costing.business.quote_business import QuoteBusiness
from backend.features.yarn_costing.dto.material_dto import CalculateQuoteRequest, QuoteResponse
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.enums import Incoterm
from backend.features.yarn_costing.models.material_price import Quote
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
        rate, _, averages, problem = MaterialPriceBusiness().month_view(inputs, MaterialStockBusiness().mapping_key)
        if problem:
            raise YarnValidationError(problem)
        if rate is None:
            raise YarnValidationError(MSG_PERIOD)
        priced, missing = business.material_components(yarn, request.groups, averages, request.market)
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
