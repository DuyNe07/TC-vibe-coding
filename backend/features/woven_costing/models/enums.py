"""Lists of values of the feature (sections 4 and 7 of the business document)."""

from enum import StrEnum


class RoleCode(StrEnum):
    SALES = "SALES"
    TRUONG_TEAM = "TRUONG_TEAM"
    TRUONG_DON_VI = "TRUONG_DON_VI"
    SO = "SO"
    PD = "PD"
    FS1 = "FS1"
    FS2 = "FS2"


class Team(StrEnum):
    FS1 = "FS1"
    FS2 = "FS2"
    SO = "SO"  # costsheets made by a user with only the SO role (BR-51)


class CustomerTeam(StrEnum):
    FS1 = "FS1"
    FS2 = "FS2"
    CHUNG = "Chung"


class FabricSource(StrEnum):
    PEACE = "Peace"
    WFX = "WFX"
    MANUAL = "Nhập tay"


class YarnDirection(StrEnum):
    WARP = "WARP"
    WEFT = "WEFT"


class YarnKind(StrEnum):
    SINGLE = "Sợi đơn"
    TWISTED = "Sợi se"


class CostsheetStatus(StrEnum):
    NHAP = "Nháp"
    CHO_DUYET = "Chờ duyệt"
    TRA_LAI = "Trả lại"
    DA_DUYET = "Đã duyệt"
    DA_CHOT_DON = "Đã chốt đơn"
    HUY = "Hủy"
    DA_THAY_THE = "Đã thay thế"


class CostsheetAction(StrEnum):
    RECALCULATE = "RECALCULATE"
    SAVE_DRAFT = "SAVE_DRAFT"
    SUBMIT = "SUBMIT"
    APPROVE = "APPROVE"
    RETURN = "RETURN"
    COPY = "COPY"
    NEW_VERSION = "NEW_VERSION"
    SAVE_OC = "SAVE_OC"
    CLOSE_ORDER = "CLOSE_ORDER"
    CANCEL = "CANCEL"
    PRINT_LABEL = "PRINT_LABEL"
    CONFIRM_YARN_PRICES = "CONFIRM_YARN_PRICES"
    EDIT_FABRIC = "EDIT_FABRIC"
    ADD_CUSTOMER = "ADD_CUSTOMER"


class HistoryAction(StrEnum):
    CREATE = "Tạo"
    SAVE = "Lưu"
    SUBMIT = "Gửi duyệt"
    APPROVE = "Duyệt"
    AUTO_APPROVE = "Duyệt tự động"
    RETURN = "Trả lại"
    NEW_VERSION = "Tạo phiên bản mới"
    CLOSE_ORDER = "Chốt đơn"
    EDIT_OC = "Sửa OC"
    CANCEL = "Hủy"
    COPY = "Sao chép"


class DyePlant(StrEnum):
    HCM = "HCM"
    TCDN = "TCDN"


class Market(StrEnum):
    EXPORT = "Xuất Khẩu"
    DOMESTIC = "Nội Địa"


class OrderType(StrEnum):
    TRIAL = "Thí Nghiệm"
    PRODUCTION = "Sản Xuất"
    STOCK = "Dự Trữ"
    OUTSOURCE = "Gia Công"


class SaleForm(StrEnum):
    GREIGE = "Mộc"
    FINISHED = "Vải Thành Phẩm"
    DYED = "Vải Nhuộm"
    WEAVING_JOB = "Gia công dệt"  # BR-89 (2026-11-25): customer gives the yarn
    DYEING_JOB = "Gia công nhuộm"  # BR-90 (2026-11-25): customer gives the greige


# sale forms without dyeing (BR-89: Gia công dệt sells greige like Mộc) / without yarn + weaving (BR-90)
NO_DYEING_FORMS = (SaleForm.GREIGE, SaleForm.WEAVING_JOB)
NO_WEAVING_FORMS = (SaleForm.DYED, SaleForm.DYEING_JOB)
JOB_FORMS = (SaleForm.WEAVING_JOB, SaleForm.DYEING_JOB)
# 4.6.2 rows that must exist (BR-88) and the row a missing job row falls back to (BR-16, 2026-11-25)
REQUIRED_BC_FORMS = (SaleForm.GREIGE, SaleForm.FINISHED, SaleForm.DYED)
BC_FALLBACK = {SaleForm.WEAVING_JOB: SaleForm.GREIGE, SaleForm.DYEING_JOB: SaleForm.DYED}


class Currency(StrEnum):
    USD = "USD"
    VND = "VND"


class PriceType(StrEnum):
    FOB = "FOB"
    CIF = "CIF"
    EXW = "EXW"
    CPT = "CPT"
    CIP = "CIP"
    FCA = "FCA"


class ShrinkageException(StrEnum):
    NONE = "Không"
    STABLE_GREIGE = "Mộc khách đã ổn định"
    PRE_SETTING = "Có pre-setting"


class FiberSystem(StrEnum):
    FILAMENT = "Filament"
    SPUN = "Spun"


class FactorStage(StrEnum):
    TWIST = "Se"
    SIZING = "Mắc Hồ"
    WARPING = "Mắc"
    CONE = "Cone"
    WEAVING = "Dệt"
    CHECKING = "Kiểm"


class CostItem(StrEnum):
    LABOR = "Nhân công"
    DEPRECIATION = "Khấu hao"
    POWER = "Điện"
    MATERIAL = "Vật tư"
    FUEL = "Nhiên liệu"
    CHEMICAL = "Hóa chất"
    OVERHEAD = "CPQL"


class ExtraCostType(StrEnum):
    DYEING = "Nhuộm"
    PARTIAL = "Partial"


class ImportResult(StrEnum):
    NEW = "Mới"
    CHANGED = "Thay đổi"
    UNCHANGED = "Không đổi"
    MISSING_YARN = "Thiếu sợi"
    ERROR = "Lỗi"


class HolidayAction(StrEnum):
    ADD = "ADD"
    DELETE = "DELETE"


class CustomerImportResult(StrEnum):
    ADDED = "Thêm"
    DUPLICATE = "Trùng"


class WarningSection(StrEnum):
    """Screen 2 tab that shows a warning at its top (UI change 2026-11-23)."""

    YARN = "Sợi"
    WEAVING = "Ngành Dệt"
    DYEING = "Nhuộm"
    PRICE = "Giá bán & lợi nhuận"
    FABRIC = "Thông số vải"
    OTHER = "Khác"


class ParamGroup(StrEnum):
    """4.6 (2026-11-25): department of a parameter (sub-tabs of Screen 5 and groups of block G)."""

    YARN = "Sợi"
    WEAVING = "Dệt"
    HCM = "Nhuộm HCM"
    TCDN = "Nhuộm TCDN"
    PRICE = "Giá bán & chung"


class DiscountDepartment(StrEnum):
    """4.6.1 department of a quantity discount row."""

    WEAVING = "Dệt"
    HCM = "Nhuộm HCM"
    TCDN = "Nhuộm TCDN"


class DiscountCondition(StrEnum):
    """4.6.1 order kind / condition of a quantity discount row."""

    MASS = "Đại trà"
    TRIAL = "Thí nghiệm"
    DYEING = "Nhuộm"
    PARTIAL = "Partial"


class QuantityUnit(StrEnum):
    """4.6.1 unit of the quantity of a discount row (fixed by the department)."""

    GREIGE_M = "m mộc"
    FINISHED_KG = "kg TP"
    FINISHED_M = "m TP"
