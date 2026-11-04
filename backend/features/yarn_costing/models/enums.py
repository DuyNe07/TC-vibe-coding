"""Lists of values of feature "Tính giá sợi" (section 4 of docs/business/yarn_costing.md)."""

from enum import StrEnum


class FactoryCode(StrEnum):
    S1 = "S1"
    S4 = "S4"


class GroupCode(StrEnum):
    """Role codes of the app (ticked per user on /admin, permission key yarn_costing/@CODE)."""

    SALES = "SALES"
    XS1 = "XS1"
    XS4 = "XS4"
    KT = "KT"
    SO = "SO"


class YarnStatus(StrEnum):
    CHO_XUONG_XEM = "Chờ xưởng xem"
    DA_HUY = "Đã huỷ"
    TU_CHOI = "Từ chối"
    DA_TINH_GIA = "Đã tính giá"
    CHUA_TINH_DUOC = "Chưa tính được"
    CO_MA_KE_TOAN = "Có mã kế toán"


class LineType(StrEnum):
    THUONG = "Thường"
    THI_NGHIEM = "Thí nghiệm"
    CHIET_KHAU = "Chiết khấu"
    PHU_PHI = "Phụ phí"


class LossGroupLevel(StrEnum):
    SO_CAP = "Sơ cấp"
    THU_CAP = "Thứ cấp"
    NHAP_TU_FILE = "Nhập từ file - chưa khai báo thành phần"


class RecoveryType(StrEnum):
    KHONG = "Không"
    CHAI_THO = "Chải thô"
    THO = "Thô"
    CON = "Con"


class Technology(StrEnum):
    RING = "Ring"
    MVS = "MVS"


class ImportMode(StrEnum):
    BAN_DAU = "Chuyển dữ liệu ban đầu"
    HANG_LOAT = "Cập nhật hàng loạt"
    THANH_PHAN = "Khai báo thành phần sợi pha"


class NsmMode(StrEnum):
    TU_DIEN = "Tự điền"
    TU_NHAP = "Tự nhập"


class SecondaryMethod(StrEnum):
    BINH_QUAN = "Bình quân"
    CONG_THANG = "Cộng thẳng"


class RateCodeSource(StrEnum):
    CHINH_CONG_DOAN = "Chính công đoạn"
    LOAI_DONG_GOI = "Loại đóng gói"


class YarnOrigin(StrEnum):
    YEU_CAU_SALES = "Yêu cầu Sales"
    DCNSM = "ĐCNSM"
    NHAP_TU_FILE = "Nhập từ file"


class PriceEvent(StrEnum):
    """Price history event (4.15) and recalculation trigger (4.16)."""

    TINH_LAN_DAU = "Tính lần đầu"
    SUA_NSM = "Sửa NSM"
    DOI_DINH_MUC = "Đổi định mức"
    DOI_DU_LIEU_NEN = "Đổi dữ liệu nền"
    SUA_TIEU_HAO = "Sửa tiêu hao"
    DOI_HE_SO_TN = "Đổi hệ số thí nghiệm"
    NHAP_TU_FILE = "Nhập từ file"
    TINH_LAI_CHUA_TINH = "Tính lại mã chưa tính được"
