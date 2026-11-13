# Sewing Performance - mở rộng 2026-11-06 lần 4 (Prompt 5): Period Report thay Monthly Report

## Thêm và thay đổi
1. Screen 4 "Monthly Report" đổi tên "Period Report" (cùng vị trí trong nhóm Reports). Bỏ toàn bộ bảng theo ngày của
   từng xưởng.
2. Bộ lọc: loại kỳ By week / By month / By quarter / By year (mặc định By week), Từ ngày, Đến ngày (mặc định 01/01 của
   năm có dữ liệu mới nhất đến ngày dữ liệu mới nhất), Xưởng. Không lọc khách hàng, sản phẩm.
3. Kỳ (BR-68): tuần thứ Bảy - thứ Sáu, tên "W43 (17.10–23.10)" (số tuần ISO của ngày thứ Sáu); tháng, quý, năm dương
   lịch; kỳ ở hai đầu chỉ tính ngày trong khoảng và ghi ngày thật.
4. 8 khối, mỗi chỉ số một khối (BR-69): MO 8h, %Efficiency (with ratio), Direct worker (số thợ trung bình mỗi ngày),
   Output, Revenue, Avg CM price, Avg SMV, Avg working hours. Mỗi khối: biểu đồ đường theo kỳ và bảng
   Period | các xưởng | HCM | Total. Số của kỳ tính như Screen 1 (cộng số tổng rồi chia). Dấu 🔴 cho MO 8h, %Efficiency.
5. Không có nút tải Excel: màn hình chỉ hiển thị (người dùng bỏ UC-30 khi chốt, 06/11/2026: "không cần nút tải file
   excel chỉ cần hiển thị thôi, còn lại đồng ý").

## Ảnh hưởng tới phần đã có
- UC-08, UC-13 (báo cáo tháng theo ngày) bỏ khỏi màn hình nhưng vẫn giữ ở phía app để bài kiểm tra cũ chạy, như UC-11.
- UC-29, UC-30 dùng chung chức năng của UC-08, UC-13 với lựa chọn loại kỳ (số chức năng của app được ghim ở bài kiểm
  tra cũ). Ghi ở mục 10.
- BR-31 sửa cho Screen 4 (mặc định từ 01/01). Screen 1, 2, 3, 5, 6 và các file Excel khác không đổi.
- Không lưu thêm dữ liệu, không chuyển dữ liệu, không xoá dòng nào.

## Câu hỏi đã trả lời (06/11/2026, "ok all đề xuất")
1. Mỗi chỉ số một bảng, dòng là kỳ, cột là xưởng + HCM + Total.
2. MO 8h; %Efficiency (with ratio); Direct worker = số thợ trung bình mỗi ngày; thêm Output, Revenue, Avg CM price,
   Avg SMV, Avg working hours.
3. Tuần thứ Bảy - thứ Sáu; tháng, quý, năm dương lịch.
4. Kỳ ở hai đầu chỉ tính ngày trong khoảng, ghi ngày thật; mặc định By week từ 01/01.
5. Cộng số tổng rồi chia, HCM và Total cũng vậy.
6. Lọc xưởng, có HCM và Total, không lọc khách hàng / sản phẩm; mỗi bảng một biểu đồ đường.
7. Đổi tên "Period Report"; Excel mỗi chỉ số một sheet, bỏ file tháng cũ trên màn hình.
- Bố cục 7 card của lần 3: người dùng xác nhận "oke" (AC-79, AC-80).

## Truy vết (điền khi làm)
| Mục | Code | Kiểm tra |
|---|---|---|
| BR-68 kỳ | `PeriodBusiness.periods` | `test_period_report.py` (AC-81, AC-82) ✅ |
| BR-69 chỉ số | `ReportBusiness.period_summaries`, `_members_direct_workers`, `PERIOD_ROWS` | AC-81, AC-83, AC-84 ✅ |
| UC-29 | `get_monthly_report` + `period_kind` -> `GetMonthlyReportService._period_report` | AC-81 đến AC-84 ✅; dữ liệu thật: By week 44 kỳ, W45 Fac 2 MO 8h 41.85 = Overview ✅ |
| UC-30 | bỏ (không có nút tải) | AC-85: trang không có nút tải ✅ |
| BR-31 sửa | `FilterBusiness.default_year_start` | `test_br31_screen4_starts_on_first_january` ✅ |
| Screen 4 | `pages/monthly_report_page.py` | page render test ✅; trình duyệt: người dùng xem (khung trình duyệt của AI chưa đăng nhập) |
| regression: existing tests | toàn bộ `backend/features/sewing_productivity/tests/` | `scripts/check.py` -> ALL CHECKS PASSED (453 passed) ✅ |

## Fix log
- Đo trên dữ liệu thật: By week cả năm lần đầu khoảng 10 giây (gồm khởi động); phần tính khoảng 3 giây, mở lại cùng bộ lọc lấy từ bộ nhớ. Không đổi gì.
