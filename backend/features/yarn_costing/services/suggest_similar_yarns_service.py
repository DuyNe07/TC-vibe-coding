"""UC-49 Gợi ý sợi tương tự khi nhập tên (BR-76, BR-77; bổ sung 2026-11-10). Không lưu gì."""

from datetime import date

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import usd
from backend.features.yarn_costing.business.blend_business import BlendBusiness
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.customer_name_business import CustomerNameBusiness
from backend.features.yarn_costing.business.name_business import collapse_spaces
from backend.features.yarn_costing.dto.sales_dto import SuggestYarnsRequest, YarnSuggestionDTO, YarnSuggestionResponse
from backend.features.yarn_costing.models.blend import BlendSuggestion
from backend.features.yarn_costing.repositories.customer_name_repository import CustomerYarnNameRepository
from backend.features.yarn_costing.repositories.exchange_rate_repository import ExchangeRateRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

MSG_UNREADABLE = "App chưa đọc được thành phần từ tên này; chỉ tìm theo tên chuẩn và tên theo khách."
MSG_NONE = "Chưa có sợi trùng hoặc gần giống đã có giá."
KIND_LABELS = {"trung": "Trùng", "gan": "Gần giống"}


class SuggestSimilarYarnsService(BaseService[SuggestYarnsRequest, YarnSuggestionResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.blends = BlendBusiness()
        self.aliases = CustomerNameBusiness()

    def execute(self, request: SuggestYarnsRequest) -> YarnSuggestionResponse:
        name = collapse_spaces(request.yarn_name)
        if not name:
            return YarnSuggestionResponse()
        aliases = CustomerYarnNameRepository().list_all()
        factory = request.factory_code.value if request.factory_code else None
        parsed, same, near = self.blends.suggest(name, self.repository.list_all(), aliases, factory)
        rate = CostingBusiness().current_exchange_rate(ExchangeRateRepository().list_all(), date.today())
        by_base = self.aliases.by_base(aliases)

        def dto(s: BlendSuggestion) -> YarnSuggestionDTO:
            regular = s.yarn.regular_line
            total = regular.total_vnd if regular else None
            codes = [line.accounting_code for line in s.yarn.lines if line.accounting_code]
            return YarnSuggestionDTO(
                kind=KIND_LABELS[s.kind],
                factory_code=s.yarn.factory_code,
                yarn_code=s.yarn.yarn_code,
                yarn_name=s.yarn.yarn_name,
                customer_names_text=self.aliases.text(by_base.get(s.yarn.base_code, [])),
                note=s.note,
                status=s.yarn.status,
                total_vnd=total,
                usd_per_kg=usd(total, rate.rate if rate else None),
                accounting_code=", ".join(dict.fromkeys(c for c in codes if c)),
            )

        message = "" if parsed.readable else MSG_UNREADABLE
        if parsed.readable and not same and not near:
            message = MSG_NONE
        self.logger.info(
            "Suggest yarns %r: %s same, %s near (readable=%s)", name, len(same), len(near), parsed.readable
        )
        return YarnSuggestionResponse(
            readable=parsed.readable,
            blend_text=parsed.text,
            message=message,
            same=[dto(s) for s in same],
            near=[dto(s) for s in near],
            same_in_factory=[s.yarn.yarn_code for s in same if factory and s.yarn.factory_code.value == factory],
        )
