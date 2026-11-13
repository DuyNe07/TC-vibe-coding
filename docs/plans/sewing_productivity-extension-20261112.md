# Sewing Performance - mở rộng 2026-11-12 (Prompt 5): Line Detail mới, sở trường chuyền, bỏ 2 màn hình, Excel Line performance

## Thêm và thay đổi
1. Menu Reports bỏ Daily Report (Screen 3) và MO by Line (Screen 5). Dữ liệu không mất.
2. Line Detail (Screen 2): bảng mỗi dòng một chuyền (BR-83): Output, MO 8h, Working hours, Matching ratio,
   Changeover, dòng Total; chọn một dòng -> chi tiết chuyền (BR-84): sở trường + đơn hàng trong kỳ (Order gốc,
   Customer, Style, Product type, CM price, Output, First day on line, Matches strength). Bảng theo ngày bỏ.
3. Sở trường chuyền (4.11): tải file Line Strength ở ô tải file của Data Update (UC-33, BR-81, BR-82), lưu thay bản
   cũ (bản cũ đánh dấu xoá), ghi lịch sử tải file; xem ở Catalogs thẻ "Line strength" (UC-34). Nhóm hàng dùng danh
   mục Nhóm sản phẩm (4.6). Không đọc dữ liệu từ file họp tuần.
4. Line performance: nút "Download Excel" (UC-32 làm lại, BR-85), bố cục hai tầng như mẫu.

## Ảnh hưởng tới phần đã có
- Số chức năng của app được ghim ở bài kiểm tra cũ: UC-33 đi qua chức năng kiểm tra / lưu file của UC-01, UC-02
  (app nhận ra loại file); UC-34 qua chức năng xem danh mục UC-21; UC-06 trả thêm bảng chuyền mới; UC-32 qua chức năng
  tải của UC-15. UC-07, UC-09, UC-12, UC-14 còn ở phía app nhưng không còn màn hình nào gọi.
- Dữ liệu: thêm bảng sở trường chuyền (bảng mới, không chuyển dữ liệu cũ). Bảng lịch sử tải file ghi thêm loại file
  qua tên sheet trong chi tiết (BR-72). Không xoá dòng nào.
- Quyền đã cấp cho Daily Report và MO by Line không còn tác dụng; các quyền khác không đổi.

## Câu hỏi đã trả lời (12/11/2026)
"không lấy dữ liệu trong file họp tuần, chỉ tham khảo, line strength phải lấy theo file ... có sẵn trên database,
all đề xuất": 1a bảng chuyền cả kỳ; 2a Matching ratio theo sản lượng; 3a Changeover đếm mã đơn gốc mới; 4a chọn dòng
xem chi tiết; 5a đơn trong khoảng đang chọn; 6a tải file ở Data Update, xem ở Catalogs; 7a bỏ khỏi menu;
8a Excel một xưởng, hai tầng tiêu đề.

## Truy vết (điền khi làm)
| Mục | Code | Kiểm tra |
|---|---|---|
| 4.11, UC-33, BR-81, BR-82 | `LineStrengthReadBuilder`, `LineStrengthBusiness`, `SaveUploadService._save_strength` | `test_line_strength.py` (3 bài) ✅; file thật `Sewing Line Strength (14-Jul-2026).xlsx` trên SQLite tạm: đọc 82, lưu 82, bỏ qua 0, "Đã lưu sở trường của 82 chuyền." ✅ (AC-110) |
| UC-34 | `GetCatalogsService`, `CatalogsPage._line_strengths` | dựng thử Catalogs không lỗi ✅ |
| BR-83 | `LineOverviewBusiness.rows`, `changeover`, `matching_ratio` | AC-112, AC-113 ✅; dựng thử Line Detail: bảng Line / Output / MO 8h / Working hours / Matching ratio / Changeover + Total ✅ |
| BR-84 | `LineOverviewBusiness.orders`, `LineStrengthBusiness.matches`, `line_overview_blocks.line_details` | AC-114 ✅ (chọn dòng trên giao diện: chưa thử bằng trình duyệt) |
| Bỏ Screen 3, 5 | `manifest.py` | menu: Overview, Line Detail, Sewing metrics, Line performance, Data Update, Targets & Thresholds, Catalogs ✅ (AC-115) |
| UC-32, BR-85 | `ExportChangeoverService._line_performance`, `LinePerformanceFileBuilder` | AC-116 ✅; nút "Download Excel" hiện ở Line performance ✅ |
| regression: existing tests | toàn bộ `backend/features/sewing_productivity/tests/` | `scripts/check.py` -> ALL CHECKS PASSED (477 passed) ✅; `scripts/doctor.py` -> APP IS HEALTHY ✅ |

## Sửa 2026-11-13 (người dùng yêu cầu)
- "Download Excel" của Line performance: một file `Line performance - <dd.mm> to <dd.mm>.xlsx`, 4 sheet `Fac Vinh Long`,
  `Fac 2`, `Fac 3`, `Fac 5` (xưởng không có dữ liệu ghi "No data in this period."). Code:
  `ExportChangeoverService._line_performance`, `LinePerformanceFileBuilder`. Kiểm tra: AC-116 (sửa) ✅,
  `scripts/check.py` -> ALL CHECKS PASSED (477 passed) ✅, `scripts/doctor.py` -> APP IS HEALTHY ✅.

## Fix log
