# Ghi chép tìm hiểu nghiệp vụ: Năng suất xưởng may

| Ngày | 2026-11-05 |
|---|---|
| Người trao đổi | Người phụ trách báo cáo năng suất may (nhóm PI - SO) |
| Trạng thái | Đang làm rõ |

> Ghi chép này đi cùng dự án lên git nên không chép số CM, doanh thu hay dòng dữ liệu thật. File gốc vẫn nằm ở chỗ cũ.

## 1. Công việc hiện tại

- Người phụ trách tự làm báo cáo tuần cho 4 xưởng bằng Excel và PivotTable, mỗi lần khoảng 20 phút.
- Dữ liệu nằm trong một file Excel trên SharePoint nội bộ, được đồng bộ về máy người phụ trách. File cần đăng nhập mới mở được.
- Mỗi ngày thêm khoảng 150 dòng vào cùng một file.
- Dữ liệu ngày cũ vẫn bị sửa khi giá CM được đồng bộ lại, hoặc khi xưởng nhập sai mã đơn, item, khách hàng.
- Mục tiêu xưởng, giờ làm, số lần đổi mã hàng trong báo cáo tuần hiện đang gõ tay.

## 2. Mong muốn (kết quả cuối cùng)

Một app cho mọi người cùng theo dõi và phân tích năng suất:

- Chọn khoảng thời gian bất kỳ rồi xem biểu đồ và báo cáo trên màn hình.
- Tải được báo cáo Excel.
- Có báo cáo tuần, báo cáo ngày, báo cáo tháng, MO 8h theo chuyền.
- Có phân tích theo khách hàng và sản phẩm.

## 3. Dữ liệu vào (file mẫu đã xem: tên file, sheet, các cột)

### File chính: `Data sewing 2026.xlsx` (khoảng 14 MB)

Đường dẫn trên máy người phụ trách: `C:\Users\DELL\THANH CONG Group\PI - SO - Tài liệu\Efficiency\Efficiency May\`

| Sheet | Nội dung | Các cột dùng |
|---|---|---|
| `Production data` (tiêu đề ở dòng 2, khoảng 32 nghìn dòng, 02/01–03/11/2026) | Sản lượng theo ngày, chuyền, đơn | `adj Date`, `Factory`, `Customer Name`, `Style`, `PO#`, `Product Name`, `Color`, `Date`, `Line`, `Target`, `Product Inline Quantiy`, `Price`, `Product Turnover`, `Revised OT`, `REVISE MO`, `SMV`, `Ngày thứ mấy làm đơn`, `Thời gian làm đơn`, `Standard output of SMV (no efficiency ratio)`, `Standard output of SMV (have efficiency ratio)`, `Revised OT 2` |
| `Target system` (chỉ có từ 03/10/2026) | Mục tiêu theo ngày và chuyền | `Line` (ví dụ `SF2 - Sewing Line 01`), `Items`, `Buyer`, `Style`, `SMV`, `CM`, `No. of Sewers`, `Daily Target (SMV)`, `Daily Target (CM)`, `Expertise`, `Date`, `PO` |
| `Worker` | Số người theo ngày | Cột ngày; tổng số người và thợ may trực tiếp (`I:L` = SF2, SF3, SF5, SFVL) |
| `Efficiency by SMV` | Tỷ lệ hiệu suất theo độ khó và ngày thứ mấy làm đơn | Nhóm SMV: ≤10, 10–15, 15–20, 20–30, >30; ngày 1–117 |
| `Daily Report Sewing` | Báo cáo ngày, có bảng số chuyền cũ và mới của Fac 1 | Xem mục 5 |
| `Report final`, `MO`, `Working Hours`, `Matching` | Báo cáo tháng, MO theo chuyền, giờ làm, tỷ lệ đúng sở trường | Dùng để đối chiếu cách tính |

Xưởng được gọi bằng nhiều tên:

| Tên trong báo cáo | Tên trong dữ liệu | Tên khác |
|---|---|---|
| Fac 1 | `SVL-Factory 2` | SFVL, XM1 (VL) – Vĩnh Long |
| Fac 2 | `SHCM-Factory 2` | SF2, XM2 – HCM |
| Fac 3 | `SHCM-Factory 3` | SF3, XM3 – HCM |
| Fac 5 | `SHCM-Factory 5` | SF5, XM5 – HCM |

### File đối chiếu

- `Data sewing 2026 - KPI CHANGEOVER.xlsx` (`D:\Thành Công\KPI Factory\Sewing Matching + Changeover\`): logic đếm đổi mã hàng theo tháng.

### Dữ liệu năm 2025 (cho đợt 3)

- `Data sewing 2025.xlsx`, sheet `data`: khoảng 39,6 nghìn dòng, 02/01–31/12/2025.
- `KPI_sewing_efficiency_2025.xlsx`: mỗi tháng một sheet, tổng 37.193 dòng.

## 4. Dữ liệu ra (file/báo cáo, người nhận)

Người nhận: mọi người đăng nhập vào app để theo dõi và phân tích.

File mẫu: `Sewing - Weekly Fac report - 24.10 to 30.10.xlsx` (`D:\Thành Công\SEWING WEEKLY MEETING\`).

| Báo cáo | Nội dung |
|---|---|
| Báo cáo tuần – `Overall` | So sánh 4 xưởng: sản lượng mục tiêu và thực tế, hiệu suất, tiền CM, MO 8h, giá CM trung bình, giờ làm, tỷ lệ đúng sở trường, số lần đổi mã hàng và số lần trên chuyền |
| Báo cáo tuần – `Fac 1`, `Fac 2`, `Fac 3`, `Fac 5` | Từng chuyền theo ngày: mục tiêu, thực tế, hiệu suất; tiền CM; MO 8h; số người và giờ làm |
| Báo cáo ngày (`Daily Report Sewing`) | MO, giờ làm, sản lượng, hiệu suất, tỷ lệ đúng sở trường, số thợ. **Bỏ phần Cutting** |
| Báo cáo tháng (`Report final`) | Theo xưởng và ngày: MO, giờ làm, MO 8h, mục tiêu theo SMV, sản lượng, hiệu suất, tiền CM, số thợ |
| MO theo chuyền (`MO`) | MO 8h của từng chuyền theo ngày |

Biểu đồ và phân tích:

- Hiệu suất theo ngày của từng xưởng (đường).
- MO 8h theo ngày của từng xưởng (đường).
- So sánh thực tế với mục tiêu giữa các xưởng (cột).
- Xếp hạng chuyền cao nhất và thấp nhất (cột).
- Tiền CM theo khách hàng hoặc theo sản phẩm (cột).
- Bảng dấu màu theo khách hàng: CM mỗi phút SMV, SMV mỗi cái, CM mỗi cái.
- Sản lượng order trung bình của xưởng và của khách hàng.

Bộ lọc: thời gian, xưởng, chuyền, khách hàng, sản phẩm.

File Excel tải về:

- Mỗi báo cáo một sheet; tiêu đề in đậm có nền màu, luôn hiện khi kéo xuống; cột tự giãn.
- Thêm cột "Đánh giá" ghi Đạt hoặc Dưới ngưỡng thay cho tô màu.
- Không giữ y bố cục sheet `Fac` của báo cáo hiện tại.

## 5. Quy tắc và cách tính đã biết

### Hiệu suất: hiện cả hai cách

| | Cách A | Cách B |
|---|---|---|
| Dùng cho | Báo cáo tuần | KPI xưởng |
| Mục tiêu | Tổng `Daily Target (SMV)` trong `Target system` | Tổng cột `Standard output of SMV (have efficiency ratio)` |
| Công thức | Sản lượng thực tế / mục tiêu | Sản lượng thực tế / mục tiêu |
| Nguồn số | Người phụ trách cung cấp qua `Target system` | **Lấy thẳng số trong file**, không tính lại |
| Trước 03/10/2026 | Để trống | Vẫn có |

Đã kiểm tra:

- Cách A khớp báo cáo tuần 24–30/10 ở cả 4 xưởng.
- Cách B tính lại từ cột gốc khớp 31.908/31.989 dòng; đây là lý do chọn lấy thẳng số trong file để luôn khớp Excel.

Công thức cột cách B trong file (để tham khảo):

- `Thời gian làm đơn` = tiền CM của dòng × giờ làm / tổng tiền CM của chuyền trong ngày.
- Mục tiêu không tỷ lệ = `Thời gian làm đơn` × số người × 60 / SMV.
- Mục tiêu có tỷ lệ = mục tiêu không tỷ lệ × tỷ lệ tra trong `Efficiency by SMV` theo nhóm SMV và ngày thứ mấy làm đơn.

### Tiền CM và MO

- Tiền CM của dòng = sản lượng × giá CM (`Price`).
- MO 8h của chuyền = tiền CM / số người × 8 / giờ làm (số người và giờ làm lấy trung bình của chuyền trong ngày). Đã khớp báo cáo trên mẫu Line 1 Fac 1.
- MO 8h của xưởng trong báo cáo tuần = tổng tiền CM / tổng số thợ của các ngày × 8 / giờ làm trung bình.
- Giá CM trung bình = tổng tiền CM / tổng sản lượng.
- Số thợ lấy từ sheet `Worker`.

### Tỷ lệ đúng sở trường

1 − (tổng mục tiêu của các dòng `Expertise` = `Mismatched Strength`) / (tổng mục tiêu), lấy từ `Target system`. Đã khớp báo cáo tuần 24–30/10.

### Mục tiêu theo xưởng

- Giá trị hiện tại: hiệu suất 95% cho Fac 1, 100% cho Fac 2, 3, 5; MO 8h là 38 cho Fac 1, 43 cho Fac 2, 3, 5.
- Chỉ người phụ trách được sửa.
- Mục tiêu có ngày hiệu lực: khi đổi, các ngày trước đó vẫn so với mức cũ.

### Ngưỡng cảnh báo

| Khu vực | Hiệu suất dưới | MO 8h dưới |
|---|---|---|
| HCM (Fac 2, 3, 5) | 90% | $40 |
| Vĩnh Long (Fac 1) | 85% | $30 |

Áp cho cả hiệu suất cách A và cách B. File báo cáo hiện dùng mốc 80%; từ nay dùng các số trên.

### Đổi mã hàng

- **Báo cáo tuần:** số do xưởng cung cấp, người phụ trách nhập tay.
- **Tổng kết KPI và khoảng thời gian bất kỳ:** app tự đếm, áp một quy tắc cho cả năm:
  1. Bỏ phần sau dấu chấm cuối của mã đơn (`...8536.1` thành `...8536`).
  2. Lấy các đơn có ngày đầu tiên làm trên chuyền nằm trong khoảng thời gian đã chọn.
  3. Trên mỗi chuyền, mỗi cặp SMV + CM chỉ tính một lần trong khoảng đó.
- Số lần trên chuyền trên ngày trong file KPI = số lần / số ngày làm việc / số chuyền.
- Kết quả đối chiếu tháng 10/2026, khớp hoàn toàn: Fac 1 = 70, Fac 2 = 68, Fac 3 = 129, Fac 5 = 87.
- Đã thống nhất: số các tháng cũ trên app có thể khác số đã báo cáo, vì tháng 1–7 trong file KPI lệch nhiều so với quy tắc này.
- **Số đề xuất thêm, đang chờ xác nhận – tính cả lần lên lại:** trên mỗi chuyền, một cặp SMV + CM được tính 1 lần mỗi khi lên chuyền mà ngày làm việc liền trước của chuyền đó không chạy cặp này. Ngày chuyền nghỉ không tính là ngày cách quãng. Hiện thành một số riêng, không thay số KPI ở trên. Thử tháng 10/2026: Fac 1 = 87, Fac 2 = 135, Fac 3 = 182, Fac 5 = 97.

### Làm sạch khi nhận file (không sửa file gốc)

- **Tên chuyền:** `LINE 1` và `Line 1` là một chuyền.
- **Số chuyền Fac 1:** dữ liệu trước 07/07/2026 được quy về tên chuyền hiện nay theo bảng dưới. Bảng lấy từ `Daily Report Sewing`; đã kiểm tra trên một số chuyền qua các đơn làm liên tục quanh ngày đổi.

| Cũ | Mới | Cũ | Mới | Cũ | Mới | Cũ | Mới | Cũ | Mới |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 30 | 8 | 24 | 15 | 17 | 22 | 3 | 29 | 31 |
| 2 | 2 | 9 | 15 | 16 | 16 | 23 | 23 | 30 | 1 |
| 3 | 25 | 10 | 12 | 17 | 28 | 24 | 10 | 31 | 4 |
| 4 | 22 | 11 | 11 | 18 | 18 | 25 | 8 | 32 | 32 |
| 5 | 26 | 12 | 7 | 19 | 19 | 26 | 9 | 33 | 33 |
| 6 | 29 | 13 | 13 | 20 | 20 | 27 | 27 | 34 | 34 |
| 7 | 21 | 14 | 14 | 21 | 5 | 28 | 6 | | |

- **Nhóm sản phẩm:** T-Shirt, Polo, Jacket, Pants, Hoodie, Dress, Swimsuit. Hiện có khoảng 183 tên sản phẩm khác nhau.
- **Tên sản phẩm trống (1.123 dòng, gần như toàn bộ ở Fac 2):** tra theo mã đơn, rồi theo style, rồi theo `Target system`. Dòng không tra được thì liệt kê để người phụ trách bổ sung.
  - Tra được 759 dòng, trong đó 94 dòng ra nhiều tên khác nhau.
  - Còn khoảng 365 dòng thuộc 63 style.
- **Khách hàng:** gộp `ELAND`, `ELAND WORLD`, `ELAND SPORT`, `ELAND RETAIL`; gộp `MIHUB`, `MI HUB`, `MI HUB LIMITED`. Hiện có khoảng 205 tên khách khác nhau.
- **Danh mục:** app có màn hình để người phụ trách tự sửa nhóm sản phẩm và nhóm khách hàng.

### Sản lượng order trung bình

Gom theo mã đơn đã bỏ phần sau dấu chấm, chỉ cộng sản lượng trong khoảng thời gian đã chọn. Hiện cả số trung bình và số ở giữa.

## 6. Quy mô, tần suất, người dùng

- **Quy mô:** khoảng 150 dòng mỗi ngày, khoảng 32 nghìn dòng tính đến 03/11/2026. Thêm năm 2025 thì khoảng 70–75 nghìn dòng.
- **Tần suất:** người phụ trách tải file lên khi có số mới, dự kiến mỗi ngày.
- **Người cập nhật:** người phụ trách tải file, sửa mục tiêu, danh mục, nhập đổi mã hàng theo tuần.
- **Người xem:** mọi người đăng nhập để xem, lọc, tải báo cáo. Hiện chưa cần giới hạn người xem theo xưởng hoặc chuyền.

## 7. Chia thành chức năng (tên, mục tiêu 1 câu, thứ tự làm)

Một app: **Năng suất xưởng may**. Mục tiêu: theo dõi và phân tích năng suất các xưởng may theo khoảng thời gian bất kỳ.

| Đợt | Nội dung | Quy mô |
|---|---|---|
| 1. Báo cáo chính | Tải file lên và báo lỗi dữ liệu; mục tiêu; danh mục sản phẩm, khách hàng, số chuyền; nhập đổi mã hàng theo tuần và tự đếm theo tháng; báo cáo tuần, ngày, tháng, MO theo chuyền; biểu đồ theo xưởng và chuyền; tải Excel | Lớn |
| 2. Phân tích khách hàng | Bảng dấu màu theo khách hàng; tiền CM theo khách hàng và sản phẩm; sản lượng order trung bình | Vừa |
| 3. Dữ liệu 2025 | Thống nhất nguồn, làm sạch, đưa vào để so sánh với 2026 | Vừa, phụ thuộc độ sạch của dữ liệu |

## 8. Khả năng đã kiểm tra (Excel / Word / PDF / web / lưu dữ liệu / biểu đồ) - làm được gì, không làm được gì

| Việc | Kết quả | Ghi chú |
|---|---|---|
| Đọc file Excel tải lên | Làm được | File khoảng 14 MB, app nhận tối đa 50 MB |
| Lưu dữ liệu trong app | Làm được | Dưới giới hạn khoảng 200 nghìn dòng mỗi bảng |
| Biểu đồ đường, cột; ô số liệu; bộ lọc | Làm được | |
| Phân quyền người sửa và người xem | Làm được | Quản trị viên cấp quyền |
| Xuất Excel nhiều sheet | Làm được | Không tô màu, không giữ y bố cục sheet `Fac` |
| Tự đọc file từ SharePoint hoặc từ máy người phụ trách | **Không làm được** | Cần đăng nhập và app không vào được máy cá nhân. Đã thống nhất dùng nút tải file lên |
| Sửa file nguồn rồi đồng bộ lên SharePoint | **Không làm** | App chỉ làm sạch dữ liệu của mình, file gốc giữ nguyên |
| Heat matrix | **Theo cách khác** | Đã thống nhất dùng bảng có dấu 🟥🟨🟩 trong ô |
| Tô màu theo ngưỡng trên màn hình | **Theo cách khác** | Dùng dấu màu cạnh con số, không tô nền ô |
| Word, PDF, lấy dữ liệu từ web | Không cần | |

## 9. Chưa rõ - cần hỏi tiếp ở bước sau

1. **Giờ làm của xưởng:** báo cáo tuần gõ tay; Fac 3 và Fac 5 khớp với số tính từ dữ liệu, Fac 1 và Fac 2 lệch nhỏ. Chốt cách tính giờ làm của xưởng để số MO 8h ổn định.
2. **Báo cáo ngày:**
   - "Target MO" và "Output target by SMV" đang gõ tay hoặc có số cộng trừ thủ công. Chốt lấy từ đâu.
   - Có cần tách Fac 1 thành 29 chuyền cũ và 3 chuyền mới như hiện tại không.
3. **Ngưỡng màu:**
   - Ngưỡng cảnh báo có đổi theo thời gian không, và có sửa cùng mục tiêu không.
   - Mức xanh, vàng, đỏ của bảng dấu màu theo khách hàng (đợt 2) chưa có.
4. **Đổi mã hàng:**
   - Cách đếm số ngày làm việc và số chuyền khi tính số lần trên chuyền trên ngày (file KPI dùng 14, 19, 15 và 29–33 chuyền).
   - Dòng cùng ngày, cùng chuyền, cùng mã đơn nhưng khác màu đã được tính một lần; cần xác nhận lại trong tài liệu nghiệp vụ.
   - Cách tính "lên lại": xác nhận ví dụ ngày 1 lên, ngày 2–3 không lên, ngày 4 lên lại là tổng 2 lần; tính theo cặp SMV + CM hay theo từng mã đơn; là số riêng hay thay số KPI.
5. **Danh mục ban đầu:**
   - Tên sản phẩm không thuộc 7 nhóm thì xếp vào đâu (ví dụ `VITRIOL`, `HAT`).
   - Danh sách khách hàng gộp đầy đủ ngoài ELAND và MIHUB (ví dụ `DXLG` và `DESTINATION XLG`, `MARK'S WORK`).
   - 94 dòng tra ra nhiều tên sản phẩm thì chọn tên nào.
6. **Dữ liệu trùng:** 21 dòng trùng ngày, xưởng, chuyền, mã đơn, màu trong 2026 – giữ nguyên hay báo lỗi.
7. **Dữ liệu 2025 (đợt 3):**
   - Factory 6 năm 2025 tính là Factory 3. SHCM-Factory 1 (đến 15/07/2025) xử lý thế nào.
   - `Data sewing 2025`: 7.447 dòng thiếu SMV, 2.694 dòng thiếu tên sản phẩm, 700 ô màu lỗi, tháng 3 chỉ có khoảng 804 nghìn cái so với khoảng 1,83 triệu trong file KPI; không có `Worker` và `Target system`.
   - `KPI_sewing_efficiency_2025`: cột xưởng và chuyền nhiều kiểu, tháng 11–12 khác bố cục, 219 dòng có ngày không thuộc tháng của sheet, hơn 8.000 dòng thiếu CM, liên kết tới 5 file khác.
   - Cần thống nhất nguồn và cách ghép. Số chuyền Fac 1 năm 2025 cũng cần quy đổi.

### Lưu ý cho bước làm app

- Mỗi lần tải lên là nguyên file. Dữ liệu trong app không bị xoá thật, nên cách cập nhật phải tránh để bảng dữ liệu tăng thêm hàng chục nghìn dòng sau mỗi lần tải.
- File phải được lưu từ Excel để có sẵn kết quả công thức, vì app lấy thẳng số cách B trong file.

## 10. Ngoài phạm vi (đã thống nhất là không làm)

- Phần Cutting.
- Tự đọc file từ SharePoint hoặc từ máy người phụ trách.
- Sửa file nguồn và đồng bộ ngược lên SharePoint.
- Tô màu và giữ y bố cục báo cáo cũ trong file Excel tải về.
- Hiệu suất cách A cho các ngày trước 03/10/2026.
- Dữ liệu 2025 trong bản đầu (làm ở đợt 3).
