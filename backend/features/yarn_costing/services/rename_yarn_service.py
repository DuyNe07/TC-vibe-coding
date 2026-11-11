"""UC-68 Đổi tên một sợi (bổ sung 2026-11-11; BR-101, BR-104, BR-105, BR-109)."""

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.name_check_business import NameCheckBusiness
from backend.features.yarn_costing.dto.name_dto import RenameYarnRequest, RenameYarnResponse, UnknownWordDTO
from backend.features.yarn_costing.exceptions import YarnNotFoundError
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.name_check_repository import NameWordRepository, PendingWordRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

USE_CASE = "UC-68"
MSG_NOT_FOUND = "Không tìm thấy mã {code}."


class RenameYarnService(BaseService[RenameYarnRequest, RenameYarnResponse]):
    def execute(self, request: RenameYarnRequest) -> RenameYarnResponse:
        access = AccessBusiness()
        repo = YarnRepository()
        yarns = repo.list_all()
        picked = next((y for y in yarns if y.yarn_code == request.yarn_code.strip()), None)
        if picked is None:
            raise YarnNotFoundError(MSG_NOT_FOUND.format(code=request.yarn_code))
        access.ensure_allowed(self.current_user, USE_CASE, picked.factory_code.value)
        base = next(y for y in yarns if y.factory_code == picked.factory_code and y.yarn_code == picked.base_code)
        family = [y for y in yarns if y.factory_code == base.factory_code and y.base_code == base.base_code]
        business = NameCheckBusiness()
        groups_repo = LossGroupRepository()
        groups = groups_repo.list_all()
        standard, misspellings = NameWordRepository().lookups(business.word_uses(yarns))
        label = access.user_label(self.current_user)
        changed, changed_groups, old_key, new_key, check = business.plan_rename(
            base,
            family,
            request.new_name,
            request.reason,
            request.unknown_word_reason,
            access.is_so(self.current_user),
            yarns,
            groups,
            standard,
            misspellings,
            label,
            utc_now(),
        )
        response = RenameYarnResponse(
            old_name=base.yarn_name,
            new_name=check.name,
            old_loss_group=old_key,
            new_loss_group=new_key,
            unknown=[UnknownWordDTO(word=u.word, suggestion=u.suggestion) for u in check.unknown],
        )
        if request.preview:
            return response
        repo.store(yarns, changed)
        groups_repo.save_many(changed_groups)
        if check.unknown:
            PendingWordRepository().record(
                [u.word for u in check.unknown], base.yarn_code, label, request.unknown_word_reason.strip()
            )
        detail = f"'{base.yarn_name}' → '{check.name}'" + (
            f"; nhóm tiêu hao {old_key} → {new_key}" if old_key != new_key else ""
        )
        AuditLogRepository().add(
            access.audit_entry(self.current_user, USE_CASE, base.yarn_code, detail, request.reason.strip())
        )
        self.logger.info(
            "Yarn %s renamed (%s versions, %s loss groups)", base.yarn_code, len(family), len(changed_groups)
        )
        return response.model_copy(
            update={"saved": True, "message": f"Đã đổi tên {base.yarn_code}: '{base.yarn_name}' → '{check.name}'."}
        )
