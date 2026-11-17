# Discovery - Kiểm tra chính tả, sửa tên sợi và chặn sai khi Sales nhập (2026-11-11)

Chức năng: `yarn_costing` (Tính giá sợi). Mở rộng sau đợt 2.

## 1. Hiện trạng (rà dữ liệu thật ngày 2026-11-11, 3.054 mã gốc của S1 + S4)
- Sai chính tả: COTTTON, VICOSE, RECYLE, CATINONIC, BAMBO (S1-875, S4-1384 "BAMBO 40/1 SIRO COMPACT"), MODACRY.
- Thiếu / thừa ngoặc: 5 tên, ví dụ "CVC 16/1 (", "PE 30/1 (RE-PE 50%, GIGA DULL 50% MVS LOW AIR",
  "HA 30/1 (VISCOSE/ECDP (60/40)/ACRYLIC FDY 75D/31F/1 BRIGHT)) MVS".
- App chưa đọc được thành phần (BR-76): 136 tên, ví dụ "RT 40/1 (65/35)", "TCD 30/1 (80/20)", tên CORE nhiều tầng ngoặc.
- Chữ hoa / thường lẫn lộn, ví dụ "CORE 30/1(cotton/ FDY 75D/32F/1 (sorona)) (58/21/21) MVS".
- Hiện không có cách sửa tên sợi đã tính giá; tên chỉ sửa được khi yêu cầu đang "Chờ xưởng xem" (UC-16).

## 2. Yêu cầu
### 2.1 Kiểm tra tên sợi
- Bảng liệt kê tên nghi sai + lý do + gợi ý sửa: chữ không có trong **từ điển tên chuẩn** (gợi ý chữ gần nhất, ví dụ
  COTTTON → COTTON), thiếu / thừa ngoặc, tỷ lệ không đủ 100, app không đọc được thành phần, hai tên chỉ khác hoa thường /
  khoảng trắng.
- Từ điển tên chuẩn quản lý trên app (chữ chuẩn + các cách viết sai thường gặp).

### 2.2 Sửa tên đang sai
- Sửa từng mã trên bảng kiểm tra, hoặc tải Excel danh sách tên nghi sai, điền tên đúng, tải lên sửa một lượt.
- Bắt buộc lý do, ghi nhật ký; giữ **tên cũ để tìm kiếm**; giá, mã tính giá, mã kế toán không đổi.
- Quyền (câu 1, 2): sợi đã tính giá (kể cả đã có mã kế toán) - **chỉ Phòng SO**, bắt buộc lý do; sợi chưa tính giá
  ("Chờ xưởng xem", "Chưa tính được") - Phòng SO và Sales.

### 2.3 Chặn sai khi Sales gửi yêu cầu
- Khi gõ tên: chữ lạ (không có trong từ điển) → **phải chọn chữ gợi ý hoặc ghi lý do** mới gửi được (câu 3b).
- Chặn gửi khi thiếu ngoặc, tỷ lệ không đủ 100, không có chi số.
- Vẫn gợi ý sợi Trùng / Gần giống như hiện nay (BR-77, BR-78).
- **Ô ghép tên** (câu 4a): mặc định Sales chọn Nhóm sợi, Chi số, Tỷ lệ, Từ khoá (SIRO, COMPACT, BCI, MVS, SLUB...) từ
  danh sách, app ghép tên chuẩn (ví dụ "CVC 30/1 (60/40) SIRO COMPACT BCI"); sợi lạ (CORE nhiều tầng, tên thương hiệu)
  chuyển sang gõ tay, phần gõ tay vẫn được kiểm tra như trên.

### 2.4 Viết hoa (câu 5)
- Tên sợi luôn viết hoa toàn bộ (tên mới và tên sửa).
- Đổi **một lượt** toàn bộ tên cũ sang viết hoa (câu 5a), ghi nhật ký; giá, mã, mã kế toán không đổi.

## 3. Còn mở (hỏi ở bước phân tích)
- Từ điển tên chuẩn: ai quản lý (Phòng SO / Sales); khởi tạo từ các chữ dùng nhiều trong tên hiện có hay nhập tay.
- Thứ tự từ khoá chuẩn khi ghép tên (ví dụ SIRO trước COMPACT, BCI cuối) và danh sách nhóm sợi / từ khoá ban đầu.
- Sửa tên có làm đổi nhóm tiêu hao (BR-04, tên bỏ chi số) không - ví dụ "BAMBO" → "BAMBOO" đổi nhóm tiêu hao "BAMBO SIRO
  COMPACT" → "BAMBOO SIRO COMPACT": đổi theo (cần nhóm tiêu hao mới khớp) hay giữ nhóm cũ.
- Tên đổi rồi trùng tên một sợi khác cùng xưởng (BR-06) thì xử lý thế nào.
- Viết hoa một lượt: chạy khi nào, ai chạy, có cần xem trước danh sách thay đổi không.
