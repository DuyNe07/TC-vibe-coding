"""BR-01..BR-04 (tên sợi → chi số, nhóm sợi, công nghệ, nhóm tiêu hao) and BR-06 name comparison."""

from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.yarn_costing.models.costing import ParsedYarnName
from backend.features.yarn_costing.models.enums import Technology

COUNT_MARK = "/1"
MAX_NAME_LENGTH = 200


def collapse_spaces(text: str) -> str:
    """Excel TRIM: strip both ends and keep single spaces between words."""
    return " ".join(str(text or "").split())


def group_key_of(label: str) -> str:
    """4.11 group_key = viết hoa, bỏ khoảng trắng hai đầu."""
    return collapse_spaces(label).upper()


class YarnNameRule(BaseBusinessRule[ParsedYarnName]):
    code = "BR-01"
    message = "Tên sợi phải có chi số dạng '<số>/1', ví dụ 'CVC 30/1 (60/40)'. Vui lòng sửa lại tên sợi."
    field = "yarn_name"

    def is_satisfied_by(self, target: ParsedYarnName) -> bool:
        return target.valid


class YarnNameBusiness(BaseBusiness[ParsedYarnName]):
    def rules(self) -> Sequence[BaseBusinessRule[ParsedYarnName]]:
        return (YarnNameRule(),)

    def count_text(self, name: str) -> str:
        """BR-02: 2 ký tự ngay trước '/1' (bỏ khoảng trắng); có dấu '.' thì lấy 4 ký tự."""
        position = name.upper().find(COUNT_MARK)
        if position < 0:
            return ""
        text = name[max(position - 2, 0) : position].strip()
        if "." in text:
            text = name[max(position - 4, 0) : position].strip()
        return text

    def parse_count(self, text: str) -> Decimal | None:
        """BR-02: kết quả phải là số > 0."""
        try:
            value = Decimal(text)
        except (InvalidOperation, ValueError):
            return None
        return value if value.is_finite() and value > 0 else None

    def yarn_group(self, name: str, count_text: str) -> str:
        """BR-02: phần tên trước lần xuất hiện đầu tiên của chi số, bỏ khoảng trắng hai đầu, viết hoa."""
        position = name.find(count_text)
        return collapse_spaces(name[:position]).upper() if position >= 0 else ""

    def is_mvs(self, name: str) -> bool:
        """BR-03: MVS nếu tên chứa 'MVS' (không phân biệt hoa thường), ngược lại Ring."""
        return "MVS" in name.upper()

    def technology(self, name: str) -> Technology:
        """BR-03: công nghệ Ring / MVS."""
        return Technology.MVS if self.is_mvs(name) else Technology.RING

    def is_compact(self, name: str) -> bool:
        """BR-03: sợi compact nếu tên chứa 'COMPACT'."""
        return "COMPACT" in name.upper()

    def loss_group_key(self, name: str, count_text: str) -> str:
        """BR-04: bỏ '<chi số>/1' (kèm khoảng trắng sau nó → một khoảng trắng), trim, viết hoa."""
        token = f"{count_text}{COUNT_MARK}"
        text = name.replace(token + " ", " ") if (token + " ") in name else name.replace(token, "")
        return collapse_spaces(text).upper()

    def analyze(self, name: str) -> ParsedYarnName:
        """BR-01..BR-04 applied to one name."""
        name = collapse_spaces(name)
        count_text = self.count_text(name) if name else ""
        count = self.parse_count(count_text) if count_text else None
        valid = bool(name) and len(name) <= MAX_NAME_LENGTH and COUNT_MARK in name.upper() and count is not None
        if not valid:
            return ParsedYarnName(valid=False, technology_is_mvs=self.is_mvs(name), is_compact=self.is_compact(name))
        return ParsedYarnName(
            valid=True,
            yarn_group=self.yarn_group(name, count_text),
            count=count,
            count_text=count_text,
            loss_group_key=self.loss_group_key(name, count_text),
            technology_is_mvs=self.is_mvs(name),
            is_compact=self.is_compact(name),
        )

    def comparable_name(self, name: str) -> str:
        """BR-06: so sánh không phân biệt hoa thường, gộp khoảng trắng liên tiếp."""
        return collapse_spaces(name).casefold()
