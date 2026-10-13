"""Constants of feature "Tính giá sợi" (UPPER_CASE values only, no classes)."""

from decimal import Decimal
from typing import Final

FEATURE_KEY: Final = "yarn_costing"

# ---- 4.3 Factories (fixed data) -------------------------------------------------------------------------------------
FACTORY_NAMES: Final = {"S1": "Xưởng Sợi 1", "S4": "Xưởng Sợi 4"}
# 4.3: carding lines (dây chuyền chải thô) of each factory, in sequence order.
CARDING_STAGES: Final = {"S4": ("C1", "C2", "C3"), "S1": ("C1", "C2")}
NO_CARDING_LABEL: Final = "Không chải thô"
MAX_PASSES_LIMIT: Final = 3
# BR-05: highest base number already used in the legacy Excel files (codes never go below it).
INITIAL_MAX_CODE: Final = {"S4": 2019, "S1": 1316}

# ---- Legacy Excel layout (5.2, 5.3, BR-58, BR-59) ------------------------------------------------------------------
# Blend-ratio cells of the old files: (cell, NSM column, carding line; "" = Không chải thô). Order = pass order.
LEGACY_CELLS: Final = {
    "S4": (
        ("PE", "C2", "C2"),
        ("Other - C3.1", "C3.1", "C3"),
        ("Other - C3.2", "C3.2", "C3"),
        ("Other - C3.3", "C3.3", "C3"),
        ("Cotton", "C1", "C1"),
    ),
    "S1": (("PE", "C1", "C1"), ("Viscose/other", "C2", "C2"), ("Cotton", "", "")),
}
BLEND_SLOTS: Final = {factory: tuple(cell for cell, _, _ in cells) for factory, cells in LEGACY_CELLS.items()}
# Old stage columns merged into one stage (BR-59: C3.1 / C3.2 / C3.3 are passes 1-3 of C3).
LEGACY_STAGE_COLUMNS: Final = {"S4": {"C3.1": "C3", "C3.2": "C3", "C3.3": "C3"}, "S1": {}}
# Old blend_slot values of stored stage rows → the carding line whose ratio they meant.
LEGACY_SLOT_LINES: Final = {
    "S4": {"Cotton": "C1", "PE": "C2", "Other - C3.1": "C3", "Other - C3.2": "C3", "Other - C3.3": "C3"},
    "S1": {"PE": "C1", "Viscose/other": "C2"},
}
COL_REMARK: Final = "REMARK"
REMARK_SCREEN_ONLY: Final = "Có thành phần chỉ sửa được trên màn hình"

# ---- 4.4.1 / 4.4.2 seeded stage configuration -----------------------------------------------------------------------
# (sequence, code, name, stage_group, recovery, blend_slot, merge, secondary_method, cumulative, varies_with_count,
#  max_passes: None = not a carding line)
_S4_MD_V: Final = ("MD1", "MD2", "MD3", "R", "S", "S Compact", "W", "V")
_S1_MD_V: Final = ("MD1", "MD2", "MD3", "R", "S", "W", "V")
_PASS: Final = "Tỷ lệ của lượt"
_LINE_C1: Final = "Tỷ lệ dây chuyền C1"
_LINE_C2: Final = "Tỷ lệ dây chuyền C2"
_CARD: Final = "Chải thô"
_NO: Final = "Không"
_AVG: Final = "Bình quân"
_SUM: Final = "Cộng thẳng"
SEED_STAGES: Final = {
    "S4": (
        (
            1,
            "C1",
            "Ăn bông - Chải thô cotton",
            "C1",
            _CARD,
            _PASS,
            False,
            _SUM,
            ("SBD", "PCD1", "PCD2", "CM", "DCM", *_S4_MD_V),
            False,
            1,
        ),
        (2, "C2", "Ăn bông - Chải thô PE", "C2", _CARD, _PASS, False, _SUM, ("PD", "PD1", *_S4_MD_V), False, 3),
        (3, "C3", "Ăn bông - Chải thô khác", "C3", _CARD, _PASS, False, _SUM, _S4_MD_V, False, 3),
        (4, "SBD", "Ghép sơ bộ CM", "SBD", _CARD, _LINE_C1, True, _AVG, ("CM", "DCM", *_S4_MD_V), False, None),
        (5, "PD", "Ghép sơ bộ PE", "D", _CARD, _LINE_C2, True, _SUM, ("PD1", *_S4_MD_V), False, None),
        (6, "PD1", "Ghép sơ bộ Viscose", "D", _NO, _NO, True, _SUM, _S4_MD_V, False, None),
        (7, "PCD1", "Ghép sơ bộ CD 1", "D", _CARD, _LINE_C1, True, _AVG, ("PCD2", *_S4_MD_V), False, None),
        (8, "PCD2", "Ghép sơ bộ CD 2", "D", _CARD, _LINE_C1, True, _SUM, _S4_MD_V, False, None),
        (9, "CM", "Chải kỹ", "CM", _CARD, _LINE_C1, False, _SUM, ("DCM", *_S4_MD_V), False, None),
        (10, "DCM", "Ghép CM sau chải kỹ", "MD", _CARD, _LINE_C1, True, _SUM, _S4_MD_V, False, None),
        (11, "MD1", "Ghép trộn A", "MD", _NO, _NO, True, _AVG, _S4_MD_V[1:], False, None),
        (12, "MD2", "Ghép trộn B", "MD", _NO, _NO, True, _SUM, _S4_MD_V[2:], False, None),
        (13, "MD3", "Ghép trộn C", "MD", _NO, _NO, True, _SUM, _S4_MD_V[3:], False, None),
        (14, "R", "Thô", "R", "Thô", _NO, False, _AVG, ("S", "S Compact", "W", "V"), True, None),
        (15, "S", "Con", "S", "Con", _NO, False, _AVG, ("W", "V"), True, None),
        (16, "S Compact", "Con - compact", "S", "Con", _NO, False, _AVG, ("W", "V"), True, None),
        (17, "W", "Ống", "W", _NO, _NO, False, _AVG, ("V",), True, None),
        (18, "V", "MVS", "V", _NO, _NO, False, _AVG, (), True, None),
        (19, "F", "Hoàn tất, đóng gói", "F", _NO, _NO, True, _SUM, (), False, None),
    ),
    "S1": (
        (1, "C1", "Chải thô PE", "C1", _CARD, _PASS, False, _AVG, ("PD", "PD2", *_S1_MD_V), False, 3),
        (2, "C2", "Chải thô đặc biệt", "C2", _CARD, _PASS, False, _AVG, ("PD", "PD2", *_S1_MD_V), False, 3),
        (3, "PD", "Ghép 1", "D", _CARD, _NO, True, _AVG, ("PD2", *_S1_MD_V[:-1]), False, None),
        (4, "PD2", "Ghép 2", "D", _NO, _NO, True, _AVG, _S1_MD_V, False, None),
        (5, "MD1", "Ghép trộn 1", "D", _NO, _NO, True, _AVG, _S1_MD_V[1:], False, None),
        (6, "MD2", "Ghép trộn 2", "D", _NO, _NO, True, _AVG, _S1_MD_V[2:], False, None),
        (7, "MD3", "Ghép trộn 3", "MD", _NO, _NO, True, _AVG, _S1_MD_V[3:], False, None),
        (8, "R", "Thô", "R", "Thô", _NO, False, _AVG, ("S", "W"), True, None),
        (9, "S", "Con", "S", "Con", _NO, False, _AVG, ("W",), True, None),
        (10, "W", "Ống", "W", _NO, _NO, False, _AVG, (), True, None),
        (11, "V", "MVS", "V", _NO, _NO, False, _AVG, (), True, None),
        (12, "F", "Hoàn tất, đóng gói", "F", _NO, _NO, True, _AVG, (), False, None),
    ),
}
PACKAGING_STAGE_CODE: Final = "F"
SEED_RECOVERY: Final = {
    "S4": {"Chải thô": Decimal("0.015"), "Thô": Decimal("0.01"), "Con": Decimal("0.025")},
    "S1": {"Chải thô": Decimal("0.02"), "Thô": Decimal("0.01"), "Con": Decimal("0.01")},
}
SEED_TRIAL_FACTOR: Final = Decimal(3)
SEED_EXCHANGE_RATE: Final = Decimal(25000)
SEED_EXCHANGE_RATE_DATE: Final = "2026-01-01"

# ---- BR-47 / BR-49: names of the use cases that change data (roles per use case: models/access.py) ----------------
SYSTEM_USERNAME: Final = "system"  # BR-49: who is recorded when no user is logged in (system code, tests)
SYSTEM_DISPLAY_NAME: Final = "Hệ thống"
USE_CASE_ACTIONS: Final = {
    "UC-03": "Sửa cấu hình công đoạn",
    "UC-04": "Áp dụng định mức chi phí/phút",
    "UC-05": "Khai báo loại đóng gói",
    "UC-06": "Khai báo hồi phế",
    "UC-07": "Khai báo quy trình công nghệ",
    "UC-08": "Cập nhật tỷ giá",
    "UC-09": "Cập nhật hệ số thí nghiệm",
    "UC-43": "Tính lại các mã chưa tính được",
    "UC-45": "Khai báo thành phần sợi pha từ file",
    "UC-11": "Thêm nhóm tiêu hao sơ cấp",
    "UC-12": "Thêm nhóm tiêu hao thứ cấp",
    "UC-13": "Sửa nhóm tiêu hao",
    "UC-14": "Xoá nhóm tiêu hao",
    "UC-15": "Tạo yêu cầu tính giá",
    "UC-16": "Sửa yêu cầu",
    "UC-17": "Huỷ yêu cầu",
    "UC-18": "Từ chối yêu cầu",
    "UC-21": "Nhập NSM và tính giá",
    "UC-23": "Sửa NSM",
    "UC-24": "Tạo bản ĐCNSM",
    "UC-25": "Tạo dòng CK/PP",
    "UC-26": "Xoá dòng CK/PP",
    "UC-28": "Nhập / sửa / xoá mã kế toán",
    "UC-34": "Nhập dữ liệu từ file",
    "UC-34-BAN-DAU": "Chuyển dữ liệu ban đầu",
}

# ---- Tolerances and limits -----------------------------------------------------------------------------------------
RATIO_TOLERANCE: Final = Decimal("0.0001")  # 0,01% (BR-09, BR-27)
MATCH_TOLERANCE_VND: Final = Decimal(1)  # BR-39, BR-55
STORAGE_QUANTUM: Final = Decimal("1E-10")  # stored amounts keep 10 decimals (far below any displayed digit)
MAX_UPLOAD_MB: Final = 60
MAX_SHEET_ROWS: Final = 10_000
HEADER_SCAN_ROWS: Final = 10
EMPTY_ROWS_STOP: Final = 300
ALLOWED_EXTENSIONS: Final = (".xlsx", ".xlsm", ".xls")
MAX_LOCKED_CODES_SHOWN: Final = 5
ACCOUNTING_CODE_MAX: Final = 100

# ---- BR-23 display precision ---------------------------------------------------------------------------------------
VND_DECIMALS: Final = 0
USD_DECIMALS: Final = 4
PERCENT_DECIMALS: Final = 2
MINUTES_DECIMALS: Final = 4
RATE_DECIMALS: Final = 2

# ---- 5.2 sheets and columns ----------------------------------------------------------------------------------------
SHEET_RATES: Final = "Dinh muc (phut)"
SHEET_RECOVERY: Final = "Hoi phe"
SHEET_PACKAGING: Final = "Dong goi"
SHEET_ROUTES: Final = "QTCN theo nhom soi"
SHEET_LOSSES: Final = "2. Input tieu hao"
SHEET_NSM: Final = "1. Input NSM"
SHEET_PRICES: Final = "4. Bang gia da tinh"
SHEET_ORDER: Final = (SHEET_RATES, SHEET_RECOVERY, SHEET_PACKAGING, SHEET_ROUTES, SHEET_LOSSES, SHEET_NSM, SHEET_PRICES)
FACTORY_SHEETS: Final = (SHEET_NSM, SHEET_LOSSES)  # BR-45: sheets a factory group may upload

COL_STAGE = "Công đoạn"
COL_STAGE_NAME = "Tên công đoạn"
COL_STAGE_GROUP = "Nhóm công đoạn"
COL_LABOR = "Nhân công"
COL_DEPRECIATION = "Khấu hao"
COL_ELECTRICITY = "Điện"
COL_MATERIALS = "Vật tư"
COL_OVERHEAD = "CPQL"
COL_NOTE = "Ghi chú"
COST_COLUMNS: Final = (COL_LABOR, COL_DEPRECIATION, COL_ELECTRICITY, COL_MATERIALS, COL_OVERHEAD)
COL_PACKAGING_NAME = "Loại đóng gói"
COL_PACKAGING_CODE = "Loại"
COL_WEIGHT = "Khối lượng"
COL_MAN_DAYS = "Công"
COL_MINUTES = "Phút/kg"
COL_YARN_GROUP = "Nhóm sợi"
COL_ROUTE_TECH = "Phân loại"
COL_COMPONENT_COUNT = "Số thành phần"
COL_ROUTE = "Quy trình công nghệ"
COL_MATERIAL = "Nguyên liệu"
COL_TECHNOLOGY = "Công nghệ"
COL_YARN_CODE = "Mã sợi"
COL_YARN_NAME = "Tên sợi"
COL_ACCOUNTING = "Mã Kế Toán"
COL_ACCOUNTING_2 = "Mã Kế toán"
COL_TOTAL = "TC"
COL_PRICED_DATE = "Ngày tính giá"
COL_SO_CHECK = "SO check"
COL_STT = "Stt"
RECOVERY_COLUMN: Final = {"S1": "Sợi 1", "S4": "Sợi 4"}
RECOVERY_LABELS: Final = {"cui ghep sau may tho": "Chải thô", "soi tho": "Thô", "bong a2": "Con"}
RECOVERY_LABEL_TEXT: Final = {"Chải thô": "Cúi ghép sau máy thô", "Thô": "Sợi thô", "Con": "Bông A2"}
RATIO_SUFFIX: Final = "2"  # S4 loss sheet: ratio column = component column name + "2" (PE2, Cotton2...)

# BR-61: a data file copied from the previous app can not be read
DATA_FILE_UNREADABLE_MESSAGE = (
    "Không đọc được dữ liệu '{file_name}'. Vui lòng chép lại file này từ app cũ (thư mục data\\yarn_costing)."
)

# BR-63: reason shown next to the disabled "Gửi yêu cầu" button (Screen 2)
SUBMIT_BLOCK_NO_PACKAGING: Final = (
    "Xưởng {factory} chưa có loại đóng gói chọn được. Vui lòng báo Phòng SO khai báo loại đóng gói và định mức."
)

# BR-64: equivalent carding lines (same technology, run in place of each other) per factory; S4 C1 (cotton) has none
EQUIVALENT_CARDING: Final = {"S4": {"C2": "C3", "C3": "C2"}, "S1": {"C1": "C2", "C2": "C1"}}

# ---- 5.7 File khai báo thành phần sợi pha (UC-44, UC-45) ----
COMP_SHEET: Final = "Khai bao thanh phan"  # read: the first sheet whose name starts with this
COMP_REF_SHEET: Final = "Danh sach nhom"
COMP_GUIDE_SHEET: Final = "Huong dan"
COMP_MAX: Final = 5
COL_COMP_NO: Final = "STT"
COL_COMP_GROUP: Final = "Nhóm sợi pha"
COL_COMP_TECH: Final = "Công nghệ"
COL_COMP_LEVEL: Final = "Loại hiện tại trong app"
COL_COMP_USAGE: Final = "Số mã đang dùng"
COL_COMP_NAME: Final = "Thành phần {k}"
COL_COMP_RATIO: Final = "Tỷ lệ {k} (%)"
COL_COMP_TOTAL: Final = "Tổng tỷ lệ (%)"
COL_COMP_LOSSES: Final = "Tiêu hao hiện tại (%)"
COMP_GUIDE_LINES: Final = (
    "File khai báo thành phần sợi pha của một xưởng (mục 5.7). Tải lên ở màn Nhập dữ liệu từ Excel, loại 'Khai báo thành phần sợi pha'.",
    "1. Sheet 'Khai bao thanh phan': mỗi dòng một nhóm tiêu hao. Điền Thành phần 1..5 (chọn trong sheet 'Danh sach nhom') và Tỷ lệ (%): 48 = 48%.",
    "2. Tổng tỷ lệ phải bằng 100%, từ 1 đến 5 thành phần. Dòng để trống mọi ô Thành phần: app không đổi nhóm đó.",
    "3. Nhóm được khai báo chuyển thành nhóm sợi pha; tiêu hao tính theo thành phần (công đoạn thành phần không có tiêu hao = 0).",
    "4. Tên nhóm chưa có trong app: app tạo nhóm sợi pha mới, cần điền cột Công nghệ (Ring hoặc MVS).",
    "5. Các cột 'Loại hiện tại trong app', 'Số mã đang dùng', 'Tổng tỷ lệ (%)', 'Tiêu hao hiện tại (%)' chỉ để xem.",
)
MSG_COMP_NO_SHEET: Final = "File không có sheet 'Khai bao thanh phan'. Vui lòng dùng file mẫu."
MSG_COMP_MISSING_COLUMNS: Final = "Sheet 'Khai bao thanh phan' thiếu cột bắt buộc: {columns}."
MSG_COMP_DUPLICATE: Final = "Nhóm '{group}' bị trùng trong file."
MSG_COMP_PAIR: Final = "Thành phần {k}: cần cả tên và tỷ lệ."
MSG_COMP_RATIO: Final = "Tỷ lệ {k} phải là số % lớn hơn 0 và không quá 100."
MSG_COMP_NOT_FOUND: Final = "Không tìm thấy nhóm thành phần '{name}' ở xưởng {factory}."
MSG_COMP_TWICE: Final = "Thành phần '{name}' bị ghi 2 lần."
MSG_COMP_NEW_TECH: Final = "Nhóm mới '{group}' cần cột Công nghệ là Ring hoặc MVS."
MSG_COMP_NO_VALID: Final = "Không có nhóm hợp lệ để lưu."
MSG_COMP_UNMATCHED: Final = (
    "Không ghép được thành phần '{material}' ({line}) của mã với thành phần của nhóm tiêu hao '{group}'. "
    "Vui lòng chọn lại nguyên liệu ở màn Nhập NSM."
)
