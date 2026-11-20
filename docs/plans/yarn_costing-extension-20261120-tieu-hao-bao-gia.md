# yarn_costing - Mở rộng 2026-11-20: tiêu hao báo giá theo loại xơ, cúi CM

## Yêu cầu (người dùng, 2026-11-19 / 20)
- Sales thấy tiêu hao ở Tính giá báo khách đang cao. Họ có file theo dõi riêng: Xơ PE 1.04, Xơ khác (Modal, Viscose, Re-PE...) 1.08,
  Cotton chải thô 1.12, Cotton chải kỹ 1.36.
- Tiêu hao điền sẵn theo bảng trên, Sales sửa được, lưu theo từng lần báo giá.
- Cúi CM (sợi S1 nhận cúi từ S4): tiêu hao cộng dồn; chi phí chế biến cúi cộng thêm khi tick (mặc định không tick).
- Mã Cúi CM có trong file định mức S4 (mã 7) nhưng app loại khi nhập vì tên không có chi số → cần nhận được mã này.

## Câu hỏi đã chốt
| # | Câu hỏi | Trả lời |
|---|---|---|
| 1 | Dùng hệ số thế nào | Phần sau "1." là % tiêu hao, giữ công thức ÷ (1 − tiêu hao); Cotton chải kỹ lấy **24%** như file tính giá của ngành |
| 2 | Xếp loại xơ | Theo tên nguyên liệu (đề xuất a) |
| 3 | Filament (DTY, FDY, Spandex) | Xơ khác |
| 4 | Ai sửa mặc định | Phòng SO, trong Khai báo tháng |
| 5 | Cộng dồn cúi CM | Tiêu hao cúi CM ở S4 (22%) + hao ở S1 từ ghép trở đi |
| 6 | Chi phí cúi lấy đâu | Mã Cúi CM ở S4 (chỉ đi đến ghép DCM, không đóng gói) |
| 7 | Supima | Giữ cách cũ |

Vòng giao diện (2026-11-20): 1a, 2a, 3a; thêm: **Cúi CD làm tương tự Cúi CM** (mã S4 "CÚI CHẢI THÔ COTTON" S41700000000000410, chỉ C1
NSM 65, tiêu hao C1 7,5%; sợi S1 nhóm CD / CVCD / TCD / tên có CARDED dùng Cúi CD).

## Thay đổi
- 4.25 thêm loss_pe / loss_other / loss_carded / loss_combed (mặc định 4 / 8 / 12 / 24%).
- 4.28 thêm sliver_cost, sliver_code, sliver_vnd, sliver_usd, loss_version; 4.28.1 thêm fiber_type, default_loss.
- 4.12 count trống với mã Cúi CM.
- UC-15, UC-58, UC-62 bổ sung; BR-94 sửa; BR-117..BR-120 mới; AC-170..AC-176.

## Ảnh hưởng tới cái đang có
- Báo giá đã lưu: không tính lại (BR-97); loss_version = 1, sliver_cost = Không, fiber_type / default_loss trống.
- Khai báo tháng đã lưu: 4 ô tiêu hao = mặc định.
- Bảng giá sợi (norm) của mọi mã: không đổi. Chỉ thêm khả năng tạo mã "Cúi CM" ở S4.
- Phần Supima (BR-111): tiêu hao Supima giữ cách cũ; bông thường dùng tiêu hao của thành phần.

## Dữ liệu đã lưu
Các trường mới đều có mặc định trong mô hình (đọc bản cũ không lỗi). Không đổi tên / bỏ trường nào → không cần đổi cấu trúc dữ liệu cũ.

## Giả định
- Chi phí cúi cộng vào Norm trước khi nhân Hệ số norm.
- Tiêu hao S1 của cúi = tổng tiêu hao các công đoạn không phải chải thô của nhóm tiêu hao của sợi.
- Mã Cúi CM = bản NSM mới nhất đã có giá của mã gốc tên "CÚI CM" ở S4.

## Sau khi làm xong
Người dùng nhờ AI tạo mã "Cúi CM" trên app (đăng nhập bằng tài khoản của người dùng, họ tự đăng nhập), sau khi bản mới lên server.
Số liệu file định mức S4: NSM C1 65, SBD 180, CM 50, DCM 83; tiêu hao C1 7,5%, CM 14,5%.

## Fix log (thử trên máy 2026-11-20)
- Sợi pha S4 ghi "cotton" (không có chữ CM) bị xếp chải thô 12% dù có chạy chải kỹ → nguyên nhân: quy tắc chỉ xét tên → sửa BR-117 (3b): cotton tên chung + NSM CM > 0 = chải kỹ → kiểm tra: S4-523 hiện Cotton chải kỹ 24%, test `test_ac171_generic_cotton_follows_combing_stage`.
- Chọn sợi S1 có cúi báo "price_kind: Input should be 'Thường'..." → nguyên nhân: biến tên cúi trùng biến "Giá gia công" trong màn hình → đổi tên biến → kiểm tra: S1-895 mở được, Tính thử chạy.
- Ô tiêu hao làm tròn 0,1 (30,16% hiện 30,10%) → bước nhập 0,01.
- Mã cúi tạo trên máy (dữ liệu chung): S4-2085 CÚI CM (C1 65, SBD 180, CM 50, DCM 83) = 5.761 đ/kg; S4-2086 CÚI CHẢI THÔ COTTON (C1 65) = 2.571 đ/kg.
