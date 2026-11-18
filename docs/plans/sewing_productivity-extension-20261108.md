# Sewing Performance - mở rộng 2026-11-08 (Prompt 5): Period Report dễ nhìn hơn (phương án A)

Khảo sát hiện trạng (ảnh chụp, số liệu thật 8 biểu đồ cũ, lý do khó nhìn):
`docs/business/_sources/sewing_productivity-period-report-ui-discovery.md`.

## Thêm và thay đổi
1. Screen 4: 8 khối xếp dọc thành 8 tab cùng thứ tự (BR-69).
2. Đầu mỗi tab: thẻ số cho mỗi cột (các xưởng đã chọn, HCM khi hiện, Total): số kỳ cuối, mũi tên + mức thay đổi so
   với kỳ trước, biểu đồ mini các kỳ, 🔴 cho MO 8h và %Efficiency như bảng (BR-70).
3. Số so sánh (BR-71): kỳ đứng ngay trước trong bảng, tính trên cùng số ngày lịch với kỳ cuối (kỳ cuối chưa hết thì
   so cùng số ngày đầu của kỳ trước); ghi "vs <kỳ trước> (<dd.mm>–<dd.mm>)". Chỉ 1 kỳ hoặc số "-": không mũi tên.
4. Biểu đồ: mỗi cột một biểu đồ nhỏ có thang riêng, gồm cả HCM và Total (thay biểu đồ đường chung 4 xưởng).
5. Bảng số giữ nguyên nội dung, trải hết bề ngang.

## Ảnh hưởng tới phần đã có
- UC-29 sửa: cùng chức năng xem, trả thêm số thẻ (không thêm chức năng mới, số chức năng của app giữ nguyên).
- BR-68, BR-69 không đổi; số trong bảng không đổi (AC-81 đến AC-84 phải vẫn đúng). AC-86 (bộ lọc, mặc định) không đổi.
- Screen 1, 2, 3, 5, 6, 7, 8, 9 và mọi file Excel không đổi.
- Dữ liệu: không lưu thêm, không chuyển, không xoá dòng nào.

## Câu hỏi đã trả lời (08/11/2026)
- Tăng là tốt: MO 8h, %Efficiency, Output (người dùng); Revenue (đề xuất, "Ok all đề xuất"). SMV chỉ thể hiện độ khó
  sản phẩm: không tô màu; Direct worker, Avg CM price, Avg working hours: không tô màu.
- Kỳ chưa hết: thẻ ghi số cộng dồn đến ngày đó; so với cùng số ngày đầu của kỳ trước.
- Kỳ thiếu ngày: vẫn vẽ.
- Loại kỳ: giữ tuần, tháng, quý, năm; mặc định tuần.
- Thẻ và biểu đồ nhỏ cho các xưởng, HCM, Total. Thẻ có 🔴 như bảng.

## Truy vết (điền khi làm)
| Mục | Code | Kiểm tra |
|---|---|---|
| BR-70 | `PeriodBusiness.rising_is_good`, `period_blocks.period_cards` | `test_br70_...` ✅; trình duyệt: Output, MO 8h xanh/đỏ, Avg SMV xám ✅ |
| BR-71 | `PeriodBusiness.comparison_range`, `changes`, `GetMonthlyReportService._compared` | `test_br71_...` (2 bài), AC-87, AC-89, AC-90 ✅ |
| UC-29 sửa | `PeriodReportResponseBuilder._cards`, `PeriodCardDTO` | AC-87 đến AC-91 ✅; dữ liệu thật: Output Fac Vinh Long W45 151.288, +911 = 151.288 − 150.377 (Overview 24/10–29/10) ✅; MO 8h −0,14 = 33,50 − 33,64 ✅; By year không mũi tên ✅ |
| Screen 4 | `pages/monthly_report_page.py`, `components/period_blocks.py` | page render test ✅; trình duyệt (cổng 8600): 8 tab, 6 thẻ, 6 biểu đồ nhỏ, bảng gấp; By month: cột, "vs Oct 2026 (01.10–05.10)" ✅ |
| regression: existing tests | toàn bộ `backend/features/sewing_productivity/tests/` | `scripts/check.py` -> ALL CHECKS PASSED (460 passed, trước đó 453) ✅; `scripts/doctor.py` -> APP IS HEALTHY ✅ |

## Fix log
- Biểu đồ nhỏ 3 cái mỗi hàng: nhãn tháng dưới trục dính nhau ("Jan 2026Mar 2026...") ở màn hình 1440 px -> đổi 2 biểu đồ mỗi hàng -> chụp lại, nhãn rõ.
- Dòng "vs W44 (24.10–29.10)" trong thẻ bị cắt ("vs W4…") -> đưa lên dòng chú thích trên hàng thẻ và vào dấu ? của thẻ -> chụp lại, đọc đủ.
- Tab Output: 6 thẻ một hàng cắt số ("151.2…") -> số dài hơn 6 ký tự thì 3 thẻ mỗi hàng -> chụp lại, đủ số.
- Xem theo tuần cả năm có 44 kỳ, biểu đồ cột dùng chung chỉ giữ 30 cột -> từ 30 kỳ vẽ vùng tô màu; By month vẽ cột -> kiểm tra trên trình duyệt.
- Sửa lần 2 (người dùng yêu cầu): bảng số xoay lại, dòng là xưởng / HCM / Total, cột là kỳ (AC-93). Cột "Factory" tự co làm cắt "Fac Vinh Long" -> đặt rộng 120 px -> chụp lại, đủ chữ; By month ô Fac 2 / Feb 2026 = 38,07 🔴 như trước ✅.
- Yêu cầu đổi 🔴 thành chữ đỏ: chưa làm được, bảng dùng chung của khung sườn chỉ ghi chữ thường, không tô màu từng ô; cần người phụ trách khung sườn bổ sung.
- App ở cổng 8501 chạy từ trước và không tự nạp mã mới -> chạy bản mới ở cổng 8600 để kiểm tra; bản 8501 cần khởi động lại.
