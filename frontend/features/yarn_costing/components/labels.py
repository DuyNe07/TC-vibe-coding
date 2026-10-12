"""Vietnamese labels of the enums shown on screen (enum values are already the Vietnamese text of the document)."""

from collections.abc import Mapping
from typing import Any

from backend.features.yarn_costing.dto.common_dto import (
    GroupCode,
    ImportMode,
    LineType,
    LossGroupLevel,
    NsmMode,
    RateCodeSource,
    RecoveryType,
    SecondaryMethod,
    Technology,
    YarnOrigin,
    YarnStatus,
)
from backend.features.yarn_costing.dto.reference_dto import FactoryDTO

ALL = "Tất cả"

STATUS_LABELS = {status: status.value for status in YarnStatus}
LINE_TYPE_LABELS = {line_type: line_type.value for line_type in LineType}
LEVEL_LABELS = {level: level.value for level in LossGroupLevel}
RECOVERY_LABELS = {recovery: recovery.value for recovery in RecoveryType}
TECHNOLOGY_LABELS = {tech: tech.value for tech in Technology}
IMPORT_MODE_LABELS = {mode: mode.value for mode in ImportMode}
NSM_MODE_LABELS = {mode: mode.value for mode in NsmMode}
SECONDARY_METHOD_LABELS = {method: method.value for method in SecondaryMethod}
RATE_SOURCE_LABELS = {source: source.value for source in RateCodeSource}
GROUP_LABELS = {
    GroupCode.SALES: "Sales",
    GroupCode.XS1: "Xưởng S1",
    GroupCode.XS4: "Xưởng S4",
    GroupCode.SO: "Phòng SO",
    GroupCode.KT: "Kế toán",
}
STATUS_ORDER = [
    YarnStatus.CHO_XUONG_XEM,
    YarnStatus.CHUA_TINH_DUOC,
    YarnStatus.DA_TINH_GIA,
    YarnStatus.CO_MA_KE_TOAN,
    YarnStatus.TU_CHOI,
    YarnStatus.DA_HUY,
]
FINAL_STATUSES = (YarnStatus.DA_HUY, YarnStatus.TU_CHOI)
ADJUSTMENT_TYPES = (LineType.CHIET_KHAU, LineType.PHU_PHI)
SALES_ORIGIN = YarnOrigin.YEU_CAU_SALES.value


def label_of(labels: Mapping[Any, str], value: Any) -> str:
    """Enum value -> label; None -> "-"; unknown value -> its text."""
    if value is None or value == "":
        return "-"
    if value in labels:
        return labels[value]
    return str(value)


def value_of(labels: Mapping[Any, str], label: str | None) -> Any:
    """Label -> enum value (for select cells of editable tables); None when not found."""
    if label is None:
        return None
    for value, text in labels.items():
        if text == label:
            return value
    return None


def factory_codes(factories: list[FactoryDTO]) -> list[str]:
    return [str(f.code) for f in factories]


def factory_label(factories: list[FactoryDTO], code: str | None) -> str:
    if code is None or code == ALL:
        return ALL
    for factory in factories:
        if str(factory.code) == str(code):
            return f"{factory.code} - {factory.name}"
    return str(code)


def all_or(value: Any) -> Any:
    """Filter value -> request value: "Tất cả" (or nothing chosen) becomes None."""
    return None if value in (None, ALL) else value
