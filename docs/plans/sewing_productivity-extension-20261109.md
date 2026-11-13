# Sewing Performance - mở rộng 2026-11-09 (Prompt 5): ghi lại đầy đủ từng lần tải file

## Thêm và thay đổi
1. Mỗi lần tải đã lưu ghi thêm (BR-72): số dòng đọc được / hợp lệ / bỏ qua của từng sheet; dòng bị bỏ qua (Sheet, Dòng,
   Lý do, tối đa 1.000 dòng đầu); cảnh báo BR-08 (Loại, Ngày, Số lượng).
2. Thay đổi của lần tải (BR-73), theo sheet và xưởng: Thêm mới, Cập nhật, Ẩn đi.
3. Lần tải bị từ chối cũng được ghi (BR-74): trạng thái Rejected và đúng câu lý do; không lưu dữ liệu; không tính là
   "Last file upload". Người không có quyền bị chặn trước, không ghi.
4. Screen 7, bảng lịch sử: thêm Trạng thái, Thêm mới, Cập nhật, Ẩn đi; chọn một dòng thì hiện chi tiết bên dưới.
5. Không giữ file gốc. Chỉ UPDATER xem như trước.

## Ảnh hưởng tới phần đã có
- UC-01 sửa (ghi dòng Rejected khi từ chối), UC-02 sửa (ghi chi tiết), UC-03 sửa (trả chi tiết). Không thêm chức năng
  mới: số chức năng của app giữ nguyên.
- Dữ liệu: bảng lịch sử tải file thêm các trường mới, đều có mặc định (dòng cũ: Saved, không có chi tiết); từ ngày /
  đến ngày cho phép trống (chỉ ở dòng Rejected). Không cần chuyển dữ liệu, không xoá dòng nào.
- AC-12, AC-13 phải vẫn đúng. Dữ liệu sản lượng, mục tiêu, số thợ lưu như cũ (BR-07 không đổi).

## Câu hỏi đã trả lời (09/11/2026, "all theo đề xuất")
1a theo dõi từng lần tải + thay đổi theo xưởng/ngày; 2 lưu số theo sheet, dòng bỏ qua, cảnh báo, thêm/cập nhật/ẩn;
3a không giữ file gốc; 4a ghi lần bị từ chối; 5a xem ngay ở bảng lịch sử Data Update, chọn dòng xem chi tiết;
6a chỉ UPDATER; 7a dòng cũ giữ nguyên, hiện "-". Câu 5 là quyết định giao diện (bước hỏi giao diện đã xong).

## Truy vết (điền khi làm)
| Mục | Code | Kiểm tra |
|---|---|---|
| 4.10 trường mới | `UploadLog` (mặc định cho dòng cũ), `UploadStatus` | AC-98 ✅ |
| BR-72 | `UploadTrackingBusiness.sheet_counts`, `saved_log`, `SaveUploadService._warnings` | AC-95 ✅ |
| BR-73 | `UploadTrackingBusiness.change_counts`, `SaveUploadService._replace` | AC-94, file giống hệt không đổi gì ✅ |
| BR-74 | `rejected_log` trong `CheckUploadService` và `SaveUploadService`, `load_report_source` | AC-96, AC-97, từ chối ở bước lưu ✅ |
| Screen 7 lịch sử | `components/upload_history.py`, `pages/data_update_page.py` | page render test ✅; trình duyệt: chưa xem được (xem Fix log) |
| regression: existing tests | toàn bộ `backend/features/sewing_productivity/tests/` | `scripts/check.py` -> ALL CHECKS PASSED (467 passed) ✅; `scripts/doctor.py` -> APP IS HEALTHY ✅ |

## Fix log
- Kiểm tra trên trình duyệt (09/11/2026): tài khoản u-admin đăng nhập ở bản mới (cổng 8600) chỉ thấy ứng dụng "Tính giá sợi", không còn thấy Sewing Performance, nên chưa xem được màn hình Data Update. Mã và đăng ký app không đổi; log không có lỗi; nhiều khả năng quyền của u-admin trên cơ sở dữ liệu chung đã được người khác đổi. Không sửa quyền (việc của quản trị viên / master).
