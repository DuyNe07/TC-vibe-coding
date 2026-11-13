# Sewing Performance - mở rộng 2026-11-13 (Prompt 5): gộp Line Detail + Line performance, Matching theo bảng sở trường, Changeover mới, 2 chỉ số mới ở Sewing metrics

## Thêm và thay đổi
1. **Gộp màn hình.** Menu Reports bỏ mục "Line performance" (Screen 6); bảng Line performance không còn hiện.
   Line Detail (Screen 2) có nút "Download Line performance", tải đúng file 4 sheet của BR-85 theo khoảng ngày đang
   chọn ở Line Detail (UC-32 đổi chỗ bấm). Nút "Tải Excel báo cáo tuần" bỏ khỏi Line Detail (vẫn có ở Overview).
2. **Matching theo bảng sở trường (BR-86, mới).** Mỗi dòng sản lượng: nhóm sản phẩm (BR-14) nằm trong 4 nhóm hàng mạnh
   của chuyền (file Line Strength, 4.11) là đúng sở trường. Matching = sản lượng đúng / sản lượng được xét. Dòng
   "Chưa phân nhóm" và chuyền chưa có sở trường bỏ khỏi cả tử và mẫu. Áp cho: bảng chuyền Line Detail (sửa BR-83),
   dòng "Line strength match" ở Overview và các file dùng số này (sửa BR-25), chỉ số mới ở Sewing metrics.
   Cách tính giống cột `Match line strength` của file tham khảo `Data sewing 2026 - MATCH STRENGTH.xlsx`
   (PRODUCT REVISED so với STRENGTH 1-4 của chuyền) - app tự tính, không đọc cột này.
3. **Changeover mới (BR-87, mới).** Theo từng chuyền, "mã hàng" = Nhóm khách hàng + SMV + giá CM. Mỗi ngày làm việc
   của chuyền trong khoảng: một mã hàng được tính 1 lần nếu ngày làm việc liền trước của chuyền không chạy mã hàng này
   (lần đầu lên chuyền cũng tính; nghỉ ít nhất 1 ngày làm việc của chuyền rồi lên lại thì tính thêm 1 lần). Đơn, style
   khác nhau mà trùng mã hàng chỉ tính 1 lần. Dòng thiếu SMV không đếm. Thay cách đếm mã đơn gốc của BR-83.
4. **Bảng chuyền Line Detail** thêm cột %Efficiency (with ratio) (BR-19) ngay sau Output, ▼ khi dưới ngưỡng.
   %Efficiency và MO 8h trình bày nổi bật, dễ đọc (cách trình bày chốt ở vòng giao diện, Step 5).
5. **Bảng đơn hàng của chuyền (BR-88, mới)** thêm SMV (bình quân theo sản lượng) và %Efficiency (with ratio) của đơn
   (sản lượng / tổng `Standard output of SMV (have efficiency ratio)` của đơn), không dùng loại "with ratio - system".
6. **Sewing metrics (BR-89, mới)** thêm 2 chỉ số sau Avg working hours: Matching strength (%) và Changeover/line/day
   (tổng changeover / số ngày làm việc / số chuyền của kỳ, 3 chữ số lẻ); có thẻ số, biểu đồ, bảng và mục trong
   "Jump to". Mũi tên Matching: tăng xanh, giảm đỏ; Changeover/line/day: có mũi tên, không tô màu.
7. File Excel Line performance giữ nguyên (không thêm cột).

## Ảnh hưởng tới phần đã có
- Đổi theo yêu cầu: BR-25 (Overview), BR-29 (Matching nay lọc theo khách hàng / sản phẩm như Output), BR-83 (Matching,
  Changeover, cột mới), BR-84 (2 cột mới), BR-69/BR-70 (2 chỉ số), Screen 2, 4, 6, UC-06, UC-11, UC-29, UC-31, UC-32.
  AC-112, AC-113 đổi theo cách tính mới (ghi "sửa"); bài kiểm tra cũ của 2 AC này được cập nhật theo yêu cầu mới,
  các bài kiểm tra khác giữ nguyên.
- File báo cáo tuần và file mẫu họp: dòng Matching ratio đổi theo BR-86 (cùng số với Overview).
- Quyền: người đã được cấp "Line performance" cần quản trị viên cấp "Line Detail" để tải file Line performance.
- Không đổi: cách tính Output, MO 8h, Working hours; file Line performance (BR-85); 8 chỉ số cũ của Sewing metrics;
  file Line Strength và cách lưu (BR-81, BR-82); số đổi mã hàng tuần nhập tay (BR-38, BR-41).

## Dữ liệu đã lưu
Không thêm trường, không thêm bảng, không chuyển dữ liệu: mọi số mới tính lại từ dòng sản lượng và sở trường đã lưu.

## Câu hỏi đã trả lời (13/11/2026, người dùng: "ok all")
1a menu chỉ còn Line Detail, nút "Download Line performance", bỏ nút báo cáo tuần ở Line Detail;
2a Matching theo bảng sở trường ở Line Detail, Sewing metrics và Overview; dòng chưa phân nhóm / chuyền chưa có sở
trường bỏ khỏi cả tử và mẫu; 3a SMV bình quân theo sản lượng + %Efficiency (with ratio) của đơn; 4 cột %Efficiency
sau Output, nổi bật dễ đọc; 5a Changeover theo Khách hàng + SMV + CM, lên lại sau ít nhất 1 ngày làm việc thì tính
thêm, áp cả cho cột Changeover của Line Detail; 6 hai chỉ số mới ở Sewing metrics như đề xuất; 7a file Excel giữ nguyên.

## Truy vết
| Mục | Code | Kiểm tra |
|---|---|---|
| BR-86 | `LineStrengthBusiness.strong_map` / `row_matches` / `matching_ratio`, `ReportSource.strengths`, `ReportFacts.strengths`, `ReportBusiness._summary`, `LineOverviewBusiness.rows` | AC-117, AC-118 ✅ (`test_extension_20261113.py`); dữ liệu thật: LINE 32 Fac Vinh Long tuần mặc định Matching 100.0%, khớp các đơn ✅ |
| BR-87 | `ChangeoverBusiness.code_of` / `code_days` / `style_changeovers`, `ReportBusiness.code_days`, `LineOverviewBusiness.changeover` | AC-119 + bài cách quãng ✅ |
| BR-83 sửa (cột %Efficiency) | `LineOverview.efficiency` / `efficiency_assessment`, `line_overview_blocks.line_table` | AC-121 ✅ (bằng Output Ratio của Line performance; Total bằng Overview) |
| BR-88 | `LineOrder.smv` / `efficiency`, `order_dtos`, `line_overview_blocks.line_details` | AC-120 ✅ |
| BR-89 | `ReportBusiness._style_changeovers`, `PERIOD_ROWS`, `CHANGEOVER_PER_LINE_DAY`, `RISING_IS_GOOD`, `monthly_report_page` | AC-123 ✅; dựng trang với dữ liệu thật: 10 chỉ số, không lỗi ✅ |
| Gộp màn hình, UC-32 đổi chỗ bấm | `line_detail_page._line_performance_file`, `manifest.py`, xoá trang `changeover_page.py` | dựng Line Detail với dữ liệu thật: nút "Download Line performance" + ghi chú ✅; menu trong trình duyệt: chưa xem (cần đăng nhập) |
| regression: existing tests | toàn bộ bài kiểm tra của app | quality gate: ALL CHECKS PASSED (484 passed) ✅; health check: APP IS HEALTHY ✅. Hai bài cũ đổi theo quy tắc mới: AC-112 (Matching), bài Overview (BR-25); bài AC-81 bỏ qua Changeover/line/day vì Screen 1 không có số này |

## Fix log
- 2026-11-13: Sewing metrics theo tuần cả năm mất ~16 giây lần đầu sau khi thêm Changeover. Nguyên nhân: mỗi kỳ đếm lại từ ngày đầu tiên của dữ liệu. Sửa: `style_changeovers` nhảy thẳng tới ngày đầu kỳ (`bisect_left`). Còn ~3,6 giây; quality gate vẫn xanh.
