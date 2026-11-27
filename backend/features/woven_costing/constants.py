"""Constants of feature "Tính giá vải dệt" (UPPER_CASE values only, no classes)."""

from decimal import Decimal
from typing import Final

FEATURE_KEY: Final = "woven_costing"
SYSTEM_USERNAME: Final = "system"
SYSTEM_NAME: Final = "Hệ thống"

# ---- Files (section 5, BR-70) ---------------------------------------------------------------------------------------
INPUT_EXTENSIONS: Final = (".xlsx", ".xls")
MAX_FILE_MB: Final = 20
MAX_FILE_ROWS: Final = 50_000
MAX_FABRIC_FILES: Final = 4

# F-01 / F-03 weaving control
COL_TCFNO: Final = "TCFNO"
COL_FABRIC: Final = "Fabric"
COL_BEFORE: Final = "Before"
COL_AFTER: Final = "After"
COL_YNAME: Final = "YNAME"
COL_TCFNO_INST: Final = "TCFNO_INST"
COL_TPM: Final = "TPM"
# 13 columns of the "Before" / "After" groups, in file order ("" = column not kept).
SPEC_GROUP_FIELDS: Final = (
    "width_cm", "cut_width_cm", "gsm", "g_per_m", "warp_density", "weft_density",
    "", "", "", "", "shrink_warp", "shrink_weft", "",
)  # fmt: skip
# F-02 / F-04 positional columns (0-based); required: columns 1, 2, 11, 13 of the document.
STD_COLUMNS: Final = {
    "tcfno": 0, "direction": 1, "full_yarn_name": 8, "yarn_code": 9, "yarn_name": 10, "rate": 12,
    "yarn_kind": 15, "raw_yarn_code": 16, "raw_yarn_name": 17, "raw_rate": 18, "tpm": 19,
}  # fmt: skip
STD_REQUIRED: Final = (("TCFNO", 0), ("YARN", 1), ("YNAME", 10), ("Rate", 12))

# F-06 customers
COL_TEAM: Final = "Team"
COL_CUSTOMER: Final = "Customer"
COL_CUSTOMER_CODE: Final = "Mã KH"
FORECAST_MARKER: Final = "TEAM FORECAST"

# F-05 norm workbook: sheet -> columns (exact order)
NORM_SHEETS: Final = {
    "DonGiaPhut": (
        "Công đoạn", "Tốc độ máy BQ", "Số cọc BQ", "Chu vi guồng", "Thời gian hoạt động (phút)",
        "Nhân công", "Khấu hao", "Điện", "Vật tư", "Nhiên liệu", "CPQL",
    ),
    "ThamSoSe": ("Tham số", "Filament", "Xơ ngắn"),
    "ThamSoMacKiem": ("Tham số", "Giá trị"),
    "DinhMucHo": (
        "Nguyên liệu hồ", "Nhóm tổng canh", "Nhân công", "Khấu hao", "Điện", "Vật tư", "Nhiên liệu", "CPQL", "Hóa chất",
    ),
    "DinhMucDet": ("Mật độ ngang", "Nhân công", "Khấu hao", "Điện", "Vật tư", "Nhiên liệu", "CPQL"),
    "ChiSo": ("Hệ sợi", "Chi số", "Chi số chuyển đổi", "", "Độ săn"),
    "NhuomHCM_TieuChuan": (
        "Loại vải", "Cấp màu", "HCTN", "Tiền lương", "Khấu hao", "Điện", "Nhiên liệu", "Vật tư", "Quản lý",
    ),
    "NhuomHCM_CongDoan": (
        "Công đoạn", "HCTN", "Tiền lương", "Khấu hao", "Điện", "Nhiên liệu", "Vật tư", "Quản lý", "Tiêu hao (%)",
    ),
    "NhuomHCM_TinhNang": (
        "Tính năng", "Loại vải", "Hóa chất sử dụng", "HCTN", "Tiền lương", "Khấu hao", "Điện", "Nhiên liệu",
        "Vật tư", "Quản lý",
    ),
    "NhuomTCDN_QuyTrinh": (
        "Mã quy trình", "Thành phần nhuộm", "Nguyên liệu nhuộm", "Cấp màu", "Quy trình chuẩn", "Hóa chất",
        "Nhân công", "Khấu hao", "Điện", "Nhiên liệu", "Vật tư", "CPQL", "Xưởng", "Tiêu hao (%)",
    ),
    "NhuomTCDN_HoaChat": ("Khóa", "Nhóm trọng lượng", "Chi phí hóa chất"),
    "DanhMuc": ("Loại danh mục", "Giá trị"),
    "Spandex": ("Loại spandex", "Cộng thêm"),
}  # fmt: skip
NORM_SHEET_TITLES: Final = {
    "DonGiaPhut": "Đơn giá theo phút",
    "ThamSoSe": "Tham số Se",
    "ThamSoMacKiem": "Tham số Mắc / Kiểm",
    "DinhMucHo": "Định mức Hồ",
    "DinhMucDet": "Định mức Dệt",
    "ChiSo": "Chi số",
    "NhuomHCM_TieuChuan": "Nhuộm HCM - định mức tiêu chuẩn",
    "NhuomHCM_CongDoan": "Nhuộm HCM - công đoạn đặc biệt",
    "NhuomHCM_TinhNang": "Nhuộm HCM - tính năng đặc biệt",
    "NhuomTCDN_QuyTrinh": "Nhuộm TCDN - quy trình",
    "NhuomTCDN_HoaChat": "Nhuộm TCDN - hóa chất CPB / Tenter",
    "DanhMuc": "Danh mục chọn",
    "Spandex": "Spandex cộng thêm",
}
# Screen 5 (2026-11-23): sub-tab of each norm table
NORM_GROUP_WEAVING: Final = "Dệt"
NORM_GROUP_HCM: Final = "Nhuộm HCM"
NORM_GROUP_TCDN: Final = "Nhuộm TCDN"
NORM_GROUP_LISTS: Final = "Danh mục chọn"
NORM_SHEET_GROUPS: Final = {
    "DonGiaPhut": NORM_GROUP_WEAVING, "ThamSoSe": NORM_GROUP_WEAVING, "ThamSoMacKiem": NORM_GROUP_WEAVING,
    "DinhMucHo": NORM_GROUP_WEAVING, "DinhMucDet": NORM_GROUP_WEAVING, "ChiSo": NORM_GROUP_WEAVING,
    "Spandex": NORM_GROUP_WEAVING, "NhuomHCM_TieuChuan": NORM_GROUP_HCM, "NhuomHCM_CongDoan": NORM_GROUP_HCM,
    "NhuomHCM_TinhNang": NORM_GROUP_HCM, "NhuomTCDN_QuyTrinh": NORM_GROUP_TCDN, "NhuomTCDN_HoaChat": NORM_GROUP_TCDN,
    "DanhMuc": NORM_GROUP_LISTS,
}  # fmt: skip
NORM_GROUPS: Final = (NORM_GROUP_WEAVING, NORM_GROUP_HCM, NORM_GROUP_TCDN, NORM_GROUP_LISTS)
# number of leading columns forming the unique key of each sheet (BR-63)
NORM_KEY_COLUMNS: Final = {
    "DonGiaPhut": 1, "ThamSoSe": 1, "ThamSoMacKiem": 1, "DinhMucHo": 2, "DinhMucDet": 1, "ChiSo": 2,
    "NhuomHCM_TieuChuan": 2, "NhuomHCM_CongDoan": 1, "NhuomHCM_TinhNang": 2, "NhuomTCDN_QuyTrinh": 3,
    "NhuomTCDN_HoaChat": 2, "DanhMuc": 2, "Spandex": 1,
}  # fmt: skip
# sheets of F-05 that may be missing (4.5.13, BR-63): the table of the set in force is kept
NORM_OPTIONAL_SHEETS: Final = ("Spandex",)
SPANDEX_SHEET: Final = "Spandex"
SPANDEX_TYPE_COLUMN: Final = "Loại spandex"
SPANDEX_ADD_COLUMN: Final = "Cộng thêm"
# text columns of the norm sheets (every other column must be a number >= 0)
NORM_TEXT_COLUMNS: Final = (
    "Công đoạn", "Tham số", "Nguyên liệu hồ", "Nhóm tổng canh", "Hệ sợi", "Chi số", "Loại vải", "Cấp màu",
    "Tính năng", "Hóa chất sử dụng", "Mã quy trình", "Thành phần nhuộm", "Nguyên liệu nhuộm", "Quy trình chuẩn",
    "Xưởng", "Khóa", "Nhóm trọng lượng", "Loại danh mục",
)  # fmt: skip
TWIST_PARAM_NAMES: Final = (
    "Đơn giá máy chạy (đ/phút)", "Đơn giá chuẩn bị (đ/lần)", "Sản lượng / lần chuẩn bị (kg)",
    "TG chuẩn bị / lần (phút)", "Số cọc", "Số máy", "Số ca",
)  # fmt: skip
TWIST_STAFF_NAME: Final = "Tổng nhân sự Se"
TWIST_HOURS_NAME: Final = "Số giờ làm/ngày"
WARP_CHECK_NAMES: Final = (
    "Tổng canh chuẩn", "Số nhịp chuẩn", "Hệ số sợi dọc có se", "Tốc độ kiểm hàng bán mộc",
    "Tốc độ kiểm hàng giao nhuộm",
)  # fmt: skip
SEED_TWIST_STAFF: Final = "33"
SEED_TWIST_HOURS: Final = "22.5"
SEED_WARP_CHECK: Final = ("7800", "12", "1.97", "11", "11")
SEED_EFFECTIVE_FROM: Final = "2026-01-01"

# ---- Minute-rate stages (4.5.1) -------------------------------------------------------------------------------------
STAGE_TWIST_FILAMENT: Final = "SE - FILAMENT"
STAGE_TWIST_SPUN: Final = "SE - XƠ NGẮN"
STAGE_WARPING: Final = "MAC"
STAGE_CONE: Final = "CONE"
STAGE_WEAVING: Final = "DET"
STAGE_CHECK_GREIGE: Final = "KIEM HANG_1"
STAGE_CHECK_DYE: Final = "KIEM HANG_2"
STAGE_SINGEING: Final = "BẤM ĐỐT - CARBON"
REQUIRED_STAGES: Final = (
    STAGE_TWIST_FILAMENT, STAGE_TWIST_SPUN, STAGE_WARPING, STAGE_CONE, STAGE_WEAVING,
    STAGE_CHECK_GREIGE, STAGE_CHECK_DYE, STAGE_SINGEING,
)  # fmt: skip

# ---- Calculation constants (BR-10..BR-29) ---------------------------------------------------------------------------
COUNT_DIVISOR: Final = Decimal(9_000_000)
CHEMICAL_BASE_WEIGHT: Final = Decimal(250)
WEFT_WIDTH_LOW: Final = Decimal(130)
WEFT_WIDTH_MID: Final = Decimal(175)
WEFT_WIDTH_HIGH: Final = Decimal(215)
QF_5000: Final = Decimal(5000)
QF_10000: Final = Decimal(10000)
QF_20000: Final = Decimal(20000)
QF_50000: Final = Decimal(50000)
QF_100000: Final = Decimal(100000)
TCDN_LARGE_METERS: Final = Decimal(50000)
TCDN_DYE_SMALL_METERS: Final = Decimal(150)
TCDN_PARTIAL_SMALL_METERS: Final = Decimal(100)
TCDN_WEIGHT_GROUP_LIMIT: Final = Decimal(150)
SPUN_SIZE_COUNT: Final = Decimal(50)
RATIO_TOLERANCE: Final = Decimal("0.0001")
TWIST_TOLERANCE: Final = Decimal("0.01")
HUNDRED: Final = Decimal(100)
TEN: Final = Decimal(10)
SIXTY: Final = Decimal(60)
FILAMENT_WORDS: Final = ("DTY", "FDY", "ATY", "POY", "NYLON")
SIZE_FILAMENT_WORDS: Final = ("SIM", "NIM")
SIZE_NAME_WORDS: Final = ("SIMHO", "HOSOI")
# BR-81 converted count: spun = 5316 / (N / k), "CB" = + 20 (sheet "Dữ liệu" of the Excel file)
SPUN_COUNT_FACTOR: Final = Decimal(5316)
CARBON_ADDITION: Final = Decimal(20)
CARBON_MARK: Final = "CB"
SPANDEX_MARK: Final = "SP"
# BR-82 twist (T/M)
TWIST_MIN: Final = 50
TWIST_MAX: Final = 3000
# BR-86 carbon yarn names -> "+ CB"
CARBON_WORDS: Final = ("CACBON", "CARBON", "C.TRANG", "C.DEN", "C TRANG")
CONTACT_TCDN: Final = "liên hệ TCDN"
TCDN_PRICED_STAGES: Final = ("Coating", "Bonding", "Santa", "Soaping")
TCDN_AUX_WORKSHOP: Final = "Phụ trợ"
TCDN_STANDARD_PREFIX: Final = "Nhuộm tiêu chuẩn"
TCDN_CPB: Final = "CPB"
TCDN_SUSE: Final = "Suse"
TCDN_MERCERIZING: Final = "Mercerzing"
TCDN_WR: Final = "WR"
# fix 2026-11-25: row added with WR in the costsheet file (row 104), stage Kiểm Trung Gian
TCDN_CHECK_BEFORE_WR: Final = "Kiểm trước WR"
TCDN_CHECK_BEFORE_WR_STAGE: Final = "Kiểm Trung Gian"
TCDN_NO_WHITE: Final = ("Khăn",)
TCDN_NO_SPECIAL: Final = ("Cotton/Nylon", "Cotton/Poly")
BLENDED: Final = "Blended"
HCM_COLORS: Final = ("Trắng", "Nhạt", "Trung bình", "Đậm", "Đặc biệt")
TCDN_COLORS: Final = ("White", "Light", "Medium", "Dark", "Special")

# ---- Limits of the costsheet lines (4.12-4.17) ----------------------------------------------------------------------
MAX_YARN_LINES: Final = 9
MAX_TWIST_LINES: Final = 9
MAX_CONE_LINES: Final = 18  # 4.14a (2026-11-26): at most 2 x the 9 Ngang Se lines
MAX_HCM_STAGES: Final = 7
MAX_HCM_FEATURES: Final = 6
MAX_HCM_SPECIAL_COSTS: Final = 2
MAX_OUTSOURCING: Final = 2
MAX_TCDN_STAGES: Final = 13
MAX_TCDN_FEATURES: Final = 6
MAX_COGS_LINES: Final = 10

# ---- Workflow, lists, labels ----------------------------------------------------------------------------------------
MIN_RETURN_REASON: Final = 5
OC_PATTERN: Final = r"^KDV\d{2}-[A-Z]{2}-[A-Z]{2}-\d{4}-\d+(\.\d+)?$"
COSTSHEET_PREFIX: Final = "CS"
COSTSHEET_SEQ_DIGITS: Final = 5
SIMILARITY_THRESHOLD: Final = 0.6
MAX_SIMILAR: Final = 10
CUSTOMER_CODE_LENGTH: Final = 4
IMPORT_LOG_LIMIT: Final = 5
LIST_DEFAULT_DAYS: Final = 90
MAX_LABELS: Final = 4
MAX_LABEL_YARNS: Final = 6
CM_PER_INCH: Final = Decimal("2.54")
MAX_CHANGES_SHOWN: Final = 300
HCM_MATERIALS: Final = ("Cotton thường", "TC/CVC/TR thường", "PE thường", "Sọc màu", "Melange")
TCDN_MATERIALS: Final = ("Khăn", "Nylon", "Cotton/Nylon", "Poly", "Cotton/Poly", "Yarn dyed")
TCDN_COLOR_ALL: Final = "All"
LIST_HCM_STAGES: Final = "Công đoạn đặc biệt HCM"
LIST_HCM_FEATURES: Final = "Tính năng đặc biệt HCM"
LIST_TCDN_STAGES: Final = "Tên công đoạn TCDN"
LIST_WR: Final = "Hóa chất WR"
LIST_SPECIAL_DYES: Final = "Phẩm nhuộm đặc biệt"
LIST_SIZE_MATERIALS: Final = "Nguyên liệu hồ"
