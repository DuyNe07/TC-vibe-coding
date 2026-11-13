# Discovery - Bông Supima / Pima pha trong phương án bông khi tính giá báo khách (2026-11-13)

Chức năng: `yarn_costing`. Bổ sung cho đợt 2 (giá báo khách, UC-62, BR-92..BR-95).

## 1. Hiện trạng
- Khi tính giá báo khách, mỗi thành phần của sợi chỉ chọn được MỘT nhóm giá. Sợi "CM (SUPIMA 30%)" có một thành phần bông
  100% nên chỉ chọn được 100% Pima hoặc 100% Cotton (phương án) - đều sai.
- Khoảng 15 sợi có Supima / Pima trong tên (CM (SUPIMA 50%) COMPACT, CM (PIMA 50%), CM (SUPIMA 70%), CD SUPIMA 100%...).
- Nhóm "Cotton Pima" đã tạo (loại Xơ theo nhà cung cấp, không gộp vào phương án), giá BQ tháng 11/2026 = 3,6267 USD/kg.

## 2. Người dùng mô tả (2026-11-13)
- Pima / Supima được pha THÊM vào phương án bông: CM (SUPIMA 30%) = 30% Supima + 70% bông thường (US + Brazil theo
  phương án).
- Hiện chỉ bông là pha ở công đoạn ăn bông; các xơ khác pha ở ghép. Tương lai chưa chắc (câu c).
- Hồi phế Supima khai báo riêng 0,30 USD/kg (bông thường 0,18) (câu b) - khai báo tháng đã cho hồi phế theo từng nhóm.
- Muốn chọn được **phương án pha bông riêng cho một mã hàng** khi tính giá, thay vì luôn dùng phương án khai báo hằng tháng
  (câu a).
- Công thức (ví dụ Supima 50%), có 2 loại:
  1. Không truyền điểm Supima coin trên TG:
     0,50 × giá bông thường / (1 − tiêu hao bông thường) + 0,50 × giá Supima / (1 − tiêu hao Supima)
  2. Có truyền điểm Supima coin trên TG (cộng phí coin):
     0,50 × giá bông thường / (1 − tiêu hao bông thường) + 0,50 × (giá Supima + 0,552 × 1,05) / (1 − tiêu hao Supima)
     với 0,552 USD/kg = giá 1 kg Supima coin, 1,05 = thuế nhà thầu 5%.
- Tên sợi không cho biết có truyền điểm hay không → thêm ô Sales tick khi tính giá ("Truyền điểm Supima coin trên TG"), app
  đổi công thức theo lựa chọn.

## 3. Đã trả lời (2026-11-13)
- Tiêu hao phần Supima: **khai báo riêng** một tỷ lệ tiêu hao cho bông Supima (1b), không dùng chung tiêu hao thành phần bông.
- Giá Supima coin (0,552 USD/kg) và thuế nhà thầu (5%): **khai báo hằng tháng** cùng chỗ hồi phế, chép từ tháng trước (2a).
- Phương án pha bông riêng cho một mã: **chỉ áp cho lần tính đó**, lưu trong báo giá (3a). Mặc định = phương án khai báo tháng.
  Sợi "100% US cotton" → Sales đặt phương án USA 100% cho lần tính đó.
- Tỷ lệ Supima: app đọc từ tên ("SUPIMA n%", "PIMA n%"; "SUPIMA 100%" / "SUPIMA COTTON" = 100%), Sales sửa được; không đọc
  được thì Sales nhập (4).
- Hồi phế Supima 0,30 USD/kg: khai báo ở hồi phế theo nhóm của tháng (nhóm Cotton Pima).

## 4. Còn mở (hỏi ở bước phân tích)
- Tiêu hao Supima khai báo ở đâu, theo gì: một tỷ lệ chung hằng tháng, theo xưởng, hay theo nhóm tiêu hao / công nghệ
  (Ring / compact...); là tiêu hao lũy kế từ chải thô (như BR-94) hay chỉ phần bông.
- Ô "Truyền điểm Supima coin trên TG" mặc định bật hay tắt; hiện trong kết quả báo giá và file Excel thế nào.
