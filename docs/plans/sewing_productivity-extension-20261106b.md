# Sewing Performance - mở rộng 2026-11-06 lần 2 (Prompt 5): file báo cáo tuần theo mẫu họp, đổi tên no ratio

## Thêm và thay đổi
1. Đổi tên ở màn hình, biểu đồ, xếp hạng và file Excel: "%Efficiency B (no ratio)" thành "%Efficiency (no ratio)",
   "Target B (no ratio)" thành "Target (no ratio)" (sửa BR-56).
2. Bảng chỉ số ở Screen 1: 2 dòng no ratio ẩn mặc định, hiện cùng nút gạt của các dòng target và with ratio - system
   (sửa BR-61). Mặc định còn 11 dòng.
3. File Excel báo cáo tuần mới, giống file `Sewing - Weekly Fac report - 24.10 to 30.10.xlsx` (UC-28, BR-64):
   - Tên file `Sewing - Weekly Fac report - <dd.mm> to <dd.mm>.xlsx`.
   - Sheet `Overall`: tiêu đề đỏ "Sewing Weekly performance (<dd.mm> to <dd.mm>)"; cột Category tô vàng, tiêu đề xưởng
     tô xanh nhạt; cột Fac Vinh Long, Fac 2, Fac 3, Fac 5, HCM. Dòng: Efficiency Target / Actual (mục tiêu A, sản lượng);
     Efficiency Target / Actual / % (mục tiêu hiệu suất, hiệu suất A, % so với mục tiêu); CM earning Actual; MO 8h
     Target / Actual / %; Average CM price; Avg working time; Matching ratio; Changeover time và dòng số lần trên chuyền.
     Dòng % chữ đỏ, tiền có dấu $, như file mẫu.
   - Sheet `Fac Vinh Long-detailed`, `Fac 2-detailed`, `Fac 3-detailed`, `Fac 5-detailed`: ô Start of week
     (Day, Month, Year); 3 khối cạnh nhau: Output (pcs) mỗi chuyền mỗi ngày Target / Actual / Efficiency, cuối dòng
     Target, Total, Efficiency, dòng Total xưởng và dòng MO 8h của xưởng theo ngày; Earning ($) chuyền × ngày, dòng
     Total, LABOR (số thợ), HOUR (giờ làm); MO 8h ($/8h) chuyền × ngày, dòng Total.
   - Ghi số, không ghi công thức Excel. Không có sheet dữ liệu thô và các sheet ẩn của file mẫu.
   - Nút "Download weekly report (Excel)" ở Screen 1 và Screen 2 tải file mới. Screen 2 chỉ có sheet của xưởng đang chọn.

## Ảnh hưởng tới phần đã có
- Cách tính không đổi: các số trong file là số app đang tính (BR-18 đến BR-28, BR-38, BR-41, BR-51).
- File báo cáo tuần cũ (sheet Tong quan / Overview) vẫn còn ở phía app nhưng không còn nút nào tải nó (UC-11 giữ nguyên
  để bài kiểm tra cũ chạy); nút trên màn hình dùng UC-28.
- Dữ liệu đã lưu không đổi, không cần chuyển dữ liệu, không xoá dòng nào.
- `test_efficiency_kinds.py` (thêm 05/11) ghim tên "%Efficiency B (no ratio)": chỉ đổi chuỗi tên theo tên mới.

## Câu hỏi đã trả lời (06/11/2026, "Ok hết đề xuất")
1. Sheet: Overall và 4 sheet Fac x-detailed.
2. Cột Overall: Fac Vinh Long, Fac 2, Fac 3, Fac 5, HCM.
3. Tên dòng Overall giữ đúng chữ file mẫu.
4. Hiệu suất trong file là loại with ratio - system như file mẫu.
5. Hai nút tải ở Screen 1 và Screen 2 tải file mới, tên file theo mẫu.
6. Changeover time lấy số đổi mã hàng tuần đã nhập, dòng dưới là số lần trên chuyền, chưa nhập thì "-".

## Truy vết (điền khi làm)
| Mục | Code | Kiểm tra |
|---|---|---|
| UC-28, BR-64 | `ExportWeeklyRequest.meeting_format`, `ExportWeeklyReportService`, `builders/meeting_report_builders.py`, nút ở `overview_page.py`, `line_detail_page.py` | `test_meeting_report.py` (AC-72 đến AC-74 + file cũ không đổi); file thật tuần 24–30/10 so với file mẫu |
| BR-56, BR-61 (sửa) | `dto/display_names.py`, `components/report_cells.py::HIDDEN_METRICS` | `test_efficiency_kinds.py` (AC-70), trình duyệt (AC-71) |

## Fix log
- Bài kiểm tra cũ ghim đúng 26 chức năng của app: UC-28 không thêm chức năng mới mà dùng chức năng tải của UC-11 với lựa chọn `meeting_format`.
| regression: existing tests | toàn bộ `backend/features/sewing_productivity/tests/` | `scripts/check.py` |
