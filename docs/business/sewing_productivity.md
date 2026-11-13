# Sewing Performance (trước đây: Năng suất xưởng may)

| Feature key | `sewing_productivity` (= folder name in `backend/features/` and `frontend/features/`) |
|---|---|
| Home group (Nhóm trên Trang chủ) | Production |
| Icon (Biểu tượng) | 🧵 |
| Owner (Người phụ trách) | PI - SO team |
| Status (Trạng thái) | Implemented |
| Run mode (Chạy ở đâu) | Local |
| Last updated | 2026-11-13 |

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
| Fac 1 HCM (closed) (thêm 2026-11-13) | Xưởng 1 ở HCM đã giải thể, tên `SHCM-Factory 1` trong dữ liệu 2025; chỉ lưu để tham khảo, không hiện ở đâu (BR-98) |
| Chuyền | Chuyền may trong một xưởng, viết chuẩn là `LINE <số>`, ví dụ `LINE 1` |
| SMV | Số phút chuẩn để may một cái |
| CM / giá CM | Đơn giá gia công của một cái (USD) |
| Tiền CM | Sản lượng × giá CM (USD) |
| Số người | Số người của chuyền trong ngày, từ cột `REVISE MO` |
| Số thợ | Số thợ may trực tiếp của xưởng trong ngày, từ sheet `Worker` |
| Tổng nhân sự | Tổng số người của xưởng trong ngày (trực tiếp và gián tiếp), khối `TOTAL` của sheet `Worker` (thêm 2026-11-06) |
| %Direct labor | Số thợ / tổng nhân sự (BR-65) |
| Avg SMV | SMV bình quân theo sản lượng (BR-66) |
| Giờ làm | Số giờ làm trong ngày, từ cột `Revised OT 2` |
| MO | Tiền CM trên một người trong ngày (USD/người) |
| MO 8h | MO quy về 8 giờ làm: MO × 8 / giờ làm |
| Mục tiêu A | Tổng `Daily Target (SMV)` trong sheet `Target system` |
| Hiệu suất A | Sản lượng / mục tiêu A; dùng cho báo cáo tuần |
| Mục tiêu B | Tổng cột `Standard output of SMV (have efficiency ratio)` trong sheet `Production data` |
| Hiệu suất B | Sản lượng / mục tiêu B; dùng cho KPI xưởng |
| Trái sở trường | Dòng có `Expertise` = `Mismatched Strength` trong `Target system`, hoặc `Match line strength` = `Trái sở trường` trong `Production data` |
| Tỷ lệ đúng sở trường | Phần mục tiêu A không thuộc dòng trái sở trường (sửa 2026-11-13: nay là phần sản lượng đúng sở trường theo bảng sở trường chuyền, BR-86) |
| Đúng sở trường (theo bảng sở trường, thêm 2026-11-13) | Dòng sản lượng có nhóm sản phẩm nằm trong các nhóm hàng mạnh của chuyền trong file Line Strength (BR-86) |
| Mã hàng (khi đếm Changeover, thêm 2026-11-13) | Bộ ba Nhóm khách hàng + SMV + giá CM trên một chuyền (BR-87) |
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
| factory | list: Fac 1/Fac 2/Fac 3/Fac 5 (thêm 2026-11-13: Fac 1 HCM (closed), chỉ lưu, BR-98) | Yes | Xưởng, đổi từ `Factory` theo BR-06 | Fac 2 |
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
| standard_output_no_ratio | decimal ≥ 0 | No | Mục tiêu không tỉ lệ, từ `Standard output of SMV (no efficiency ratio)` (thêm 2026-11-05; dòng đã lưu trước đó để trống đến khi tải lại file) | 608.70 |
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
| derived (thêm 2026-11-13) | yes/no | Yes | Có khi số thợ do app tính từ file chỉ có `Production data` (BR-97): tổng số người các chuyền trong ngày. Dòng đã lưu trước đó: không | không |
| total_workers | decimal > 0 | No | Tổng nhân sự, từ khối `TOTAL` (thêm 2026-11-06; dòng đã lưu trước đó để trống đến khi tải lại file) | 1296 |

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
| status (thêm 2026-11-09) | Saved / Rejected | Yes | Lần tải đã lưu hay bị từ chối (BR-74). Dòng cũ: Saved | Saved |
| reject_reason (thêm 2026-11-09) | text | No | Lý do từ chối, đúng câu thông báo đã hiện cho người tải. Dòng cũ: trống | File thiếu sheet: Worker. Hãy dùng đúng file Data sewing. |
| sheet_counts (thêm 2026-11-09) | danh sách | No | Mỗi sheet một dòng: Sheet, Số dòng đọc được, Hợp lệ, Bỏ qua (BR-72). Dòng cũ: trống | Production data, 32051, 32050, 1 |
| changes (thêm 2026-11-09) | danh sách | No | Mỗi sheet và mỗi xưởng một dòng: Thêm mới, Cập nhật, Ẩn đi (BR-73). Dòng cũ: trống | Production data, Fac 2, 120, 3, 1 |
| skipped (thêm 2026-11-09) | danh sách | No | Các dòng bị bỏ qua: Sheet, Dòng, Lý do; giữ tối đa 1.000 dòng đầu (BR-72). Dòng cũ: trống | Production data, 32052, thiếu adj Date |
| warnings (thêm 2026-11-09) | danh sách | No | Các cảnh báo BR-08: Loại, Ngày, Số lượng (BR-72). Dòng cũ: trống | Ngày có sản lượng nhưng chưa có số thợ, 2026-11-05, 1 |
| has_details (thêm 2026-11-09) | yes/no | Yes | Có chi tiết hay không. Dòng cũ: không, các cột chi tiết hiện "-" | yes |

Từ ngày, đến ngày của lần tải bị từ chối có thể trống (file chưa đọc được ngày). (sửa 2026-11-09)

### 4.11 Sở trường chuyền (LineStrength) (thêm 2026-11-12)
Lấy từ file Line Strength (mục 5.1, BR-81). Duy nhất theo xưởng và chuyền. Tải file mới thì thay toàn bộ (BR-82).

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| factory | Fac 1 / Fac 2 / Fac 3 / Fac 5 | Yes | Từ cột `FAC`: XM1 = Fac 1, XM2 = Fac 2, XM3 = Fac 3, XM5 = Fac 5 | Fac 2 |
| line | text | Yes | Từ cột `LINE`, viết `LINE <số>` (BR-10) | LINE 14 |
| strong_groups | danh sách (tối đa 4) | No | Các ô `STRONG ITEM GROUP` 1 đến 4, theo thứ tự | Pants, Hoodie |
| buyers | text | No | `BUYER'S STRENGTH` | MCC, MARK'S WORK |
| changeover_speed | text | No | `CHANGEOVER SPEED` | Medium |
| remark | text | No | `REMARK` | May được váy |
| file_name | text | Yes | Tên file đã tải | Sewing Line Strength (14-Jul-2026).xlsx |

## 5. Input / output files (File nhập / xuất)
### 5.1 File dữ liệu (in)
- **Định dạng:** `.xlsx`, tối đa 50 MB, tối đa 200.000 dòng mỗi sheet. Ví dụ: `Data sewing 2026.xlsx`.
- **Đối chiếu tiêu đề:** không phân biệt hoa thường, dấu và khoảng trắng thừa. Các sheet và cột khác được bỏ qua.
- **File phải được lưu từ Excel** để có sẵn kết quả công thức.
- **File gốc không bị thay đổi.**

| Sheet | Dòng tiêu đề | Cột bắt buộc | Cột không bắt buộc |
|---|---|---|---|
| `Production data` | Dòng 2 | `adj Date`, `Factory` (cột đầu tiên có tên này), `Customer Name`, `Style`, `PO#`, `Line`, `Product Inline Quantiy` (chấp nhận thêm `Product Inline Quantity`), `Price`, `REVISE MO`, `Revised OT 2` | `Product Name`, `Color`, `SMV`, `Standard output of SMV (have efficiency ratio)`, `Standard output of SMV (no efficiency ratio)`, `Match line strength` |
| `Target system` | Dòng 1 | `Line`, `Daily Target (SMV)`, `Date` | `Items`, `Style`, `Daily Target (CM)`, `Expertise`, `PO` |
| `Worker` | Dòng 2 | Cột C (ngày, không có tiêu đề); cột đầu tiên có tiêu đề `SF2`, `SF3`, `SF5`, `SFVL` | Cột đầu tiên có tiêu đề `Fac.2`, `Fac.3`, `Fac.5`, `Fac.1(VL)` (khối `TOTAL`, tổng nhân sự; thêm 2026-11-06) |

Ví dụ dòng `Production data`: `2026-10-03 | SHCM-Factory 2 | MARK'S WORK | 2DIBDHAS-320D | XKA21-SX-EX-0726-6775.1 | LINE 1 | 700 | 0.75 | 24 | 9`.

Khi file sai: xem BR-01 đến BR-06. Dữ liệu đã lưu giữ nguyên khi file bị từ chối.

**File Line Strength (in, thêm 2026-11-12):** `.xlsx`, ví dụ `Sewing Line Strength (14-Jul-2026).xlsx`, tải ở cùng ô tải file của Screen 7; app nhận ra file này khi sheet đầu tiên có tiêu đề `FAC`, `LINE`, `STRONG ITEM GROUP` (BR-81). Tiêu đề ở dòng 1 (dòng 2 ghi số 1 đến 4 dưới `STRONG ITEM GROUP`), dữ liệu từ dòng 3. Cột: `FAC`, `LINE`, `STRONG ITEM GROUP` (4 cột liền nhau), `BUYER'S STRENGTH`, `CHANGEOVER SPEED`, `REMARK`. Bảng `Main Item Group` / `Items` bên phải không đọc: app dùng danh mục Nhóm sản phẩm (mục 4.6), có cùng nội dung. Không đọc dữ liệu nào từ file báo cáo họp tuần (chỉ để tham khảo cách trình bày).

### 5.2 File Excel xuất (out)
Định dạng chung theo BR-49.

| File | Direction | Format | Sheets và cột |
|---|---|---|---|
| `bao-cao-tuan_<từ ngày>_<đến ngày>.xlsx` | out | .xlsx | Sheet `Tong quan`: Chỉ số, Fac 1, Fac 2, Fac 3, Fac 5 (các chỉ số ở Screen 1, thêm dòng Đánh giá hiệu suất A, Đánh giá hiệu suất B, Đánh giá MO 8h). Sheet `Fac 1`, `Fac 2`, `Fac 3`, `Fac 5`: Chuyền, Ngày, Mục tiêu A, Sản lượng, Hiệu suất A (%), Mục tiêu B, Hiệu suất B (%), Tiền CM, Số người, Giờ làm, MO 8h, Đánh giá hiệu suất A, Đánh giá hiệu suất B, Đánh giá MO 8h |
| `bao-cao-ngay_<ngày>.xlsx` | out | .xlsx | Sheet `Xuong`: Chỉ số, Fac 1, Fac 2, Fac 3, Fac 5 (các chỉ số ở Screen 3, thêm dòng Đánh giá hiệu suất A, Đánh giá hiệu suất B, Đánh giá MO 8h). Sheet `Chuyen`: Xưởng, Chuyền, Sản lượng, Tiền CM, Giờ làm, Số người, MO, MO 8h, Sản lượng trái sở trường, Đánh giá MO 8h |
| `bao-cao-thang_<từ ngày>_<đến ngày>.xlsx` | out | .xlsx | Mỗi xưởng một sheet: Ngày, MO, Giờ làm, MO 8h, Mục tiêu B, Sản lượng, Hiệu suất B (%), Tiền CM, Số thợ, Đánh giá hiệu suất B, Đánh giá MO 8h; dòng cuối là Tổng (bỏ khỏi màn hình từ 2026-11-06, thay bằng file báo cáo theo kỳ) |
| `period-report_<loại kỳ>_<từ ngày>_<đến ngày>.xlsx` (bỏ từ 2026-11-06, chưa từng làm: Screen 4 không có nút tải) | out | .xlsx | Mỗi chỉ số của BR-69 một sheet (MO 8h, %Efficiency (with ratio), Direct worker, Output, Revenue, Avg CM price, Avg SMV, Avg working hours): cột Period, các xưởng đã chọn (Fac Vinh Long, Fac 2, Fac 3, Fac 5), HCM, Total |
| `mo-theo-chuyen_<xưởng>_<từ ngày>_<đến ngày>.xlsx` | out | .xlsx | Sheet `MO 8h`, `Tien CM`, `Gio lam`, `So nguoi`, `Hieu suat B`: Chuyền, các cột ngày, Cả kỳ; dòng cuối là Tổng |
| `doi-ma-hang_<từ ngày>_<đến ngày>.xlsx` | out | .xlsx | Sheet `Theo xuong`, `Theo thang`, `Theo chuyen`, `Chi tiet` theo các bảng ở Screen 6 |

## 6. Use cases (Nghiệp vụ) - each UC becomes ONE controller method + ONE service
### UC-01: Kiểm tra file dữ liệu
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Chọn file ở Screen 7 rồi bấm "Check & save" (sửa 2026-11-06: trước đây nút "Kiểm tra file", BR-57)
- **Preconditions:** Có vai trò `UPDATER`
- **Input:** File Excel
- **Main flow:**
  1. Kiểm tra định dạng, dung lượng, sheet, cột (BR-01 đến BR-04).
  2. Đọc 3 sheet, kiểm tra từng dòng (BR-05, BR-06, BR-16).
  3. Làm sạch dữ liệu (BR-10 đến BR-15).
  4. Tổng hợp cảnh báo (BR-08). Chưa lưu gì.
- **Output:** Số dòng đọc được, hợp lệ, bị bỏ qua; ngày đầu, ngày cuối; danh sách dòng bị bỏ qua và lý do; danh sách cảnh báo; so sánh số dòng với dữ liệu đang lưu trong cùng khoảng ngày.
- **Errors / alternative flows:** File sai thì hiện đúng thông báo của BR-01 đến BR-04, không có nút Lưu. (sửa 2026-11-09: file bị từ chối được ghi vào lịch sử tải file với trạng thái Rejected và lý do, BR-74; dữ liệu sản lượng vẫn không lưu gì)
- **Rules applied:** BR-01, BR-02, BR-03, BR-04, BR-05, BR-06, BR-08, BR-09, BR-10, BR-11, BR-12, BR-13, BR-14, BR-15, BR-16, BR-74, BR-97, BR-98 (thêm 2026-11-13: file năm cũ chỉ có `Production data`)

### UC-02: Lưu dữ liệu từ file
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Ngay sau UC-01 khi file không bị từ chối, trong cùng một lần bấm "Check & save" (sửa 2026-11-06: trước đây bấm "Lưu dữ liệu" rồi xác nhận, BR-57)
- **Preconditions:** File đã qua UC-01 và không bị từ chối
- **Input:** File đã kiểm tra
- **Main flow:**
  1. Kiểm tra lại như UC-01.
  2. Thay dữ liệu theo khoảng ngày của từng sheet (BR-07).
  3. Ghi lịch sử tải file. (sửa 2026-11-09: kèm chi tiết của lần tải theo BR-72, BR-73)
- **Output:** Thông báo "Đã lưu <số> dòng, dữ liệu đến ngày <ngày>." và bản ghi lịch sử mới.
- **Errors / alternative flows:** Lỗi như UC-01. Không đủ quyền thì hiện thông báo BR-09.
- **Rules applied:** BR-01, BR-02, BR-03, BR-04, BR-05, BR-06, BR-07, BR-09, BR-10, BR-11, BR-12, BR-13, BR-14, BR-15, BR-16, BR-72, BR-73, BR-97, BR-98 (thêm 2026-11-13: lưu file năm cũ, số thợ tính từ các chuyền)

### UC-03: Xem lịch sử tải file
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Mở Screen 7
- **Input:** Không
- **Main flow:**
  1. Lấy lịch sử, mới nhất lên đầu.
- **Output:** Danh sách lịch sử tải file. (sửa 2026-11-09: mỗi lần tải có trạng thái, tổng Thêm mới / Cập nhật / Ẩn đi và chi tiết của BR-72, BR-73, BR-74 để xem khi chọn một dòng)
- **Errors / alternative flows:** Chưa có lịch sử thì hiện "Chưa có lần tải file nào."
- **Rules applied:** BR-09, BR-72, BR-73, BR-74

### UC-04: Xem tổng quan xưởng
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở Screen 1 hoặc đổi bộ lọc
- **Input:** Từ ngày, đến ngày, xưởng, nhóm khách hàng, nhóm sản phẩm
- **Main flow:**
  1. Lấy dữ liệu theo bộ lọc (BR-29, BR-30).
  2. Tính các chỉ số cho từng xưởng (BR-17 đến BR-28, BR-38, BR-41).
- **Output:** Bảng chỉ số theo xưởng ở Screen 1, ghi chú nếu cách A chỉ tính từ một ngày nhất định.
- **Errors / alternative flows:** Khoảng ngày sai thì hiện thông báo BR-30. Không có dữ liệu thì hiện "Chưa có dữ liệu trong khoảng thời gian này."
- **Rules applied:** BR-17, BR-18, BR-19, BR-20, BR-23, BR-24, BR-25, BR-26, BR-27, BR-28, BR-29, BR-30, BR-38, BR-41, BR-50, BR-86 (thêm 2026-11-13: dòng "Line strength match")

### UC-05: Xem biểu đồ
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở Screen 1 hoặc đổi bộ lọc, đổi chỉ số xếp hạng
- **Input:** Bộ lọc của UC-04; chỉ số xếp hạng (Hiệu suất B/Hiệu suất A/MO 8h)
- **Main flow:**
  1. Tính dữ liệu từng biểu đồ (BR-18, BR-19, BR-22, BR-23, BR-44).
- **Output:** Hiệu suất A theo ngày của từng xưởng; hiệu suất B theo ngày của từng xưởng; MO 8h theo ngày của từng xưởng; sản lượng so với mục tiêu A giữa các xưởng; 10 chuyền cao nhất và 10 chuyền thấp nhất.
- **Errors / alternative flows:** Khi lọc khách hàng hoặc sản phẩm, biểu đồ hiệu suất A, MO 8h và mục tiêu A hiện "Không áp dụng khi lọc theo khách hàng hoặc sản phẩm." Không có dữ liệu thì hiện "Chưa có dữ liệu trong khoảng thời gian này."
- **Rules applied:** BR-18, BR-19, BR-22, BR-23, BR-29, BR-30, BR-44
- **Sửa 2026-11-13 lần 4:** bỏ biểu đồ "Output vs Target (with ratio - system) by factory" và phần xếp hạng chuyền (BR-44 bỏ khỏi màn hình, BR-92); thêm khu "Products & customers": cơ cấu hàng theo xưởng (BR-93), top khách hàng (BR-94), giá CM trung bình theo nhóm hàng (BR-95), cơ cấu hàng theo tháng (BR-96). Rules applied thêm: BR-92 đến BR-96.

### UC-06: Xem chi tiết chuyền
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở Screen 2 hoặc đổi bộ lọc
- **Input:** Từ ngày, đến ngày, xưởng, chuyền, nhóm khách hàng, nhóm sản phẩm
- **Main flow:**
  1. Tính từng chuyền theo từng ngày và cả kỳ (BR-17 đến BR-22, BR-27, BR-28).
  2. Tính dòng Tổng của xưởng.
  3. (thêm 2026-11-12) Tính bảng chuyền mới của Screen 2 (BR-83) và chi tiết từng chuyền: sở trường, đơn hàng trong kỳ (BR-84).
- **Output:** Bảng chuyền theo ngày, dòng Cả kỳ của từng chuyền, dòng Tổng xưởng; số thợ và giờ làm của xưởng theo ngày. (sửa 2026-11-12: Screen 2 chỉ hiện bảng chuyền của BR-83 và chi tiết chuyền đã chọn của BR-84; bảng chuyền theo ngày bỏ khỏi màn hình) (sửa 2026-11-13: bảng chuyền thêm %Efficiency (with ratio), Matching ratio theo BR-86, Changeover theo BR-87; bảng đơn hàng thêm SMV và %Efficiency (with ratio) theo BR-88) (sửa 2026-11-13 lần 2: chi tiết chuyền thêm "Line trend" theo tuần / tháng / năm, BR-90)
- **Errors / alternative flows:** Như UC-04.
- **Rules applied:** BR-12, BR-17, BR-18, BR-19, BR-20, BR-21, BR-22, BR-23, BR-26, BR-27, BR-28, BR-29, BR-30, BR-43, BR-50, BR-68, BR-83, BR-84, BR-86, BR-87, BR-88, BR-90

### UC-07: Xem báo cáo ngày (bỏ khỏi màn hình từ 2026-11-12: Screen 3 bỏ khỏi menu)
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở Screen 3 hoặc đổi ngày, đổi xưởng
- **Input:** Ngày; xưởng cho bảng chuyền
- **Main flow:**
  1. Tính chỉ số theo xưởng trong ngày (BR-17 đến BR-20, BR-23, BR-25, BR-42).
  2. Tính bảng chuyền của xưởng đã chọn (BR-21, BR-22, BR-43).
- **Output:** Bảng chỉ số theo xưởng và bảng chuyền ở Screen 3.
- **Errors / alternative flows:** Ngày không có dữ liệu thì hiện "Chưa có dữ liệu của ngày này."
- **Rules applied:** BR-17, BR-18, BR-19, BR-20, BR-21, BR-22, BR-23, BR-25, BR-26, BR-27, BR-28, BR-42, BR-43, BR-50

### UC-08: Xem báo cáo tháng (bỏ khỏi màn hình từ 2026-11-06, thay bằng UC-29)
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở Screen 4 hoặc đổi bộ lọc
- **Input:** Từ ngày, đến ngày, xưởng
- **Main flow:**
  1. Tính từng xưởng theo ngày (BR-17, BR-19, BR-20, BR-23).
  2. Tính dòng Tổng (BR-48).
- **Output:** Bảng theo ngày và dòng Tổng của từng xưởng.
- **Errors / alternative flows:** Như UC-04.
- **Rules applied:** BR-17, BR-19, BR-20, BR-23, BR-26, BR-28, BR-30, BR-48, BR-50

### UC-09: Xem MO theo chuyền (bỏ khỏi màn hình từ 2026-11-12: Screen 5 bỏ khỏi menu)
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở Screen 5 hoặc đổi bộ lọc
- **Input:** Từ ngày, đến ngày, một xưởng, chuyền
- **Main flow:**
  1. Tính MO 8h, tiền CM, giờ làm, số người, hiệu suất B theo chuyền và ngày (BR-17, BR-19, BR-20, BR-21, BR-22).
  2. Tính cột Cả kỳ và dòng Tổng (BR-48).
- **Output:** 5 bảng chuyền theo ngày ở Screen 5.
- **Errors / alternative flows:** Như UC-04.
- **Rules applied:** BR-17, BR-19, BR-20, BR-21, BR-22, BR-26, BR-28, BR-30, BR-48, BR-50

### UC-31: Xem hiệu quả theo chuyền (thêm 2026-11-11, thay UC-10 ở Screen 6; bỏ khỏi màn hình từ 2026-11-13: Screen 6 bỏ khỏi menu, bảng không còn hiện, chỉ còn file tải ở Screen 2 qua UC-32)
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở Screen 6 hoặc đổi bộ lọc
- **Input:** Từ ngày, đến ngày, một xưởng
- **Main flow:**
  1. Kiểm tra khoảng ngày (BR-30).
  2. Tính từng chuyền của xưởng (BR-78) và dòng Total (BR-79).
  3. Đánh dấu dưới ngưỡng (BR-80).
- **Output:** Bảng Line performance của Screen 6.
- **Errors / alternative flows:** Khoảng ngày sai thì hiện thông báo BR-30. Không có dữ liệu thì hiện "Chưa có dữ liệu trong khoảng thời gian này."
- **Rules applied:** BR-11, BR-17, BR-19, BR-21, BR-22, BR-23, BR-26, BR-28, BR-30, BR-50, BR-75, BR-78, BR-79, BR-80

### UC-33: Lưu sở trường chuyền từ file (thêm 2026-11-12)
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Chọn file Line Strength ở Screen 7 rồi bấm "Check & save" (cùng nút với file dữ liệu, BR-57)
- **Preconditions:** Có vai trò `UPDATER`
- **Input:** File Line Strength
- **Main flow:**
  1. Kiểm tra file (BR-01, BR-81).
  2. Đọc từng dòng, đổi mã xưởng, chuẩn hoá tên chuyền (BR-81, BR-10).
  3. Thay sở trường đang có (BR-82); ghi lịch sử tải file (BR-72, BR-74).
- **Output:** Thông báo "Đã lưu sở trường của <số> chuyền." và dòng lịch sử mới.
- **Errors / alternative flows:** File sai thì hiện thông báo BR-01 hoặc BR-81, không lưu gì, lịch sử ghi Rejected. Không đủ quyền thì hiện thông báo BR-09.
- **Rules applied:** BR-01, BR-09, BR-10, BR-72, BR-74, BR-81, BR-82

### UC-34: Xem sở trường chuyền (thêm 2026-11-12)
- **Actor:** Người cập nhật dữ liệu
- **Trigger:** Mở thẻ "Line strength" ở Screen 9
- **Input:** Không
- **Main flow:** Lấy sở trường đang có, sắp theo xưởng rồi số chuyền.
- **Output:** Bảng chỉ xem: Factory, Line, Strong item group 1 đến 4, Buyer's strength, Changeover speed, Remark; tên file và thời điểm tải.
- **Errors / alternative flows:** Chưa tải file thì hiện "Chưa có sở trường chuyền. Hãy tải file Line Strength ở màn hình Data Update."
- **Rules applied:** BR-09

### UC-32: Tải Excel hiệu quả theo chuyền (bỏ từ 2026-11-11 theo yêu cầu người dùng khi chốt; làm lại từ 2026-11-12 theo yêu cầu mới: nút "Download Excel" ở Screen 6, file theo BR-85)
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Bấm "Download Excel" ở Screen 6 (sửa 2026-11-13: bấm "Download Line performance" ở Screen 2 Line Detail)
- **Input:** Bộ lọc của UC-31 (sửa 2026-11-13: Từ ngày, đến ngày đang chọn ở Screen 2; các bộ lọc khác của Screen 2 không áp dụng cho file)
- **Main flow:**
  1. Tính như UC-31.
  2. Ghi file theo BR-85. (sửa 2026-11-12: trước đây tiêu đề gộp một tầng)
- **Output:** File `Line performance - <xưởng> - <dd.mm> to <dd.mm>.xlsx`. (sửa 2026-11-12) (sửa 2026-11-13: file `Line performance - <dd.mm> to <dd.mm>.xlsx`, 4 sheet cho 4 xưởng, BR-85)
- **Errors / alternative flows:** Khoảng ngày sai thì hiện thông báo BR-30, không tải.
- **Rules applied:** BR-30, BR-49, BR-50, BR-78, BR-79, BR-80

### UC-10: Xem đổi mã hàng (bỏ khỏi màn hình từ 2026-11-11, thay bằng UC-31)
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
- **Trigger:** Bấm "Tải Excel báo cáo tuần" ở Screen 1 hoặc Screen 2 (sửa 2026-11-13: chỉ còn ở Screen 1; Screen 2 bỏ nút này)
- **Input:** Bộ lọc đang chọn của màn hình
- **Main flow:**
  1. Tính như UC-04 và UC-06.
  2. Tạo file theo mục 5.2.
- **Output:** File `bao-cao-tuan_<từ ngày>_<đến ngày>.xlsx`.
- **Errors / alternative flows:** Khoảng ngày sai thì hiện thông báo BR-30.
- **Rules applied:** BR-28, BR-29, BR-30, BR-49, BR-50

### UC-12: Tải Excel báo cáo ngày (bỏ khỏi màn hình từ 2026-11-12)
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Bấm "Tải Excel" ở Screen 3
- **Input:** Ngày
- **Main flow:**
  1. Tính như UC-07 cho cả 4 xưởng.
  2. Tạo file theo mục 5.2.
- **Output:** File `bao-cao-ngay_<ngày>.xlsx`.
- **Errors / alternative flows:** Không có.
- **Rules applied:** BR-28, BR-49, BR-50

### UC-13: Tải Excel báo cáo tháng (bỏ khỏi màn hình từ 2026-11-06, thay bằng UC-30)
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Bấm "Tải Excel" ở Screen 4
- **Input:** Bộ lọc của UC-08
- **Main flow:**
  1. Tính như UC-08.
  2. Tạo file theo mục 5.2.
- **Output:** File `bao-cao-thang_<từ ngày>_<đến ngày>.xlsx`.
- **Errors / alternative flows:** Khoảng ngày sai thì hiện thông báo BR-30.
- **Rules applied:** BR-28, BR-30, BR-49, BR-50

### UC-14: Tải Excel MO theo chuyền (bỏ khỏi màn hình từ 2026-11-12)
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Bấm "Tải Excel" ở Screen 5
- **Input:** Bộ lọc của UC-09
- **Main flow:**
  1. Tính như UC-09.
  2. Tạo file theo mục 5.2.
- **Output:** File `mo-theo-chuyen_<xưởng>_<từ ngày>_<đến ngày>.xlsx`.
- **Errors / alternative flows:** Khoảng ngày sai thì hiện thông báo BR-30.
- **Rules applied:** BR-30, BR-49, BR-50

### UC-15: Tải Excel đổi mã hàng (bỏ khỏi màn hình từ 2026-11-11, thay bằng UC-32)
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

### UC-27: Xem cột tổng hợp HCM (thêm 2026-11-05)
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Xem Screen 1, Screen 3, hoặc tải Excel của hai màn hình đó
- **Input:** Như UC-04, UC-05, UC-07
- **Main flow:**
  1. Lấy các xưởng HCM đã chọn trong Fac 2, Fac 3, Fac 5.
  2. Tính cột HCM theo BR-51.
  3. Hiện cột HCM cạnh các xưởng, thêm đường HCM vào biểu đồ theo ngày và cột HCM vào biểu đồ sản lượng.
- **Output:** Cột HCM trong bảng chỉ số và file Excel; đường và cột HCM trong biểu đồ; khối Summary ở Screen 1. (sửa 2026-11-06: khối card Vinh Long - HCM có 7 card, thêm Avg SMV và %Direct labor, BR-58, BR-65, BR-66)
- **Errors / alternative flows:** Chọn ít hơn 2 xưởng HCM thì không hiện HCM.
- **Rules applied:** BR-51, BR-54, BR-58, BR-65, BR-66

### UC-28: Tải Excel báo cáo tuần theo mẫu họp (thêm 2026-11-06; làm bằng cùng nút và cùng chức năng tải của UC-11, chọn mẫu họp)
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Bấm "Download weekly report (Excel)" ở Screen 1 hoặc Screen 2 (thay UC-11 trên màn hình)
- **Input:** Bộ lọc của màn hình đó (khoảng ngày, xưởng, nhóm khách hàng, nhóm sản phẩm)
- **Main flow:**
  1. Kiểm tra khoảng ngày (BR-30).
  2. Tính số của từng xưởng, HCM, từng chuyền và từng ngày như Screen 1 và Screen 2.
  3. Ghi file theo BR-64.
- **Output:** File `Sewing - Weekly Fac report - <dd.mm> to <dd.mm>.xlsx`.
- **Errors / alternative flows:** Khoảng ngày sai thì hiện thông báo BR-30, không tải.
- **Rules applied:** BR-17 đến BR-30, BR-38, BR-41, BR-51, BR-64

### UC-29: Xem báo cáo theo kỳ (thêm 2026-11-06, thay UC-08 ở Screen 4)
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Mở Screen 4 hoặc đổi bộ lọc
- **Input:** Loại kỳ (By week / By month / By quarter / By year), từ ngày, đến ngày, xưởng
- **Main flow:**
  1. Kiểm tra khoảng ngày (BR-30).
  2. Chia khoảng ngày thành các kỳ (BR-68).
  3. Tính các chỉ số của từng kỳ cho từng xưởng, HCM và Total (BR-69).
- **Output:** Mỗi chỉ số một bảng: mỗi dòng một kỳ, mỗi cột một xưởng, HCM, Total; biểu đồ đường theo kỳ. (sửa 2026-11-08: thêm, cho mỗi chỉ số và mỗi cột, thẻ số của kỳ cuối với mức thay đổi so với kỳ trước theo BR-71, màu mũi tên theo BR-70; biểu đồ là một biểu đồ nhỏ cho mỗi cột, gồm cả HCM và Total) (sửa 2026-11-13: thêm 2 chỉ số Matching strength và Changeover/line/day theo BR-89, thành 10 chỉ số)
- **Errors / alternative flows:** Khoảng ngày sai thì hiện thông báo BR-30. Không có dữ liệu thì hiện "Chưa có dữ liệu trong khoảng thời gian này."
- **Rules applied:** BR-19, BR-20, BR-23, BR-24, BR-26, BR-28, BR-30, BR-50, BR-51, BR-66, BR-68, BR-69, BR-70, BR-71, BR-86, BR-87, BR-89

### UC-30: Tải Excel báo cáo theo kỳ (bỏ từ 2026-11-06 theo yêu cầu người dùng, chưa từng làm: Screen 4 chỉ hiển thị, không có nút tải)
- **Actor:** Người xem, Người cập nhật dữ liệu
- **Trigger:** Bấm "Tải Excel" ở Screen 4
- **Input:** Bộ lọc của UC-29
- **Main flow:**
  1. Tính như UC-29.
  2. Ghi file, mỗi chỉ số một sheet (BR-49).
- **Output:** File `period-report_<by week|by month|by quarter|by year>_<từ ngày>_<đến ngày>.xlsx`.
- **Errors / alternative flows:** Khoảng ngày sai thì hiện thông báo BR-30, không tải.
- **Rules applied:** BR-30, BR-49, BR-50, BR-68, BR-69

## 7. Business rules (Quy tắc nghiệp vụ)
| ID | Rule | Error message shown to user (VI) |
|---|---|---|
| BR-01 | File phải là .xlsx, không quá 50 MB, mỗi sheet không quá 200.000 dòng | File phải có định dạng .xlsx, không quá 50 MB và mỗi sheet không quá 200.000 dòng. Hãy kiểm tra lại rồi tải lên. |
| BR-02 | File phải có đủ 3 sheet `Production data`, `Target system`, `Worker` (sửa 2026-11-13: trừ file năm cũ chỉ có `Production data`, mọi ngày trước 01/01/2026, BR-97) | File thiếu sheet: <tên sheet>. Hãy dùng đúng file Data sewing. |
| BR-03 | Mỗi sheet phải có đủ cột bắt buộc ở mục 5.1 | Sheet <tên sheet> thiếu cột: <tên cột>. Hãy kiểm tra dòng tiêu đề của sheet. |
| BR-04 | `Production data` phải có ít nhất 1 dòng hợp lệ và có ít nhất một ô mục tiêu B có giá trị | File chưa có kết quả công thức. Hãy mở file bằng Excel, lưu lại rồi tải lên. |
| BR-05 | Dòng sản lượng hợp lệ khi có ngày đúng định dạng, xưởng, khách hàng, style, mã đơn, chuyền; sản lượng là số ≥ 0; giá CM, số người, giờ làm là số > 0. Dòng sai bị bỏ qua và được liệt kê | Dòng <số dòng>: thiếu hoặc sai <tên cột>. |
| BR-06 | Xưởng được đổi tên: `SVL-Factory 2` = Fac 1, `SHCM-Factory 2` = Fac 2, `SHCM-Factory 3` = Fac 3, `SHCM-Factory 5` = Fac 5. Tên khác bị bỏ qua và được liệt kê (sửa 2026-11-13: thêm `SHCM-Factory 1` = Fac 1 HCM (closed), chỉ lưu, BR-98) | Dòng <số dòng>: chưa nhận diện được xưởng "<tên>". |
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
| BR-25 | Tỷ lệ đúng sở trường = 1 − tổng mục tiêu A dòng trái sở trường / tổng mục tiêu A. Không có mục tiêu A thì hiện "-". (sửa 2026-11-13 theo yêu cầu người dùng: nay tính theo BR-86 từ bảng sở trường chuyền, ở dòng "Line strength match" của Screen 1, file báo cáo tuần và dòng Matching ratio của file mẫu họp; trước đây theo mục tiêu A và cột `Expertise`) | - |
| BR-26 | Mức mục tiêu, ngưỡng của một ngày là mức có ngày hiệu lực gần nhất, không sau ngày đó. Số của một ngày so với mức của ngày đó. Số cả kỳ so với mức của ngày cuối kỳ | - |
| BR-27 | % so với mục tiêu = thực tế / mục tiêu. Áp cho hiệu suất A, hiệu suất B, MO 8h | - |
| BR-28 | Hiệu suất dưới ngưỡng hiệu suất hoặc MO 8h dưới ngưỡng MO 8h thì đánh giá "Dưới ngưỡng" và hiện dấu 🔴 cạnh con số; bằng hoặc trên ngưỡng thì "Đạt"; số "-" thì đánh giá "-". Áp cho cả hiệu suất A và B, ở cấp chuyền và cấp xưởng | - |
| BR-29 | Khi lọc khách hàng hoặc sản phẩm: sản lượng, tiền CM, giá CM trung bình, mục tiêu B và hiệu suất B lọc theo lựa chọn; mục tiêu A, hiệu suất A, MO, MO 8h, số người, số thợ, tỷ lệ đúng sở trường hiện "-". (sửa 2026-11-13: tỷ lệ đúng sở trường nay theo sản lượng (BR-86) nên lọc theo lựa chọn như sản lượng, không còn hiện "-") | - |
| BR-30 | Từ ngày phải không sau đến ngày | Từ ngày không được sau đến ngày. Hãy chọn lại khoảng thời gian. |
| BR-31 | Thời gian mặc định: Screen 1, 2 lấy tuần thứ Bảy đến thứ Sáu đầy đủ gần nhất, có thứ Sáu không sau ngày dữ liệu mới nhất; Screen 3 lấy ngày dữ liệu mới nhất; Screen 4, 5, 6 lấy từ ngày 1 của tháng có dữ liệu mới nhất đến ngày dữ liệu mới nhất. (sửa 2026-11-06: Screen 4 lấy từ ngày 1/1 của năm có dữ liệu mới nhất đến ngày dữ liệu mới nhất, loại kỳ mặc định By week. Sửa 2026-11-11: Screen 6 lấy tuần thứ Bảy đến thứ Sáu đầy đủ gần nhất như Screen 1) | - |
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
| BR-51 | Cột HCM (thêm 2026-11-05) gộp Fac 2, Fac 3, Fac 5 đã chọn như một xưởng, tính lại từ các con số tổng, không lấy trung bình các tỷ lệ: mục tiêu, sản lượng, tiền CM là tổng; hiệu suất = tổng sản lượng / tổng mục tiêu; MO 8h = tổng tiền CM × 8 / (tổng số thợ × giờ làm trung bình), chỉ trên các ngày của xưởng có số thợ; giờ làm là trung bình các ngày của từng xưởng. Mục tiêu và ngưỡng của HCM là mức chung khi cả 3 xưởng cùng mức, nếu khác nhau thì hiện "-". Số đổi mã hàng tuần chỉ có khi mọi xưởng đã chọn đều có số. Chỉ hiện khi chọn từ 2 xưởng HCM trở lên | - |
| BR-52 | Tên trên màn hình và trong file Excel bằng tiếng Anh (thêm 2026-11-05): tên ứng dụng "Sewing Performance", "Đổi mã hàng" thành "Changeover", "Hiệu suất" thành "%Efficiency" theo BR-56, Fac 1 hiển thị là "Fac Vinh Long". Dữ liệu đã lưu không đổi, vẫn ghi Fac 1. Các câu thông báo do hệ thống kiểm tra trả về vẫn bằng tiếng Việt, chỉ đổi các tên trên trong câu | - |
| BR-53 | Hàng và cột của 3 loại %Efficiency (BR-56) và MO 8h trong bảng trên màn hình được in đậm (thêm 2026-11-05) | - |
| BR-54 | Biểu đồ có nhãn số (thêm 2026-11-05): biểu đồ theo ngày ghi số cả kỳ cạnh tên xưởng ở chú thích; biểu đồ sản lượng ghi sản lượng / mục tiêu A dưới tên xưởng; biểu đồ xếp hạng là cột ngang, ghi số cạnh tên chuyền. Screen 1 có bảng Summary với Output, 3 loại %Efficiency, MO 8h của Fac Vinh Long và HCM | - |
| BR-55 | Hiệu suất không tỉ lệ (thêm 2026-11-05) = tổng sản lượng / tổng cột `Standard output of SMV (no efficiency ratio)`, bỏ các dòng thiếu cột này khỏi cả tử số và mẫu số, không còn dòng nào thì hiện "-". Cách tính theo chuyền, ngày, xưởng, HCM và bộ lọc khách hàng, sản phẩm giống hiệu suất B của BR-19. Không so với mục tiêu và ngưỡng, không có dấu 🔴 | - |
| BR-56 | Tên 3 loại hiệu suất (thêm 2026-11-05): nhóm có tỉ lệ gồm "%Efficiency (with ratio - system)" là hiệu suất A của BR-18, mục tiêu lấy từ sheet `Target system`, và "%Efficiency (with ratio - sum)" là hiệu suất B của BR-19, mục tiêu là tổng cột `have efficiency ratio`; loại không tỉ lệ là "%Efficiency B (no ratio)" của BR-55. Trong tài liệu này, "hiệu suất A" và "hiệu suất B" vẫn theo nghĩa BR-18, BR-19. (sửa 2026-11-06: trước đây "%Efficiency (with ratio - sum)" và "Target (with ratio - sum)"; nay là "%Efficiency (with ratio)" và "Target (with ratio)" ở màn hình, biểu đồ và Excel. Sửa 2026-11-06 lần 2: "%Efficiency B (no ratio)" và "Target B (no ratio)" nay là "%Efficiency (no ratio)" và "Target (no ratio)") | - |
| BR-57 | Tải file bằng một nút "Check & save" (thêm 2026-11-06): file qua kiểm tra BR-01 đến BR-05 thì lưu ngay, không hỏi lại; các dòng bị bỏ qua không được lưu và được liệt kê sau khi lưu. File bị từ chối thì không lưu gì và hiện lý do | - |
| BR-58 | Khu vực "Vinh Long - HCM" ở Screen 1 (thêm 2026-11-06, thay bảng Summary của BR-54): 5 card Revenue (tiền CM), Output, Avg CM price (Revenue / Output, BR-24), MO 8h, %Efficiency (with ratio - sum). Mỗi card ghi số Total lớn, dưới là Fac Vinh Long và HCM. Total gộp mọi xưởng đã chọn, tính từ số tổng như BR-51; không có mức mục tiêu chung nên Total không có dấu 🔴. (sửa 2026-11-06: các card cao bằng nhau; mỗi card có màu, biểu tượng và đơn vị riêng: Revenue (USD) xanh lá, Output (pcs) xanh dương, Avg CM price (USD/pc) tím, MO 8h (USD) cam, %Efficiency đỏ; dưới số Total có cột nhỏ so sánh Vinh Long và HCM; Revenue và Output không có số lẻ, các số khác giữ số lẻ của BR-50. Sửa 2026-11-06 lần 3: 7 card trên một hàng theo thứ tự Revenue, Output, Avg CM price, Avg SMV, MO 8h, %Efficiency, %Direct labor; thêm Avg SMV (min) màu xanh ngọc theo BR-66 và %Direct labor (%) màu xám xanh theo BR-65, cùng kiểu Total, Vinh Long, HCM, thanh so sánh và nút ＋ của BR-60; tên card, số Total và các dòng xưởng thẳng hàng giữa các card) | - |
| BR-59 | Bảng chỉ số ở Screen 1 (thêm 2026-11-06): mặc định ẩn 3 dòng của loại with ratio - system (Target, %Efficiency, % so với mục tiêu); nút gạt "Show %Efficiency (with ratio - system)" ở đầu bảng mở lại, app nhớ lựa chọn trong phiên làm việc. File Excel không đổi. (sửa 2026-11-06: nay theo BR-61, nút gạt mở cả các dòng target) | - |
| BR-60 | Card "Vinh Long - HCM" (thêm 2026-11-06): một nút ＋ ở đầu khu card. Bật lên thì dưới dòng HCM của cả 5 card hiện thêm Fac 2, Fac 3, Fac 5 đã chọn, mỗi dòng có thanh so sánh với dòng lớn nhất của card; tắt thì chỉ còn Vinh Long và HCM. App nhớ lựa chọn trong phiên làm việc | - |
| BR-61 | Bảng chỉ số ở Screen 1 (thêm 2026-11-06): thứ tự dòng Target (with ratio), Output, %Efficiency (with ratio), %Efficiency (with ratio) vs target, Target B (no ratio), %Efficiency B (no ratio), CM earning, MO 8h, Average CM price, Average working hours, Line strength match, Weekly changeover, Weekly changeover per line. Mặc định ẩn %Efficiency target, MO 8h target, MO 8h vs target và 3 dòng with ratio - system; nút gạt "Show targets & with ratio - system" hiện lại tất cả, mỗi dòng nằm đúng nhóm. Cột Category bên trái có nhãn màu theo nhóm Output, Efficiency, CM, MO 8h, Other. Bảng ở Screen 3 và file Excel giữ thứ tự cũ. (sửa 2026-11-06 lần 2: Target (no ratio) và %Efficiency (no ratio) cũng ẩn mặc định, hiện cùng nút gạt; mặc định còn 11 dòng. Sửa 2026-11-06 lần 3: "%Efficiency (with ratio) vs target" cũng ẩn mặc định, hiện cùng nút gạt; mặc định còn 10 dòng) | - |
| BR-64 | File báo cáo tuần theo mẫu họp (thêm 2026-11-06, UC-28), giống file `Sewing - Weekly Fac report - 24.10 to 30.10.xlsx`. Sheet `Overall`: tiêu đề đỏ "Sewing Weekly performance (<dd.mm> to <dd.mm>)"; cột Category và cột xưởng Fac Vinh Long, Fac 2, Fac 3, Fac 5, HCM; dòng Efficiency Target / Actual = mục tiêu A / sản lượng; Efficiency Target / Actual / % = mục tiêu hiệu suất / hiệu suất A / % so với mục tiêu; CM earning; MO 8h Target / Actual / %; Average CM price; Avg working time; Matching ratio; Changeover time (BR-38) và dòng dưới là số lần trên chuyền (BR-41); xưởng không chọn hoặc không có số ghi "-". Màu như file mẫu: Category vàng, tiêu đề xanh nhạt, dòng % chữ đỏ; tiền định dạng $, hiệu suất định dạng %. Sheet `<xưởng>-detailed` cho mỗi xưởng đã chọn: Start of week (Day, Month, Year); khối Output (pcs) mỗi chuyền mỗi ngày Target (mục tiêu A) / Actual / Efficiency, cột Target, Total, Efficiency cả kỳ, dòng Total xưởng, dòng MO 8h xưởng theo ngày; khối Earning ($) chuyền × ngày với dòng Total, LABOR (số thợ), HOUR (giờ làm); khối MO 8h ($/8h) chuyền × ngày với dòng Total. Ghi số, không ghi công thức | - |
| BR-65 | %Direct labor (thêm 2026-11-06) = tổng số thợ / tổng nhân sự, cộng dồn các ngày trong khoảng đã chọn, chỉ tính các ngày có cả hai số. Total gộp mọi xưởng đã chọn, HCM gộp Fac 2, Fac 3, Fac 5 đã chọn, đều tính từ số tổng như BR-51. Không có ngày nào đủ hai số thì hiện "-". Khi lọc nhóm khách hàng hoặc nhóm sản phẩm thì hiện "-" như số thợ ở BR-29. Hiện 1 chữ số lẻ, không có mục tiêu và dấu 🔴 | - |
| BR-66 | Avg SMV (thêm 2026-11-06) = tổng (SMV × sản lượng) / tổng sản lượng của các dòng có SMV, bỏ dòng thiếu SMV khỏi cả tử số và mẫu số. Total, HCM tính từ số tổng như BR-51. Lọc theo nhóm khách hàng, nhóm sản phẩm như sản lượng. Không còn dòng nào thì hiện "-". Hiện 2 chữ số lẻ (phút), không có mục tiêu và dấu 🔴 | - |
| BR-68 | Kỳ của Screen 4 (thêm 2026-11-06): By week là tuần thứ Bảy đến thứ Sáu, tên "W<số tuần> (<dd.mm>–<dd.mm>)", số tuần là số tuần ISO của ngày thứ Sáu cuối tuần (ví dụ W43 (17.10–23.10)); By month là tháng dương lịch, tên "<Tháng tiếng Anh viết tắt> <năm>"; By quarter là quý dương lịch (Q1 = tháng 1–3), tên "Q<số> <năm>"; By year là năm dương lịch. Kỳ ở đầu hoặc cuối khoảng ngày chỉ tính các ngày nằm trong khoảng và tên ghi thêm ngày thật, ví dụ "Oct 2026 (01.10–23.10)". Kỳ không có sản lượng thì không hiện | - |
| BR-69 | Chỉ số của một kỳ (thêm 2026-11-06), tính như Screen 1 trên các ngày của kỳ, cộng số tổng rồi mới chia: MO 8h (BR-23, BR-51); %Efficiency (with ratio) là hiệu suất B (BR-19); Direct worker = số thợ trung bình mỗi ngày của xưởng (tổng số thợ các ngày có số / số ngày đó), HCM và Total là tổng Direct worker của các xưởng trong nhóm; Output; Revenue (tiền CM); Avg CM price (BR-24); Avg SMV (BR-66); Avg working hours (BR-20). Dấu 🔴 theo BR-28 cho MO 8h và %Efficiency, so với mức của ngày cuối kỳ (BR-26); HCM và Total chỉ có dấu khi các xưởng cùng mức (BR-51). (sửa 2026-11-13: thêm Matching strength và Changeover/line/day theo BR-89, đứng sau Avg working hours) | - |
| BR-67 | Screen 1 không còn biểu đồ "%Efficiency (no ratio) by day" và "%Efficiency (with ratio - system) by day" (thêm 2026-11-06). Các biểu đồ khác và các lựa chọn của xếp hạng chuyền giữ nguyên | - |
| BR-72 | Chi tiết một lần tải đã lưu (thêm 2026-11-09): mỗi sheet `Production data`, `Target system`, `Worker` ghi số dòng đọc được, hợp lệ, bị bỏ qua; danh sách dòng bị bỏ qua (Sheet, Dòng, Lý do), giữ tối đa 1.000 dòng đầu, tổng số vẫn đúng; danh sách cảnh báo BR-08 (Loại, Ngày, Số lượng) như đã hiện sau khi lưu. Không giữ file gốc | - |
| BR-73 | Thay đổi của một lần tải (thêm 2026-11-09), đếm theo sheet và theo xưởng khi lưu theo BR-07: Thêm mới = dòng chưa có trong dữ liệu đang hiện (kể cả dòng trước đây đã ẩn nay có lại); Cập nhật = dòng đang có mà nội dung đổi; Ẩn đi = dòng đang có trong khoảng ngày của sheet mà file không còn (được đánh dấu xoá, không mất). Dòng giống hệt không tính | - |
| BR-74 | Lần tải bị từ chối (thêm 2026-11-09): khi file bị từ chối theo BR-01 đến BR-04, hoặc không lưu được, app vẫn ghi một dòng lịch sử: thời điểm, người tải, tên file, trạng thái Rejected, lý do (đúng câu đã hiện), không lưu dữ liệu nào. Người chưa có quyền (BR-09) bị chặn trước, không ghi. Lần tải bị từ chối không tính là "Last file upload" của các báo cáo | - |
| BR-81 | File Line Strength (thêm 2026-11-12): .xlsx theo BR-01; sheet đầu tiên có tiêu đề `FAC`, `LINE`, `STRONG ITEM GROUP`, `BUYER'S STRENGTH`, `CHANGEOVER SPEED`, `REMARK` (không phân biệt hoa thường, khoảng trắng). Mã xưởng XM1 = Fac 1, XM2 = Fac 2, XM3 = Fac 3, XM5 = Fac 5; mã khác bị bỏ qua và được liệt kê. Chuyền là số, ghi `LINE <số>`. Dòng không có FAC và LINE bị bỏ qua không báo. Trùng xưởng và chuyền thì lấy dòng đầu tiên, các dòng sau được liệt kê | File Line Strength thiếu cột: <tên cột>. Hãy dùng đúng file Sewing Line Strength. / Dòng <số dòng>: chưa nhận diện được xưởng "<mã>". |
| BR-82 | Lưu sở trường (thêm 2026-11-12): file mới thay toàn bộ sở trường đang có; chuyền cùng xưởng và số được cập nhật, chuyền không còn trong file được đánh dấu xoá (không mất). Lịch sử tải file ghi một dòng (BR-72): sheet `Line Strength`, số dòng đọc được, hợp lệ, bỏ qua; số chuyền thêm mới, cập nhật, ẩn đi theo xưởng (BR-73) | - |
| BR-83 | Bảng chuyền của Screen 2 (thêm 2026-11-12), mỗi dòng một chuyền trên các ngày trong khoảng đã chọn, sắp theo số chuyền, dòng cuối Total: Output = tổng sản lượng; MO 8h = trung bình MO 8h các ngày của chuyền (BR-22); Working hours = trung bình giờ làm các ngày của chuyền (BR-20); Matching ratio = sản lượng các dòng không phải `Trái sở trường` / tổng sản lượng (%), theo cột `Match line strength` (BR-43); Changeover = số mã đơn gốc (BR-12) có ngày đầu tiên trên chuyền đó, tính trên toàn bộ dữ liệu đã lưu, nằm trong khoảng đã chọn, mỗi mã đơn gốc tính 1 lần. Total: Output, Changeover là tổng; Matching ratio tính lại từ tổng; MO 8h của xưởng (BR-23); Working hours của xưởng (BR-20). Lọc khách hàng, sản phẩm theo BR-29: MO 8h hiện "-", Changeover chỉ đếm đơn của nhóm đã chọn. Dấu ▼ cho MO 8h dưới ngưỡng (BR-28, BR-76). (sửa 2026-11-13 theo yêu cầu người dùng: thêm cột %Efficiency (with ratio) ngay sau Output = hiệu suất B của chuyền (BR-19), dòng Total tính lại từ tổng, ▼ khi dưới ngưỡng hiệu suất (BR-28, BR-76), lọc như Output; Matching ratio nay theo BR-86 thay cột `Match line strength`; Changeover nay theo BR-87 thay cách đếm mã đơn gốc mới, Total là tổng các chuyền) | - |
| BR-84 | Chi tiết một chuyền ở Screen 2 (thêm 2026-11-12): phần sở trường lấy từ LineStrength của xưởng và chuyền đó (nhóm hàng mạnh 1 đến 4, khách hàng mạnh, tốc độ đổi mã, ghi chú), chưa có thì ghi "No strength saved for this line."; bảng đơn hàng đã làm trong khoảng đã chọn, mỗi dòng một mã đơn gốc: Order (mã đơn gốc), Customer, Style (các style, cách nhau dấu phẩy), Product type (nhóm sản phẩm theo 4.6), CM price (tiền CM / sản lượng của đơn trong khoảng), Output, First day on line (ngày đầu tiên của đơn trên chuyền, trên toàn bộ dữ liệu), Matches strength (Yes khi nhóm sản phẩm thuộc nhóm hàng mạnh của chuyền, không phân biệt hoa thường; No khi không thuộc; "-" khi chuyền chưa có sở trường hoặc sản phẩm "Chưa phân nhóm"). Sắp theo ngày đầu tiên, rồi mã đơn. (sửa 2026-11-13: thêm cột SMV và %Efficiency (with ratio) của đơn theo BR-88; Matches strength dùng cùng cách so của BR-86, nên khớp với Matching ratio của bảng chuyền) | - |
| BR-85 | File Excel Line performance (thêm 2026-11-12, UC-32) theo mẫu báo cáo chuyền của người dùng. (sửa 2026-11-13 theo yêu cầu người dùng: một lần tải ra một file `Line performance - <dd.mm> to <dd.mm>.xlsx` gồm 4 sheet `Fac Vinh Long`, `Fac 2`, `Fac 3`, `Fac 5`, mỗi sheet một xưởng theo khoảng ngày đang chọn, không phụ thuộc xưởng đang chọn trên màn hình; xưởng không có dữ liệu vẫn có sheet, ghi "No data in this period."; trước đây: một sheet `Line performance` cho xưởng đang chọn. Sửa 2026-11-13: tải bằng nút "Download Line performance" ở Screen 2, theo từ ngày, đến ngày của Screen 2; nội dung file không đổi.) Mỗi sheet: dòng 1 tiêu đề "Line performance - <xưởng> (<dd.mm> to <dd.mm>)"; tiêu đề hai tầng: Number of Operators, Production Output (pcs) gồm Target / Actual / ratio, Production Value ($) gồm Target / Actual / ratio, MO $ (Convert to 8h); mỗi dòng một chuyền, dòng cuối Total; số như màn hình (BR-78 đến BR-80), ratio định dạng %, tiền 2 chữ số lẻ; số dưới ngưỡng ghi thêm cột "Below threshold" (Output ratio, MO 8h); ghi số, không ghi công thức | - |
| BR-86 | Đúng sở trường theo bảng sở trường (thêm 2026-11-13): mỗi dòng sản lượng là đúng sở trường khi nhóm sản phẩm của dòng (BR-14) nằm trong các nhóm hàng mạnh (`STRONG ITEM GROUP` 1 đến 4) của cùng xưởng và chuyền trong sở trường đang lưu (4.11), không phân biệt hoa thường; không nằm trong là trái sở trường. Dòng "Chưa phân nhóm", và dòng của chuyền chưa có sở trường hoặc sở trường không có nhóm hàng nào, không được xét (bỏ khỏi cả tử số và mẫu số). Tỷ lệ = tổng sản lượng đúng sở trường / tổng sản lượng được xét (%); không còn dòng nào được xét thì hiện "-". Chuyền, xưởng, HCM, Total và kỳ đều tính lại từ tổng sản lượng. Lọc khách hàng, sản phẩm như sản lượng. Dùng sở trường đang lưu cho mọi ngày. Không đọc cột `Match line strength` và `Expertise` | - |
| BR-87 | Changeover theo mã hàng (thêm 2026-11-13): với mỗi chuyền, mã hàng = nhóm khách hàng (BR-15) + SMV + giá CM của dòng sản lượng. Ngày làm việc của chuyền = ngày chuyền có sản lượng lớn hơn 0, tính trên toàn bộ dữ liệu đã lưu. Với mỗi ngày làm việc của chuyền trong khoảng đã chọn, một mã hàng chạy ngày đó được tính 1 lần nếu ngày làm việc liền trước của chuyền không chạy mã hàng này: lần đầu lên chuyền được tính; mã hàng chạy liên tục không tính thêm; mã hàng nghỉ ít nhất 1 ngày làm việc của chuyền rồi lên lại được tính thêm 1 lần; ngày chuyền nghỉ (không có sản lượng) không tính là cách quãng. Các đơn, style khác nhau mà cùng mã hàng chỉ tính như một. Dòng thiếu SMV không được tính. Changeover của xưởng = tổng các chuyền | - |
| BR-88 | Đơn hàng ở chi tiết chuyền (thêm 2026-11-13, bổ sung BR-84): SMV của đơn = tổng (SMV × sản lượng) / tổng sản lượng các dòng có SMV của đơn trên chuyền trong khoảng đã chọn, không có thì "-", 2 chữ số lẻ; %Efficiency (with ratio) của đơn = tổng sản lượng / tổng `Standard output of SMV (have efficiency ratio)` của các dòng có cột này, bỏ dòng thiếu khỏi cả hai vế (như BR-19), không có thì "-", 1 chữ số lẻ. Không dùng mục tiêu `Target system` ("with ratio - system") | - |
| BR-89 | Hai chỉ số mới của Screen 4 (thêm 2026-11-13), tính cho từng kỳ (BR-68) và từng cột: Matching strength (%) theo BR-86, 1 chữ số lẻ; Changeover/line/day = tổng Changeover (BR-87) của các chuyền trong kỳ / số ngày làm việc (BR-33) / số chuyền (BR-34) của xưởng trong kỳ, 3 chữ số lẻ. HCM và Total tính từ số tổng: Matching từ tổng sản lượng; Changeover/line/day = tổng Changeover / tổng (số ngày làm việc × số chuyền) của từng xưởng. Không có mục tiêu, ngưỡng, dấu dưới ngưỡng. Thẻ số so với kỳ trước theo BR-71; màu mũi tên theo BR-70 | - |
| BR-90 | "Line trend" của một chuyền ở chi tiết chuyền Screen 2 (thêm 2026-11-13 lần 2): khoảng thời gian từ 01/01 của năm của "Đến ngày" đến "Đến ngày" đang chọn ("Từ ngày" của bảng không áp dụng); chia kỳ By week / By month / By year theo BR-68 (mặc định By week); kỳ chuyền không có sản lượng thì không hiện. Mỗi kỳ: Output = tổng sản lượng của chuyền; %Efficiency (with ratio) = hiệu suất B của chuyền (BR-19); MO 8h = trung bình MO 8h các ngày của chuyền (BR-22). Lọc khách hàng, sản phẩm theo BR-29: Output và %Efficiency theo nhóm đã chọn, MO 8h hiện "-". Bảng số ngay dưới biểu đồ: dòng Output, %Efficiency (with ratio), MO 8h, mỗi kỳ một cột, số viết theo BR-50, BR-75; ▼ khi %Efficiency hoặc MO 8h dưới ngưỡng, so với mức của ngày cuối kỳ (BR-26, BR-28, BR-76). Biểu đồ: cột Output theo kỳ, ngay dưới là đường của chỉ số đã chọn (%Efficiency (with ratio) mặc định, hoặc MO 8h) | - |
| BR-91 | "Line trend" dễ đọc hơn (thêm 2026-11-13 lần 3, bổ sung BR-90): cột Output của mỗi kỳ có màu theo %Efficiency (with ratio) của kỳ đó: xanh dương "On target" khi bằng hoặc trên ngưỡng hiệu suất, cam "Below threshold" khi dưới ngưỡng (BR-28, so với mức của ngày cuối kỳ, BR-26), màu thứ ba "No number" khi kỳ không có %Efficiency; có chú thích màu. By week hiện 26 tuần gần nhất tính đến "Đến ngày" (sửa BR-90: trước đây từ 01/01; By month, By year giữ từ 01/01), để biểu đồ luôn vẽ được dạng cột có màu (biểu đồ cột dùng chung giữ tối đa 30 cột). Đầu khối chi tiết chuyền có một dòng tóm tắt bộ lọc đang chọn (xưởng, khoảng ngày, chuyền, nhóm khách hàng, nhóm sản phẩm) và liên kết "Back to filters" cuộn trang về ô bộ lọc | - |
| BR-92 | Overview gọn lại (thêm 2026-11-13 lần 4): bỏ biểu đồ "Output vs Target (with ratio - system) by factory" và phần xếp hạng chuyền (10 cao nhất, 10 thấp nhất, nút chọn chỉ số; BR-44 bỏ khỏi màn hình). Thứ tự từ trên xuống: bộ lọc; dòng thời điểm dữ liệu; 7 thẻ số (BR-58); bảng chỉ số theo xưởng (luôn mở, BR-61) và nút tải báo cáo tuần; 2 biểu đồ %Efficiency (with ratio) theo ngày và MO 8h theo ngày xếp cạnh nhau; khu "Products & customers" (BR-93 đến BR-96) | - |
| BR-93 | Cơ cấu hàng theo xưởng (thêm 2026-11-13 lần 4): với mỗi xưởng đã chọn và Total, tỷ lệ sản lượng của từng nhóm sản phẩm (BR-14) = sản lượng nhóm / sản lượng của xưởng (%), trong khoảng ngày và theo bộ lọc khách hàng, sản phẩm như sản lượng (BR-29). Biểu đồ: mỗi xưởng một cột 100%, mỗi nhóm một màu; 5 nhóm có sản lượng lớn nhất trên tất cả xưởng đã chọn, các nhóm còn lại (kể cả "Chưa phân nhóm") gộp vào "Other". Bảng cạnh biểu đồ: mỗi dòng một nhóm sản phẩm (đủ mọi nhóm), mỗi xưởng và Total hai cột pcs và %, sắp theo sản lượng Total giảm dần | - |
| BR-94 | Top khách hàng (thêm 2026-11-13 lần 4): 10 nhóm khách hàng (BR-15) có tổng sản lượng lớn nhất trên các xưởng đã chọn trong khoảng ngày; biểu đồ cột ngang, mỗi khách một cột, chia màu theo xưởng; theo bộ lọc khách hàng, sản phẩm (BR-29) | - |
| BR-95 | Giá CM trung bình theo nhóm hàng (thêm 2026-11-13 lần 4): với mỗi nhóm sản phẩm = tổng tiền CM / tổng sản lượng của nhóm (BR-24) trên các xưởng đã chọn trong khoảng ngày; biểu đồ cột, sắp giảm dần; nhóm "Chưa phân nhóm" vẫn hiện; theo bộ lọc khách hàng, sản phẩm | - |
| BR-96 | Cơ cấu hàng theo tháng (thêm 2026-11-13 lần 4): từ 01/01 của năm của "Đến ngày" đến "Đến ngày", mỗi tháng một cột, chia màu theo nhóm sản phẩm như BR-93 (5 nhóm lớn nhất + "Other"), giá trị là sản lượng (pcs); trên các xưởng đã chọn, theo bộ lọc khách hàng, sản phẩm | - |
| BR-97 | File năm cũ chỉ có sheet `Production data` (thêm 2026-11-13 lần 4, sửa BR-02): file không có `Target system` và `Worker` vẫn được nhận khi mọi ngày hợp lệ trong `Production data` đều trước 01/01/2026; có ngày từ 01/01/2026 trở đi thì vẫn báo lỗi BR-02 như cũ. Khi lưu: dòng sản lượng lưu như file thường (BR-05 đến BR-07, BR-10 đến BR-15; đổi số chuyền Fac 1 theo BR-11); số thợ của mỗi xưởng mỗi ngày = tổng số người trong ngày của các chuyền (BR-21), lưu vào 4.3 với `derived` = có, thay số thợ đang có trong khoảng ngày của file (BR-07); không lưu mục tiêu A và tổng nhân sự, nên %Efficiency (with ratio - system) và %Direct labor của những ngày này là "-". Lịch sử tải file ghi sheet `Worker` là "tính từ Production data" | File thiếu sheet: <tên sheet>. Hãy dùng đúng file Data sewing. (như BR-02, khi file có ngày từ 01/01/2026) |
| BR-98 | Xưởng đã giải thể (thêm 2026-11-13 lần 4, bổ sung BR-06): `SHCM-Factory 1` = Fac 1 HCM (closed). Dòng của xưởng này được lưu (kể cả số thợ tính theo BR-97) để tham khảo nhưng không hiện ở bất kỳ màn hình, bộ lọc, thẻ số, bảng, biểu đồ, file Excel nào và không tính vào HCM, Total | - |
| BR-78 | Một chuyền ở Screen 6 (thêm 2026-11-11), trên các ngày trong khoảng đã chọn, tên chuyền theo BR-10, BR-11: Number of Operators = trung bình số người mỗi ngày của chuyền (số người trong ngày theo BR-21, chỉ các ngày chuyền có dòng sản lượng), 1 chữ số lẻ; Output Target = tổng `Standard output of SMV (have efficiency ratio)` (mục tiêu with ratio); Output Actual = tổng `Product Inline Quantity`; Output Ratio = sản lượng / mục tiêu, bỏ các dòng thiếu mục tiêu khỏi cả hai vế (bằng %Efficiency (with ratio) của chuyền, BR-19); Value Target = tổng (mục tiêu × giá CM) từng dòng; Value Actual = tiền CM (BR-17); Value Ratio = tiền CM / Value Target, bỏ các dòng thiếu mục tiêu khỏi cả hai vế; MO $ (8h) = trung bình MO 8h các ngày của chuyền (BR-22). Không có số thì "-" | - |
| BR-79 | Dòng Total của Screen 6 (thêm 2026-11-11): Number of Operators = tổng các chuyền; Target, Actual = tổng các chuyền; hai Ratio tính lại từ tổng như BR-78; MO $ (8h) = MO 8h của xưởng cả kỳ theo BR-23 (bằng số ở Screen 1) | - |
| BR-80 | Dưới ngưỡng ở Screen 6 (thêm 2026-11-11): Output Ratio dưới ngưỡng hiệu suất và MO $ (8h) dưới ngưỡng MO 8h của xưởng thì có ▼ (BR-28, BR-76), so với mức của ngày cuối khoảng (BR-26); áp cho từng chuyền và dòng Total | - |
| BR-75 | Cách viết số trên màn hình (thêm 2026-11-09, mọi màn hình của app): dấu chấm cho phần thập phân, dấu phẩy ngăn hàng nghìn, ví dụ `151,288`, `33.50`, `91.4%`, `-15,422`. Số chữ số lẻ vẫn theo BR-50. File Excel xuất ra không đổi (ô số, Excel tự hiện theo máy người mở). Nhãn trục và số khi rê chuột trên biểu đồ theo biểu đồ dùng chung của khung sườn (chờ người phụ trách khung sườn) | - |
| BR-76 | Dấu "dưới ngưỡng" (thêm 2026-11-09, sửa BR-28: trước đây dấu 🔴): trong bảng, số dưới ngưỡng có ký hiệu ▼ ngay sau số, ví dụ `38.07 ▼`, dưới bảng ghi "▼ below threshold"; trên thẻ số của Screen 4, tên cột chuyển màu đỏ kèm ▼, ví dụ "Fac 2 ▼". Cách xác định dưới ngưỡng không đổi (BR-28, BR-69) | - |
| BR-77 | %Direct labor theo kỳ (thêm 2026-11-09): tab Direct worker của Screen 4 có thêm một hàng thẻ %Direct labor, mỗi cột một thẻ, số = tổng số thợ / tổng nhân sự của kỳ cuối theo BR-65; mũi tên và mức thay đổi theo BR-71 (so cùng số ngày đầu của kỳ trước), không tô màu như Direct worker (BR-70); thẻ có biểu đồ mini các kỳ. Kỳ không đủ hai số thì ghi "-" | - |
| BR-70 | Thẻ số của Screen 4 (thêm 2026-11-08): mũi tên lên khi số kỳ cuối lớn hơn số so sánh của BR-71, xuống khi nhỏ hơn. Màu: MO 8h, %Efficiency (with ratio), Output, Revenue tăng là xanh, giảm là đỏ; Direct worker, Avg CM price, Avg SMV (chỉ thể hiện độ khó của sản phẩm), Avg working hours có mũi tên nhưng không tô màu. (sửa 2026-11-13: Matching strength tăng là xanh, giảm là đỏ; Changeover/line/day có mũi tên, không tô màu) Thẻ MO 8h và %Efficiency có dấu 🔴 khi số kỳ cuối có dấu 🔴 trong bảng (BR-69). Mức thay đổi ghi theo số lẻ của BR-50 | - |
| BR-71 | Số so sánh của thẻ số Screen 4 (thêm 2026-11-08): thẻ ghi số của kỳ cuối trong bảng, đã cộng dồn đến ngày cuối của khoảng đã chọn (BR-68). Số so sánh là số của kỳ đứng ngay trước trong bảng, tính như BR-69 trên các ngày từ ngày đầu của kỳ trước, cùng số ngày lịch với kỳ cuối, không quá ngày cuối của kỳ trước. Ví dụ kỳ cuối W45 (31.10–05.11) có 6 ngày thì so với W44 tính 24.10–29.10; kỳ cuối đủ ngày thì so với cả kỳ trước. Dưới mức thay đổi ghi "vs <tên kỳ trước> (<dd.mm>–<dd.mm>)" với các ngày đã dùng. Bảng chỉ có 1 kỳ, hoặc số kỳ cuối hay số so sánh là "-", thì thẻ chỉ ghi số, không có mũi tên | - |

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
- **Cập nhật dữ liệu:** từ trên xuống: khối Bước 1 chọn file và nút "Kiểm tra file"; khối Bước 2 kết quả kiểm tra, bảng dòng bị bỏ qua, bảng cảnh báo, nút "Lưu dữ liệu" có hỏi lại trước khi lưu (sửa 2026-11-06: một nút "Check & save" kiểm tra và lưu luôn, BR-57); khối đổi mã hàng tuần dạng form (Từ ngày, Đến ngày, 4 ô số, nút "Lưu số đổi mã hàng", không hỏi lại); bảng chọn một dòng đã nhập và nút "Xoá dòng đã chọn" có hỏi lại; bảng lịch sử tải file chỉ xem.
- **Mục tiêu và ngưỡng:** bảng đang áp dụng chỉ xem; form thêm mức mới (Xưởng, Ngày hiệu lực, 4 ô số, nút "Lưu mức mới", không hỏi lại); bảng lịch sử chỉ xem.
- **Danh mục:** 4 thẻ: Nhóm sản phẩm, Nhóm khách hàng, Số chuyền Fac 1, Tên sản phẩm theo style; mỗi thẻ một bảng sửa trực tiếp trong ô, thêm và bớt được dòng, nút lưu tương ứng, không hỏi lại; dưới bảng là danh sách còn thiếu, chỉ xem.

**Sửa 2026-11-05 (BR-51 đến BR-54):** tên trên màn hình đổi sang tiếng Anh. Menu "Reports": Overview, Line Detail, Daily Report, Monthly Report, MO by Line, Changeover. Menu "Data management": Data Update, Targets & Thresholds, Catalogs. Bảng chỉ số ở Screen 1 và Screen 3 thêm cột HCM sau Fac 5. Screen 1 thêm khối Summary trên bảng chỉ số (trước đây không có ô số liệu tổng hợp). Biểu đồ xếp hạng đổi từ cột đứng sang cột ngang. Các mô tả tiếng Việt ở trên giữ để đối chiếu với mục 5, 6, 7.

**Sửa 2026-11-05 (BR-55, BR-56):** Screen 1, 2, 3, 4 và file Excel thêm %Efficiency B (no ratio), Screen 1 và 2, 4 thêm Target B (no ratio). Screen 1 thêm biểu đồ theo ngày của loại này, biểu đồ Output xuống một hàng riêng, xếp hạng chuyền có thêm lựa chọn no ratio. Screen 5 có thêm thẻ thứ 6.

**Sửa 2026-11-06 lần 3 (BR-58, BR-61, BR-65 đến BR-67):** khu card Vinh Long - HCM ở Screen 1 có 7 card trên một hàng (Revenue, Output, Avg CM price, Avg SMV, MO 8h, %Efficiency, %Direct labor; tên, số Total và các dòng thẳng hàng giữa các card), thêm Avg SMV (min, xanh ngọc) và %Direct labor (%, xám xanh), cùng kiểu với 5 card cũ, nút ＋ áp cho cả 7 card. Bỏ 2 biểu đồ "%Efficiency (no ratio) by day" và "%Efficiency (with ratio - system) by day"; các biểu đồ còn lại giữ thứ tự cũ. Bảng Metrics ẩn thêm dòng "%Efficiency (with ratio) vs target", hiện lại khi bật nút gạt "Show targets & with ratio - system". Hai số mới chỉ có ở card, không thêm vào bảng Metrics và file Excel.

**Sửa 2026-11-06 lần 4 (UC-29, UC-30, BR-68, BR-69):** mục menu "Monthly Report" đổi tên thành "Period Report", vẫn trong nhóm Reports, cùng vị trí. Từ trên xuống: bộ lọc (lựa chọn By week / By month / By quarter / By year dạng nút bấm, Từ ngày, Đến ngày, Xưởng); dòng thời điểm dữ liệu; 8 khối (không có nút tải Excel), mỗi khối một chỉ số theo thứ tự MO 8h, %Efficiency (with ratio), Direct worker, Output, Revenue, Avg CM price, Avg SMV, Avg working hours; mỗi khối có biểu đồ đường theo kỳ (mỗi xưởng một đường) và bảng chỉ xem: Period | các xưởng đã chọn | HCM | Total. Bảng theo ngày của từng xưởng trước đây bỏ khỏi màn hình.

**Sửa 2026-11-08 (BR-70, BR-71, phương án A làm biểu đồ dễ nhìn):** bộ lọc và dòng thời điểm dữ liệu giữ nguyên. 8 khối xếp dọc đổi thành 8 tab cùng thứ tự (MO 8h, %Efficiency (with ratio), Direct worker, Output, Revenue, Avg CM price, Avg SMV, Avg working hours). Mỗi tab, từ trên xuống: hàng thẻ số, mỗi cột một thẻ (các xưởng đã chọn, HCM khi hiện, Total) ghi số kỳ cuối, mũi tên và mức thay đổi (BR-70, BR-71) và biểu đồ mini các kỳ; các biểu đồ nhỏ, mỗi cột một biểu đồ có thang riêng (thay biểu đồ đường chung 4 xưởng, nay có cả HCM và Total); bảng số Period | các xưởng | HCM | Total như cũ, trải hết bề ngang. Không có nút tải.
Chốt giao diện 2026-11-08 ("ok" toàn bộ đề xuất): thẻ số nằm trên một hàng (tối đa 6 thẻ); Output, Revenue, Direct worker vẽ cột, 5 chỉ số còn lại vẽ đường, cả ở biểu đồ nhỏ và biểu đồ mini trong thẻ; biểu đồ nhỏ xếp 3 biểu đồ mỗi hàng; bảng số nằm trong khối gấp "Xem bảng số", mặc định đóng; app nhớ tab đang xem trong phiên làm việc.
**Sửa 2026-11-12 (người dùng yêu cầu):** menu Reports bỏ "Daily Report" (Screen 3) và "MO by Line" (Screen 5); còn Overview, Line Detail, Sewing metrics, Line performance. Line Detail (Screen 2): bộ lọc giữ nguyên; bảng mỗi dòng một chuyền (BR-83) thay bảng chuyền theo ngày, chọn một dòng (bảng chọn một dòng) thì bên dưới hiện chi tiết chuyền đó (BR-84); nút tải file báo cáo tuần giữ. Line performance (Screen 6): thêm nút "Download Excel" (UC-32, BR-85). Data Update (Screen 7): cùng ô tải file nhận cả file Line Strength (UC-33). Catalogs (Screen 9): thêm thẻ "Line strength" chỉ xem (UC-34).
**Chốt giao diện 2026-11-13 ("ok" toàn bộ đề xuất):** bảng chuyền Line Detail: %Efficiency (with ratio) và Matching ratio hiện dạng thanh màu kèm số, cột Line và %Efficiency luôn đứng bên trái khi kéo ngang, MO 8h chữ số thường (bỏ kiểu chữ đậm đặc biệt), thêm cột "Alert" ghi "▼ Eff" và/hoặc "▼ MO 8h" khi dưới ngưỡng (ô thanh màu không gắn được ▼); bảng đơn hàng: %Efficiency (with ratio) dạng thanh màu kèm số, SMV 2 chữ số lẻ, thứ tự Order, Customer, Style, Product type, SMV, CM price, Output, %Efficiency (with ratio), First day on line, Matches strength; nút "Download Line performance" ngay dưới bộ lọc, trên bảng chuyền, ghi chú "File gồm 4 xưởng, theo khoảng ngày đang chọn"; Sewing metrics: 2 chỉ số mới vẽ đường, thẻ Matching strength xanh lá, Changeover/line/day tím, bảng số và khối "Charts" như 8 chỉ số kia.
**Chốt giao diện 2026-11-13 lần 4 ("1a, 2abcd, 3b"):** Overview: bộ lọc; dòng thời điểm dữ liệu; 7 thẻ số; bảng chỉ số theo xưởng ở chỗ cũ, luôn mở, nút tải báo cáo tuần; hai biểu đồ theo ngày (%Efficiency (with ratio), MO 8h) cạnh nhau; khu "Products & customers" hai cột: Cơ cấu hàng theo xưởng (cột 100%) | bảng cơ cấu hàng pcs / %; Top 10 khách hàng (cột ngang, màu theo xưởng) | Giá CM trung bình theo nhóm hàng; dưới cùng Cơ cấu hàng theo tháng trải hết bề ngang. Bỏ "Output vs Target (with ratio - system) by factory" và Ranking (BR-92 đến BR-96). Số chính xác xem khi rê chuột hoặc trong bảng.
**Chốt giao diện 2026-11-13 lần 2 ("all đề xuất"):** trong khối chi tiết của chuyền đã chọn ở Line Detail, trên bảng đơn hàng, có phần "Line trend": hàng nút By week / By month / By year (mặc định By week) và nút chọn đường %Efficiency (with ratio) / MO 8h (mặc định %Efficiency); biểu đồ cột Output; ngay dưới, cùng trục thời gian, biểu đồ đường của chỉ số đã chọn; ngay dưới hai biểu đồ là bảng số Output, %Efficiency (with ratio), MO 8h, mỗi kỳ một cột (BR-90). Một biểu đồ gộp cột + đường có số trên từng điểm chờ người phụ trách khung sườn bổ sung biểu đồ dùng chung.
**Sửa 2026-11-13 (người dùng yêu cầu):** menu Reports còn Overview, Line Detail, Sewing metrics (bỏ "Line performance"). Line Detail: bộ lọc giữ nguyên; nút "Download Line performance" (UC-32) thay nút tải báo cáo tuần; bảng chuyền thêm cột %Efficiency (with ratio) sau Output, %Efficiency và MO 8h trình bày nổi bật, dễ đọc; bảng đơn hàng thêm SMV và %Efficiency (with ratio). Sewing metrics: thêm Matching strength và Changeover/line/day sau Avg working hours, cùng kiểu với các chỉ số khác, có trong thanh "Jump to".
Sửa 2026-11-10 lần 2 (người dùng yêu cầu): dưới dòng thời điểm dữ liệu có thanh "Jump to" gồm 8 thẻ chuyển hướng theo thứ tự BR-69 (MO 8h, %Efficiency, Direct worker, Output, Revenue, Avg CM price, Avg SMV, Avg working hours); bấm một thẻ là trang cuộn ngay tới chỉ số đó. Cuối mỗi chỉ số có liên kết "Back to top" về thanh này.
Sửa 2026-11-10 (người dùng yêu cầu): bỏ 8 tab, các chỉ số xếp dọc trên một trang theo đúng thứ tự BR-69, kéo xuống là thấy từng chỉ số. Mỗi chỉ số: hàng thẻ số (Direct worker có thêm hàng %Direct labor), khối gấp "Charts" có dấu ＋, bấm mới mở các biểu đồ nhỏ (mặc định đóng, chỉ vẽ khi mở), khối gấp bảng số như cũ. Không còn "nhớ tab".
Sửa 2026-11-08 lần 2 (người dùng yêu cầu): bảng số xoay lại, mỗi dòng một cột của báo cáo (các xưởng đã chọn, HCM, Total), mỗi cột một kỳ; cột đầu "Factory" luôn hiện khi kéo ngang.

Screen 1 đến 6 cấp cho mọi người xem. Screen 7 đến 9 chỉ cấp cho người có vai trò `UPDATER`. Mọi báo cáo hiện ngày dữ liệu mới nhất và thời điểm tải file gần nhất (UC-26).

### Screen 1: Tổng quan (landing page)
- **Purpose:** So sánh 4 xưởng theo khoảng thời gian, tương ứng sheet `Overall`.
- **Inputs/filters:** Từ ngày, đến ngày (mặc định BR-31, bắt buộc); Xưởng (chọn nhiều, mặc định tất cả); Nhóm khách hàng (chọn nhiều, mặc định tất cả); Nhóm sản phẩm (chọn nhiều, mặc định tất cả).
- **Bảng chỉ số, mỗi xưởng một cột:** Mục tiêu A; Sản lượng; Mục tiêu hiệu suất; Hiệu suất A; % so với mục tiêu của hiệu suất A; Mục tiêu B; Hiệu suất B; % so với mục tiêu của hiệu suất B; Tiền CM; Mục tiêu MO 8h; MO 8h; % so với mục tiêu của MO 8h; Giá CM trung bình; Giờ làm trung bình; Tỷ lệ đúng sở trường; Đổi mã hàng tuần; Đổi mã hàng tuần trên chuyền. Có dấu 🔴 theo BR-28.
- **Biểu đồ (UC-05):** Hiệu suất A theo ngày; Hiệu suất B theo ngày; MO 8h theo ngày; Sản lượng so với mục tiêu A giữa các xưởng; Xếp hạng chuyền với lựa chọn Hiệu suất B/Hiệu suất A/MO 8h.
- **Actions:** "Tải Excel báo cáo tuần" → UC-11. Đổi bộ lọc → UC-04, UC-05.
- **Khi không có dữ liệu:** "Chưa có dữ liệu trong khoảng thời gian này."

### Screen 2: Chi tiết chuyền - Line Detail
- **Sửa 2026-11-12:** bảng chính là bảng chuyền của BR-83 (Line | Output | MO 8h | Working hours | Matching ratio | Changeover, dòng Total), chọn được một dòng; bên dưới là chi tiết chuyền đã chọn (BR-84): khối sở trường và bảng đơn hàng (Order | Customer | Style | Product type | CM price | Output | First day on line | Matches strength). Bảng chuyền theo ngày và bảng xưởng theo ngày bỏ khỏi màn hình. Bộ lọc và nút tải file báo cáo tuần giữ nguyên.
- **Sửa 2026-11-13:** gộp Line performance vào đây. Bảng chuyền: Line | Output | %Efficiency (with ratio) | MO 8h | Working hours | Matching ratio | Changeover, dòng Total (BR-83 sửa, BR-86, BR-87). Bảng đơn hàng: Order | Customer | Style | Product type | SMV | CM price | Output | %Efficiency (with ratio) | First day on line | Matches strength (BR-84, BR-88). Actions: "Download Line performance" → UC-32 (file BR-85 theo từ ngày, đến ngày đang chọn); bỏ nút "Tải Excel báo cáo tuần" (vẫn có ở Screen 1).
- **Thêm 2026-11-13 lần 3:** cột Output của "Line trend" có màu On target / Below threshold / No number; By week 26 tuần gần nhất; đầu khối chi tiết chuyền có dòng tóm tắt bộ lọc và liên kết "Back to filters" (BR-91).
- **Thêm 2026-11-13 lần 2:** chi tiết chuyền đã chọn có phần "Line trend" trên bảng đơn hàng (BR-90): kỳ By week / By month / By year, nút chọn đường %Efficiency (with ratio) / MO 8h, biểu đồ cột Output, biểu đồ đường của chỉ số đã chọn, bảng số Output / %Efficiency / MO 8h theo kỳ.
- **Purpose:** Xem từng chuyền theo ngày, tương ứng các sheet `Fac`.
- **Inputs/filters:** Từ ngày, đến ngày (mặc định BR-31); Xưởng (một xưởng, mặc định Fac 1); Chuyền (chọn nhiều, mặc định tất cả); Nhóm khách hàng; Nhóm sản phẩm.
- **Bảng, sắp theo số chuyền rồi ngày:** Chuyền, Ngày, Mục tiêu A, Sản lượng, Hiệu suất A, Mục tiêu B, Hiệu suất B, Tiền CM, Số người, Giờ làm, MO 8h. Có dòng Cả kỳ của từng chuyền và dòng Tổng xưởng. Có dấu 🔴 theo BR-28.
- **Thông tin xưởng theo ngày:** Số thợ, Giờ làm.
- **Actions:** "Tải Excel báo cáo tuần" → UC-11. Đổi bộ lọc → UC-06.
- **Khi không có dữ liệu:** "Chưa có dữ liệu trong khoảng thời gian này."

### Screen 3: Báo cáo ngày (bỏ khỏi menu từ 2026-11-12 theo yêu cầu người dùng)
- **Purpose:** Xem kết quả một ngày, tương ứng `Daily Report Sewing`, bỏ Cutting.
- **Inputs/filters:** Ngày (mặc định BR-31, bắt buộc); Xưởng cho bảng chuyền (một xưởng, mặc định Fac 1).
- **Bảng xưởng, mỗi xưởng một cột:** MO; Giờ làm; Target MO 8h; MO 8h; % so với Target MO 8h; Mục tiêu sản lượng; Sản lượng; Hiệu suất A; Hiệu suất B; Tỷ lệ đúng sở trường; Số thợ.
- **Bảng chuyền, sắp theo số chuyền, có dòng Tổng:** Chuyền, Sản lượng, Tiền CM, Giờ làm, Số người, MO, MO 8h, Sản lượng trái sở trường. Fac 1 hiện chung, không tách chuyền cũ và mới.
- **Actions:** "Tải Excel" → UC-12. Đổi ngày hoặc xưởng → UC-07.
- **Khi không có dữ liệu:** "Chưa có dữ liệu của ngày này."

### Screen 4: Báo cáo theo kỳ - Sewing metrics (sửa 2026-11-06, thay toàn bộ nội dung báo cáo tháng bên dưới; sửa 2026-11-09: tên trên menu và trang đổi từ "Period Report" thành "Sewing metrics", đường dẫn giữ `.../monthly`)
- **Thêm 2026-11-13:** 2 chỉ số mới sau Avg working hours: Matching strength (%) và Changeover/line/day (BR-89), mỗi chỉ số có hàng thẻ số, khối "Charts", bảng số và mục trên thanh "Jump to"; tổng cộng 10 chỉ số.
- **Thêm 2026-11-09:** tab Direct worker có thêm hàng thẻ %Direct labor (BR-77). Số viết theo BR-75, dấu dưới ngưỡng theo BR-76. Số trên từng điểm của biểu đồ: chờ người phụ trách khung sườn bổ sung biểu đồ dùng chung (mục 10).
- **Purpose:** Xem xu hướng các xưởng theo tuần, tháng, quý, năm.
- **Inputs/filters:** Loại kỳ By week / By month / By quarter / By year (mặc định By week); Từ ngày, đến ngày (mặc định BR-31); Xưởng (chọn nhiều, mặc định tất cả). Không lọc khách hàng, sản phẩm.
- **Bảng, mỗi chỉ số một bảng (BR-69), theo thứ tự:** MO 8h (USD), %Efficiency (with ratio), Direct worker, Output, Revenue (USD), Avg CM price (USD), Avg SMV, Avg working hours. Mỗi bảng: cột Period, các xưởng đã chọn, HCM (khi chọn từ 2 xưởng HCM), Total; mỗi dòng một kỳ (BR-68). Dấu 🔴 theo BR-69.
- **Biểu đồ:** cạnh hoặc trên mỗi bảng một biểu đồ đường theo kỳ, mỗi xưởng một đường. (sửa 2026-11-08: mỗi chỉ số một tab; mỗi cột một biểu đồ nhỏ có thang riêng, gồm cả HCM và Total; kỳ thiếu ngày vẫn được vẽ)
- **Bảng số (sửa 2026-11-08 lần 2):** mỗi dòng một xưởng đã chọn, HCM, Total; mỗi cột một kỳ (trước đây: mỗi dòng một kỳ, mỗi cột một xưởng). Số và dấu 🔴 không đổi.
- **Thẻ số (thêm 2026-11-08):** đầu mỗi tab, mỗi cột (các xưởng đã chọn, HCM, Total) một thẻ: số kỳ cuối, mũi tên và mức thay đổi so với kỳ trước (BR-70, BR-71), biểu đồ mini các kỳ.
- **Actions:** Đổi bộ lọc → UC-29. Không có nút tải Excel (chỉ hiển thị).
- **Khi không có dữ liệu:** "Chưa có dữ liệu trong khoảng thời gian này."

Nội dung cũ (bỏ từ 2026-11-06):
- **Purpose:** Xem từng xưởng theo ngày, tương ứng `Report final`.
- **Inputs/filters:** Từ ngày, đến ngày (mặc định BR-31); Xưởng (chọn nhiều, mặc định tất cả).
- **Bảng mỗi xưởng, sắp theo ngày, có dòng Tổng:** Ngày, MO, Giờ làm, MO 8h, Mục tiêu B, Sản lượng, Hiệu suất B, Tiền CM, Số thợ. Có dấu 🔴 theo BR-28.
- **Actions:** "Tải Excel" → UC-13. Đổi bộ lọc → UC-08.
- **Khi không có dữ liệu:** "Chưa có dữ liệu trong khoảng thời gian này."

### Screen 5: MO theo chuyền (bỏ khỏi menu từ 2026-11-12 theo yêu cầu người dùng)
- **Purpose:** Xem MO 8h của từng chuyền theo ngày, tương ứng sheet `MO`.
- **Inputs/filters:** Từ ngày, đến ngày (mặc định BR-31); Xưởng (một xưởng, mặc định Fac 1); Chuyền (chọn nhiều, mặc định tất cả).
- **5 bảng, hàng là chuyền, cột là ngày, có cột Cả kỳ và dòng Tổng:** MO 8h; Tiền CM; Giờ làm; Số người; Hiệu suất B. Có dấu 🔴 theo BR-28 ở MO 8h và Hiệu suất B.
- **Actions:** "Tải Excel" → UC-14. Đổi bộ lọc → UC-09.
- **Khi không có dữ liệu:** "Chưa có dữ liệu trong khoảng thời gian này."

### Screen 6: Hiệu quả theo chuyền - Line performance (sửa 2026-11-11, thay toàn bộ màn hình Đổi mã hàng bên dưới; bỏ khỏi menu từ 2026-11-13 theo yêu cầu người dùng: gộp vào Screen 2, chỉ còn nút tải file "Download Line performance" ở Screen 2)
- **Purpose:** Xem từng chuyền của một xưởng trong khoảng ngày: số người, sản lượng và giá trị so với mục tiêu, MO 8h, theo mẫu báo cáo chuyền của người dùng.
- **Menu:** mục "Line performance" ở đúng vị trí của "Changeover" trong nhóm Reports; đường dẫn giữ `.../changeover` để quyền đã cấp không đổi.
- **Inputs/filters:** Từ ngày, đến ngày (mặc định tuần thứ Bảy đến thứ Sáu đầy đủ gần nhất, BR-31 sửa); Xưởng (chọn một, mặc định Fac Vinh Long). Không lọc khách hàng, sản phẩm.
- **Bảng (BR-78 đến BR-80), mỗi dòng một chuyền sắp theo số chuyền, dòng cuối Total:** Line | Number of Operators | Production Output (pcs): Target, Actual, Ratio | Production Value ($): Target, Actual, Ratio | MO $ (Convert to 8h). Số viết theo BR-75, dấu dưới ngưỡng ▼ theo BR-80.
- **Actions:** Đổi bộ lọc → UC-31. Không có nút tải Excel (chỉ hiển thị, người dùng bỏ UC-32 khi chốt 11/11/2026). (sửa 2026-11-12: nút "Download Excel" → UC-32, file theo BR-85)
- **Khi không có dữ liệu:** "Chưa có dữ liệu trong khoảng thời gian này."

Nội dung cũ (bỏ khỏi màn hình từ 2026-11-11; số đổi mã hàng tuần vẫn nhập ở Screen 7 và vẫn có trong file Excel báo cáo tuần):
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
- **Khối tải file:** Chọn file (.xlsx, bắt buộc). Nút "Kiểm tra file" → UC-01. Sau khi kiểm tra hiện: số dòng đọc được, hợp lệ, bị bỏ qua; ngày đầu, ngày cuối; so sánh số dòng với dữ liệu đang lưu; bảng dòng bị bỏ qua (Sheet, Dòng, Lý do); bảng cảnh báo (Loại, Ngày, Số lượng). Nút "Lưu dữ liệu" → UC-02, chỉ hiện khi file không bị từ chối. Sau khi lưu hiện thông báo của UC-02. (sửa 2026-11-06: một nút "Check & save" làm cả UC-01 và UC-02; kết quả kiểm tra, dòng bị bỏ qua và cảnh báo hiện sau khi lưu, BR-57.)
- **Khối lịch sử tải file (UC-03):** Thời điểm, Người tải, Tên file, Từ ngày, Đến ngày, Số dòng lưu, Số dòng bỏ qua. (sửa 2026-11-09: thêm cột Trạng thái, Thêm mới, Cập nhật, Ẩn đi; chọn một dòng thì bên dưới hiện chi tiết lần tải đó: lý do từ chối nếu có, bảng theo sheet (Sheet, Đọc được, Hợp lệ, Bỏ qua), bảng thay đổi (Sheet, Xưởng, Thêm mới, Cập nhật, Ẩn đi), bảng dòng bị bỏ qua, bảng cảnh báo. Dòng cũ chưa có chi tiết hiện "-" và ghi chú "Lần tải trước 09/11/2026 không có chi tiết.")
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
- **Line strength (thêm 2026-11-12):** bảng chỉ xem sở trường chuyền (UC-34), ghi tên file và thời điểm tải; muốn sửa thì sửa file Line Strength rồi tải lại ở Screen 7 (UC-33).
- **Tên sản phẩm theo style:** bảng sửa được Style, Tên sản phẩm; danh sách style chưa có tên kèm khách hàng và số dòng. Nút "Lưu tên sản phẩm" → UC-25.

## 9. Acceptance criteria (Tiêu chí nghiệm thu)
Số liệu dưới đây lấy từ các file mẫu; số có thể đổi nếu file được cập nhật sau đó.

- [ ] AC-01: Given người có vai trò `UPDATER`, When tải file `.pdf`, Then thấy thông báo BR-01 và không có nút Lưu.
- [ ] AC-02: Given file thiếu sheet `Worker`, When kiểm tra, Then thấy "File thiếu sheet: Worker. Hãy dùng đúng file Data sewing." và dữ liệu đã lưu giữ nguyên.
- [ ] AC-03: Given sheet `Production data` thiếu cột `Price`, When kiểm tra, Then thấy thông báo BR-03 nêu đúng sheet và cột.
- [ ] AC-04: Given file chưa có kết quả công thức, When kiểm tra, Then thấy thông báo BR-04.
- [ ] AC-05: Given file có một dòng thiếu mã đơn, When kiểm tra, Then dòng đó được liệt kê với số dòng và lý do, các dòng khác vẫn hợp lệ, có nút Lưu.
- [ ] AC-06: Given file có xưởng lạ, When kiểm tra, Then dòng đó được liệt kê với thông báo BR-06.
- [ ] AC-07 (sửa 2026-11-06: trước đây bấm "Kiểm tra file" thì chưa lưu): Given file `Data sewing 2026.xlsx` đúng mẫu, When bấm "Check & save", Then dữ liệu được lưu, thấy thông báo của UC-02 và kết quả kiểm tra gồm số dòng, ngày đầu, ngày cuối, dòng bị bỏ qua, cảnh báo.
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
- [ ] AC-53: Given Fac 2 sản lượng 400, mục tiêu B 500 và Fac 3 sản lượng 100, mục tiêu B 100, When xem Screen 1, Then %Efficiency B của HCM là 83,3%, không phải trung bình của 80% và 100%.
- [ ] AC-54: Given có cột HCM, When xem các cột Fac 2, Fac 3, Fac 5, Then số của từng xưởng không đổi so với khi chưa có cột HCM.
- [ ] AC-55: Given chỉ chọn Fac 2, hoặc chọn Fac Vinh Long và Fac 3, When xem Screen 1, Then không có cột HCM. Given chọn Fac 2 và Fac 3, Then có cột HCM.
- [ ] AC-56: Given có dữ liệu ngày 24/10/2026, When xem Screen 3 và biểu đồ Screen 1, Then bảng có cột HCM, biểu đồ theo ngày có đường HCM, biểu đồ sản lượng có cột HCM.
- [ ] AC-57: Given tải Excel báo cáo tuần hoặc báo cáo ngày trên màn hình, When mở file, Then tên sheet, tên cột, tên chỉ số và kết quả đánh giá bằng tiếng Anh, có cột HCM và cột Fac Vinh Long.
- [ ] AC-58: Given đã đổi tên hiển thị, When mở app với dữ liệu đã lưu trước đó, Then báo cáo vẫn đủ số; dữ liệu đã lưu vẫn ghi Fac 1, trên màn hình hiện Fac Vinh Long.
- [ ] AC-59: Given sản lượng 400, mục tiêu `Target system` 1000, cột `have efficiency ratio` 500, cột `no efficiency ratio` 800, When xem Screen 1, Then %Efficiency (with ratio - system) là 40%, %Efficiency (with ratio - sum) là 80%, %Efficiency B (no ratio) là 50%.
- [ ] AC-60: Given Fac 2 sản lượng 400, cột no ratio 800 và Fac 3 sản lượng 100, cột no ratio 200, When xem cột HCM, Then %Efficiency B (no ratio) là 50%, Target B (no ratio) là 1.000.
- [ ] AC-61: Given %Efficiency B (no ratio) dưới ngưỡng 90%, When xem bảng, Then ô đó không có dấu 🔴.
- [ ] AC-62: Given có cột no ratio, When xem biểu đồ, xếp hạng, Screen 2, Screen 4, Screen 5 và tải Excel, Then đều có số no ratio.
- [ ] AC-63: Given file hoặc dữ liệu đã lưu không có cột no ratio, When xem báo cáo, Then %Efficiency B (no ratio) hiện "-", các chỉ số khác không đổi.
- [ ] AC-64: Given Fac 2 tiền CM 400, sản lượng 400 và Fac 3 tiền CM 300, sản lượng 100, When xem Screen 1, Then card Total ghi Revenue 700, Output 500, Avg CM price 1,40; chỉ chọn Fac 2 thì Total bằng Fac 2.
- [ ] AC-65: Given mở Screen 1, When chưa bật nút gạt, Then bảng chỉ số không có 3 dòng with ratio - system; When bật, Then 3 dòng hiện lại. (sửa 2026-11-06: xem AC-67)
- [ ] AC-66: Given chọn cả 4 xưởng, When bật nút ＋ ở khu card, Then mỗi card có thêm dòng Fac 2, Fac 3, Fac 5 dưới HCM và Fac 2 + Fac 3 + Fac 5 khớp với HCM (Revenue, Output); When tắt, Then chỉ còn Vinh Long và HCM.
- [ ] AC-67: Given mở Screen 1, When chưa bật nút gạt, Then bảng không có %Efficiency target, MO 8h target, MO 8h vs target và 3 dòng with ratio - system, dòng đầu là Target (with ratio); When bật, Then 6 dòng đó hiện lại.
- [ ] AC-68: Given mở Screen 1 và tải Excel báo cáo tuần, When xem tên chỉ số, Then là "%Efficiency (with ratio)" và "Target (with ratio)", số không đổi so với trước.
- [ ] AC-69: Given bảng chỉ số ở Screen 1, When xem, Then cột Category có nhãn màu cho từng nhóm và các dòng cùng nhóm nằm liền nhau.
- [ ] AC-70: Given xem bất kỳ màn hình, biểu đồ hay file Excel nào, When tìm loại hiệu suất không tỉ lệ, Then tên là "%Efficiency (no ratio)" và "Target (no ratio)", số không đổi.
- [ ] AC-71: Given mở Screen 1, When chưa bật nút gạt, Then bảng không có 2 dòng no ratio (còn 11 dòng); When bật, Then 2 dòng hiện lại trong nhóm Efficiency.
- [ ] AC-72: Given chọn 24/10/2026–30/10/2026, When bấm "Download weekly report (Excel)" ở Screen 1, Then file tên `Sewing - Weekly Fac report - 24.10 to 30.10.xlsx` có sheet Overall và 4 sheet Fac x-detailed; sheet Overall có Fac 2 Efficiency Target 63.289, Actual 62.559, CM earning, MO 8h, Average CM price giống Screen 1, dòng % chữ đỏ, tiền có dấu $.
- [ ] AC-73: Given cùng khoảng ngày, When mở sheet Fac 2-detailed, Then mỗi chuyền có Target / Actual / Efficiency từng ngày, dòng Total xưởng bằng Efficiency Target / Actual của Overall, khối Earning ($) có LABOR và HOUR, khối MO 8h ($/8h) có dòng Total.
- [ ] AC-74: Given chọn Fac 2 ở Screen 2, When bấm "Download weekly report (Excel)", Then file chỉ có sheet Overall và Fac 2-detailed.
- [ ] AC-75: Given đã tải file `Data sewing 2026` có ngày 02/01/2026 Fac 2 tổng nhân sự 599, số thợ 345, When chọn 02/01/2026–02/01/2026 và chỉ Fac 2 ở Screen 1, Then card %Direct labor ghi 57.6%.
- [ ] AC-76: Given chọn cả 4 xưởng, When xem card %Direct labor, Then Total = tổng số thợ / tổng nhân sự của 4 xưởng (không lấy trung bình %), HCM tính tương tự cho Fac 2, 3, 5; When lọc một nhóm khách hàng, Then card hiện "-".
- [ ] AC-77: Given 2 dòng sản lượng SMV 10 với 100 cái và SMV 20 với 300 cái, và 1 dòng thiếu SMV, When xem card Avg SMV, Then ghi 17.50; When lọc nhóm sản phẩm chỉ còn dòng SMV 10, Then ghi 10.00.
- [ ] AC-78: Given dữ liệu số thợ lưu trước 06/11/2026 chưa có tổng nhân sự, When xem card %Direct labor, Then hiện "-"; When tải lại file, Then có số; số thợ, MO và MO 8h không đổi.
- [ ] AC-79: Given mở Screen 1, When xem, Then có 7 card trên một hàng, nút ＋ hiện thêm Fac 2, 3, 5 ở cả 7 card; không có biểu đồ "%Efficiency (no ratio) by day" và "%Efficiency (with ratio - system) by day"; biểu đồ %Efficiency (with ratio), MO 8h, Output và xếp hạng chuyền vẫn hiện.
- [ ] AC-80: Given mở Screen 1, When chưa bật nút gạt, Then bảng Metrics không có "%Efficiency (with ratio) vs target" (còn 10 dòng); When bật, Then dòng đó hiện lại trong nhóm Efficiency. File Excel báo cáo tuần không đổi.
- [ ] AC-81: Given chọn By week, 10/10/2026–23/10/2026, cả 4 xưởng ở Screen 4, When xem bảng MO 8h, Then có 2 dòng "W42 (10.10–16.10)" và "W43 (17.10–23.10)"; dòng W43 có số của từng xưởng, HCM và Total bằng MO 8h ở Screen 1 khi chọn 17/10–23/10.
- [ ] AC-82: Given chọn By month, 15/09/2026–23/10/2026, When xem, Then có 2 dòng "Sep 2026 (15.09–30.09)" và "Oct 2026 (01.10–23.10)"; By quarter cùng khoảng ngày có "Q3 2026 (15.09–30.09)" và "Q4 2026 (01.10–23.10)"; By year có "2026 (15.09–23.10)".
- [ ] AC-83: Given Fac 2 trong một tuần có 5 ngày có số thợ 300, 310, 320, 330, 340, When xem bảng Direct worker, Then Fac 2 ghi 320; HCM bằng tổng Direct worker của Fac 2, Fac 3, Fac 5.
- [ ] AC-84: Given một kỳ, When xem %Efficiency (with ratio), Output, Revenue, Avg CM price, Avg SMV, Avg working hours, Then mỗi số bằng số ở Screen 1 khi chọn đúng khoảng ngày của kỳ đó.
- [ ] AC-85: Given mở Screen 4, When xem, Then không có nút tải Excel. (sửa 2026-11-06: trước đây kiểm tra file tải về; người dùng bỏ nút tải)
- [ ] AC-86: Given mở Screen 4 lần đầu, When chưa đổi gì, Then loại kỳ là By week, khoảng ngày từ 01/01 của năm có dữ liệu mới nhất đến ngày dữ liệu mới nhất; menu ghi "Period Report"; Screen 1, 2, 3, 5, 6 không đổi.
- [ ] AC-87: Given By week, 01/01/2026–05/11/2026, cả 4 xưởng ở Screen 4, When mở tab Output, Then có 6 thẻ (Fac Vinh Long, Fac 2, Fac 3, Fac 5, HCM, Total); thẻ Fac Vinh Long ghi 151.288 là số của W45 (31.10–05.11) trong bảng, và ghi "vs W44 (24.10–29.10)" với mức thay đổi = 151.288 − Output Fac Vinh Long ở Screen 1 khi chọn 24/10–29/10.
- [ ] AC-88: Given cùng bộ lọc, When số kỳ cuối của MO 8h, %Efficiency (with ratio), Output hoặc Revenue lớn hơn số so sánh, Then mũi tên lên màu xanh; nhỏ hơn thì xuống màu đỏ; When xem tab Avg SMV, Direct worker, Avg CM price, Avg working hours, Then mũi tên không tô màu.
- [ ] AC-89: Given By week, 10/10/2026–30/10/2026, When xem thẻ, Then kỳ cuối W44 (24.10–30.10) đủ ngày và thẻ ghi "vs W43 (17.10–23.10)", so với cả tuần W43.
- [ ] AC-90: Given By year, 01/01/2026–05/11/2026, When xem thẻ, Then thẻ chỉ ghi số của năm 2026, không có mũi tên.
- [ ] AC-91: Given MO 8h kỳ cuối của một xưởng có dấu 🔴 trong bảng, When xem tab MO 8h, Then thẻ của xưởng đó cũng có 🔴; thẻ Direct worker, Output, Revenue không bao giờ có 🔴.
- [ ] AC-103: Given mở Screen 4, When kéo xuống, Then 8 chỉ số xếp dọc theo thứ tự BR-69, không có tab; mỗi chỉ số có hàng thẻ số và khối "Charts" đang đóng; When bấm "Charts" của một chỉ số, Then hiện các biểu đồ nhỏ của chỉ số đó (mỗi cột một biểu đồ, có HCM và Total).
- [ ] AC-110: Given tải file `Sewing Line Strength (14-Jul-2026).xlsx` ở Screen 7, When bấm "Check & save", Then hiện "Đã lưu sở trường của 82 chuyền."; Catalogs thẻ "Line strength" có Fac 2 / LINE 14: Pants, T-Shirt, MCC, MARK'S WORK, Medium; lịch sử tải file có dòng Saved của file đó; dữ liệu sản lượng không đổi.
- [ ] AC-111: Given đã lưu sở trường, When tải lại file đã bỏ dòng XM5 / 15, Then Fac 5 / LINE 15 không còn trong bảng (đánh dấu xoá), các chuyền khác giữ; When tải file thiếu cột `CHANGEOVER SPEED`, Then hiện "File Line Strength thiếu cột: CHANGEOVER SPEED. Hãy dùng đúng file Sewing Line Strength." và không đổi gì.
- [ ] AC-112 (sửa 2026-11-13: Matching ratio nay theo BR-86, xem AC-117; phần MO 8h, Working hours giữ): Given một chuyền có 3 ngày MO 8h 30, 33, 36, giờ làm 8, 9, 10, sản lượng 600 trong đó 100 cái `Trái sở trường`, When xem Line Detail, Then MO 8h 33.00, Working hours 9.00, Matching ratio 83.3%.
- [ ] AC-113 (sửa 2026-11-13: Changeover nay theo BR-87, xem AC-119): Given đơn `PO-7.1` lên chuyền LINE 2 lần đầu ngày 20/10, đơn `PO-7.2` ngày 25/10, đơn `PO-8.1` ngày 25/10 và đơn `PO-9.1` đã chạy từ 01/10, When chọn 24/10–30/10, Then Changeover của LINE 2 là 1 (`PO-8`); `PO-7` không tính vì ngày đầu tiên của đơn gốc là 20/10.
- [ ] AC-114: Given chọn LINE 14 của Fac 2 trong bảng, When xem chi tiết, Then thấy sở trường Pants, T-Shirt, khách MCC, MARK'S WORK, tốc độ Medium và bảng đơn hàng trong khoảng ngày; đơn loại Pants ghi Matches strength = Yes, loại Polo ghi No.
- [ ] AC-115 (sửa 2026-11-13: "Line performance" cũng bỏ khỏi menu, xem AC-122): Given mở menu Reports, When xem, Then không còn "Daily Report" và "MO by Line"; Overview, Line Detail, Sewing metrics, Line performance vẫn mở được.
- [ ] AC-116 (sửa 2026-11-13: trước đây một sheet cho xưởng đang chọn): Given Line performance 24/10/2026–30/10/2026, When bấm "Download Excel", Then tải file `Line performance - 24.10 to 30.10.xlsx` có 4 sheet `Fac Vinh Long`, `Fac 2`, `Fac 3`, `Fac 5`; mỗi sheet có tiêu đề hai tầng như mẫu, mỗi chuyền một dòng, dòng Total, số giống màn hình khi chọn xưởng đó; xưởng không có dữ liệu ghi "No data in this period.". (sửa 2026-11-13: bấm nút "Download Line performance" ở Line Detail, xem AC-122)
- [ ] AC-117 (thêm 2026-11-13): Given chuyền LINE 14 của Fac 2 có sở trường Pants, T-Shirt và trong khoảng ngày làm 300 cái nhóm Pants, 100 cái nhóm Polo, 50 cái "Chưa phân nhóm", When xem Line Detail, Then Matching ratio của LINE 14 là 75.0% (300 / 400); bảng đơn hàng ghi đơn Pants = Yes, đơn Polo = No, đơn chưa phân nhóm = "-". Given chuyền chưa có sở trường, Then Matching ratio là "-". Given một chuyền có mọi đơn Matches strength = Yes (như LINE 32 Fac Vinh Long), Then Matching ratio của chuyền đó là 100.0%.
- [ ] AC-118 (thêm 2026-11-13): Given cùng khoảng ngày, chỉ chọn một xưởng ở Overview, When so sánh, Then dòng "Line strength match" ở Overview bằng Matching ratio dòng Total ở Line Detail của xưởng đó, và bằng Matching strength ở Sewing metrics khi kỳ trùng đúng khoảng ngày đó; khi lọc một nhóm khách hàng, dòng này không còn "-" mà tính theo nhóm đã chọn.
- [ ] AC-119 (thêm 2026-11-13): Given LINE 5 chạy mã hàng X (ELAND, SMV 10.50, CM 1.20) ngày 23/10 và 24/10; mã hàng Y (MCC, SMV 8.00, CM 0.90) style A lên lần đầu ngày 24/10, ngày 25/10 chạy Y style A và Y style B (cùng khách, SMV, CM); 26/10 chuyền không có sản lượng; 27/10 chạy Y; 28/10 X lên lại; một dòng ngày 28/10 thiếu SMV, When chọn 24/10–30/10, Then Changeover của LINE 5 là 2 (Y ngày 24/10, X ngày 28/10); X ngày 24/10 không tính vì đã chạy 23/10; Y ngày 27/10 không tính vì ngày 26/10 chuyền nghỉ; dòng thiếu SMV không tính.
- [ ] AC-120 (thêm 2026-11-13): Given một đơn trên chuyền trong khoảng ngày có 2 dòng: 200 cái SMV 10.00 mục tiêu with ratio 250; 100 cái SMV 13.00 mục tiêu with ratio 90, When xem bảng đơn hàng, Then SMV 11.00, %Efficiency (with ratio) 88.2% (300 / 340); đơn không có dòng nào có mục tiêu with ratio ghi "-".
- [ ] AC-121 (thêm 2026-11-13): Given Line Detail của một xưởng và khoảng ngày, When xem bảng chuyền, Then cột %Efficiency (with ratio) đứng ngay sau Output; số của mỗi chuyền bằng Output Ratio của chuyền đó trong file Line performance (BR-78), dòng Total bằng %Efficiency (with ratio) của xưởng ở Overview; số dưới ngưỡng hiệu suất có ▼.
- [ ] AC-122 (thêm 2026-11-13): Given mở menu Reports, When xem, Then chỉ có Overview, Line Detail, Sewing metrics; Line Detail có nút "Download Line performance", không có nút tải báo cáo tuần; bấm nút ở khoảng 24/10/2026–30/10/2026 thì tải file `Line performance - 24.10 to 30.10.xlsx` giống AC-116; Overview vẫn có nút tải báo cáo tuần.
- [ ] AC-123 (thêm 2026-11-13): Given Sewing metrics By week, When kéo xuống, Then có 10 chỉ số, 2 chỉ số cuối là Matching strength và Changeover/line/day, cả hai có trên thanh "Jump to"; Given một tuần Fac 2 có Changeover tổng 3, 6 ngày làm việc, 14 chuyền, Then Changeover/line/day của Fac 2 tuần đó là 0.036; mũi tên Matching strength tăng màu xanh, Changeover/line/day không tô màu.
- [ ] AC-124 (thêm 2026-11-13, giữ phần cũ): Given cùng dữ liệu, When xem Line Detail và Sewing metrics, Then Output, MO 8h, Working hours của bảng chuyền, 8 chỉ số cũ của Sewing metrics (AC-81 đến AC-84, AC-103, AC-104) và file Line Strength (AC-110, AC-111) không đổi; dữ liệu đã lưu không mất dòng nào.
- [ ] AC-125 (thêm 2026-11-13 lần 2): Given Line Detail Fac Vinh Long, Đến ngày 30/10/2026, chọn LINE 25, When chọn By month, Then "Line trend" có các kỳ Jan 2026 … Oct 2026 (chỉ các tháng LINE 25 có sản lượng), biểu đồ cột Output, biểu đồ đường %Efficiency (with ratio) và bảng số 3 dòng; cột Oct 2026 có Output và %Efficiency bằng dòng LINE 25 của bảng chuyền khi chọn 01/10/2026–30/10/2026, MO 8h bằng cột MO 8h của dòng đó.
- [ ] AC-126 (thêm 2026-11-13 lần 2): Given cùng chuyền, When chọn By week, Then kỳ cuối là W44 (24.10–30.10) và số khớp bảng chuyền khi chọn 24/10–30/10; When bấm nút MO 8h, Then biểu đồ đường đổi sang MO 8h, biểu đồ cột và bảng số không đổi; số dưới ngưỡng trong bảng số có ▼.
- [ ] AC-127 (thêm 2026-11-13 lần 2): Given đang lọc Customer group = SANMAR, When xem "Line trend" của LINE 25, Then Output và %Efficiency chỉ tính các dòng SANMAR, dòng MO 8h ghi "-".
- [ ] AC-128 (thêm 2026-11-13 lần 2, giữ phần cũ): Given cùng bộ lọc, When mở Line Detail, Then bảng chuyền, khối sở trường, bảng đơn hàng và nút "Download Line performance" giống trước (AC-117 đến AC-122 vẫn đúng).
- [ ] AC-129 (thêm 2026-11-13 lần 3): Given "Line trend" By month của một chuyền có tháng %Efficiency 81.5% (dưới ngưỡng 85% của Fac Vinh Long) và tháng 100.5%, When xem biểu đồ, Then cột tháng 81.5% màu cam "Below threshold", cột tháng 100.5% màu xanh dương "On target", có chú thích màu; Output trên cột không đổi.
- [ ] AC-130 (thêm 2026-11-13 lần 3): Given chọn By week, Đến ngày 30/10/2026, When xem "Line trend", Then có tối đa 26 tuần, tuần cuối W44 (24.10–30.10), biểu đồ dạng cột có màu; By month vẫn từ Jan 2026.
- [ ] AC-131 (thêm 2026-11-13 lần 3): Given đã kéo xuống khối chi tiết chuyền, When bấm "Back to filters", Then trang cuộn về ô bộ lọc; dòng tóm tắt ghi đúng xưởng, khoảng ngày và các nhóm đang lọc.
- [ ] AC-132 (thêm 2026-11-13 lần 4): Given mở Overview, When kéo hết trang, Then không còn "Output vs Target (with ratio - system) by factory" và phần xếp hạng chuyền; thẻ số, bảng chỉ số (luôn mở, cùng chỗ), nút tải báo cáo tuần và 2 biểu đồ theo ngày vẫn có, số không đổi (AC-75 đến AC-80 vẫn đúng).
- [ ] AC-133 (thêm 2026-11-13 lần 4): Given Fac 2 trong khoảng ngày làm 600 cái T-Shirt, 300 cái Pants, 100 cái Polo, When xem Cơ cấu hàng theo xưởng, Then cột Fac 2 chia T-Shirt 60%, Pants 30%, Polo 10%; bảng có dòng T-Shirt: Fac 2 600 pcs 60.0%; khi lọc nhóm khách hàng thì chỉ tính các dòng của nhóm đó.
- [ ] AC-134 (thêm 2026-11-13 lần 4): Given 12 nhóm khách hàng có sản lượng, When xem Top khách hàng, Then có đúng 10 nhóm lớn nhất, mỗi cột chia màu theo xưởng, tổng mỗi cột bằng sản lượng của nhóm đó.
- [ ] AC-135 (thêm 2026-11-13 lần 4): Given nhóm Polo có 200 cái giá 1.5 và 100 cái giá 2.1, When xem Giá CM trung bình theo nhóm hàng, Then Polo = 1.70 (510 / 300).
- [ ] AC-136 (thêm 2026-11-13 lần 4): Given Đến ngày 30/10/2026, When xem Cơ cấu hàng theo tháng, Then có các tháng từ Jan 2026 đến Oct 2026 có sản lượng, mỗi tháng tổng bằng sản lượng tháng đó của các xưởng đã chọn.
- [ ] AC-137 (thêm 2026-11-13 lần 4): Given file `Data sewing 2025 (format 2026).xlsx` chỉ có sheet `Production data`, ngày 02/01/2025–31/12/2025, When bấm "Check & save", Then lưu được; số thợ Fac 2 ngày 02/01/2025 = tổng số người các chuyền Fac 2 hôm đó; Sewing metrics By month năm 2025 có MO 8h và %Efficiency (with ratio), %Direct labor "-"; dữ liệu 2026 không đổi.
- [ ] AC-138 (thêm 2026-11-13 lần 4): Given file chỉ có sheet `Production data` nhưng có một ngày 05/01/2026, When bấm "Check & save", Then báo "File thiếu sheet: Target system, Worker. Hãy dùng đúng file Data sewing." và không lưu gì (AC của BR-02 vẫn đúng).
- [ ] AC-139 (thêm 2026-11-13 lần 4): Given file 2025 có dòng `SHCM-Factory 1`, When lưu, Then các dòng đó được lưu (lịch sử tải file đếm vào số dòng lưu), nhưng không có "Fac 1 HCM" ở bộ lọc, thẻ số, bảng, biểu đồ, file Excel nào; HCM và Total không đổi.
- [ ] AC-140 (thêm 2026-11-13 lần 4, giữ phần cũ): Given cùng dữ liệu 2026, When mở Line Detail, Sewing metrics, Data Update, Then số không đổi so với trước khi lưu file 2025 cho các khoảng ngày trong 2026.
- [ ] AC-105 (sửa 2026-11-13: Screen 6 bỏ khỏi menu; AC-105, AC-108, AC-109 chỉ còn để tham khảo, số của BR-78 đến BR-80 vẫn kiểm tra qua file ở AC-106, AC-107, AC-116): Given mở Screen 6 lần đầu, When chưa đổi gì, Then menu ghi "Line performance" ở vị trí cũ của Changeover, khoảng ngày là tuần thứ Bảy đến thứ Sáu đầy đủ gần nhất, xưởng Fac Vinh Long; bảng có các cột Line, Number of Operators, Output Target / Actual / Ratio, Value Target / Actual / Ratio, MO $ (8h) và dòng Total.
- [ ] AC-106: Given một chuyền có 2 ngày, số người 20 và 30, 3 dòng sản lượng (100 cái mục tiêu 120 giá 1.5; 50 cái mục tiêu 40 giá 2; 30 cái không có mục tiêu giá 1), When xem chuyền đó, Then Operators 25.0; Output Target 160, Actual 180, Ratio 93.8% (150/160); Value Target 260.00, Actual 280.00, Ratio 96.2% (250/260).
- [ ] AC-107: Given cùng khoảng ngày và xưởng, When so dòng Total với Screen 1, Then Output Actual = Output, Output Ratio = %Efficiency (with ratio), Value Actual = CM earning, MO $ (8h) = MO 8h của xưởng ở Screen 1; MO $ (8h) của từng chuyền bằng cột Cả kỳ ở Screen 5 (MO by Line).
- [ ] AC-108: Given Ratio của Output một chuyền dưới ngưỡng hiệu suất của xưởng, When xem, Then ô ghi kèm ▼ và dưới bảng có "▼ below threshold".
- [ ] AC-109: Given mở Screen 6, When xem, Then không có nút tải Excel (sửa 2026-11-11: trước đây kiểm tra file tải về; người dùng bỏ nút tải); số đổi mã hàng tuần vẫn nhập được ở Screen 7 và vẫn có trong file báo cáo tuần (AC-72 vẫn đúng).
- [ ] AC-104: Given mở Screen 4 có dữ liệu, When bấm thẻ "Output" trên thanh "Jump to", Then trang cuộn tới khối Output (pcs); When bấm "Back to top" ở cuối khối, Then trang cuộn về thanh "Jump to".
- [ ] AC-92 (sửa 2026-11-10: tab bỏ, xem AC-103; phần còn lại giữ): Given mở Screen 4, When xem, Then có 8 tab theo đúng thứ tự BR-69; mỗi tab có một biểu đồ nhỏ cho mỗi cột (cả HCM và Total) và bảng số; số trong bảng không đổi (AC-81 đến AC-84 vẫn đúng); bộ lọc và mặc định như AC-86; chọn chỉ 1 xưởng HCM thì không có thẻ và biểu đồ HCM.
- [ ] AC-93: Given By month, 01/01/2026–05/11/2026, cả 4 xưởng, When mở "Exact numbers by period" ở tab MO 8h, Then bảng có 6 dòng Fac Vinh Long, Fac 2, Fac 3, Fac 5, HCM, Total và các cột Jan 2026 … Nov 2026 (01.11–05.11); ô Fac 2 / Feb 2026 ghi 38,07 🔴 như trước khi xoay.
- [ ] AC-99: Given mở Screen 4, When xem menu và tiêu đề, Then ghi "Sewing metrics"; đường dẫn `/thynguyen-sewing-productivity-monthly` vẫn mở được trang; quyền đã cấp không đổi.
- [ ] AC-100: Given bất kỳ màn hình nào của app, When xem số, Then Output ghi `151,288`, MO 8h ghi `33.50`, %Efficiency ghi `91.4%`; file Excel xuất ra vẫn là ô số như trước.
- [ ] AC-101: Given một ô có dấu dưới ngưỡng theo BR-28 (ví dụ MO 8h Fac 2 Feb 2026), When xem bảng, Then ô ghi `38.07 ▼`, không còn 🔴, dưới bảng có "▼ below threshold"; thẻ số dưới ngưỡng có tên cột màu đỏ kèm ▼.
- [ ] AC-102: Given By week, 01/01/2026–05/11/2026, cả 4 xưởng, When mở tab Direct worker, Then có thêm hàng thẻ %Direct labor (Fac Vinh Long, Fac 2, Fac 3, Fac 5, HCM, Total); mỗi số bằng card %Direct labor ở Screen 1 khi chọn 31/10–05/11; mũi tên so với W44 (24.10–29.10), không tô màu.
- [ ] AC-94: Given đã lưu một file, When lưu lại file đó với 1 dòng Fac 2 đổi sản lượng, 1 dòng Fac 3 mới và bỏ 1 dòng Fac 5 trong khoảng ngày, Then dòng lịch sử mới ghi Saved; bảng thay đổi có Production data / Fac 2 Cập nhật 1, Fac 3 Thêm mới 1, Fac 5 Ẩn đi 1; dòng Fac 5 vẫn còn trong thùng rác (đánh dấu xoá).
- [ ] AC-95: Given file có 1 dòng thiếu PO# và 1 cảnh báo ngày chưa có số thợ, When lưu, Then chi tiết lần tải có bảng sheet (Production data: đọc 3, hợp lệ 2, bỏ qua 1), dòng bị bỏ qua đúng số dòng và lý do, và cảnh báo đúng ngày, giống kết quả hiện ngay sau khi lưu.
- [ ] AC-96: Given chọn file .pdf hoặc file thiếu sheet Worker, When bấm "Check & save", Then màn hình hiện thông báo BR-01 / BR-02 như trước, không lưu dữ liệu nào, và lịch sử có thêm dòng Rejected với đúng câu thông báo đó; "Last file upload" của báo cáo không đổi.
- [ ] AC-97: Given người không có vai trò UPDATER, When tải file, Then bị chặn bằng thông báo BR-09 và lịch sử không có dòng mới.
- [ ] AC-98: Given dòng lịch sử lưu trước 09/11/2026, When chọn dòng đó, Then các cột mới hiện "-", trạng thái Saved, và chi tiết ghi "Lần tải trước 09/11/2026 không có chi tiết."; AC-13 vẫn đúng.

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
- Mở rộng 2026-11-05: đổi tên app thành Sewing Performance, tên trên màn hình và Excel sang tiếng Anh, thêm cột HCM, nhãn số cho biểu đồ, khối Summary, in đậm %Efficiency và MO 8h. Xem `docs/plans/sewing_productivity-extension-20261105.md`.
- Giả định: Đường dẫn app giữ `/thynguyen-sewing-productivity` và mã `sewing_productivity`, để không ảnh hưởng dữ liệu và quyền đã cấp.
- Giả định: Cột HCM chỉ thêm ở bảng có cột theo xưởng (Screen 1, Screen 3 và Excel của chúng). Screen 2, 4, 5, 6 giữ theo từng xưởng.
- Giả định: Biểu đồ dùng chung không ghi số trên từng điểm, nên nhãn số đặt ở chú thích và tên cột (BR-54).
- Giả định: In đậm chỉ áp dụng trên màn hình, file Excel không đổi cách trình bày (BR-49).
- Mở rộng 2026-11-05: thêm %Efficiency B (no ratio) và đặt lại tên 3 loại hiệu suất (BR-55, BR-56). Dữ liệu đã lưu trước đó cần tải lại file để có số này.
- Mở rộng 2026-11-06: gộp kiểm tra và lưu file thành một nút (BR-57). App không đọc file theo đường dẫn trên máy người dùng: app chạy trên server, không thấy thư mục OneDrive của từng người (xem `docs/capabilities.md`).
- Mở rộng 2026-11-06: 5 card Vinh Long - HCM có dòng Total ở Screen 1 (BR-58, UC-27). Total chỉ hiện ở card, không thêm vào bảng chỉ số và file Excel.
- Giả định: Người dùng nói "4 card ... 5 chỉ số"; làm 5 card, mỗi chỉ số một card.
- Mở rộng 2026-11-06 (prompt 05): nút ＋ tách HCM trong card, bảng chỉ số gọn lại theo kiểu bảng Excel báo cáo tuần, đổi tên %Efficiency (with ratio) (BR-56 sửa, BR-59 sửa, BR-60, BR-61). Xem `docs/plans/sewing_productivity-extension-20261106.md`.
- Giả định: Bảng của app không tô nền từng ô như Excel, nên màu chỉ nằm ở nhãn nhóm của cột Category.
- Mở rộng 2026-11-06 lần 2 (prompt 05): file báo cáo tuần theo mẫu họp (UC-28, BR-64), đổi tên no ratio và ẩn 2 dòng no ratio (BR-56, BR-61 sửa). Xem `docs/plans/sewing_productivity-extension-20261106b.md`.
- Giả định (triển khai): UC-28 dùng chung chức năng tải của UC-11 (thêm lựa chọn "mẫu họp") để giữ nguyên số chức năng của app; file kiểu cũ vẫn tạo được nhưng không còn nút nào tải.
- Đã đối chiếu tuần 24–30/10/2026 với file mẫu: sheet Overall khớp mục tiêu, sản lượng, %Efficiency, CM earning, Average CM price, Matching ratio; MO 8h và giờ làm của Fac Vinh Long lệch nhẹ (33,64 so với 33,78) như giả định ở trên; Changeover time là "-" khi chưa nhập số đổi mã hàng tuần.
- Giả định: File báo cáo tuần mới ghi số, không ghi công thức; không có sheet dữ liệu thô, các sheet ẩn và bảng nhỏ dùng cho biểu đồ (dòng 27-29) của file mẫu.
- Giả định: File hằng ngày luôn có vài dòng cuối chưa có ngày (16 dòng ở file ngày 06/11/2026), nên nút vẫn lưu khi có dòng bị bỏ qua và chỉ dừng khi file bị từ chối.
- Giả định: Mục tiêu và ngưỡng hiện có chỉ dùng cho 2 loại có tỉ lệ. %Efficiency B (no ratio) không có dấu 🔴 và không có dòng so với mục tiêu, vì chưa có mức riêng.
- Mở rộng 2026-11-06 lần 3 (prompt 05): thêm card Avg SMV và %Direct labor (BR-65, BR-66, sửa BR-58), đọc thêm tổng nhân sự từ sheet Worker; bỏ 2 biểu đồ theo ngày (BR-67); ẩn mặc định dòng "%Efficiency (with ratio) vs target" (sửa BR-61). Xem `docs/plans/sewing_productivity-extension-20261106c.md`.
- Giả định: File cũ không có khối `TOTAL` trong sheet Worker vẫn tải được; %Direct labor của các ngày đó hiện "-".
- Giả định: Dữ liệu số thợ đã lưu giữ nguyên; tổng nhân sự để trống đến khi tải lại file, không cần chuyển dữ liệu.
- Mở rộng 2026-11-06 lần 4 (prompt 05): Screen 4 đổi thành Period Report, xem theo tuần, tháng, quý, năm (UC-29, UC-30, BR-68, BR-69); bảng theo ngày của báo cáo tháng bỏ khỏi màn hình (UC-08, UC-13). Xem `docs/plans/sewing_productivity-extension-20261106d.md`.
- Giả định: Không lưu thêm dữ liệu nào; báo cáo theo kỳ tính từ dữ liệu đã lưu.
- Giả định (triển khai): UC-29 dùng chung chức năng xem của UC-08 với lựa chọn loại kỳ, để giữ nguyên số chức năng của app (bài kiểm tra cũ ghim số này); UC-08, UC-13 vẫn còn ở phía app nhưng không còn màn hình nào gọi. Đường dẫn trang giữ `.../monthly` để quyền đã cấp không đổi.
- Giả định (triển khai): Biểu đồ của Screen 4 chỉ vẽ các xưởng; HCM và Total nằm trong bảng, vì với Output, Revenue, Direct worker số cộng của nhóm lớn hơn nhiều sẽ làm các đường xưởng bị dẹt. Mỗi điểm đặt ở ngày đầu của kỳ.
- Giả định (triển khai): Xem theo tuần cả năm lần đầu mất vài giây; mở lại cùng bộ lọc thì nhanh vì app nhớ kết quả.
- Giả định: Số tuần là số tuần ISO của ngày thứ Sáu cuối tuần, để tuần 17.10–23.10 là W43 như cách gọi đã thống nhất.
- Giả định (dữ liệu từ khảo sát): Giờ làm Fac 1 trong file họp tuần thấp hơn app vì công thức dòng TOTAL Fac 1 của sheet `Working Hours` trong file Data sewing chỉ lấy LINE 1–15; app giữ cách lấy trung bình mọi chuyền có sản xuất (BR-20).
- Giả định (triển khai): Bảng màu có sẵn của app không có xanh ngọc, nên card Avg SMV dùng mã màu riêng (#0F9D8F) và %Direct labor dùng xám xanh (#5B7083), chỉ đổi màu chữ, không thêm định dạng nào khác.
- Mở rộng 2026-11-08 (prompt 05): Screen 4 dễ nhìn hơn theo phương án A: mỗi chỉ số một tab, thẻ số mỗi cột có mũi tên so với kỳ trước, mỗi cột một biểu đồ nhỏ có thang riêng (BR-70, BR-71, sửa UC-29). Xem `docs/plans/sewing_productivity-extension-20261108.md` và khảo sát `docs/business/_sources/sewing_productivity-period-report-ui-discovery.md`.
- Giả định: Giữ cả 4 loại kỳ tuần, tháng, quý, năm, mặc định By week (AC-86 không đổi). Kỳ thiếu ngày vẫn được vẽ.
- Giả định: Revenue tăng là tốt như Output; Direct worker, Avg CM price, Avg working hours không tô màu mũi tên (người dùng chọn đề xuất 08/11/2026).
- Giả định: Biểu đồ của Screen 4 nay vẽ cả HCM và Total vì mỗi cột có biểu đồ và thang riêng (sửa giả định ngày 2026-11-06 ở trên: trước đây chỉ vẽ các xưởng).
- Giả định: Không lưu thêm dữ liệu, không chuyển dữ liệu; thẻ số tính từ dữ liệu đã lưu như bảng.
- Giả định (triển khai): Biểu đồ nhỏ xếp 2 biểu đồ mỗi hàng thay vì 3: ở màn hình rộng 1440 px, 3 biểu đồ mỗi hàng làm nhãn tháng dưới trục dính vào nhau, khó đọc.
- Giả định (triển khai): Thẻ số nằm trên một hàng khi số ngắn (MO 8h, %Efficiency, Avg SMV...); với số dài như Output, Revenue thì 3 thẻ mỗi hàng, vì 6 thẻ một hàng bị cắt số ("151.2…").
- Giả định (triển khai): Output, Revenue, Direct worker vẽ cột khi có dưới 30 kỳ (tháng, quý, năm, hoặc ít tuần); từ 30 kỳ trở lên (xem theo tuần cả năm) vẽ vùng tô màu, vì biểu đồ cột dùng chung chỉ giữ 30 cột và gộp phần còn lại vào "Khác".
- Giả định (triển khai): Tên trên màn hình bằng tiếng Anh như phần còn lại của app (BR-52): khối gấp bảng số tên "Exact numbers by period"; dòng ghi kỳ so sánh đặt trên hàng thẻ và trong dấu ? của từng thẻ, vì dòng chữ trong thẻ bị cắt khi thẻ hẹp. Tab đang xem được nhớ trong phiên làm việc; khởi động lại app thì về tab MO 8h.
- Mở rộng 2026-11-13 (prompt 05): gộp Line performance vào Line Detail (chỉ còn nút "Download Line performance", bỏ nút báo cáo tuần ở Line Detail); Matching tính theo bảng sở trường chuyền ở Line Detail, Overview, file báo cáo tuần và Sewing metrics (BR-86, sửa BR-25, BR-29, BR-83, BR-84); Changeover đếm theo mã hàng Khách hàng + SMV + CM, lên lại sau ít nhất 1 ngày làm việc thì tính thêm (BR-87); bảng chuyền thêm %Efficiency (with ratio); bảng đơn hàng thêm SMV, %Efficiency (with ratio) (BR-88); Sewing metrics thêm Matching strength, Changeover/line/day (BR-89). Xem `docs/plans/sewing_productivity-extension-20261113.md`.
- Giả định: Người dùng chọn toàn bộ đề xuất (13/11/2026, "ok all"). File `Data sewing 2026 - MATCH STRENGTH.xlsx` chỉ để tham khảo cách tính đúng / trái sở trường (nhóm sản phẩm so với STRENGTH 1-4 của chuyền); app không đọc file này và không đọc cột `Match line strength`.
- Giả định: "Khách hàng" khi đếm Changeover là nhóm khách hàng (BR-15), để cùng một khách viết khác nhau (ví dụ `ELAND`, `ELAND WORLD LTD.,`) không bị đếm thành đổi mã hàng. SMV và giá CM so sánh sau khi làm tròn 6 chữ số lẻ như các giả định đổi mã hàng trước.
- Giả định: Sở trường đang lưu (file Line Strength mới nhất) áp cho mọi ngày, kể cả ngày trước khi tải file; app không giữ sở trường theo từng thời kỳ.
- Giả định: Bảng dùng chung của app không đổi được cỡ chữ hay màu từng ô (xem giả định ngày 08/11/2026 ở dưới); "nổi bật, dễ đọc" cho %Efficiency và MO 8h sẽ chốt ở vòng giao diện bằng cách bảng dùng chung làm được.
- Giả định: Cột Matches strength của bảng đơn hàng giữ nguyên cách BR-84 (Yes khi mọi nhóm sản phẩm của đơn là nhóm mạnh), cùng cách so của BR-86 nên đơn Yes thì mọi dòng của đơn được tính đúng sở trường.
- Cập nhật 2026-11-13 (người dùng yêu cầu): app chỉ chạy trên máy người làm (Run mode Local), không gửi duyệt vào `dev`. Theo yêu cầu, nhánh của app được đặt lên bản `dev` mới nhất (có các biểu đồ mới: gộp cột + đường hai thang, ghi số trên biểu đồ...) và lưu lên GitHub để giữ an toàn, thay vì gộp vào nhánh máy cá nhân dựng trên `main`.
- Mở rộng 2026-11-13 lần 4 (prompt 05): Overview bỏ Output vs Target (system) và Ranking, thêm khu "Products & customers" (BR-92 đến BR-96); nhận file năm cũ chỉ có `Production data`, số thợ tính từ các chuyền (BR-97, 4.3 `derived`); lưu xưởng đã giải thể Fac 1 HCM chỉ để tham khảo (BR-98). Xem `docs/plans/sewing_productivity-extension-20261113d.md`.
- Giả định: Người dùng trả lời "1a, 2abcd, 3b, 4a, 5a" và "Fac 1 là 1 xưởng cũ đã giải thể ... chỉ để ref cho 2025" (13/11/2026). Dữ liệu 2025 do người dùng tải một lần ở Data Update (app không tự đọc file trong OneDrive). Cơ cấu hàng theo tháng dùng khoảng từ 01/01 đến "Đến ngày" như "Line trend", vì khoảng mặc định của Overview chỉ 1 tuần. Biểu đồ dùng chung tối đa 6 màu, nên 5 nhóm lớn nhất + "Other"; bảng cạnh biểu đồ có đủ mọi nhóm.
- Mở rộng 2026-11-13 lần 3 (prompt 05): cột Output của "Line trend" có màu theo kết quả %Efficiency, By week 26 tuần gần nhất, dòng tóm tắt bộ lọc và "Back to filters" (BR-91). Xem `docs/plans/sewing_productivity-extension-20261113c.md`.
- Giả định: Người dùng chọn 1b (không ghi đề nghị biểu đồ gộp có số / ô bộ lọc dính đầu trang gửi người phụ trách khung sườn), 2a, 3a (13/11/2026). App không tự làm được biểu đồ gộp cột + đường có số trên điểm và ô bộ lọc dính đầu trang: hai việc này thuộc khung sườn.
- Giả định (triển khai, 2026-11-13 lần 3): màu cột lấy theo thứ tự màu cố định của biểu đồ dùng chung (xanh dương trước, cam sau, xanh nhạt thứ ba), không chọn được tím / đỏ như hình mẫu. 26 tuần là 26 tuần lịch (thứ Bảy đến thứ Sáu) gần nhất, tuần không có sản lượng của chuyền không hiện, nên có thể ít hơn 26 cột. Ô bộ lọc có tiêu đề cỡ lớn hơn một chút để làm mốc cho "Back to filters".
- Mở rộng 2026-11-13 lần 2 (prompt 05): "Line trend" theo tuần / tháng / năm trong chi tiết chuyền của Line Detail (BR-90, sửa UC-06, Screen 2). Xem `docs/plans/sewing_productivity-extension-20261113b.md`.
- Giả định: Người dùng chọn toàn bộ đề xuất (13/11/2026, "all đề xuất"). Người dùng muốn một biểu đồ cột + đường có số ghi trên biểu đồ; biểu đồ dùng chung chưa làm được (đã ghi chờ khung sườn ngày 09/11/2026), nên tạm dùng 2 biểu đồ chung trục thời gian và bảng số ngay dưới. Không lưu thêm dữ liệu.
- Giả định: Xem By week cả năm có hơn 30 kỳ; biểu đồ cột dùng chung chỉ giữ 30 cột (gộp phần còn lại vào "Khác"), nên khi có từ 30 kỳ trở lên, Output vẽ dạng vùng tô màu như Sewing metrics (giả định ngày 08/11/2026).
- Giả định (triển khai, 2026-11-13 lần 2): "Line trend" đi qua chức năng xem Line Detail (UC-06) với tên chuyền và loại kỳ, để giữ nguyên số chức năng của app; app chỉ tính phần này khi đã chọn một chuyền. Mở lần đầu sau khi khởi động app chậm hơn vì app nạp dữ liệu; sau đó mỗi lần đổi kỳ dưới 1 giây.
- Giả định (triển khai, 2026-11-13): cột luôn đứng bên trái của bảng luôn nằm đầu bảng, nên thứ tự là Line, %Efficiency (with ratio), rồi Output (BR-83 ghi "sau Output"; người dùng chọn cột %Efficiency luôn đứng bên trái). Ô thanh màu trống nghĩa là "-". Thanh %Efficiency đầy ở 120%, màu đi từ đỏ (thấp) sang xanh (cao); số trên thanh vẫn là số thật.
- Giả định (triển khai, 2026-11-13): khi đếm Changeover (BR-87), ngày chuyền chỉ có dòng thiếu SMV không tính là ngày làm việc (không tạo cách quãng giả), như BR-37.
- Giả định (triển khai, 2026-11-13): nút "Download Line performance" hiện cả khi xưởng đang chọn không có dữ liệu trong khoảng ngày, vì file gồm 4 xưởng. Trang Line performance được gỡ khỏi app (mỗi trang của app phải nằm trong menu); quyền đã cấp cho trang đó không còn tác dụng.
- Giả định (triển khai, 2026-11-13): thẻ số của Screen 4 không có lựa chọn màu, nên màu xanh lá / tím của 2 chỉ số mới nằm ở tiêu đề chỉ số. Sewing metrics theo tuần cả năm mất khoảng 4 giây lần đầu (đếm Changeover trên toàn bộ dữ liệu); mở lại cùng bộ lọc thì nhanh vì app nhớ kết quả.
- Sửa 2026-11-13 (người dùng yêu cầu): nút "Download Excel" của Line performance tải một file 4 sheet cho 4 xưởng (BR-85, UC-32, AC-116 sửa).
- Mở rộng 2026-11-12 (prompt 05): bỏ Screen 3, Screen 5 khỏi menu; Line Detail đổi thành bảng chuyền + chi tiết chuyền (BR-83, BR-84, sửa UC-06); lưu sở trường chuyền từ file Line Strength (4.11, UC-33, UC-34, BR-81, BR-82); làm lại nút tải Excel Line performance (UC-32, BR-85). Xem `docs/plans/sewing_productivity-extension-20261112.md`.
- Giả định: Không đọc dữ liệu nào từ file báo cáo họp tuần, chỉ tham khảo cách trình bày (người dùng, 12/11/2026). Matching ratio theo sản lượng và cột `Match line strength`; Changeover đếm mã đơn gốc mới lên chuyền; "đơn hàng tuần trước" là các đơn trong khoảng ngày đang chọn (mặc định tuần gần nhất); sở trường tải bằng file ở Data Update, chỉ xem ở Catalogs; nhóm hàng dùng danh mục Nhóm sản phẩm (người dùng chọn toàn bộ đề xuất).
- Giả định (triển khai): UC-33 đi qua chức năng kiểm tra / lưu file của UC-01, UC-02 (app nhận ra file Line Strength khi file không có sheet nào của file dữ liệu); UC-34 qua chức năng xem danh mục UC-21; UC-32 qua chức năng tải của UC-15 - để giữ nguyên số chức năng của app (bài kiểm tra cũ ghim số này). Hai trang Daily Report, MO by Line bị gỡ khỏi app (mỗi trang của app phải nằm trong menu); UC-07, UC-09, UC-12, UC-14 còn phía app. Lần tải file Line Strength không tính là "Last file upload" của báo cáo. Bảng đơn hàng của Line Detail không tính theo cột trong file họp tuần, chỉ theo dữ liệu đã lưu.
- Giả định: Dòng XM1 / 34 trong file không có nhóm hàng nào vẫn được lưu (chuyền có, sở trường trống). Số 82 chuyền ở AC-110 đếm theo file 14-Jul-2026 (34 + 14 + 19 + 15).
- Mở rộng 2026-11-11 (prompt 05): Screen 6 "Changeover" thay bằng "Line performance" theo mẫu báo cáo chuyền của người dùng (UC-31, BR-78 đến BR-80, sửa BR-31 cho Screen 6; UC-32 tải Excel bị bỏ khi chốt: "không cần down file excel, đồng ý all"); thêm thanh "Jump to" ở Screen 4 (AC-104). Xem `docs/plans/sewing_productivity-extension-20261111.md`.
- Giả định (triển khai): UC-31 dùng chung chức năng xem của UC-10 với lựa chọn `line_performance` (số chức năng của app được ghim ở bài kiểm tra cũ); UC-10, UC-15 vẫn còn phía app nhưng không còn màn hình nào gọi. Bảng không có tiêu đề hai tầng như file mẫu (bảng dùng chung chỉ có một hàng tiêu đề), nên tên cột ghi đủ: "Output Target (pcs)", "Value Ratio"... Thanh "Jump to" là các liên kết chữ (app không có nút chuyển trang trong cùng trang); "Back to top" ở cuối mỗi chỉ số.
- Giả định: "cột đầu là target %Efficiency (with ratio)" được hiểu là Output Target = mục tiêu with ratio (sản lượng mục tiêu dùng để tính %Efficiency (with ratio)); Value Actual = tiền CM; dòng thiếu mục tiêu bỏ khỏi hai vế của Ratio (người dùng chọn toàn bộ đề xuất, 11/11/2026).
- Mở rộng 2026-11-09 lần 2 (prompt 05): Screen 4 đổi tên "Sewing metrics"; số viết `1,234.56` ở mọi màn hình (BR-75); dấu 🔴 thay bằng ▼ và tên thẻ màu đỏ (BR-76, sửa BR-28); thêm thẻ %Direct labor ở tab Direct worker (BR-77). Xem `docs/plans/sewing_productivity-extension-20261109b.md`.
- Yêu cầu chờ khung sườn (09/11/2026): hiện số ngay trên từng điểm của biểu đồ, và nhãn trục / số khi rê chuột trên biểu đồ viết theo BR-75. Biểu đồ dùng chung (`line_chart`, `bar_chart`) chưa có lựa chọn này; người phụ trách khung sườn bổ sung thì app áp dụng. Trong lúc chờ: số chính xác ở thẻ số, khi rê chuột và trong bảng.
- Giả định: Người dùng chọn toàn bộ đề xuất (09/11/2026): đổi cách viết số cho cả app, giữ đường dẫn `.../monthly`, ghi yêu cầu số trên điểm biểu đồ cho khung sườn. Ký hiệu ▼ do AI chọn khi người dùng nhờ "tìm cách bỏ dấu đỏ bằng signal khác": bảng dùng chung chưa tô màu từng ô, ▼ là chữ thường, đọc được cả khi in đen trắng.
- Mở rộng 2026-11-09 (prompt 05): mỗi lần tải file được ghi lại đầy đủ để theo dõi: số theo sheet, dòng bị bỏ qua, cảnh báo, số dòng thêm mới / cập nhật / ẩn đi theo xưởng, cả lần bị từ chối (BR-72 đến BR-74, sửa UC-01, UC-02, UC-03, Screen 7). Xem `docs/plans/sewing_productivity-extension-20261109.md`.
- Giả định (triển khai): Sheet Worker ghi số dòng đọc được = hợp lệ = số cặp xưởng - ngày có số thợ, bỏ qua = 0 (dòng không có ngày bị bỏ qua không báo, như trước). Lần tải bị từ chối được ghi ngay ở bước kiểm tra của nút "Check & save"; nếu bước lưu từ chối file thì cũng ghi.
- Giả định: Không giữ file Excel gốc (mỗi file tới 50 MB). Chỉ người có vai trò UPDATER xem lịch sử như trước. Dòng lịch sử cũ giữ nguyên, không có chi tiết (người dùng chọn toàn bộ đề xuất, 09/11/2026).
- Giả định (triển khai): Người dùng muốn số dưới ngưỡng ở bảng Screen 4 ghi bằng chữ đỏ thay dấu 🔴 (08/11/2026). Bảng dùng chung của app chưa tô màu được từng ô, nên vẫn giữ 🔴 (BR-28) cho đến khi người phụ trách khung sườn bổ sung.

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
| UC-27 | `get_overview`, `get_charts`, `get_daily_report`, `export_weekly_report`, `export_daily_report` -> `ReportBusiness.hcm_summary`, `hcm_daily_summary`, `hcm_days` |
| BR-51 | `business/report_business.py::ReportBusiness.hcm_members`, `_common_goal`, `_members_mo8h` |
| BR-52 | `dto/display_names.py`, `builders/display.py::file_sheets`, frontend pages |
| BR-53 | `frontend/features/sewing_productivity/components/report_cells.py` |
| BR-54 | `frontend/features/sewing_productivity/components/overview_charts.py` |
| BR-55 | `business/productivity_business.py::ProductivityBusiness.target_no_ratio`, `efficiency_no_ratio` |
| BR-56 | `dto/display_names.py` |
| BR-58 | `business/report_business.py::ReportBusiness.total_summary`, `components/overview_charts.py::group_summary` |
| BR-59, BR-61 | `frontend/features/sewing_productivity/components/report_cells.py` (`METRIC_GROUPS`, `HIDDEN_METRICS`, `grouped_metric_rows`), `pages/overview_page.py` |
| BR-60 | `frontend/features/sewing_productivity/components/overview_charts.py` (`group_summary`, `_hcm_detail_button`) |
| UC-28, BR-64 | `export_weekly_report` -> `ExportWeeklyReportService` với `ExportWeeklyRequest.meeting_format`, `builders/meeting_report_builders.py::MeetingReportFileBuilder` |
| BR-57 | `frontend/features/sewing_productivity/components/upload_blocks.py::_check_and_save` |
| Tổng nhân sự (4.3, 5.1) | `constants.py::WORKER_TOTAL_COLUMNS`, `builders/upload_read_builders.py::RawWorkbookBuilder._worker_rows`, `business/upload_business.py::UploadBusiness._worker_records`, `models/source_records.py::WorkerRecord.total_workers` |
| BR-65 | `business/productivity_business.py::ProductivityBusiness.direct_labor`, `business/report_business.py::ReportBusiness._members_direct_labor` |
| BR-66 | `business/productivity_business.py::ProductivityBusiness.average_smv` |
| BR-58 (7 card) | `builders/overview_builders.py::CARD_ROWS`, `OverviewResponse.cards`, `components/overview_charts.py::CARDS` |
| BR-67 | `frontend/features/sewing_productivity/components/overview_charts.py::daily_charts` |
| AC-75 đến AC-78, AC-80 | `tests/test_cards_extension.py` |
| UC-29 | `get_monthly_report` (với `MonthlyReportRequest.period_kind`) -> `GetMonthlyReportService._period_report`, `builders/period_builders.py::PeriodReportResponseBuilder` |
| BR-68 | `business/period_business.py::PeriodBusiness.periods` |
| BR-69 | `business/report_business.py::ReportBusiness.period_summaries`, `_members_direct_workers`; `builders/period_builders.py::PERIOD_ROWS` |
| BR-31 (sửa Screen 4) | `business/filter_business.py::FilterBusiness.default_year_start`, `FilterOptionsResponse.default_year_from` |
| Screen 4 (Period Report) | `frontend/features/sewing_productivity/pages/monthly_report_page.py::MonthlyReportPage` |
| AC-81 đến AC-84, AC-86 | `tests/test_period_report.py` |
| BR-70 | `business/period_business.py::PeriodBusiness.rising_is_good` (`RISING_IS_GOOD`), `components/period_blocks.py::period_cards` |
| BR-71 | `business/period_business.py::PeriodBusiness.comparison_range`, `changes`; `services/get_monthly_report_service.py::GetMonthlyReportService._compared` |
| UC-29 (sửa 2026-11-08) | `builders/period_builders.py::PeriodReportResponseBuilder._cards`, `dto/monthly_dto.py::PeriodCardDTO`, `PeriodMetricDTO.cards`, `compare_label`, `rising_is_good` |
| Screen 4 (sửa 2026-11-08) | `pages/monthly_report_page.py` (tab), `components/period_blocks.py` (`period_cards`, `small_charts`, `number_table`) |
| AC-87 đến AC-91 | `tests/test_period_cards.py` |
| 4.10 (thêm 2026-11-09) | `models/settings_records.py::UploadLog`, `UploadSheetCount`, `UploadChangeCount`, `UploadSkippedNote`, `UploadWarningNote`; `models/enums.py::UploadStatus` |
| BR-72 | `business/upload_tracking_business.py::UploadTrackingBusiness.sheet_counts`, `saved_log`; `constants.py::SKIPPED_ROWS_KEPT`; `services/save_upload_service.py::SaveUploadService._warnings` |
| BR-73 | `business/upload_tracking_business.py::UploadTrackingBusiness.change_counts`; `services/save_upload_service.py::SaveUploadService._replace` |
| BR-74 | `business/upload_tracking_business.py::UploadTrackingBusiness.rejected_log`, `counts_as_last_upload`; `services/check_upload_service.py`, `save_upload_service.py` (`execute`); `repositories/report_source_loader.py::load_report_source` |
| UC-03 (sửa 2026-11-09), Screen 7 lịch sử | `builders/upload_response_builders.py::UploadLogListBuilder._item`, `dto/upload_dto.py::UploadLogDTO`; `frontend/.../components/upload_history.py` |
| AC-94 đến AC-98 | `tests/test_upload_tracking.py` |
| Screen 4 tên "Sewing metrics" (sửa 2026-11-09) | `pages/monthly_report_page.py::MonthlyReportPage.title` |
| BR-75 | `frontend/.../components/number_format.py::format_number` (dùng ở `report_cells.py`, `period_blocks.py`, `overview_charts.py`, `upload_blocks.py`) |
| BR-76 | `components/report_cells.py::BELOW_MARK`, `below_note`; `components/period_blocks.py::period_cards` (tên thẻ màu đỏ); các trang Overview, Daily Report, Line Detail, MO by Line, Sewing metrics |
| 4.11, UC-33, BR-81, BR-82 (thêm 2026-11-12) | `models/source_records.py::LineStrength`, `repositories/source_repositories.py::LineStrengthRepository`, `builders/strength_read_builders.py::LineStrengthReadBuilder`, `business/line_strength_business.py::LineStrengthBusiness` (`is_strength_file`, `read`, `parse`, `replacement_writes`), `services/check_upload_service.py`, `services/save_upload_service.py::_save_strength`, `business/upload_tracking_business.py::strength_log`; `tests/test_line_strength.py` |
| UC-34 | `get_catalogs` -> `GetCatalogsService` (`CatalogsResponse.line_strengths`), `builders/line_overview_builders.py::strength_dtos`, `pages/catalogs_page.py::_line_strengths` |
| UC-06 sửa, BR-83, BR-84 | `business/line_overview_business.py::LineOverviewBusiness` (`first_days`, `rows`, `matching_ratio`, `changeover`, `orders`), `LineStrengthBusiness.matches`, `services/get_line_detail_service.py`, `builders/line_overview_builders.py`, `components/line_overview_blocks.py`, `pages/line_detail_page.py`; `tests/test_line_overview.py` |
| UC-32, BR-85 (làm lại 2026-11-12) | `export_changeover` (với `line_performance`) -> `ExportChangeoverService._line_performance`, `builders/line_performance_file_builders.py::LinePerformanceFileBuilder`, nút ở `pages/changeover_page.py` |
| Bỏ Screen 3, Screen 5 (2026-11-12) | `frontend/features/sewing_productivity/manifest.py` (không còn trang Daily Report, MO by Line) |
| UC-31 (thêm 2026-11-11) | `get_changeover` (với `ChangeoverRequest.line_performance`) -> `GetChangeoverService._line_performance`, `builders/line_performance_builders.py::LinePerformanceResponseBuilder` |
| BR-78, BR-79, BR-80 | `business/line_performance_business.py::LinePerformanceBusiness.rows`, `target_value`, `value_ratio`, `_total`; `business/line_report_business.py::LineReportBusiness.line_periods`; `models/report_values.py::LinePerformance` |
| Screen 6 Line performance (sửa 2026-11-11) | `frontend/features/sewing_productivity/pages/changeover_page.py::ChangeoverPage` (tên lớp và đường dẫn giữ) |
| AC-106 đến AC-108 | `tests/test_line_performance.py` |
| AC-104 thanh "Jump to" | `pages/monthly_report_page.py::MonthlyReportPage._jump_bar`, `_anchor`, `JUMP_ANCHOR` |
| Screen 4 không tab, khối "Charts" (sửa 2026-11-10), AC-103 | `pages/monthly_report_page.py::MonthlyReportPage.render`, `_metric_block` |
| BR-77 | `builders/period_builders.py::PERIOD_ROWS` ("%Direct labor"), `pages/monthly_report_page.py::EXTRA_CARDS`; `tests/test_period_cards.py::test_ac102_...` |
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
| Screen 6 | `frontend/features/sewing_productivity/pages/changeover_page.py` (gỡ khỏi app 2026-11-13: gộp vào Screen 2, chỉ còn file tải) |
| Screen 7 | `frontend/features/sewing_productivity/pages/data_update_page.py` |
| Screen 8 | `frontend/features/sewing_productivity/pages/goals_page.py` |
| Screen 9 | `frontend/features/sewing_productivity/pages/catalogs_page.py` |
| Logs | Mỗi dịch vụ ghi các bước chính vào `logs/app.log` |
| Tests | `backend/features/sewing_productivity/tests/` |
| BR-86 (mở rộng 2026-11-13) | `business/line_strength_business.py::LineStrengthBusiness` (`strong_map`, `row_matches`, `matching_ratio`); sở trường nạp vào `ReportSource.strengths` (`repositories/report_source_loader.py`) và `ReportFacts.strengths` (`ReportBusiness.facts`); dùng ở `LineOverviewBusiness.rows` (Line Detail), `ReportBusiness._summary` (Overview, file báo cáo tuần, file mẫu họp, Sewing metrics); `tests/test_extension_20261113.py` (AC-117, AC-118) |
| BR-87 (mở rộng 2026-11-13) | `business/changeover_business.py::ChangeoverBusiness` (`code_of`, `code_days`, `style_changeovers`), `ReportBusiness.code_days`, `LineOverviewBusiness.changeover`; `tests/test_extension_20261113.py` (AC-119) |
| BR-83 sửa, BR-88 (mở rộng 2026-11-13) | `LineOverview.efficiency`, `LineOrder.smv` / `efficiency`, `builders/line_overview_builders.py`, `dto/line_detail_dto.py`; giao diện `components/line_overview_blocks.py` (thanh màu, cột Alert); `tests/test_extension_20261113.py` (AC-120, AC-121) |
| BR-89 (mở rộng 2026-11-13) | `ReportBusiness._style_changeovers`, `FactorySummary.changeovers` / `changeover_per_line_day`, `builders/period_builders.py::PERIOD_ROWS`, `dto/monthly_dto.py::CHANGEOVER_PER_LINE_DAY`, `PeriodBusiness.rising_is_good`, `pages/monthly_report_page.py` (`METRIC_LABELS`, `METRIC_COLORS`); `tests/test_extension_20261113.py` (AC-123) |
| BR-90 (mở rộng 2026-11-13 lần 2) | `LineDetailRequest.trend_line` / `trend_kind` (đi qua `get_line_detail` của UC-06), `GetLineDetailService._trend`, `LineOverviewBusiness.trend_point`, `LineTrendPoint`, `builders/line_overview_builders.py::LineTrendResponseBuilder`, `LineTrendPointDTO`; giao diện `components/line_trend_blocks.py::line_trend`, `pages/line_detail_page.py::_trend`; `tests/test_line_trend.py` (AC-125 đến AC-127) |
| BR-92 đến BR-96 (mở rộng 2026-11-13 lần 4) | `business/product_mix_business.py::ProductMixBusiness` (`top_groups`, `shares`, `top_customers`, `cm_prices`, `monthly`), `ProductMix` và các giá trị trong `models/report_values.py`, `ChartsRequest.products`, `GetChartsService._products`, `ChartsResponseBuilder` (`product_shares`, `product_table`, `top_customers`, `cm_by_group`, `monthly_mix`); giao diện `components/product_mix_blocks.py::products_section`, `pages/overview_page.py` (bỏ Ranking), `components/overview_charts.py::daily_charts` (bỏ Output vs Target); `tests/test_overview_products.py` (AC-133 đến AC-136) |
| BR-97, 4.3 `derived` (mở rộng 2026-11-13 lần 4) | `UploadBusiness.ensure_sheets` (trả về file năm cũ), `parse(production_only=)`, `_ensure_past_year`, `derived_workers`; `WorkerRecord.derived`; `ParsedUpload.derived_workers`; `RawWorkbookBuilder._read` (sheet thiếu = rỗng); `constants.py::PRODUCTION_ONLY_BEFORE`, `SHEET_WORKER_DERIVED`; `tests/test_overview_products.py` (AC-137, AC-138) |
| BR-98 (mở rộng 2026-11-13 lần 4) | `Factory.FAC_1_HCM`, `REPORT_FACTORIES`, `constants.py::ALL_FACTORIES` / `FACTORY_BY_SOURCE_NAME`, `GetFilterOptionsService`, `ExportChangeoverService._line_performance`, `meeting_report_builders._overall`, `components/report_filters.py::FACTORIES`; `tests/test_overview_products.py` (AC-139) |
| BR-91 (mở rộng 2026-11-13 lần 3) | 26 tuần: `GetLineDetailService._trend_periods`, `constants.py::TREND_WEEKS`; màu cột: `components/line_trend_blocks.py` (`_status`, `_output_chart`, `ON_TARGET` / `BELOW_THRESHOLD` / `NO_NUMBER`); tóm tắt bộ lọc và "Back to filters": `pages/line_detail_page.py` (`_filter_note`, `FILTERS_ANCHOR`), `line_overview_blocks.line_details(filter_note=)`; `tests/test_line_trend.py` (AC-130) |
| Gộp Line performance vào Line Detail, UC-32 (mở rộng 2026-11-13) | `pages/line_detail_page.py::_line_performance_file`, `manifest.py` (bỏ trang Line performance); AC-122 |
