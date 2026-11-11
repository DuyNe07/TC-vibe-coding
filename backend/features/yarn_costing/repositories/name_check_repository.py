"""Tên sợi (bổ sung 2026-11-11) tables xuan2894__yarn_costing__name_word / pending_word / name_part (4.29-4.31)."""

from collections.abc import Sequence

from backend.features.yarn_costing.models.enums import NamePartKind, NameWordKind, PendingWordStatus
from backend.features.yarn_costing.models.name_check import NamePart, NameWord, PendingUse, PendingWord
from backend.features.yarn_costing.repositories.yarn_sql_repository import YarnSqlRepository


class NameWordRepository(YarnSqlRepository[NameWord]):
    def by_word(self) -> dict[str, NameWord]:
        return {w.word: w for w in self.list_all()}

    def standard(self) -> set[str]:
        return {w.word for w in self.list_all() if w.kind == NameWordKind.CHUAN}

    def misspellings(self) -> dict[str, str]:
        return {w.word: w.correct_word for w in self.list_all() if w.kind == NameWordKind.SAI}

    def lookups(self, uses: dict[str, int]) -> tuple[dict[str, int], dict[str, str]]:
        """(Chữ chuẩn → số tên dùng, Cách viết sai → Chữ đúng) for BR-100."""
        words = self.list_all()
        standard = {w.word: uses.get(w.word, 0) for w in words if w.kind == NameWordKind.CHUAN}
        return standard, {w.word: w.correct_word for w in words if w.kind == NameWordKind.SAI}


class PendingWordRepository(YarnSqlRepository[PendingWord]):
    def by_word(self) -> dict[str, PendingWord]:
        return {w.word: w for w in self.list_all()}

    def record(self, words: Sequence[str], yarn_code: str, typed_by: str, reason: str) -> None:
        """BR-104: one use per unknown word; a word already resolved goes back to "Chờ duyệt"."""
        current = self.by_word()
        changed = []
        for word in dict.fromkeys(words):
            use = PendingUse(yarn_code=yarn_code, typed_by=typed_by, reason=reason)
            found = current.get(word)
            if found is None:
                changed.append(PendingWord(word=word, uses=[use]))
            else:
                changed.append(
                    found.model_copy(update={"uses": [*found.uses, use], "status": PendingWordStatus.CHO_DUYET})
                )
        if changed:
            self.save_many(changed)


class NamePartRepository(YarnSqlRepository[NamePart]):
    def groups(self) -> list[NamePart]:
        return sorted(self.find_by(kind=NamePartKind.NHOM), key=lambda p: p.text)

    def keywords(self) -> list[NamePart]:
        return sorted(self.find_by(kind=NamePartKind.TU_KHOA), key=lambda p: (p.sequence, p.text))
