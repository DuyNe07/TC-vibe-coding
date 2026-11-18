# Discovery: Period Report (Screen 4) - làm biểu đồ đơn giản, dễ nhìn hơn

Ngày: 2026-11-08. Người yêu cầu: thynguyen-lab. Hướng đã chọn: **phương án A** (chỉ thay đổi trong ứng dụng
Sewing Performance, dùng các thành phần có sẵn; không đổi phần biểu đồ dùng chung của khung sườn, không dùng 3D).
Bước tiếp theo: Prompt 5 (`docs/prompt/05-extend-feature.md`) cho `sewing_productivity`.

## 1. Hiện trạng trước khi làm lại (ghi lại ngày 2026-11-08, bộ lọc mặc định)

Bộ lọc: By week, 01/01/2026 - 05/11/2026, 4 xưởng (Fac Vinh Long, Fac 2, Fac 3, Fac 5).
Dữ liệu mới nhất 05/11/2026, lần tải file cuối 08/11/2026 00:23. 44 kỳ (tuần), không có tuần 14.02-20.02 (Tết).

Trang xếp dọc 8 khối, mỗi khối: biểu đồ đường bên trái (3/5 bề ngang, cao 360px), bảng số bên phải (2/5).

| # | Khối | Biểu đồ | Khoảng giá trị theo xưởng (tuần) |
|---|---|---|---|
| 1 | MO 8h (USD) | 4 đường, 1 trục chung | Vinh Long 26-34; Fac 2/3/5 khoảng 36-44 |
| 2 | %Efficiency (with ratio) | 4 đường | 80-114 % |
| 3 | Direct worker (people per day) | 4 đường | Vinh Long 629-743; Fac 2/3/5 khoảng 299-393 |
| 4 | Output (pcs) | 4 đường | Vinh Long 25.097-186.152; Fac 2/3/5 12.195-96.181 |
| 5 | Revenue (USD) | 4 đường | Vinh Long 23.052-161.449; Fac 2/3/5 17.570-120.089 |
| 6 | Avg CM price (USD/pc) | 4 đường | 0,79-2,64 |
| 7 | Avg SMV (min) | 4 đường | 8,63-24,23 |
| 8 | Avg working hours | 4 đường | 8,0-10,0 |

Chung cho cả 8 biểu đồ: màu cố định (Vinh Long xanh đậm, Fac 2 cam, Fac 3 xanh da trời, Fac 5 tím), chú thích
ở trên, trục X chỉ ghi tháng, không có chấm trên đường, không ghi số (phải rê chuột), HCM và Total chỉ có trong bảng,
dòng chú thích "Each point sits at the first day of its period.".

## 2. Vì sao khó nhìn (kiểm tra trên màn hình thật)

1. **Một trục cho 4 xưởng khác cỡ:** Vinh Long lớn gấp khoảng 2 lần (Output, Revenue, Direct worker) hoặc thấp hơn hẳn
   (MO 8h), nên 3 đường còn lại bị ép thành một bó, khó tách.
2. **Đường đan chéo nhau:** Avg CM price, Avg SMV, %Efficiency dao động mạnh từng tuần; 4 đường cắt nhau liên tục.
3. **Kỳ thiếu ngày làm nhiễu:** tuần đầu 01.01-02.01 chỉ 2 ngày nên Output / Revenue rơi xuống đáy rồi vọt lên; tuần
   25.04 và 29.08 (nghỉ lễ) cũng tụt sâu; tuần cuối 31.10-05.11 chưa đủ tuần.
4. **Không thấy số:** muốn biết giá trị phải rê chuột hoặc dò bảng.
5. **Bảng bị cắt:** bảng chỉ rộng 2/5 nên các cột Fac 3, Fac 5, HCM, Total bị che, phải kéo ngang.
6. **Trang rất dài:** 8 khối cao khoảng 600px, phải cuộn khoảng 4.800px.

## 3. Đề xuất (phương án A)

- Mỗi chỉ số một tab (chỉ tab đang mở mới tính và vẽ): trang ngắn lại.
- Trong mỗi tab:
  - hàng 4 thẻ số (mỗi xưởng một thẻ): giá trị kỳ mới nhất, mũi tên tăng/giảm so với kỳ trước, biểu đồ mini các kỳ;
  - 4 biểu đồ nhỏ, mỗi xưởng một biểu đồ với thang riêng (hết bị ép, hết đan chéo);
  - bảng số đầy đủ (Period, 4 xưởng, HCM, Total, chấm đỏ) trong khối gấp "Xem bảng số", trải hết bề ngang.

## 4. Câu hỏi nghiệp vụ - người dùng đã trả lời (2026-11-08)

1. **Tăng là tốt hay xấu (màu mũi tên):** MO 8h, %Efficiency, Output: tăng = tốt (xanh), giảm = xấu (đỏ).
   Avg SMV chỉ thể hiện độ khó của sản phẩm: chỉ hiện mũi tên, không tô màu.
   Chưa được nói: Revenue, Direct worker, Avg CM price, Avg working hours -> mặc định an toàn: chỉ hiện mũi tên, không
   tô màu; hỏi lại ở Prompt 5.
2. **Kỳ mới nhất chưa đủ ngày:** thẻ số lấy số tích lũy từ đầu kỳ đến ngày có dữ liệu mới nhất của kỳ đó.
   Tôi hiểu là: so sánh với kỳ trước tính trên cùng số ngày đầu kỳ (ví dụ 6 ngày đầu của tuần trước) để công bằng -
   cần xác nhận ở Prompt 5.
3. **Kỳ thiếu ngày có vẽ không:** có, vẫn vẽ.
4. **Loại kỳ:** có cả lựa chọn theo tuần và theo tháng (đã có sẵn cùng quý, năm); mặc định giữ By week (AC-86).
   Tôi hiểu là: không bỏ lựa chọn quý / năm - cần xác nhận ở Prompt 5.
