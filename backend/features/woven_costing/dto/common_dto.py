"""Shared DTOs, the enums and the role table the pages and the manifest need."""

from backend.core.base import BaseDTO, BaseResponseDTO
from backend.features.woven_costing.models.access import ROLE_LABELS
from backend.features.woven_costing.models.enums import (
    CostItem,
    CostsheetAction,
    CostsheetStatus,
    Currency,
    CustomerImportResult,
    CustomerTeam,
    DiscountCondition,
    DiscountDepartment,
    DyePlant,
    ExtraCostType,
    FabricSource,
    FactorStage,
    FiberSystem,
    HistoryAction,
    HolidayAction,
    ImportResult,
    Market,
    OrderType,
    ParamGroup,
    PriceType,
    QuantityUnit,
    RoleCode,
    SaleForm,
    ShrinkageException,
    Team,
    WarningSection,
    YarnDirection,
    YarnKind,
)

__all__ = [
    "ROLE_LABELS",
    "CostItem",
    "CostsheetAction",
    "CostsheetStatus",
    "Currency",
    "CustomerImportResult",
    "CustomerTeam",
    "DiscountCondition",
    "DiscountDepartment",
    "DyePlant",
    "ExtraCostType",
    "FabricSource",
    "FactorStage",
    "FiberSystem",
    "HistoryAction",
    "HolidayAction",
    "ImportResult",
    "Market",
    "MessageResponse",
    "OrderType",
    "ParamGroup",
    "PriceType",
    "QuantityUnit",
    "RoleCode",
    "SaleForm",
    "ShrinkageException",
    "Team",
    "WarningDTO",
    "WarningSection",
    "YarnDirection",
    "YarnKind",
]


class MessageResponse(BaseResponseDTO):
    message: str


class WarningDTO(BaseDTO):
    code: str
    message: str
    blocking: bool = False
    section: WarningSection = WarningSection.OTHER  # Screen 2 tab that shows it at its top
