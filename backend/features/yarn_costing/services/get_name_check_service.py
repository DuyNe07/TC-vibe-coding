"""UC-65 Kiểm tra tên sợi + dữ liệu các thẻ Từ điển, Chữ mới chờ duyệt, Nhóm sợi & từ khoá (bổ sung 2026-11-11).

Lần mở đầu tiên khởi tạo từ điển và nhóm sợi / từ khoá (BR-103); chữ chờ duyệt của sợi đã được tính giá tự vào từ điển (BR-104)."""

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.name_check_business import NameCheckBusiness
from backend.features.yarn_costing.dto.name_dto import (
    GetNameCheckRequest,
    NameCheckResponse,
    NamePartDTO,
    NameWordDTO,
    PendingUseDTO,
    PendingWordDTO,
    SuspectNameDTO,
)
from backend.features.yarn_costing.models.enums import (
    NameIssueKind,
    NameWordKind,
    NameWordSource,
    PendingWordStatus,
    YarnStatus,
)
from backend.features.yarn_costing.models.name_check import NameWord
from backend.features.yarn_costing.repositories.name_check_repository import (
    NamePartRepository,
    NameWordRepository,
    PendingWordRepository,
)
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

USE_CASE = "UC-65"
PRICED = (YarnStatus.DA_TINH_GIA, YarnStatus.CO_MA_KE_TOAN)


class GetNameCheckService(BaseService[GetNameCheckRequest, NameCheckResponse]):
    def execute(self, request: GetNameCheckRequest) -> NameCheckResponse:
        access = AccessBusiness()
        access.ensure_allowed(self.current_user, USE_CASE)
        business = NameCheckBusiness()
        yarns = YarnRepository().list_all()
        words_repo, parts_repo, pending_repo = NameWordRepository(), NamePartRepository(), PendingWordRepository()
        label = access.user_label(self.current_user)
        if not words_repo.list_all():  # BR-103: once, while the dictionary is empty
            words_repo.save_many(business.initial_words(yarns, label))
        if not parts_repo.list_all():
            parts_repo.save_many(business.initial_parts(yarns))
        self._auto_add(yarns, words_repo, pending_repo, label)
        words = words_repo.list_all()
        uses = business.word_uses(yarns)
        standard = {w.word: uses.get(w.word, 0) for w in words if w.kind == NameWordKind.CHUAN}
        misspellings = {w.word: w.correct_word for w in words if w.kind == NameWordKind.SAI}
        suspects = business.suspects(yarns, standard, misspellings)
        counts = {kind.value: sum(1 for s in suspects if kind in s.issues) for kind in NameIssueKind}
        keyword = request.keyword.strip().casefold()
        shown = [
            s
            for s in suspects
            if (request.factory_code is None or s.factory_code == request.factory_code)
            and (not request.issues or any(i in request.issues for i in s.issues))
            and (not keyword or keyword in f"{s.yarn_code} {s.yarn_name}".casefold())
        ]
        pending = sorted(
            pending_repo.list_all(), key=lambda p: (p.status != PendingWordStatus.CHO_DUYET, -p.count, p.word)
        )
        return NameCheckResponse(
            counts=counts,
            suspects=[SuspectNameDTO(**s.model_dump()) for s in shown],
            words=[
                NameWordDTO(word=w.word, kind=w.kind, correct_word=w.correct_word, source=w.source)
                for w in sorted(words, key=lambda w: (w.kind != NameWordKind.CHUAN, w.word))
            ],
            pending=[
                PendingWordDTO(
                    id=p.id,
                    word=p.word,
                    count=p.count,
                    status=p.status,
                    last_at=max((u.at for u in p.uses), default=None),
                    suggestion=business.suggest(p.word, standard, misspellings),
                    resolved_word=p.resolved_word,
                    uses=[PendingUseDTO(**u.model_dump()) for u in p.uses],
                )
                for p in pending
            ],
            groups=[NamePartDTO(**p.model_dump(exclude={"created_at", "updated_at"})) for p in parts_repo.groups()],
            keywords=[NamePartDTO(**p.model_dump(exclude={"created_at", "updated_at"})) for p in parts_repo.keywords()],
        )

    def _auto_add(
        self, yarns: list, words_repo: NameWordRepository, pending_repo: PendingWordRepository, label: str
    ) -> None:
        """BR-104: words still waiting whose yarn has been priced since become standard words."""
        priced = {y.yarn_code for y in yarns if y.status in PRICED}
        known = words_repo.by_word()
        now = utc_now()
        for pending in pending_repo.list_all():
            if pending.status != PendingWordStatus.CHO_DUYET or not any(u.yarn_code in priced for u in pending.uses):
                continue
            if pending.word not in known:
                words_repo.add(NameWord(word=pending.word, source=NameWordSource.TU_THEM, created_by=label))
            pending_repo.save(
                pending.model_copy(
                    update={"status": PendingWordStatus.TU_THEM, "resolved_by": label, "resolved_at": now}
                )
            )
            self.logger.info("Word %s added to the dictionary (yarn priced)", pending.word)
