# Sewing Performance - mở rộng 2026-11-09 lần 2 (Prompt 5): Sewing metrics, cách viết số, dấu dưới ngưỡng, %Direct labor

## Thêm và thay đổi
1. Screen 4 đổi tên "Period Report" -> "Sewing metrics" (menu, tiêu đề). Đường dẫn giữ `.../monthly`.
2. BR-75: số trên mọi màn hình của app viết `1,234.56` (trước đây `1.234,56`). Excel không đổi.
3. BR-76 (sửa BR-28): dấu 🔴 -> `▼` sau số trong bảng (ghi chú "▼ below threshold" dưới bảng); thẻ số dưới ngưỡng có
   tên màu đỏ kèm ▼.
4. BR-77: tab Direct worker thêm hàng thẻ %Direct labor (BR-65 theo kỳ, so sánh BR-71, không tô màu).
5. Số trên từng điểm biểu đồ và định dạng số bên trong biểu đồ: chờ người phụ trách khung sườn (mục 10).

## Ảnh hưởng tới phần đã có
- Mọi màn hình: chỉ đổi cách viết số và ký hiệu dưới ngưỡng; số, cách tính, đánh giá BR-28 không đổi.
- UC-29 trả thêm số %Direct labor theo kỳ (cùng chức năng, không thêm chức năng mới).
- Không lưu thêm dữ liệu, không chuyển dữ liệu.

## Câu hỏi đã trả lời (09/11/2026)
1a đổi cách viết số cả app; 2a ghi yêu cầu số trên điểm biểu đồ cho khung sườn; 3a giữ đường dẫn; thêm thẻ
%Direct labor ở tab Direct worker; "tìm cách bỏ dấu đỏ bằng signal khác" -> ▼ (đề xuất của AI, chốt ở bước "đồng ý").

## Truy vết (điền khi làm)
| Mục | Code | Kiểm tra |
|---|---|---|
| Đổi tên Screen 4 | `MonthlyReportPage.title` | dựng thử không trình duyệt: breadcrumb "Sewing metrics", slug `monthly` giữ ✅ |
| BR-75 | `components/number_format.py` | dựng thử: `5.31`, `+0.15`, `4,280`, `322.7` ✅ |
| BR-76 | `report_cells.BELOW_MARK`, `below_note`, `period_cards` | dựng thử: thẻ `:red[Fac 2 ▼]`, chú thích "▼ below threshold" ✅ |
| BR-77 | `PERIOD_ROWS`, `EXTRA_CARDS` | `test_ac102_...` (bằng card Screen 1, không tô màu, so W42 10.10–13.10) ✅; dựng thử: hàng thẻ %Direct labor ở tab Direct worker ✅ |
| regression: existing tests | toàn bộ `backend/features/sewing_productivity/tests/` | `scripts/check.py` -> ALL CHECKS PASSED (468 passed) ✅; `scripts/doctor.py` -> APP IS HEALTHY ✅ |

## Sửa 2026-11-10 (người dùng yêu cầu)
- Bỏ 8 tab: các chỉ số xếp dọc theo thứ tự BR-69; biểu đồ nhỏ vào khối gấp "Charts" (dấu ＋, mặc định đóng, chỉ vẽ
  khi mở); bảng số vẫn gấp. Kiểm tra: `scripts/check.py` -> ALL CHECKS PASSED (468) ✅; dựng thử trên SQLite tạm:
  không còn tab, 8 khối đúng thứ tự, 54 thẻ, 0 biểu đồ khi đóng, 4 biểu đồ khi mở "Charts" của MO 8h ✅ (AC-103).
- Số trên từng điểm biểu đồ: vẫn chờ người phụ trách khung sườn (biểu đồ dùng chung chưa có lựa chọn này).
- Trình duyệt: chưa xem được, app không khởi động vì cơ sở dữ liệu chung từ chối mật khẩu trong `.env` (10/11/2026).

## Fix log
- Trình duyệt: u-admin vẫn chỉ thấy "Tính giá sợi" ở bản cổng 8600 (quyền trên cơ sở dữ liệu chung), nên kiểm tra bằng cách dựng trang không trình duyệt (Streamlit AppTest) trên một cơ sở dữ liệu SQLite tạm, không đụng dữ liệu thật.
