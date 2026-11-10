# Discovery - yêu cầu của Sales sau buổi training (2026-11-10)

Chức năng: `yarn_costing` (Tính giá sợi). Dữ liệu mẫu: `D:\Vibe Coding\Spinning\New data\3. Z SOI T09.2026.xlsx`.

## Đợt 1 (làm trước)

### S1. Gợi ý sợi tương tự khi Sales nhập tên (form yêu cầu tính giá)
- App đọc tên: chi số + các loại xơ + tỷ lệ (+ từ khoá MVS, SIRO, COMPACT, BCI, SUPIMA, RE-PE, CORE...).
- Tên khác nhưng cùng bản chất là một: CVC 20/1 (50/50) = TC 20/1 (50/50) = Poly/cotton 20/1 (50/50) = Cotton/poly 20/1 (50/50).
- Chi số phải khớp tuyệt đối, không lệch.
- Sales làm gì khi có gợi ý (câu 1 = c): được chọn sợi có sẵn để xem giá, hoặc vẫn gửi yêu cầu mới nhưng phải ghi lý do.
- Đã thử đọc tên trên file Z: hiểu các tên dạng NHÓM chi số (tỷ lệ); tên CORE và tên tiếng Anh dài cần thêm quy tắc.
- Sợi đã có giá: so bằng thành phần + tỷ lệ đã lưu trên app (không chỉ bằng tên).
- Đã chốt (2a): CVC = cotton đứng trước; TC/PC/TR = PE đứng trước; tên ghi rõ xơ (Poly/cotton, Cotton/poly) thì
  tỷ lệ theo thứ tự trong tên.
- Đã chốt (2b): gợi ý chia 2 nhóm - "Trùng" (cùng chi số + thành phần + tỷ lệ + từ khoá) và "Gần giống" (cùng chi số
  + thành phần + tỷ lệ, khác từ khoá; ghi rõ khác ở đâu, ví dụ "khác: MVS").

### S2. Bảng so sánh 2 sợi
- Chọn 2 sợi bất kỳ (cả 2 xưởng, cả dòng CK/PP); mọi vai trò dùng được (câu 3).

### S3. Tên theo khách hàng
- Mỗi sợi: 1 tên chuẩn + n tên theo khách (khách hàng, tên khách gọi, ghi chú).
- Sales và phòng SO được thêm/sửa (câu 8 = b).
- Nhập ở form yêu cầu (chọn gợi ý thì tự lưu tên) và ở chi tiết sợi (câu 9 = c).
- Tên chuẩn: tạm giữ tên cũ; sau này sẽ có quy tắc đặt tên khi nhập yêu cầu (câu 10). Không cần nhập bằng file (câu 11).
- Hiện tên theo khách ở bảng giá và bảng so sánh; lọc bảng giá theo khách (câu 12).
- Tên khách đã lưu được dùng để gợi ý (S1).

### S4. Nhập file Z kế toán hằng tháng + dashboard
- File Z: một sheet mỗi tháng ("Z SỢI T09.26"), dòng = mã kế toán; cột SỐ LƯỢNG, VLC, NHÂN CÔNG + BẢO TRÌ, KHẤU HAO,
  ĐỘNG LỰC, VẬT TƯ..., CHI PHÍ QUẢN LÝ, CỘNG, GIÁ THÀNH ĐƠN VỊ; phần S1 kết thúc "CỘNG SỢI 1", S4 "CỘNG SỢI 4".
- Lưu theo tháng; tải lại cùng tháng thì thay (bản cũ giữ để tra); dashboard cho chọn tháng (câu 5).
- Phần 1 (đợt 1): so giá định mức trên app với chi phí chế biến kế toán = (CỘNG - VLC) / SỐ LƯỢNG
  (ví dụ CM 20/1 S4 T09.26: 19.680 đ/kg, khớp sheet "Norm S4").
- Mã sản lượng nhỏ có giá đơn vị rất cao (CORE 40/1, 29 kg, > 1,4 triệu đ/kg) -> hiện số lượng, đánh dấu.

## Đợt 2 (khi có file nguyên liệu)

### S5. Giá đề xuất = nguyên liệu + chế biến + GP
- Chi phí nguyên liệu = giá bình quân nguyên liệu / (1 - tiêu hao) + chi phí chế biến định mức; GP Sales nhập mỗi lần tính (câu 6).
- Bình quân: lô còn tồn = tồn đầu kỳ theo số kế toán + số sẽ về trong kỳ theo file theo dõi của Sales (câu 7).
- Phần 2 của dashboard: so với giá thành kế toán có nguyên liệu. Còn mở: chọn thời điểm / giá nào để so
  (một mã có nhiều lần tính, nhiều giá vốn, nhiều giá bán).
- Còn mở: GP tính trên giá vốn hay trên giá bán; đơn vị tiền nguyên liệu (VND/USD, tỷ giá).
