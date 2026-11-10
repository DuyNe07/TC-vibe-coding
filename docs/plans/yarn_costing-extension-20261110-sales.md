# yarn_costing - mở rộng 2026-11-10: yêu cầu của Sales sau buổi training (đợt 1)

Nguồn: `docs/business/_sources/yarn_costing-sales-requests-discovery.md`, file mẫu
`D:\Vibe Coding\Spinning\New data\3. Z SOI T09.2026.xlsx`. Đợt 2 (giá đề xuất có nguyên liệu + GP) làm sau khi có file
nguyên liệu - không thuộc lần này.

## 1. Thêm / đổi gì
| # | Nội dung | UC / BR / AC |
|---|---|---|
| 1 | Gợi ý sợi "Trùng" / "Gần giống" khi Sales gõ tên: app đọc chi số + xơ + tỷ lệ + từ khoá (bảng quy đổi cố định) | UC-49, BR-76, BR-77 |
| 2 | Có sợi Trùng ở đúng xưởng đang chọn: vẫn gửi được nhưng bắt buộc "Lý do gửi yêu cầu mới"; hoặc "Dùng sợi này" (xem giá, lưu tên theo khách) | UC-15 (sửa), UC-50, BR-78 |
| 3 | Ô "Khách hàng" (không bắt buộc) trên form yêu cầu | 4.12, UC-15/16/19 (sửa) |
| 4 | Tên theo khách: 1 tên chuẩn + n tên theo khách, Sales / Phòng SO thêm-sửa-xoá; hiện ở bảng giá (cột + lọc Khách hàng + file xuất) và màn so sánh | 4.20, UC-51, BR-79, UC-27/29 + 5.4 (sửa) |
| 5 | Màn mới "So sánh 2 sợi": chọn 2 dòng giá bất kỳ | Screen 9, UC-52 |
| 6 | Nhập file Z kế toán theo tháng (Sales, Phòng SO); tải lại cùng tháng thì thay (bản cũ đặt cờ xoá) | 4.21, 5.9, UC-53, BR-80, BR-81 |
| 7 | Màn mới "Đối chiếu giá kế toán": giá app tại cuối tháng (lịch sử giá) so với chi phí chế biến kế toán = (Cộng − VLC) ÷ Số lượng, từng khoản; cảnh báo Sản lượng nhỏ (< 100 kg) và Lệch nhiều (> ±10%), hai mức đổi được trên màn hình | Screen 10, UC-54, BR-82, BR-83 |
| 8 | Quyền: Sales thêm UC-50, UC-51, UC-53 | BR-47 (sửa) |

## 2. Ảnh hưởng tới cái đang có
- UC-15: thêm ô Khách hàng, lý do khi có sợi Trùng cùng xưởng. BR-06 (chặn trùng tên chính xác) giữ nguyên.
- UC-16: sửa được Khách hàng. UC-19: thêm cột Khách hàng, Lý do gửi khi đã có sợi trùng.
- UC-27 / UC-29 / 5.4: thêm cột "Tên theo khách" (cuối sheet `Bang gia`) và bộ lọc Khách hàng.
- Menu Dùng chung thêm 2 màn hình; quản trị viên cần tích quyền màn hình ở `/admin`.
- Không đổi cách tính giá, trạng thái, khoá, lịch sử giá, các file nhập hiện có.

## 3. Dữ liệu đã lưu
- Mã sợi (4.12): 2 trường mới `customer_name`, `duplicate_reason` mặc định trống - mã cũ đọc được, không cần chuyển đổi.
- Tên theo khách (4.20), giá thành kế toán (4.21, 4.21.1): bảng mới, ban đầu trống.
- Tải lại một tháng Z: bản cũ đặt cờ xoá (`is_deleted`), không xoá thật.

## 4. Câu hỏi đã trả lời (2026-11-10)
- Gợi ý: chọn sợi có sẵn để xem giá, hoặc gửi yêu cầu mới có lý do (1c). Chi số khớp tuyệt đối; thứ tự tỷ lệ: CVC cotton trước,
  CVCD cotton chải thô trước, TC/PC/TR PE trước, tên ghi rõ xơ thì theo thứ tự trong tên (2a). Trùng / Gần giống (2b).
- Gợi ý cả 2 xưởng, chỉ bắt lý do khi Trùng ở đúng xưởng đang chọn (vòng 3, 1a). Bảng quy đổi xơ đồng ý, sửa CVCD (vòng 3, 2).
- So sánh 2 sợi: mọi vai trò, cả 2 xưởng, cả dòng CK/PP (3).
- Tên theo khách: Sales + Phòng SO (8b); nhập ở form yêu cầu và ở chi tiết dòng giá (9c); tên chuẩn giữ tên cũ (10); không nhập
  bằng file (11); hiện ở bảng giá + so sánh, lọc theo khách (12); một khách + một tên chỉ thuộc 1 sợi (vòng 3, 3); cột + lọc + file xuất (vòng 3, 4).
- File Z: lưu theo tháng, chọn tháng trên dashboard (5); giá app tại cuối tháng theo lịch sử giá (vòng 3, 5a); Sales + Phòng SO tải,
  mọi người xem (vòng 3, 7a); giữ 2 cảnh báo, 100 kg và ±10% (vòng 3, 6a).
- Đợt 2 (đã ghi, chưa làm): GP Sales nhập mỗi lần tính; bình quân nguyên liệu = lô còn tồn (tồn đầu kỳ theo số kế toán + số sẽ về
  trong kỳ theo file theo dõi của Sales); chọn thời điểm so giá có nguyên liệu - chốt khi có file nguyên liệu.
