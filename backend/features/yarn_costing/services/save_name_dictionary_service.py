"""UC-66 Quản lý từ điển tên chuẩn (bổ sung 2026-11-11, BR-103): bảng sửa trong ô, dòng bỏ đi = cờ xoá."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.name_check_business import NameCheckBusiness
from backend.features.yarn_costing.dto.name_dto import NameSaveResponse, SaveNameDictionaryRequest
from backend.features.yarn_costing.models.enums import NameWordKind, NameWordSource
from backend.features.yarn_costing.models.name_check import NameWord
from backend.features.yarn_costing.repositories.name_check_repository import NameWordRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.shared.utils.text import strip_accents

USE_CASE = "UC-66"


def clean(word: str) -> str:
    return strip_accents(word or "").upper().strip()


class SaveNameDictionaryService(BaseService[SaveNameDictionaryRequest, NameSaveResponse]):
    def execute(self, request: SaveNameDictionaryRequest) -> NameSaveResponse:
        access = AccessBusiness()
        access.ensure_allowed(self.current_user, USE_CASE)
        repo = NameWordRepository()
        current = repo.by_word()
        label = access.user_label(self.current_user)
        incoming = [
            NameWord(
                word=clean(w.word),
                kind=w.kind,
                correct_word=clean(w.correct_word) if w.kind == NameWordKind.SAI else "",
                source=current[clean(w.word)].source if clean(w.word) in current else NameWordSource.PHONG_SO,
                created_by=label,
            )
            for w in request.words
            if clean(w.word)
        ]
        NameCheckBusiness().ensure_dictionary(incoming)
        added, edited = [], []
        for w in incoming:
            old = current.get(w.word)
            if old is None:
                added.append(w)
            elif (old.kind, old.correct_word) != (w.kind, w.correct_word):
                edited.append(old.model_copy(update={"kind": w.kind, "correct_word": w.correct_word}))
        kept = {w.word for w in incoming}
        removed = [w for word, w in current.items() if word not in kept]
        repo.save_many([*added, *edited])
        for w in removed:
            repo.delete(w.id)
        if added or edited or removed:
            AuditLogRepository().add(
                access.audit_entry(
                    self.current_user,
                    USE_CASE,
                    "Từ điển tên chuẩn",
                    f"Thêm {', '.join(w.word for w in added) or '-'}; sửa {', '.join(w.word for w in edited) or '-'}; "
                    f"xoá {', '.join(w.word for w in removed) or '-'}",
                )
            )
        return NameSaveResponse(
            message=f"Đã lưu từ điển: {len(added)} chữ thêm, {len(edited)} sửa, {len(removed)} xoá.",
            saved_count=len(added) + len(edited) + len(removed),
        )
