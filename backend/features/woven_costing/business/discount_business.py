"""BR-16 % B/C by sale form, BR-23 / BR-25 / BR-26 quantity discount factors from the tables of the parameter set
(4.6.1, 4.6.2, added 2026-11-25) and BR-88 checks of those tables."""

from collections.abc import Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.woven_costing.business.numbers import ONE, ZERO
from backend.features.woven_costing.models.checks import Check
from backend.features.woven_costing.models.enums import (
    NO_WEAVING_FORMS,
    REQUIRED_BC_FORMS,
    DiscountCondition,
    DiscountDepartment,
    OrderType,
    SaleForm,
)
from backend.features.woven_costing.models.parameter_tables import (
    DEPARTMENT_CONDITIONS,
    BcRow,
    DiscountPick,
    DiscountRow,
    OpRateRow,
    ParameterTables,
    complete_bc_rows,
    quantity_text,
)


class ParameterTableRule(BaseBusinessRule[Check]):
    """Target text = the full message (built by DiscountBusiness.table_errors)."""

    code = "BR-88"
    message = "Bảng discount / % B/C không hợp lệ."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return target.text


def _before(first: DiscountRow, second: DiscountRow) -> bool:
    """True when every quantity of ``first`` is below every quantity of ``second``."""
    if first.to_qty is None or second.from_qty is None:
        return False
    if first.to_qty < second.from_qty:
        return True
    return first.to_qty == second.from_qty and not (first.to_inclusive and second.from_inclusive)


def overlaps(first: DiscountRow, second: DiscountRow) -> bool:
    return not (_before(first, second) or _before(second, first))


def _span(row: DiscountRow) -> str:
    low = quantity_text(row.from_qty) if row.from_qty is not None else "0"
    high = quantity_text(row.to_qty) if row.to_qty is not None else "không giới hạn"
    return f"{low}–{high}"


class DiscountBusiness(BaseBusiness[Check]):
    def rules(self) -> Sequence[BaseBusinessRule[Check]]:
        return (ParameterTableRule(),)

    # ---- lookups ------------------------------------------------------------------------------------------------
    def find(
        self, tables: ParameterTables, department: DiscountDepartment, condition: DiscountCondition, quantity: Decimal
    ) -> DiscountRow | None:
        """4.6.1: first row of the department + condition whose range contains the quantity (≥ / > / ≤ / <)."""
        rows = [r for r in tables.discount_rows if r.department == department and r.condition == condition]
        return next((r for r in rows if r.contains(quantity)), None)

    def row_factor(self, tables: ParameterTables, row: DiscountRow, quantity: Decimal) -> Decimal:
        """Factor of the row; interpolate = Yes (sets stored before 2026-11-25): linear from the row's factor at
        "Từ" to the factor of the row that starts at its "Đến" (Excel formula of BR-23)."""
        if not row.interpolate or row.from_qty is None or row.to_qty is None or quantity == row.from_qty:
            return row.factor
        same = [r for r in tables.discount_rows if r.department == row.department and r.condition == row.condition]
        following = next((r for r in same if r.from_qty == row.to_qty), None)
        if following is None:
            return row.factor
        low, high = row.from_qty, row.to_qty
        return row.factor - (row.factor - following.factor) * (quantity - low) / (high - low)

    def pick(
        self,
        tables: ParameterTables,
        department: DiscountDepartment,
        conditions: Sequence[DiscountCondition],
        quantity: Decimal,
    ) -> DiscountPick:
        for condition in conditions:
            row = self.find(tables, department, condition, quantity)
            if row is not None:
                return DiscountPick(factor=self.row_factor(tables, row, quantity), reason=row.reason)
        return DiscountPick(factor=ONE, reason="Không có dòng khớp trong bảng discount", found=False)

    def weaving(
        self, tables: ParameterTables, greige_meters: Decimal, sale_form: SaleForm | None, order_type: OrderType | None
    ) -> DiscountPick:
        """BR-23: Vải Nhuộm -> not used (0); Thí Nghiệm -> row "Thí nghiệm"; otherwise row "Đại trà" by m mộc."""
        if sale_form in NO_WEAVING_FORMS:  # BR-23, BR-90
            return DiscountPick(factor=ZERO, reason=f"{sale_form.value}: không áp dụng", applies=False)
        trial = order_type == OrderType.TRIAL
        condition = DiscountCondition.TRIAL if trial else DiscountCondition.MASS
        return self.pick(tables, DiscountDepartment.WEAVING, (condition,), greige_meters)

    def hcm(self, tables: ParameterTables, finished_kg: Decimal, order_type: OrderType | None) -> DiscountPick:
        """BR-26: Thí Nghiệm -> row "Thí nghiệm"; otherwise row "Đại trà" by kg TP; no row -> 1."""
        trial = order_type == OrderType.TRIAL
        condition = DiscountCondition.TRIAL if trial else DiscountCondition.MASS
        return self.pick(tables, DiscountDepartment.HCM, (condition,), finished_kg)

    def tcdn(self, tables: ParameterTables, meters: Decimal, dyeing: bool) -> DiscountPick:
        """BR-25: rows "Đại trà" (≥ 50.000 m) first, then "Nhuộm" or "Partial"; no row -> 1."""
        kind = DiscountCondition.DYEING if dyeing else DiscountCondition.PARTIAL
        return self.pick(tables, DiscountDepartment.TCDN, (DiscountCondition.MASS, kind), meters)

    def bc_row(self, tables: ParameterTables, sale_form: SaleForm | None) -> BcRow | None:
        """BR-16: row of the sale form (no sale form yet -> Vải Thành Phẩm, as before)."""
        wanted = sale_form or SaleForm.FINISHED
        return next((r for r in complete_bc_rows(tables.bc_rows) if r.sale_form == wanted), None)

    def bc_rates(self, tables: ParameterTables, sale_form: SaleForm | None) -> tuple[Decimal, Decimal]:
        row = self.bc_row(tables, sale_form)
        return (row.greige_bc_rate, row.finished_bc_rate) if row else (ZERO, ZERO)

    # ---- BR-88 --------------------------------------------------------------------------------------------------
    def _group_errors(self, name: str, group: list[DiscountRow]) -> list[str]:
        errors: list[str] = []
        for index, row in enumerate(group):
            if row.factor <= 0:
                errors.append(f"{name}: hệ số phải lớn hơn 0.")
            negative = row.from_qty is not None and row.from_qty < 0
            reversed_ = row.from_qty is not None and row.to_qty is not None and row.to_qty <= row.from_qty
            if negative or reversed_:
                errors.append(f"{name}: khoảng {_span(row)} không hợp lệ (Từ không âm, Đến lớn hơn Từ).")
            elif any(overlaps(row, other) for other in group[:index]):
                errors.append(f"{name}: khoảng {_span(row)} chồng lên khoảng khác.")
        return errors

    def _discount_errors(self, rows: list[DiscountRow]) -> list[str]:
        errors: list[str] = []
        for department in DiscountDepartment:
            allowed = DEPARTMENT_CONDITIONS[department]
            for row in rows:
                if row.department == department and row.condition not in allowed:
                    errors.append(
                        f"Bảng discount {department.value}: điều kiện {row.condition.value} không dùng cho ngành này."
                    )
            for condition in allowed:
                group = [r for r in rows if r.department == department and r.condition == condition]
                errors += self._group_errors(f"Bảng discount {department.value} – {condition.value}", group)
        return errors

    def _bc_errors(self, rows: list[BcRow]) -> list[str]:
        errors: list[str] = []
        for form in SaleForm:
            found = [r for r in rows if r.sale_form == form]
            if not found and form in REQUIRED_BC_FORMS:  # the 2 job rows are optional (2026-11-25)
                errors.append(f"Bảng % B/C thiếu hình thức bán {form.value}.")
            elif len(found) > 1:
                errors.append(f"Bảng % B/C có nhiều dòng hình thức bán {form.value}.")
            for row in found:
                if not (0 <= row.greige_bc_rate < 1 and 0 <= row.finished_bc_rate < 1):
                    errors.append(f"Bảng % B/C {form.value}: % B/C phải từ 0% đến dưới 100%.")
        return errors

    def _op_rate_errors(self, rows: list[OpRateRow]) -> list[str]:
        """BR-93 (2026-11-25): 0 < rate <= 1, one row per stage."""
        errors = [f"Hệ số vận hành {r.stage} phải lớn hơn 0 và không quá 1." for r in rows if not 0 < r.rate <= 1]
        names = [r.stage.strip().casefold() for r in rows]
        errors += [f"Hệ số vận hành có nhiều dòng công đoạn {r.stage}." for i, r in enumerate(rows)
                   if names.index(r.stage.strip().casefold()) != i]  # fmt: skip
        return errors

    def table_errors(self, tables: ParameterTables) -> list[str]:
        """BR-88: per department + condition the ranges do not overlap (≥ / > / ≤ / < counted), factor > 0;
        % B/C in 0..1 and one row for each of the 3 sale forms."""
        messages = self._discount_errors(tables.discount_rows) + self._bc_errors(tables.bc_rows)
        messages += self._op_rate_errors(tables.op_rates)
        return [v.message for m in messages for v in self.collect_violations(Check(ok=False, text=m))]
