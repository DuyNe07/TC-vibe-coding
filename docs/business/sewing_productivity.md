# Năng suất xưởng may

| Feature key | `sewing_productivity` (= folder name in `backend/features/` and `frontend/features/`) |
|---|---|
| Home group (Nhóm trên Trang chủ) | Sản xuất |
| Icon (Biểu tượng) | 🧵 |
| Owner (Người phụ trách) | Nhóm PI - SO |
| Status (Trạng thái) | Implemented |
| Last updated | 2026-11-05 |

> Tài liệu này mô tả đợt 1. Đợt 2 (phân tích khách hàng) và đợt 3 (dữ liệu 2025) sẽ bổ sung sau, xem mục 10.

## 1. Goal (Mục tiêu)
Báo cáo năng suất các xưởng may hiện làm tay bằng Excel và PivotTable, mỗi lần khoảng 20 phút, nhiều số phải gõ tay. App cho người phụ trách tải file dữ liệu lên, rồi mọi người đăng nhập để xem báo cáo tuần, ngày, tháng, MO theo chuyền, đổi mã hàng và biểu đồ theo khoảng thời gian bất kỳ. Kết quả mong đợi: số liệu dùng chung một cách tính, xem được ngay, tải được file Excel.

## 2. Actors (Người dùng)
| Actor | Description |
|---|---|
| Người cập nhật dữ liệu (vai trò `UPDATER`) | Tải file dữ liệu; sửa mục tiêu, ngưỡng, danh mục; nhập đổi mã hàng theo tuần; xem mọi báo cáo |
| Người xem | Xem, lọc, tải Excel các báo cáo |
| Quản trị viên | Cấp màn hình và vai trò `UPDATER` trên trang phân quyền có sẵn của app |

## 3. Glossary (Thuật ngữ)
| Term | Meaning |
|---|---|
| Fac 1 / Fac 2 / Fac 3 / Fac 5 | 4 xưởng. Fac 1 ở Vĩnh Long; Fac 2, 3, 5 ở HCM |
| Chuyền | Chuyền may trong một xưởng, viết chuẩn là `LINE <số>`, ví dụ `LINE 1` |
| SMV | Số phút chuẩn để may một cái |
| CM / giá CM | Đơn giá gia công của một cái (USD) |
| Tiền CM | Sản lượng × giá CM (USD) |
| Số người | Số người của chuyền trong ngày, từ cột `REVISE MO` |
| Số thợ | Số thợ may trực tiếp của xưởng trong ngày, từ sheet `Worker` |
| Giờ làm | Số giờ làm trong ngày, từ cột `Revised OT 2` |
| MO | Tiền CM trên một người trong ngày (USD/người) |
| MO 8h | MO quy về 8 giờ làm: MO × 8 / giờ làm |
| Mục tiêu A | Tổng `Daily Target (SMV)` trong sheet `Target system` |
| Hiệu suất A | Sản lượng / mục tiêu A; dùng cho báo cáo tuần |
| Mục tiêu B | Tổng cột `Standard output of SMV (have efficiency ratio)` trong sheet `Production data` |
| Hiệu suất B | Sản lượng / mục tiêu B; dùng cho KPI xưởng |
| Trái sở trường | Dòng có `Expertise` = `Mismatched Strength` trong `Target system`, hoặc `Match line strength` = `Trái sở trường` trong `Production data` |
| Tỷ lệ đúng sở trường | Phần mục tiêu A không thuộc dòng trái sở trường |
| Mã đơn gốc | Mã đơn đã bỏ phần số sau dấu chấm cuối: `...8536.1` thành `...8536` |
| Cặp SMV + CM | Một giá trị SMV đi cùng một giá trị giá CM |
| Số lần đổi KPI | Số lần đổi mã hàng đã trừ style lặp lại cùng SMV + CM (BR-32) |
| KPI đổi mã hàng | Số lần đổi KPI / số ngày làm việc / số chuyền (BR-35) |
| Số lần đổi gồm cả lên lại | Số riêng, tính thêm cả lần một cặp SMV + CM lên lại chuyền (BR-36); không thay KPI |
| Đổi mã hàng tuần | Số do xưởng cung cấp, người cập nhật nhập tay |
| Ngày hiệu lực | Ngày một mức mục tiêu, ngưỡng bắt đầu áp dụng |
| Chưa phân nhóm | Sản phẩm chưa thuộc nhóm nào trong danh mục |

## 4. Data (Dữ liệu)
### 4.1 Dòng sản lượng (ProductionRecord)
Mỗi dòng của sheet `Production data`. Một dòng được nhận diện bằng ngày, xưởng, chuyền gốc, mã đơn, style, màu và thứ tự xuất hiện của tổ hợp đó trong file. Tải lại file thì dòng cùng nhận diện được cập nhật, không tạo dòng mới.

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| production_date | date | Yes | Ngày sản xuất, từ `adj Date` | 2026-10-24 |
| factory | list: Fac 1/Fac 2/Fac 3/Fac 5 | Yes | Xưởng, đổi từ `Factory` theo BR-06 | Fac 2 |
| customer_name | text | Yes | Tên khách hàng trong file | ELAND WORLD |
| customer_group | text, tính ra | Yes | Nhóm khách hàng theo BR-15 | ELAND |
| style | text | Yes | Mã style, số được giữ dạng chữ | 796470 |
| po_number | text | Yes | Mã đơn trong file | XKA30-SX-EX-0826-7598.1 |
| base_po | text, tính ra | Yes | Mã đơn gốc theo BR-12 | XKA30-SX-EX-0826-7598 |
| product_name | text | No | Tên sản phẩm sau khi điền theo BR-13 | T-SHIRT |
| product_group | text, tính ra | Yes | Nhóm sản phẩm theo BR-14 | T-Shirt |
| color | text | No | Màu | NAVY |
| source_line | text | Yes | Tên chuyền trong file | Line 1 |
| line | text, tính ra | Yes | Tên chuyền chuẩn theo BR-10, BR-11 | LINE 30 |
| quantity | integer ≥ 0 | Yes | Sản lượng (cái), từ `Product Inline Quantiy` | 680 |
| cm_price | decimal > 0 | Yes | Giá CM (USD/cái), từ `Price` | 1.13 |
| cm_earning | decimal, tính ra | Yes | Tiền CM = quantity × cm_price (BR-17) | 768.40 |
| working_hours | decimal > 0 | Yes | Giờ làm, từ `Revised OT 2` | 9.5 |
| sewers | decimal > 0 | Yes | Số người, từ `REVISE MO` | 24 |
| smv | decimal > 0 | No | SMV | 10.79 |
| standard_output | decimal ≥ 0 | No | Mục tiêu B, từ `Standard output of SMV (have efficiency ratio)` | 315.14 |
| is_mismatched | yes-no | Yes | Có khi `Match line strength` = `Trái sở trường` | Không |

### 4.2 Dòng mục tiêu (TargetRecord)
Mỗi dòng có dữ liệu của sheet `Target system`.

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| target_date | date | Yes | Ngày, từ `Date` | 2026-10-24 |
| factory | list: Fac 1/Fac 2/Fac 3/Fac 5 | Yes | Xưởng, từ phần đầu của `Line` theo BR-16 | Fac 2 |
| line | text | Yes | Chuyền, từ phần cuối của `Line` theo BR-16 | LINE 1 |
| base_po | text | No | Mã đơn gốc, từ `PO` | XKA21-SX-EX-0726-6775 |
| style | text | No | Style | 2DIBDHAS-320D |
| item_name | text | No | Tên sản phẩm, từ `Items` | T-SHIRT |
| daily_target_qty | decimal ≥ 0 | Yes | Mục tiêu A (cái), từ `Daily Target (SMV)` | 750 |
| daily_target_cm | decimal ≥ 0 | No | Mục tiêu tiền CM (USD), từ `Daily Target (CM)` | 562.5 |
| is_mismatched | yes-no | Yes | Có khi `Expertise` = `Mismatched Strength` | Không |

### 4.3 Số thợ theo ngày (WorkerRecord)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| work_date | date | Yes | Ngày | 2026-10-24 |
| factory | list: Fac 1/Fac 2/Fac 3/Fac 5 | Yes | Xưởng | Fac 1 |
| direct_sewers | decimal > 0 | Yes | Số thợ may trực tiếp | 720 |

### 4.4 Mục tiêu và ngưỡng (FactoryGoal)
Duy nhất theo factory + effective_from.

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| factory | list: Fac 1/Fac 2/Fac 3/Fac 5 | Yes | Xưởng | Fac 1 |
| effective_from | date | Yes | Ngày hiệu lực | 2026-01-01 |
| efficiency_target | decimal > 0 (%) | Yes | Mục tiêu hiệu suất, áp cho cả A và B | 95 |
| mo8h_target | decimal > 0 (USD) | Yes | Mục tiêu MO 8h | 38 |
| efficiency_threshold | decimal > 0 (%) | Yes | Ngưỡng cảnh báo hiệu suất | 85 |
| mo8h_threshold | decimal > 0 (USD) | Yes | Ngưỡng cảnh báo MO 8h | 30 |
| updated_by | text | Yes | Người lưu | Nguyễn Văn A |

Giá trị ban đầu, hiệu lực từ 2026-01-01:

| Xưởng | Mục tiêu hiệu suất | Mục tiêu MO 8h | Ngưỡng hiệu suất | Ngưỡng MO 8h |
|---|---|---|---|---|
| Fac 1 | 95% | 38 | 85% | 30 |
| Fac 2 | 100% | 43 | 90% | 40 |
| Fac 3 | 100% | 43 | 90% | 40 |
| Fac 5 | 100% | 43 | 90% | 40 |

### 4.5 Đổi mã hàng tuần (WeeklyChangeover)
Duy nhất theo factory + from_date + to_date.

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| factory | list: Fac 1/Fac 2/Fac 3/Fac 5 | Yes | Xưởng | Fac 2 |
| from_date | date | Yes | Từ ngày | 2026-10-24 |
| to_date | date ≥ from_date | Yes | Đến ngày | 2026-10-30 |
| changeover_count | integer ≥ 0 | Yes | Số lần xưởng cung cấp | 17 |
| updated_by | text | Yes | Người lưu | Nguyễn Văn A |

### 4.6 Nhóm sản phẩm (ProductGroupRule)
Duy nhất theo product_name (không phân biệt hoa thường, bỏ khoảng trắng hai đầu).

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| product_name | text | Yes | Tên sản phẩm | POLO SHIRT |
| product_group | text | Yes | Nhóm sản phẩm; có thể thêm nhóm mới | Polo |

Giá trị ban đầu:

| Nhóm | Tên sản phẩm |
|---|---|
| T-Shirt | T-SHIRT, T SHIRT, T- SHIRT, TSHIRT, T.SHIRT, MTM, MEN-TO-MEN, TANK TOP, HAT, BAG |
| Polo | POLO, POLO SHIRT, HENLEY, CHEMISE, BASEBALL SHIRT, CARDIGAN |
| Jacket | JACKET, HALF ZIP UP, HALF ZIP, HZIP, FULL ZIP UP |
| Pants | PANTS, PANT, LONG PANTS, SHORT PANTS, SHORTS, LEGGING, UNDERWEAR, SKIRT |
| Hoodie | HOODIE, HOODY, PULLOVER |
| Dress | DRESS |
| Swimsuit | SWIMSUIT |

### 4.7 Nhóm khách hàng (CustomerGroupRule)
Duy nhất theo customer_name (không phân biệt hoa thường, bỏ khoảng trắng hai đầu).

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| customer_name | text | Yes | Tên khách trong file | MI HUB LIMITED |
| customer_group | text | Yes | Nhóm khách | MIHUB |

Giá trị ban đầu: `MIHUB`, `MI HUB`, `MI HUB LIMITED` thuộc nhóm MIHUB. Mọi tên bắt đầu bằng `ELAND` thuộc nhóm ELAND theo BR-15.

### 4.8 Bảng số chuyền Fac 1 (LineMappingRule)
Duy nhất theo old_line. Áp cho dữ liệu Fac 1 trước ngày 07/07/2026.

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| old_line | text | Yes | Tên chuyền cũ | LINE 1 |
| new_line | text | Yes | Tên chuyền hiện nay | LINE 30 |

Giá trị ban đầu (cũ → mới): 1→30, 2→2, 3→25, 4→22, 5→26, 6→29, 7→21, 8→24, 9→15, 10→12, 11→11, 12→7, 13→13, 14→14, 15→17, 16→16, 17→28, 18→18, 19→19, 20→20, 21→5, 22→3, 23→23, 24→10, 25→8, 26→9, 27→27, 28→6, 29→31, 30→1, 31→4, 32→32, 33→33, 34→34.

### 4.9 Tên sản phẩm theo style (StyleProductRule)
Duy nhất theo style. Người cập nhật bổ sung cho các style chưa tra được tên.

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| style | text | Yes | Style | WT62I2OC |
| product_name | text | Yes | Tên sản phẩm | T-SHIRT |

### 4.10 Lịch sử tải file (UploadLog)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| uploaded_at | datetime | Yes | Thời điểm lưu | 2026-11-05 08:30 |
| uploaded_by | text | Yes | Người tải | Nguyễn Văn A |
| file_name | text | Yes | Tên file | Data sewing 2026.xlsx |
| from_date | date | Yes | Ngày đầu trong file | 2026-01-02 |
| to_date | date | Yes | Ngày cuối trong file | 2026-11-04 |
| saved_rows | integer ≥ 0 | Yes | Số dòng sản lượng đã lưu | 32050 |
| skipped_rows | integer ≥ 0 | Yes | Số dòng bị bỏ qua | 0 |

## 5. Input / output files (File nhập / xuất)
### 5.1 File dữ liệu (in)
- **Định dạng:** `.xlsx`, tối đa 50 MB, tối đa 200.000 dòng mỗi sheet. Ví dụ: `Data sewing 2026.xlsx`.
- **Đối chiếu tiêu đề:** không phân biệt hoa thường, dấu và khoảng trắng thừa. Các sheet và cột khác được bỏ qua.
- **File phải được lưu từ Excel** để có sẵn kết quả công thức.
- **File gốc không bị thay đổi.**

| Sheet | Dòng tiêu đề | Cột bắt buộc | Cột không bắt buộc |
|---|---|---|---|
| `Production data` | Dòng 2 | `adj Date`, `Factory` (cột đầu tiên có tên này), `Customer Name`, `Style`, `PO#`, `Line`, `Product Inline Quantiy` (chấp nhận thêm `Product Inline Quantity`), `Price`, `REVISE MO`, `Revised OT 2` | `Product Name`, `Color`, `SMV`, `Standard output of SMV (have efficiency ratio)`, `Match line strength` |
| `Target system` | Dòng 1 | `Line`, `Daily Target (SMV)`, `Date` | `Items`, `Style`, `Daily Target (CM)`, `Expertise`, `PO` |
| `Worker` | Dòng 2 | Cột C (ngày, không có tiêu đề); cột đầu tiên có tiêu đề `SF2`, `SF3`, `SF5`, `SFVL` | |

Ví dụ dòng `Production data`: `2026-10-03 | SHCM-Factory 2 | MARK'S WORK | 2DIBDHAS-320D | XKA21-SX-EX-0726-6775.1 | LINE 1 | 700 | 0.75 | 24 | 9`.

Khi file sai: xem BR-01 đến BR-06. Dữ liệu đã lưu giữ nguyên khi file bị từ chối.

### 5.2 File Excel xuất (out)
Định dạng chung theo BR-49.

| File | Direction | Format | Sheets và cột |
|---|---|---|---|
| `bao-cao-tuan_<từ ngày>_<đến ngày>.xlsx` | out | .xlsx | Sheet `Tong quan`: Chỉ số, Fac 1, Fac 2, Fac 3, Fac 5 (các chỉ số ở Screen 1, thêm dòng Đánh giá hiệu suất A, Đánh giá hiệu suất B, Đánh giá MO 8h). Sheet `Fac 1`, `Fac 2`, `Fac 3`, `Fac 5`: Chuyền, Ngày, Mục tiêu A, Sản lượng, Hiệu suất A (%), Mục tiêu B, Hiệu suất B (%), Tiền CM, Số người, Giờ làm, MO 8h, Đánh giá hiệu suất A, Đánh giá hiệu suất B, Đánh giá MO 8h |
| `bao-cao-ngay_<ngày>.xlsx` | out | .xlsx | Sheet `Xuong`: Chỉ số, Fac 1, Fac 2, Fac 3, Fac 5 (các chỉ số ở Screen 3, thêm dòng Đánh giá hiệu suất A, Đánh giá hiệu suất B, Đánh giá MO 8h). Sheet `Chuyen`: Xưởng, Chuyền, Sản lượng, Tiền CM, Giờ làm, Số người, MO, MO 8h, Sản lượng trái sở trường, Đánh giá MO 8h |
| `bao-cao-thang_<từ ngày>_<đến ngày>.xlsx` | out | .xlsx | Mỗi xưởng một sheet: Ngày, MO, Giờ làm, MO 8h, Mục tiêu B, Sản lượng, Hiệu suất B (%), Tiền CM, Số thợ, Đánh giá hiệu suất B, Đánh giá MO 8h; dòng cuối là Tổng |
| `mo-theo-chuyen_<xưởng>_<từ ngày>_<đến ngày>.xlsx` | out | .xlsx | Sheet `MO 8h`, `Tien CM`, `Gio lam`, `So nguoi`, `Hieu suat B`: Chuyền, các cột ngày, Cả kỳ; dòng cuối là Tổng |
| `doi-ma-hang_<từ ngày>_<đến ngày>.xlsx` | out | .xlsx | Sheet `Theo xuong`, `Theo thang`, `Theo chuyen`, `Chi tiet` theo các bảng ở Screen 6 |

## 6. Use cases (Nghiệp vụ) - each UC becomes ONE controller method + ONE service
### UC-01: Kiểm tra file dữ liệu
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Chọn file ở Screen 7 rồi bấm "Kiểm tra file"
- **Preconditions:** Có vai trò `UPDATER`
- **Input:** File Excel
- **Main flow:**
  1. Kiểm tra định dạng, dung lượng, sheet, cột (BR-01 đến BR-04).
  2. Đọc 3 sheet, kiểm tra từng dòng (BR-05, BR-06, BR-16).
  3. Làm sạch dữ liệu (BR-10 đến BR-15).
  4. Tổng hợp cảnh báo (BR-08). Chưa lưu gì.
- **Output:** Số dòng đọc được, hợp lệ, bị bỏ qua; ngày đầu, ngày cuối; danh sách dòng bị bỏ qua và lý do; danh sách cảnh báo; so sánh số dòng với dữ liệu đang lưu trong cùng khoảng ngày.
- **Errors / alternative flows:** File sai thì hiện đúng thông báo của BR-01 đến BR-04, không có nút Lưu.
- **Rules applied:** BR-01, BR-02, BR-03, BR-04, BR-05, BR-06, BR-08, BR-09, BR-10, BR-11, BR-12, BR-13, BR-14, BR-15, BR-16

### UC-02: Lưu dữ liệu từ file
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Bấm "Lưu dữ liệu" sau khi kiểm tra
- **Preconditions:** File đã qua UC-01 và không bị từ chối
- **Input:** File đã kiểm tra
- **Main flow:**
  1. Kiểm tra lại như UC-01.
  2. Thay dữ liệu theo khoảng ngày của từng sheet (BR-07).
  3. Ghi lịch sử tải file.
- **Output:** Thông báo "Đã lưu <số> dòng, dữ liệu đến ngày <ngày>." và bản ghi lịch sử mới.
- **Errors / alternative flows:** Lỗi như UC-01. Không đủ quyền thì hiện thông báo BR-09.
- **Rules applied:** BR-01, BR-02, BR-03, BR-04, BR-05, BR-06, BR-07, BR-09, BR-10, BR-11, BR-12, BR-13, BR-14, BR-15, BR-16

### UC-03: Xem lịch sử tải file
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Mở Screen 7
- **Input:** Không
- **Main flow:**
  1. Lấy lịch sử, mới nhất lên đầu.
- **Output:** Danh sách lịch sử tải file.
- **Errors / alternative flows:** Chưa có lịch sử thì hiện "Chưa có lần tải file nào."
- **Rules applied:** BR-09

### UC-04: Xem tổng quan xưởng
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở Screen 1 hoặc đổi bộ lọc
- **Input:** Từ ngày, đến ngày, xưởng, nhóm khách hàng, nhóm sản phẩm
- **Main flow:**
  1. Lấy dữ liệu theo bộ lọc (BR-29, BR-30).
  2. Tính các chỉ số cho từng xưởng (BR-17 đến BR-28, BR-38, BR-41).
- **Output:** Bảng chỉ số theo xưởng ở Screen 1, ghi chú nếu cách A chỉ tính từ một ngày nhất định.
- **Errors / alternative flows:** Khoảng ngày sai thì hiện thông báo BR-30. Không có dữ liệu thì hiện "Chưa có dữ liệu trong khoảng thời gian này."
- **Rules applied:** BR-17, BR-18, BR-19, BR-20, BR-23, BR-24, BR-25, BR-26, BR-27, BR-28, BR-29, BR-30, BR-38, BR-41, BR-50

### UC-05: Xem biểu đồ
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở Screen 1 hoặc đổi bộ lọc, đổi chỉ số xếp hạng
- **Input:** Bộ lọc của UC-04; chỉ số xếp hạng (Hiệu suất B/Hiệu suất A/MO 8h)
- **Main flow:**
  1. Tính dữ liệu từng biểu đồ (BR-18, BR-19, BR-22, BR-23, BR-44).
- **Output:** Hiệu suất A theo ngày của từng xưởng; hiệu suất B theo ngày của từng xưởng; MO 8h theo ngày của từng xưởng; sản lượng so với mục tiêu A giữa các xưởng; 10 chuyền cao nhất và 10 chuyền thấp nhất.
- **Errors / alternative flows:** Khi lọc khách hàng hoặc sản phẩm, biểu đồ hiệu suất A, MO 8h và mục tiêu A hiện "Không áp dụng khi lọc theo khách hàng hoặc sản phẩm." Không có dữ liệu thì hiện "Chưa có dữ liệu trong khoảng thời gian này."
- **Rules applied:** BR-18, BR-19, BR-22, BR-23, BR-29, BR-30, BR-44

### UC-06: Xem chi tiết chuyền
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở Screen 2 hoặc đổi bộ lọc
- **Input:** Từ ngày, đến ngày, xưởng, chuyền, nhóm khách hàng, nhóm sản phẩm
- **Main flow:**
  1. Tính từng chuyền theo từng ngày và cả kỳ (BR-17 đến BR-22, BR-27, BR-28).
  2. Tính dòng Tổng của xưởng.
- **Output:** Bảng chuyền theo ngày, dòng Cả kỳ của từng chuyền, dòng Tổng xưởng; số thợ và giờ làm của xưởng theo ngày.
- **Errors / alternative flows:** Như UC-04.
- **Rules applied:** BR-17, BR-18, BR-19, BR-20, BR-21, BR-22, BR-23, BR-26, BR-27, BR-28, BR-29, BR-30, BR-50

### UC-07: Xem báo cáo ngày
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở Screen 3 hoặc đổi ngày, đổi xưởng
- **Input:** Ngày; xưởng cho bảng chuyền
- **Main flow:**
  1. Tính chỉ số theo xưởng trong ngày (BR-17 đến BR-20, BR-23, BR-25, BR-42).
  2. Tính bảng chuyền của xưởng đã chọn (BR-21, BR-22, BR-43).
- **Output:** Bảng chỉ số theo xưởng và bảng chuyền ở Screen 3.
- **Errors / alternative flows:** Ngày không có dữ liệu thì hiện "Chưa có dữ liệu của ngày này."
- **Rules applied:** BR-17, BR-18, BR-19, BR-20, BR-21, BR-22, BR-23, BR-25, BR-26, BR-27, BR-28, BR-42, BR-43, BR-50

### UC-08: Xem báo cáo tháng
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở Screen 4 hoặc đổi bộ lọc
- **Input:** Từ ngày, đến ngày, xưởng
- **Main flow:**
  1. Tính từng xưởng theo ngày (BR-17, BR-19, BR-20, BR-23).
  2. Tính dòng Tổng (BR-48).
- **Output:** Bảng theo ngày và dòng Tổng của từng xưởng.
- **Errors / alternative flows:** Như UC-04.
- **Rules applied:** BR-17, BR-19, BR-20, BR-23, BR-26, BR-28, BR-30, BR-48, BR-50

### UC-09: Xem MO theo chuyền
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở Screen 5 hoặc đổi bộ lọc
- **Input:** Từ ngày, đến ngày, một xưởng, chuyền
- **Main flow:**
  1. Tính MO 8h, tiền CM, giờ làm, số người, hiệu suất B theo chuyền và ngày (BR-17, BR-19, BR-20, BR-21, BR-22).
  2. Tính cột Cả kỳ và dòng Tổng (BR-48).
- **Output:** 5 bảng chuyền theo ngày ở Screen 5.
- **Errors / alternative flows:** Như UC-04.
- **Rules applied:** BR-17, BR-19, BR-20, BR-21, BR-22, BR-26, BR-28, BR-30, BR-48, BR-50

### UC-10: Xem đổi mã hàng
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở Screen 6 hoặc đổi bộ lọc
- **Input:** Từ ngày, đến ngày, xưởng, chuyền
- **Main flow:**
  1. Đếm số lần đổi KPI và các mẫu số trong khoảng đã chọn (BR-32 đến BR-35, BR-37).
  2. Đếm số lần đổi gồm cả lên lại (BR-36).
  3. Tính riêng từng tháng trong khoảng, từng chuyền và danh sách chi tiết.
- **Output:** Các bảng ở Screen 6.
- **Errors / alternative flows:** Như UC-04.
- **Rules applied:** BR-12, BR-30, BR-32, BR-33, BR-34, BR-35, BR-36, BR-37, BR-38, BR-50

### UC-11: Tải Excel báo cáo tuần
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Bấm "Tải Excel báo cáo tuần" ở Screen 1 hoặc Screen 2
- **Input:** Bộ lọc đang chọn của màn hình
- **Main flow:**
  1. Tính như UC-04 và UC-06.
  2. Tạo file theo mục 5.2.
- **Output:** File `bao-cao-tuan_<từ ngày>_<đến ngày>.xlsx`.
- **Errors / alternative flows:** Khoảng ngày sai thì hiện thông báo BR-30.
- **Rules applied:** BR-28, BR-29, BR-30, BR-49, BR-50

### UC-12: Tải Excel báo cáo ngày
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Bấm "Tải Excel" ở Screen 3
- **Input:** Ngày
- **Main flow:**
  1. Tính như UC-07 cho cả 4 xưởng.
  2. Tạo file theo mục 5.2.
- **Output:** File `bao-cao-ngay_<ngày>.xlsx`.
- **Errors / alternative flows:** Không có.
- **Rules applied:** BR-28, BR-49, BR-50

### UC-13: Tải Excel báo cáo tháng
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Bấm "Tải Excel" ở Screen 4
- **Input:** Bộ lọc của UC-08
- **Main flow:**
  1. Tính như UC-08.
  2. Tạo file theo mục 5.2.
- **Output:** File `bao-cao-thang_<từ ngày>_<đến ngày>.xlsx`.
- **Errors / alternative flows:** Khoảng ngày sai thì hiện thông báo BR-30.
- **Rules applied:** BR-28, BR-30, BR-49, BR-50

### UC-14: Tải Excel MO theo chuyền
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Bấm "Tải Excel" ở Screen 5
- **Input:** Bộ lọc của UC-09
- **Main flow:**
  1. Tính như UC-09.
  2. Tạo file theo mục 5.2.
- **Output:** File `mo-theo-chuyen_<xưởng>_<từ ngày>_<đến ngày>.xlsx`.
- **Errors / alternative flows:** Khoảng ngày sai thì hiện thông báo BR-30.
- **Rules applied:** BR-30, BR-49, BR-50

### UC-15: Tải Excel đổi mã hàng
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Bấm "Tải Excel" ở Screen 6
- **Input:** Bộ lọc của UC-10
- **Main flow:**
  1. Tính như UC-10.
  2. Tạo file theo mục 5.2.
- **Output:** File `doi-ma-hang_<từ ngày>_<đến ngày>.xlsx`.
- **Errors / alternative flows:** Khoảng ngày sai thì hiện thông báo BR-30.
- **Rules applied:** BR-30, BR-49, BR-50

### UC-16: Xem mục tiêu và ngưỡng
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Mở Screen 8
- **Input:** Không
- **Main flow:**
  1. Lấy mọi mức đã lưu, chỉ ra mức đang áp dụng hôm nay của từng xưởng (BR-26).
- **Output:** Bảng mức đang áp dụng và bảng lịch sử.
- **Errors / alternative flows:** Không có.
- **Rules applied:** BR-09, BR-26

### UC-17: Lưu mục tiêu và ngưỡng
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Bấm "Lưu mức mới" ở Screen 8
- **Input:** Xưởng, ngày hiệu lực, mục tiêu hiệu suất, mục tiêu MO 8h, ngưỡng hiệu suất, ngưỡng MO 8h
- **Main flow:**
  1. Kiểm tra dữ liệu (BR-45).
  2. Lưu mức mới; trùng xưởng và ngày hiệu lực thì thay mức cũ (BR-46).
- **Output:** Thông báo "Đã lưu mục tiêu của <xưởng>, hiệu lực từ <ngày>." Báo cáo tính lại theo mức mới.
- **Errors / alternative flows:** Dữ liệu sai thì hiện thông báo BR-45.
- **Rules applied:** BR-09, BR-45, BR-46

### UC-18: Xem đổi mã hàng tuần đã nhập
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Mở Screen 7
- **Input:** Không
- **Main flow:**
  1. Lấy các số đã nhập, mới nhất lên đầu.
- **Output:** Danh sách xưởng, từ ngày, đến ngày, số lần, người lưu.
- **Errors / alternative flows:** Chưa có thì hiện "Chưa nhập số đổi mã hàng tuần nào."
- **Rules applied:** BR-09

### UC-19: Lưu đổi mã hàng tuần
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Bấm "Lưu số đổi mã hàng" ở Screen 7
- **Input:** Từ ngày, đến ngày, số lần của từng xưởng (để trống là không lưu xưởng đó)
- **Main flow:**
  1. Kiểm tra dữ liệu (BR-39).
  2. Lưu; trùng xưởng và khoảng ngày thì thay số cũ (BR-40).
- **Output:** Thông báo "Đã lưu số đổi mã hàng từ <ngày> đến <ngày>."
- **Errors / alternative flows:** Dữ liệu sai thì hiện thông báo BR-39.
- **Rules applied:** BR-09, BR-39, BR-40

### UC-20: Xoá số đổi mã hàng tuần
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Chọn một dòng rồi bấm "Xoá dòng đã chọn" ở Screen 7
- **Input:** Dòng đã chọn
- **Main flow:**
  1. Xoá dòng khỏi danh sách.
- **Output:** Thông báo "Đã xoá." Báo cáo tuần hiện "-" cho khoảng đó.
- **Errors / alternative flows:** Không có.
- **Rules applied:** BR-09

### UC-21: Xem danh mục
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Mở Screen 9
- **Input:** Không
- **Main flow:**
  1. Lấy 4 danh mục.
  2. Lấy danh sách tên sản phẩm chưa phân nhóm và style chưa có tên sản phẩm, kèm số dòng.
- **Output:** Các bảng ở Screen 9.
- **Errors / alternative flows:** Không có.
- **Rules applied:** BR-09, BR-13, BR-14, BR-15

### UC-22: Lưu nhóm sản phẩm
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Bấm "Lưu nhóm sản phẩm" ở Screen 9
- **Input:** Danh sách tên sản phẩm và nhóm
- **Main flow:**
  1. Kiểm tra dữ liệu (BR-47).
  2. Lưu; áp dụng ngay cho toàn bộ dữ liệu.
- **Output:** Thông báo "Đã lưu nhóm sản phẩm."
- **Errors / alternative flows:** Dữ liệu sai thì hiện thông báo BR-47.
- **Rules applied:** BR-09, BR-14, BR-47

### UC-23: Lưu nhóm khách hàng
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Bấm "Lưu nhóm khách hàng" ở Screen 9
- **Input:** Danh sách tên khách và nhóm
- **Main flow:**
  1. Kiểm tra dữ liệu (BR-47).
  2. Lưu; áp dụng ngay cho toàn bộ dữ liệu.
- **Output:** Thông báo "Đã lưu nhóm khách hàng."
- **Errors / alternative flows:** Dữ liệu sai thì hiện thông báo BR-47.
- **Rules applied:** BR-09, BR-15, BR-47

### UC-24: Lưu bảng số chuyền Fac 1
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Bấm "Lưu bảng số chuyền" ở Screen 9
- **Input:** Danh sách chuyền cũ và chuyền mới
- **Main flow:**
  1. Kiểm tra dữ liệu (BR-47).
  2. Lưu; áp dụng ngay cho dữ liệu Fac 1 trước 07/07/2026.
- **Output:** Thông báo "Đã lưu bảng số chuyền."
- **Errors / alternative flows:** Dữ liệu sai thì hiện thông báo BR-47.
- **Rules applied:** BR-09, BR-11, BR-47

### UC-25: Lưu tên sản phẩm theo style
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Bấm "Lưu tên sản phẩm" ở Screen 9
- **Input:** Danh sách style và tên sản phẩm
- **Main flow:**
  1. Kiểm tra dữ liệu (BR-47).
  2. Lưu; áp dụng ngay cho các dòng còn trống tên sản phẩm.
- **Output:** Thông báo "Đã lưu tên sản phẩm."
- **Errors / alternative flows:** Dữ liệu sai thì hiện thông báo BR-47.
- **Rules applied:** BR-09, BR-13, BR-47

### UC-26: Lấy lựa chọn bộ lọc và thời gian mặc định
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở một màn hình báo cáo
- **Input:** Không
- **Main flow:**
  1. Lấy ngày dữ liệu mới nhất và lần tải gần nhất.
  2. Lấy danh sách xưởng, chuyền, nhóm khách hàng, nhóm sản phẩm đang có.
  3. Tính thời gian mặc định (BR-31).
- **Output:** Lựa chọn của bộ lọc, ngày dữ liệu mới nhất, thời gian mặc định.
- **Errors / alternative flows:** Chưa có dữ liệu thì mọi báo cáo hiện "Chưa có dữ liệu. Người cập nhật cần tải file ở màn hình Cập nhật dữ liệu."
- **Rules applied:** BR-31

## 7. Business rules (Quy tắc nghiệp vụ)
| ID | Rule | Error message shown to user (VI) |
|---|---|---|
| BR-01 | File phải là .xlsx, không quá 50 MB, mỗi sheet không quá 200.000 dòng | File phải có định dạng .xlsx, không quá 50 MB và mỗi sheet không quá 200.000 dòng. Hãy kiểm tra lại rồi tải lên. |
| BR-02 | File phải có đủ 3 sheet `Production data`, `Target system`, `Worker` | File thiếu sheet: <tên sheet>. Hãy dùng đúng file Data sewing. |
| BR-03 | Mỗi sheet phải có đủ cột bắt buộc ở mục 5.1 | Sheet <tên sheet> thiếu cột: <tên cột>. Hãy kiểm tra dòng tiêu đề của sheet. |
| BR-04 | `Production data` phải có ít nhất 1 dòng hợp lệ và có ít nhất một ô mục tiêu B có giá trị | File chưa có kết quả công thức. Hãy mở file bằng Excel, lưu lại rồi tải lên. |
| BR-05 | Dòng sản lượng hợp lệ khi có ngày đúng định dạng, xưởng, khách hàng, style, mã đơn, chuyền; sản lượng là số ≥ 0; giá CM, số người, giờ làm là số > 0. Dòng sai bị bỏ qua và được liệt kê | Dòng <số dòng>: thiếu hoặc sai <tên cột>. |
| BR-06 | Xưởng được đổi tên: `SVL-Factory 2` = Fac 1, `SHCM-Factory 2` = Fac 2, `SHCM-Factory 3` = Fac 3, `SHCM-Factory 5` = Fac 5. Tên khác bị bỏ qua và được liệt kê | Dòng <số dòng>: chưa nhận diện được xưởng "<tên>". |
| BR-07 | Khi lưu, mỗi sheet thay dữ liệu đang có trong khoảng từ ngày đầu đến ngày cuối của sheet đó trong file. Dòng cùng nhận diện được cập nhật; dòng không còn trong file không hiện nữa nhưng vẫn được giữ lại có đánh dấu đã xoá; dữ liệu ngoài khoảng giữ nguyên | - |
| BR-08 | Cảnh báo không chặn việc lưu, gồm: số dòng thiếu SMV hoặc thiếu mục tiêu B theo ngày; ngày có sản lượng nhưng chưa có số thợ; ngày từ 03/10/2026 có sản lượng nhưng chưa có `Target system`; số dòng trùng; số tên sản phẩm chưa phân nhóm; số style chưa có tên sản phẩm | - |
| BR-09 | Chỉ người có vai trò `UPDATER` hoặc quản trị viên được tải file, sửa mục tiêu, ngưỡng, danh mục và nhập đổi mã hàng tuần | Bạn chưa có quyền cập nhật dữ liệu. Hãy liên hệ quản trị viên. |
| BR-10 | Tên chuyền được chuẩn hoá thành `LINE <số>`, không phân biệt hoa thường | - |
| BR-11 | Dữ liệu Fac 1 có ngày trước 07/07/2026 được đổi tên chuyền theo bảng số chuyền Fac 1. Chuyền không có trong bảng giữ tên đã chuẩn hoá | - |
| BR-12 | Mã đơn gốc = mã đơn bỏ khoảng trắng hai đầu và bỏ phần số sau dấu chấm cuối (nếu có) | - |
| BR-13 | Tên sản phẩm trống được điền theo thứ tự: bảng tên sản phẩm theo style; cùng mã đơn gốc trong dữ liệu; cùng style trong dữ liệu; cùng mã đơn gốc trong `Target system`; cùng style trong `Target system`. Nếu ra nhiều tên, lấy tên xuất hiện nhiều nhất; bằng nhau thì lấy tên đứng trước theo bảng chữ cái. Không tra được thì để trống. File gốc giữ nguyên | - |
| BR-14 | Nhóm sản phẩm lấy theo danh mục (không phân biệt hoa thường). Tên không có trong danh mục hoặc để trống thuộc "Chưa phân nhóm" | - |
| BR-15 | Nhóm khách hàng lấy theo danh mục trước. Nếu không có: tên bắt đầu bằng `ELAND` thuộc nhóm ELAND; tên khác lấy chính tên đó, viết hoa, bỏ khoảng trắng hai đầu | - |
| BR-16 | Dòng `Target system` có dạng `<xưởng> - Sewing Line <số>`: SFVL = Fac 1, SF2 = Fac 2, SF3 = Fac 3, SF5 = Fac 5. Dòng trống bị bỏ qua không báo. Dòng có dữ liệu nhưng sai dạng, sai ngày hoặc sai mục tiêu bị bỏ qua và được liệt kê | Sheet Target system, dòng <số dòng>: sai <tên cột>. |
| BR-17 | Tiền CM = sản lượng × giá CM. Không làm tròn khi tính | - |
| BR-18 | Hiệu suất A = tổng sản lượng / tổng mục tiêu A, chỉ tính các ngày và chuyền có mục tiêu A; cả tử số và mẫu số cùng phạm vi. Không có ngày nào có mục tiêu A thì hiện "-". Khoảng có ngày không có mục tiêu A thì báo "Hiệu suất A chỉ tính từ <ngày đầu có mục tiêu>." | - |
| BR-19 | Hiệu suất B = tổng sản lượng / tổng mục tiêu B, bỏ các dòng thiếu mục tiêu B khỏi cả tử số và mẫu số. Không còn dòng nào thì hiện "-" | - |
| BR-20 | Giờ làm chuyền trong ngày = trung bình giờ làm các dòng của chuyền. Giờ làm xưởng trong ngày = trung bình giờ làm các chuyền. Giờ làm xưởng cả kỳ = trung bình giờ làm các ngày của xưởng | - |
| BR-21 | Số người chuyền trong ngày = trung bình số người các dòng của chuyền | - |
| BR-22 | MO 8h của chuyền trong ngày = tiền CM của chuyền / số người × 8 / giờ làm. MO 8h của chuyền cả kỳ = trung bình MO 8h các ngày | - |
| BR-23 | MO của xưởng trong ngày = tiền CM / số thợ. MO 8h của xưởng trong ngày = MO × 8 / giờ làm. MO 8h của xưởng cả kỳ = tổng tiền CM / tổng số thợ × 8 / giờ làm cả kỳ, chỉ tính các ngày có số thợ. Ngày chưa có số thợ thì MO và MO 8h của ngày đó hiện "-" | - |
| BR-24 | Giá CM trung bình = tổng tiền CM / tổng sản lượng | - |
| BR-25 | Tỷ lệ đúng sở trường = 1 − tổng mục tiêu A dòng trái sở trường / tổng mục tiêu A. Không có mục tiêu A thì hiện "-" | - |
| BR-26 | Mức mục tiêu, ngưỡng của một ngày là mức có ngày hiệu lực gần nhất, không sau ngày đó. Số của một ngày so với mức của ngày đó. Số cả kỳ so với mức của ngày cuối kỳ | - |
| BR-27 | % so với mục tiêu = thực tế / mục tiêu. Áp cho hiệu suất A, hiệu suất B, MO 8h | - |
| BR-28 | Hiệu suất dưới ngưỡng hiệu suất hoặc MO 8h dưới ngưỡng MO 8h thì đánh giá "Dưới ngưỡng" và hiện dấu 🔴 cạnh con số; bằng hoặc trên ngưỡng thì "Đạt"; số "-" thì đánh giá "-". Áp cho cả hiệu suất A và B, ở cấp chuyền và cấp xưởng | - |
| BR-29 | Khi lọc khách hàng hoặc sản phẩm: sản lượng, tiền CM, giá CM trung bình, mục tiêu B và hiệu suất B lọc theo lựa chọn; mục tiêu A, hiệu suất A, MO, MO 8h, số người, số thợ, tỷ lệ đúng sở trường hiện "-" | - |
| BR-30 | Từ ngày phải không sau đến ngày | Từ ngày không được sau đến ngày. Hãy chọn lại khoảng thời gian. |
| BR-31 | Thời gian mặc định: Screen 1, 2 lấy tuần thứ Bảy đến thứ Sáu đầy đủ gần nhất, có thứ Sáu không sau ngày dữ liệu mới nhất; Screen 3 lấy ngày dữ liệu mới nhất; Screen 4, 5, 6 lấy từ ngày 1 của tháng có dữ liệu mới nhất đến ngày dữ liệu mới nhất | - |
| BR-32 | Số lần đổi KPI: với mỗi chuyền, lấy các mã đơn gốc có ngày đầu tiên trên chuyền (tính trên toàn bộ dữ liệu đã lưu) nằm trong khoảng đã chọn; mỗi cặp SMV + CM của các đơn đó chỉ tính 1 lần trong khoảng | - |
| BR-33 | Số ngày làm việc = số ngày xưởng có sản lượng trong khoảng đã chọn | - |
| BR-34 | Số chuyền = số chuyền của xưởng có sản lượng trong khoảng đã chọn | - |
| BR-35 | KPI đổi mã hàng = số lần đổi KPI / số ngày làm việc / số chuyền | - |
| BR-36 | Số lần đổi gồm cả lên lại: với mỗi chuyền và mỗi ngày trong khoảng, một cặp SMV + CM được tính 1 lần nếu ngày làm việc liền trước của chuyền đó không chạy cặp này. Ngày làm việc liền trước tính trên toàn bộ dữ liệu đã lưu; ngày chuyền nghỉ không tính là cách quãng. Lần đầu tiên cũng được tính. Số này không thay KPI | - |
| BR-37 | Dòng thiếu SMV không được tính vào BR-32 và BR-36 | - |
| BR-38 | Đổi mã hàng tuần chỉ hiện khi khoảng đã chọn trùng đúng từ ngày và đến ngày đã nhập của xưởng; nếu không thì hiện "-" | - |
| BR-39 | Khi nhập đổi mã hàng tuần: từ ngày không sau đến ngày; số lần là số nguyên ≥ 0; có ít nhất một xưởng được nhập | Hãy nhập khoảng ngày hợp lệ và số lần là số nguyên từ 0 trở lên cho ít nhất một xưởng. |
| BR-40 | Trùng xưởng, từ ngày và đến ngày thì số mới thay số cũ | - |
| BR-41 | Đổi mã hàng tuần trên chuyền = đổi mã hàng tuần / số chuyền theo BR-34 | - |
| BR-42 | Báo cáo ngày: mục tiêu sản lượng lấy nguyên tổng `Daily Target (SMV)`; Target MO 8h = tổng `Daily Target (CM)` / số thợ × 8 / giờ làm thực tế của xưởng trong ngày. Không có điều chỉnh tay. Thiếu số thì hiện "-" | - |
| BR-43 | Sản lượng trái sở trường của chuyền = tổng sản lượng các dòng `Match line strength` = `Trái sở trường` | - |
| BR-44 | Xếp hạng chuyền theo chỉ số đã chọn trong khoảng đã chọn, mặc định hiệu suất B; hiện 10 chuyền cao nhất và 10 chuyền thấp nhất; bỏ chuyền có giá trị "-" | - |
| BR-45 | Khi lưu mục tiêu: có xưởng và ngày hiệu lực; 4 giá trị đều là số > 0 | Hãy chọn xưởng, ngày hiệu lực và nhập cả 4 mức là số lớn hơn 0. |
| BR-46 | Trùng xưởng và ngày hiệu lực thì mức mới thay mức cũ | - |
| BR-47 | Danh mục: cột đầu và cột giá trị không được trống; cột đầu không được trùng trong cùng một danh mục (không phân biệt hoa thường); với bảng số chuyền, tên chuyền phải có dạng `LINE <số>` | Danh mục có dòng trống hoặc trùng: <giá trị>. Hãy sửa rồi lưu lại. |
| BR-48 | Dòng Tổng báo cáo tháng theo xưởng: tổng tiền CM, tổng sản lượng, tổng mục tiêu B, hiệu suất B = sản lượng / mục tiêu B, MO 8h theo BR-23. Dòng Tổng màn hình MO theo chuyền: trong ngày MO 8h = tổng tiền CM các chuyền / tổng số người các chuyền × 8 / giờ làm xưởng; cả kỳ dùng tổng của các ngày và giờ làm trung bình các ngày | - |
| BR-49 | File Excel xuất: mỗi báo cáo một sheet; tiêu đề in đậm, có nền màu, luôn hiện khi kéo xuống; cột tự giãn; không tô màu theo ngưỡng; có cột hoặc dòng Đánh giá theo BR-28 ở các báo cáo ghi trong mục 5.2; số "-" được ghi là "-" | - |
| BR-50 | Hiển thị: sản lượng và mục tiêu là số nguyên; hiệu suất và các tỷ lệ theo % có 1 chữ số lẻ; tiền CM, giá CM, MO, MO 8h, giờ làm có 2 chữ số lẻ; KPI đổi mã hàng có 3 chữ số lẻ. Chỉ làm tròn khi hiển thị và xuất file | - |

## 8. Screens (Màn hình) - each screen becomes ONE page
### Giao diện đã chốt (UI concept)
- **Menu:** mỗi màn hình là một mục trong menu bên trái của ứng dụng, chia 2 nhóm. Nhóm "Báo cáo": Tổng quan, Chi tiết chuyền, Báo cáo ngày, Báo cáo tháng, MO theo chuyền, Đổi mã hàng. Nhóm "Quản lý dữ liệu": Cập nhật dữ liệu, Mục tiêu và ngưỡng, Danh mục.
- **Chung:** mọi bảng báo cáo chỉ xem, lọc, sắp xếp, tìm kiếm và tải Excel. Bộ lọc ở trên cùng. Không có ô số liệu tổng hợp ở các màn hình báo cáo. Dấu 🔴 đặt cạnh con số trong bảng.
- **Tổng quan (trang đầu):** từ trên xuống: bộ lọc (Từ ngày, Đến ngày, Xưởng, Nhóm khách hàng, Nhóm sản phẩm); dòng thời điểm dữ liệu; ghi chú cách A nếu có; bảng Chỉ số | Fac 1 | Fac 2 | Fac 3 | Fac 5; nút "Tải Excel báo cáo tuần"; biểu đồ hiện ngay dưới bảng, xếp 2 cột: Hiệu suất A theo ngày (đường), Hiệu suất B theo ngày (đường), MO 8h theo ngày (đường), Sản lượng so với mục tiêu A giữa các xưởng (cột); hàng cuối: lựa chọn chỉ số xếp hạng, 10 chuyền cao nhất (cột), 10 chuyền thấp nhất (cột).
- **Chi tiết chuyền:** bộ lọc (Từ ngày, Đến ngày, Xưởng, Chuyền, Nhóm khách hàng, Nhóm sản phẩm); bảng mỗi dòng là một chuyền trong một ngày, kèm dòng Cả kỳ và dòng Tổng: Chuyền | Ngày | Mục tiêu A | Sản lượng | Hiệu suất A | Mục tiêu B | Hiệu suất B | Tiền CM | Số người | Giờ làm | MO 8h; bảng nhỏ Ngày | Số thợ | Giờ làm của xưởng; nút "Tải Excel báo cáo tuần".
- **Báo cáo ngày:** bộ lọc Ngày; bảng Chỉ số | Fac 1 | Fac 2 | Fac 3 | Fac 5; lựa chọn Xưởng; bảng chuyền: Chuyền | Sản lượng | Tiền CM | Giờ làm | Số người | MO | MO 8h | Sản lượng trái sở trường, có dòng Tổng; nút "Tải Excel".
- **Báo cáo tháng:** bộ lọc (Từ ngày, Đến ngày, Xưởng); mỗi xưởng một bảng: Ngày | MO | Giờ làm | MO 8h | Mục tiêu B | Sản lượng | Hiệu suất B | Tiền CM | Số thợ, dòng cuối là Tổng; nút "Tải Excel".
- **MO theo chuyền:** bộ lọc (Từ ngày, Đến ngày, Xưởng, Chuyền); 5 thẻ: MO 8h, Tiền CM, Giờ làm, Số người, Hiệu suất B; mỗi thẻ một bảng: Chuyền | các cột ngày | Cả kỳ, dòng cuối là Tổng; nút "Tải Excel".
- **Đổi mã hàng:** bộ lọc (Từ ngày, Đến ngày, Xưởng, Chuyền); 4 thẻ: Theo xưởng, Theo tháng, Theo chuyền, Chi tiết; nút "Tải Excel".
- **Cập nhật dữ liệu:** từ trên xuống: khối Bước 1 chọn file và nút "Kiểm tra file"; khối Bước 2 kết quả kiểm tra, bảng dòng bị bỏ qua, bảng cảnh báo, nút "Lưu dữ liệu" có hỏi lại trước khi lưu; khối đổi mã hàng tuần dạng form (Từ ngày, Đến ngày, 4 ô số, nút "Lưu số đổi mã hàng", không hỏi lại); bảng chọn một dòng đã nhập và nút "Xoá dòng đã chọn" có hỏi lại; bảng lịch sử tải file chỉ xem.
- **Mục tiêu và ngưỡng:** bảng đang áp dụng chỉ xem; form thêm mức mới (Xưởng, Ngày hiệu lực, 4 ô số, nút "Lưu mức mới", không hỏi lại); bảng lịch sử chỉ xem.
- **Danh mục:** 4 thẻ: Nhóm sản phẩm, Nhóm khách hàng, Số chuyền Fac 1, Tên sản phẩm theo style; mỗi thẻ một bảng sửa trực tiếp trong ô, thêm và bớt được dòng, nút lưu tương ứng, không hỏi lại; dưới bảng là danh sách còn thiếu, chỉ xem.

Screen 1 đến 6 cấp cho mọi người xem. Screen 7 đến 9 chỉ cấp cho người có vai trò `UPDATER`. Mọi báo cáo hiện ngày dữ liệu mới nhất và thời điểm tải file gần nhất (UC-26).

### Screen 1: Tổng quan (landing page)
- **Purpose:** So sánh 4 xưởng theo khoảng thời gian, tương ứng sheet `Overall`.
- **Inputs/filters:** Từ ngày, đến ngày (mặc định BR-31, bắt buộc); Xưởng (chọn nhiều, mặc định tất cả); Nhóm khách hàng (chọn nhiều, mặc định tất cả); Nhóm sản phẩm (chọn nhiều, mặc định tất cả).
- **Bảng chỉ số, mỗi xưởng một cột:** Mục tiêu A; Sản lượng; Mục tiêu hiệu suất; Hiệu suất A; % so với mục tiêu của hiệu suất A; Mục tiêu B; Hiệu suất B; % so với mục tiêu của hiệu suất B; Tiền CM; Mục tiêu MO 8h; MO 8h; % so với mục tiêu của MO 8h; Giá CM trung bình; Giờ làm trung bình; Tỷ lệ đúng sở trường; Đổi mã hàng tuần; Đổi mã hàng tuần trên chuyền. Có dấu 🔴 theo BR-28.
- **Biểu đồ (UC-05):** Hiệu suất A theo ngày; Hiệu suất B theo ngày; MO 8h theo ngày; Sản lượng so với mục tiêu A giữa các xưởng; Xếp hạng chuyền với lựa chọn Hiệu suất B/Hiệu suất A/MO 8h.
- **Actions:** "Tải Excel báo cáo tuần" → UC-11. Đổi bộ lọc → UC-04, UC-05.
- **Khi không có dữ liệu:** "Chưa có dữ liệu trong khoảng thời gian này."

### Screen 2: Chi tiết chuyền
- **Purpose:** Xem từng chuyền theo ngày, tương ứng các sheet `Fac`.
- **Inputs/filters:** Từ ngày, đến ngày (mặc định BR-31); Xưởng (một xưởng, mặc định Fac 1); Chuyền (chọn nhiều, mặc định tất cả); Nhóm khách hàng; Nhóm sản phẩm.
- **Bảng, sắp theo số chuyền rồi ngày:** Chuyền, Ngày, Mục tiêu A, Sản lượng, Hiệu suất A, Mục tiêu B, Hiệu suất B, Tiền CM, Số người, Giờ làm, MO 8h. Có dòng Cả kỳ của từng chuyền và dòng Tổng xưởng. Có dấu 🔴 theo BR-28.
- **Thông tin xưởng theo ngày:** Số thợ, Giờ làm.
- **Actions:** "Tải Excel báo cáo tuần" → UC-11. Đổi bộ lọc → UC-06.
- **Khi không có dữ liệu:** "Chưa có dữ liệu trong khoảng thời gian này."

### Screen 3: Báo cáo ngày
- **Purpose:** Xem kết quả một ngày, tương ứng `Daily Report Sewing`, bỏ Cutting.
- **Inputs/filters:** Ngày (mặc định BR-31, bắt buộc); Xưởng cho bảng chuyền (một xưởng, mặc định Fac 1).
- **Bảng xưởng, mỗi xưởng một cột:** MO; Giờ làm; Target MO 8h; MO 8h; % so với Target MO 8h; Mục tiêu sản lượng; Sản lượng; Hiệu suất A; Hiệu suất B; Tỷ lệ đúng sở trường; Số thợ.
- **Bảng chuyền, sắp theo số chuyền, có dòng Tổng:** Chuyền, Sản lượng, Tiền CM, Giờ làm, Số người, MO, MO 8h, Sản lượng trái sở trường. Fac 1 hiện chung, không tách chuyền cũ và mới.
- **Actions:** "Tải Excel" → UC-12. Đổi ngày hoặc xưởng → UC-07.
- **Khi không có dữ liệu:** "Chưa có dữ liệu của ngày này."

### Screen 4: Báo cáo tháng
- **Purpose:** Xem từng xưởng theo ngày, tương ứng `Report final`.
- **Inputs/filters:** Từ ngày, đến ngày (mặc định BR-31); Xưởng (chọn nhiều, mặc định tất cả).
- **Bảng mỗi xưởng, sắp theo ngày, có dòng Tổng:** Ngày, MO, Giờ làm, MO 8h, Mục tiêu B, Sản lượng, Hiệu suất B, Tiền CM, Số thợ. Có dấu 🔴 theo BR-28.
- **Actions:** "Tải Excel" → UC-13. Đổi bộ lọc → UC-08.
- **Khi không có dữ liệu:** "Chưa có dữ liệu trong khoảng thời gian này."

### Screen 5: MO theo chuyền
- **Purpose:** Xem MO 8h của từng chuyền theo ngày, tương ứng sheet `MO`.
- **Inputs/filters:** Từ ngày, đến ngày (mặc định BR-31); Xưởng (một xưởng, mặc định Fac 1); Chuyền (chọn nhiều, mặc định tất cả).
- **5 bảng, hàng là chuyền, cột là ngày, có cột Cả kỳ và dòng Tổng:** MO 8h; Tiền CM; Giờ làm; Số người; Hiệu suất B. Có dấu 🔴 theo BR-28 ở MO 8h và Hiệu suất B.
- **Actions:** "Tải Excel" → UC-14. Đổi bộ lọc → UC-09.
- **Khi không có dữ liệu:** "Chưa có dữ liệu trong khoảng thời gian này."

### Screen 6: Đổi mã hàng
- **Purpose:** Theo dõi KPI đổi mã hàng và số lần đổi gồm cả lên lại.
- **Inputs/filters:** Từ ngày, đến ngày (mặc định BR-31); Xưởng (chọn nhiều, mặc định tất cả); Chuyền (chọn nhiều, mặc định tất cả).
- **Bảng theo xưởng:** Xưởng, Số lần đổi KPI, Số ngày làm việc, Số chuyền, KPI đổi mã hàng, Số lần đổi gồm cả lên lại, Đổi mã hàng tuần. Có dòng tổng chỉ cộng số lần.
- **Bảng theo tháng, tính riêng từng tháng trong khoảng:** Tháng, Xưởng, Số lần đổi KPI, Số ngày làm việc, Số chuyền, KPI đổi mã hàng, Số lần đổi gồm cả lên lại.
- **Bảng theo chuyền:** Xưởng, Chuyền, Số lần đổi KPI, Số lần đổi gồm cả lên lại.
- **Bảng chi tiết các lần tính vào KPI:** Ngày, Xưởng, Chuyền, Mã đơn gốc, Style, SMV, Giá CM.
- **Actions:** "Tải Excel" → UC-15. Đổi bộ lọc → UC-10.
- **Khi không có dữ liệu:** "Chưa có dữ liệu trong khoảng thời gian này."

### Screen 7: Cập nhật dữ liệu
- **Purpose:** Tải file dữ liệu và nhập đổi mã hàng tuần.
- **Khối tải file:** Chọn file (.xlsx, bắt buộc). Nút "Kiểm tra file" → UC-01. Sau khi kiểm tra hiện: số dòng đọc được, hợp lệ, bị bỏ qua; ngày đầu, ngày cuối; so sánh số dòng với dữ liệu đang lưu; bảng dòng bị bỏ qua (Sheet, Dòng, Lý do); bảng cảnh báo (Loại, Ngày, Số lượng). Nút "Lưu dữ liệu" → UC-02, chỉ hiện khi file không bị từ chối. Sau khi lưu hiện thông báo của UC-02.
- **Khối lịch sử tải file (UC-03):** Thời điểm, Người tải, Tên file, Từ ngày, Đến ngày, Số dòng lưu, Số dòng bỏ qua.
- **Khối đổi mã hàng tuần:** Từ ngày, Đến ngày (mặc định tuần của BR-31); Số lần của Fac 1, Fac 2, Fac 3, Fac 5 (số nguyên, để trống là không lưu). Nút "Lưu số đổi mã hàng" → UC-19.
- **Danh sách đã nhập (UC-18):** Xưởng, Từ ngày, Đến ngày, Số lần, Người lưu. Chọn một dòng rồi bấm "Xoá dòng đã chọn" → UC-20.

### Screen 8: Mục tiêu và ngưỡng
- **Purpose:** Xem và đổi mục tiêu, ngưỡng theo ngày hiệu lực.
- **Bảng đang áp dụng (UC-16):** Xưởng, Ngày hiệu lực, Mục tiêu hiệu suất, Mục tiêu MO 8h, Ngưỡng hiệu suất, Ngưỡng MO 8h.
- **Khối thêm mức mới:** Xưởng (bắt buộc), Ngày hiệu lực (mặc định hôm nay, bắt buộc), 4 mức (số > 0, bắt buộc). Nút "Lưu mức mới" → UC-17.
- **Bảng lịch sử:** các cột như bảng đang áp dụng và Người lưu, mới nhất lên đầu.

### Screen 9: Danh mục
- **Purpose:** Sửa các danh mục dùng để làm sạch dữ liệu. Sửa xong áp dụng ngay cho toàn bộ dữ liệu.
- **Nhóm sản phẩm (UC-21):** bảng sửa được Tên sản phẩm, Nhóm sản phẩm; danh sách tên chưa phân nhóm kèm số dòng. Nút "Lưu nhóm sản phẩm" → UC-22.
- **Nhóm khách hàng:** bảng sửa được Tên khách hàng, Nhóm khách hàng; danh sách mọi tên đang có kèm nhóm hiện tại và số dòng. Nút "Lưu nhóm khách hàng" → UC-23.
- **Bảng số chuyền Fac 1:** bảng sửa được Chuyền cũ, Chuyền mới. Nút "Lưu bảng số chuyền" → UC-24.
- **Tên sản phẩm theo style:** bảng sửa được Style, Tên sản phẩm; danh sách style chưa có tên kèm khách hàng và số dòng. Nút "Lưu tên sản phẩm" → UC-25.

## 9. Acceptance criteria (Tiêu chí nghiệm thu)
Số liệu dưới đây lấy từ các file mẫu; số có thể đổi nếu file được cập nhật sau đó.

- [ ] AC-01: Given người có vai trò `UPDATER`, When tải file `.pdf`, Then thấy thông báo BR-01 và không có nút Lưu.
- [ ] AC-02: Given file thiếu sheet `Worker`, When kiểm tra, Then thấy "File thiếu sheet: Worker. Hãy dùng đúng file Data sewing." và dữ liệu đã lưu giữ nguyên.
- [ ] AC-03: Given sheet `Production data` thiếu cột `Price`, When kiểm tra, Then thấy thông báo BR-03 nêu đúng sheet và cột.
- [ ] AC-04: Given file chưa có kết quả công thức, When kiểm tra, Then thấy thông báo BR-04.
- [ ] AC-05: Given file có một dòng thiếu mã đơn, When kiểm tra, Then dòng đó được liệt kê với số dòng và lý do, các dòng khác vẫn hợp lệ, có nút Lưu.
- [ ] AC-06: Given file có xưởng lạ, When kiểm tra, Then dòng đó được liệt kê với thông báo BR-06.
- [ ] AC-07: Given file `Data sewing 2026.xlsx` đúng mẫu, When bấm "Kiểm tra file", Then chưa có gì được lưu và thấy số dòng, ngày đầu, ngày cuối, cảnh báo.
- [ ] AC-08: Given đã lưu file đến ngày 04/11, When tải file có giá CM ngày cũ đã đổi, Then báo cáo ngày cũ dùng giá mới và số dòng hiện trên báo cáo không tăng thêm với các dòng đã có.
- [ ] AC-09: Given đã có dữ liệu 2026, When lưu file chỉ có các ngày năm 2027, Then dữ liệu 2026 giữ nguyên.
- [ ] AC-10: Given một dòng có trong file trước nhưng không còn trong file mới, cùng khoảng ngày, When lưu, Then dòng đó không còn tính vào báo cáo và vẫn được giữ lại có đánh dấu đã xoá.
- [ ] AC-11: Given ngày 04/11 có 45 dòng thiếu SMV và chưa có `Worker`, `Target system`, When kiểm tra, Then thấy cảnh báo và vẫn lưu được; hiệu suất A và MO xưởng ngày đó hiện "-"; hiệu suất B bỏ 45 dòng đó.
- [ ] AC-12: Given người không có vai trò `UPDATER`, When gọi việc lưu file, Then thấy thông báo BR-09 và dữ liệu không đổi.
- [ ] AC-13: Given sau khi lưu, When mở Screen 7, Then lịch sử có thời điểm, người tải, tên file, khoảng ngày, số dòng.
- [ ] AC-14: Given dữ liệu Fac 1 có `Line 1` và `LINE 1` cùng sau 07/07/2026, When xem chi tiết chuyền, Then chỉ có một chuyền LINE 1.
- [ ] AC-15: Given dòng Fac 1 ngày 06/07/2026 ở `LINE 1`, When xem báo cáo, Then dòng đó thuộc LINE 30. Dòng ngày 07/07/2026 ở `LINE 1` vẫn thuộc LINE 1.
- [ ] AC-16: Given dòng trống tên sản phẩm có mã đơn gốc đã có tên trong dữ liệu, When lưu file, Then dòng đó nhận tên đó và file gốc không đổi.
- [ ] AC-17: Given style không tra được tên, When người cập nhật nhập tên ở Screen 9 và bấm "Lưu tên sản phẩm", Then các dòng của style đó nhận tên mới và rời danh sách chưa có tên.
- [ ] AC-18: Given tên `VITRIOL`, When xem Screen 9, Then tên này nằm trong danh sách chưa phân nhóm. Given bấm "Lưu nhóm sản phẩm" sau khi xếp nhóm, Then báo cáo dùng nhóm mới cho cả ngày cũ.
- [ ] AC-19: Given các tên `ELAND WORLD`, `ELAND SPORT`, `ELAND WORLD/SPAO (QR)`, `MI HUB LIMITED`, When xem bộ lọc, Then chỉ có nhóm ELAND và MIHUB. Given bấm "Lưu nhóm khách hàng" với một tên mới gộp, Then báo cáo dùng nhóm mới.
- [ ] AC-20: Given chọn 24/10/2026–30/10/2026, When xem Screen 1, Then sản lượng, mục tiêu A và hiệu suất A là: Fac 1 181.450 / 197.589 / 91,8%; Fac 2 62.559 / 63.289 / 98,8%; Fac 3 69.300 / 65.080 / 106,5%; Fac 5 54.534 / 52.983 / 102,9%.
- [ ] AC-21: Given cùng khoảng ngày, When xem Screen 1, Then hiệu suất B là: Fac 1 92,5%; Fac 2 100,4%; Fac 3 110,8%; Fac 5 104,6%.
- [ ] AC-22: Given cùng khoảng ngày, When xem Screen 1, Then tỷ lệ đúng sở trường là: Fac 1 82,3%; Fac 2 99,2%; Fac 3 96,6%; Fac 5 100,0%.
- [ ] AC-23: Given chọn 01/10/2026–10/10/2026, When xem Screen 1, Then hiệu suất A chỉ tính từ 03/10/2026 và có ghi chú BR-18. Given chọn 01/09/2026–30/09/2026, Then hiệu suất A hiện "-", hiệu suất B vẫn có số.
- [ ] AC-24: Given lọc nhóm khách hàng ELAND, When xem Screen 1, Then sản lượng, tiền CM và hiệu suất B thay đổi theo lọc; hiệu suất A, MO 8h, tỷ lệ đúng sở trường hiện "-".
- [ ] AC-25: Given chọn 24/10/2026–30/10/2026, When xem Screen 2 với LINE 1 Fac 1, Then MO 8h ngày 24/10 là 26,56 và cả kỳ khoảng 26,54.
- [ ] AC-26: Given chọn 24/10/2026–30/10/2026, When xem Screen 1, Then MO 8h Fac 3 khoảng 43,1 và Fac 5 khoảng 42,4; Fac 1 khoảng 33,6 vì giờ làm được tính từ dữ liệu.
- [ ] AC-27: Given mục tiêu MO 8h Fac 1 là 38, When lưu mức 40 hiệu lực từ 01/12/2026, Then số ngày 30/11/2026 so với 38 và số ngày 01/12/2026 so với 40.
- [ ] AC-28: Given bỏ trống một mức hoặc nhập 0 ở Screen 8, When bấm "Lưu mức mới", Then thấy thông báo BR-45.
- [ ] AC-29: Given hiệu suất của một chuyền Fac 2 là 89,9%, When xem báo cáo, Then có dấu 🔴 và Excel ghi "Dưới ngưỡng". Given hiệu suất của một chuyền Fac 1 là 85,0%, Then Excel ghi "Đạt".
- [ ] AC-30: Given MO 8h của một chuyền Fac 2 là 39,9, When xem báo cáo, Then có dấu 🔴. Given MO 8h của một chuyền Fac 1 là 30,0, Then không có dấu 🔴.
- [ ] AC-31: Given đã nhập Fac 2 = 17 cho 24/10/2026–30/10/2026, When chọn đúng khoảng đó, Then Screen 1 hiện 17 và 17/14 trên chuyền. Given chọn 24/10/2026–29/10/2026, Then hiện "-".
- [ ] AC-32: Given nhập số lần là -1 hoặc từ ngày sau đến ngày, When bấm "Lưu số đổi mã hàng", Then thấy thông báo BR-39.
- [ ] AC-33: Given dữ liệu file KPI, chọn 01/10/2026–31/10/2026, When xem Screen 6, Then số lần đổi KPI là Fac 2 = 68, Fac 3 = 129, Fac 5 = 87, Fac 1 = 69; KPI đổi mã hàng của Fac 2 = 68 / 27 / 14.
- [ ] AC-34: Given cùng dữ liệu, When xem Screen 6, Then số lần đổi gồm cả lên lại là Fac 1 = 87, Fac 2 = 135, Fac 3 = 182, Fac 5 = 97.
- [ ] AC-35: Given một chuyền chạy cặp SMV + CM ở ngày 1, không chạy ở ngày 2, 3, chạy lại ở ngày 4, When xem Screen 6, Then số lần đổi gồm cả lên lại của cặp này là 2 và số lần đổi KPI không tăng do lần lên lại.
- [ ] AC-36: Given chuyền chạy một cặp SMV + CM thứ Bảy và thứ Hai, nghỉ Chủ nhật, When xem Screen 6, Then lần thứ Hai không tính là lên lại.
- [ ] AC-37: Given ngày 03/11/2026, When xem Screen 3, Then mục tiêu sản lượng Fac 2 = 9.863 và Target MO 8h = tổng `Daily Target (CM)` / số thợ × 8 / giờ làm của ngày đó.
- [ ] AC-38: Given mở Screen 3 với Fac 1, When xem bảng chuyền, Then mọi chuyền có sản lượng trong ngày hiện chung một bảng, không tách chuyền cũ và mới, và có cột sản lượng trái sở trường.
- [ ] AC-39: Given chọn tháng 10/2026, When xem Screen 4, Then mỗi xưởng có các ngày có dữ liệu và dòng Tổng theo BR-48.
- [ ] AC-40: Given chọn Fac 2, When xem Screen 5, Then có 5 bảng, dòng Tổng MO 8h trong ngày theo BR-48.
- [ ] AC-41: Given chọn khoảng thời gian bất kỳ, When xem Screen 1, Then có 5 biểu đồ theo UC-05; xếp hạng mặc định theo hiệu suất B, đổi được sang hiệu suất A và MO 8h. Given có bộ lọc khách hàng, Then biểu đồ không áp dụng hiện thông báo của UC-05.
- [ ] AC-42: Given từ ngày sau đến ngày, When xem một báo cáo, Then thấy thông báo BR-30.
- [ ] AC-43: Given bấm "Tải Excel báo cáo tuần", When mở file, Then có sheet `Tong quan`, `Fac 1`, `Fac 2`, `Fac 3`, `Fac 5`, tiêu đề in đậm có nền màu, có cột Đánh giá, số khớp màn hình.
- [ ] AC-44: Given bấm "Tải Excel" ở Screen 3, 4, 5, 6, When mở file, Then có đúng các sheet ở mục 5.2 và số khớp màn hình.
- [ ] AC-45: Given chưa có dữ liệu, When mở Screen 1, Then thấy "Chưa có dữ liệu. Người cập nhật cần tải file ở màn hình Cập nhật dữ liệu." và không có lỗi.
- [ ] AC-46: Given mở Screen 1 với dữ liệu đến 04/11/2026, When chưa đổi bộ lọc, Then khoảng thời gian là 24/10/2026–30/10/2026.
- [ ] AC-47: Given đã có Fac 2 = 17 cho 24/10–30/10, When lưu lại số 18 cùng khoảng, Then danh sách vẫn có một dòng với số 18. Given chọn dòng đó và bấm "Xoá dòng đã chọn", Then báo cáo khoảng đó hiện "-".
- [ ] AC-48: Given danh mục có hai dòng trùng tên hoặc tên chuyền sai dạng, When bấm lưu, Then thấy thông báo BR-47.
- [ ] AC-49: Given bảng số chuyền đổi `LINE 1` thành `LINE 2`, When bấm "Lưu bảng số chuyền", Then dữ liệu Fac 1 trước 07/07/2026 ở chuyền cũ đó tính vào LINE 2.
- [ ] AC-50: Given mở Screen 8, When xem, Then thấy mức đang áp dụng của 4 xưởng và lịch sử. Given lưu mức mới trùng xưởng và ngày hiệu lực, Then mức mới thay mức cũ, không thêm dòng.
- [ ] AC-51: Given chọn 24/10/2026–30/10/2026, When xem Screen 1, Then giá CM trung bình của mỗi xưởng = tiền CM / sản lượng của xưởng đó.
- [ ] AC-52: Given dữ liệu mới nhất ngày 04/11/2026, When mở Screen 3, Then ngày mặc định là 04/11/2026. When mở Screen 4, 5 hoặc 6, Then khoảng mặc định là 01/11/2026–04/11/2026.

## 10. Open questions (Câu hỏi mở)
Phạm vi: đợt 2 (bảng dấu màu theo khách hàng, tiền CM theo khách hàng và sản phẩm, sản lượng order trung bình) và đợt 3 (dữ liệu 2025) không thuộc tài liệu này. Không làm: phần Cutting; tự đọc file từ SharePoint hoặc máy cá nhân; sửa file nguồn; tô màu trong file Excel xuất; hiệu suất A trước 03/10/2026.

- Giả định: Số lần đổi KPI của Fac 1 tháng 10/2026 trên app là 69, file KPI là 70, vì app đã quy số chuyền trước 07/07/2026 về tên hiện nay. Fac 1 tháng 7/2026 là 99, file KPI là 234.
- Giả định: Khoảng thời gian dài hơn một tháng đếm cặp SMV + CM trong toàn khoảng, nên số lần có thể nhỏ hơn tổng các tháng. Bảng theo tháng ở Screen 6 vẫn tính riêng từng tháng.
- Giả định: Số cả kỳ so với mục tiêu và ngưỡng của ngày cuối kỳ.
- Giả định: MO 8h xưởng cả kỳ bỏ các ngày chưa có số thợ.
- Giả định: MO 8h Fac 1 và Fac 2 có thể lệch nhẹ so với báo cáo tuần cũ vì giờ làm không còn gõ tay. Tuần 24–30/10/2026: giờ làm Fac 1 là 8,88 so với 8,84, MO 8h khoảng 33,6 so với 33,8.
- Giả định: Dòng trùng ngày, xưởng, chuyền, mã đơn, màu đều được giữ và cộng vào báo cáo như Excel (51 dòng trong năm 2026), kèm cảnh báo.
- Giả định: Bộ lọc theo từng màn hình như mục 8: Screen 1 không lọc chuyền; Screen 3, 4 không lọc khách hàng và sản phẩm; Screen 5, 6 không lọc khách hàng và sản phẩm.
- Giả định: Nhóm sản phẩm ban đầu gồm các tên ở mục 4.6; các tên khác thuộc "Chưa phân nhóm".
- Giả định: Một style có nhiều tên sản phẩm bằng số lần xuất hiện thì lấy tên đứng trước theo bảng chữ cái.
- Giả định: Tên file, tên sheet và định dạng hiển thị số như mục 5.2 và BR-50.
- Giả định (triển khai): Tên viết tắt của người làm là `thynguyen`, lấy từ tài khoản GitHub `thynguyen-lab`, vì tên viết tắt chỉ gồm chữ thường và số.
- Giả định (triển khai): BR-32 đọc cặp SMV + CM ở ngày đầu tiên của đơn trên chuyền, khớp file KPI tháng 10/2026. SMV được sửa ở các ngày sau không tính thành lần đổi mới.
- Giả định (triển khai): Khi đếm đổi mã hàng, dòng thiếu SMV bị bỏ ngay từ đầu, kể cả khi tìm ngày đầu tiên của đơn và ngày làm việc liền trước. SMV và giá CM được so sánh sau khi làm tròn đến 6 chữ số lẻ để bỏ sai số của Excel.
- Giả định (triển khai): "Có sản lượng" trong BR-33, BR-34 nghĩa là sản lượng lớn hơn 0. Bộ lọc Chuyền ở Screen 6 cũng thu hẹp số ngày và số chuyền. Dòng tổng ở Screen 6 chỉ cộng hai cột số lần.
- Giả định (triển khai): Với BR-18, chuyền có mục tiêu A nhưng không có sản lượng vẫn được tính, sản lượng bằng 0, và có dòng riêng ở Screen 2. Ghi chú "chỉ tính từ" hiện khi một xưởng đã chọn có sản lượng ở ngày không có mục tiêu.
- Giả định (triển khai): Khi lọc khách hàng hoặc sản phẩm, giờ làm và số chuyền vẫn tính trên toàn bộ dòng của xưởng.
- Giả định (triển khai): Dòng Tổng ở Screen 2 luôn tính cả xưởng, kể cả khi chọn một số chuyền. Dòng Tổng ở Screen 3 và Screen 5 tính MO và MO 8h từ tổng tiền CM và tổng số người của các chuyền.
- Giả định (triển khai): Số người, số thợ hiển thị 1 chữ số lẻ; SMV và đổi mã hàng tuần trên chuyền hiển thị 2 chữ số lẻ. Excel ghi số đã làm tròn dạng số.
- Giả định (triển khai): Khi đọc file: dòng trống mọi cột nhận diện bị bỏ qua không báo; SMV không dương hoặc mục tiêu B âm tính là thiếu; dòng `Worker` không có ngày hợp lệ bị bỏ qua; ngày `Worker` bị trùng thì lấy giá trị đầu tiên. Số dòng trong thông báo lỗi có thể nhỏ hơn thực tế nếu sheet có dòng trống xen giữa.
- Giả định (triển khai): Cảnh báo dòng trùng đếm từ lần lặp thứ hai. Cảnh báo được tính trên dữ liệu sau khi lưu. Lịch sử ghi thêm một dòng cho mỗi lần lưu, kể cả khi file không đổi.
- Giả định (triển khai): Dòng danh mục trống hoàn toàn bị bỏ qua khi lưu; tên chuyền được viết lại thành `LINE <số>`.
- Giả định (triển khai): Bảng báo cáo ghi số dạng chữ căn phải, kèm dấu 🔴 trong ô, để giữ định dạng BR-50 và thứ tự sắp xếp. Cột Ngày và Chuyền sắp theo chữ khi bấm vào tiêu đề; thứ tự mặc định vẫn đúng.
- Giả định (triển khai): File trên 50 MB bị chặn ngay ở ô chọn file với thông báo có sẵn của app, không phải thông báo BR-01.
- Giả định (triển khai): Nút Tải Excel ẩn khi không có dữ liệu hoặc khoảng ngày sai. Tải Excel ở Screen 2 theo xưởng đang chọn và không theo bộ lọc Chuyền; màn hình có ghi chú việc này.
- Giả định (triển khai): Bỏ chọn hết xưởng được hiểu là chọn tất cả. Bảng Screen 1 chỉ hiện các xưởng đã chọn.
- Giả định (triển khai): Trục ngày của biểu đồ hiện tiếng Anh, ví dụ "Oct 24", do khung sườn quy định.

## 11. Implementation map (filled by the AI)
| Spec item | Code |
|---|---|
| Section 4 | `backend/features/sewing_productivity/models/` (`source_records.py`, `settings_records.py`, `clean_values.py`, `report_values.py`) |
| Section 5.1 | `constants.py`, `builders/upload_read_builders.py` |
| Section 5.2 | `builders/overview_builders.py`, `line_detail_builders.py`, `daily_builders.py`, `monthly_builders.py`, `line_mo_builders.py`, `changeover_builders.py` |
| UC-01 | `check_upload` -> `CheckUploadService` |
| UC-02 | `save_upload` -> `SaveUploadService` |
| UC-03 | `list_upload_logs` -> `ListUploadLogsService` |
| UC-04 | `get_overview` -> `GetOverviewService` |
| UC-05 | `get_charts` -> `GetChartsService` |
| UC-06 | `get_line_detail` -> `GetLineDetailService` |
| UC-07 | `get_daily_report` -> `GetDailyReportService` |
| UC-08 | `get_monthly_report` -> `GetMonthlyReportService` |
| UC-09 | `get_line_mo` -> `GetLineMoService` |
| UC-10 | `get_changeover` -> `GetChangeoverService` |
| UC-11 | `export_weekly_report` -> `ExportWeeklyReportService` |
| UC-12 | `export_daily_report` -> `ExportDailyReportService` |
| UC-13 | `export_monthly_report` -> `ExportMonthlyReportService` |
| UC-14 | `export_line_mo` -> `ExportLineMoService` |
| UC-15 | `export_changeover` -> `ExportChangeoverService` |
| UC-16 | `list_goals` -> `ListGoalsService` |
| UC-17 | `save_goal` -> `SaveGoalService` |
| UC-18 | `list_weekly_changeovers` -> `ListWeeklyChangeoversService` |
| UC-19 | `save_weekly_changeovers` -> `SaveWeeklyChangeoversService` |
| UC-20 | `delete_weekly_changeover` -> `DeleteWeeklyChangeoverService` |
| UC-21 | `get_catalogs` -> `GetCatalogsService` |
| UC-22 | `save_product_groups` -> `SaveProductGroupsService` |
| UC-23 | `save_customer_groups` -> `SaveCustomerGroupsService` |
| UC-24 | `save_line_mappings` -> `SaveLineMappingsService` |
| UC-25 | `save_style_products` -> `SaveStyleProductsService` |
| UC-26 | `get_filter_options` -> `GetFilterOptionsService` |
| BR-01 | `exceptions.py::UploadFileError` |
| BR-02 | `business/upload_business.py::UploadBusiness.ensure_sheets` |
| BR-03 | `builders/upload_read_builders.py::RawWorkbookBuilder._missing` |
| BR-04 | `builders/upload_read_builders.py::RawWorkbookBuilder._missing` |
| BR-05 | `business/upload_business.py::UploadBusiness.parse` |
| BR-06 | `business/upload_business.py::UploadBusiness.parse` |
| BR-07 | `business/upload_business.py::UploadBusiness.replacement_writes` |
| BR-08 | `business/catalog_business.py::CatalogBusiness.warnings` |
| BR-09 | `business/access_rules.py::UpdaterRoleRule` |
| BR-10 | `business/cleaning_business.py::CleaningBusiness.standard_line` |
| BR-11 | `business/cleaning_business.py::CleaningBusiness.current_line` |
| BR-12 | `business/cleaning_business.py::base_po_number` |
| BR-13 | `business/catalog_business.py::CatalogBusiness.styles_without_name` |
| BR-14 | `business/catalog_business.py::CatalogBusiness.unclassified_names` |
| BR-15 | `business/catalog_business.py::CatalogBusiness.customer_names` |
| BR-16 | `business/upload_business.py::UploadBusiness.parse` |
| BR-17 | `business/cleaning_business.py::CleaningBusiness.cm_earning` |
| BR-18 | `business/line_report_business.py::LineReportBusiness._days_by_line` |
| BR-19 | `business/line_report_business.py::LineReportBusiness.factory_total_row` |
| BR-20 | `business/line_report_business.py::LineReportBusiness.factory_total_row` |
| BR-21 | `business/line_report_business.py::LineReportBusiness.day_rows` |
| BR-22 | `business/line_report_business.py::LineReportBusiness.line_rows` |
| BR-23 | `business/line_report_business.py::LineReportBusiness.factory_total_row` |
| BR-24 | `business/productivity_business.py::ProductivityBusiness.average_cm_price` |
| BR-25 | `business/productivity_business.py::ProductivityBusiness.strength_match` |
| BR-26 | `business/productivity_business.py::ProductivityBusiness.goal_on` |
| BR-27 | `business/line_report_business.py::LineReportBusiness.line_rows` |
| BR-28 | `builders/display.py::is_below` |
| BR-29 | `business/filter_business.py::FilterBusiness.apply_groups` |
| BR-30 | `business/filter_business.py::DateRangeRule` |
| BR-31 | `business/filter_business.py::FilterBusiness.default_week` |
| BR-32 | `business/changeover_business.py::ChangeoverBusiness.usable_rows` |
| BR-33 | `business/changeover_business.py::ChangeoverBusiness.working_days` |
| BR-34 | `business/changeover_business.py::ChangeoverBusiness.line_count` |
| BR-35 | `business/changeover_business.py::ChangeoverBusiness.kpi` |
| BR-36 | `business/changeover_business.py::ChangeoverBusiness.usable_rows` |
| BR-37 | `business/changeover_business.py::ChangeoverBusiness.usable_rows` |
| BR-38 | `business/changeover_business.py::ChangeoverBusiness.weekly_count` |
| BR-39 | `business/settings_business.py::WeeklyChangeoverRule` |
| BR-40 | `business/settings_business.py::SettingsBusiness.to_weekly` |
| BR-41 | `business/changeover_business.py::ChangeoverBusiness.weekly_per_line` |
| BR-42 | `business/report_business.py::ReportBusiness.daily_summary` |
| BR-43 | `business/line_report_business.py::LineReportBusiness.day_rows` |
| BR-44 | `business/report_business.py::ReportBusiness.line_ranking` |
| BR-45 | `business/settings_business.py::GoalInputRule` |
| BR-46 | `business/settings_business.py::SettingsBusiness.to_goal` |
| BR-47 | `business/settings_business.py::CatalogRowsRule` |
| BR-48 | `business/line_report_business.py::LineReportBusiness.day_total_row` |
| BR-49 | `builders/display.py::excel_value` |
| BR-50 | `builders/display.py::excel_value` |
| BR-01 | `exceptions.py::UploadFileError` |
| Screen 1 | `frontend/features/sewing_productivity/pages/overview_page.py` |
| Screen 2 | `frontend/features/sewing_productivity/pages/line_detail_page.py` |
| Screen 3 | `frontend/features/sewing_productivity/pages/daily_report_page.py` |
| Screen 4 | `frontend/features/sewing_productivity/pages/monthly_report_page.py` |
| Screen 5 | `frontend/features/sewing_productivity/pages/line_mo_page.py` |
| Screen 6 | `frontend/features/sewing_productivity/pages/changeover_page.py` |
| Screen 7 | `frontend/features/sewing_productivity/pages/data_update_page.py` |
| Screen 8 | `frontend/features/sewing_productivity/pages/goals_page.py` |
| Screen 9 | `frontend/features/sewing_productivity/pages/catalogs_page.py` |
| Logs | Mỗi dịch vụ ghi các bước chính vào `logs/app.log` |
| Tests | `backend/features/sewing_productivity/tests/` |
