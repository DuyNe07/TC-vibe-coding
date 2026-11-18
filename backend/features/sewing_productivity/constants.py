"""Constants of feature "Năng suất xưởng may" (UPPER_CASE values only, no classes)."""

from datetime import date
from decimal import Decimal
from typing import Final

from backend.features.sewing_productivity.models.enums import REPORT_FACTORIES, Factory, FactoryGroup

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
# BR-97 (thêm 2026-11-13): a file with only Production data is a past year when every day is before this one
PRODUCTION_ONLY_BEFORE: Final = date(2026, 1, 1)
SHEET_WORKER_DERIVED: Final = "Worker (tính từ Production data)"  # BR-97 the upload history names it so
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
    "standard_output_no_ratio": ("Standard output of SMV (no efficiency ratio)",),
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
# Section 5.1 (2026-11-06): the TOTAL block of sheet Worker (headcount), optional; the first column of each title wins
WORKER_TOTAL_COLUMNS: Final = {
    "Fac.2": Factory.FAC_2,
    "Fac.3": Factory.FAC_3,
    "Fac.5": Factory.FAC_5,
    "Fac.1(VL)": Factory.FAC_1,
}

# BR-06: keys made with normalize_key
FACTORY_BY_SOURCE_NAME: Final = {
    "svl factory 2": Factory.FAC_1,
    "shcm factory 2": Factory.FAC_2,
    "shcm factory 3": Factory.FAC_3,
    "shcm factory 5": Factory.FAC_5,
    "shcm factory 1": Factory.FAC_1_HCM,  # BR-98 (thêm 2026-11-13): the closed factory of the 2025 data
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
ALL_FACTORIES: Final = REPORT_FACTORIES  # BR-98 (sửa 2026-11-13): the closed Fac 1 HCM is left out
NO_RATIO_TABLE_TITLE: Final = "Hiệu suất (không tỉ lệ)"  # BR-55
HCM_COLUMN: Final = FactoryGroup.HCM.value  # BR-51
TOTAL_COLUMN: Final = FactoryGroup.TOTAL.value  # BR-58
HCM_FACTORIES: Final = (Factory.FAC_2, Factory.FAC_3, Factory.FAC_5)  # BR-51
MIN_HCM_FACTORIES: Final = 2  # BR-51: one factory alone would only repeat its own column

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
MIN_PERIODS_TO_COMPARE: Final = 2  # BR-71 the cards of Screen 4 need the last period and the one before it
SKIPPED_ROWS_KEPT: Final = 1_000  # BR-72 skipped rows kept in one upload history row (the total stays exact)
# Line Strength file (section 5.1, BR-81, thêm 2026-11-12): column -> accepted header names
SHEET_LINE_STRENGTH: Final = "Line Strength"  # the name shown in the upload history for this file (BR-82)
STRENGTH_RECOGNIZING_COLUMNS: Final = {"factory": ("FAC",), "line": ("LINE",), "groups": ("STRONG ITEM GROUP",)}
STRENGTH_OTHER_COLUMNS: Final = {
    "buyers": ("BUYER'S STRENGTH", "BUYERS STRENGTH"),
    "changeover_speed": ("CHANGEOVER SPEED",),
    "remark": ("REMARK",),
}
STRENGTH_GROUP_COLUMNS: Final = 4  # STRONG ITEM GROUP 1 to 4, side by side
STRENGTH_HEADER_ROW: Final = 0
STRENGTH_FACTORY_CODES: Final = {"XM1": "Fac 1", "XM2": "Fac 2", "XM3": "Fac 3", "XM5": "Fac 5"}
MESSAGE_BR81_COLUMNS: Final = "File Line Strength thiếu cột: {columns}. Hãy dùng đúng file Sewing Line Strength."
MESSAGE_BR81_FACTORY: Final = 'Dòng {row}: chưa nhận diện được xưởng "{code}".'
MESSAGE_BR81_DUPLICATE: Final = "Dòng {row}: trùng xưởng và chuyền với một dòng phía trên, đã bỏ qua."
MESSAGE_STRENGTH_SAVED: Final = "Đã lưu sở trường của {count} chuyền."

# BR-91 (thêm 2026-11-13 lần 3): "Line trend" by week shows this many weeks up to the chosen To date (the shared
# column chart keeps 30 columns)
TREND_WEEKS = 26

# BR-93 to BR-96 (thêm 2026-11-13 lần 4): Overview "Products & customers"; the shared chart has 6 colours
MIX_TOP_GROUPS = 5
MIX_OTHER_GROUP = "Other"
MIX_TOP_CUSTOMERS = 10
