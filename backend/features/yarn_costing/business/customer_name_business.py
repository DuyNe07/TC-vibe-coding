"""BR-79 Tên theo khách (bổ sung 2026-11-10)."""

from collections.abc import Sequence

from backend.core.base import BaseBusiness
from backend.features.yarn_costing.business.name_business import YarnNameBusiness, collapse_spaces
from backend.features.yarn_costing.exceptions import YarnValidationError
from backend.features.yarn_costing.models.customer_name import CustomerYarnName
from backend.features.yarn_costing.models.enums import YarnStatus
from backend.features.yarn_costing.models.yarn import Yarn

MAX_CUSTOMER = 100
MAX_NAME = 200
MAX_NOTE = 500
MSG_REQUIRED = "Vui lòng nhập khách hàng và tên khách gọi."
MSG_TOO_LONG = "Khách hàng tối đa 100 ký tự, tên khách gọi tối đa 200 ký tự, ghi chú tối đa 500 ký tự."
MSG_OTHER = "Tên '{name}' của khách {customer} đã gắn với sợi {code}."
MSG_SAME = "Sợi {code} đã có tên '{name}' của khách {customer}."
MSG_STANDARD = "Tên khách gọi trùng tên chuẩn của sợi, không cần lưu."
MSG_CLOSED = "Sợi {code} đang ở trạng thái '{status}', không thêm được tên theo khách."
CLOSED = (YarnStatus.DA_HUY, YarnStatus.TU_CHOI)


class CustomerNameBusiness(BaseBusiness[CustomerYarnName]):
    def __init__(self) -> None:
        self.names = YarnNameBusiness()

    def key(self, customer: str, name: str) -> tuple[str, str]:
        return self.names.comparable_name(customer), self.names.comparable_name(name)

    def by_base(self, aliases: Sequence[CustomerYarnName]) -> dict[str, list[CustomerYarnName]]:
        grouped: dict[str, list[CustomerYarnName]] = {}
        for alias in sorted(aliases, key=lambda a: (a.customer_name.casefold(), a.customer_yarn_name.casefold())):
            grouped.setdefault(alias.base_code, []).append(alias)
        return grouped

    def text(self, aliases: Sequence[CustomerYarnName]) -> str:
        """5.4 cột 'Tên theo khách': '<khách>: <tên>; …'."""
        return "; ".join(f"{a.customer_name}: {a.customer_yarn_name}" for a in aliases)

    def check(
        self,
        base: Yarn,
        customer: str,
        name: str,
        note: str,
        existing: Sequence[CustomerYarnName],
        editing_id: str | None = None,
    ) -> tuple[str, str, str]:
        """BR-79 → cleaned (customer, name, note); raises the exact message of the rule."""
        customer, name, note = collapse_spaces(customer), collapse_spaces(name), (note or "").strip()
        if not customer or not name:
            raise YarnValidationError(MSG_REQUIRED)
        if len(customer) > MAX_CUSTOMER or len(name) > MAX_NAME or len(note) > MAX_NOTE:
            raise YarnValidationError(MSG_TOO_LONG)
        if base.status in CLOSED:
            raise YarnValidationError(MSG_CLOSED.format(code=base.base_code, status=base.status.value))
        if self.names.comparable_name(name) == self.names.comparable_name(base.yarn_name):
            raise YarnValidationError(MSG_STANDARD)
        wanted = self.key(customer, name)
        for alias in existing:
            if alias.id == editing_id or self.key(alias.customer_name, alias.customer_yarn_name) != wanted:
                continue
            template = MSG_SAME if alias.base_code == base.base_code else MSG_OTHER
            raise YarnValidationError(
                template.format(name=alias.customer_yarn_name, customer=alias.customer_name, code=alias.base_code)
            )
        return customer, name, note
