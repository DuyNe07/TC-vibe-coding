"""UC-67 Duyệt chữ mới (bổ sung 2026-11-11): "Thêm vào từ điển" hoặc "Sai, sửa thành" (BR-104, BR-106)."""

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.name_check_business import NameCheckBusiness, upper_name
from backend.features.yarn_costing.dto.name_dto import ResolvePendingResponse, ResolvePendingWordRequest
from backend.features.yarn_costing.exceptions import YarnNotFoundError, YarnValidationError
from backend.features.yarn_costing.models.enums import NameWordKind, NameWordSource, PendingWordStatus
from backend.features.yarn_costing.models.name_check import NameWord
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.name_check_repository import NameWordRepository, PendingWordRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

USE_CASE = "UC-67"
MSG_NOT_FOUND = "Không tìm thấy chữ chờ duyệt."
MSG_NOT_STANDARD = "Chữ đúng '{word}' chưa có trong từ điển."
MSG_SAME = "Chữ đúng phải khác chữ sai."


class ResolvePendingWordService(BaseService[ResolvePendingWordRequest, ResolvePendingResponse]):
    def execute(self, request: ResolvePendingWordRequest) -> ResolvePendingResponse:
        access = AccessBusiness()
        access.ensure_allowed(self.current_user, USE_CASE)
        pending_repo, words_repo = PendingWordRepository(), NameWordRepository()
        pending = pending_repo.get(request.pending_id)
        if pending is None:
            raise YarnNotFoundError(MSG_NOT_FOUND)
        label = access.user_label(self.current_user)
        now = utc_now()
        known = words_repo.by_word()
        audit = AuditLogRepository()
        if not request.correct_word.strip():
            if pending.word not in known:
                words_repo.add(NameWord(word=pending.word, source=NameWordSource.PHONG_SO, created_by=label))
            pending_repo.save(
                pending.model_copy(
                    update={"status": PendingWordStatus.DA_THEM, "resolved_by": label, "resolved_at": now}
                )
            )
            audit.add(access.audit_entry(self.current_user, USE_CASE, pending.word, "Thêm vào từ điển"))
            return ResolvePendingResponse(message=f"Đã thêm '{pending.word}' vào từ điển.")
        right = upper_name(request.correct_word)
        if right == pending.word:
            raise YarnValidationError(MSG_SAME)
        if right not in known or known[right].kind != NameWordKind.CHUAN:
            raise YarnValidationError(MSG_NOT_STANDARD.format(word=right))
        yarn_repo, group_repo = YarnRepository(), LossGroupRepository()
        yarns = yarn_repo.list_all()
        yarns_changed, groups_changed = NameCheckBusiness().replace_everywhere(
            pending.word, right, yarns, group_repo.list_all(), label, now
        )
        before = {y.id: y.yarn_name for y in yarns}
        named = sum(1 for y in yarns_changed if y.is_base and y.yarn_name != before[y.id])
        response = ResolvePendingResponse(
            message=f"Sửa '{pending.word}' thành '{right}': {named} tên sợi, {len(groups_changed)} nhóm tiêu hao sẽ đổi.",
            yarn_count=named,
            group_count=len(groups_changed),
        )
        if request.preview:
            return response
        yarn_repo.store(yarns, yarns_changed)
        group_repo.save_many(groups_changed)
        current = known.get(pending.word)
        wrong = NameWord(
            word=pending.word,
            kind=NameWordKind.SAI,
            correct_word=right,
            source=NameWordSource.PHONG_SO,
            created_by=label,
        )
        words_repo.save(
            current.model_copy(update={"kind": NameWordKind.SAI, "correct_word": right}) if current else wrong
        )
        pending_repo.save(
            pending.model_copy(
                update={
                    "status": PendingWordStatus.DA_SUA,
                    "resolved_word": right,
                    "resolved_by": label,
                    "resolved_at": now,
                }
            )
        )
        audit.add(
            access.audit_entry(
                self.current_user,
                USE_CASE,
                pending.word,
                f"Sửa '{pending.word}' → '{right}': {named} tên sợi, {len(groups_changed)} nhóm tiêu hao",
            )
        )
        self.logger.info("Word %s replaced by %s in %s yarns", pending.word, right, len(yarns_changed))
        return response.model_copy(
            update={
                "message": f"Đã sửa '{pending.word}' thành '{right}' trong {named} tên sợi và {len(groups_changed)} nhóm tiêu hao."
            }
        )
