"""BR-46 parameter overrides, BR-60 rates, BR-61 rate of the costing date, BR-62 sets in force, BR-64 unique dates,
BR-65 parameter ranges, BR-70 input files."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule, UploadedFileDTO
from backend.features.woven_costing.constants import INPUT_EXTENSIONS, MAX_FILE_MB, MAX_FILE_ROWS
from backend.features.woven_costing.models.checks import Check
from backend.features.woven_costing.models.costsheet_result import AppliedParameter
from backend.features.woven_costing.models.master import ExchangeRate
from backend.features.woven_costing.models.parameter_set import (
    ALL_DEFINITIONS,
    ParameterOverride,
    ParameterValues,
)

ONE = Decimal(1)


class RatePositiveRule(BaseBusinessRule[Decimal]):
    code = "BR-60"
    message = "Tỷ giá phải lớn hơn 0."
    field = "rate"

    def is_satisfied_by(self, target: Decimal) -> bool:
        return target > 0


class RateExistsRule(BaseBusinessRule[Check]):
    """Target text = MM/YYYY."""

    code = "BR-61"
    message = "Chưa có tỷ giá tháng này. Liên hệ SO cập nhật."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Chưa có tỷ giá tháng {target.text}. Liên hệ SO cập nhật."


class SetInForceRule(BaseBusinessRule[Check]):
    """Target text = dd/mm/yyyy."""

    code = "BR-62"
    message = "Chưa có bộ định mức / tham số hiệu lực. Liên hệ SO."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Chưa có bộ định mức / tham số hiệu lực cho ngày {target.text}. Liên hệ SO."


class UniqueDateRule(BaseBusinessRule[Check]):
    code = "BR-64"
    message = "Đã có bộ hiệu lực từ ngày này. Chọn ngày khác."
    field = "effective_from"

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Đã có bộ hiệu lực từ {target.text}. Chọn ngày khác."


class ParameterRangeRule(BaseBusinessRule[Check]):
    """Target text = parameter label."""

    code = "BR-65"
    message = "Tham số không hợp lệ."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"{target.text} không hợp lệ."


class InputFileRule(BaseBusinessRule[Check]):
    """Target text = file name, other = reason ("size" or the missing column)."""

    code = "BR-70"
    message = "File không đúng mẫu."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        if target.other == "size":
            rows = f"{MAX_FILE_ROWS:,}".replace(",", ".")
            return f"File quá lớn (tối đa {MAX_FILE_MB} MB, {rows} dòng)."
        if target.other == "type":
            return f"File {target.text} không đúng mẫu: chỉ nhận file .xlsx / .xls."
        return f"File {target.text} không đúng mẫu: thiếu cột {target.other}."


def _fmt(day: date) -> str:
    return day.strftime("%d/%m/%Y")


class MasterBusiness(BaseBusiness[Check]):
    def rules(self) -> Sequence[BaseBusinessRule[Check]]:
        return (ParameterRangeRule(),)

    def ensure_rate(self, rate: Decimal) -> None:
        RatePositiveRule().check(rate)

    def ensure_rate_exists(self, rate: ExchangeRate | None, day: date) -> Decimal:
        """BR-61: the rate of the month / year of the costing date."""
        RateExistsRule().check(Check(ok=rate is not None, text=day.strftime("%m/%Y")))
        return rate.rate if rate is not None else Decimal(0)

    def ensure_in_force(self, found: object | None, day: date) -> None:
        """BR-62: a norm set and a parameter set with effective_from <= costing date."""
        SetInForceRule().check(Check(ok=found is not None, text=_fmt(day)))

    def ensure_unique_date(self, day: date, existing: list[date]) -> None:
        """BR-64."""
        UniqueDateRule().check(Check(ok=day not in existing, text=_fmt(day)))

    def ensure_file(self, file: UploadedFileDTO) -> None:
        """BR-70: .xlsx / .xls and at most 20 MB (rows and columns are checked by the readers)."""
        InputFileRule().check(Check(ok=file.extension in INPUT_EXTENSIONS, text=file.filename, other="type"))
        InputFileRule().check(Check(ok=file.size_mb <= MAX_FILE_MB, text=file.filename, other="size"))

    def ensure_rows(self, file_name: str, rows: int) -> None:
        InputFileRule().check(Check(ok=rows <= MAX_FILE_ROWS, text=file_name, other="size"))

    def ensure_columns(self, file_name: str, missing: list[str]) -> None:
        InputFileRule().check(Check(ok=not missing, text=file_name, other=", ".join(missing)))

    def parameter_violations(self, values: ParameterValues) -> list[str]:
        """BR-65: rates 0 <= x < 1; GP / OP thresholds -100%..100%; every value >= 0 otherwise."""
        messages = []
        for definition in ALL_DEFINITIONS:
            value = values.get(definition.code)
            if definition.is_threshold:
                ok = -ONE <= value <= ONE
            elif definition.is_ratio:
                ok = 0 <= value < 1
            else:
                ok = value >= 0
            violation = ParameterRangeRule().evaluate(Check(ok=ok, text=definition.label))
            if violation is not None:
                messages.append(violation.message)
        return messages

    def apply_overrides(
        self, defaults: ParameterValues, wanted: dict[str, Decimal], allow_so_only: bool = False
    ) -> tuple[ParameterValues, list[ParameterOverride]]:
        """BR-46: sales change any 4.6 value except the "chỉ SO" ones; overrides are kept per costsheet (4.18).
        Values replaced by the tables on 2026-11-25 stay accepted: overrides stored on older costsheets keep working."""
        overrides = []
        updates = {}
        for definition in ALL_DEFINITIONS:
            if definition.code not in wanted or (definition.so_only and not allow_so_only):
                continue
            used = wanted[definition.code]
            default = defaults.get(definition.code)
            if used != default:
                overrides.append(ParameterOverride(parameter=definition.code, default_value=default, used_value=used))
                updates[definition.code] = used
        values = defaults.model_copy(update=updates)
        return values, overrides

    def applied_overrides(
        self,
        wanted: dict[str, Decimal],
        applied: list[AppliedParameter],
        previous: dict[str, ParameterOverride],
    ) -> list[ParameterOverride]:
        """BR-46 (2026-11-25): discount factor / % B/C typed on the costsheet, default = value of the table for this
        costsheet. A value not used by this calculation (not calculated yet, other dyeing plant) is kept as typed."""
        defaults = {a.code: a.default_value for a in applied}
        overrides = []
        for code, used in wanted.items():
            if code in defaults:
                if used != defaults[code]:
                    overrides.append(ParameterOverride(parameter=code, default_value=defaults[code], used_value=used))
                continue
            old = previous.get(code)
            overrides.append(ParameterOverride(parameter=code, default_value=old.default_value if old else used,
                                               used_value=used))  # fmt: skip
        return overrides
