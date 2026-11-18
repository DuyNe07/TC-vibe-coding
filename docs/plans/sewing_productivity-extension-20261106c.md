# Sewing Performance - mở rộng 2026-11-06 lần 3 (Prompt 5): card Avg SMV, %Direct labor, gọn biểu đồ

## Thêm và thay đổi
1. Card mới ở khu "Vinh Long - HCM" của Screen 1 (sửa BR-58): 7 card trên một hàng.
   - **Avg SMV** (min, xanh ngọc) theo BR-66: tổng (SMV × sản lượng) / tổng sản lượng, bỏ dòng thiếu SMV; lọc theo
     nhóm khách hàng, nhóm sản phẩm như sản lượng.
   - **%Direct labor** (%, xám xanh) theo BR-65: tổng số thợ / tổng nhân sự, cộng dồn các ngày có đủ hai số; lọc
     khách hàng hoặc sản phẩm thì "-".
   - Total, Vinh Long, HCM, thanh so sánh, nút ＋ hiện Fac 2, 3, 5 như 5 card cũ.
2. Sheet `Worker`: đọc thêm khối `TOTAL` (cột đầu tiên có tiêu đề `Fac.2`, `Fac.3`, `Fac.5`, `Fac.1(VL)`) thành
   tổng nhân sự. Không bắt buộc: file cũ không có khối này vẫn tải được.
3. Bỏ 2 biểu đồ ở Screen 1: "%Efficiency (no ratio) by day", "%Efficiency (with ratio - system) by day" (BR-67).
4. Bảng Metrics ở Screen 1: "%Efficiency (with ratio) vs target" ẩn mặc định, hiện cùng nút gạt
   "Show targets & with ratio - system" (sửa BR-61). Mặc định còn 10 dòng.

## Ảnh hưởng tới phần đã có
- Cách tính cũ không đổi: số thợ, MO, MO 8h, các %Efficiency, file Excel giữ nguyên.
- Hai số mới chỉ ở card, không thêm vào bảng Metrics và file Excel.
- Xếp hạng chuyền giữ đủ các lựa chọn; các biểu đồ còn lại giữ thứ tự.
- Bài kiểm tra cũ giữ nguyên, thêm bài mới cho BR-65, BR-66, BR-67, BR-61 sửa.

## Dữ liệu đã lưu
- Số thợ theo ngày (WorkerRecord) thêm ô `total_workers`, mặc định trống. Không chuyển dữ liệu, không xoá dòng.
- Ngày chưa có tổng nhân sự thì %Direct labor hiện "-". Tải lại file Data sewing ở Data Update là có số cho cả năm
  (BR-07 thay dữ liệu trong khoảng ngày của file).

## Câu hỏi đã trả lời (06/11/2026, "ok all đề xuất")
1. %Direct labor = số thợ / tổng nhân sự, cộng dồn các ngày; Total và HCM tính từ số tổng.
2. Avg SMV bình quân theo sản lượng, bỏ dòng thiếu SMV.
3. Lọc khách hàng / sản phẩm: Avg SMV lọc theo; %Direct labor hiện "-".
4. Dữ liệu cũ: "-" đến khi tải lại file.
5. 7 card một hàng; Avg SMV xanh ngọc, %Direct labor xám xanh; nút ＋ áp cho cả 7.
6. Hai số mới chỉ ở card.
7. Bỏ hẳn 2 biểu đồ; dòng vs target ẩn mặc định, hiện bằng nút gạt; Excel không đổi.

## Truy vết (điền khi làm)
| Mục | Code | Kiểm tra |
|---|---|---|
| Sheet Worker khối TOTAL, `total_workers` | `constants.py::WORKER_TOTAL_COLUMNS`, `upload_read_builders.py::_worker_rows`, `upload_business.py::_worker_records`, `WorkerRecord.total_workers` (mặc định trống) | `test_cards_extension.py::test_total_block_is_stored_with_the_direct_sewers`; file thật `Data sewing 2026 (6).xlsx`: 997 ngày-xưởng, 993 có tổng nhân sự, 02/01 Fac 2 = 599 / 345 ✅ |
| BR-65 %Direct labor | `ProductivityBusiness.direct_labor`, `ReportBusiness._members_direct_labor` | AC-75, AC-76, AC-78 ✅ |
| BR-66 Avg SMV | `ProductivityBusiness.average_smv` | AC-77 ✅ |
| BR-58 sửa (7 card) | `CARD_ROWS`, `OverviewResponse.cards`, `overview_charts.py::CARDS`, `_colored` | page render test; người dùng xác nhận trên trình duyệt sau khi đổi thứ tự (Avg SMV cạnh Avg CM price) và căn thẳng hàng (AC-79) ✅ |
| BR-67 bỏ 2 biểu đồ | `overview_charts.py::daily_charts` | page render test; trình duyệt (AC-79) |
| BR-61 sửa (ẩn vs target) | `report_cells.py::HIDDEN_METRICS` | trình duyệt (AC-80); `test_ac80_new_figures_stay_out_of_the_metrics_table` ✅ |
| regression: existing tests | toàn bộ `backend/features/sewing_productivity/tests/` | `scripts/check.py` -> ALL CHECKS PASSED (446 passed) ✅ |

## Fix log
- App cũ (bản chạy từ 11:31) đang giữ cổng 8599 nên lần chạy thử đầu tiên không khởi động -> tắt bản cũ, chạy lại bằng code mới.
