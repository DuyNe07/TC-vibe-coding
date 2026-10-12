# Ghi chép tìm hiểu nghiệp vụ: Tính giá sợi (Xưởng Sợi 1 và Sợi 4)

| Ngày | 2026-09-25 |
|---|---|
| Người trao đổi | Phòng SO (claude09@thanhcong.com.vn) |
| Trạng thái | Đã xác nhận với người dùng |

## 1. Công việc hiện tại
- Sales cần giá cho sợi mới → gửi yêu cầu qua **Zalo** cho xưởng sợi; khoảng **5-10 mã/ngày (25-50 mã/tuần)**.
- Mọi việc làm trên file Excel có macro, mỗi xưởng một file:
  `20250106 Bieu mau dinh muc soi 2025 (VIE) S4.xlsm` (28 sheet, 18 ẩn) và `... S1.xlsm` (18 sheet), thư mục
  OneDrive `SO team - Tài liệu/File tinh gia Soi/`.
- Quy trình trên file:
  1. Sales nhập tên sợi mới + loại đóng gói vào sheet `1. Input NSM`; mã tính giá = mã dòng trên + 1.
  2. Xưởng kiểm tra có chạy được không; nếu được thì nhập **năng suất máy (NSM, kg/h)** cho từng công đoạn theo
     quy trình công nghệ của nhóm sợi, và **tỷ lệ pha** nguyên liệu.
  3. Xưởng chép mã vào sheet tính `3. TH CP 1 DH`; công thức kéo NSM, định mức chi phí/phút, tiêu hao, tỷ lệ pha;
     có dòng Check các tham số phải khớp.
  4. Nếu Check = TRUE → chép giá trị chi phí/kg vào `4. Bang gia da tinh`; sheet `4. Bang gia da tinh (TN x3)` tự có
     dòng giá thí nghiệm = giá đại trà × 3. Macro dùng để tính lại hàng loạt (đưa lần lượt từng mã qua sheet tính).
  5. Kế toán nhập mã kế toán khi có đơn hàng chính thức để lấy giá về tính giá thành.
- Không có thông báo khi xưởng làm xong; Sales tự mở file xem.
- Vấn đề thấy trong file hiện tại: sheet `Norm`, `Chi phi bao tri chung - NC` lỗi `#REF!`; 98 nhóm sợi (S4) có NSM
  nhưng thiếu tiêu hao; 84 mã giá = 0; hệ số thí nghiệm không thống nhất (sheet tính dùng 4, bảng TN dùng 3); hồi
  phế lúc nhân lúc không; tên công nghệ viết không thống nhất (`Ring`/`ring`/`mvs `); mã viết lẫn `S4 - 586` và
  `S4-2019`.

## 2. Mong muốn (kết quả cuối cùng)
Một app **thay thế hoàn toàn** file Excel tính giá sợi cho cả 2 xưởng: Sales tạo yêu cầu → xưởng nhập NSM → app kiểm
tra và tính chi phí sản xuất/kg → lưu bảng giá (giá thường, giá thí nghiệm, CK/PP, ĐCNSM) → kế toán nhập mã kế toán;
có lịch sử giá, tính lại đồng loạt, xuất Excel và dashboard kiểm soát sai lệch.
Giá chỉ là **chi phí sản xuất (gia công)**, **không** gồm tiền nguyên liệu bông/xơ.

## 3. Dữ liệu vào (file mẫu đã xem: tên file, sheet, các cột)
File S4 (và S1 cùng cấu trúc, khác số liệu):
- **`Dinh muc (phut)`** - định mức chi phí/phút theo công đoạn (VND/phút): Stt, Xưởng sợi, Công đoạn, Tên công đoạn,
  Nhóm công đoạn, **Nhân công, Khấu hao, Điện, Vật tư, CPQL**, Giá thành sản xuất (= tổng), Ghi chú.
  S4 có khoảng 24 công đoạn: C1, C2, C3/C3.1/C3.2/C3.3 (ăn bông - chải thô cotton/PE/viscose), SBD, PD, PD1, PCD1,
  PCD2 (ghép sơ bộ), CM (chải kỹ), DCM, MD1-MD3 (ghép trộn), R (thô), S, S Compact (con), W (ống), V (MVS),
  Type 1/2/3 (hoàn tất, đóng gói). Ví dụ C1 = 113,55 + 421,84 + 1.533,64 + 297,58 + 172,02 = 2.538,63 đ/phút.
  S1 có danh sách khác: C1, C2, PD, PD2, MD1-MD3, R, S, W, V, Type 1…7 (7 kiểu đóng gói).
- **`1. Input NSM`** - mỗi mã sợi 1 dòng: Stt, Mã sợi (mã tính giá), Tên sợi, Nhóm sợi, Chi số, tỷ lệ pha (PE,
  Other - C3.1, Other - C3.2, Other - C3.3, Cotton), NSM (kg/h) từng công đoạn (V, W, S Compact, S, R, MD3…C1),
  Nhóm tiêu hao, Nguyên liệu, **Loại đóng gói**, Remark. S4 khoảng 2.105 mã, S1 khoảng 1.369 mã.
  Ví dụ: `S42003000010000000` "PE 30/1": PE = 1, W = 51,6; S = 9; R = 90; MD3 = 83; MD2 = 90; C2 = 45; Type 1.
- **`2. Input tieu hao`** - tiêu hao (tỷ lệ hao hụt) từng công đoạn theo **nhóm tiêu hao** (S4 khoảng 1.133 nhóm):
  - dòng **sơ cấp** (sợi 1 thành phần, dòng 5-296): Nhóm sợi, Nguyên liệu, Công nghệ, khoá "Nguyên liệu - Công nghệ"
    (ví dụ "PE Normal - Ring": W 1%, S 0,5%, R 0,2%, MD3/MD2 0,2%, C2 2,5%) - xưởng nhập tay;
  - dòng **thứ cấp** (sợi pha, từ dòng 298): chọn tối đa 5 nguyên liệu sơ cấp (ô PE, C3.1, C3.2, C3.3, Cotton) +
    tỷ lệ pha (tổng phải = 1, có cột Check). Ví dụ "TR (65/35)" = PE Normal - Ring 65% + Viscose - Ring 35%.
- **`Hoi phe`** - tỷ lệ hồi phế (S4: chải thô 1,5%, thô 1%, con 2,5%).
- **`Dong goi`** - phút/kg theo loại đóng gói (S4: Type 1 Cont 40' 0,1734; Type 2 Cont 20' 0,3154; Type 3 xe tải 5T
  0,2195).
- **`QTCN theo nhom soi`** - quy trình công nghệ theo nhóm sợi + công nghệ (ví dụ TC Ring: B2 - C1 - C2 - SBD - PD -
  LF - CM - MD1 - MD2 - MD3 - R - S - W - F).
- Tỷ giá: 25.000 VND/USD (ô trong bảng giá).
- Nhập liệu mới: trên màn hình **và** tải file Excel mẫu (có nút tải mẫu và chỗ tải file lên).

## 4. Dữ liệu ra (file/báo cáo, người nhận)
- **Bảng giá đã tính** (như `4. Bang gia da tinh`): STT, Mã tính giá, Tên sợi, Nhóm sợi, Chi số, Công nghệ
  (Ring/MVS), tỷ lệ nguyên liệu, **Nhân công, Khấu hao, Điện, Vật tư, CPQL, Tổng (VND/kg), USD/kg**, Loại đóng gói,
  Ngày tính giá, **Mã kế toán**. Gồm dòng giá thường, dòng giá thí nghiệm (× hệ số), dòng CK/PP, bản ĐCNSM.
  Người xem: Sales, xưởng, SO, kế toán.
- **Xuất Excel toàn bộ giá đã tính.** Không cần phiếu báo giá.
- **Chi tiết tính giá 1 mã**: từng công đoạn - thời gian chạy máy, tiêu hao, tiêu hao lũy kế, định mức, chi phí/kg,
  5 khoản chi phí.
- **Dashboard kiểm soát** (SO, quản lý) - xem mục 5 (QT-15).

## 5. Quy tắc và cách tính đã biết
- **QT-01 Mã tính giá**: mỗi xưởng 1 dãy, dạng `S4-2020`, `S1-1317` = số lớn nhất hiện có + 1 (đã kiểm: S4 lớn
  nhất S4-2019, S1 lớn nhất S1-1316, không trùng). Thống nhất cách viết về dạng không dấu cách. Mã tính giá **khác**
  mã kế toán.
- **QT-02 Thời gian chạy máy** (phút/kg) của một công đoạn = 60 ÷ NSM × (1 + hồi phế của công đoạn, nếu có) × tỷ lệ
  pha của nguyên liệu chạy riêng ở công đoạn đó (công đoạn trước khi ghép); NSM = 0 → công đoạn không chạy.
  Đóng gói: thời gian = phút/kg của loại đóng gói đã chọn.
- **QT-03 Chi phí/kg của công đoạn** = định mức (đ/phút) × thời gian ÷ (1 − tiêu hao lũy kế). Tiêu hao lũy kế = tổng
  tiêu hao từ công đoạn đó đến cuối quy trình, **bỏ các công đoạn thuộc nhánh nguyên liệu khác** (giữ đúng cách
  file). Tính riêng cho 5 khoản (Nhân công, Khấu hao, Điện, Vật tư, CPQL); giá = tổng các công đoạn + đóng gói.
  USD/kg = VND/kg ÷ tỷ giá. Ví dụ S4-2017 "CORE 40/1 (COTTON/FDY 30D/24F/1) (70/30) MVS" = 19.777,84 đ/kg ≈
  0,7911 USD.
- **QT-04 Nhóm sợi, nhóm tiêu hao, công nghệ**: tự nhận từ tên sợi **theo đúng cách của file** (tách chi số "xx/1";
  "MVS" trong tên → MVS, ngược lại Ring; "compact" → con compact). Tiêu hao lấy theo nhóm sợi + tỷ lệ pha +
  nguyên liệu đặc biệt (ví dụ "CD 30/1 Supima" → nhóm "CD SUPIMA").
- **QT-05 Kiểm tra khớp**: các công đoạn có NSM của sợi phải khớp các công đoạn đã khai báo tiêu hao cho nhóm; chỉ
  khi đạt mới cho ra và lưu giá. Thiếu nhóm tiêu hao → chặn tính giá, báo cần khai báo.
- **QT-06 Tiêu hao thứ cấp** = kết hợp tiêu hao sơ cấp của các nguyên liệu thành phần: công đoạn có dấu "x" (đã chạy
  chung: MVS, Ống, Con compact, Con, Thô, Ghép trộn 1, Ghép sơ bộ CD1, Ghép sơ bộ CM) → bình quân theo tỷ lệ pha;
  công đoạn còn lại → cộng thẳng (người dùng xác nhận là **cố ý**, vì sau khi ghép sợi đã trộn). Danh sách công đoạn
  có "x" riêng cho từng xưởng.
- **QT-07 Giá thí nghiệm** = giá đại trà × hệ số; hệ số hiện là **3**, sửa được. Tự tạo dòng khi lưu giá đại trà.
  Bỏ phần "loại đơn hàng" (thường/đặc biệt) của sheet tính cũ.
- **QT-08 Chiết khấu / phụ phí**: xưởng nhập % cho từng lần (có thể theo sản lượng đơn hàng); lưu thành **dòng riêng**
  trong bảng giá, mã có hậu tố **CK** hoặc **PP**; bắt buộc ghi **lý do** và **đơn hàng cụ thể**.
- **QT-09 ĐCNSM** (điều chỉnh NSM của riêng một sợi do đổi công nghệ, chất lượng nguyên liệu, sản lượng lớn): tạo bản
  mới có hậu tố (ví dụ `S4-586 (ĐCNSM2)`), bản gốc vẫn giữ giá riêng. Nhập sai thì sửa thẳng (lưu lịch sử) khi chưa
  có mã kế toán.
- **QT-10 Khoá bằng mã kế toán**: khi đã có mã kế toán thì không ai sửa được thông tin riêng của sợi đó (NSM, tỷ lệ
  pha, đóng gói, tên, CK/PP); muốn điều chỉnh phải tạo bản ĐCNSM. Nhưng giá **vẫn được tính lại** khi định mức
  chi phí/phút thay đổi (QT-11) hoặc SO sửa tiêu hao (QT-12); giá cũ lưu vào lịch sử kèm ngày hiệu lực.
- **QT-11 Tính lại đồng loạt**: khi định mức chi phí/phút thay đổi → tính lại **toàn bộ** mã, **kể cả** mã có mã kế
  toán; SO bấm nút; lưu giá trước/sau để so sánh.
- **QT-12 Sửa tiêu hao**: xưởng tự khai báo tiêu hao mới (sơ cấp và thứ cấp), không cần duyệt. Sửa tiêu hao đã có:
  - nếu **chưa có sợi nào** trong các nhóm bị ảnh hưởng có mã kế toán → xưởng được sửa, app tính lại các mã bị ảnh
    hưởng;
  - nếu **có ít nhất 1 sợi** bị ảnh hưởng đã có mã kế toán → xưởng **không** được sửa; **chỉ SO** được sửa, áp dụng
    cho **tất cả** (kể cả sợi có mã kế toán), ghi nhật ký kèm lý do.
- **QT-13 Nhập NSM - 2 cách**: (a) **tự điền** từ các sợi cùng nhóm + cùng công nghệ, xưởng chỉ sửa công đoạn khác;
  (b) **tự nhập**, app **cảnh báo** khi số nhập lệch so với các sợi cùng nhóm. Tỷ lệ pha do xưởng nhập cùng NSM.
- **QT-14 Trạng thái yêu cầu**: Chờ xưởng xem → Xưởng từ chối (ghi lý do) / Đã nhập NSM → Đã tính giá → Đã có mã
  kế toán (khoá). Sales được sửa/huỷ khi xưởng chưa xử lý.
- **QT-15 Dashboard / kiểm soát sai lệch**:
  - số sợi có đơn hàng (có mã kế toán) / số sợi đã báo giá; số yêu cầu báo giá mới; khả năng đáp ứng (tỷ lệ yêu cầu
    xưởng nhận chạy được / từ chối); chênh lệch giá trước - sau khi tính lại đồng loạt;
  - kiểm tra giá theo thứ tự **Công nghệ (Ring/MVS) → Nhóm sợi → có/không nguyên liệu đặc biệt → Chi số tăng dần**
    thì giá phải tăng dần (thay sheet `Check`);
  - NSM các sợi cùng nhóm chỉ được khác ở **Thô, Con, Ống** (Ring) và **MVS** (MVS); khác ở công đoạn khác là bất
    thường.
- **QT-16 Dữ liệu nền riêng từng xưởng**: danh sách công đoạn, định mức chi phí/phút, quy trình công nghệ, tiêu hao,
  hồi phế (xưởng chốt với SO, hầu như không đổi), loại đóng gói, hệ số thí nghiệm, tỷ giá (bảng riêng để cập nhật).
- **QT-17 Tải Excel**: có file mẫu; chọn ngày chốt để chuyển toàn bộ dữ liệu cũ (S1 + S4) vào app; báo dòng lỗi/thiếu.
  Vì cần giai đoạn chạy thử, dòng tải lên được app **tự tạo mã tiếp theo** trong dãy của xưởng.
- **QT-18 Người thao tác**: không đăng nhập thật; chọn nhóm (Sales, Xưởng S1, Xưởng S4, SO, Kế toán) → nhập mã nội bộ
  của nhóm → chọn tên (như chức năng Điều chuyển chi phí nội bộ). Phân quyền: Sales tạo/sửa yêu cầu, xem giá; Xưởng
  nhập NSM/tiêu hao, tính và lưu giá, CK/PP, ĐCNSM; SO dữ liệu nền, tính lại đồng loạt, sửa tiêu hao bị khoá,
  dashboard; Kế toán nhập mã kế toán. Mọi thay đổi ghi nhật ký (ai, lúc nào, lý do).

## 6. Quy mô, tần suất, người dùng
- Khoảng 3.400 mã sợi hiện có (S4 khoảng 2.105, S1 khoảng 1.369); khoảng 1.100 nhóm tiêu hao (S4); khoảng 11.000
  dòng chi tiết công đoạn.
- 25-50 yêu cầu mới/tuần; tính lại đồng loạt khi định mức thay đổi (thường đầu năm).
- Người dùng: Sales, Xưởng S1, Xưởng S4, Phòng SO, Kế toán - khoảng 20-30 người, máy tính công ty, nhiều người xem
  cùng lúc.

## 7. Chia thành chức năng (tên, mục tiêu 1 câu, thứ tự làm)
Một chức năng trên Trang chủ (các phần dùng chung một bộ dữ liệu): **Tính giá sợi** - thay thế hoàn toàn file Excel
tính giá sợi S1/S4, từ yêu cầu của Sales đến bảng giá cho kế toán. Các màn hình:
1. Yêu cầu tính giá (Sales)
2. Nhập NSM & tính giá (Xưởng)
3. Bảng giá đã tính (tất cả; kế toán nhập mã; kiểm tra giá bất thường; xuất Excel)
4. Tiêu hao (sơ cấp / thứ cấp; quy tắc sửa QT-12)
5. Dữ liệu nền & định mức (SO; tính lại toàn bộ)
6. Nhập dữ liệu từ Excel (file mẫu, ngày chốt, chuyển dữ liệu cũ)
7. Dashboard kiểm soát
+ Khai báo người dùng (nhóm, mã nội bộ, tên) và nhật ký thay đổi.

Thứ tự làm (người dùng đã đồng ý):
- **Đợt 1**: màn 5, 4, 6, 3 - dữ liệu nền, tiêu hao, chuyển dữ liệu cũ, bảng giá, xuất Excel, mã kế toán; đối chiếu
  app tính ra đúng như file Excel trên các mã cũ.
- **Đợt 2**: màn 1, 2 - luồng Sales → Xưởng, tính giá mã mới, ĐCNSM, CK/PP.
- **Đợt 3**: màn 7 - dashboard.

## 8. Khả năng đã kiểm tra (Excel / Word / PDF / web / lưu dữ liệu / biểu đồ) - làm được gì, không làm được gì
- **Làm được**: đọc file Excel mẫu và dữ liệu cũ, xuất Excel bảng giá, tính toán chính xác (không sai số làm tròn),
  lưu dữ liệu + trạng thái + lịch sử, bảng như Excel (xem/sửa), biểu đồ và ô số liệu cho dashboard. Quy mô khoảng
  3.400 mã nằm trong khả năng.
- **Làm được theo cách khác (đã đồng ý)**:
  - tính lại đồng loạt: SO **bấm nút**, app không tự chạy theo giờ;
  - chuyển dữ liệu cũ: tải lên từ các sheet hiện có, app báo dòng lỗi/thiếu để bổ sung;
  - thông báo cho xưởng (thay Zalo): màn hình xưởng hiện danh sách "yêu cầu mới chờ xử lý", Sales xem trạng thái;
  - đăng nhập/phân quyền: thay bằng nhóm + mã nội bộ + chọn tên (không phải bảo mật thật);
  - tỷ giá: nhập tay trong bảng tỷ giá (cách cập nhật tự động bàn sau).
- **Không cần**: Word, PDF, lấy dữ liệu từ web (bản đầu), phiếu báo giá.
- **Hướng mở rộng sau** (đã giải thích): chuyển sang cơ sở dữ liệu công ty / thêm đăng nhập thật cần nâng cấp khung
  sườn; phần quy tắc tính giá không phải viết lại, chỉ thay phần lưu dữ liệu và bước xác thực.

## 9. Chưa rõ - cần hỏi tiếp ở bước sau
- Dòng Excel tải lên mà **đã có mã cũ** (ví dụ `S4 - 586`): giữ mã cũ hay luôn tạo mã mới? (người dùng nói "mặc định
  tạo mã tiếp theo" cho giai đoạn chạy thử - cần chốt khi chuyển dữ liệu thật.)
- Khoảng 160 dòng S4 dùng thẳng mã kế toán làm mã tính giá (ví dụ `S42003000010000000`) và các dòng `(ĐCNSM)`: cách
  chuyển vào app (tách mã tính giá / mã kế toán / bản điều chỉnh).
- Cách đặt hậu tố cụ thể cho CK/PP và ĐCNSM (ví dụ `S4-2020-CK1`, `S4-2020 (ĐCNSM2)`); dòng CK/PP có tạo dòng giá thí
  nghiệm không.
- Giá mới sau tính lại có **ngày hiệu lực** thế nào; kế toán lấy giá theo ngày nào.
- Quy tắc chính xác của "tiêu hao lũy kế" theo nhánh nguyên liệu cho từng quy trình (S1 và S4), cách xử lý các chỗ
  hồi phế đang áp không đồng nhất trong file.
- Dữ liệu cũ bị thiếu (98 nhóm thiếu tiêu hao, 84 mã giá = 0): xưởng bổ sung trước hay sau khi chuyển.
- Mức lệch bao nhiêu thì cảnh báo khi nhập NSM (QT-13b), và cách xác định "sợi cùng nhóm" để tự điền (cùng nhóm +
  công nghệ + chi số gần nhất?).
- Danh sách "nguyên liệu đặc biệt" dùng cho dashboard (Supima, Recycle, Tencel, Ecovero…) lấy từ đâu.
- Cách cập nhật tỷ giá (bàn sau).

## 10. Ngoài phạm vi (đã thống nhất là không làm)
- Đăng nhập / phân quyền thật; kết nối cơ sở dữ liệu công ty (để sau, cần nâng cấp khung sườn).
- Gửi Zalo / email / thông báo tự động; chạy tự động theo giờ.
- Phiếu báo giá cho khách; tiền nguyên liệu bông/xơ trong giá.
- Loại đơn hàng thường/đặc biệt và hệ số thí nghiệm theo sản lượng của sheet tính cũ.
- Cập nhật tỷ giá tự động (bàn sau).

## Bổ sung 2026-09-28: Loại đóng gói mặc định theo xưởng
- Mỗi xưởng có thể chọn đúng một loại đóng gói làm **mặc định** (Phòng SO chọn ở Dữ liệu nền → Đóng gói).
- Màn Yêu cầu tính giá: chọn xưởng → ô Loại đóng gói tự điền loại mặc định; Sales **được đổi** sang loại khác (câu 1: a).
- Nhập dữ liệu cũ từ Excel: mã để trống loại đóng gói **không** tự gán mặc định, giữ "Chưa tính được" để xưởng tự chọn
  (câu 2: b).
- Phòng SO sẽ chọn loại mặc định cho cả S1 và S4. Chỉ trong lúc chưa chọn (ví dụ ngay sau khi nhập dữ liệu), ô để trống và Sales tự chọn.

## Bổ sung 2026-09-28: Chải thô nhiều lượt (C3 ở S4, C2 ở S1) - bỏ C3.1 / C3.2 / C3.3
- Nghiệp vụ: C3 (S4) là **một dây chuyền chải thô dùng chung**; C3.1 / C3.2 / C3.3 chỉ là **số lượt** chạy của từng nguyên
  liệu "khác" trên cùng dây chuyền (ví dụ sợi pha Viscose + PE recycle: Viscose chạy trước = C3.1, PE recycle chạy sau = C3.2).
  Tiêu hao chải thô của một nguyên liệu giống nhau ở mọi lượt; NSM chải thô tính theo từng nguyên liệu; một sợi không bao giờ
  có quá 3 nguyên liệu chạy chung một dây chuyền. Số lượt không làm đổi giá (cùng định mức, cùng hồi phế, cùng công đoạn sau).
- Hạn chế của Excel: phải có 3 cột C3.1 / C3.2 / C3.3 cho tỷ lệ, NSM và tiêu hao, nên cùng một nguyên liệu phải khai báo nhiều
  dòng tiêu hao chỉ khác ô C3 (ví dụ VISCOSE ở C3.2 và VISCOSE MVS ở C3.1; MODAL ở C3.1 và C3.2) → nhóm trùng, khó quản lý.
- Công nghệ C2 và C3 (S4) là như nhau: khi C3 bị kẹt, xưởng chạy nguyên liệu đặc biệt trên C2. → Dây chuyền chải thô mà một
  nguyên liệu đi qua được chọn theo **từng sợi**, không cố định theo nguyên liệu.
- Phương án đã đồng ý (người dùng xác nhận "Đồng ý"):
  1. Công đoạn "chải thô nhiều lượt" (tối đa 3 lượt / dây chuyền), áp dụng chung: C3 và C2 ở S4, C2 ở S1; C1 (cotton) giữ nguyên.
  2. Tiêu hao sơ cấp: mỗi nguyên liệu khai báo **một** tiêu hao chải thô, dùng được cho dây chuyền C2 hoặc C3.
  3. Nhóm sợi pha: chỉ liệt kê nguyên liệu + tỷ lệ; không xếp vào ô C3.x.
  4. Nhập NSM: mỗi nguyên liệu không phải cotton có một dòng chải thô: chọn dây chuyền (C2 / C3, mặc định theo dây chuyền nguyên
     liệu thường chạy), nhập NSM; app tự đánh lượt 1, 2, 3 trên mỗi dây chuyền theo thứ tự; định mức lấy theo dây chuyền đã chọn.
  5. Chuyển dữ liệu cũ: gộp C3.1 / C3.2 / C3.3 (và C2 cho nguyên liệu tương ứng) thành một tiêu hao chải thô; các dòng trùng chỉ
     khác ô C3 được gộp; **nếu số tiêu hao khác nhau thì lấy số thấp nhất** (người dùng chốt); NSM C3.1 / C3.2 / C3.3 → lượt
     1 / 2 / 3 của C3; giá tính ra phải giữ nguyên như hiện tại (ví dụ S4-2017 = 19.777,8356 VND/kg).
  6. S1: C2 dùng cùng khái niệm; hiện mỗi sợi 1 lượt nên giá S1 không đổi.
- Cần xác nhận ở bước tài liệu: tiêu hao chải thô của một nguyên liệu giống nhau dù chạy C2 hay C3 (suy từ "công nghệ như nhau").

## Việc còn lại khi chuyển sang thư mục / app mới (ghi ngày 2026-09-29)
- Phân hệ trên Trang chủ: KHÔNG phải "Tài chính - Kế toán"; người dùng sẽ chốt tên mới ở Prompt 1 của app mới.
- App mới chỉ có chức năng Tính giá sợi (Điều chuyển chi phí nội bộ ở lại app cũ).
- Lỗi cần sửa (Prompt 3): hộp xác nhận "Lưu đóng gói và tính lại" luôn ghi "tính lại toàn bộ giá" kể cả khi chỉ đổi loại
  mặc định / tên / trạng thái → chỉ cảnh báo tính lại khi Phút/kg của loại đang dùng thay đổi; ngược lại ghi "Giá các mã
  không thay đổi".
- Góp ý hiển thị (Prompt 3, tuỳ chọn): lý do nút "Gửi yêu cầu" bị khoá (chưa xác thực / nhóm chưa có thành viên / chưa có loại
  đóng gói chọn được) hiện rõ ngay cạnh nút.
- Sau khi nhập dữ liệu ở app mới: SO thêm thành viên cho Sales, Xưởng S1, Xưởng S4, Kế toán; đổi các mã nội bộ mặc định; chọn
  loại đóng gói mặc định cho S1 và S4; sửa các nhóm tiêu hao trùng tên còn lại trong file S4 rồi nhập lại.
- Yêu cầu khung sườn (xem `sap-xep-menu-theo-don-vi-discovery.md` mục 8b): menu gấp / mở, đăng nhập, danh sách người dùng dùng
  chung, chạy app trên máy chủ để người khác truy cập.
