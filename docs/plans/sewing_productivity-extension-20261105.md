# Sewing Performance - mở rộng 2026-11-05

Người dùng yêu cầu trực tiếp, trên nhánh đang làm.

## Thêm và thay đổi
- Tên app "Năng suất xưởng may" thành "Sewing Performance". Tên trên màn hình và trong Excel sang tiếng Anh. "Đổi mã hàng" thành "Changeover", "Hiệu suất" thành "%Efficiency", Fac 1 hiển thị là "Fac Vinh Long" (BR-52).
- Cột HCM gộp Fac 2, 3, 5 ở Screen 1, Screen 3, Excel của hai màn hình, và trong biểu đồ Screen 1 (UC-27, BR-51).
- Nhãn số cho biểu đồ, khối Summary ở Screen 1 (BR-54). In đậm %Efficiency và MO 8h trong bảng trên màn hình (BR-53).

## Ảnh hưởng tới phần đã có
- Dữ liệu đã lưu không đổi, không cần chuyển dữ liệu: `Factory.FAC_1` vẫn là `Fac 1`, tên mới chỉ dùng khi hiển thị (`dto/display_names.py`). Mã `sewing_productivity`, đường dẫn app, vai trò `UPDATER` giữ nguyên.
- Số của từng xưởng không đổi (AC-54). `factory_summary`, `daily_summary`, `period_mo8h` dùng chung cách tính với HCM, kết quả cho một xưởng như cũ.
- Bài kiểm tra cũ giữ nguyên, không sửa bài nào. Vì vậy các tên tiếng Việt trong DTO (`metric`, `title`) và file Excel mặc định được giữ; màn hình dịch khi hiển thị, còn file Excel dịch khi yêu cầu có `english=True`, là giá trị mọi màn hình đang gửi. Đường HCM trong biểu đồ nằm ở trường riêng `hcm_*` của `ChartsResponse`.

## Đợt sửa thứ 2 cùng ngày: 3 loại hiệu suất
Người dùng yêu cầu: nhóm có tỉ lệ có 2 mục (lấy mục tiêu từ sheet system, và cộng cột), cộng thêm Efficiency B không tỉ lệ từ cột `Standard output of SMV (no efficiency ratio)`.
- Hiệu suất A cũ thành `%Efficiency (with ratio - system)`, hiệu suất B cũ thành `%Efficiency (with ratio - sum)`, số không đổi. Thêm `%Efficiency B (no ratio)` (BR-55, BR-56).
- Dữ liệu: thêm trường `standard_output_no_ratio`, mặc định trống; dòng đã lưu không cần chuyển dữ liệu nhưng hiện "-" đến khi tải lại file. Không xoá dòng nào.
- Bài kiểm tra: bài cũ của đợt đầu giữ nguyên. `test_sewing_performance.py` (thêm trong đợt sửa thứ nhất, cùng ngày) có 3 chỗ ghim tên `%Efficiency A/B` mà người dùng vừa đổi: chỉ đổi chuỗi tên, không đổi con số nào. Bài mới: `test_efficiency_kinds.py`.

## Truy vết
| Mục | Code | Kiểm tra |
|---|---|---|
| UC-27, BR-51 | `ReportBusiness.hcm_summary`, `hcm_daily_summary`, `hcm_days`, `hcm_members`, `_common_goal` | `test_sewing_performance.py`: AC-53, AC-54, AC-55, AC-56 |
| BR-52 | `dto/display_names.py`, `builders/display.py:file_sheets`, các trang trong `frontend/features/sewing_productivity/` | `test_sewing_performance.py`: AC-57, AC-58; trình duyệt |
| BR-53 | `components/report_cells.py` (`BOLD_LABELS`, `number_cells`, `metric_rows`) | trình duyệt |
| BR-54 | `components/overview_charts.py` | trình duyệt |
| BR-55, BR-56 | `productivity_business.py`, `report_business.py`, `line_report_business.py`, `dto/display_names.py` | `test_efficiency_kinds.py`: AC-59 đến AC-63 |
| regression: existing tests | toàn bộ `backend/features/sewing_productivity/tests/` | `scripts/check.py` |

## Fix log
- `dto` không được import `constants` theo quy tắc lớp: tên nhóm HCM chuyển vào `models/enums.py` (`FactoryGroup`).
- `test_ac41_charts_and_ranking` ghim danh sách điểm của biểu đồ: không sửa bài này, đường HCM tách sang trường `hcm_*`.
