"""English names shown on screen and in the Excel files (BR-52). Stored data keeps its own values: `Fac 1` stays `Fac 1`."""

from backend.features.sewing_productivity.models.enums import FactoryGroup

FACTORY_NAMES = {"Fac 1": "Fac Vinh Long"}
HCM_COLUMN = FactoryGroup.HCM.value
TOTAL_COLUMN = FactoryGroup.TOTAL.value
# BR-56: the two with-ratio kinds and the kind without ratio
EFFICIENCY_SYSTEM = "%Efficiency (with ratio - system)"
EFFICIENCY_SUM = "%Efficiency (with ratio)"
EFFICIENCY_NO_RATIO = "%Efficiency (no ratio)"
TARGET_SYSTEM = "Target (with ratio - system)"
TARGET_SUM = "Target (with ratio)"
TARGET_NO_RATIO = "Target (no ratio)"

ENGLISH_NAMES = {
    **FACTORY_NAMES,
    # overview and daily rows
    "Chỉ số": "Metric",
    "Mục tiêu A": TARGET_SYSTEM,
    "Sản lượng": "Output",
    "Mục tiêu hiệu suất": "%Efficiency target",
    "Hiệu suất A": EFFICIENCY_SYSTEM,
    "% so với mục tiêu của hiệu suất A": f"{EFFICIENCY_SYSTEM} vs target",
    "Mục tiêu B": TARGET_SUM,
    "Hiệu suất B": EFFICIENCY_SUM,
    "% so với mục tiêu của hiệu suất B": f"{EFFICIENCY_SUM} vs target",
    "Mục tiêu (không tỉ lệ)": TARGET_NO_RATIO,
    "Hiệu suất (không tỉ lệ)": EFFICIENCY_NO_RATIO,
    "Tiền CM": "CM earning",
    "Mục tiêu MO 8h": "MO 8h target",
    "% so với mục tiêu của MO 8h": "MO 8h vs target",
    "Giá CM trung bình": "Average CM price",
    "Giờ làm trung bình": "Average working hours",
    "Tỷ lệ đúng sở trường": "Line strength match",
    "Đổi mã hàng tuần": "Weekly changeover",
    "Đổi mã hàng tuần trên chuyền": "Weekly changeover per line",
    "Giờ làm": "Working hours",
    "Target MO 8h": "MO 8h target",
    "% so với Target MO 8h": "MO 8h vs target",
    "Mục tiêu sản lượng": "Output target",
    "Số thợ": "Workers",
    "Số người": "Sewers",
    "Đánh giá hiệu suất A": f"{EFFICIENCY_SYSTEM} assessment",
    "Đánh giá hiệu suất B": f"{EFFICIENCY_SUM} assessment",
    "Đánh giá MO 8h": "MO 8h assessment",
    "Đạt": "Passed",
    "Dưới ngưỡng": "Below threshold",
    # Excel columns and row labels
    "Hiệu suất A (%)": EFFICIENCY_SYSTEM,
    "Hiệu suất B (%)": EFFICIENCY_SUM,
    "Hiệu suất (không tỉ lệ) (%)": EFFICIENCY_NO_RATIO,
    "Xưởng": "Factory",
    "Chuyền": "Line",
    "Ngày": "Date",
    "Tháng": "Month",
    "Sản lượng trái sở trường": "Mismatched-strength output",
    "Tổng": "Total",
    "Cả kỳ": "Whole period",
    # changeover
    "Số lần đổi KPI": "KPI changeovers",
    "Số ngày làm việc": "Working days",
    "Số chuyền": "Lines",
    "KPI đổi mã hàng": "Changeover KPI",
    "Số lần đổi gồm cả lên lại": "Changeovers incl. re-runs",
    "Mã đơn gốc": "Base PO",
    "Giá CM": "CM price",
    # Excel sheets
    "Tong quan": "Overview",
    "Xuong": "Factories",
    "Chuyen": "Lines",
    "Theo xuong": "By factory",
    "Theo thang": "By month",
    "Theo chuyen": "By line",
    "Chi tiet": "Details",
    "Tien CM": "CM earning",
    "Gio lam": "Working hours",
    "So nguoi": "Sewers",
    "Hieu suat B": EFFICIENCY_SUM,
    "Hieu suat khong ti le": EFFICIENCY_NO_RATIO,
    # upload warnings and the group without a name
    "Dòng thiếu SMV": "Rows without SMV",
    "Dòng thiếu mục tiêu B": "Rows without target B",
    "Ngày có sản lượng nhưng chưa có số thợ": "Days with output but no workers",
    "Ngày có sản lượng nhưng chưa có Target system": "Days with output but no Target system",
    "Dòng trùng": "Duplicate rows",
    "Tên sản phẩm chưa phân nhóm": "Unclassified product names",
    "Style chưa có tên sản phẩm": "Styles without a product name",
    "Chưa phân nhóm": "Unclassified",
    "Hệ thống": "System",
}
# terms inside the Vietnamese sentences that the backend still writes (messages stay Vietnamese)
ENGLISH_TERMS = {
    "Hiệu suất A": EFFICIENCY_SYSTEM,
    "Hiệu suất B": EFFICIENCY_SUM,
    "số đổi mã hàng": "số Changeover",
    "Fac 1": "Fac Vinh Long",
}


def english_name(text: str) -> str:
    """A name in English; a value without a translation (LINE 1, a customer group...) stays as it is."""
    return ENGLISH_NAMES.get(text, text)


def english_terms(message: str) -> str:
    """The English names inside a Vietnamese sentence."""
    for term, name in ENGLISH_TERMS.items():
        message = message.replace(term, name)
    return message
