"""UC-38 Lấy danh mục cho costsheet (lists of the norm set in force, customers, roles and team of the user)."""

from datetime import date

from backend.core.base import BaseService, EmptyRequest
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.norm_lookup_business import NormLookupBusiness
from backend.features.woven_costing.constants import (
    BLENDED,
    HCM_COLORS,
    HCM_MATERIALS,
    LIST_HCM_FEATURES,
    LIST_HCM_STAGES,
    LIST_SIZE_MATERIALS,
    LIST_SPECIAL_DYES,
    LIST_WR,
    TCDN_COLOR_ALL,
    TCDN_COLORS,
    TCDN_MATERIALS,
    TCDN_STANDARD_PREFIX,
)
from backend.features.woven_costing.dto.list_dto import (
    CostsheetOptionsResponse,
    CountOptionDTO,
    CustomerOptionDTO,
    UserOptionDTO,
)
from backend.features.woven_costing.models.enums import Team
from backend.features.woven_costing.repositories.costsheet_repository import CostsheetRepository
from backend.features.woven_costing.repositories.master_repository import CustomerRepository
from backend.features.woven_costing.repositories.norm_repository import NormSetRepository


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(v for v in values if v))


class GetCostsheetOptionsService(BaseService[EmptyRequest, CostsheetOptionsResponse]):
    def __init__(self, norms: NormSetRepository | None = None, today: date | None = None) -> None:
        self.norms = norms or NormSetRepository()
        self.today = today or date.today()

    def execute(self, request: EmptyRequest) -> CostsheetOptionsResponse:
        access = AccessBusiness()
        sets = self.norms.list_with_seed()
        current = self.norms.effective_on(self.today) or sets[-1]
        lookup = NormLookupBusiness(current.tables)
        tables = current.tables
        customers = [c for c in CustomerRepository().sorted_by_name() if c.active]
        sales = {(s.sales_username, s.sales_name, s.team) for s in CostsheetRepository().list_all() if s.sales_username}
        # 4.16 (fixed 2026-11-23): only the stages with their own row in 4.5.10, never a name of the list alone
        stage_codes = [p.code for p in tables.tcdn_processes if not p.code.startswith(TCDN_STANDARD_PREFIX)]
        self.logger.info("UC-38 options from norm set %s, %s customers", current.norm_set_code, len(customers))
        return CostsheetOptionsResponse(
            customers=[
                CustomerOptionDTO(name=c.name, customer_code=c.customer_code, team=c.team.value) for c in customers
            ],
            teams=[t.value for t in Team],
            sales_users=[UserOptionDTO(username=u, name=n, team=t) for u, n, t in sorted(sales, key=lambda x: x[1])],
            counts=[CountOptionDTO(fiber_system=c.fiber_system, count=c.count) for c in tables.yarn_counts],
            twists=sorted(set(tables.twist_levels)),
            size_materials=_unique(lookup.list_values(LIST_SIZE_MATERIALS) or [n.material for n in tables.size_norms]),
            hcm_dye_materials=list(HCM_MATERIALS),
            hcm_color_levels=[*HCM_COLORS, BLENDED],
            hcm_special_stages=_unique(lookup.list_values(LIST_HCM_STAGES) or [s.name for s in tables.hcm_stages]),
            hcm_special_features=_unique(
                lookup.list_values(LIST_HCM_FEATURES) or [f.feature for f in tables.hcm_features]
            ),
            tcdn_dye_materials=list(TCDN_MATERIALS),
            tcdn_color_levels=[*TCDN_COLORS, TCDN_COLOR_ALL, BLENDED],
            tcdn_stages=_unique(stage_codes),
            special_dyes=lookup.list_values(LIST_SPECIAL_DYES),
            wr_chemicals=lookup.list_values(LIST_WR),
            my_roles=sorted(access.roles(self.current_user)),
            my_team=access.team(self.current_user),
        )
