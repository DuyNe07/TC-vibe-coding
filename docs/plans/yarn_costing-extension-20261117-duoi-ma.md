# yarn_costing - mở rộng 2026-11-17 (lần 2): bảng "Đuôi mã → Loại hàng" do người dùng tự khai báo

Nguồn: trao đổi với người dùng ngày 2026-11-17. Người dùng lo rằng sau này sẽ có đuôi mã mới. Họ muốn tự khai báo cách gợi ý loại hàng mà
không phải sửa code.

## 1. Thêm / đổi gì
| # | Nội dung | Mục / UC / BR / AC |
|---|---|---|
| 1 | Bảng đuôi mã (Đuôi mã, Loại hàng, Ghi chú). Có 4 dòng khởi tạo: IDR Nội địa, ID Xuất khẩu, IR Xuất khẩu, I Chung | 4.32, UC-72, BR-116, AC-160, AC-161 |
| 2 | Loại hàng gợi ý cho mã mới lấy theo bảng (so đúng đuôi); mã không đuôi và mã có đuôi lạ thì gợi ý Chung | BR-86 (sửa), AC-162 |
| 3 | Khối mã kho: thêm cột Đuôi mã và Ghi chú đuôi, kèm cảnh báo số mã có đuôi lạ | UC-57 (sửa), AC-163 |
| 4 | Xoá dòng = đặt cờ xoá | 4.32, AC-164 |

## 2. Ảnh hưởng tới cái đang có
- Khi bảng chưa sửa, gợi ý y như quy tắc hiện nay (AC-165, AC-119, AC-157).
- Sửa bảng chỉ ảnh hưởng mã **mới**. Mã đã có trong 4.23 giữ nguyên Loại hàng (BR-87 không đổi).
- Giá bình quân, báo giá và So giá xuất không đổi.

## 3. Dữ liệu đã lưu
- Thêm bảng 4.32 mới. Chưa có dòng nào thì dùng 4 dòng khởi tạo; không cần chuyển dữ liệu cũ.
- Không xoá, không đổi dòng nào đã lưu.

## 4. Câu hỏi đã trả lời (2026-11-17; người dùng trả lời "ok", tức là dùng toàn bộ đề xuất)
1. Đặt ở thẻ Khai báo, trên khối mã kho (1a).
2. Sales và Phòng SO được sửa (2a).
3. Dòng khởi tạo: IDR → Nội địa, ID → Xuất khẩu, IR → Xuất khẩu, I → Chung; mã không đuôi luôn là Chung (3a).
4. So bằng đúng, không phân biệt hoa thường (4a).
5. Đuôi lạ thì gợi ý Chung, có cột ghi chú và cảnh báo (5a).
6. Chỉ áp dụng cho mã mới, không có nút áp dụng lại (6a).
7. Xoá bằng cờ xoá; đuôi đã xoá được coi là đuôi lạ (7a).

## 5. Đã làm (2026-11-17)
- Code + test AC-160..AC-164; test cũ vẫn đạt (AC-165). Bản đồ ở mục 11.
- 4 dòng khởi tạo được tạo khi bảng chưa từng có dòng nào (lần đầu đọc), sửa / xoá như dòng thường.
- Chạy thử giao diện trên cơ sở dữ liệu tạm với file kho tháng 10 thật: thẻ Khai báo hiện bảng 4 dòng IDR / ID / IR / I, nút "Lưu bảng đuôi
  mã" → "Đã lưu bảng đuôi mã (4 dòng)."; khối mã kho có cột Đuôi mã, Ghi chú đuôi; file tháng 10 không có đuôi lạ (mã ...I đã có trong bảng).
- `scripts/check.py` ALL CHECKS PASSED (320 test), `scripts/migrate.py status` up to date, `scripts/doctor.py` APP IS HEALTHY.
