"""Tên sợi (bổ sung 2026-11-11): BR-100 kiểm tra tên, BR-101 kiểm tra khi gửi / đổi tên, BR-102 ô ghép tên, BR-103 khởi tạo,
BR-104 chữ mới, BR-105 đổi tên một sợi, BR-106 sửa chữ sai trong mọi tên, BR-107 chuẩn hoá viết hoa + tên trùng."""

import re
from collections import Counter
from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal, InvalidOperation

from backend.core.base import BaseBusiness
from backend.features.yarn_costing.business.blend_business import BlendBusiness
from backend.features.yarn_costing.business.name_business import YarnNameBusiness, collapse_spaces
from backend.features.yarn_costing.business.request_business import RequestBusiness
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.enums import (
    FactoryCode,
    NameIssueKind,
    NamePartKind,
    NamePartSource,
    NameWordKind,
    NameWordSource,
    YarnStatus,
)
from backend.features.yarn_costing.models.loss_group import LossGroup
from backend.features.yarn_costing.models.name_check import (
    DuplicateDecision,
    NameCheck,
    NamePart,
    NameWord,
    SuspectName,
    UnknownWord,
)
from backend.features.yarn_costing.models.yarn import OldName, Yarn
from backend.shared.utils.text import strip_accents

ZERO = Decimal(0)
HUNDRED = Decimal(100)
WORD_SPLIT = re.compile(r"[^A-Z0-9]+")
RATIO = re.compile(r"\(\s*(\d+(?:[.,]\d+)?(?:\s*/\s*\d+(?:[.,]\d+)?)+)\s*\)")
INACTIVE = (YarnStatus.DA_HUY, YarnStatus.TU_CHOI)
NOT_COMPARED = (YarnStatus.DA_HUY, YarnStatus.TU_CHOI, YarnStatus.KHONG_SAN_XUAT)
KEEP_RANK = {
    YarnStatus.CO_MA_KE_TOAN: 0,
    YarnStatus.DA_TINH_GIA: 1,
    YarnStatus.CHUA_TINH_DUOC: 2,
    YarnStatus.CHO_XUONG_XEM: 3,
}
MIN_DICTIONARY_USES = 3
MIN_KEYWORD_USES = 5
MAX_SUGGEST_DISTANCE = 2
MIN_SUGGEST_LENGTH = 4
MAX_REASON = 500
MAX_FIBERS = 5
MSG_PARENS = "Tên sợi bị thiếu hoặc thừa dấu ngoặc."
MSG_RATIO = "Tỷ lệ '{ratio}' cộng lại {total}, phải bằng 100."
MSG_UNKNOWN = "Tên có chữ chưa có trong từ điển: {words}. Vui lòng chọn chữ gợi ý hoặc nhập lý do giữ chữ lạ."
MSG_REASON_LONG = "Lý do tối đa 500 ký tự."
MSG_REASON = "Vui lòng nhập lý do."
MSG_GROUP = "Vui lòng chọn nhóm sợi."
MSG_COUNT = "Chi số phải lớn hơn 0."
MSG_RATIO_TOTAL = "Tổng tỷ lệ phải bằng 100 (hiện là {total})."
MSG_SAME_NAME = "Tên mới giống tên hiện tại."
MSG_CHANGES = "Đổi tên làm đổi {what} - hãy tạo yêu cầu mới."
MSG_GROUP_EXISTS = "Nhóm tiêu hao '{key}' đã có; đổi tên sẽ làm đổi tiêu hao. Phòng SO xử lý nhóm tiêu hao trước."
MSG_GROUP_SHARED = "Nhóm tiêu hao '{key}' còn dùng cho {count} sợi khác. Hãy sửa chữ sai cho cả nhóm ở thẻ Chữ mới chờ duyệt / Từ điển."
MSG_STATUS = "Mã {code} đang '{status}', không đổi tên được."
MSG_SALES_ONLY = "Sales chỉ đổi được tên sợi chưa tính giá (Chờ xưởng xem, Chưa tính được). Mã {code} đang '{status}'."
MSG_REPLACE_CLASH = "Không sửa được vì sẽ trùng: {items}."
MSG_DUP_WORD = "Chữ '{word}' bị trùng."
MSG_NEED_CORRECT = "Chữ '{word}' là cách viết sai, vui lòng chọn chữ đúng."
MSG_CORRECT_MISSING = "Chữ đúng '{word}' chưa có trong từ điển."
MSG_DUP_PART = "{kind} '{text}' bị trùng."
MSG_FIBERS = "Số xơ phải từ 1 đến 5."
REASON_DUPLICATE = "Trùng tên với {code}"
REASON_UPPER = "Chuẩn hoá viết hoa"
REASON_SPELLING = "Sửa chính tả {wrong} → {right}"


def upper_name(name: str) -> str:
    """Tên lưu: viết hoa, gộp khoảng trắng (BR-101)."""
    return collapse_spaces(name).upper()


def words_of(name: str) -> list[str]:
    """BR-100: chuỗi chữ cái liền nhau (không chữ số) dài ≥ 2, viết hoa, bỏ dấu."""
    tokens = WORD_SPLIT.split(strip_accents(name).upper())
    return [t for t in tokens if len(t) >= 2 and t.isalpha()]


def distance(a: str, b: str, limit: int = MAX_SUGGEST_DISTANCE) -> int:
    """Levenshtein distance (stops early above ``limit``)."""
    if abs(len(a) - len(b)) > limit:
        return limit + 1
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + (ca != cb)))
        if min(current) > limit:
            return limit + 1
        previous = current
    return previous[-1]


def replace_word(text: str, wrong: str, right: str) -> str:
    """Whole-word replacement, any case (letters / digits around = not a boundary); the rest of the text keeps its case."""
    pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(wrong)}(?![A-Za-z0-9])", re.IGNORECASE)
    return pattern.sub(right, text)


def number(text: str) -> Decimal:
    return Decimal(text.replace(",", ".").strip())


class NameCheckBusiness(BaseBusiness[Yarn]):
    def __init__(self) -> None:
        self.names = YarnNameBusiness()
        self.blend = BlendBusiness()

    # ---- BR-100 ----
    def parens_ok(self, name: str) -> bool:
        depth = 0
        for ch in name:
            depth += ch == "("
            depth -= ch == ")"
            if depth < 0:
                return False
        return depth == 0

    def bad_ratios(self, name: str) -> list[tuple[str, Decimal]]:
        bad = []
        for match in RATIO.finditer(name):
            parts = [p for p in match.group(1).split("/")]
            try:
                total = sum((number(p) for p in parts), ZERO)
            except InvalidOperation:
                continue
            if total != HUNDRED:
                bad.append(("/".join(p.strip() for p in parts), total))
        return bad

    def suggest(self, word: str, standard: dict[str, int], misspellings: dict[str, str]) -> str:
        if word in misspellings:
            return misspellings[word]
        if len(word) < MIN_SUGGEST_LENGTH:
            return ""
        best: tuple[int, int, str] | None = None
        for candidate, uses in standard.items():
            d = distance(word, candidate)
            if d <= MAX_SUGGEST_DISTANCE and (best is None or (d, -uses, candidate) < best):
                best = (d, -uses, candidate)
        return best[2] if best else ""

    def check(
        self, name: str, standard: dict[str, int], misspellings: dict[str, str], use_dictionary: bool = True
    ) -> NameCheck:
        """BR-100 (1)-(5) for one name; ``standard`` = Chữ chuẩn → số tên dùng (for the nearest suggestion).
        An empty dictionary checks no word (``use_dictionary`` False)."""
        clean = upper_name(name)
        issues: list[NameIssueKind] = []
        unknown: list[UnknownWord] = []
        if use_dictionary and standard:
            seen: set[str] = set()
            for word in words_of(clean):
                if word in standard or word in seen:
                    continue
                seen.add(word)
                unknown.append(UnknownWord(word=word, suggestion=self.suggest(word, standard, misspellings)))
        if unknown:
            issues.append(NameIssueKind.CHU_LA)
        if not self.parens_ok(clean):
            issues.append(NameIssueKind.NGOAC)
        ratios = self.bad_ratios(clean)
        if ratios:
            issues.append(NameIssueKind.TY_LE)
        readable = self.blend.parse(clean).readable
        if not readable:
            issues.append(NameIssueKind.KHONG_DOC)
        if collapse_spaces(name) != clean:
            issues.append(NameIssueKind.CHU_THUONG)
        suggested = clean
        for item in unknown:
            if item.suggestion:
                suggested = replace_word(suggested, item.word, item.suggestion)
        return NameCheck(
            name=clean,
            issues=issues,
            unknown=unknown,
            bad_ratios=[f"{r} ({t.normalize():f})" for r, t in ratios],
            suggested_name=suggested,
            readable=readable,
        )

    def suspects(
        self, yarns: Sequence[Yarn], standard: dict[str, int], misspellings: dict[str, str]
    ) -> list[SuspectName]:
        """UC-65: every base yarn (except Đã huỷ / Từ chối) with at least one BR-100 issue."""
        bases = [y for y in yarns if y.is_base and y.status not in INACTIVE]
        groups: dict[tuple[FactoryCode, str], list[Yarn]] = {}
        for y in bases:
            if y.status not in NOT_COMPARED:
                groups.setdefault((y.factory_code, upper_name(y.yarn_name)), []).append(y)
        duplicates = {y.yarn_code: g for g in groups.values() if len(g) > 1 for y in g}
        rows = []
        for y in bases:
            result = self.check(y.yarn_name, standard, misspellings)
            issues = list(result.issues)
            details = []
            if result.unknown:
                details.append(
                    "Chữ lạ: "
                    + ", ".join(f"{u.word} → {u.suggestion}" if u.suggestion else u.word for u in result.unknown)
                )
            if result.bad_ratios:
                details.append("Tỷ lệ: " + ", ".join(result.bad_ratios))
            if y.yarn_code in duplicates:
                issues.append(NameIssueKind.TRUNG)
                others = [o.yarn_code for o in duplicates[y.yarn_code] if o.yarn_code != y.yarn_code]
                details.append("Trùng với: " + ", ".join(others))
            if issues:
                rows.append(
                    SuspectName(
                        factory_code=y.factory_code,
                        yarn_code=y.yarn_code,
                        status=y.status,
                        yarn_name=y.yarn_name,
                        issues=issues,
                        detail="; ".join(details),
                        suggested_name=result.suggested_name,
                    )
                )
        return rows

    def word_uses(self, yarns: Sequence[Yarn]) -> Counter[str]:
        """Number of base-yarn names using each word (BR-103, suggestion order)."""
        uses: Counter[str] = Counter()
        for y in yarns:
            if y.is_base:
                uses.update(set(words_of(y.yarn_name)))
        return uses

    # ---- BR-101 ----
    def ensure_request_name(self, check: NameCheck, reason: str) -> str:
        """Blocks broken parentheses / ratios; unknown words need a reason. Returns the cleaned reason."""
        if NameIssueKind.NGOAC in check.issues:
            raise YarnValidationError(MSG_PARENS)
        if check.bad_ratios:
            ratio, total = check.bad_ratios[0].rsplit(" (", 1)
            raise YarnValidationError(MSG_RATIO.format(ratio=ratio, total=total.rstrip(")")))
        text = (reason or "").strip()
        if len(text) > MAX_REASON:
            raise YarnValidationError(MSG_REASON_LONG)
        if check.unknown and not text:
            raise YarnValidationError(MSG_UNKNOWN.format(words=", ".join(u.word for u in check.unknown)))
        return text if check.unknown else ""

    # ---- BR-102 ----
    def build_name(
        self, group: NamePart | None, count: Decimal | None, ratios: Sequence[Decimal], keywords: Sequence[NamePart]
    ) -> str:
        if group is None:
            raise YarnValidationError(MSG_GROUP)
        if count is None or count <= 0:
            raise YarnValidationError(MSG_COUNT)
        text = f"{group.text} {count.normalize():f}/1"
        if group.fiber_count >= 2:
            total = sum(ratios, ZERO)
            if len(ratios) != group.fiber_count or any(r <= 0 for r in ratios) or total != HUNDRED:
                raise YarnValidationError(MSG_RATIO_TOTAL.format(total=f"{total.normalize():f}"))
            text += " (" + "/".join(f"{r.normalize():f}" for r in ratios) + ")"
        ordered = sorted(keywords, key=lambda k: (k.sequence, k.text))
        if ordered:
            text += " " + " ".join(k.text for k in ordered)
        return upper_name(text)

    def new_group(self, name: str, existing: Sequence[NamePart]) -> NamePart | None:
        """BR-102: a typed name whose yarn group is not in the list → a new "Sales thêm - mới" group."""
        parsed = self.names.analyze(name)
        group = upper_name(parsed.yarn_group)
        if not parsed.valid or not group or any(p.text == group for p in existing if p.kind == NamePartKind.NHOM):
            return None
        match = RATIO.search(upper_name(name))
        fibers = len(match.group(1).split("/")) if match else 1
        return NamePart(
            kind=NamePartKind.NHOM,
            text=group,
            fiber_count=min(max(fibers, 1), MAX_FIBERS),
            source=NamePartSource.SALES_MOI,
            reviewed=False,
        )

    # ---- BR-103 ----
    def initial_words(self, yarns: Sequence[Yarn], user_label: str) -> list[NameWord]:
        uses = self.word_uses(yarns)
        return [
            NameWord(word=w, kind=NameWordKind.CHUAN, source=NameWordSource.KHOI_TAO, created_by=user_label)
            for w, n in sorted(uses.items())
            if n >= MIN_DICTIONARY_USES
        ]

    def initial_parts(self, yarns: Sequence[Yarn]) -> list[NamePart]:
        bases = [y for y in yarns if y.is_base and y.status not in INACTIVE]
        fibers: dict[str, Counter[int]] = {}
        keyword_pos: dict[str, list[float]] = {}
        for y in bases:
            name = upper_name(y.yarn_name)
            parsed = self.names.analyze(name)
            if not parsed.valid or not parsed.yarn_group:
                continue
            group = upper_name(parsed.yarn_group)
            match = RATIO.search(name)
            fibers.setdefault(group, Counter())[len(match.group(1).split("/")) if match else 1] += 1
            tail = name.split(f"{parsed.count_text}/1", 1)[-1]
            tail = re.sub(r"\([^()]*\)", " ", tail)
            tokens = [
                t
                for t in tail.replace("(", " ").replace(")", " ").split()
                if t.isascii() and any(c.isalpha() for c in t)
            ]
            for index, token in enumerate(tokens):
                if not any(c.isdigit() for c in token):
                    keyword_pos.setdefault(token, []).append(index / max(len(tokens), 1))
        parts = [
            NamePart(kind=NamePartKind.NHOM, text=g, fiber_count=min(c.most_common(1)[0][0], MAX_FIBERS))
            for g, c in sorted(fibers.items())
        ]
        keywords = sorted(
            ((sum(p) / len(p), k) for k, p in keyword_pos.items() if len(p) >= MIN_KEYWORD_USES),
            key=lambda item: (item[0], item[1]),
        )
        parts += [
            NamePart(kind=NamePartKind.TU_KHOA, text=k, sequence=(index + 1) * 10)
            for index, (_, k) in enumerate(keywords)
        ]
        return parts

    def ensure_dictionary(self, words: Sequence[NameWord]) -> None:
        seen: set[str] = set()
        standard = {w.word for w in words if w.kind == NameWordKind.CHUAN}
        for w in words:
            if w.word in seen:
                raise YarnValidationError(MSG_DUP_WORD.format(word=w.word))
            seen.add(w.word)
            if w.kind == NameWordKind.SAI:
                if not w.correct_word:
                    raise YarnValidationError(MSG_NEED_CORRECT.format(word=w.word))
                if w.correct_word not in standard:
                    raise YarnValidationError(MSG_CORRECT_MISSING.format(word=w.correct_word))

    def ensure_parts(self, parts: Sequence[NamePart]) -> None:
        seen: set[tuple[NamePartKind, str]] = set()
        for p in parts:
            if (p.kind, p.text) in seen:
                raise YarnValidationError(MSG_DUP_PART.format(kind=p.kind.value.replace(" sợi", ""), text=p.text))
            seen.add((p.kind, p.text))
            if p.kind == NamePartKind.NHOM and not 1 <= p.fiber_count <= MAX_FIBERS:
                raise YarnValidationError(MSG_FIBERS)

    # ---- BR-105 ----
    def ensure_can_rename(self, yarn: Yarn, is_so: bool) -> None:
        if yarn.status in INACTIVE:
            raise YarnValidationError(MSG_STATUS.format(code=yarn.yarn_code, status=yarn.status.value))
        if not is_so and yarn.status not in (YarnStatus.CHO_XUONG_XEM, YarnStatus.CHUA_TINH_DUOC):
            raise YarnValidationError(MSG_SALES_ONLY.format(code=yarn.yarn_code, status=yarn.status.value))

    def ensure_same_basis(self, old: str, new: str) -> None:
        """Count, technology and compact come from the name and change the price: never changed by a rename."""
        before, after = self.names.analyze(old), self.names.analyze(new)
        changed = []
        if before.count != after.count:
            changed.append("chi số")
        if self.names.technology(old) != self.names.technology(new):
            changed.append("công nghệ")
        if self.names.is_compact(old) != self.names.is_compact(new):
            changed.append("compact")
        if changed:
            raise YarnValidationError(MSG_CHANGES.format(what=" / ".join(changed)))

    def loss_group_change(
        self, yarn: Yarn, new_key: str, yarns: Sequence[Yarn], groups: Sequence[LossGroup]
    ) -> LossGroup | None:
        """BR-105: the loss group to rename (None = key unchanged). Raises when the change would alter the losses."""
        old_key = yarn.loss_group_key
        if new_key == old_key:
            return None
        same_factory = [g for g in groups if g.factory_code == yarn.factory_code]
        if any(g.group_key == new_key for g in same_factory):
            raise YarnValidationError(MSG_GROUP_EXISTS.format(key=new_key))
        users = {
            y.base_code
            for y in yarns
            if y.factory_code == yarn.factory_code and y.loss_group_key == old_key and y.status not in INACTIVE
        } - {yarn.base_code}
        if users:
            raise YarnValidationError(MSG_GROUP_SHARED.format(key=old_key, count=len(users)))
        return next((g for g in same_factory if g.group_key == old_key), None)

    def renamed_group(
        self, group: LossGroup, new_key: str, groups: Sequence[LossGroup], yarns: Sequence[Yarn]
    ) -> tuple[list[LossGroup], list[Yarn]]:
        """Rename one loss group (key + label) and every reference to it: secondary components, yarn components."""
        old_label = group.material_label
        changed_groups = [group.model_copy(update={"group_key": new_key, "yarn_group_label": new_key})]
        new_label = changed_groups[0].material_label
        for g in groups:
            if g.id == group.id or g.factory_code != group.factory_code:
                continue
            if any(c.component_group_key == group.group_key for c in g.components):
                changed_groups.append(
                    g.model_copy(
                        update={
                            "components": [
                                c.model_copy(update={"component_group_key": new_key})
                                if c.component_group_key == group.group_key
                                else c
                                for c in g.components
                            ]
                        }
                    )
                )
        changed_yarns = []
        if old_label != new_label:
            for y in yarns:
                if y.factory_code == group.factory_code and any(c.material_label == old_label for c in y.components):
                    changed_yarns.append(
                        y.model_copy(
                            update={
                                "components": [
                                    c.model_copy(update={"material_label": new_label})
                                    if c.material_label == old_label
                                    else c
                                    for c in y.components
                                ]
                            }
                        )
                    )
        return changed_groups, changed_yarns

    def with_new_name(
        self, yarn: Yarn, new_name: str, new_key: str, user_label: str, reason: str, now: datetime
    ) -> Yarn:
        parsed = self.names.analyze(new_name)
        return yarn.model_copy(
            update={
                "yarn_name": new_name,
                "yarn_group": parsed.yarn_group,
                "loss_group_key": new_key,
                "old_names": [
                    *yarn.old_names,
                    OldName(name=yarn.yarn_name, changed_by=user_label, changed_at=now, reason=reason),
                ],
            }
        )

    def plan_rename(
        self,
        base: Yarn,
        family: Sequence[Yarn],
        new_name: str,
        reason: str,
        unknown_reason: str,
        is_so: bool,
        yarns: Sequence[Yarn],
        groups: Sequence[LossGroup],
        standard: dict[str, int],
        misspellings: dict[str, str],
        user_label: str,
        now: datetime,
    ) -> tuple[list[Yarn], list[LossGroup], str, str, NameCheck]:
        """BR-105 for one base code and its NSM revisions → (changed yarns, changed loss groups, old key, new key, check)."""
        self.ensure_can_rename(base, is_so)
        reason = self.ensure_reason(reason)
        new = upper_name(new_name)
        if new == base.yarn_name:
            raise YarnValidationError(MSG_SAME_NAME)
        parsed = self.names.analyze(new)
        self.names.ensure_valid(parsed)
        self.ensure_same_basis(base.yarn_name, new)
        check = self.check(new, standard, misspellings)
        self.ensure_request_name(check, unknown_reason)
        old_key = base.loss_group_key
        # a legacy key that does not come from the name (BR-04) is kept as it is
        new_key = parsed.loss_group_key if self.names.analyze(base.yarn_name).loss_group_key == old_key else old_key
        group = self.loss_group_change(base, new_key, yarns, groups)
        renamed = {
            y.id: self.with_new_name(
                y, new, new_key if y.loss_group_key == old_key else y.loss_group_key, user_label, reason, now
            )
            for y in family
        }
        RequestBusiness().ensure_unique_name(renamed[base.id], yarns)
        changed_groups: list[LossGroup] = []
        if group is not None:
            changed_groups, component_yarns = self.renamed_group(group, new_key, groups, yarns)
            for y in component_yarns:
                renamed[y.id] = renamed[y.id].model_copy(update={"components": y.components}) if y.id in renamed else y
        return list(renamed.values()), changed_groups, old_key, new_key, check

    def ensure_reason(self, reason: str) -> str:
        text = (reason or "").strip()
        if not text:
            raise YarnValidationError(MSG_REASON)
        if len(text) > MAX_REASON:
            raise YarnValidationError(MSG_REASON_LONG)
        return text

    # ---- BR-106 ----
    def replace_everywhere(
        self, wrong: str, right: str, yarns: Sequence[Yarn], groups: Sequence[LossGroup], user_label: str, now: datetime
    ) -> tuple[list[Yarn], list[LossGroup]]:
        """W → W' in yarn names, loss group keys / labels / materials, secondary components and yarn components.
        Raises (nothing changed) when a new yarn name or a new loss group key would clash with an existing one."""
        reason = REASON_SPELLING.format(wrong=wrong, right=right)
        changed_yarns: list[Yarn] = []
        for y in yarns:
            name = replace_word(y.yarn_name, wrong, right) if wrong in words_of(y.yarn_name) else y.yarn_name
            key = (
                replace_word(y.loss_group_key, wrong, right)
                if wrong in words_of(y.loss_group_key)
                else y.loss_group_key
            )
            components = [
                c.model_copy(update={"material_label": replace_word(c.material_label, wrong, right)})
                if wrong in words_of(c.material_label)
                else c
                for c in y.components
            ]
            if (name, key, components) == (y.yarn_name, y.loss_group_key, y.components):
                continue
            update: dict[str, object] = {"loss_group_key": key, "components": components}
            if name != y.yarn_name:
                parsed = self.names.analyze(name)
                update |= {
                    "yarn_name": name,
                    "yarn_group": parsed.yarn_group or y.yarn_group,
                    "old_names": [
                        *y.old_names,
                        OldName(name=y.yarn_name, changed_by=user_label, changed_at=now, reason=reason),
                    ],
                }
            changed_yarns.append(y.model_copy(update=update))
        changed_groups: list[LossGroup] = []
        for g in groups:
            fields = {
                "group_key": replace_word(g.group_key, wrong, right),
                "yarn_group_label": replace_word(g.yarn_group_label, wrong, right)
                if wrong in words_of(g.yarn_group_label)
                else g.yarn_group_label,
                "material": replace_word(g.material, wrong, right) if wrong in words_of(g.material) else g.material,
                "components": [
                    c.model_copy(update={"component_group_key": replace_word(c.component_group_key, wrong, right)})
                    if wrong in words_of(c.component_group_key)
                    else c
                    for c in g.components
                ],
            }
            if wrong not in words_of(g.group_key):
                fields["group_key"] = g.group_key
            if any(getattr(g, k) != v for k, v in fields.items()):
                changed_groups.append(g.model_copy(update=fields))
        self._ensure_no_clash(yarns, changed_yarns, groups, changed_groups)
        return changed_yarns, changed_groups

    def _ensure_no_clash(
        self,
        yarns: Sequence[Yarn],
        changed_yarns: Sequence[Yarn],
        groups: Sequence[LossGroup],
        changed_groups: Sequence[LossGroup],
    ) -> None:
        clashes: list[str] = []
        final = {y.id: y for y in yarns} | {y.id: y for y in changed_yarns}
        names: dict[tuple[FactoryCode, str], list[str]] = {}
        for y in final.values():
            if y.is_base and y.status not in NOT_COMPARED:
                names.setdefault((y.factory_code, upper_name(y.yarn_name)), []).append(y.yarn_code)
        touched = {(y.factory_code, upper_name(y.yarn_name)) for y in changed_yarns if y.is_base}
        clashes += [
            f"{n} ({', '.join(c)})" for key, c in names.items() if key in touched and len(c) > 1 for n in [key[1]]
        ]
        final_groups = {g.id: g for g in groups} | {g.id: g for g in changed_groups}
        keys: Counter[tuple[FactoryCode, str]] = Counter((g.factory_code, g.group_key) for g in final_groups.values())
        touched_keys = {(g.factory_code, g.group_key) for g in changed_groups}
        clashes += [f"nhóm tiêu hao {k[1]} ({k[0].value})" for k, n in keys.items() if n > 1 and k in touched_keys]
        if clashes:
            raise YarnValidationError(MSG_REPLACE_CLASH.format(items="; ".join(clashes[:10])))

    # ---- BR-107 ----
    def duplicate_plan(self, yarns: Sequence[Yarn], alias_counts: dict[str, int]) -> list[DuplicateDecision]:
        bases = [y for y in yarns if y.is_base and y.status not in NOT_COMPARED]
        revisions: Counter[tuple[FactoryCode, str]] = Counter(
            (y.factory_code, y.base_code) for y in yarns if not y.is_base
        )
        groups: dict[tuple[FactoryCode, str], list[Yarn]] = {}
        for y in bases:
            groups.setdefault((y.factory_code, upper_name(y.yarn_name)), []).append(y)

        def codes(y: Yarn) -> list[str]:
            return sorted({line.accounting_code for line in y.lines if line.accounting_code})

        def number_of(code: str) -> int:
            tail = code.split("-", 1)[-1]
            return int(tail) if tail.isdigit() else 10**9

        def rank(y: Yarn) -> tuple:
            return (
                KEEP_RANK.get(y.status, 9),
                -len(codes(y)),
                -revisions[(y.factory_code, y.base_code)],
                -alias_counts.get(y.base_code, 0),
                -len(y.lines),
                number_of(y.yarn_code),
                y.created_at,  # same conditions: the code created first is kept
                y.yarn_code,
            )

        decisions = []
        for (factory, name), members in sorted(groups.items(), key=lambda item: (item[0][0].value, item[0][1])):
            if len(members) < 2:
                continue
            ordered = sorted(members, key=rank)
            keep = ordered[0]
            for y in ordered:
                decisions.append(
                    DuplicateDecision(
                        factory_code=factory,
                        upper_name=name,
                        yarn_code=y.yarn_code,
                        yarn_name=y.yarn_name,
                        status=y.status,
                        keep=y is keep,
                        keep_code=keep.yarn_code,
                        accounting_codes=codes(y),
                        reason="" if y is keep else REASON_DUPLICATE.format(code=keep.yarn_code),
                    )
                )
        return decisions

    def upper_changes(self, yarns: Sequence[Yarn], dropped: set[str]) -> list[Yarn]:
        """Yarns whose stored name is not upper case yet; codes dropped as duplicates (now or by an earlier run) keep
        their name."""
        earlier = {
            y.base_code
            for y in yarns
            if (y.not_produced_reason or y.reject_reason).startswith(REASON_DUPLICATE.split("{")[0])
        }
        return [
            y
            for y in yarns
            if y.yarn_name != upper_name(y.yarn_name) and y.base_code not in dropped and y.base_code not in earlier
        ]

    def uppered(self, yarn: Yarn, user_label: str, now: datetime) -> Yarn:
        return yarn.model_copy(
            update={
                "yarn_name": upper_name(yarn.yarn_name),
                "old_names": [
                    *yarn.old_names,
                    OldName(name=yarn.yarn_name, changed_by=user_label, changed_at=now, reason=REASON_UPPER),
                ],
            }
        )
