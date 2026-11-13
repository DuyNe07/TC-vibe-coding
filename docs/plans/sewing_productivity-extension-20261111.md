# Sewing Performance - mở rộng 2026-11-11 (Prompt 5): Line performance thay Changeover, thanh "Jump to"

## Thêm và thay đổi
1. Screen 6 "Changeover" -> "Line performance" (cùng vị trí menu, đường dẫn `.../changeover` giữ để quyền không đổi).
   Bộ lọc: Từ ngày, Đến ngày (mặc định tuần thứ Bảy - thứ Sáu gần nhất), một xưởng (mặc định Fac Vinh Long).
2. Bảng theo chuyền (BR-78): Line | Number of Operators | Output Target / Actual / Ratio | Value Target / Actual /
   Ratio | MO $ (8h); dòng Total (BR-79); ▼ dưới ngưỡng cho Output Ratio và MO 8h (BR-80).
3. Không có nút tải Excel: người dùng bỏ UC-32 khi chốt (11/11/2026: "không cần down file excel, đồng ý all").
4. Screen 4: thanh "Jump to" 8 thẻ chuyển nhanh tới từng chỉ số, "Back to top" cuối mỗi chỉ số (AC-104).

## Ảnh hưởng tới phần đã có
- UC-10, UC-15 (đổi mã hàng) bỏ khỏi màn hình, vẫn giữ phía app để bài kiểm tra cũ chạy. UC-31, UC-32 dùng chung
  chức năng xem / tải của UC-10, UC-15 với một lựa chọn kiểu báo cáo (số chức năng của app được ghim ở bài kiểm tra cũ).
- Số đổi mã hàng tuần vẫn nhập ở Data Update (UC-18 đến UC-20) và vẫn vào file báo cáo tuần (BR-38, BR-41, BR-64).
- BR-31 sửa cho Screen 6. Không lưu thêm dữ liệu, không chuyển dữ liệu.

## Câu hỏi đã trả lời (11/11/2026, "Ok all đề xuất")
1a thay hẳn Changeover; 2a lọc ngày + một xưởng; 3a Value Actual = tiền CM; 4a bỏ dòng thiếu mục tiêu khỏi hai vế
Ratio; 5a có dòng Total; 6a ▼ cho Output Ratio và MO 8h; 7a có Download Excel; 8a làm thanh "Jump to".

## Truy vết (điền khi làm)
| Mục | Code | Kiểm tra |
|---|---|---|
| UC-31, BR-78 | `GetChangeoverService._line_performance`, `LinePerformanceBusiness.rows` | AC-106 ✅; dựng thử trang (SQLite tạm): đủ 9 cột, 3 chuyền + Total ✅ (AC-105) |
| BR-79 | `LinePerformanceBusiness._total` | AC-107: Total = Overview (Output, %Efficiency, CM earning, MO 8h) ✅ |
| BR-80 | `assess_efficiency`, `assess_mo8h` (mức ngày cuối) | AC-108 ✅; chú thích "▼ below threshold" ✅ |
| UC-32 bỏ (không có nút tải) | `pages/changeover_page.py` không còn nút tải | AC-109 ✅ |
| Jump to (Screen 4) | `MonthlyReportPage._jump_bar`, `_anchor` | dựng thử: 8 liên kết `#metric-...` khớp tiêu đề, "Back to top" -> `#jump-to` ✅ (AC-104; cuộn thật cần trình duyệt) |
| regression: existing tests | toàn bộ `backend/features/sewing_productivity/tests/` | `scripts/check.py` -> ALL CHECKS PASSED (472 passed) ✅; `scripts/doctor.py` -> APP IS HEALTHY ✅ |

## Fix log
