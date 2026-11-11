"""BR-101 / BR-102 (bổ sung 2026-11-11): tên ghép từ ô ghép tên hoặc gõ tay + kết quả kiểm tra, hiện ngay khi Sales nhập."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.name_check_business import (
    MSG_PARENS,
    MSG_RATIO,
    NameCheckBusiness,
    upper_name,
)
from backend.features.yarn_costing.dto.name_dto import (
    CheckYarnNameRequest,
    NamePartDTO,
    UnknownWordDTO,
    YarnNameCheckResponse,
)
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.enums import NameIssueKind, NameMode, NameWordKind
from backend.features.yarn_costing.repositories.name_check_repository import NamePartRepository, NameWordRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class CheckYarnNameService(BaseService[CheckYarnNameRequest, YarnNameCheckResponse]):
    def execute(self, request: CheckYarnNameRequest) -> YarnNameCheckResponse:
        business = NameCheckBusiness()
        parts = NamePartRepository()
        groups, keywords = parts.groups(), parts.keywords()
        options = {
            "groups": [NamePartDTO(**g.model_dump(exclude={"created_at", "updated_at"})) for g in groups],
            "keywords": [NamePartDTO(**k.model_dump(exclude={"created_at", "updated_at"})) for k in keywords],
        }
        if request.mode == NameMode.GHEP:
            group = next((g for g in groups if g.text == upper_name(request.group)), None)
            chosen = [k for k in keywords if k.text in {upper_name(x) for x in request.keywords}]
            try:
                name = business.build_name(group, request.count, request.ratios, chosen)
            except YarnValidationError as exc:
                return YarnNameCheckResponse(problem=exc.message, **options)
        else:
            name = upper_name(request.yarn_name)
        if not name:
            return YarnNameCheckResponse(**options)
        words = NameWordRepository().list_all()
        uses = business.word_uses(YarnRepository().list_all()) if words else {}
        standard = {w.word: uses.get(w.word, 0) for w in words if w.kind == NameWordKind.CHUAN}
        misspellings = {w.word: w.correct_word for w in words if w.kind == NameWordKind.SAI}
        check = business.check(name, standard, misspellings)
        problem = ""
        if NameIssueKind.NGOAC in check.issues:
            problem = MSG_PARENS
        elif check.bad_ratios:
            ratio, total = check.bad_ratios[0].rsplit(" (", 1)
            problem = MSG_RATIO.format(ratio=ratio, total=total.rstrip(")"))
        return YarnNameCheckResponse(
            name=name,
            problem=problem,
            issues=check.issues,
            unknown=[UnknownWordDTO(word=u.word, suggestion=u.suggestion) for u in check.unknown],
            suggested_name=check.suggested_name,
            **options,
        )
