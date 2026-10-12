"""BR-05 mã tính giá, BR-06 trùng tên, BR-07 sửa/huỷ, BR-08 từ chối, BR-33 mã ĐCNSM, BR-44 chuẩn hoá mã,
BR-63 lý do khoá nút "Gửi yêu cầu"."""

import re
from collections.abc import Sequence

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.yarn_costing.business.name_business import YarnNameBusiness
from backend.features.yarn_costing.constants import (
    INITIAL_MAX_CODE,
    SUBMIT_BLOCK_NO_PACKAGING,
    SUBMIT_BLOCK_NO_SALES_MEMBER,
    SUBMIT_BLOCK_NOT_ALLOWED,
    SUBMIT_BLOCK_NOT_AUTHENTICATED,
    USE_CASE_PERMISSIONS,
)
from backend.features.yarn_costing.models.enums import FactoryCode, YarnStatus
from backend.features.yarn_costing.models.user_group import UserGroup
from backend.features.yarn_costing.models.yarn import Yarn

REVISION_PATTERN = re.compile(r"\(\s*[ĐDđd]\s*C\s*N\s*S\s*M\s*(\d*)\s*\)", re.IGNORECASE)
CLOSED_STATUSES = (YarnStatus.DA_HUY, YarnStatus.TU_CHOI)


class DuplicateNameRule(BaseBusinessRule[Yarn]):
    """Target = the yarn being created / edited; ``others`` = base yarns of the same factory."""

    code = "BR-06"
    message = "Sợi đã có ở xưởng. Không tạo yêu cầu mới."
    field = "yarn_name"

    def __init__(self, others: Sequence[Yarn]) -> None:
        self.names = YarnNameBusiness()
        self.others = others

    def duplicate_of(self, target: Yarn) -> Yarn | None:
        wanted = self.names.comparable_name(target.yarn_name)
        return next(
            (
                y
                for y in self.others
                if y.id != target.id
                and y.is_base
                and y.factory_code == target.factory_code
                and y.status not in CLOSED_STATUSES
                and self.names.comparable_name(y.yarn_name) == wanted
            ),
            None,
        )

    def is_satisfied_by(self, target: Yarn) -> bool:
        return self.duplicate_of(target) is None

    def describe_violation(self, target: Yarn) -> str:
        other = self.duplicate_of(target)
        assert other is not None
        return (
            f"Sợi '{target.yarn_name}' đã có ở mã {other.yarn_code} của xưởng {other.factory_code.value} "
            f"(trạng thái: {other.status.value}). Không tạo yêu cầu mới."
        )


class PendingRequestRule(BaseBusinessRule[Yarn]):
    code = "BR-07"
    message = "Chỉ sửa hoặc huỷ được yêu cầu đang 'Chờ xưởng xem'."

    def is_satisfied_by(self, target: Yarn) -> bool:
        return target.status == YarnStatus.CHO_XUONG_XEM

    def describe_violation(self, target: Yarn) -> str:
        return (
            f"Chỉ sửa hoặc huỷ được yêu cầu đang 'Chờ xưởng xem'. Yêu cầu {target.yarn_code} đang ở trạng thái "
            f"'{target.status.value}'."
        )


class RejectReasonRule(BaseBusinessRule[str]):
    code = "BR-08"
    message = "Vui lòng nhập lý do."

    def is_satisfied_by(self, target: str) -> bool:
        return bool((target or "").strip())


class RequestBusiness(BaseBusiness[Yarn]):
    def base_number(self, factory_code: str, code: str) -> int | None:
        match = re.fullmatch(rf"{factory_code}-(\d+)", code.strip())
        return int(match.group(1)) if match else None

    def next_base_code(self, factory_code: FactoryCode, yarns: Sequence[Yarn], extra_codes: Sequence[str] = ()) -> str:
        """BR-05: tiền tố xưởng + (số lớn nhất N của mã gốc '<xưởng>-N' đã có, kể cả huỷ / từ chối / nhập file) + 1."""
        numbers = [INITIAL_MAX_CODE[factory_code.value]]
        codes = [y.base_code for y in yarns if y.factory_code == factory_code] + list(extra_codes)
        numbers += [n for code in codes if (n := self.base_number(factory_code.value, code)) is not None]
        return f"{factory_code.value}-{max(numbers) + 1}"

    def next_revision(self, base_code: str, yarns: Sequence[Yarn]) -> tuple[str, int]:
        """BR-33: mã ĐCNSM = mã gốc + ' (ĐCNSMn)', n = số lớn nhất đã dùng cho mã gốc + 1."""
        used = [y.revision_no for y in yarns if y.base_code == base_code]
        number = max(used, default=0) + 1
        return f"{base_code} (ĐCNSM{number})", number

    def normalize_import_code(self, raw: str) -> tuple[str, str, int]:
        """BR-44: 'S4 - 586 (ĐCNSM2)' → ('S4-586 (ĐCNSM2)', 'S4-586', 2); '(ĐCNSM)' không số = 1."""
        text = re.sub(r"\s*-\s*", "-", " ".join(str(raw or "").split()))
        match = REVISION_PATTERN.search(text)
        if not match:
            return text, text, 0
        number = int(match.group(1)) if match.group(1) else 1
        base = text[: match.start()].strip()
        return f"{base} (ĐCNSM{number})", base, number

    def ensure_pending(self, yarn: Yarn) -> None:
        """BR-07."""
        PendingRequestRule().check(yarn)

    def ensure_unique_name(self, yarn: Yarn, others: Sequence[Yarn]) -> None:
        """BR-06."""
        DuplicateNameRule(others).check(yarn)

    def submit_block_reasons(
        self,
        authenticated_group: UserGroup | None,
        sales_group: UserGroup | None,
        factory_code: str | None,
        has_selectable_packaging: bool,
    ) -> list[str]:
        """BR-63: các lý do khoá nút "Gửi yêu cầu" theo thứ tự (1) xác nhận, (2) quyền, (3) loại đóng gói; rỗng = bấm được."""
        reasons: list[str] = []
        if authenticated_group is None:
            no_member = sales_group is None or not sales_group.active_member_names
            reasons.append(SUBMIT_BLOCK_NO_SALES_MEMBER if no_member else SUBMIT_BLOCK_NOT_AUTHENTICATED)
        elif authenticated_group.code.value not in USE_CASE_PERMISSIONS["UC-15"]:
            reasons.append(SUBMIT_BLOCK_NOT_ALLOWED.format(group=authenticated_group.name))
        if factory_code and not has_selectable_packaging:
            reasons.append(SUBMIT_BLOCK_NO_PACKAGING.format(factory=factory_code))
        return reasons
