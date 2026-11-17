# yarn_costing - mở rộng 2026-11-17: Sales chọn Tách / Gom khi tính giá bình quân, sửa gợi ý đuôi mã kho, dòng Cotton (phương án)

Nguồn: trao đổi với người dùng 2026-11-13..2026-11-17.
- Mã kho đuôi **IDR** là xơ đã đóng thuế, dùng cho sợi Nội địa.
- Mã kho đuôi **ID** và **IR** là xơ tạm nhập tái xuất (chưa đóng thuế), dùng cho sợi Xuất khẩu. Đuôi IR còn chờ kế toán xác nhận.
- Mã kho đuôi **I** hoặc không đuôi là Chung.
- Ví dụ thật tháng 11/2026: Pima chỉ có tồn mã IDR, nên giá Xuất khẩu tách riêng không có. Người dùng không muốn tự động mượn giá của loại hàng
  kia; người dùng muốn Sales **tự chọn** Tách hoặc Gom cho mỗi lần tính.

## 1. Thêm / đổi gì
| # | Nội dung | Mục / UC / BR / AC |
|---|---|---|
| 1 | Ô "Cách tính bình quân: Tách / Gom" ở Screen 13 cho mỗi lần tính, mặc định Tách. Gom áp dụng cho mọi thành phần của sợi, kể cả Cotton (phương án) và Supima | 4.28 `avg_mode`, UC-62, BR-114, AC-153, AC-154 |
| 2 | Ô "Cách tính bình quân" ở thẻ Giá bình quân (Screen 11) để xem bảng theo cách Tách hoặc Gom; Gom → một dòng mỗi nhóm, cột Loại hàng ghi "Gom" | UC-59, BR-114, AC-156 |
| 3 | Báo giá lưu "Cách tính bình quân"; chi tiết và file Excel báo giá thêm cột "Cách tính bình quân" sau cột Nội địa / Xuất khẩu; báo giá cũ = Tách | 4.28, 5.12, UC-63, AC-155 |
| 4 | Ô Nội địa / Xuất khẩu của báo giá giữ nguyên (ghi báo giá bán cho loại khách nào); khi Gom không dùng để lọc giá | UC-62, BR-114 |
| 5 | Gợi ý loại hàng cho mã kho mới theo đuôi: IDR → Nội địa; ID, IR → Xuất khẩu; còn lại → Chung | BR-86 (sửa), AC-157 |
| 6 | Dòng "Cotton (phương án)" hiện Giá tồn / Giá về theo phương án thay cho 0 | UC-59, BR-115, AC-158 |

## 2. Ảnh hưởng tới cái đang có
- Mặc định Tách: kết quả mọi lần tính và bảng giá bình quân y như trước (AC-159). BR-92, BR-94, BR-96, BR-99, BR-110, BR-111 giữ nguyên khi Tách.
- BR-99 (So giá xuất) không đổi: luôn so theo loại hàng của mã như trước.
- BR-86 chỉ đổi phần gợi ý cho mã **mới**; các mã đã khai báo giữ nguyên Loại hàng (BR-87 không đổi).
- Dòng Cotton (phương án): Giá BQ, Hồi phế, Giá tính không đổi; chỉ đổi 2 ô Giá tồn, Giá về (trước đây 0).

## 3. Dữ liệu đã lưu
- Trường mới `avg_mode` của 4.28 có mặc định "Tách"; các báo giá đã lưu đọc ra là Tách, không cần chuyển đổi.
- Không xoá, không đổi dòng nào đã lưu. Không thêm bảng mới.

## 4. Câu hỏi đã trả lời (2026-11-17, người dùng trả lời "ok" = dùng toàn bộ đề xuất)
1. Chọn ở màn Tính giá báo khách cho từng lần tính; thẻ Giá bình quân cũng có ô này (1a).
2. Mặc định Tách (2a).
3. Gom áp dụng cho cả lần tính, mọi thành phần (3a).
4. Giữ ô Nội địa / Xuất khẩu để ghi loại khách (4a).
5. Báo giá và file Excel có cột "Cách tính bình quân"; báo giá cũ = Tách (5a).
6. Làm luôn: gợi ý đuôi mã và dòng Cotton (phương án) (6a).
- Trước đó (2026-11-16): không tự động mượn giá của loại hàng kia khi một loại không có tồn và hàng về.

## 5. Đã làm (2026-11-17)
- Code + test AC-153..AC-158; test cũ vẫn đạt (AC-159). AC-119 sửa một dòng theo BR-86 sửa (mã đuôi ID → Xuất khẩu); bản đồ ở mục 11.
- Chạy thử giao diện trên cơ sở dữ liệu tạm, với file kho tháng 10 thật:
  - Thẻ Giá bình quân: Tách có 10 dòng Nội địa / Xuất khẩu, dòng Cotton (phương án) có Giá tồn 1,9580 (không còn 0).
  - Thẻ Giá bình quân: Gom có 5 dòng "Gom".
  - Màn Tính giá báo khách: Xuất khẩu + Tách cho sợi CM 40/1 (SUPIMA 50%) COMPACT báo "chưa có giá"; Xuất khẩu + Gom tính được và ghi "Bình quân: Gom".
- `scripts/check.py` ALL CHECKS PASSED (310 test), `scripts/migrate.py status` up to date, `scripts/doctor.py` APP IS HEALTHY.
