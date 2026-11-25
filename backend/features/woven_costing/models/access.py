"""Roles of the app (BR-51), labels shown on /admin, and the roles allowed per use case."""

from typing import Final

from backend.features.woven_costing.models.enums import RoleCode

ROLE_LABELS: Final = {
    RoleCode.SALES: "Sales",
    RoleCode.TRUONG_TEAM: "Trưởng team",
    RoleCode.TRUONG_DON_VI: "Trưởng đơn vị",
    RoleCode.SO: "Phòng SO",
    RoleCode.PD: "PD",
    RoleCode.FS1: "Team FS1",
    RoleCode.FS2: "Team FS2",
}
TEAM_ROLES: Final = (RoleCode.FS1.value, RoleCode.FS2.value)
_S, _T, _D, _SO, _PD = (
    RoleCode.SALES.value, RoleCode.TRUONG_TEAM.value, RoleCode.TRUONG_DON_VI.value, RoleCode.SO.value, RoleCode.PD.value,
)  # fmt: skip
# BR-51 / BR-85: SO creates and works on costsheets like sales (mostly to try the app)
CREATORS: Final = (_S, _T, _SO)
SO_TEAM: Final = RoleCode.SO.value  # team of a costsheet made by a user with only the SO role (BR-51)
# Section 6 actors: use case -> roles allowed (checked by AccessBusiness; system code and tests pass).
USE_CASE_ROLES: Final = {
    "UC-01": (_SO,),
    "UC-02": (_SO,),
    "UC-03": (_SO, _PD),
    "UC-05": (_SO,),
    "UC-07": (_SO,),
    "UC-09": (_SO,),
    "UC-10": (_SO,),
    "UC-11": (_SO,),
    "UC-12": (_SO,),
    "UC-13": (_SO,),
    "UC-14": CREATORS,
    "UC-15": CREATORS,
    "UC-16": CREATORS,
    "UC-17": CREATORS,
    "UC-18": (_S, _T, _SO),
    "UC-19": CREATORS,
    "UC-20": CREATORS,
    "UC-21": (_T, _D, _SO),
    "UC-22": (_T, _D, _SO),
    "UC-23": CREATORS,
    "UC-24": CREATORS,
    "UC-25": CREATORS,
    "UC-26": (_S, _T, _D, _SO, _PD),
    "UC-36": (_SO,),
    # 2026-11-25 dyeing job order (Screen 8): approve / return reuse UC-21 / UC-22
    "UC-40": CREATORS,
    "UC-41": CREATORS,
    "UC-42": CREATORS,
    "UC-43": CREATORS,
    "UC-45": CREATORS,
    "UC-37": (_SO,),
}
USE_CASE_NAMES: Final = {
    "UC-01": "Kiểm tra dữ liệu vải",
    "UC-02": "Lưu dữ liệu vải",
    "UC-03": "Nhập nhanh / sửa mã vải",
    "UC-05": "Cập nhật tỷ giá",
    "UC-07": "Lưu bộ định mức",
    "UC-09": "Lưu bộ tham số",
    "UC-10": "Hệ số theo mã hàng",
    "UC-11": "Ngày lễ",
    "UC-12": "Tải danh sách khách hàng",
    "UC-13": "Sửa khách hàng",
    "UC-14": "Sửa thông số vải",
    "UC-15": "Tạo costsheet",
    "UC-16": "Tính lại costsheet",
    "UC-17": "Lưu nháp",
    "UC-18": "Thêm khách hàng",
    "UC-19": "Sao chép costsheet",
    "UC-20": "Gửi duyệt",
    "UC-21": "Duyệt",
    "UC-22": "Trả lại",
    "UC-23": "Tạo phiên bản mới",
    "UC-24": "Lưu OC / Chốt đơn",
    "UC-25": "Hủy costsheet",
    "UC-26": "In nhãn",
    "UC-36": "Xem trước danh sách khách hàng",
    "UC-37": "Kiểm tra bộ định mức",
    "UC-40": "Tạo phiếu gia công",
    "UC-41": "Tính phiếu gia công",
    "UC-42": "Lưu phiếu gia công",
    "UC-43": "Gửi duyệt phiếu gia công",
    "UC-45": "Sao chép phiếu gia công",
}
