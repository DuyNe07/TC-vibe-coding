# Discovery - Đợt 2: giá nguyên liệu bình quân và giá báo khách (2026-11-10)

Chức năng: `yarn_costing` (Tính giá sợi). Nối tiếp phần "Đợt 2" của
[yarn_costing-sales-requests-discovery.md](yarn_costing-sales-requests-discovery.md).

Dữ liệu mẫu (thư mục `D:\Vibe Coding\Spinning\New data`):
- `GIÁ SỢI 4 THÁNG 10.xlsx` - báo cáo nhập - xuất - tồn kho xưởng S4, tháng 10/2026 (xuất từ hệ thống kế toán).
- `Giá nguyên liệu.xlsx` - Sales mô tả cách tính giá nguyên liệu bình quân tháng 11.
- `Ke hoach xo ve NM - 06.11.xlsx` - file Sales theo dõi xơ / bông sắp về nhà máy.

## 1. File kho (GIÁ SỢI 4 THÁNG 10)
- Một sheet, một dòng = một mã kế toán (cột ITT_CODE), tên hàng (VAT_TU), ĐVT, nhóm (ICA_NAME).
- Nhóm ICA_NAME: "Bông", "Xơ " (nguyên liệu); "Mua ngoài", "Sợi hòan kho" (phụ liệu: FDY, DTY, Nylon, Sorona, PE 20/2...);
  "Do cty sx" (sợi thành phẩm do công ty sản xuất, theo mã kế toán sợi, ví dụ S41602000010000000FCE).
- Cột số: SL_TON / GT_TON (tồn đầu), SL_NHAP / GT_NHAP, SL_XUAT / GT_XUAT, SL_CUOI / GT_CUOI (tồn cuối), giá trị VND.
- Sales quy ra USD/kg = GT_CUOI / SL_CUOI / tỷ giá (file đang ghi cứng 25.800). **Đính chính: tỷ giá lấy theo tỷ giá
  đã khai báo trên app**, không dùng số trong file.
- Mã kế toán có đuôi ID / IDR = hàng nội địa, đuôi IR = hàng xuất khẩu (Sales tách giá riêng).
- Hiện chỉ cần kho S4: S1 chủ yếu là xơ thí nghiệm, Sales không quan tâm (câu 7).
- Hai mục đích:
  1. Giá tồn nguyên liệu -> giá nguyên liệu bình quân khi tính giá; giá tồn sợi "Do cty sx" cùng mã kế toán -> giá
     sợi bình quân báo khách.
  2. So đơn giá xuất thực tế của nguyên liệu và phụ liệu (GT_XUAT / SL_XUAT) với bảng giá nguyên liệu bình quân ở mục 1.

## 2. Giá nguyên liệu bình quân (theo file Giá nguyên liệu)
- Giá tồn tháng này = giá tồn cuối tháng trước (đơn giá = tổng giá trị / SL, quy USD theo tỷ giá trên app).
- Bình quân = (SL tồn x giá tồn + SL sắp về x giá nhập) / (SL tồn + SL sắp về).
  Ví dụ T11: Bông Mỹ 356.255,52 kg x 1,9376 + 140.000 kg x 2,158 -> 1,9998 USD/kg.
- Cotton: chỉ phân theo xuất xứ - Australia, Brazil, USA (US). Giá cotton để tính = theo phương án pha bông, ví dụ
  "01/10 - 20/12: 31% USA + 69% Brazil" = 0,31 x 1,9998 + 0,69 x 1,9758 = 1,9832. Sales cập nhật phương án khi ngành
  thay đổi.
- Xơ (PE, viscose, modal, micro modal...): phân theo nhà cung cấp (hầu hết là chỉ định). Nội địa / xuất khẩu tách giá.
- Hồi phế: **trừ** khỏi giá bình quân (câu 1), Sales khai báo theo nhóm nguyên liệu hằng tháng (USD/kg).
  Ví dụ file: cotton -0,18; poly -0,07; modal -0,20; viscose -0,15 -> cotton 1,9832 - 0,18 = 1,8032 ("costing").
  Lưu ý: khác với "hồi phế" (tỷ lệ) đang có trong app ở phần chi phí chế biến - cần đặt tên khác để không nhầm.
- Nội địa hay xuất khẩu: Sales chọn theo từng lần tính giá (câu 2).
- Phân loại nguyên liệu (câu 8): làm một phần khai báo cho Sales - mỗi mã kế toán nguyên liệu trong file kho gán vào
  một "nhóm giá nguyên liệu" (cotton theo xuất xứ, xơ theo nhà cung cấp) hoặc "không tính" (bông phế...). Khi file kho
  mới có mã chưa khai báo thì app hiện ra để Sales khai báo thêm.
  Đề xuất ban đầu (Sales chốt trên app):
  - Cotton USA: COTTON Usa 1-5/32" Green Card. Cotton Brazil: COTTON Brazil 1-5/32" Middling.
  - Chưa rõ: COTTON USA SJV PIMA (gộp USA hay nhóm Pima/Supima riêng), XO PE 1.3Dx32MM, PSF Vietnam Recycle 1.4D,
    XO MODAL Thailand, XO MODACRYLIC Protex.
  - Không tính: COTTON Usa 1-3/16" (giá trị 0), Bông Thailand Scrap, Bông B4 xử lý, Bông gin mote xử lý.
  - Poly nguyên sinh - Indorama; Poly nguyên sinh - Hengyi; Poly tái chế - Unifi (Repreve); Poly tái chế - BHF (2 mã);
    Poly tái chế - Benma; Poly tái chế - Cocona; Modal - Lenzing; Viscose - Birla (Livaeco).
  - Phụ liệu (Mua ngoài, Sợi hoàn kho): đề xuất theo từng mã kế toán.

## 3. Hàng sắp về (câu 6)
- Một màn hình mới theo dõi nguyên liệu sắp về: Sales cập nhật tay hoặc nhập file Excel.
- File Ke hoach xo ve: sheet "Update Fiber arrival 06.11" (SUPPLIER, COMMODITY, mô tả / TYPE, Spec, Contract No., DATE,
  Quantity in kg, Unit price, Term, Value USD, COUNTRY OF ORIGIN, SHIPMENT DATE, ETA AT PORT, ETA AT WAREHOUSE,
  WAREHOUSE = MILL 1 / MILL 4, NOTE); sheet "the aver price of cotton & PE" (cotton theo tháng về: Basis, Fixation,
  Fixed price USD/kg, Logistic cost, Final price, Qty, Arrival month, Factory). Đơn giá nhập kho chưa đủ trong file,
  Sales sẽ bổ sung sau.
- Giá nhập có thể cộng chi phí logistic (ví dụ poly 1,255 + 0,025; cotton + 0,035 / 0,04).

## 4. Giá vốn và giá báo khách
- Giá vốn sợi sản xuất mới = giá NL bình quân (sau hồi phế, theo tỷ lệ thành phần) / (1 - tiêu hao sản xuất)
  + norm (chi phí sản xuất đã tính ở phần 1 của app) x hệ số.
- Hệ số: khai báo mặc định, Sales được đổi cho từng lần tính (câu 4).
- Nhóm giá nguyên liệu của từng thành phần sợi (câu 3 = a): Sales chọn mỗi lần tính, app gợi ý sẵn theo tên nhóm tiêu
  hao của thành phần (tên nhóm tiêu hao không cho biết nhà cung cấp, ví dụ "PE Recycle , Ecopet, Ciclo - MVS").
- Nếu cùng mã kế toán còn sợi tồn (nhóm "Do cty sx") thì bình quân tiếp:
  (SL sợi tồn x giá tồn + SL sản xuất mới x giá vốn mới) / tổng SL; SL sản xuất mới = số kg đơn hàng Sales nhập mỗi lần
  tính (câu 5).

## 5. Yêu cầu bổ sung (2026-11-10, lượt 2)
- Phần tính giá chọn **Thường / Thí nghiệm**. Hiểu ban đầu: chọn norm của dòng giá Thường hay dòng Thí nghiệm
  (= giá thường x hệ số thí nghiệm, đang có trên app) - xác nhận ở bước phân tích.
- Giá bán (selling price) chọn **FOB / CIF**.
- Chọn CIF thì có thêm chi phí **F&I**, mặc định 3 cent/kg (0,03 USD/kg), Sales được sửa.
- Thêm dòng chi phí **Commission** = % trên giá bán.
- **GP tính trên giá bán** (ví dụ 10%), nhập mỗi lần tính.

## 6. Đã trả lời
- Tỷ giá: sau này khai báo **theo tháng**; tính giá tháng nào thì lấy tỷ giá tháng đó.
- Sợi tồn ghép với dòng giá theo **18 ký tự đầu** của mã kế toán (như BR-82).
- **Có lưu** mỗi lần tính giá báo khách.

- Công thức giá bán (đã chốt): giá bán FOB = giá vốn / (1 - GP% - commission%); **CIF = FOB + F&I** (cộng sau cùng).
  Ví dụ: giá vốn 3,00, GP 10%, commission 2% -> FOB 3,409; CIF = 3,409 + 0,03 = 3,439 USD/kg.

## 7. Còn mở (hỏi ở bước phân tích)
- Kết quả hiển thị USD/kg (và VND/kg theo tỷ giá tháng) hay chỉ USD.
- Tỷ giá đang khai báo theo ngày hiệu lực: chuyển sang theo tháng thì các mốc cũ xử lý thế nào.
