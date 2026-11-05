"""Constants of feature "Năng suất xưởng may" (UPPER_CASE values only, no classes)."""

from datetime import date
from decimal import Decimal
from typing import Final

from backend.features.sewing_productivity.models.enums import Factory

FEATURE_KEY: Final = "sewing_productivity"
UPDATER_ROLE: Final = "UPDATER"
SYSTEM_USER: Final = "Hệ thống"

# ---- data file (section 5.1) ----
ALLOWED_EXTENSION: Final = ".xlsx"
MAX_FILE_MB: Final = 50
MAX_SHEET_ROWS: Final = 200_000
SHEET_PRODUCTION: Final = "Production data"
SHEET_TARGET: Final = "Target system"
SHEET_WORKER: Final = "Worker"
REQUIRED_SHEETS: Final = (SHEET_PRODUCTION, SHEET_TARGET, SHEET_WORKER)
HEADER_INDEX_PRODUCTION: Final = 1
HEADER_INDEX_TARGET: Final = 0
HEADER_INDEX_WORKER: Final = 1
WORKER_DATE_COLUMN_INDEX: Final = 2
WORKER_DATE_COLUMN_LABEL: Final = "Cột C (ngày)"
TEXT_DATE_FORMATS: Final = ("%Y/%m/%d", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S")

# field -> accepted headers; the first name is the one shown in messages
PRODUCTION_REQUIRED_COLUMNS: Final = {
    "production_date": ("adj Date",),
    "factory_text": ("Factory",),
    "customer_name": ("Customer Name",),
    "style": ("Style",),
    "po_number": ("PO#",),
    "source_line": ("Line",),
    "quantity": ("Product Inline Quantiy", "Product Inline Quantity"),
    "cm_price": ("Price",),
    "sewers": ("REVISE MO",),
    "working_hours": ("Revised OT 2",),
}
PRODUCTION_OPTIONAL_COLUMNS: Final = {
    "product_name": ("Product Name",),
    "color": ("Color",),
    "smv": ("SMV",),
    "standard_output": ("Standard output of SMV (have efficiency ratio)",),
    "match_text": ("Match line strength",),
}
TARGET_REQUIRED_COLUMNS: Final = {
    "line_text": ("Line",),
    "daily_target_qty": ("Daily Target (SMV)",),
    "target_date": ("Date",),
}
TARGET_OPTIONAL_COLUMNS: Final = {
    "item_name": ("Items",),
    "style": ("Style",),
    "daily_target_cm": ("Daily Target (CM)",),
    "expertise": ("Expertise",),
    "po_number": ("PO",),
}
WORKER_COLUMNS: Final = {"SF2": Factory.FAC_2, "SF3": Factory.FAC_3, "SF5": Factory.FAC_5, "SFVL": Factory.FAC_1}

# BR-06: keys made with normalize_key
FACTORY_BY_SOURCE_NAME: Final = {
    "svl factory 2": Factory.FAC_1,
    "shcm factory 2": Factory.FAC_2,
    "shcm factory 3": Factory.FAC_3,
    "shcm factory 5": Factory.FAC_5,
}
MISMATCHED_PRODUCTION_VALUE: Final = "trai so truong"
MISMATCHED_TARGET_VALUE: Final = "mismatched strength"

# ---- business values ----
FAC1_LINE_CUTOVER: Final = date(2026, 7, 7)  # BR-11
TARGET_SYSTEM_START: Final = date(2026, 10, 3)  # BR-08
UNCLASSIFIED_GROUP: Final = "Chưa phân nhóm"  # BR-14
ELAND_PREFIX: Final = "ELAND"  # BR-15
ELAND_GROUP: Final = "ELAND"  # BR-15
HOURS_PER_SHIFT: Final = Decimal(8)  # BR-22, BR-23
RANKING_SIZE: Final = 10  # BR-44
FRIDAY_WEEKDAY: Final = 4  # BR-31
DAYS_IN_WEEK: Final = 7  # BR-31
TOTAL_LINE_LABEL: Final = "Tổng"
PERIOD_LABEL: Final = "Cả kỳ"
ALL_FACTORIES: Final = tuple(Factory)

# ---- messages (section 7) ----
MESSAGE_BR01: Final = (
    "File phải có định dạng .xlsx, không quá 50 MB và mỗi sheet không quá 200.000 dòng. Hãy kiểm tra lại rồi tải lên."
)
MESSAGE_BR04: Final = "File chưa có kết quả công thức. Hãy mở file bằng Excel, lưu lại rồi tải lên."
MESSAGE_BR09: Final = "Bạn chưa có quyền cập nhật dữ liệu. Hãy liên hệ quản trị viên."
MESSAGE_BR30: Final = "Từ ngày không được sau đến ngày. Hãy chọn lại khoảng thời gian."
MESSAGE_BR39: Final = "Hãy nhập khoảng ngày hợp lệ và số lần là số nguyên từ 0 trở lên cho ít nhất một xưởng."
MESSAGE_BR45: Final = "Hãy chọn xưởng, ngày hiệu lực và nhập cả 4 mức là số lớn hơn 0."
MESSAGE_NOT_APPLICABLE: Final = "Không áp dụng khi lọc theo khách hàng hoặc sản phẩm."
MESSAGE_NO_DATA_IN_RANGE: Final = "Chưa có dữ liệu trong khoảng thời gian này."
MESSAGE_NO_DATA_ON_DAY: Final = "Chưa có dữ liệu của ngày này."
MESSAGE_NO_DATA: Final = "Chưa có dữ liệu. Người cập nhật cần tải file ở màn hình Cập nhật dữ liệu."

# ---- BR-08 warning kinds ----
WARNING_MISSING_SMV: Final = "Dòng thiếu SMV"
WARNING_MISSING_TARGET_B: Final = "Dòng thiếu mục tiêu B"
WARNING_NO_WORKERS: Final = "Ngày có sản lượng nhưng chưa có số thợ"
WARNING_NO_TARGET_SYSTEM: Final = "Ngày có sản lượng nhưng chưa có Target system"
WARNING_DUPLICATES: Final = "Dòng trùng"
WARNING_UNCLASSIFIED: Final = "Tên sản phẩm chưa phân nhóm"
WARNING_NO_PRODUCT_NAME: Final = "Style chưa có tên sản phẩm"

# ---- initial values (sections 4.4, 4.6, 4.7, 4.8) ----
GOAL_SEED_FROM: Final = date(2026, 1, 1)
GOAL_SEED: Final = (  # factory, efficiency target, MO 8h target, efficiency threshold, MO 8h threshold
    (Factory.FAC_1, Decimal(95), Decimal(38), Decimal(85), Decimal(30)),
    (Factory.FAC_2, Decimal(100), Decimal(43), Decimal(90), Decimal(40)),
    (Factory.FAC_3, Decimal(100), Decimal(43), Decimal(90), Decimal(40)),
    (Factory.FAC_5, Decimal(100), Decimal(43), Decimal(90), Decimal(40)),
)
PRODUCT_GROUP_SEED: Final = {
    "T-Shirt": ("T-SHIRT", "T SHIRT", "T- SHIRT", "TSHIRT", "T.SHIRT", "MTM", "MEN-TO-MEN", "TANK TOP", "HAT", "BAG"),
    "Polo": ("POLO", "POLO SHIRT", "HENLEY", "CHEMISE", "BASEBALL SHIRT", "CARDIGAN"),
    "Jacket": ("JACKET", "HALF ZIP UP", "HALF ZIP", "HZIP", "FULL ZIP UP"),
    "Pants": ("PANTS", "PANT", "LONG PANTS", "SHORT PANTS", "SHORTS", "LEGGING", "UNDERWEAR", "SKIRT"),
    "Hoodie": ("HOODIE", "HOODY", "PULLOVER"),
    "Dress": ("DRESS",),
    "Swimsuit": ("SWIMSUIT",),
}
CUSTOMER_GROUP_SEED: Final = {"MIHUB": "MIHUB", "MI HUB": "MIHUB", "MI HUB LIMITED": "MIHUB"}
LINE_MAPPING_SEED: Final = (  # (old line number, new line number)
    (1, 30), (2, 2), (3, 25), (4, 22), (5, 26), (6, 29), (7, 21), (8, 24), (9, 15), (10, 12), (11, 11), (12, 7),
    (13, 13), (14, 14), (15, 17), (16, 16), (17, 28), (18, 18), (19, 19), (20, 20), (21, 5), (22, 3), (23, 23),
    (24, 10), (25, 8), (26, 9), (27, 27), (28, 6), (29, 31), (30, 1), (31, 4), (32, 32), (33, 33), (34, 34),
)  # fmt: skip
LINE_LABEL_FORMAT: Final = "LINE {}"
