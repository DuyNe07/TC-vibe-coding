"""UC-70 Quản lý nhóm sợi và từ khoá của ô ghép tên (bổ sung 2026-11-11, BR-102, BR-103)."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.name_check_business import NameCheckBusiness, upper_name
from backend.features.yarn_costing.dto.name_dto import NameSaveResponse, SaveNamePartsRequest
from backend.features.yarn_costing.models.enums import NamePartKind, NamePartSource
from backend.features.yarn_costing.models.name_check import NamePart
from backend.features.yarn_costing.repositories.name_check_repository import NamePartRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository

USE_CASE = "UC-70"
FIELDS = ("text", "fiber_count", "sequence", "reviewed")


class SaveNamePartsService(BaseService[SaveNamePartsRequest, NameSaveResponse]):
    def execute(self, request: SaveNamePartsRequest) -> NameSaveResponse:
        access = AccessBusiness()
        access.ensure_allowed(self.current_user, USE_CASE)
        repo = NamePartRepository()
        current = {p.id: p for p in repo.list_all()}
        incoming = [
            NamePart(
                kind=p.kind,
                text=upper_name(p.text),
                fiber_count=p.fiber_count if p.kind == NamePartKind.NHOM else 1,
                sequence=p.sequence,
                source=current[p.id].source if p.id in current else NamePartSource.PHONG_SO,
                reviewed=p.reviewed,
            )
            for p in request.parts
            if upper_name(p.text)
        ]
        NameCheckBusiness().ensure_parts(incoming)
        ids = [p.id if p.id in current else "" for p in request.parts if upper_name(p.text)]
        changed = []
        for part, part_id in zip(incoming, ids, strict=True):
            old = current.get(part_id)
            if old is None:
                changed.append(part)
            elif any(getattr(old, f) != getattr(part, f) for f in FIELDS):
                changed.append(old.model_copy(update={f: getattr(part, f) for f in FIELDS}))
        removed = [p for pid, p in current.items() if pid not in set(ids)]
        repo.save_many(changed)
        for p in removed:
            repo.delete(p.id)
        groups = sum(1 for p in changed + removed if p.kind == NamePartKind.NHOM)
        keywords = len(changed) + len(removed) - groups
        if changed or removed:
            AuditLogRepository().add(
                access.audit_entry(
                    self.current_user,
                    USE_CASE,
                    "Nhóm sợi / từ khoá",
                    f"Lưu {', '.join(p.text for p in changed) or '-'}; xoá {', '.join(p.text for p in removed) or '-'}",
                )
            )
        return NameSaveResponse(
            message=f"Đã lưu {groups} nhóm sợi, {keywords} từ khoá.", saved_count=len(changed) + len(removed)
        )
