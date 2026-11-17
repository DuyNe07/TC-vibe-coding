"""UC-72 Khai báo bảng đuôi mã → loại hàng (bổ sung 2026-11-17; 4.32, BR-116)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.material_stock_business import MaterialStockBusiness
from backend.features.yarn_costing.dto.material_dto import MaterialSaveResponse, SaveSuffixRulesRequest
from backend.features.yarn_costing.repositories.material_price_repository import CodeSuffixRuleRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository

USE_CASE = "UC-72"


class SaveSuffixRulesService(BaseService[SaveSuffixRulesRequest, MaterialSaveResponse]):
    def execute(self, request: SaveSuffixRulesRequest) -> MaterialSaveResponse:
        access = AccessBusiness()
        access.ensure_material_access(self.current_user, USE_CASE)
        business = MaterialStockBusiness()
        rows = business.clean_suffix_rows([(r.suffix, r.market, r.note) for r in request.rows])
        repo = CodeSuffixRuleRepository()
        save, removed, notes = business.plan_suffix_rules(rows, repo.list_all(), access.user_label(self.current_user))
        repo.save_many(save)
        for rule in removed:
            repo.delete(rule.id)  # cờ xoá, không xoá thật (người / lúc xoá được ghi lại)
        if notes:
            AuditLogRepository().add(access.audit_entry(self.current_user, USE_CASE, "Bảng đuôi mã", "; ".join(notes)))
        self.logger.info("Suffix rules saved: %s changed, %s removed", len(save), len(removed))
        return MaterialSaveResponse(message=f"Đã lưu bảng đuôi mã ({len(rows)} dòng).", saved_count=len(save) + len(removed))
