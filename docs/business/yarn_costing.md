# Tính giá sợi

| Feature key | `yarn_costing` (= folder name in `backend/features/` and `frontend/features/`) |
|---|---|
| Home group (Nhóm trên Trang chủ) | Tính Giá Sợi |
| Icon (Biểu tượng) | 🧵 |
| Owner (Người phụ trách) | Phòng SO |
| Status (Trạng thái) | Implemented |
| Last updated | 2026-10-13 |

## 1. Goal (Mục tiêu)
Hiện nay giá sợi của Xưởng Sợi 1 (S1) và Sợi 4 (S4) được tính trên hai file Excel có macro: Sales gửi yêu cầu qua
Zalo, xưởng nhập năng suất máy vào file, chép mã qua sheet tính rồi chép tay kết quả sang bảng giá; file có nhiều chỗ
lỗi `#REF!`, nhóm thiếu tiêu hao, giá bằng 0 và cách viết mã không thống nhất. Chức năng này thay thế hoàn toàn hai
file đó: Sales tạo yêu cầu và mã tính giá tự sinh, xưởng nhập năng suất máy và tỷ lệ pha, app kiểm tra đầu vào khớp
nhau rồi tính chi phí sản xuất cho 1 kg sợi (5 khoản, VND và USD), tự tạo giá thí nghiệm, lưu bảng giá có lịch sử;
kế toán hoặc xưởng nhập mã kế toán để khoá sợi. Phòng SO quản lý dữ liệu nền của từng xưởng, tính lại toàn bộ khi
định mức thay đổi và theo dõi sai lệch trên dashboard. Giá chỉ là chi phí gia công, không gồm tiền nguyên liệu.
Chức năng được chuyển từ app cũ sang app mới (chỉ có chức năng này); toàn bộ dữ liệu đã nhập ở app cũ được chép sang một lần
(mục 5.6) và từ đó chỉ dùng app mới.

## 2. Actors (Người dùng)
Mỗi người dùng app bằng **tài khoản đăng nhập riêng** của ứng dụng. Mỗi actor dưới đây là một **vai trò** của chức năng
(mã SALES, XS1, XS4, KT, SO): quản trị viên tích vai trò cho từng tài khoản hoặc nhóm tài khoản ở trang `/admin` (một cột cho mỗi
vai trò). Một tài khoản có thể có nhiều vai trò. Quản trị viên làm được như Phòng SO mà không cần tích vai trò.

| Actor (vai trò) | Description |
|---|---|
| Sales (SALES) | Tạo yêu cầu tính giá cho sợi mới (chọn xưởng, nhập tên sợi, chọn loại đóng gói); sửa / huỷ yêu cầu khi xưởng chưa xử lý; xem trạng thái và giá |
| Xưởng S1 (XS1), Xưởng S4 (XS4) | Mỗi xưởng chỉ thao tác dữ liệu của xưởng mình: từ chối yêu cầu; nhập NSM + tỷ lệ pha và tính giá; tạo bản ĐCNSM, dòng CK/PP; khai báo và sửa tiêu hao (khi chưa bị khoá); nhập / sửa / xoá mã kế toán; tải file cập nhật NSM và tiêu hao |
| Phòng SO (SO) | Làm được mọi thao tác của hai xưởng cho cả S1 và S4; ngoài ra: dữ liệu nền (cấu hình công đoạn, định mức chi phí/phút, loại đóng gói, hồi phế, quy trình công nghệ, tỷ giá, hệ số thí nghiệm); sửa tiêu hao đã bị khoá; chuyển dữ liệu cũ từ file Excel |
| Kế toán (KT) | Nhập / sửa / xoá mã kế toán cho các dòng bảng giá |
| Người xem | Bất kỳ tài khoản nào được cấp quyền mở chức năng (không cần vai trò): xem mọi màn hình, tra cứu, xuất Excel, xem dashboard, xem nhật ký thao tác |

## 3. Glossary (Thuật ngữ)
| Term | Meaning |
|---|---|
| Xưởng | Xưởng Sợi 1 (mã S1) hoặc Xưởng Sợi 4 (mã S4); mỗi xưởng có dữ liệu nền, dãy mã và tiêu hao riêng |
| Mã tính giá | Mã do app cấp cho mỗi sợi, dãy riêng từng xưởng, dạng `S4-2020`; khác mã kế toán |
| Mã kế toán | Mã do kế toán (hoặc xưởng) nhập vào một dòng bảng giá khi có đơn hàng chính thức |
| Tên sợi | Tên đầy đủ, luôn có chi số dạng `<số>/1`, ví dụ `CVC 30/1 (60/40) MVS` |
| Chi số | Số đứng ngay trước `/1` trong tên sợi, ví dụ 30 |
| Nhóm sợi | Phần tên sợi đứng trước chi số, ví dụ `CVC` |
| Nhóm tiêu hao | Tên sợi bỏ phần `<chi số>/1`, viết hoa, ví dụ `CVC (60/40) MVS`; dùng để tìm bảng tiêu hao; đã phân biệt tỷ lệ pha và nguyên liệu đặc biệt |
| Công nghệ | Ring hoặc MVS |
| Sợi compact | Sợi có chữ "compact" trong tên; ở S4 công đoạn con dùng "S Compact" thay cho "S" |
| Công đoạn | Một bước sản xuất có mã (C1, SBD, MD1, R, S, W, V...) và định mức chi phí/phút riêng |
| Đóng gói | Công đoạn cuối, mã `F`; chi phí theo loại đóng gói (Type 1, Type 2...) |
| NSM | Năng suất máy của một sợi ở một công đoạn, đơn vị kg/giờ; 0 hoặc để trống = sợi không chạy công đoạn đó |
| Tỷ lệ pha | Tỷ lệ của từng thành phần nguyên liệu trong sợi (4.12.1), tổng 100% |
| Thành phần nguyên liệu | Một nguyên liệu của sợi: tên nguyên liệu, tỷ lệ, dây chuyền chải thô nó chạy qua, lượt, NSM chải thô (4.12.1) |
| Dây chuyền chải thô | Công đoạn ăn bông - chải thô mà một nguyên liệu chạy qua: S4 có C1 (cotton), C2, C3; S1 có C1, C2 |
| Chải thô nhiều lượt | Dây chuyền chải thô dùng chung cho nhiều nguyên liệu của cùng một sợi, mỗi nguyên liệu chạy một lượt, tối đa 3 lượt: S4 C2, C3; S1 C1, C2. C2 và C3 (S4), C1 và C2 (S1) cùng công nghệ, xưởng chọn dây chuyền theo từng sợi |
| Lượt | Thứ tự (1, 2, 3) của một nguyên liệu trên cùng dây chuyền chải thô; app tự đánh, không làm đổi giá. Thay cho C3.1 / C3.2 / C3.3 của file Excel |
| Tỷ lệ dây chuyền | Tổng tỷ lệ các thành phần chạy trên một dây chuyền chải thô (ví dụ tỷ lệ dây chuyền C1 của S4 = tỷ lệ cotton) |
| Loại đóng gói mặc định | Loại đóng gói Phòng SO chọn cho mỗi xưởng, được điền sẵn khi Sales tạo yêu cầu |
| Định mức chi phí/phút | Chi phí 1 phút chạy máy của một công đoạn (VND/phút), chia 5 khoản: Nhân công, Khấu hao, Điện, Vật tư, CPQL (chi phí quản lý) |
| Tiêu hao | Tỷ lệ nguyên liệu hao hụt tại một công đoạn, ví dụ 1,5% |
| Tiêu hao lũy kế | Tổng tiêu hao của công đoạn đó và các công đoạn phía sau được khai báo cho nó (BR-19) |
| Hồi phế | Tỷ lệ nguyên liệu hồi lại phải chạy lại, làm tăng thời gian chạy máy; 3 loại: Chải thô, Thô, Con |
| Tiêu hao sơ cấp | Tiêu hao của sợi một nguyên liệu + một công nghệ, xưởng nhập tay, ví dụ "PE Normal - Ring" |
| Tiêu hao thứ cấp | Tiêu hao của sợi pha, app tính từ 1-5 nhóm thành phần và tỷ lệ (BR-26) |
| Công đoạn ghép | Công đoạn được miễn kiểm tra khớp NSM - tiêu hao (BR-15) |
| Bản NSM | Một bộ NSM + thành phần nguyên liệu + đóng gói của một mã; mã gốc là bản 0, mỗi ĐCNSM là một bản mới |
| ĐCNSM | Điều chỉnh năng suất máy của riêng một sợi (do công nghệ, chất lượng nguyên liệu, sản lượng lớn); tạo bản NSM mới có mã `S4-586 (ĐCNSM1)` |
| Dòng giá thường | Giá đại trà của một bản NSM, mã = mã của bản NSM |
| Dòng giá thí nghiệm (TN) | Giá thường × hệ số thí nghiệm, mã = mã dòng thường + `TN` |
| Dòng CK / PP | Dòng chiết khấu (giảm) / phụ phí (tăng) theo % cho một đơn hàng cụ thể, mã `S4-2020 (CK1)` / `S4-2020 (PP1)` |
| Khoá | Bản NSM có ít nhất một dòng giá có mã kế toán thì không sửa được thông tin riêng của sợi |
| Tính lại toàn bộ | Tính lại giá mọi bản NSM của một xưởng khi dữ liệu nền thay đổi, kể cả bản đã khoá |
| File khai báo thành phần | File Excel khai báo thành phần + tỷ lệ cho nhiều nhóm tiêu hao sợi pha của một xưởng cùng lúc (5.7, UC-45) |
| Dây chuyền tương đương | Hai dây chuyền chải thô cùng công nghệ, chạy thay nhau được, dùng được tiêu hao chải thô của nhau (BR-64): S4 C2 ↔ C3; S1 C1 ↔ C2. S4 C1 (cotton) không có dây chuyền tương đương |
| Ngày hiệu lực | Ngày áp dụng của giá sau một lần tính lại toàn bộ, do Phòng SO chọn |
| Vai trò | Quyền của một actor trong chức năng (SALES, XS1, XS4, KT, SO); quản trị viên tích cho từng tài khoản ở trang `/admin`; ai thao tác là tài khoản đang đăng nhập |

## 4. Data (Dữ liệu)

### 4.1 Vai trò của chức năng (Role)
Không lưu trong cơ sở dữ liệu: 5 vai trò cố định, khai báo cùng chức năng (mã và tên hiển thị lấy từ cùng một danh sách trong code);
quản trị viên tích vai trò cho tài khoản / nhóm tài khoản ở trang `/admin` (khoá quyền `yarn_costing/@<mã>`).

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| code | list of values: SALES / XS1 / XS4 / KT / SO (cố định) | Yes | Mã vai trò | XS4 |
| label | text | Yes | Tên hiện ở trang `/admin`: Sales, Xưởng S1, Xưởng S4, Kế toán, Phòng SO | Xưởng S4 |
| factory_code | list of values: S1 / S4 / để trống | No | Xưởng mà vai trò được thao tác: XS1 = S1, XS4 = S4; các vai trò khác để trống (cả hai xưởng) | S4 |

### 4.2 Thành viên nhóm (đã bỏ)
Đã bỏ (2026-10-13): người thao tác là tài khoản đăng nhập của app, không còn danh sách thành viên riêng của chức năng.

### 4.3 Xưởng (Factory) - dữ liệu cố định
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| code | list of values: S1 / S4 | Yes | Mã xưởng | S4 |
| name | text | Yes | Tên xưởng | Xưởng Sợi 4 |
| carding_stages | list of stage_code | Yes | Các dây chuyền chải thô theo thứ tự: S4 = C1, C2, C3; S1 = C1, C2 | C1, C2, C3 |
| equivalent_carding | danh sách cặp (dây chuyền → dây chuyền tương đương), cố định | Yes | Dây chuyền tương đương (BR-64): S4 = C2 ↔ C3; S1 = C1 ↔ C2 | C2 → C3, C3 → C2 |
| code_prefix | text | Yes | Tiền tố mã tính giá = mã xưởng + "-" | S4- |

### 4.4 Công đoạn và cấu hình tính (Stage)
Một dòng cho mỗi công đoạn của mỗi xưởng. Phòng SO sửa được (UC-03). Dữ liệu khởi tạo lấy đúng theo quy trình kỹ thuật
của hai file Excel (bảng 4.4.1 và 4.4.2).

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| factory_code | S1 / S4 | Yes | Xưởng | S4 |
| stage_code | text ≤ 20, duy nhất trong xưởng | Yes | Mã công đoạn, trùng với tiêu đề cột NSM / tiêu hao / định mức trong file | SBD |
| stage_name | text ≤ 100 | Yes | Tên công đoạn | Ghép sơ bộ CM |
| stage_group | text ≤ 20 | Yes | Nhóm công đoạn (như cột "Nhóm công đoạn" của file) | SBD |
| sequence | integer ≥ 1, duy nhất trong xưởng | Yes | Thứ tự công đoạn trong bảng tính | 6 |
| is_packaging | yes-no | Yes | Là công đoạn đóng gói `F` (chỉ 1 công đoạn mỗi xưởng) | Không |
| recovery_type | list of values: Không / Chải thô / Thô / Con | Yes | Loại hồi phế nhân vào thời gian chạy máy | Chải thô |
| blend_slot | list of values: Không / Tỷ lệ của lượt / Tỷ lệ dây chuyền <mã dây chuyền chải thô của xưởng> | Yes | Tỷ lệ nhân vào thời gian chạy máy (BR-17): dây chuyền chải thô dùng "Tỷ lệ của lượt"; công đoạn sau chải thô dùng tỷ lệ của một dây chuyền | Tỷ lệ dây chuyền C1 |
| is_carding | yes-no | Yes | Là dây chuyền chải thô (NSM, tỷ lệ và tiêu hao theo từng thành phần nguyên liệu) | Có |
| max_passes | integer 1-3 | Yes với dây chuyền chải thô | Số lượt tối đa: 1 = một nguyên liệu (S4 C1), 3 = chải thô nhiều lượt | 3 |
| is_merge_stage | yes-no | Yes | Công đoạn ghép, miễn kiểm tra khớp (BR-15) | Có |
| secondary_method | list of values: Bình quân / Cộng thẳng | Yes | Cách tính tiêu hao thứ cấp ở công đoạn này (BR-26) | Bình quân |
| cumulative_stages | list of stage_code (các công đoạn phía sau) | Yes | Các công đoạn được cộng vào tiêu hao lũy kế, ngoài chính công đoạn này (BR-19) | CM, DCM, MD1, MD2, MD3, R, S, S Compact, W, V |
| varies_with_count | yes-no | Yes | Công đoạn mà NSM thay đổi theo chi số (Thô, Con, Ống, MVS): không cảnh báo khi khác sợi cùng nhóm | Không |
| rate_code_source | list of values: Chính công đoạn / Loại đóng gói | Yes | Định mức lấy theo mã công đoạn, hoặc (đóng gói) theo loại đóng gói của sợi | Chính công đoạn |

"MD1..V" dưới đây nghĩa là: MD1, MD2, MD3, R, S, S Compact, W, V (S4) hoặc MD1, MD2, MD3, R, S, W, V (S1).

#### 4.4.1 Cấu hình khởi tạo - S4 (hồi phế: Chải thô 1,5%, Thô 1%, Con 2,5%)
| sequence | stage_code | stage_name | recovery_type | blend_slot | is_merge_stage | secondary_method | cumulative_stages | varies_with_count |
|---|---|---|---|---|---|---|---|---|
| 1 | C1 | Ăn bông - Chải thô cotton | Chải thô | Tỷ lệ của lượt | Không | Cộng thẳng | SBD, PCD1, PCD2, CM, DCM, MD1..V | Không |
| 2 | C2 | Ăn bông - Chải thô PE | Chải thô | Tỷ lệ của lượt | Không | Cộng thẳng | PD, PD1, MD1..V | Không |
| 3 | C3 | Ăn bông - Chải thô khác | Chải thô | Tỷ lệ của lượt | Không | Cộng thẳng | MD1..V | Không |
| 4 | SBD | Ghép sơ bộ CM | Chải thô | Tỷ lệ dây chuyền C1 | Có | Bình quân | CM, DCM, MD1..V | Không |
| 5 | PD | Ghép sơ bộ PE | Chải thô | Tỷ lệ dây chuyền C2 | Có | Cộng thẳng | PD1, MD1..V | Không |
| 6 | PD1 | Ghép sơ bộ Viscose | Không | Không | Có | Cộng thẳng | MD1..V | Không |
| 7 | PCD1 | Ghép sơ bộ CD 1 | Chải thô | Tỷ lệ dây chuyền C1 | Có | Bình quân | PCD2, MD1..V | Không |
| 8 | PCD2 | Ghép sơ bộ CD 2 | Chải thô | Tỷ lệ dây chuyền C1 | Có | Cộng thẳng | MD1..V | Không |
| 9 | CM | Chải kỹ | Chải thô | Tỷ lệ dây chuyền C1 | Không | Cộng thẳng | DCM, MD1..V | Không |
| 10 | DCM | Ghép CM sau chải kỹ | Chải thô | Tỷ lệ dây chuyền C1 | Có | Cộng thẳng | MD1..V | Không |
| 11 | MD1 | Ghép trộn A | Không | Không | Có | Bình quân | MD2, MD3, R, S, S Compact, W, V | Không |
| 12 | MD2 | Ghép trộn B | Không | Không | Có | Cộng thẳng | MD3, R, S, S Compact, W, V | Không |
| 13 | MD3 | Ghép trộn C | Không | Không | Có | Cộng thẳng | R, S, S Compact, W, V | Không |
| 14 | R | Thô | Thô | Không | Không | Bình quân | S, S Compact, W, V | Có |
| 15 | S | Con | Con | Không | Không | Bình quân | W, V | Có |
| 16 | S Compact | Con - compact | Con | Không | Không | Bình quân | W, V | Có |
| 17 | W | Ống | Không | Không | Không | Bình quân | V | Có |
| 18 | V | MVS | Không | Không | Không | Bình quân | (không có) | Có |
| 19 | F | Hoàn tất, đóng gói | Không | Không | Có | Cộng thẳng | (không có) | Không |

Dây chuyền chải thô S4: C1 (`is_carding` = Có, `max_passes` = 1, chỉ cotton), C2 và C3 (`is_carding` = Có, `max_passes` = 3,
cùng công nghệ, chạy thay nhau được). Công đoạn C3 thay cho C3.1 / C3.2 / C3.3 của file Excel (cùng định mức - dòng "C3" của
sheet định mức, cùng hồi phế; số 1-2-3 là lượt).

#### 4.4.2 Cấu hình khởi tạo - S1 (hồi phế: Chải thô 2%, Thô 1%, Con 1%)
| sequence | stage_code | stage_name | recovery_type | blend_slot | is_merge_stage | secondary_method | cumulative_stages | varies_with_count |
|---|---|---|---|---|---|---|---|---|
| 1 | C1 | Chải thô PE | Chải thô | Tỷ lệ của lượt | Không | Bình quân | PD, PD2, MD1..V | Không |
| 2 | C2 | Chải thô đặc biệt | Chải thô | Tỷ lệ của lượt | Không | Bình quân | PD, PD2, MD1..V | Không |
| 3 | PD | Ghép 1 | Chải thô | Không | Có | Bình quân | PD2, MD1, MD2, MD3, R, S, W (không gồm V) | Không |
| 4 | PD2 | Ghép 2 | Không | Không | Có | Bình quân | MD1..V | Không |
| 5 | MD1 | Ghép trộn 1 | Không | Không | Có | Bình quân | MD2, MD3, R, S, W, V | Không |
| 6 | MD2 | Ghép trộn 2 | Không | Không | Có | Bình quân | MD3, R, S, W, V | Không |
| 7 | MD3 | Ghép trộn 3 | Không | Không | Có | Bình quân | R, S, W, V | Không |
| 8 | R | Thô | Thô | Không | Không | Bình quân | S, W | Có |
| 9 | S | Con | Con | Không | Không | Bình quân | W | Có |
| 10 | W | Ống | Không | Không | Không | Bình quân | (không có) | Có |
| 11 | V | MVS | Không | Không | Không | Bình quân | (không có) | Có |
| 12 | F | Hoàn tất, đóng gói | Không | Không | Có | Bình quân | (không có) | Không |

Dây chuyền chải thô S1: C1 và C2 (`is_carding` = Có, `max_passes` = 3, cùng công nghệ, chạy thay nhau được). Cotton ở S1 nhận
cúi từ S4 nên không qua chải thô ("Không chải thô"). Các công đoạn không phải chải thô: `is_carding` = Không.

Công đoạn F của cả hai xưởng: `is_packaging` = Có, `rate_code_source` = Loại đóng gói. Các công đoạn khác:
`is_packaging` = Không, `rate_code_source` = Chính công đoạn.

### 4.5 Bảng định mức chi phí/phút (Rate version)
Mỗi lần Phòng SO áp dụng định mức mới cho một xưởng tạo một phiên bản; phiên bản mới nhất là phiên bản đang dùng.

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| id | text (tự sinh) | Yes | Mã phiên bản | DM-S4-003 |
| factory_code | S1 / S4 | Yes | Xưởng | S4 |
| effective_date | date | Yes | Ngày hiệu lực | 2026-01-01 |
| reason | text ≤ 500 | Yes | Lý do thay đổi | Cập nhật định mức năm 2026 |
| created_by, created_at | text, datetime | Yes | Người và lúc áp dụng | Trần Thị B (SO), 2026-01-02 09:15 |
| lines | danh sách dòng 4.5.1 | Yes | Định mức từng mã | |

#### 4.5.1 Dòng định mức (Rate line)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| rate_code | text ≤ 20 | Yes | Mã công đoạn (4.4) hoặc mã loại đóng gói (4.6) | C1 |
| labor | decimal ≥ 0 | Yes | Nhân công (VND/phút) | 113.5521 |
| depreciation | decimal ≥ 0 | Yes | Khấu hao (VND/phút) | 421.8444 |
| electricity | decimal ≥ 0 | Yes | Điện (VND/phút) | 1533.6356 |
| materials | decimal ≥ 0 | Yes | Vật tư (VND/phút) | 297.5751 |
| overhead | decimal ≥ 0 | Yes | CPQL (VND/phút) | 172.0208 |
| total_rate | decimal (tính) | - | = labor + depreciation + electricity + materials + overhead | 2538.6280 |
| note | text ≤ 200 | No | Ghi chú | Con. 40 |

### 4.6 Loại đóng gói (Packaging type)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| factory_code | S1 / S4 | Yes | Xưởng | S4 |
| code | text ≤ 20, duy nhất trong xưởng | Yes | Mã loại đóng gói | Type 3 |
| name | text ≤ 200 | Yes | Tên loại đóng gói | Xe tải 5T (165 bao × 30,24 kg) |
| weight_kg | decimal > 0 | No | Khối lượng một lần đóng (kg), chỉ để tham khảo | 4989.6 |
| man_days | decimal ≥ 0 | No | Số công, chỉ để tham khảo | 2.2812 |
| minutes_per_kg | decimal > 0 | Yes | Thời gian đóng gói (phút/kg), dùng để tính giá | 0.2195 |
| active | yes-no (default Yes) | Yes | Còn cho chọn khi tạo yêu cầu không | Có |
| is_default | yes-no (default Không) | Yes | Loại đóng gói mặc định của xưởng, được điền sẵn khi Sales tạo yêu cầu (BR-60); mỗi xưởng tối đa 1 loại | Có |

### 4.7 Hồi phế (Recovery rate)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| factory_code | S1 / S4 | Yes | Xưởng | S4 |
| recovery_type | list of values: Chải thô / Thô / Con | Yes | Loại hồi phế (file: "Cúi ghép sau máy thô" = Chải thô, "Sợi thô" = Thô, "Bông A2" = Con) | Chải thô |
| rate | decimal 0 ≤ x < 1 | Yes | Tỷ lệ hồi phế | 0.015 |

### 4.8 Quy trình công nghệ (Process route)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| factory_code | S1 / S4 | Yes | Xưởng | S4 |
| yarn_group | text ≤ 100 | Yes | Nhóm sợi, viết hoa | TC |
| technology | list of values: Ring / MVS | Yes | Công nghệ | Ring |
| component_count | integer 1-5 | No | Số thành phần | 2 |
| route_text | text ≤ 500 | No | Quy trình, các bước ngăn cách bởi "-" | B2 - C1 - C2 - SBD - PD - LF - CM - MD1 - MD2 - MD3 - R - S - W - F |
| route_stages | list of stage_code (tính) | - | Các công đoạn của xưởng có trong quy trình (BR-13) | C1, C2, SBD, PD, CM, MD1, MD2, MD3, R, S, W, F |
Khoá duy nhất: (factory_code, yarn_group, technology).

### 4.9 Tỷ giá (Exchange rate)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| effective_date | date | Yes | Ngày áp dụng | 2026-01-01 |
| rate | decimal > 0 | Yes | Số VND cho 1 USD, dùng chung cho S1 và S4 | 25000 |
| note | text ≤ 200 | No | Ghi chú | |
| created_by, created_at | text, datetime | Yes | Người và lúc nhập | |
Tỷ giá đang dùng = dòng có `effective_date` lớn nhất ≤ hôm nay (nếu nhiều dòng cùng ngày: dòng nhập sau cùng).

### 4.10 Tham số chung (Settings)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| trial_factor | decimal > 0 (default 3) | Yes | Hệ số giá thí nghiệm, dùng chung cho S1 và S4 | 3 |

### 4.11 Nhóm tiêu hao (Loss group)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| factory_code | S1 / S4 | Yes | Xưởng | S4 |
| group_key | text ≤ 200, viết hoa, bỏ khoảng trắng hai đầu, duy nhất trong xưởng | Yes | Nhóm tiêu hao, so khớp với nhóm tiêu hao của sợi (BR-04) | TR (65/35) |
| yarn_group_label | text ≤ 200 | Yes | Tên nhóm như người dùng nhập (cột "Nhóm sợi" của file) | TR (65/35) |
| material | text ≤ 200 | No | Nguyên liệu | PE Normal |
| technology | list of values: Ring / MVS | Yes | Công nghệ (khi nhập từ file: "ring"/"mvs " được chuẩn hoá thành Ring/MVS) | Ring |
| material_tech_key | text (tính) | - | = material + " - " + technology (dùng để chọn thành phần như file S4) | PE Normal - Ring |
| level | list of values: Sơ cấp / Thứ cấp / Nhập từ file - chưa khai báo thành phần | Yes | Loại nhóm (BR-25, BR-26, BR-27) | Thứ cấp |
| losses | danh sách (stage_code → decimal 0 ≤ x < 1) | Yes | Tiêu hao từng công đoạn. Ở dây chuyền chải thô là tiêu hao chải thô của nguyên liệu khi chạy dây chuyền đó: chạy C2 thì khai báo ở C2, chạy C3 thì khai báo ở C3 (có thể khai báo cả hai). Thứ cấp: app tính (BR-26), không nhập tay | C3: 0.034 |
| components | danh sách 1-5 dòng (component_group_key, ratio decimal 0 < x ≤ 1) | Chỉ với Thứ cấp | Nhóm thành phần và tỷ lệ | PE NORMAL - RING 0,65; VISCOSE - RING 0,35 |
| is_locked | yes-no (tính) | - | Có ít nhất một bản NSM dùng nhóm này (trực tiếp hoặc qua nhóm thứ cấp dùng nó làm thành phần) đang bị khoá (BR-24) | Có |
| updated_by, updated_at | text, datetime | Yes | Người và lúc sửa gần nhất | |

### 4.12 Mã sợi / bản NSM (Yarn)
Mỗi yêu cầu của Sales tạo một mã sợi (bản NSM gốc). Mỗi ĐCNSM tạo thêm một mã sợi mới (bản NSM mới) trỏ về mã gốc.

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| id | text (tự sinh) | Yes | Định danh nội bộ | |
| factory_code | S1 / S4 | Yes | Xưởng | S4 |
| yarn_code | text ≤ 60, duy nhất trong toàn app | Yes | Mã của bản NSM: mã gốc (BR-05) hoặc mã ĐCNSM (BR-33) | S4-2020 |
| base_code | text | Yes | Mã gốc; bằng `yarn_code` nếu là bản gốc | S4-2020 |
| revision_no | integer ≥ 0 | Yes | 0 = bản gốc; n = ĐCNSM thứ n | 0 |
| yarn_name | text ≤ 200 | Yes | Tên sợi | CVC 30/1 (60/40) MVS |
| yarn_group | text (tính, BR-02) | - | Nhóm sợi, viết hoa | CVC |
| count | decimal (tính, BR-02) | - | Chi số | 30 |
| loss_group_key | text (tính, BR-04) | - | Nhóm tiêu hao | CVC (60/40) MVS |
| technology | Ring / MVS (tính, BR-03) | - | Công nghệ | MVS |
| is_compact | yes-no (tính, BR-03) | - | Sợi compact | Không |
| packaging_code | text (mã 4.6 của xưởng) | Yes (trừ dữ liệu cũ thiếu) | Loại đóng gói do Sales chọn | Type 3 |
| components | danh sách 1-9 dòng 4.12.1 | Yes khi nhập NSM | Thành phần nguyên liệu do xưởng nhập (tỷ lệ, dây chuyền chải thô, NSM chải thô) | Cotton 70% C1; Viscose 30% C3 |
| nsm | danh sách (stage_code → decimal ≥ 0, kg/giờ) | Yes khi nhập NSM | NSM các công đoạn không phải chải thô (NSM chải thô nằm trong `components`) | MD1: 100; V: 25 |
| nsm_mode | list of values: Tự điền / Tự nhập | No | Cách xưởng nhập NSM lần gần nhất | Tự điền |
| reference_yarn_code | text | No | Sợi so sánh / tự điền (BR-37) | S4-1988 |
| nsm_warning_reason | text ≤ 500 | No | Lý do khi NSM khác sợi cùng nhóm (BR-38) | Nguyên liệu Pima, chạy chậm hơn |
| adjust_reason | text ≤ 500 | Yes với ĐCNSM | Lý do ĐCNSM | Đơn 50 tấn, chạy tốc độ cao |
| status | list of values (bảng dưới) | Yes | Trạng thái | Đã tính giá |
| status_reasons | danh sách text | No | Lý do "Chưa tính được" (BR-16) | Chưa có nhóm tiêu hao 'CVC (60/40) MVS' |
| reject_reason | text ≤ 500 | Yes khi Từ chối | Lý do xưởng từ chối | Xưởng không có máy compact |
| origin | list of values: Yêu cầu Sales / ĐCNSM / Nhập từ file | Yes | Nguồn tạo | Yêu cầu Sales |
| requested_by, requested_at | text, datetime | Yes | Người và lúc tạo (Sales / xưởng / người nhập file) | |
| handled_by, handled_at | text, datetime | No | Người và lúc xưởng từ chối hoặc lưu NSM lần đầu | |
| first_priced_at | date | No | Ngày tính giá lần đầu (dữ liệu cũ: "Ngày tính giá" của file) | 2026-09-26 |
| last_calculated_at | datetime | No | Lần tính gần nhất | |
| effective_date | date | No | Ngày hiệu lực của giá hiện tại (lần tính lại toàn bộ gần nhất, hoặc ngày tính) | 2026-09-26 |
| is_locked | yes-no (tính) | - | Có ít nhất một dòng giá (4.13) của bản NSM này có mã kế toán | Không |

#### 4.12.1 Thành phần nguyên liệu của sợi (Yarn component)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| material_label | text ≤ 200 | Yes | Tên nguyên liệu; nếu nhóm tiêu hao của sợi có thành phần thì phải là `material_tech_key` của một thành phần (BR-57) | Viscose - Ring |
| ratio | decimal 0 ≤ x ≤ 1 | Yes | Tỷ lệ pha của nguyên liệu | 0.3 |
| carding_stage | list of values: mã dây chuyền chải thô của xưởng / Không chải thô | Yes | Dây chuyền chải thô nguyên liệu chạy qua, xưởng chọn theo từng sợi; mặc định = dây chuyền mà nguyên liệu có tiêu hao chải thô trong nhóm tiêu hao (có nhiều: dây chuyền có `sequence` nhỏ nhất) | C3 |
| pass_no | integer 1-3 (tính) | - | Lượt trên dây chuyền = thứ tự của dòng trong các dòng cùng dây chuyền (BR-56) | 1 |
| nsm_carding | decimal ≥ 0 | Yes nếu có dây chuyền | NSM chải thô của nguyên liệu (kg/giờ) | 45 |
| line_ratio | decimal (tính) | - | Tỷ lệ dây chuyền = tổng `ratio` các dòng cùng `carding_stage` | 0.3 |

**Trạng thái và chuyển đổi:**
| Từ | Sang | Khi nào |
|---|---|---|
| (mới) | Chờ xưởng xem | Sales tạo yêu cầu (UC-15) |
| Chờ xưởng xem | Đã huỷ | Sales huỷ (UC-17) |
| Chờ xưởng xem | Từ chối | Xưởng từ chối, có lý do (UC-18) |
| Chờ xưởng xem | Đã tính giá / Chưa tính được | Xưởng lưu NSM (UC-21): kiểm tra khớp đạt → Đã tính giá; không đạt → Chưa tính được |
| Chưa tính được | Đã tính giá | Tính lại thành công (sửa NSM UC-21, khai báo/sửa tiêu hao UC-11..UC-14, tính lại toàn bộ) |
| Đã tính giá | Có mã kế toán | Có ít nhất một dòng giá được nhập mã kế toán (UC-28) |
| Có mã kế toán | Đã tính giá | Mọi mã kế toán của bản NSM bị xoá (UC-28) |
| Đã tính giá / Có mã kế toán | Chưa tính được | Một lần tính lại không đạt kiểm tra khớp (giữ nguyên giá đang có, BR-16) |
| (mới) | Đã tính giá / Chưa tính được | Tạo ĐCNSM (UC-24) hoặc nhập từ file (UC-34) |
| (mới, nhập từ file) | Có mã kế toán | Dòng dữ liệu cũ có mã kế toán (UC-34) |
Đã huỷ và Từ chối là trạng thái cuối: không sửa, không dùng lại mã.

### 4.13 Dòng bảng giá (Price line)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| id | text (tự sinh) | Yes | Định danh | |
| yarn_id | tham chiếu 4.12 | Yes | Bản NSM | |
| line_code | text ≤ 80, duy nhất | Yes | Mã dòng (BR-30, BR-31) | S4-2020 (CK1) |
| line_type | list of values: Thường / Thí nghiệm / Chiết khấu / Phụ phí | Yes | Loại dòng | Chiết khấu |
| adjustment_percent | decimal 0 < x < 1 | Yes với CK/PP | % chiết khấu / phụ phí | 0.05 |
| adjustment_reason | text ≤ 500 | Yes với CK/PP | Lý do | Đơn hàng lớn, khách hàng chiến lược |
| order_ref | text ≤ 100 | Yes với CK/PP | Đơn hàng cụ thể | PO-2026-118 |
| labor, depreciation, electricity, materials, overhead | decimal ≥ 0 | Yes | 5 khoản chi phí (VND/kg) | 7354.3022 |
| total_vnd | decimal (tính) | - | = tổng 5 khoản (VND/kg) | 19273.3054 |
| usd_per_kg | decimal (tính, không lưu) | - | = total_vnd ÷ tỷ giá đang dùng (BR-22) | 0.7709 |
| accounting_code | text ≤ 100 | No | Mã kế toán; không kiểm tra định dạng, không kiểm tra trùng | S42003000010000000 |
| accounting_code_by, accounting_code_at | text, datetime | No | Người và lúc nhập / sửa mã kế toán | |
| created_by, created_at | text, datetime | Yes | Người và lúc tạo dòng | |
Mỗi bản NSM có đúng 1 dòng Thường và 1 dòng Thí nghiệm khi đã có giá; có 0..n dòng Chiết khấu / Phụ phí.

### 4.14 Chi tiết tính giá (Stage cost detail)
Kết quả lần tính gần nhất của dòng Thường, một dòng cho mỗi công đoạn có thời gian chạy máy > 0 (kể cả đóng gói).

| Field | Type | Description | Example |
|---|---|---|---|
| yarn_id | tham chiếu 4.12 | Bản NSM | |
| sequence, stage_code, stage_name | integer, text, text | Công đoạn | 1, C1, Ăn bông - Chải thô cotton |
| material_label, pass_no | text, integer | Nguyên liệu và lượt (chỉ dây chuyền chải thô; mỗi lượt một dòng) | Cotton, 1 |
| nsm | decimal | NSM (kg/giờ); đóng gói để trống | 65 |
| run_minutes | decimal | Thời gian chạy máy (phút/kg) - BR-17, BR-18 | 0.9473 |
| loss | decimal | Tiêu hao của công đoạn | 0.075 |
| loss_source_stage | text | Chỉ dòng chải thô: dây chuyền mà tiêu hao được lấy từ đó khi khác dây chuyền đang chạy (BR-64); để trống khi lấy đúng dây chuyền đang chạy | C2 |
| loss_note | text (tính) | Ghi chú tiêu hao = "Tiêu hao lấy từ <loss_source_stage> (<dây chuyền đang chạy> chưa khai báo)"; để trống khi `loss_source_stage` trống | Tiêu hao lấy từ C2 (C3 chưa khai báo) |
| cumulative_loss | decimal | Tiêu hao lũy kế - BR-19 | 0.2596 |
| total_rate | decimal | Định mức (VND/phút) | 2538.6280 |
| cost_per_kg | decimal | Chi phí/kg của công đoạn - BR-20 | 3248.1454 |
| labor … overhead | decimal | 5 khoản của công đoạn (VND/kg) | 145.2886 |

### 4.15 Lịch sử giá (Price history)
Một dòng mỗi khi giá của một dòng bảng giá thay đổi (giữ giá TRƯỚC khi đổi) hoặc được tạo.

| Field | Type | Description | Example |
|---|---|---|---|
| line_code | text | Dòng giá | S4-2020 |
| changed_at | datetime | Lúc thay đổi | |
| changed_by | text | Họ tên của tài khoản đăng nhập thực hiện ("Hệ thống" khi không có tài khoản) | Nguyễn Văn A |
| event | list of values: Tính lần đầu / Sửa NSM / Đổi định mức / Đổi dữ liệu nền / Sửa tiêu hao / Đổi hệ số thí nghiệm / Nhập từ file / Tính lại mã chưa tính được | Nguyên nhân | Đổi định mức |
| batch_id | text | Lần tính lại toàn bộ (nếu có) | TL-S4-005 |
| effective_date | date | Ngày hiệu lực của giá mới | 2026-01-01 |
| old_labor … old_overhead, old_total | decimal | Giá trước khi đổi (trống khi Tính lần đầu) | |
| new_labor … new_overhead, new_total | decimal | Giá sau khi đổi | |
| reason | text | Lý do người dùng nhập (nếu có) | |

### 4.16 Lần tính lại toàn bộ (Recalculation batch)
| Field | Type | Description | Example |
|---|---|---|---|
| id | text (tự sinh) | Mã lần tính lại | TL-S4-005 |
| factory_code | S1 / S4 | Xưởng | S4 |
| trigger | list of values: Đổi định mức / Đổi dữ liệu nền / Sửa tiêu hao / Đổi hệ số thí nghiệm / Nhập từ file / Tính lại mã chưa tính được | Nguyên nhân | Đổi định mức |
| effective_date | date | Ngày hiệu lực | 2026-01-01 |
| reason | text | Lý do | |
| run_by, run_at | text, datetime | Người, lúc | |
| yarn_count, changed_line_count, failed_yarn_count | integer | Số bản NSM đã tính, số dòng giá thay đổi, số bản NSM "Chưa tính được" | 2105, 4012, 84 |

### 4.17 Giá cũ đối chiếu (Legacy price)
Giá đọc từ sheet "4. Bang gia da tinh" khi nhập file, để so với giá app tính (UC-35). Không dùng để tính.

| Field | Type | Description | Example |
|---|---|---|---|
| import_id | text | Lần nhập file | NF-S4-001 |
| yarn_code | text | Mã tính giá (đã chuẩn hoá) | S4-2017 |
| labor … overhead, total | decimal | 5 khoản và tổng trong file | |
| priced_date_text | text | "Ngày tính giá" trong file | 06/01/2024 |

### 4.18 Lần nhập file (Import batch)
| Field | Type | Description | Example |
|---|---|---|---|
| id | text (tự sinh) | Mã lần nhập | NF-S4-001 |
| factory_code | S1 / S4 | Xưởng | S4 |
| mode | list of values: Chuyển dữ liệu ban đầu / Cập nhật hàng loạt / Khai báo thành phần sợi pha | Loại | Chuyển dữ liệu ban đầu |
| cutoff_date | date | Ngày chốt dữ liệu (= ngày hiệu lực của giá sau khi nhập) | 2026-10-01 |
| file_name | text | Tên file | 20250106 Bieu mau dinh muc soi 2025 (VIE) S4.xlsm |
| imported_by, imported_at | text, datetime | Người, lúc | |
| counts | số dòng đọc / tạo / cập nhật / bị loại theo từng sheet | Kết quả | |

### 4.19 Nhật ký thay đổi (Audit log)
| Field | Type | Description | Example |
|---|---|---|---|
| at | datetime | Lúc thao tác | |
| username | text | Tên đăng nhập của tài khoản thao tác ("system" khi không có tài khoản) | nva |
| display_name | text | Họ tên của tài khoản thao tác ("Hệ thống" khi không có tài khoản) | Nguyễn Văn A |
| action | text | Thao tác (tên UC) | Sửa nhóm tiêu hao |
| object_ref | text | Đối tượng | S4 / TR (65/35) |
| detail | text | Nội dung thay đổi (trước → sau) | W: 1,00% → 1,20% |
| reason | text | Lý do (nếu có) | |

## 5. Input / output files (File nhập / xuất)

### 5.1 Quy định chung cho file tải lên (UC-33, UC-34)
- Định dạng: .xlsx, .xlsm hoặc .xls; tối đa 60 MB; tối đa 10.000 dòng dữ liệu mỗi sheet. Sai định dạng / quá dung lượng
  → BR-41. Mỗi lần tải lên là file của MỘT xưởng (người dùng chọn xưởng trước khi tải).
- App chỉ đọc các sheet có tên đúng như bảng 5.2 (so khớp không phân biệt hoa thường, dấu, khoảng trắng thừa); các
  sheet khác (kể cả `Norm`, sheet ẩn, sheet `4. Bang gia da tinh (TN x3)`, `Check`...) bị bỏ qua. Macro không chạy.
- Dòng tiêu đề: app tìm trong 10 dòng đầu của sheet các ô có tên cột hoặc mã công đoạn cần đọc (so khớp không phân biệt
  hoa thường, dấu, khoảng trắng thừa); một cột có thể có tên ở dòng này và mã ở dòng kia (như file hiện tại). Dữ liệu
  bắt đầu từ dòng ngay sau dòng tiêu đề cuối cùng; dòng trống ở cột khoá (mã / tên) bị bỏ qua.
- App đọc GIÁ TRỊ của ô (kết quả công thức Excel đã lưu), trừ quy tắc nhận biết nhóm thứ cấp S1 (BR-42).
- Chuyển dữ liệu ban đầu bắt buộc có đủ 7 sheet; cập nhật hàng loạt chỉ cần các sheet muốn cập nhật.
- Dòng lỗi không làm hỏng cả file: dòng hợp lệ vẫn được lưu, dòng lỗi được liệt kê với lý do (BR-43).

### 5.2 Các sheet đọc được
| Sheet | Cột đọc (tên tiêu đề hoặc mã) | Bắt buộc | Dữ liệu tạo ra | Ai được tải (BR-45) |
|---|---|---|---|---|
| Dinh muc (phut) | Công đoạn; Tên công đoạn; Nhóm công đoạn; Nhân công; Khấu hao; Điện; Vật tư; CPQL; Ghi chú (các cột Stt, Xưởng sợi, Giá thành sản xuất bỏ qua - tổng do app tính) | Công đoạn, 5 khoản | Phiên bản định mức mới (4.5), mã = cột "Công đoạn" (gồm cả Type 1..n) | Phòng SO |
| Hoi phe | Cột B nhãn dòng: "Cúi ghép sau máy thô" → Chải thô, "Sợi thô" → Thô, "Bông A2" → Con; cột "Sợi 1" (S1) hoặc "Sợi 4" (S4) theo xưởng đang nhập | 3 dòng | Hồi phế (4.7) | Phòng SO |
| Dong goi | Loại đóng gói (→ name); Loại (→ code); Khối lượng; Công; Phút/kg | Loại, Phút/kg | Loại đóng gói (4.6) | Phòng SO |
| QTCN theo nhom soi | Nhóm sợi; Phân loại (→ technology); Số thành phần; Quy trình công nghệ | Nhóm sợi, Phân loại | Quy trình công nghệ (4.8) | Phòng SO |
| 2. Input tieu hao | Nhóm sợi (→ yarn_group_label; group_key = viết hoa, bỏ khoảng trắng hai đầu); Nguyên liệu; Công nghệ; các cột mã công đoạn của xưởng (tiêu hao; S4 đọc được cả cột "C3" và 3 cột cũ C3.1 / C3.2 / C3.3 - gộp theo BR-59); S4: 5 cột tên thành phần (tiêu đề PE, Other - C3.1, Other - C3.2, Other - C3.3, Cotton ở dòng mã) + 5 cột tỷ lệ tương ứng (PE2, Other - C3.12, Other - C3.22, Other - C3.32, Cotton2) | Nhóm sợi, Công nghệ | Nhóm tiêu hao (4.11) theo BR-42, BR-59 | Xưởng của file, Phòng SO |
| 1. Input NSM | Mã sợi; Tên sợi; các cột ô tỷ lệ pha của file (S4: PE, Other - C3.1, Other - C3.2, Other - C3.3, Cotton; S1: PE, Viscose/other, Cotton); các cột mã công đoạn (NSM, kg/giờ; S4 C3.1 / C3.2 / C3.3 = lượt 1 / 2 / 3 của C3; cột RW, Type 1/2/3 và cột tính sẵn bỏ qua); Loại đóng gói | Tên sợi | Mã sợi / bản NSM (4.12) theo BR-44; thành phần nguyên liệu theo BR-58 | Xưởng của file, Phòng SO |
| 4. Bang gia da tinh | Cột thứ 2 (tiêu đề "Mã Kế Toán" đầu tiên) = mã tính giá; Nhân công; Khấu hao; Điện; Vật tư; CPQL; Ngày tính giá; cột "Mã Kế toán" thứ hai (sau cột "SO check") = mã kế toán | Mã tính giá | Giá cũ đối chiếu (4.17), mã kế toán của dòng Thường, first_priced_at | Phòng SO |

Ví dụ dòng "1. Input NSM" (S4): `S4-2017 | CORE 40/1 (COTTON/ FDY 30D/24F/1) (70/30) MVS | Cotton 0,7 | Other - C3.3 0,3 |
V 25 | MD3 83 | MD2 90 | MD1 100 | CM 50 | C3.3 45 | C1 45 | Type 3`.

Sheet "Dinh muc (phut)": mã định mức = giá trị cột "Công đoạn"; nếu giá trị đó là mã công đoạn đóng gói (F) thì mã định mức
= giá trị cột "Nhóm công đoạn" (file S1 ghi Type 1..7 ở cột "Nhóm công đoạn" và F ở cột "Công đoạn"). Dòng có mã không phải
công đoạn và không phải loại đóng gói của xưởng (ví dụ "C3.1", "C3.2", "C3.3" của S4 - định mức C3 lấy từ dòng "C3") được lưu nhưng
không dùng để tính.

### 5.3 File mẫu (UC-33) - out
`mau-du-lieu-tinh-gia-<S1|S4>.xlsx`: 7 sheet đúng tên bảng 5.2, mỗi sheet có dòng tiêu đề như bảng 5.2 và dữ liệu HIỆN TẠI của
xưởng đó (để người dùng sửa rồi tải lên lại). Sheet "4. Bang gia da tinh" chỉ có tiêu đề.
- Sheet "2. Input tieu hao": một cột cho mỗi công đoạn của xưởng theo thứ tự `sequence` (S4 chỉ có một cột "C3").
- Sheet "1. Input NSM" giữ đúng bố cục cột của file hiện tại để tải lên lại được: ô tỷ lệ pha của file + một cột NSM mỗi công
  đoạn, trong đó S4 ghi lượt 1 / 2 / 3 của C3 vào cột C3.1 / C3.2 / C3.3 (tỷ lệ vào Other - C3.1 / C3.2 / C3.3), lượt 1 của C2
  vào cột C2 (tỷ lệ vào PE), cotton vào C1 (tỷ lệ vào Cotton); S1 ghi lượt 1 của C1 vào C1 (tỷ lệ PE), lượt 1 của C2 vào C2 (tỷ
  lệ Viscose/other), thành phần "Không chải thô" vào ô Cotton. Mã có thành phần không ghi được vào bố cục này (lượt 2-3 trên
  S4 C2, trên S1 C1 / C2, hoặc nguyên liệu chạy dây chuyền khác dây chuyền của cột) được ghi dòng thông tin cơ bản và cột
  REMARK = "Có thành phần chỉ sửa được trên màn hình"; khi tải lên lại, app không đổi thành phần của mã đó (BR-58).

### 5.4 Xuất bảng giá (UC-29) - out
`bang-gia-soi-<yyyymmdd-hhmm>.xlsx`, áp dụng bộ lọc đang chọn trên màn hình:
- Sheet `Bang gia`: STT; Xưởng; Mã dòng; Loại dòng; Mã gốc; Tên sợi; Nhóm sợi; Chi số; Công nghệ; Nhóm tiêu hao; Thành phần
  (dạng "Cotton 70% (C1); Viscose - Ring 30% (C3 lượt 1)"); Nhân công; Khấu
  hao; Điện; Vật tư; CPQL; Tổng (VND/kg); USD/kg; Tỷ giá; Loại đóng gói; Tên loại đóng gói; Ngày tính giá; Ngày hiệu
  lực; Trạng thái; Mã kế toán; % CK/PP; Lý do CK/PP; Đơn hàng.
- Sheet `Chi tiet cong doan`: Mã tính giá; Tên sợi; STT; Công đoạn; Tên công đoạn; Nguyên liệu; Lượt; NSM (kg/giờ); Thời gian chạy máy
  (phút/kg); Tiêu hao; Tiêu hao lũy kế; Định mức (VND/phút); Chi phí/kg; Nhân công; Khấu hao; Điện; Vật tư; CPQL; Ghi chú tiêu hao (`loss_note`, BR-64) -
  cho các bản NSM có trong sheet `Bang gia`.
- Số VND làm tròn đến đồng, USD 4 chữ số thập phân, tỷ lệ dạng % 2 chữ số thập phân (BR-23).

### 5.5 Xuất danh sách khác - out
- `doi-chieu-gia-cu-<yyyymmdd>.xlsx` (UC-35): Mã; Tên sợi; Tổng giá cũ; Tổng giá app; Chênh lệch (VND); Chênh lệch (%);
  5 khoản cũ và mới; Trạng thái.
- `chenh-lech-tinh-lai-<batch_id>.xlsx` (UC-37): Mã dòng; Tên sợi; Loại dòng; Tổng trước; Tổng sau; Chênh lệch (VND);
  Chênh lệch (%).
- `ket-qua-nhap-file-<import_id>.xlsx` (UC-34): Sheet; Dòng Excel; Mã / nhóm; Kết quả (Tạo / Cập nhật / Bị loại); Lý do.

### 5.6 Chuyển dữ liệu từ app cũ (một lần, trước khi dùng app mới)
- **Nguồn:** thư mục dữ liệu Tính giá sợi của app cũ `D:\Vibe Coding\TC-vibe-coding\data\yarn_costing\` - 15 file: `audit_log`,
  `exchange_rates`, `import_batches`, `legacy_prices`, `loss_groups`, `packaging_types`, `price_history`, `process_routes`,
  `rate_versions`, `recalc_batches`, `recovery_rates`, `settings`, `stages`, `user_groups`, `yarns` (đuôi `.json`, tổng khoảng 15 MB).
  Không chép dữ liệu của chức năng Điều chuyển chi phí nội bộ và chức năng mẫu.
- **Đích:** thư mục dữ liệu của chức năng trong app mới `data\yarn_costing\` (thư mục dự án app mới).
- **Cách làm (Phòng SO):** 1. Ngừng nhập liệu Tính giá sợi ở app cũ. 2. Tắt app mới nếu đang chạy. 3. Chép nguyên 15 file từ
  nguồn sang đích (thay file cùng tên nếu có). 4. Mở app mới. Từ đó chỉ dùng app mới; app cũ không còn dùng cho Tính giá sợi.
- **Dữ liệu được giữ nguyên hoàn toàn (BR-61):** cấu hình công đoạn, phiên bản định
  mức, loại đóng gói (cả loại mặc định), hồi phế, quy trình, tỷ giá, hệ số thí nghiệm; nhóm tiêu hao; mã sợi / bản NSM kèm
  thành phần, NSM, trạng thái; dòng giá, mã kế toán; chi tiết tính giá; lịch sử giá; các lần tính lại; các lần nhập file; giá cũ
  đối chiếu; nhật ký thay đổi. App mới **không** tính lại giá khi đọc dữ liệu chép sang; dãy mã tính giá tiếp tục từ số lớn
  nhất đã có (BR-05). File `user_groups` của app cũ không còn được đọc (từ 2026-10-13 người dùng là tài khoản đăng nhập
  của app); dòng nhật ký cũ có nhóm + tên được đọc thành họ tên "<nhóm> - <tên>" (không có tên đăng nhập).
- **Dữ liệu lưu theo cách cũ:** một phần dữ liệu app cũ còn lưu theo cách trước ngày 2026-09-28 (công đoạn C3.1 / C3.2 / C3.3,
  tỷ lệ pha theo ô). App mới tự hiểu và chuyển sang cách mới (C3 nhiều lượt, thành phần nguyên liệu) khi đọc, cùng cách app cũ
  đã làm, không xoá dữ liệu, không đổi giá.
- **Số liệu tham khảo ngày 2026-09-29** (để kiểm tra sau khi chép): 3.435 mã sợi / bản NSM, 1.463 nhóm tiêu hao, 10 loại đóng
  gói, 80 quy trình, 3.258 dòng giá cũ đối chiếu, 4.066 dòng lịch sử giá, 2 lần nhập file, 2 lần tính lại,
  7 dòng nhật ký.
- **Chép lỗi:** nếu một file bị thiếu hoặc hỏng, màn hình không bị dừng; màn hình hiện cảnh báo ghi rõ tên file không đọc được
  và Phòng SO chép lại file đó từ app cũ.
- **Lưu trong cơ sở dữ liệu (từ 2026-10-13):** app lưu dữ liệu trong cơ sở dữ liệu PostgreSQL của công ty (mỗi loại dữ liệu một
  bảng `xuan2894__yarn_costing__<tên>`). Cách chép ở trên vẫn dùng được: lần đầu mở app, khi bảng còn trống, app tự nhập file đã chép vào
  `data\yarn_costing\` (kèm chuyển cách lưu cũ như trên) rồi đổi tên file thành `<tên>.json.imported` để không nhập lại lần hai.

### 5.7 File khai báo thành phần sợi pha (UC-44 out, UC-45 in)
- **Tên file mẫu:** `mau-khai-bao-thanh-phan-<S1|S4>.xlsx`. Định dạng tải lên: .xlsx / .xlsm / .xls, tối đa 60 MB, 10.000 dòng
  (BR-41). Mỗi file là của MỘT xưởng (người dùng chọn xưởng trước khi tải).
- **Sheet đọc:** sheet đầu tiên có tên bắt đầu bằng "Khai bao thanh phan" (so khớp không phân biệt hoa thường, dấu, khoảng
  trắng), ví dụ "Khai bao thanh phan" hoặc "Khai bao thanh phan S1"; không có → "File không có sheet 'Khai bao thanh phan'.
  Vui lòng dùng file mẫu." Các sheet khác bỏ qua.
- **Dòng tiêu đề:** dòng 1. Cột đọc theo tên tiêu đề (so khớp không phân biệt hoa thường, dấu, khoảng trắng thừa), thứ tự cột
  không quan trọng; các cột khác bỏ qua (ví dụ "Dòng trong file S1", "Gợi ý từ công thức Excel", "Ghi chú gợi ý" của bản nháp).

| Cột | Đọc / chỉ để xem | Bắt buộc | Dữ liệu | Ví dụ |
|---|---|---|---|---|
| STT | chỉ để xem | Không | - | 1 |
| Nhóm sợi pha | đọc | Có | `group_key` của nhóm (4.11; viết hoa, bỏ khoảng trắng hai đầu khi so khớp) | MODAL/POLY (52/48) |
| Công nghệ | đọc | Có với nhóm mới | `technology` (Ring / MVS, "ring"/"mvs " được chuẩn hoá); nhóm đã có: bỏ qua, giữ công nghệ của nhóm | Ring |
| Loại hiện tại trong app | chỉ để xem | Không | `level` hiện tại | Nhập từ file - chưa khai báo thành phần |
| Số mã đang dùng | chỉ để xem | Không | số bản NSM có `loss_group_key` = nhóm | 1 |
| Thành phần 1 … Thành phần 5 | đọc | Có ít nhất Thành phần 1 để đổi nhóm | `component_group_key` - `group_key` hoặc `material_tech_key` của một nhóm đã có của cùng xưởng | PE |
| Tỷ lệ 1 (%) … Tỷ lệ 5 (%) | đọc | Có khi có Thành phần tương ứng | `ratio` × 100, số > 0 và ≤ 100 (48 = 48%) | 48 |
| Tổng tỷ lệ (%) | chỉ để xem | Không | công thức cộng tỷ lệ trong file mẫu | 100 |
| Tiêu hao hiện tại (%) | chỉ để xem | Không | tiêu hao đang lưu, dạng "C1 1.344; C2 1.56; …" | |

- **Dòng bỏ qua (không đổi gì, không báo lỗi):** "Nhóm sợi pha" trống, hoặc mọi ô Thành phần 1-5 trống.
- **File mẫu (UC-44)** có 3 sheet: "Khai bao thanh phan" - mỗi nhóm tiêu hao của xưởng một dòng (mọi loại; nhóm Thứ cấp điền sẵn
  thành phần và tỷ lệ đang có; nhóm khác để trống), sắp theo Số mã đang dùng giảm dần; "Danh sach nhom" - các nhóm của xưởng
  (Nhóm tiêu hao, Loại, Nguyên liệu, Công nghệ, Tiêu hao %) để chọn làm thành phần (ô Thành phần có danh sách chọn từ sheet này);
  "Huong dan" - cách điền. File mẫu của app không có gợi ý đọc từ công thức Excel cũ; bản nháp
  `mau-khai-bao-thanh-phan-soi-pha-S1-20260929.xlsx` (đã gửi người dùng, có gợi ý) tải lên được vì có đủ các cột đọc.
- **File kết quả:** như `ket-qua-nhap-file-<import_id>.xlsx` (5.5) với Sheet = "Khai bao thanh phan"; thêm các dòng "Mã sợi" cho
  các mã không ghép được thành phần (BR-68).

## 6. Use cases (Nghiệp vụ)
Mọi UC làm thay đổi dữ liệu đều chạy bằng tài khoản đã đăng nhập (BR-46: thay bằng đăng nhập của ứng dụng) có vai trò phù hợp
(BR-47, BR-48) và ghi nhật ký theo tài khoản (BR-49). Xem, tra cứu, xuất file chỉ cần được cấp quyền mở chức năng.

### UC-01: Khai báo nhóm người dùng và thành viên (đã bỏ 2026-10-13)
- Đã bỏ: người dùng và vai trò do quản trị viên quản lý ở trang `/admin` của app (xem mục 2 và 4.1). Mã UC không dùng lại.

### UC-02: Xem nhật ký thao tác
- **Actor:** Người xem
- **Trigger:** mở Screen 8, chọn khoảng ngày, tài khoản, thao tác, từ khoá.
- **Output:** danh sách nhật ký (mới nhất trước): Lúc, Tài khoản, Họ tên, Thao tác, Đối tượng, Nội dung, Lý do; kèm danh sách tài
  khoản và thao tác có trong khoảng ngày để chọn bộ lọc.
- **Rules applied:** BR-49

### UC-03: Sửa cấu hình công đoạn
- **Actor:** Phòng SO
- **Trigger:** Screen 5, tab xưởng, sửa bảng công đoạn (thêm công đoạn mới, sửa các trường 4.4), nhập ngày hiệu lực và lý
  do, bấm "Lưu cấu hình và tính lại".
- **Main flow:** 1. Kiểm tra BR-50. 2. Lưu. 3. Tính lại toàn bộ xưởng (BR-36) với trigger "Đổi dữ liệu nền".
- **Output:** "Đã lưu cấu hình công đoạn <xưởng>. Đã tính lại N mã, M mã chưa tính được."
- **Errors:** mã công đoạn trùng → "Mã công đoạn '<mã>' đã có ở xưởng <xưởng>."; cumulative_stages có mã không tồn
  tại → "Công đoạn '<mã>' không có ở xưởng <xưởng>."; thiếu ngày hiệu lực / lý do → "Vui lòng chọn ngày hiệu lực và nhập
  lý do."
- **Rules applied:** BR-36, BR-50

### UC-04: Áp dụng định mức chi phí/phút mới
- **Actor:** Phòng SO
- **Trigger:** Screen 5, tab xưởng, sửa bảng định mức (5 khoản cho mỗi công đoạn và mỗi loại đóng gói), nhập ngày hiệu
  lực và lý do, bấm "Áp dụng định mức và tính lại toàn bộ".
- **Main flow:** 1. Kiểm tra mỗi khoản ≥ 0, đủ dòng cho mọi công đoạn (trừ F) và mọi loại đóng gói đang dùng. 2. Tạo phiên
  bản định mức mới (4.5). 3. Tính lại toàn bộ xưởng (BR-36), trigger "Đổi định mức", kể cả bản NSM đã khoá.
- **Output:** "Đã áp dụng định mức mới cho <xưởng> từ ngày <dd/mm/yyyy>. Đã tính lại N mã, M mã chưa tính được." + nút mở
  chênh lệch của lần tính lại (UC-37).
- **Errors:** số âm → "Định mức phải là số ≥ 0."; thiếu dòng → "Thiếu định mức cho: <danh sách mã>."; thiếu ngày / lý do
  → "Vui lòng chọn ngày hiệu lực và nhập lý do."
- **Rules applied:** BR-20, BR-36, BR-51

### UC-05: Khai báo loại đóng gói
- **Actor:** Phòng SO
- **Trigger:** Screen 5, tab xưởng, thêm / sửa loại đóng gói (kể cả đánh dấu "Mặc định"), nhập ngày hiệu lực và lý do (khi có
  tính lại - BR-62), bấm "Lưu đóng gói".
- **Main flow:** 1. Kiểm tra mã duy nhất trong xưởng, phút/kg > 0, tối đa một loại mặc định (BR-60). 2. Hộp xác nhận trước khi
  lưu ghi đúng nội dung theo BR-62 (có tính lại hay không). 3. Lưu. 4. Nếu phút/kg của loại đang được dùng thay đổi (BR-62): tính
  lại toàn bộ xưởng (BR-36), trigger "Đổi dữ liệu nền". Đổi loại mặc định, tên, khối lượng, số công, còn hoạt động, thêm loại
  mới không tính lại và không đổi loại đóng gói của mã đã có.
- **Output:** có tính lại → "Đã lưu loại đóng gói <xưởng>. Đã tính lại N mã, M mã chưa tính được."; không tính lại → "Đã lưu
  loại đóng gói <xưởng>. Giá các mã không thay đổi."
- **Errors:** "Mã đóng gói '<mã>' đã có ở xưởng <xưởng>."; "Phút/kg phải lớn hơn 0."; loại mới chưa có định mức →
  "Loại đóng gói <mã> chưa có định mức chi phí/phút. Vui lòng bổ sung định mức (UC-04) trước khi dùng." (vẫn lưu, nhưng
  chưa hiện cho Sales chọn cho đến khi có định mức); nhiều hơn một loại mặc định → thông báo BR-60.
- **Rules applied:** BR-36, BR-52, BR-60, BR-62

### UC-06: Khai báo hồi phế
- **Actor:** Phòng SO
- **Trigger:** Screen 5, tab xưởng, sửa 3 tỷ lệ hồi phế, nhập ngày hiệu lực và lý do, bấm "Lưu hồi phế và tính lại".
- **Main flow:** 1. Kiểm tra 0 ≤ tỷ lệ < 100%. 2. Lưu. 3. Tính lại toàn bộ xưởng (BR-36), trigger "Đổi dữ liệu nền".
- **Output:** "Đã lưu hồi phế <xưởng>. Đã tính lại N mã, M mã chưa tính được."
- **Errors:** "Tỷ lệ hồi phế phải từ 0% đến dưới 100%."
- **Rules applied:** BR-36

### UC-07: Khai báo quy trình công nghệ
- **Actor:** Phòng SO
- **Trigger:** Screen 5, tab xưởng, thêm / sửa / xoá quy trình theo nhóm sợi + công nghệ, bấm "Lưu quy trình".
- **Main flow:** 1. Kiểm tra khoá (xưởng, nhóm sợi, công nghệ) duy nhất. 2. Lưu, hiển thị các công đoạn nhận ra (BR-13).
  Không tính lại giá.
- **Output:** "Đã lưu quy trình <nhóm sợi> - <công nghệ>."
- **Errors:** "Quy trình cho nhóm '<nhóm>' - <công nghệ> đã có."
- **Rules applied:** BR-13

### UC-08: Cập nhật tỷ giá
- **Actor:** Phòng SO
- **Trigger:** Screen 5, khối Tỷ giá, nhập ngày áp dụng và tỷ giá, bấm "Thêm tỷ giá".
- **Main flow:** 1. Kiểm tra tỷ giá > 0. 2. Lưu. Mọi giá USD hiển thị / xuất sau đó dùng tỷ giá đang dùng (BR-22); không
  tính lại VND.
- **Output:** "Đã thêm tỷ giá <số> từ ngày <dd/mm/yyyy>."
- **Errors:** "Tỷ giá phải lớn hơn 0."
- **Rules applied:** BR-22

### UC-09: Cập nhật hệ số thí nghiệm
- **Actor:** Phòng SO
- **Trigger:** Screen 5, khối Tham số, nhập hệ số, ngày hiệu lực, lý do, bấm "Lưu hệ số".
- **Main flow:** 1. Kiểm tra hệ số > 0. 2. Lưu. 3. Tính lại dòng Thí nghiệm của mọi bản NSM của cả 2 xưởng (BR-30), mỗi
  xưởng một lần tính lại, trigger "Đổi hệ số thí nghiệm".
- **Output:** "Đã đổi hệ số thí nghiệm từ <cũ> thành <mới>. Đã cập nhật N dòng thí nghiệm."
- **Errors:** "Hệ số thí nghiệm phải lớn hơn 0."
- **Rules applied:** BR-30, BR-36

### UC-10: Tra cứu tiêu hao
- **Actor:** Người xem
- **Trigger:** Screen 4, chọn xưởng, loại nhóm, từ khoá.
- **Output:** danh sách nhóm tiêu hao: Nhóm, Nguyên liệu, Công nghệ, Loại, Thành phần (tên + tỷ lệ), tiêu hao từng công
  đoạn (%), Đang khoá (Có/Không), Số mã đang dùng; chọn một nhóm → xem chi tiết và danh sách mã sợi đang dùng nhóm đó.
- **Rules applied:** BR-24

### UC-11: Khai báo nhóm tiêu hao sơ cấp
- **Actor:** Xưởng (xưởng mình), Phòng SO
- **Trigger:** Screen 4, "Thêm nhóm sơ cấp": nhập Nhóm sợi, Nguyên liệu, Công nghệ, tiêu hao từng công đoạn, bấm "Lưu nhóm".
- **Main flow:** 1. Chuẩn hoá group_key. 2. Kiểm tra duy nhất, tiêu hao hợp lệ. 3. Lưu, level = Sơ cấp. 4. Tính lại các
  bản NSM "Chưa tính được" của xưởng có nhóm tiêu hao = group_key (BR-40).
- **Output:** "Đã thêm nhóm tiêu hao '<nhóm>'. Đã tính lại N mã đang chờ tiêu hao."
- **Errors:** "Nhóm tiêu hao '<nhóm>' đã có ở xưởng <xưởng>."; "Tiêu hao phải từ 0% đến dưới 100%."
- **Rules applied:** BR-25, BR-28, BR-40

### UC-12: Khai báo nhóm tiêu hao thứ cấp
- **Actor:** Xưởng (xưởng mình), Phòng SO
- **Trigger:** Screen 4 "Thêm nhóm sợi pha" (hoặc từ Screen 3 khi mã báo thiếu tiêu hao: nhóm được điền sẵn), nhập Nhóm
  sợi, Công nghệ, 1-5 thành phần (chọn nhóm có sẵn của xưởng) và tỷ lệ; bấm "Xem tiêu hao tính ra" rồi "Lưu nhóm".
- **Main flow:** 1. Kiểm tra BR-26, BR-27, BR-28. 2. Tính tiêu hao từng công đoạn (BR-26), hiển thị để xem. 3. Lưu, level
  = Thứ cấp. 4. Tính lại các bản NSM "Chưa tính được" có nhóm tiêu hao = group_key (BR-40).
- **Output:** "Đã thêm nhóm tiêu hao '<nhóm>'. Đã tính lại N mã đang chờ tiêu hao."
- **Errors:** "Nhóm sợi pha cần từ 1 đến 5 thành phần."; "Tổng tỷ lệ thành phần phải bằng 100% (hiện là <x>%)."; "Một
  nhóm không thể là thành phần của chính nó."
- **Rules applied:** BR-26, BR-27, BR-28, BR-40

### UC-13: Sửa nhóm tiêu hao
- **Actor:** Xưởng (xưởng mình, chỉ khi nhóm không khoá), Phòng SO (mọi trường hợp)
- **Trigger:** Screen 4, chọn nhóm, sửa tiêu hao (Sơ cấp / Nhập từ file) hoặc thành phần + tỷ lệ (Thứ cấp; khai báo thành
  phần cho nhóm "Nhập từ file" chuyển nó thành Thứ cấp), nhập lý do, bấm "Lưu thay đổi".
- **Main flow:** 1. Kiểm tra quyền sửa (BR-24). 2. Kiểm tra dữ liệu như UC-11 / UC-12. 3. Lưu. 4. Tính lại tiêu hao của mọi
  nhóm thứ cấp dùng nhóm này làm thành phần (trực tiếp hoặc gián tiếp). 5. Tính lại mọi bản NSM bị ảnh hưởng (BR-24), kể
  cả bản đã khoá khi người sửa là Phòng SO, trigger "Sửa tiêu hao", ngày hiệu lực = ngày nhập trên form (mặc định hôm nay).
- **Output:** "Đã sửa nhóm tiêu hao '<nhóm>'. Đã tính lại N mã (trong đó K mã đã có mã kế toán)."
- **Errors:** xưởng sửa nhóm đang khoá → "Nhóm tiêu hao '<nhóm>' đang được dùng cho sợi đã có mã kế toán (<tối đa 5 mã>).
  Chỉ Phòng SO được sửa."; thiếu lý do → "Vui lòng nhập lý do."
- **Rules applied:** BR-24, BR-25, BR-26, BR-27, BR-28, BR-36

### UC-14: Xoá nhóm tiêu hao
- **Actor:** Xưởng (xưởng mình), Phòng SO
- **Trigger:** Screen 4, chọn nhóm, bấm "Xoá nhóm", xác nhận.
- **Main flow:** chỉ xoá được nhóm không có mã sợi nào dùng và không là thành phần của nhóm khác.
- **Output:** "Đã xoá nhóm tiêu hao '<nhóm>'."
- **Errors:** "Không xoá được: nhóm đang được dùng bởi <N> mã sợi / <M> nhóm sợi pha."
- **Rules applied:** BR-29

### UC-15: Tạo yêu cầu tính giá
- **Actor:** Sales
- **Trigger:** Screen 2, chọn Xưởng (ô Loại đóng gói tự điền loại mặc định của xưởng nếu có - BR-60; Sales đổi được sang loại
  khác trong danh sách), nhập Tên sợi, bấm "Gửi yêu cầu".
- **Main flow:** 1. Kiểm tra tên (BR-01), trùng tên (BR-06). 2. Cấp mã tính giá (BR-05). 3. Tạo mã sợi, trạng thái "Chờ
  xưởng xem", origin = Yêu cầu Sales. 4. Hiển thị nhóm sợi, chi số, công nghệ, nhóm tiêu hao app nhận ra, và cảnh báo nếu
  nhóm tiêu hao chưa có ở xưởng (chỉ thông tin, không chặn).
- **Preconditions:** nút "Gửi yêu cầu" chỉ bấm được khi không có lý do khoá nào của BR-63; khi bị khoá, các lý do hiện ngay
  cạnh nút.
- **Output:** "Đã gửi yêu cầu <mã> - <tên sợi> cho <xưởng>."
- **Errors:** BR-01, BR-06 (chặn, hiện đúng thông báo); các lý do khoá nút của BR-63 (lấy qua UC-42).
- **Rules applied:** BR-01, BR-02, BR-03, BR-04, BR-05, BR-06, BR-52, BR-60, BR-63

### UC-16: Sửa yêu cầu
- **Actor:** Sales
- **Trigger:** Screen 2, chọn yêu cầu "Chờ xưởng xem", sửa Tên sợi / Loại đóng gói, bấm "Lưu sửa đổi". (Không đổi xưởng
  được; muốn đổi xưởng: huỷ và tạo yêu cầu mới.)
- **Main flow:** kiểm tra BR-07, BR-01, BR-06 (không tính chính nó); lưu, giữ nguyên mã.
- **Output:** "Đã cập nhật yêu cầu <mã>."
- **Rules applied:** BR-01, BR-06, BR-07

### UC-17: Huỷ yêu cầu
- **Actor:** Sales
- **Trigger:** Screen 2, chọn yêu cầu "Chờ xưởng xem", bấm "Huỷ yêu cầu", xác nhận.
- **Main flow:** kiểm tra BR-07; trạng thái → Đã huỷ; mã không dùng lại.
- **Output:** "Đã huỷ yêu cầu <mã>."
- **Rules applied:** BR-05, BR-07

### UC-18: Từ chối yêu cầu
- **Actor:** Xưởng (xưởng của yêu cầu), Phòng SO
- **Trigger:** Screen 3, chọn yêu cầu "Chờ xưởng xem", nhập lý do, bấm "Từ chối".
- **Main flow:** kiểm tra trạng thái = Chờ xưởng xem và có lý do; trạng thái → Từ chối; lưu handled_by/at.
- **Output:** "Đã từ chối yêu cầu <mã>."
- **Errors:** "Vui lòng nhập lý do."; trạng thái khác → "Yêu cầu <mã> không còn ở trạng thái 'Chờ xưởng xem'."
- **Rules applied:** BR-08

### UC-19: Xem danh sách yêu cầu
- **Actor:** Người xem (Sales, Xưởng)
- **Trigger:** Screen 2 hoặc Screen 3, lọc theo xưởng, trạng thái, khoảng ngày tạo, từ khoá (mã / tên).
- **Output:** danh sách: Mã, Xưởng, Tên sợi, Loại đóng gói, Trạng thái, Người tạo, Ngày tạo, Người xử lý, Ngày xử lý, Lý do
  từ chối / chưa tính được, Tổng (VND/kg), USD/kg (nếu đã có giá). Screen 3 mặc định lọc "Chờ xưởng xem" và "Chưa tính
  được" và hiện số lượng mỗi trạng thái ở đầu màn hình.
- **Rules applied:** BR-22

### UC-20: Lấy NSM gợi ý (tự điền)
- **Actor:** Xưởng, Phòng SO
- **Trigger:** Screen 3, đang mở một mã, chọn cách nhập "Tự điền", bấm "Lấy NSM từ sợi cùng nhóm".
- **Main flow:** 1. Tìm sợi so sánh (BR-37). 2. Điền NSM các công đoạn trong quy trình (BR-13) và các thành phần nguyên liệu
  (nguyên liệu, tỷ lệ, dây chuyền, NSM chải thô) từ sợi so sánh vào form (chưa lưu). 3. Hiển thị mã, tên, chi số của sợi so
  sánh.
- **Output:** form đã điền sẵn; xưởng sửa các công đoạn khác biệt rồi dùng UC-21.
- **Errors:** không có sợi so sánh → "Chưa có sợi cùng nhóm để tự điền. Vui lòng nhập NSM." (form để trống).
- **Rules applied:** BR-13, BR-37

### UC-21: Nhập NSM, kiểm tra và lưu giá
- **Actor:** Xưởng (xưởng của mã), Phòng SO
- **Trigger:** Screen 3, mở mã ở trạng thái Chờ xưởng xem / Chưa tính được / Đã tính giá (chưa khoá); nhập thành phần nguyên
  liệu và NSM các công đoạn; bấm "Kiểm tra và xem giá" (không lưu) rồi "Lưu NSM và giá".
- **Input:** thành phần nguyên liệu (4.12.1): các dòng được điền sẵn theo thành phần của nhóm tiêu hao của sợi (nhóm Thứ cấp:
  mỗi thành phần một dòng; nhóm Sơ cấp: một dòng là nguyên liệu của nhóm), dây chuyền mặc định theo 4.12.1; xưởng nhập tỷ lệ
  (%), chọn dây chuyền chải thô (hoặc "Không chải thô"), nhập NSM chải thô; khi nhóm tiêu hao chưa có hoặc chưa khai báo thành
  phần, xưởng tự thêm dòng (tên nguyên liệu nhập tay); NSM các công đoạn không phải chải thô (kg/giờ); lý do khác sợi cùng
  nhóm (nếu có cảnh báo).
- **Main flow:**
  1. Kiểm tra khoá (BR-32), tỷ lệ pha (BR-09), thành phần (BR-56, BR-57), NSM (BR-10, BR-11, BR-12); app đánh lượt (BR-56).
  2. So với sợi so sánh (BR-38): nếu có công đoạn khác → hiện cảnh báo, bắt buộc nhập lý do mới lưu được.
  3. Tính giá (BR-14..BR-21) và hiển thị: bảng chi tiết công đoạn (4.14), 5 khoản, Tổng VND/kg, USD/kg, giá thí nghiệm.
  4. Khi bấm Lưu: lưu NSM, thành phần nguyên liệu, cách nhập, sợi so sánh, lý do cảnh báo. Nếu kiểm tra khớp đạt: tạo / cập nhật dòng
     Thường và dòng Thí nghiệm (BR-30), cập nhật các dòng CK/PP đang có (BR-31), lưu chi tiết công đoạn, ghi lịch sử giá
     (event Tính lần đầu hoặc Sửa NSM), trạng thái → Đã tính giá, first_priced_at = hôm nay nếu chưa có, effective_date =
     hôm nay. Nếu không đạt: trạng thái → Chưa tính được + danh sách lý do (BR-16), không tạo / đổi giá.
- **Output:** "Đã lưu giá <mã>: <tổng> VND/kg (<usd> USD/kg)." hoặc "Đã lưu NSM <mã> nhưng chưa tính được giá: <lý do>."
- **Errors:** thông báo của BR-09..BR-12, BR-32, BR-38, BR-56, BR-57.
- **Rules applied:** BR-09 … BR-23, BR-30, BR-31, BR-32, BR-37, BR-38, BR-56, BR-57, BR-58, BR-64

### UC-22: Xem chi tiết tính giá và lịch sử
- **Actor:** Người xem
- **Trigger:** Screen 1 (hoặc 3), chọn một dòng giá.
- **Output:** thông tin mã (tên, nhóm sợi, chi số, công nghệ, nhóm tiêu hao, đóng gói, thành phần nguyên liệu kèm dây chuyền
  và lượt, NSM, trạng thái, khoá,
  sợi so sánh, lý do cảnh báo); bảng chi tiết công đoạn (4.14); tất cả dòng giá của bản NSM; các bản ĐCNSM cùng mã gốc;
  lịch sử giá của dòng (4.15, mới nhất trước).
- **Rules applied:** BR-22, BR-23

### UC-23: Sửa NSM của mã đã có giá (nhập sai)
Dùng lại UC-21 trên mã "Đã tính giá" / "Chưa tính được" chưa khoá; lịch sử ghi event "Sửa NSM". Mã đã khoá: nút lưu bị
tắt và hiện thông báo BR-32, kèm nút "Tạo bản ĐCNSM" (UC-24).

### UC-24: Tạo bản ĐCNSM
- **Actor:** Xưởng (xưởng của mã), Phòng SO
- **Trigger:** Screen 3, mở một mã (gốc hoặc ĐCNSM, bất kể khoá), bấm "Tạo bản ĐCNSM", nhập lý do, sửa NSM / thành phần nguyên liệu, bấm
  "Kiểm tra và xem giá" rồi "Lưu bản ĐCNSM".
- **Main flow:** 1. Chép tên, đóng gói, thành phần nguyên liệu, NSM từ bản đang mở vào form. 2. Kiểm tra như UC-21 (trừ khoá) + lý do bắt
  buộc. 3. Cấp mã ĐCNSM (BR-33). 4. Tạo mã sợi mới (origin ĐCNSM, revision_no = n), tính giá như UC-21 bước 4. Bản gốc giữ
  nguyên.
- **Output:** "Đã tạo bản <mã ĐCNSM>: <tổng> VND/kg."
- **Errors:** "Vui lòng nhập lý do điều chỉnh."; các lỗi của UC-21.
- **Rules applied:** BR-09 … BR-23, BR-30, BR-33, BR-38, BR-56, BR-57, BR-58, BR-64

### UC-25: Tạo dòng chiết khấu / phụ phí
- **Actor:** Xưởng (xưởng của mã), Phòng SO
- **Trigger:** Screen 1 hoặc 3, chọn một bản NSM đã có giá (kể cả đã khoá), bấm "Thêm CK/PP", chọn Chiết khấu hoặc Phụ phí,
  nhập %, lý do, đơn hàng, bấm "Lưu dòng CK/PP".
- **Main flow:** 1. Kiểm tra BR-34. 2. Cấp mã (BR-31). 3. Tính 5 khoản (BR-31), tạo dòng, ghi lịch sử (Tính lần đầu).
- **Output:** "Đã tạo dòng <mã dòng>: <tổng> VND/kg."
- **Errors:** "% chiết khấu / phụ phí phải lớn hơn 0 và nhỏ hơn 100."; "Vui lòng nhập lý do và đơn hàng cụ thể."; bản NSM
  chưa có giá → "Mã <mã> chưa có giá, chưa tạo được dòng CK/PP."
- **Rules applied:** BR-31, BR-34

### UC-26: Xoá dòng chiết khấu / phụ phí
- **Actor:** Xưởng (xưởng của mã), Phòng SO
- **Trigger:** Screen 1, chọn dòng CK/PP chưa có mã kế toán, bấm "Xoá dòng CK/PP", xác nhận.
- **Main flow:** kiểm tra dòng chưa có mã kế toán; xoá dòng (lịch sử của dòng vẫn giữ); số thứ tự CK/PP không dùng lại.
- **Output:** "Đã xoá dòng <mã dòng>."
- **Errors:** "Dòng <mã dòng> đã có mã kế toán, không xoá được."
- **Rules applied:** BR-35

### UC-27: Tra cứu bảng giá
- **Actor:** Người xem
- **Trigger:** Screen 1, chọn bộ lọc: Xưởng, Loại dòng, Trạng thái, Công nghệ, Nhóm sợi, Có / chưa có mã kế toán, khoảng ngày
  tính giá, từ khoá (mã dòng / tên / mã kế toán).
- **Output:** danh sách dòng giá (cột như sheet `Bang gia` 5.4) + tổng số dòng, số dòng có mã kế toán, số mã "Chưa tính
  được"; tỷ giá đang dùng và hệ số thí nghiệm hiện ở đầu màn hình.
- **Rules applied:** BR-22, BR-23

### UC-28: Nhập / sửa / xoá mã kế toán
- **Actor:** Kế toán, Xưởng (xưởng của mã), Phòng SO
- **Trigger:** Screen 1, chọn một dòng giá, nhập hoặc sửa ô Mã kế toán (để trống = xoá), bấm "Lưu mã kế toán".
- **Main flow:** 1. Lưu mã (bỏ khoảng trắng hai đầu), người và lúc nhập. 2. Cập nhật khoá và trạng thái bản NSM (BR-32,
  bảng trạng thái 4.12). 3. Ghi nhật ký (mã cũ → mã mới).
- **Output:** "Đã lưu mã kế toán cho dòng <mã dòng>." / "Đã xoá mã kế toán của dòng <mã dòng>."
- **Errors:** "Mã kế toán tối đa 100 ký tự."
- **Rules applied:** BR-32, BR-48

### UC-29: Xuất Excel bảng giá
- **Actor:** Người xem
- **Trigger:** Screen 1, bấm "Xuất Excel".
- **Output:** file 5.4 theo bộ lọc đang chọn.
- **Rules applied:** BR-22, BR-23

### UC-30: Kiểm tra giá bất thường
- **Actor:** Người xem
- **Trigger:** Screen 7 khối "Sai lệch giá" (và Screen 1 nút "Kiểm tra giá bất thường"), chọn xưởng.
- **Output:** danh sách cặp mã vi phạm BR-39: Công nghệ, Nhóm sợi, Nhóm tiêu hao, Mã trước, Chi số trước, Giá trước, Mã sau,
  Chi số sau, Giá sau, Lý do sai; số nhóm và số cặp vi phạm.
- **Rules applied:** BR-39

### UC-31: Kiểm tra NSM bất thường
- **Actor:** Người xem
- **Trigger:** Screen 7 khối "NSM bất thường", chọn xưởng.
- **Output:** danh sách theo BR-54: Công nghệ, Nhóm tiêu hao, Công đoạn, Giá trị phổ biến, Mã khác biệt, NSM của mã đó, Lý
  do đã ghi (nếu có).
- **Rules applied:** BR-54

### UC-32: Xem dashboard
- **Actor:** Người xem
- **Trigger:** Screen 7, chọn xưởng (S1 / S4 / Cả hai), khoảng ngày (mặc định: từ ngày 1 tháng hiện tại đến hôm nay).
- **Output:** các chỉ số BR-53 dạng ô số liệu; số yêu cầu mới theo tuần và khả năng đáp ứng theo tuần dạng biểu đồ; số dòng
  giá theo trạng thái.
- **Rules applied:** BR-53

### UC-33: Tải file mẫu
- **Actor:** Người xem
- **Trigger:** Screen 6, chọn xưởng, bấm "Tải file mẫu".
- **Output:** file 5.3.

### UC-34: Kiểm tra và lưu dữ liệu từ file
- **Actor:** Phòng SO (mọi sheet), Xưởng (sheet NSM và tiêu hao của xưởng mình)
- **Trigger:** Screen 6, chọn xưởng, chọn loại (Chuyển dữ liệu ban đầu / Cập nhật hàng loạt), chọn ngày chốt, tải file, bấm
  "Kiểm tra file" (không lưu); xem kết quả từng sheet; bấm "Lưu N dòng hợp lệ".
- **Main flow:**
  1. Kiểm tra file (BR-41) và quyền theo sheet (BR-45).
  2. Đọc các sheet theo thứ tự: Dinh muc (phut), Hoi phe, Dong goi, QTCN theo nhom soi, 2. Input tieu hao, 1. Input NSM,
     4. Bang gia da tinh; áp dụng BR-42, BR-43, BR-44 cho từng dòng; hiển thị số dòng Tạo / Cập nhật / Bị loại mỗi sheet và
     danh sách dòng bị loại kèm lý do.
  3. Khi bấm Lưu: lưu các dòng hợp lệ; nếu có sheet định mức, hồi phế hoặc đóng gói thì tạo phiên bản định mức / dữ liệu nền
     mới với ngày hiệu lực = ngày chốt; tính lại toàn bộ xưởng một lần (BR-36, trigger "Nhập từ file", ngày hiệu lực = ngày
     chốt); lưu giá cũ đối chiếu (4.17); tạo lần nhập file (4.18).
- **Output:** "Đã nhập file <tên file>: tạo X, cập nhật Y, bị loại Z dòng. Đã tính giá N mã, M mã chưa tính được." + nút tải
  kết quả nhập file (5.5) + nút mở đối chiếu giá cũ (UC-35).
- **Errors:** BR-41; chuyển dữ liệu ban đầu thiếu sheet → "File thiếu sheet: <danh sách>."; sheet thiếu cột bắt buộc →
  "Sheet '<sheet>' thiếu cột bắt buộc: <danh sách>."; xưởng tải sheet không được phép → sheet đó bị bỏ qua với thông báo
  "Sheet '<sheet>' chỉ Phòng SO được cập nhật, đã bỏ qua."
- **Rules applied:** BR-36, BR-41 … BR-45, BR-58, BR-59

### UC-35: Đối chiếu giá cũ với giá app
- **Actor:** Người xem
- **Trigger:** Screen 6, chọn một lần nhập file.
- **Output:** danh sách mã có giá cũ: Mã, Tên sợi, Tổng cũ, Tổng app, Chênh lệch VND, Chênh lệch %, 5 khoản cũ / mới, Trạng
  thái; lọc "Chỉ hiện mã lệch trên 1 VND/kg"; số mã khớp (lệch ≤ 1 VND/kg), số mã lệch, số mã chưa tính được; nút "Xuất
  Excel" (5.5).
- **Rules applied:** BR-55

### UC-36: Xem danh sách lần tính lại toàn bộ
- **Actor:** Người xem
- **Trigger:** Screen 5 hoặc Screen 7, khối "Các lần tính lại".
- **Output:** danh sách 4.16 (mới nhất trước).

### UC-37: Xem chênh lệch của một lần tính lại
- **Actor:** Người xem
- **Trigger:** chọn một lần tính lại (UC-36) hoặc bấm nút sau UC-04.
- **Output:** danh sách dòng giá thay đổi: Mã dòng, Tên sợi, Loại dòng, Tổng trước, Tổng sau, Chênh lệch VND, Chênh lệch %;
  số dòng tăng / giảm / không đổi; chênh lệch % trung bình; lọc theo loại dòng; nút "Xuất Excel" (5.5).
- **Rules applied:** BR-53

### UC-38: Lấy dữ liệu tham chiếu (bổ sung ở Prompt 2 cho giao diện)
- **Actor:** Người xem
- **Trigger:** mở bất kỳ màn hình nào (danh sách chọn, thẻ dữ liệu nền).
- **Input:** xưởng (không bắt buộc).
- **Output:** xưởng và dây chuyền chải thô, cấu hình công đoạn, phiên bản định mức (hiện tại + danh sách), loại đóng gói, hồi phế, quy
  trình công nghệ, tỷ giá (danh sách + đang dùng), hệ số thí nghiệm, danh sách nhóm sợi. Không có thay đổi dữ liệu.
- **Errors:** file dữ liệu chép từ app cũ không đọc được → thông báo BR-61 (các dữ liệu khác vẫn hiện).
- **Rules applied:** BR-61

### UC-39: Xác thực người thao tác (đã bỏ 2026-10-13)
- Đã bỏ: ai thao tác là tài khoản đăng nhập của app, chức năng không hỏi lại. Mã UC không dùng lại.

### UC-40: Nhận diện tên sợi (bổ sung ở Prompt 2 cho giao diện)
- **Actor:** Người xem (Sales khi gõ tên)
- **Trigger:** Screen 2, gõ tên sợi và chọn xưởng.
- **Output:** nhóm sợi, chi số, công nghệ, compact, nhóm tiêu hao (BR-02..BR-04), có / chưa có nhóm tiêu hao ở xưởng, tên
  hợp lệ hay không (BR-01), mã trùng tên (BR-06) nếu có. Không lưu gì.
- **Rules applied:** BR-01, BR-02, BR-03, BR-04, BR-06

### UC-41: Xem danh sách lần nhập file (bổ sung ở Prompt 2 cho giao diện)
- **Actor:** Người xem
- **Trigger:** Screen 6, khối "Các lần nhập".
- **Output:** danh sách 4.18 (mới nhất trước): mã, xưởng, loại, ngày chốt, tên file, người, lúc, số dòng tạo / cập nhật / bị
  loại.

### UC-42: Kiểm tra điều kiện gửi yêu cầu (bổ sung ở Prompt 2 cho giao diện, 2026-09-29)
- **Actor:** Người xem (Sales trên Screen 2)
- **Trigger:** mở Screen 2, chọn xưởng.
- **Input:** xưởng đang chọn (không bắt buộc).
- **Main flow:** áp dụng BR-63, trả lý do khoá nút "Gửi yêu cầu" do dữ liệu của xưởng (rỗng = bấm được); kết quả không phụ thuộc
  tài khoản đang dùng. Lý do thiếu vai trò (BR-47) do màn hình tự thêm khi tắt nút. Không lưu gì.
- **Output:** các lý do hiện ngay cạnh nút "Gửi yêu cầu".
- **Rules applied:** BR-63

### UC-43: Tính lại các mã chưa tính được (bổ sung 2026-09-29)
- **Actor:** Phòng SO
- **Trigger:** Screen 5, chọn xưởng, nhập ngày hiệu lực (mặc định hôm nay) và lý do, bấm "Tính lại các mã chưa tính được", xác
  nhận.
- **Preconditions:** tài khoản có vai trò Phòng SO (BR-47).
- **Input:** xưởng; ngày hiệu lực; lý do.
- **Main flow:** 1. Kiểm tra ngày hiệu lực và lý do. 2. Lấy các bản NSM "Chưa tính được" của xưởng (BR-65); không có → thông
  báo lỗi. 3. Tính lại từng bản (BR-14..BR-20, BR-58, BR-64). 4. Lưu kết quả, lịch sử giá, tạo lần tính lại (4.16). 5. Ghi nhật ký
  (BR-49).
- **Output:** "Đã tính lại N mã chưa tính được của xưởng <xưởng>: M mã đã có giá, K mã vẫn chưa tính được." + nút "Xem chênh lệch"
  (UC-37).
- **Errors / alternative flows:** không có mã → "Xưởng <xưởng> không có mã nào đang 'Chưa tính được'."; thiếu ngày / lý do →
  "Vui lòng chọn ngày hiệu lực và nhập lý do."; không phải Phòng SO → thông báo BR-47.
- **Rules applied:** BR-14..BR-20, BR-47, BR-49, BR-58, BR-64, BR-65

### UC-44: Tải file mẫu khai báo thành phần sợi pha (bổ sung 2026-09-29)
- **Actor:** Người xem
- **Trigger:** Screen 6, chọn xưởng, chọn Loại tải "Khai báo thành phần sợi pha", bấm "Tải file mẫu".
- **Output:** file mẫu 5.7 của xưởng đó.

### UC-45: Kiểm tra và lưu file khai báo thành phần sợi pha (bổ sung 2026-09-29)
- **Actor:** Xưởng (xưởng mình, nhóm chưa khoá), Phòng SO (mọi nhóm) - BR-69
- **Trigger:** Screen 6, chọn xưởng, Loại tải "Khai báo thành phần sợi pha", nhập Ngày hiệu lực (mặc định hôm nay) và Lý do, tải
  file, bấm "Kiểm tra file" (không lưu); xem kết quả; bấm "Lưu N nhóm hợp lệ", xác nhận.
- **Preconditions:** tài khoản có vai trò phù hợp (BR-47, BR-48); ngày hiệu lực và lý do bắt buộc khi lưu.
- **Main flow:**
  1. Kiểm tra file (BR-41, 5.7), quyền (BR-69).
  2. Đọc từng dòng theo BR-66; dòng lỗi liệt kê với lý do (BR-43).
  3. Với mỗi nhóm hợp lệ: nhóm mới / loại mới / thành phần mới, tiêu hao tính theo thành phần (BR-67) - hiển thị tiêu hao cũ và mới
     từng công đoạn; số mã bị ảnh hưởng (mã dùng nhóm đó hoặc nhóm sợi pha dùng nhóm đó làm thành phần, BR-24); các mã không ghép
     được thành phần (BR-68).
  4. Khi bấm Lưu: lưu các nhóm (BR-67), tính lại tiêu hao các nhóm sợi pha dùng chúng làm thành phần, đổi tên thành phần của các
     mã (BR-68), tính lại mọi bản NSM bị ảnh hưởng (trạng thái Đã tính giá, Có mã kế toán, Chưa tính được; kể cả đã khoá) theo
     BR-14..BR-20, BR-64 với trigger "Sửa tiêu hao", ngày hiệu lực và lý do đã nhập; tạo một lần tính lại (4.16), một lần nhập
     file (4.18, loại "Khai báo thành phần sợi pha"), ghi nhật ký (BR-49).
- **Output:** "Đã khai báo thành phần cho N nhóm (tạo mới M nhóm), bị loại Z dòng. Đã tính lại K mã, L mã chưa tính được." + nút
  "Xem chênh lệch" (UC-37) + nút "Tải kết quả nhập file" (5.7).
- **Errors / alternative flows:** BR-41; không có sheet → thông báo 5.7; thiếu cột "Nhóm sợi pha" hoặc "Thành phần 1" / "Tỷ lệ 1
  (%)" → "Sheet 'Khai bao thanh phan' thiếu cột bắt buộc: <danh sách>."; lỗi từng dòng theo BR-66, BR-69; không có dòng hợp lệ →
  nút Lưu tắt, thông báo "Không có nhóm hợp lệ để lưu."; thiếu ngày / lý do khi lưu → "Vui lòng chọn ngày hiệu lực và nhập lý
  do."
- **Rules applied:** BR-14..BR-20, BR-24, BR-26, BR-27, BR-36, BR-41, BR-43, BR-47, BR-49, BR-64, BR-66, BR-67, BR-68, BR-69

## 7. Business rules (Quy tắc nghiệp vụ)
| ID | Rule | Error message shown to user (VI) |
|---|---|---|
| BR-01 | Tên sợi bắt buộc, ≤ 200 ký tự, phải chứa "/1" và có chi số hợp lệ đứng ngay trước "/1" (BR-02) | Tên sợi phải có chi số dạng '<số>/1', ví dụ 'CVC 30/1 (60/40)'. Vui lòng sửa lại tên sợi. |
| BR-02 | Nhận chi số và nhóm sợi từ tên (như file): lấy 2 ký tự ngay trước "/1", bỏ khoảng trắng; nếu 2 ký tự đó chứa dấu "." thì lấy 4 ký tự ngay trước "/1"; kết quả phải là số > 0 → `count`. `yarn_group` = phần tên trước lần xuất hiện đầu tiên của chi số, bỏ khoảng trắng hai đầu, viết hoa | (dùng thông báo BR-01) |
| BR-03 | `technology` = MVS nếu tên chứa "MVS" (không phân biệt hoa thường), ngược lại Ring. `is_compact` = Có nếu tên chứa "COMPACT" (không phân biệt hoa thường) | - |
| BR-04 | `loss_group_key` = tên sợi bỏ đoạn "<chi số>/1" (nếu sau đó là khoảng trắng thì thay "<chi số>/1 " bằng một khoảng trắng), bỏ khoảng trắng hai đầu, viết hoa. Ví dụ "CVC 30/1 (60/40) recycle" → "CVC (60/40) RECYCLE" | - |
| BR-05 | Mã tính giá mới = `code_prefix` của xưởng + (số lớn nhất N trong các mã gốc dạng "<xưởng>-N" đã từng có ở xưởng, kể cả Đã huỷ, Từ chối, mã nhập từ file) + 1. Khởi đầu: S4 lớn nhất 2019 → S4-2020; S1 lớn nhất 1316 → S1-1317. Mã không dùng lại. Mã không theo dạng "<xưởng>-N" (ví dụ mã kế toán dùng làm mã) không tính vào N | - |
| BR-06 | Không cho tạo / sửa yêu cầu nếu cùng xưởng đã có mã gốc có tên sợi trùng (so sánh không phân biệt hoa thường, gộp khoảng trắng liên tiếp) và trạng thái khác Đã huỷ, Từ chối | Sợi '<tên>' đã có ở mã <mã> của xưởng <xưởng> (trạng thái: <trạng thái>). Không tạo yêu cầu mới. |
| BR-07 | Sales chỉ sửa / huỷ được yêu cầu đang "Chờ xưởng xem" | Chỉ sửa hoặc huỷ được yêu cầu đang 'Chờ xưởng xem'. Yêu cầu <mã> đang ở trạng thái '<trạng thái>'. |
| BR-08 | Từ chối chỉ áp dụng cho yêu cầu "Chờ xưởng xem" và bắt buộc có lý do | Vui lòng nhập lý do. |
| BR-09 | Tỷ lệ pha: mỗi thành phần nguyên liệu từ 0% đến 100%; tổng các thành phần = 100% (cho phép sai lệch ≤ 0,01%) | Tổng tỷ lệ pha phải bằng 100% (hiện là <x>%). |
| BR-10 | NSM mỗi công đoạn là số ≥ 0 (để trống = 0); phải có ít nhất một công đoạn (không kể F) có NSM > 0 | NSM phải là số ≥ 0 và cần nhập ít nhất một công đoạn. |
| BR-11 | Ở xưởng có cả "S" và "S Compact": sợi compact chỉ được có NSM ở "S Compact", sợi không compact chỉ được có NSM ở "S" | Sợi compact phải nhập NSM ở công đoạn 'S Compact' (sợi thường nhập ở 'S'). |
| BR-12 | Mã phải có loại đóng gói đang có định mức; công đoạn đóng gói F luôn được tính (không nhập NSM) | Mã <mã> chưa có loại đóng gói hợp lệ. Vui lòng chọn loại đóng gói. |
| BR-13 | Công đoạn hiển thị để nhập NSM: tách `route_text` của quy trình (xưởng, nhóm sợi, công nghệ) theo dấu "-", bỏ khoảng trắng; mỗi bước khớp với `stage_code` của xưởng (không phân biệt hoa thường); bước "C3.1", "C3.2", "C3.3" (nếu có) khớp C3; bước "S" khớp S và S Compact; bước không khớp công đoạn nào (B1, B2, B3, LF, RW, "Cúi cotton"...) bị bỏ qua; F luôn có. Không có quy trình hoặc quy trình trống → hiển thị tất cả công đoạn của xưởng. Mã đã có NSM ở công đoạn ngoài quy trình thì công đoạn đó vẫn hiển thị | - |
| BR-14 | Chỉ tính giá khi kiểm tra khớp (BR-15) đạt ở mọi công đoạn; không đạt thì không tạo / đổi giá | - |
| BR-15 | Kiểm tra khớp: có nhóm tiêu hao `loss_group_key` ở xưởng; với mọi công đoạn không phải chải thô và không phải công đoạn ghép: (NSM > 0 và tiêu hao > 0) hoặc (NSM = 0 và tiêu hao = 0); với mỗi thành phần có dây chuyền chải thô: (NSM chải thô > 0 và tiêu hao của lượt (BR-58) > 0) hoặc (cả hai = 0); mỗi thành phần của nhóm tiêu hao có tiêu hao ở một dây chuyền chải thô phải có dòng thành phần tương ứng trong sợi; có định mức cho mọi công đoạn có NSM > 0 và cho loại đóng gói | (lý do theo BR-16) |
| BR-16 | Khi không đạt, trạng thái "Chưa tính được", `status_reasons` gồm các câu tương ứng: "Chưa có nhóm tiêu hao '<nhóm>' ở xưởng <xưởng>. Vui lòng khai báo tiêu hao."; "Công đoạn <mã>: có NSM nhưng nhóm tiêu hao không có tiêu hao."; "Công đoạn <mã>: nhóm tiêu hao có tiêu hao nhưng chưa nhập NSM."; "<Dây chuyền> lượt <n> (<nguyên liệu>): có NSM nhưng nguyên liệu chưa khai báo tiêu hao ở <dây chuyền>. Vui lòng khai báo tiêu hao chải thô của nguyên liệu ở dây chuyền này." (dây chuyền không có dây chuyền tương đương, ví dụ S4 C1) hoặc "<Dây chuyền> lượt <n> (<nguyên liệu>): có NSM nhưng nguyên liệu chưa khai báo tiêu hao ở <dây chuyền> hoặc <dây chuyền tương đương>. Vui lòng khai báo tiêu hao chải thô của nguyên liệu." (dây chuyền có dây chuyền tương đương - BR-64); "<Dây chuyền> lượt <n> (<nguyên liệu>): có tiêu hao nhưng chưa nhập NSM."; "Nguyên liệu <nguyên liệu> có tiêu hao chải thô nhưng chưa có dòng thành phần trong sợi."; "<Dây chuyền>: nhóm tiêu hao chưa khai báo thành phần nên chưa xác định được tiêu hao từng lượt. Vui lòng khai báo thành phần cho nhóm tiêu hao."; "Chưa có định mức chi phí/phút cho <mã>."; "Chưa có loại đóng gói." Giá đang có (nếu có) được giữ nguyên | Đã lưu NSM <mã> nhưng chưa tính được giá: <các lý do>. |
| BR-17 | Thời gian chạy máy (phút/kg) = 0 nếu NSM = 0; ngược lại = 60 ÷ NSM × (1 + hồi phế của `recovery_type`, = 0 nếu "Không") × tỷ lệ theo `blend_slot`: "Tỷ lệ của lượt" = `ratio` của thành phần (dây chuyền chải thô: tính riêng cho từng lượt với NSM chải thô của lượt đó); "Tỷ lệ dây chuyền X" = `line_ratio` của dây chuyền X; "Không" = 1 | - |
| BR-18 | Thời gian đóng gói (phút/kg) = `minutes_per_kg` của loại đóng gói của mã; tiêu hao và tiêu hao lũy kế của F = 0 | - |
| BR-19 | Tiêu hao lũy kế của công đoạn X (hoặc của một lượt chải thô trên dây chuyền X) = 0 nếu thời gian chạy máy = 0; ngược lại = tiêu hao của X (với lượt chải thô: tiêu hao của lượt, BR-58) + tổng tiêu hao (theo nhóm tiêu hao của mã) của các công đoạn trong `cumulative_stages` của X. Chi phí từng lượt tính theo BR-20 với định mức của dây chuyền X | - |
| BR-20 | Với mỗi công đoạn có thời gian > 0 và mỗi khoản K (Nhân công, Khấu hao, Điện, Vật tư, CPQL): chi phí K (VND/kg) = định mức K của công đoạn (đóng gói: của loại đóng gói) × thời gian ÷ (1 − tiêu hao lũy kế). Chi phí/kg của công đoạn = tổng 5 khoản. Giá dòng Thường: mỗi khoản = tổng khoản đó qua mọi công đoạn; Tổng = tổng 5 khoản. Định mức dùng là phiên bản mới nhất của xưởng | - |
| BR-21 | Tính toán giữ đủ chữ số thập phân (không làm tròn trung gian) | - |
| BR-22 | USD/kg = Tổng VND/kg ÷ tỷ giá đang dùng (4.9) tại lúc xem / xuất; đổi tỷ giá không làm đổi giá VND và không ghi lịch sử giá | - |
| BR-23 | Hiển thị và xuất: VND làm tròn đến đồng; USD 4 chữ số thập phân; tỷ lệ, tiêu hao, hồi phế dạng % 2 chữ số thập phân; thời gian 4 chữ số thập phân; định mức VND/phút 2 chữ số thập phân | - |
| BR-24 | Nhóm tiêu hao "bị ảnh hưởng" khi sửa nhóm G = G và mọi nhóm thứ cấp dùng G làm thành phần (trực tiếp hoặc gián tiếp). Bản NSM bị ảnh hưởng = mọi bản NSM (trạng thái Đã tính giá, Có mã kế toán, Chưa tính được) có `loss_group_key` thuộc các nhóm bị ảnh hưởng. G "đang khoá" nếu ít nhất một bản NSM bị ảnh hưởng đang khoá. Nhóm không khoá: xưởng của nhóm hoặc Phòng SO được sửa. Nhóm đang khoá: chỉ Phòng SO được sửa, bắt buộc lý do; thay đổi áp dụng cho TẤT CẢ bản NSM bị ảnh hưởng, kể cả bản đã khoá | Nhóm tiêu hao '<nhóm>' đang được dùng cho sợi đã có mã kế toán (<tối đa 5 mã>). Chỉ Phòng SO được sửa. |
| BR-25 | Nhóm sơ cấp và nhóm "Nhập từ file - chưa khai báo thành phần": tiêu hao nhập tay từng công đoạn | - |
| BR-26 | Tiêu hao thứ cấp tại công đoạn s = Σ (tiêu hao của thành phần i tại s × tỷ lệ i) nếu `secondary_method` của s = Bình quân; = Σ tiêu hao của thành phần i tại s nếu = Cộng thẳng. Tính lại tự động mỗi khi một thành phần thay đổi | - |
| BR-27 | Nhóm thứ cấp có 1-5 thành phần; mỗi thành phần là một nhóm (bất kỳ loại) đã có của cùng xưởng, khác chính nó và không tạo vòng (A dùng B, B dùng A); mỗi tỷ lệ > 0 và tổng tỷ lệ = 100% (sai lệch ≤ 0,01%) | Nhóm sợi pha cần từ 1 đến 5 thành phần, tổng tỷ lệ bằng 100% và không được dùng chính nó làm thành phần. |
| BR-28 | group_key duy nhất trong xưởng; mỗi tiêu hao 0 ≤ x < 100% | Nhóm tiêu hao '<nhóm>' đã có ở xưởng <xưởng>. / Tiêu hao phải từ 0% đến dưới 100%. |
| BR-29 | Chỉ xoá được nhóm tiêu hao không có mã sợi nào dùng và không là thành phần của nhóm khác | Không xoá được: nhóm đang được dùng bởi <N> mã sợi / <M> nhóm sợi pha. |
| BR-30 | Dòng Thí nghiệm của một bản NSM: mã = mã dòng Thường + "TN" (ví dụ S4-2020TN, S4-586 (ĐCNSM2)TN); mỗi khoản = khoản của dòng Thường × `trial_factor`. Tạo cùng lúc với dòng Thường, cập nhật mỗi khi dòng Thường đổi hoặc hệ số đổi. Dòng CK/PP không tạo dòng thí nghiệm | - |
| BR-31 | Dòng CK/PP: mã = mã dòng Thường + " (CKn)" hoặc " (PPn)", n = số thứ tự lớn nhất đã dùng cho loại đó của bản NSM + 1 (không dùng lại). Mỗi khoản = khoản của dòng Thường × (1 − %) với Chiết khấu, × (1 + %) với Phụ phí. Tự cập nhật (giữ nguyên %) mỗi khi dòng Thường đổi | - |
| BR-32 | Bản NSM bị khoá khi ít nhất một dòng giá của nó (Thường, Thí nghiệm, CK, PP) có mã kế toán. Bản khoá: không sửa tên, đóng gói, tỷ lệ pha, NSM; không sửa / xoá dòng CK/PP đã có mã kế toán. Vẫn được: tạo ĐCNSM, tạo dòng CK/PP mới, nhập / sửa mã kế toán, và giá vẫn được tính lại theo BR-24, BR-36 | Mã <mã> đã có mã kế toán nên không sửa được. Muốn điều chỉnh NSM, hãy tạo bản ĐCNSM. |
| BR-33 | Mã ĐCNSM = mã gốc + " (ĐCNSMn)", n = số lớn nhất đã dùng cho mã gốc đó + 1 (bản nhập từ file "(ĐCNSM)" không số được tính là n = 1); bắt buộc lý do | Vui lòng nhập lý do điều chỉnh. |
| BR-34 | % CK/PP: 0 < % < 100; bắt buộc lý do và đơn hàng; chỉ tạo cho bản NSM đã có dòng Thường | % chiết khấu / phụ phí phải lớn hơn 0 và nhỏ hơn 100. / Vui lòng nhập lý do và đơn hàng cụ thể. |
| BR-35 | Chỉ xoá được dòng CK/PP chưa có mã kế toán; không xoá được dòng Thường, Thí nghiệm | Dòng <mã dòng> đã có mã kế toán, không xoá được. |
| BR-36 | Tính lại toàn bộ một xưởng: với mọi bản NSM trạng thái Đã tính giá, Có mã kế toán, Chưa tính được (kể cả đã khoá): tính lại theo dữ liệu hiện tại (BR-14..BR-20); đạt → cập nhật dòng Thường, TN, CK/PP, chi tiết, `effective_date` = ngày hiệu lực, trạng thái Đã tính giá / Có mã kế toán; không đạt → Chưa tính được (giữ giá cũ). Mỗi dòng giá có Tổng thay đổi > 0 được ghi lịch sử (4.15) với batch_id. Tạo một bản ghi 4.16 | - |
| BR-37 | Sợi so sánh cho mã X: trong các bản NSM gốc và ĐCNSM cùng xưởng, khác X, trạng thái Đã tính giá / Có mã kế toán, cùng công nghệ: ưu tiên cùng `loss_group_key`, nếu không có thì cùng `yarn_group`; trong nhóm đó chọn chi số gần chi số của X nhất (bằng nhau thì chọn mã tính giá lần cuối gần nhất). Không có → không có sợi so sánh. Khi so sánh / tự điền, NSM chải thô được ghép theo cặp (dây chuyền, nguyên liệu) | Chưa có sợi cùng nhóm để tự điền. Vui lòng nhập NSM. |
| BR-38 | Cảnh báo NSM: nếu có sợi so sánh, với mọi công đoạn có `varies_with_count` = Không (trừ F), NSM của X khác NSM của sợi so sánh (dây chuyền chải thô: so theo cặp dây chuyền + nguyên liệu) → cảnh báo liệt kê các công đoạn đó; phải nhập `nsm_warning_reason` mới lưu được. Công đoạn Thô, Con, Ống, MVS không cảnh báo | NSM khác sợi cùng nhóm (<mã so sánh>) ở công đoạn: <danh sách>. Vui lòng nhập lý do trước khi lưu. |
| BR-39 | Kiểm tra giá bất thường: xét dòng Thường của các bản NSM GỐC trạng thái Đã tính giá / Có mã kế toán; gom theo (xưởng, công nghệ, nhóm sợi, nhóm tiêu hao); trong mỗi nhóm sắp theo chi số tăng dần (bằng nhau: theo mã); với mỗi cặp liền nhau (trước, sau): cùng chi số mà Tổng khác nhau (lệch > 1 VND/kg) → sai "Cùng chi số nhưng khác giá"; chi số sau lớn hơn mà Tổng sau ≤ Tổng trước → sai "Chi số cao hơn nhưng giá không cao hơn" | - |
| BR-40 | Khi thêm nhóm tiêu hao mới (UC-11, UC-12): tự tính lại các bản NSM "Chưa tính được" cùng xưởng có `loss_group_key` = nhóm mới (không tạo bản ghi 4.16; lịch sử event "Tính lần đầu" hoặc "Sửa tiêu hao") | - |
| BR-41 | File tải lên: .xlsx / .xlsm / .xls, ≤ 60 MB, mỗi sheet ≤ 10.000 dòng dữ liệu | File phải là .xlsx, .xlsm hoặc .xls, không quá 60 MB và mỗi sheet không quá 10.000 dòng. |
| BR-42 | Đọc sheet "2. Input tieu hao": group_key trùng trong file → mọi dòng trùng bị loại ("Nhóm '<nhóm>' bị trùng trong file."). S4: gộp các cột C3.1 / C3.2 / C3.3 theo BR-59 trước khi xử lý; dòng có ít nhất một ô tên thành phần → Thứ cấp, thành phần = nhóm sơ cấp có `material_tech_key` bằng tên đó (không có → loại dòng "Không tìm thấy thành phần '<tên>'."), tỷ lệ lấy từ cột tỷ lệ tương ứng, tiêu hao do app tính (BR-26); dòng không có thành phần → Sơ cấp, tiêu hao lấy từ các cột công đoạn. S1: dòng có ít nhất một ô tiêu hao là công thức → "Nhập từ file - chưa khai báo thành phần", tiêu hao = giá trị đã lưu của ô; ngược lại → Sơ cấp. Nhóm đã có trong app: cập nhật theo quyền BR-24 (không đủ quyền → loại dòng với thông báo BR-24) | - |
| BR-43 | Mỗi dòng lỗi được liệt kê với: sheet, số dòng Excel, mã / nhóm, lý do; dòng hợp lệ vẫn được lưu | - |
| BR-44 | Đọc sheet "1. Input NSM": mã chuẩn hoá = bỏ khoảng trắng quanh "-" ("S4 - 586" → "S4-586"), hậu tố "(ĐCNSM…)" chuẩn hoá thành " (ĐCNSMn)" (không số → n = 1) và tạo bản ĐCNSM trỏ về mã gốc; mã trống → cấp mã mới theo BR-05; mã đã có trong app → cập nhật tên, thành phần nguyên liệu (BR-58), NSM, đóng gói nếu bản chưa khoá (đã khoá → loại dòng với thông báo BR-32); mã chưa có → tạo mới với mã đó. Mã trùng trong file → mọi dòng trùng bị loại. Tên không hợp lệ (BR-01) → loại dòng. Thiếu đóng gói / thiếu tiêu hao → vẫn tạo, trạng thái "Chưa tính được" (BR-16). Sheet "4. Bang gia da tinh": mã kế toán không trống → gán cho dòng Thường của mã đó (bản bị khoá); mã tính giá không dạng "<xưởng>-N" và không có ở sheet NSM → loại dòng "Không có dữ liệu NSM cho mã '<mã>'."; mã tính giá dạng mã kế toán (không theo "<xưởng>-N") có ở sheet NSM → giữ làm mã tính giá, đồng thời điền vào mã kế toán nếu cột mã kế toán trống; "Ngày tính giá" → `first_priced_at` (không đọc được → để trống). Tên trùng trong dữ liệu cũ không bị chặn | - |
| BR-45 | Quyền theo sheet khi tải file: Phòng SO được mọi sheet và cả hai loại tải; Xưởng chỉ được "Cập nhật hàng loạt" với sheet "1. Input NSM" và "2. Input tieu hao" của xưởng mình; "Chuyển dữ liệu ban đầu" chỉ Phòng SO | Sheet '<sheet>' chỉ Phòng SO được cập nhật, đã bỏ qua. |
| BR-46 | Thay bằng đăng nhập của ứng dụng (2026-10-13): mỗi người dùng app bằng tài khoản riêng; chức năng không còn khối chọn nhóm / nhập mã / chọn tên. Mã quy tắc giữ trống | - |
| BR-47 | Quyền theo vai trò: tài khoản làm được một thao tác khi có ít nhất một vai trò cho phép thao tác đó. Sales → UC-15, UC-16, UC-17. Xưởng (XS1, XS4) → UC-11, UC-12, UC-13, UC-14, UC-18, UC-20, UC-21, UC-23, UC-24, UC-25, UC-26, UC-28, UC-34 (theo BR-45), UC-45 (theo BR-69). Kế toán → UC-28. Phòng SO → mọi UC thay đổi dữ liệu. Quản trị viên làm như Phòng SO. Tài khoản không có vai trò nào của chức năng chỉ xem được | Tài khoản của bạn chưa có vai trò cho thao tác '<thao tác>'. Hãy nhờ quản trị viên cấp vai trò ở trang /admin. |
| BR-48 | Vai trò Xưởng S1 / Xưởng S4 chỉ thao tác trên dữ liệu có `factory_code` bằng xưởng của vai trò: thao tác chỉ được phép khi có ít nhất một vai trò cho phép thao tác đó mà đúng xưởng (Sales, Kế toán, Phòng SO không giới hạn xưởng) | Bạn chỉ được thao tác dữ liệu của xưởng <xưởng>. |
| BR-49 | Mọi thao tác làm thay đổi dữ liệu ghi một dòng nhật ký (4.19): lúc, tài khoản đăng nhập (tên đăng nhập + họ tên), thao tác, đối tượng, nội dung trước → sau, lý do. Các cột "người làm" khác (người tạo, người xử lý...) ghi họ tên của tài khoản. Khi không có tài khoản (chạy bằng mã hệ thống) ghi "system" / "Hệ thống" | - |
| BR-50 | Cấu hình công đoạn: stage_code và sequence duy nhất trong xưởng; đúng một công đoạn `is_packaging` = Có; `cumulative_stages` chỉ gồm mã công đoạn có của xưởng và có `sequence` lớn hơn; `blend_slot` "Tỷ lệ dây chuyền X" với X là dây chuyền chải thô của xưởng; dây chuyền chải thô có `max_passes` từ 1 đến 3. Không xoá công đoạn đang có NSM hoặc tiêu hao khác 0 (chỉ đổi tên / cấu hình) | Cấu hình công đoạn không hợp lệ: <chi tiết>. |
| BR-51 | Phiên bản định mức mới phải có đủ 5 khoản ≥ 0 cho mọi công đoạn không phải đóng gói và mọi loại đóng gói đang hoạt động; bắt buộc ngày hiệu lực và lý do | Thiếu định mức cho: <danh sách mã>. / Vui lòng chọn ngày hiệu lực và nhập lý do. |
| BR-52 | Mã loại đóng gói duy nhất trong xưởng; phút/kg > 0; chỉ loại đang hoạt động và đã có định mức mới hiện cho Sales chọn | Mã đóng gói '<mã>' đã có ở xưởng <xưởng>. / Phút/kg phải lớn hơn 0. |
| BR-53 | Chỉ số dashboard trong khoảng ngày [từ, đến] và xưởng chọn: (1) Số sợi báo giá = số bản NSM GỐC có `first_priced_at` trong khoảng; (2) Số sợi có đơn hàng = trong (1), số bản có ít nhất một dòng giá có mã kế toán; tỷ lệ = (2) ÷ (1) × 100%; (3) Số yêu cầu báo giá mới = số mã origin "Yêu cầu Sales" có `requested_at` trong khoảng (mọi trạng thái); (4) Khả năng đáp ứng = số yêu cầu của (3) đã được xưởng lưu NSM (trạng thái Đã tính giá, Có mã kế toán, Chưa tính được) ÷ (số đó + số yêu cầu của (3) bị Từ chối) × 100% (không có yêu cầu đã xử lý → hiển thị "-"); (5) Số yêu cầu đang chờ xưởng xem (hiện tại); (6) Lần tính lại gần nhất trong khoảng: số dòng tăng / giảm, chênh lệch % trung bình = trung bình của (Tổng sau − Tổng trước) ÷ Tổng trước × 100% các dòng Thường thay đổi | - |
| BR-54 | NSM bất thường: xét bản NSM gốc và ĐCNSM trạng thái Đã tính giá / Có mã kế toán; gom theo (xưởng, công nghệ, nhóm tiêu hao), chỉ nhóm có ≥ 2 mã; với mỗi công đoạn có `varies_with_count` = Không (dây chuyền chải thô: theo cặp dây chuyền + nguyên liệu): giá trị phổ biến = giá trị NSM xuất hiện nhiều nhất (bằng nhau: giá trị nhỏ nhất); mọi mã có NSM khác giá trị phổ biến được liệt kê | - |
| BR-55 | Đối chiếu giá cũ: chênh lệch = Tổng app − Tổng cũ; "khớp" nếu |chênh lệch| ≤ 1 VND/kg; chênh lệch % = chênh lệch ÷ Tổng cũ × 100% (Tổng cũ = 0 → "-") | - |
| BR-56 | Thành phần nguyên liệu của sợi: mỗi dây chuyền chải thô có tối đa `max_passes` thành phần (S4 C1: 1; S4 C2, C3 và S1 C1, C2: 3); lượt = thứ tự của thành phần trong các thành phần cùng dây chuyền (1, 2, 3), app tự đánh lại khi thêm / xoá / đổi dây chuyền; `material_label` không trùng trong cùng sợi | <Dây chuyền> chỉ chạy tối đa <n> nguyên liệu trong một sợi. / Nguyên liệu '<nguyên liệu>' bị nhập 2 lần. |
| BR-57 | Nếu nhóm tiêu hao của sợi có thành phần (Thứ cấp) thì `material_label` của mỗi thành phần có dây chuyền chải thô phải là `material_tech_key` của một thành phần của nhóm; nhóm Sơ cấp: chỉ một thành phần có dây chuyền chải thô, là nguyên liệu của nhóm; nhóm chưa có hoặc "Nhập từ file - chưa khai báo thành phần": tên nguyên liệu nhập tự do | Nguyên liệu '<nguyên liệu>' không có trong nhóm tiêu hao '<nhóm>'. Vui lòng chọn nguyên liệu của nhóm. |
| BR-58 | Tiêu hao của một lượt chải thô (thành phần M chạy dây chuyền X): nếu M là thành phần của nhóm tiêu hao của sợi → tiêu hao của nhóm thành phần M tại X (khi `secondary_method` của X = Cộng thẳng) hoặc tiêu hao đó × tỷ lệ của M trong nhóm (khi = Bình quân); nếu nhóm Sơ cấp hoặc nhóm không có thành phần → tiêu hao của nhóm tại X, chỉ dùng được khi X có đúng 1 lượt (có từ 2 lượt → "Chưa tính được", BR-16). "Tiêu hao tại X" ở hai trường hợp trên được lấy theo BR-64 (khi X chưa khai báo thì dùng tiêu hao của dây chuyền tương đương, rồi áp dụng `secondary_method` của X). Ngoài BR-64, không tự điều chỉnh tiêu hao đã khai báo. Nhập NSM từ file cũ: S4 ô Cotton + C1 → thành phần dây chuyền C1; ô PE + C2 → C2 lượt 1; ô Other - C3.k + C3.k → C3 lượt k; S1 ô PE + C1 → C1 lượt 1, ô Viscose/other + C2 → C2 lượt 1, ô Cotton → "Không chải thô"; tên nguyên liệu = `material_tech_key` của thành phần nhóm tiêu hao ở đúng ô đó (S4, nhóm Thứ cấp), nguyên liệu của nhóm (nhóm Sơ cấp), ngược lại = tên ô ("PE", "Other - C3.1", "Cotton"...); ô tỷ lệ = 0 và NSM = 0 thì không tạo thành phần; mã có REMARK "Có thành phần chỉ sửa được trên màn hình" giữ nguyên thành phần | - |
| BR-59 | Nhập tiêu hao S4 từ file cũ: tiêu hao C3 của một dòng = số khác 0 nhỏ nhất trong 3 cột C3.1 / C3.2 / C3.3 (không có → 0). Các dòng cùng `group_key` mà mọi cột khác giống nhau, chỉ khác các cột C3.x → gộp thành một nhóm, tiêu hao C3 = số khác 0 nhỏ nhất của các dòng; các dòng trùng `group_key` khác còn lại vẫn bị loại theo BR-42. Không tự điều chỉnh tiêu hao C2 | - |
| BR-60 | Mỗi xưởng có tối đa một loại đóng gói mặc định, phải là loại đang hoạt động; khi Sales chọn xưởng ở Screen 2, ô Loại đóng gói tự điền loại mặc định nếu loại đó chọn được (BR-52), ngược lại để trống; Sales đổi được; loại mặc định không tự gán cho mã nhập từ file thiếu đóng gói | Mỗi xưởng chỉ được chọn một loại đóng gói mặc định. |
| BR-61 | Dữ liệu chép từ app cũ (5.6) được đọc nguyên trạng: mọi mã, dòng giá, số tiền, trạng thái, mã kế toán, lịch sử, lần tính lại, lần nhập file, nhật ký giữ nguyên (dòng cũ có nhóm + tên được đọc thành họ tên "<nhóm> - <tên>", tên đăng nhập để trống), không tính lại giá. Dữ liệu lưu theo cách trước 2026-09-28 được chuyển khi đọc: công đoạn C3.1 / C3.2 / C3.3 của S4 gộp thành C3 (tối đa 3 lượt); tỷ lệ pha và NSM theo ô → thành phần nguyên liệu theo cách ghép ô của BR-58; tiêu hao C3 của nhóm = số khác 0 nhỏ nhất trong C3.1 / C3.2 / C3.3 (BR-59). Giá sau khi chuyển phải bằng giá đang lưu (ví dụ S4-2017 = 19.777,8356 VND/kg). Một file dữ liệu không đọc được → màn hình hiện thông báo, các dữ liệu khác vẫn dùng được | Không đọc được dữ liệu '<tên file>'. Vui lòng chép lại file này từ app cũ (thư mục data\yarn_costing). |
| BR-62 | Loại đóng gói "đang được dùng" = có ít nhất một bản NSM của xưởng (trạng thái khác Đã huỷ, Từ chối) có `packaging_code` bằng mã loại. Khi lưu bảng Đóng gói (UC-05): chỉ tính lại toàn bộ xưởng khi ít nhất một loại đang được dùng có `minutes_per_kg` khác giá trị đang lưu; ngày hiệu lực và lý do chỉ bắt buộc trong trường hợp này. Hộp xác nhận: có tính lại → "Phút/kg của loại <danh sách mã> (đang có mã sợi dùng) thay đổi. App sẽ tính lại toàn bộ giá xưởng <xưởng> từ ngày <dd/mm/yyyy>."; không tính lại (chỉ đổi loại mặc định, tên, khối lượng, số công, còn hoạt động, thêm loại mới, đổi phút/kg của loại chưa có mã dùng) → "Giá các mã không thay đổi." | Vui lòng chọn ngày hiệu lực và nhập lý do. |
| BR-63 | Nút "Gửi yêu cầu" (Screen 2) bị khoá khi có ít nhất một lý do dưới đây; mọi lý do đang đúng hiện ngay cạnh nút, theo thứ tự: (1) tài khoản không có vai trò Sales hoặc Phòng SO (BR-47; quản trị viên được phép) → câu (a); (2) xưởng đang chọn không có loại đóng gói chọn được (BR-52) → câu (b). Hết lý do → nút bấm được | (a) Tài khoản của bạn chưa có vai trò cho thao tác này (quản trị viên cấp ở trang /admin). (b) Xưởng <xưởng> chưa có loại đóng gói chọn được. Vui lòng báo Phòng SO khai báo loại đóng gói và định mức. |
| BR-64 | Dây chuyền tương đương (cố định theo xưởng): S4 C2 ↔ C3; S1 C1 ↔ C2; S4 C1 không có. Khi tính tiêu hao của một lượt chải thô (nguyên liệu chạy dây chuyền X, BR-58): lấy tiêu hao khai báo tại X của nhóm liên quan (nhóm thành phần của nguyên liệu, hoặc nhóm Sơ cấp / nhóm không có thành phần của sợi); nếu tiêu hao tại X = 0 hoặc để trống và X có dây chuyền tương đương Y với tiêu hao tại Y > 0 → dùng tiêu hao tại Y, ghi `loss_source_stage` = Y (4.14). Nếu tiêu hao tại X > 0 thì luôn dùng số của X, kể cả khi Y có số khác. Nếu cả X và Y đều = 0 → "Chưa tính được" với câu thứ hai của BR-16. Chỉ áp dụng cho tiêu hao của lượt chải thô khi tính giá (và kiểm tra khớp BR-15); không đổi số tiêu hao đã khai báo, không đổi bảng "Tiêu hao tính ra" của nhóm sợi pha (BR-26), không đổi so sánh NSM (BR-37, BR-38, BR-54) | - |
| BR-65 | Tính lại các mã chưa tính được của một xưởng (UC-43): xét mọi bản NSM của xưởng trạng thái "Chưa tính được" (kể cả bản đã khoá hoặc đang giữ mã kế toán chờ); tính lại theo dữ liệu hiện tại (BR-14..BR-20, BR-64); đạt → tạo / cập nhật dòng Thường, Thí nghiệm, CK/PP, chi tiết công đoạn, `effective_date` = ngày hiệu lực, `first_priced_at` = ngày hiệu lực nếu chưa có, trạng thái "Đã tính giá" (hoặc "Có mã kế toán" nếu bản có mã kế toán), ghi lịch sử giá event "Tính lại mã chưa tính được"; không đạt → giữ "Chưa tính được", cập nhật lại `status_reasons`. Bắt buộc ngày hiệu lực và lý do; tạo một bản ghi 4.16 trigger "Tính lại mã chưa tính được". Các bản NSM trạng thái khác không bị tính lại | Xưởng <xưởng> không có mã nào đang 'Chưa tính được'. / Vui lòng chọn ngày hiệu lực và nhập lý do. |
| BR-66 | Đọc file khai báo thành phần (5.7), từng dòng: tên nhóm trùng nhau trong file (so khớp như `group_key`) → loại mọi dòng trùng ("Nhóm '<nhóm>' bị trùng trong file."); mỗi cặp Thành phần k / Tỷ lệ k: có tên mà trống tỷ lệ hoặc có tỷ lệ mà trống tên → loại dòng ("Thành phần <k>: cần cả tên và tỷ lệ."); tỷ lệ không phải số hoặc ≤ 0 hoặc > 100 → loại ("Tỷ lệ <k> phải là số % lớn hơn 0 và không quá 100."); tên thành phần không khớp `group_key` hoặc `material_tech_key` của nhóm nào của xưởng → loại ("Không tìm thấy nhóm thành phần '<tên>' ở xưởng <xưởng>."); cùng một thành phần ghi 2 lần → loại ("Thành phần '<tên>' bị ghi 2 lần."); nhóm chưa có trong app mà thiếu / sai Công nghệ → loại ("Nhóm mới '<nhóm>' cần cột Công nghệ là Ring hoặc MVS."); sau đó kiểm tra BR-27 trên toàn bộ các nhóm sau khi khai báo (1-5 thành phần, tổng 100% ± 0,01%, không dùng chính nó, không tạo vòng - kể cả vòng giữa các dòng trong cùng file) → loại dòng với thông báo BR-27 | (các câu trong quy tắc) |
| BR-67 | Lưu một nhóm hợp lệ từ file khai báo thành phần: nhóm đã có (mọi loại: Sơ cấp, Nhập từ file - chưa khai báo thành phần, Thứ cấp) → `level` = Thứ cấp, `components` = các thành phần trong file (thay toàn bộ thành phần cũ), `losses` = tính theo BR-26 từ thành phần (thay toàn bộ tiêu hao cũ, kể cả công đoạn thành phần không có tiêu hao → 0); giữ `group_key`, `yarn_group_label`, `material`, `technology`. Nhóm chưa có → tạo nhóm Thứ cấp mới: `group_key` = tên đã chuẩn hoá, `yarn_group_label` = tên như trong file, `material` trống, `technology` = cột Công nghệ. Ghi `updated_by`, `updated_at` | - |
| BR-68 | Đổi thành phần của mã sợi khi nhóm tiêu hao của mã được khai báo lại bằng file (BR-67): với mỗi thành phần của mã có dây chuyền chải thô X: ứng viên = các thành phần của nhóm mà nhóm thành phần có tiêu hao chải thô > 0 ở X hoặc ở dây chuyền tương đương của X (BR-64); đúng 1 ứng viên → `material_label` = `material_tech_key` của ứng viên; nhiều ứng viên → chọn ứng viên có tỷ lệ trong nhóm bằng tỷ lệ của thành phần mã (sai lệch ≤ 0,01%), còn lại nhiều hơn 1 hoặc không có → không ghép được. Không đổi tỷ lệ, dây chuyền, NSM, lượt; thành phần "Không chải thô" giữ nguyên tên. Áp dụng cả mã đã khoá (chỉ đổi tên nguyên liệu). Mã có thành phần không ghép được → sau khi tính lại là "Chưa tính được" với lý do "Không ghép được thành phần '<tên>' (<dây chuyền>) của mã với thành phần của nhóm tiêu hao '<nhóm>'. Vui lòng chọn lại nguyên liệu ở màn Nhập NSM." và có tên trong file kết quả | Không ghép được thành phần '<tên>' (<dây chuyền>) của mã với thành phần của nhóm tiêu hao '<nhóm>'. Vui lòng chọn lại nguyên liệu ở màn Nhập NSM. |
| BR-69 | Quyền tải file khai báo thành phần: vai trò Xưởng chỉ tải cho xưởng mình, và chỉ được đổi nhóm không khoá (BR-24; dòng của nhóm đang khoá bị loại với thông báo BR-24) và tạo nhóm mới; Phòng SO tải cho cả hai xưởng, đổi được mọi nhóm kể cả nhóm đang khoá; Kế toán, Sales không được tải | Nhóm tiêu hao '<nhóm>' đang được dùng cho sợi đã có mã kế toán (<tối đa 5 mã>). Chỉ Phòng SO được sửa. / Tài khoản của bạn chưa có vai trò cho thao tác '<thao tác>'. Hãy nhờ quản trị viên cấp vai trò ở trang /admin. |

## 8. Screens (Màn hình)

### Giao diện đã chốt (UI concept)
> Chốt lại ở app mới ngày 2026-09-29 (Prompt 2): câu 2-7 giữ đề xuất (giống app cũ); câu 1 - menu **phân theo vai trò,
> có nút mở rộng / thu gọn**.

- **Menu (chốt 2026-09-29):**
  - Menu bên trái (khung sườn, cập nhật 2026-10-13 theo YC-01): khối "🧵 Tính giá sợi" bấm mũi tên để mở / thu gọn; bên trong
    8 màn hình chia theo vai trò: **Dùng chung** (Bảng giá đã tính - trang chính, Dashboard kiểm soát) → **Sales** (Yêu cầu
    tính giá) → **Xưởng sợi** (Nhập NSM & tính giá, Tiêu hao) → **Phòng SO** (Dữ liệu nền & định mức, Nhập dữ liệu từ Excel,
    Nhật ký thao tác). Kế toán dùng Bảng giá đã tính (nhập mã kế toán). Người dùng chỉ thấy những màn hình được cấp quyền.
  - Khối "📂 Menu theo vai trò" ở đầu mỗi màn hình (2026-09-29) đã bỏ vì menu bên trái đã gấp / mở theo nhóm.
- **Vai trò (2026-10-13):** chức năng không có khối chọn người riêng; ai thao tác là tài khoản đang đăng nhập. Nút làm thay đổi dữ liệu bị tắt kèm chú thích khi tài khoản không có vai trò phù hợp (BR-47, BR-48).
- **Bảng danh sách** (bảng giá, yêu cầu, mã cần xử lý, nhóm tiêu hao, lần nhập file, lần tính lại, nhật ký): chỉ xem (lọc,
  sắp xếp, tìm, tải) + chọn 1 dòng; chọn dòng xong mới hiện khối chi tiết / thao tác của dòng đó bên dưới bảng.
- **Screen 1 - Bảng giá đã tính:** bộ lọc ở trên → dòng thông tin tỷ giá đang dùng + hệ số TN → 4 ô số liệu (Tổng dòng, Có
  mã kế toán, Chưa tính được, Chờ xưởng xem) → bảng chọn dòng hiện **đầy đủ mọi cột** như sheet `Bang gia` (5.4), gồm cả cột
  "Thành phần" dạng chữ (cập nhật 2026-09-28) → nút
  "Xuất Excel", "Kiểm tra giá bất thường" (kết quả hiện dưới bảng) → khối dòng đang chọn: thông tin mã, bảng chi tiết công
  đoạn, lịch sử giá, ô Mã kế toán + "Lưu mã kế toán", "Thêm CK/PP" (form), "Xoá dòng CK/PP", "Mở trong Nhập NSM".
- **Screen 2 - Yêu cầu tính giá:** form tạo (Xưởng, Tên sợi, Loại đóng gói - chọn xưởng thì tự điền loại mặc định, đổi được) + dòng "App nhận ra" (nhóm sợi, chi số, công
  nghệ, nhóm tiêu hao, cảnh báo nhóm chưa có) + "Gửi yêu cầu" → bộ lọc → bảng yêu cầu chọn dòng → khối sửa (Tên sợi, Loại
  đóng gói) với "Lưu sửa đổi", "Huỷ yêu cầu".
- **Screen 3 - Nhập NSM & tính giá:** chọn xưởng → ô số liệu theo trạng thái → bảng mã cần xử lý (chọn dòng) → khối mã
  đang mở: thông tin mã; Cách nhập (Tự nhập / Tự điền) + "Lấy NSM từ sợi cùng nhóm"; (cập nhật 2026-09-28) ① **bảng thành
  phần nguyên liệu sửa trong ô**, thêm / xoá dòng (cột: Nguyên liệu - danh sách chọn các nguyên liệu của nhóm tiêu hao, gõ tay
  khi nhóm chưa có thành phần; Tỷ lệ %; Dây chuyền - danh sách chọn dây chuyền chải thô của xưởng + "Không chải thô"; Lượt -
  chỉ xem, app đánh sau khi kiểm tra; NSM chải thô; NSM sợi so sánh - chỉ xem) ở trên, ② **bảng NSM các công đoạn khác sửa
  trong ô** (cột: Công đoạn, Tên công đoạn, NSM (kg/giờ) - sửa được, NSM sợi so sánh - chỉ xem) ở dưới; ô Lý do khác
  sợi cùng nhóm (hiện khi có cảnh báo); nút "Kiểm tra và xem giá", "Lưu NSM và giá", "Tạo bản ĐCNSM" (chuyển form sang chế độ
  ĐCNSM có ô Lý do điều chỉnh và nút "Lưu bản ĐCNSM"), ô Lý do từ chối + "Từ chối", "Khai báo tiêu hao cho nhóm này" → khối
  kết quả: kiểm tra khớp, bảng chi tiết công đoạn (có cột Nguyên liệu, Lượt), 5 khoản, Tổng VND/kg, USD/kg, giá thí nghiệm.
- **Screen 4 - Tiêu hao:** bộ lọc → bảng nhóm (chọn dòng) → khối nhóm: Sơ cấp / Nhập từ file: bảng tiêu hao sửa trong ô
  (Công đoạn, Tiêu hao %); Thứ cấp: bảng thành phần sửa trong ô (Nhóm thành phần - chọn từ danh sách, Tỷ lệ %) + bảng tiêu hao
  tính ra (chỉ xem); ô Lý do; danh sách mã đang dùng; nút "Thêm nhóm sơ cấp", "Thêm nhóm sợi pha", "Xem tiêu hao tính ra",
  "Lưu nhóm", "Lưu thay đổi", "Xoá nhóm".
- **Screen 5 - Dữ liệu nền & định mức:** chọn xưởng → các thẻ (tab): Công đoạn | Định mức | Đóng gói | Hồi phế | Quy trình |
  Tỷ giá & hệ số TN | Các lần tính lại. Thẻ Đóng gói có thêm cột ô tick "Mặc định" ngay sau cột Mã (cập nhật 2026-09-28). Mỗi
  thẻ dữ liệu nền là **bảng sửa trong ô** (thêm / xoá dòng ngay trên bảng) + ô Ngày
  hiệu lực + ô Lý do + nút "Lưu … và tính lại" (Quy trình: "Lưu quy trình", không có ngày / lý do). Thẻ Định mức có danh sách
  phiên bản (chọn để xem). Thẻ Tỷ giá: bảng tỷ giá chỉ xem + form thêm; hệ số TN: ô số + ngày + lý do + "Lưu hệ số". Thẻ Các
  lần tính lại: bảng chọn dòng → bảng chênh lệch + "Xuất Excel".
- **Screen 6 - Nhập dữ liệu từ Excel:** Xưởng, Loại tải, Ngày chốt, "Tải file mẫu" → ô tải file + "Kiểm tra file" → ô số liệu
  và bảng kết quả từng sheet (đọc / tạo / cập nhật / bị loại) + bảng dòng bị loại có công tắc "Chỉ hiện dòng lỗi" → "Lưu N dòng
  hợp lệ", "Tải kết quả nhập file" → bảng các lần nhập (chọn dòng) → ô số liệu đối chiếu + bảng đối chiếu giá cũ + công tắc
  "Chỉ hiện mã lệch trên 1 VND/kg" + "Xuất Excel".
- **Screen 7 - Dashboard kiểm soát:** Xưởng (S1 / S4 / Cả hai), Từ ngày - Đến ngày → 5 ô số liệu (Sợi báo giá, Sợi có đơn
  hàng + tỷ lệ %, Yêu cầu mới, Khả năng đáp ứng %, Đang chờ xưởng xem) → biểu đồ cột "Yêu cầu mới theo tuần" và biểu đồ đường
  "Khả năng đáp ứng theo tuần" → số dòng giá theo trạng thái (ô số liệu) → khối chênh lệch lần tính lại gần nhất + nút xem chi
  tiết → bảng "Sai lệch giá" → bảng "NSM bất thường".
- **Screen 8 - Nhật ký thao tác:** bộ lọc (khoảng ngày, tài khoản, thao tác, từ khoá) → bảng nhật ký (Lúc, Tài khoản, Họ tên, Thao tác,
  Đối tượng, Nội dung, Lý do).
- **Bổ sung 2026-09-29 (BR-64, UC-43)** - theo đúng cách giao diện đã chốt, không hỏi lại: bảng chi tiết công đoạn (Screen 1
  khối dòng đang chọn, Screen 3 khối kết quả) có thêm cột cuối "Ghi chú tiêu hao"; Screen 5 thẻ "Các lần tính lại" có khối "🔄
  Tính lại các mã chưa tính được" ở đầu thẻ (ô Ngày hiệu lực, ô Lý do, nút "Tính lại các mã chưa tính được" có hộp xác nhận), bên
  dưới là bảng các lần tính lại như cũ.
- **Bổ sung 2026-09-29 (UC-44, UC-45)** - theo cách giao diện đã chốt, không hỏi lại: Screen 6 ô "Loại tải" có thêm lựa chọn
  "Khai báo thành phần sợi pha"; khi chọn: ô ngày đổi tên "Ngày hiệu lực", nút "Tải file mẫu" tải mẫu 5.7; khối "🧩 Khai báo thành
  phần sợi pha" (ô Lý do, ô tải file, nút "Kiểm tra file") → khối kết quả (5 ô số liệu; bảng nhóm hợp lệ chỉ xem với cột tiêu hao
  cũ / mới từng công đoạn; bảng dòng bị loại; bảng mã không ghép được) → nút "Lưu N nhóm hợp lệ" (hộp xác nhận) → khối kết quả lần
  lưu với nút "Xem chênh lệch" và "Tải kết quả nhập file"; bên dưới là bảng các lần nhập như cũ.
- **Ô số liệu:** Screen 1, 3, 6, 7. **Biểu đồ:** chỉ ở Screen 7.
- **Hộp thoại xác nhận** trước khi: Huỷ yêu cầu, Từ chối, Xoá nhóm tiêu hao, Xoá dòng CK/PP, "Lưu đóng gói" (nội dung theo BR-62), mọi nút "… và tính lại" (Screen
  5), "Lưu hệ số", "Lưu thay đổi" nhóm tiêu hao (có tính lại), "Lưu N dòng hợp lệ". Không hỏi lại khi: Gửi yêu cầu, Lưu sửa
  đổi, Lưu NSM và giá, Lưu bản ĐCNSM, Lưu dòng CK/PP, Lưu mã kế toán, Lưu nhóm tiêu hao mới, Lưu quy trình, Thêm tỷ giá.

Mỗi màn hình lấy danh sách chọn từ dữ liệu tham chiếu (UC-38). Nút làm thay đổi dữ liệu bị tắt kèm chú thích khi tài khoản đăng nhập
không có vai trò phù hợp (BR-47, BR-48); phía xử lý vẫn kiểm tra lại ở mỗi thao tác.

### Screen 1: Bảng giá đã tính (landing page)
- **Purpose:** xem, lọc, xuất toàn bộ giá; nhập mã kế toán; tạo / xoá dòng CK/PP; xem chi tiết và lịch sử.
- **Information shown:** tỷ giá đang dùng (ngày áp dụng), hệ số thí nghiệm; ô số liệu: tổng số dòng, số dòng có mã kế toán,
  số mã "Chưa tính được", số yêu cầu "Chờ xưởng xem".
- **Inputs / filters:** Xưởng (S1 / S4 / Tất cả, mặc định Tất cả); Loại dòng (nhiều lựa chọn, mặc định tất cả); Trạng thái
  (nhiều lựa chọn); Công nghệ (Ring / MVS / Tất cả); Nhóm sợi (danh sách); Mã kế toán (Có / Chưa có / Tất cả); Ngày tính
  giá từ - đến (mặc định trống); Từ khoá (mã dòng, tên sợi, mã kế toán).
- **Table (UC-27):** cột như sheet `Bang gia` (5.4), sắp theo Xưởng, Mã gốc, Loại dòng (Thường, Thí nghiệm, CK, PP); rỗng: "Chưa có
  giá nào phù hợp bộ lọc."
- **Selected line panel:** chi tiết (UC-22; bảng chi tiết công đoạn có cột "Ghi chú tiêu hao" - BR-64); ô Mã kế toán + nút "Lưu mã kế toán" (UC-28); nút "Thêm CK/PP" (UC-25); nút "Xoá
  dòng CK/PP" (UC-26, chỉ hiện với dòng CK/PP); nút "Mở trong Nhập NSM" (sang Screen 3).
- **Buttons:** "Xuất Excel" → UC-29; "Kiểm tra giá bất thường" → UC-30 (hiện kết quả ngay dưới bảng).
- **After actions:** thông báo của UC; bảng tải lại, dòng vừa sửa vẫn được chọn.

### Screen 2: Yêu cầu tính giá
- **Purpose:** Sales tạo, sửa, huỷ yêu cầu và theo dõi trạng thái.
- **Inputs (tạo / sửa):** Xưởng (S1 / S4, bắt buộc); Tên sợi (chữ, bắt buộc); Loại đóng gói (danh sách loại chọn được của xưởng,
  bắt buộc; khi tạo mới: tự điền loại mặc định của xưởng - BR-60, đổi được). Khi gõ tên: hiện ngay (UC-40) nhóm sợi, chi số, công nghệ, nhóm tiêu hao app nhận ra và thông báo nếu nhóm tiêu hao
  chưa có ở xưởng.
- **Table:** danh sách yêu cầu (UC-19), mặc định lọc 30 ngày gần nhất, mới nhất trước; rỗng: "Chưa có yêu cầu nào."
- **Lý do khoá nút:** khi nút "Gửi yêu cầu" bị khoá, ngay cạnh nút hiện các lý do theo BR-63 (đúng câu thông báo) - UC-42.
- **Buttons:** "Gửi yêu cầu" → UC-15; "Lưu sửa đổi" → UC-16; "Huỷ yêu cầu" → UC-17 (chỉ bật với yêu cầu "Chờ xưởng xem").
- **After actions:** thông báo có mã mới; yêu cầu mới ở đầu danh sách.

### Screen 3: Nhập NSM & tính giá
- **Purpose:** xưởng xử lý yêu cầu, nhập NSM, xem kết quả tính, lưu giá, tạo ĐCNSM.
- **Information shown:** số yêu cầu mỗi trạng thái của xưởng chọn; danh sách mã (UC-19) mặc định lọc "Chờ xưởng xem" và "Chưa
  tính được", cũ nhất trước.
- **Inputs:** Xưởng; chọn một mã. Với mã đang mở: thông tin mã (tên, nhóm sợi, chi số, công nghệ, nhóm tiêu hao, đóng gói,
  trạng thái, khoá, lý do chưa tính được); Cách nhập (Tự điền / Tự nhập, mặc định Tự nhập); bảng thành phần nguyên liệu (Nguyên
  liệu, Tỷ lệ %, Dây chuyền chải thô, Lượt - app tự đánh, NSM chải thô, NSM của sợi so sánh; thêm / xoá dòng khi nhóm tiêu hao
  chưa có thành phần); NSM các công đoạn không phải chải thô theo BR-13 (kg/giờ), cạnh mỗi ô: NSM của sợi so sánh; ô Lý do khác sợi cùng nhóm (hiện khi có cảnh
  báo); ô Lý do từ chối.
- **Result block (sau "Kiểm tra và xem giá"):** kết quả kiểm tra khớp (đạt / danh sách lý do); bảng chi tiết công đoạn (4.14, có cột "Ghi chú tiêu hao" - BR-64);
  5 khoản, Tổng VND/kg, USD/kg, giá thí nghiệm.
- **Buttons:** "Lấy NSM từ sợi cùng nhóm" → UC-20; "Kiểm tra và xem giá" → UC-21 (không lưu); "Lưu NSM và giá" → UC-21; "Từ
  chối" → UC-18; "Lưu NSM và giá" trên mã đã có giá chưa khoá → UC-23; "Tạo bản ĐCNSM" → UC-24 (form chuyển sang chế độ ĐCNSM, có ô Lý do điều chỉnh, nút "Lưu bản ĐCNSM");
  "Khai báo tiêu hao cho nhóm này" (hiện khi thiếu nhóm tiêu hao) → mở Screen 4 với nhóm điền sẵn.
- **After actions:** thông báo của UC; mã chuyển trạng thái trong danh sách.

### Screen 4: Tiêu hao
- **Purpose:** tra cứu, khai báo, sửa, xoá nhóm tiêu hao.
- **Inputs / filters:** Xưởng; Loại (Sơ cấp / Thứ cấp / Nhập từ file / Tất cả); Từ khoá; Chỉ nhóm đang khoá (bật / tắt).
- **Table:** danh sách nhóm (UC-10); rỗng: "Chưa có nhóm tiêu hao nào."
- **Form nhóm:** Nhóm sợi, Nguyên liệu, Công nghệ; Sơ cấp / Nhập từ file: ô tiêu hao (%) cho từng công đoạn của xưởng; Thứ
  cấp: 1-5 dòng (Nhóm thành phần - chọn trong danh sách nhóm của xưởng, Tỷ lệ %), bảng tiêu hao tính ra (chỉ xem); Lý do
  (bắt buộc khi sửa); danh sách mã đang dùng nhóm và cảnh báo "Nhóm đang khoá" nếu có.
- **Buttons:** "Thêm nhóm sơ cấp" → UC-11; "Thêm nhóm sợi pha" → UC-12; "Xem tiêu hao tính ra" (UC-12, không lưu); "Lưu nhóm"
  → UC-11 / UC-12; "Lưu thay đổi" → UC-13; "Xoá nhóm" → UC-14.
- **After actions:** thông báo của UC kèm số mã đã tính lại.

### Screen 5: Dữ liệu nền & định mức (Phòng SO)
- **Purpose:** quản lý dữ liệu nền của từng xưởng và tham số chung.
- **Blocks (theo xưởng chọn):** Cấu hình công đoạn (bảng 4.4) → UC-03; Định mức chi phí/phút hiện tại (bảng 4.5.1, kèm phiên
  bản, ngày hiệu lực, người áp dụng) → UC-04; danh sách các phiên bản định mức (xem được phiên bản cũ); Loại đóng gói →
  UC-05 (có cột "Mặc định"); Hồi phế → UC-06; Quy trình công nghệ (bảng 4.8 + cột công đoạn nhận ra) → UC-07; Các lần tính lại → UC-36 / UC-37.
- **Blocks (chung):** Tỷ giá (danh sách + form thêm) → UC-08; Hệ số thí nghiệm → UC-09.
- **Inputs dùng chung cho mọi thay đổi có tính lại:** Ngày hiệu lực (ngày, mặc định hôm nay, bắt buộc); Lý do (chữ, bắt buộc).
- **Đóng gói:** ô Ngày hiệu lực và Lý do chỉ bắt buộc khi việc lưu có tính lại (BR-62); hộp xác nhận ghi đúng một trong hai
  câu của BR-62.
- **Buttons:** "Lưu cấu hình và tính lại" → UC-03; "Áp dụng định mức và tính lại toàn bộ" → UC-04; "Lưu đóng gói" → UC-05; "Lưu hồi phế và tính lại" → UC-06; "Lưu quy trình" → UC-07; "Thêm tỷ giá" → UC-08; "Lưu hệ số" → UC-09; "Tính lại các mã chưa
  tính được" (theo xưởng đang chọn, có ngày hiệu lực + lý do, hỏi xác nhận trước khi chạy) → UC-43.
- **After actions:** thông báo kèm số mã đã tính lại, nút "Xem chênh lệch" → UC-37.

### Screen 6: Nhập dữ liệu từ Excel
- **Purpose:** tải file mẫu, chuyển dữ liệu cũ, cập nhật hàng loạt, đối chiếu giá cũ.
- **Inputs:** Xưởng (bắt buộc); Loại tải (Chuyển dữ liệu ban đầu / Cập nhật hàng loạt / Khai báo thành phần sợi pha); Ngày chốt
  (ngày, mặc định hôm nay; với "Khai báo thành phần sợi pha" ô này là "Ngày hiệu lực") ; Lý do (chữ, chỉ hiện và bắt buộc với
  "Khai báo thành phần sợi pha"); ô tải file (.xlsx / .xlsm / .xls).
- **Result block:** mỗi sheet: số dòng đọc, tạo, cập nhật, bị loại; bảng dòng bị loại (Sheet, Dòng, Mã / nhóm, Lý do) với công
  tắc "Chỉ hiện dòng lỗi".
- **Khai báo thành phần sợi pha (UC-44, UC-45):** kết quả kiểm tra gồm ô số liệu (Số nhóm hợp lệ, Nhóm tạo mới, Dòng bị loại, Mã
  bị ảnh hưởng, Mã không ghép được thành phần); bảng nhóm hợp lệ (Nhóm, Loại cũ → Thứ cấp, Thành phần + tỷ lệ, tiêu hao cũ → mới
  từng công đoạn (%), Số mã bị ảnh hưởng); bảng dòng bị loại (Dòng, Nhóm, Lý do); bảng mã không ghép được (Mã, Tên sợi, Thành
  phần, Dây chuyền, Nhóm). Nút "Tải file mẫu" → UC-44; "Kiểm tra file" → UC-45 (không lưu); "Lưu N nhóm hợp lệ" → UC-45 (hỏi
  xác nhận); sau khi lưu: thông báo UC-45, nút "Xem chênh lệch" (UC-37), "Tải kết quả nhập file".
- **Buttons:** "Tải file mẫu" → UC-33; "Kiểm tra file" → UC-34 (không lưu); "Lưu N dòng hợp lệ" → UC-34; "Tải kết quả nhập
  file" (5.5); danh sách lần nhập file (UC-41) → chọn một lần → "Đối chiếu giá cũ" → UC-35, "Xuất Excel" đối chiếu.
- **After actions:** thông báo UC-34; lần nhập mới ở đầu danh sách.

### Screen 7: Dashboard kiểm soát
- **Purpose:** theo dõi hiệu quả báo giá và sai lệch.
- **Inputs:** Xưởng (S1 / S4 / Cả hai, mặc định Cả hai); Từ ngày - Đến ngày (mặc định ngày 1 tháng hiện tại → hôm nay).
- **Blocks (UC-32):** ô số liệu BR-53 (1)-(5); biểu đồ số yêu cầu mới theo tuần và khả năng đáp ứng theo tuần; số dòng giá theo trạng
  thái; chênh lệch lần tính lại gần nhất (BR-53 (6)) + nút xem chi tiết → UC-37; "Sai lệch giá" → UC-30; "NSM bất thường"
  → UC-31. Rỗng: "Không có dữ liệu trong khoảng ngày đã chọn."
- **Buttons:** không có thao tác thay đổi dữ liệu.

### Screen 8: Nhật ký thao tác
- **Purpose:** mọi người xem ai (tài khoản đăng nhập) đã làm thao tác nào, lúc nào.
- **Inputs / filters:** Từ ngày - Đến ngày (mặc định 30 ngày gần nhất); Tài khoản và Thao tác (danh sách giá trị có trong khoảng ngày,
  mặc định Tất cả); Từ khoá.
- **Table (UC-02):** Lúc, Tài khoản, Họ tên, Thao tác, Đối tượng, Nội dung, Lý do; mới nhất trước; rỗng: "Chưa có thao tác nào
  trong khoảng thời gian này."
- **Buttons:** không có thao tác thay đổi dữ liệu.

## 9. Acceptance criteria (Tiêu chí nghiệm thu)
- [ ] AC-01 (UC-34, BR-20): Cho trước file S4 hiện tại được chuyển dữ liệu ban đầu, khi app tính giá mã S4-2017 thì Tổng =
  19.778 VND/kg (19.777,8356) và USD = 0,7911 với tỷ giá 25.000; chi tiết C1: thời gian 0,9473 phút/kg, lũy kế 25,96%, chi
  phí 3.248 VND/kg.
- [ ] AC-02 (UC-35, BR-55): Sau khi chuyển dữ liệu S4 và S1, màn đối chiếu hiện số mã khớp / lệch / chưa tính được và liệt kê
  từng mã lệch. Kết quả kiểm tra trước trên file hiện tại (dùng làm mốc): S4 khoảng 984 mã khớp, 897 mã lệch (chủ yếu mã tính
  giá năm 2024 - đầu 2025, được tính bằng dữ liệu nền cũ hơn); S1 khoảng 1.055 mã khớp, 71 mã lệch.
- [ ] AC-03 (UC-15, BR-05): Sau khi chuyển dữ liệu S4 (lớn nhất S4-2019), Sales tạo yêu cầu "CVC 30/1 (60/40)" cho S4 → mã
  S4-2020, trạng thái "Chờ xưởng xem"; tạo tiếp yêu cầu S1 → S1-1317.
- [ ] AC-04 (BR-01): Tạo yêu cầu với tên "CVC 30 (60/40)" → bị chặn với thông báo BR-01.
- [ ] AC-05 (BR-06): Tạo yêu cầu S4 với tên "pe 30/1" khi đã có "PE 30/1" ở S4 → bị chặn, thông báo nêu mã đã có.
- [ ] AC-06 (UC-16, UC-17, BR-07): Sales sửa được tên yêu cầu "Chờ xưởng xem"; sau khi xưởng đã lưu NSM, nút sửa / huỷ báo
  thông báo BR-07; yêu cầu huỷ S4-2021 → mã tiếp theo là S4-2022.
- [ ] AC-07 (UC-18, BR-08): Xưởng từ chối không nhập lý do → "Vui lòng nhập lý do."; có lý do → trạng thái Từ chối.
- [ ] AC-08 (UC-21, BR-15, BR-16): Lưu NSM cho mã có nhóm tiêu hao chưa có → trạng thái "Chưa tính được", lý do "Chưa có nhóm
  tiêu hao ..."; sau khi khai báo nhóm đó (UC-12) → mã tự chuyển "Đã tính giá" (BR-40).
- [ ] AC-09 (BR-15): Mã có NSM ở R nhưng nhóm tiêu hao có tiêu hao R = 0 → "Chưa tính được", lý do "Công đoạn R: có NSM
  nhưng nhóm tiêu hao không có tiêu hao."; công đoạn MD2 (công đoạn ghép) có NSM mà tiêu hao 0 → không báo lỗi.
- [ ] AC-10 (BR-09): Thành phần Cotton 60% + PE 30% → thông báo "Tổng tỷ lệ pha phải bằng 100% (hiện là 90,00%)."
- [ ] AC-11 (BR-11): Sợi "CM 40/1 COMPACT" ở S4 nhập NSM ở S → thông báo BR-11.
- [ ] AC-12 (BR-17, BR-19): Với S4-2017 (Cotton 70%, NSM C1 = 45): thời gian C1 = 60 ÷ 45 × 1,015 × 0,7 = 0,9473 phút/kg;
  lũy kế C1 cộng tiêu hao SBD, PCD1, PCD2, CM, DCM, MD1..V và không cộng C2, C3, PD, PD1. Với S1-1310 "TC 20/1 (60/40)
  MVS": Tổng = 12.170 VND/kg (12.169,6248), chi phí C1 = 2.669 VND/kg.
- [ ] AC-13 (BR-30): Lưu giá dòng Thường 19.273 VND/kg với hệ số 3 → dòng S4-xxxxTN có mỗi khoản gấp 3, Tổng 57.820; SO đổi
  hệ số thành 2,5 → mọi dòng TN cập nhật và có lịch sử event "Đổi hệ số thí nghiệm".
- [ ] AC-14 (UC-25, BR-31, BR-34): Thêm Chiết khấu 5% cho S4-2020 kèm lý do và đơn hàng → dòng "S4-2020 (CK1)" = mỗi khoản ×
  0,95; thêm Phụ phí 10% → "S4-2020 (PP1)"; thiếu đơn hàng → thông báo BR-34; không có dòng TN cho CK/PP.
- [ ] AC-15 (UC-28, BR-32): Nhập mã kế toán cho dòng S4-2020TN → bản S4-2020 bị khoá, trạng thái "Có mã kế toán"; mở Nhập NSM
  → không lưu được, thông báo BR-32; xoá mã kế toán → trạng thái về "Đã tính giá", sửa được.
- [ ] AC-16 (UC-24, BR-33): Trên S4-586 đã khoá, tạo ĐCNSM có lý do → mã "S4-586 (ĐCNSM3)" nếu đã có ĐCNSM1, ĐCNSM2; bản gốc
  không đổi; thiếu lý do → thông báo BR-33.
- [ ] AC-17 (UC-04, BR-36): SO áp dụng định mức mới cho S4 (tăng Điện của V 10%) ngày hiệu lực 01/01/2027 → mọi mã S4 có V được
  tính lại, kể cả mã có mã kế toán; lịch sử giá có giá cũ; màn chênh lệch hiện số dòng tăng; mã S1 không đổi.
- [ ] AC-18 (UC-13, BR-24): Xưởng S4 sửa nhóm "PE NORMAL - RING" khi có sợi TR (65/35) dùng nó (qua nhóm thứ cấp) đã có mã kế
  toán → bị chặn với thông báo BR-24; SO sửa có lý do → nhóm TR (65/35) tính lại tiêu hao, mọi mã bị ảnh hưởng (kể cả đã khoá)
  được tính lại.
- [ ] AC-19 (UC-13): Xưởng S4 sửa nhóm không có mã nào bị khoá → lưu được, các mã bị ảnh hưởng tính lại.
- [ ] AC-20 (BR-26, BR-42): Nhóm S4 "TR (65/35)" = PE Normal - Ring 65% + Viscose - Ring 35%: tiêu hao W (Bình quân) = 0,01 ×
  0,65 + 0,02 × 0,35 = 1,35%; tiêu hao C2 (Cộng thẳng) = 2,5% + 0 = 2,5%.
- [ ] AC-21 (BR-42): Chuyển dữ liệu S1: nhóm có ô tiêu hao là công thức được nhập với loại "Nhập từ file - chưa khai báo thành
  phần" và đúng giá trị trong file; nhóm không có công thức là Sơ cấp.
- [ ] AC-22 (UC-20, BR-37, BR-38): Xưởng chọn Tự điền cho sợi "CVC 40/1 (60/40)" khi đã có "CVC 30/1 (60/40)" → NSM được điền
  từ mã 30/1; đổi NSM C1 → cảnh báo, phải nhập lý do mới lưu được; đổi NSM Con → không cảnh báo.
- [ ] AC-23 (BR-39): Nhóm "CVC (60/40)" Ring có 30/1 giá 20.000 và 40/1 giá 19.500 → dashboard liệt kê cặp này với lý do "Chi số
  cao hơn nhưng giá không cao hơn".
- [ ] AC-24 (BR-54): Ba mã cùng nhóm tiêu hao có NSM C1 = 65, 65, 60 → mã NSM 60 được liệt kê ở "NSM bất thường".
- [ ] AC-25 (BR-53): Trong khoảng ngày có 10 yêu cầu mới, 6 đã lưu NSM, 2 bị từ chối, 2 đang chờ → Khả năng đáp ứng = 75%.
- [ ] AC-26 (BR-44): Dòng NSM mã "S4 - 586 (ĐCNSM2)" nhập thành bản "S4-586 (ĐCNSM2)" trỏ về "S4-586"; dòng không có mã được cấp
  mã tiếp theo; mã "S42003000010000000" có ở sheet NSM được giữ làm mã tính giá và điền vào mã kế toán, bản bị khoá.
- [ ] AC-27 (BR-41, UC-34): Tải file .pdf → thông báo BR-41; Xưởng S4 tải file có sheet "Dinh muc (phut)" → sheet đó bị bỏ qua
  với thông báo BR-45, sheet NSM vẫn được xử lý.
- [ ] AC-28 (BR-47, BR-48): Tài khoản chỉ có vai trò Kế toán bấm "Lưu NSM và giá", hoặc tài khoản không có vai trò nào bấm "Lưu mã kế toán" → thông báo BR-47; tài khoản chỉ có vai trò
  Xưởng S1 thao tác mã S4 → thông báo BR-48; quản trị viên thao tác như Phòng SO; mọi thao tác thành công có dòng nhật ký.
- [ ] AC-29 (UC-08, BR-22): SO thêm tỷ giá 26.000 hôm nay → USD/kg của S4-2017 hiển thị 0,7607; giá VND và lịch sử giá không đổi.
- [ ] AC-30 (UC-29, BR-23): Xuất Excel với bộ lọc Xưởng = S4, Loại dòng = Thường → file có đúng các dòng đang hiển thị, 2 sheet
  `Bang gia` và `Chi tiet cong doan`, VND làm tròn đến đồng.
- [ ] AC-31 (UC-14, BR-29): Xoá nhóm đang có mã dùng → thông báo BR-29; xoá nhóm không dùng → nhóm biến mất.
- [ ] AC-32 (UC-26, BR-35): Xoá dòng CK chưa có mã kế toán → thành công; dòng CK có mã kế toán → thông báo BR-35.
- [ ] AC-33 (UC-03, UC-05, UC-06, BR-50, BR-52): Thêm công đoạn với mã đã có → thông báo trùng; đổi hồi phế Con S4 từ 2,5% thành
  3% → mọi mã S4 có công đoạn S được tính lại.
- [ ] AC-34 (UC-07, BR-13): Quy trình TC Ring "B2 - C1 - C2 - SBD - PD - LF - CM - MD1 - MD2 - MD3 - R - S - W - F" → form NSM hiện
  C1, C2, SBD, PD, CM, MD1, MD2, MD3, R, S, S Compact, W (không hiện B2, LF); nhóm chưa có quy trình → hiện mọi công đoạn.
- [ ] AC-35 (UC-02, BR-49): Mỗi dòng nhật ký ghi tên đăng nhập và họ tên của tài khoản thao tác ("system" / "Hệ thống" khi chạy bằng mã hệ thống); lọc theo tài khoản,
  thao tác hoặc từ khoá chỉ còn các dòng phù hợp.

- [ ] AC-36 (UC-09, BR-30): SO lưu hệ số thí nghiệm 0 → "Hệ số thí nghiệm phải lớn hơn 0."
- [ ] AC-37 (UC-10, UC-11, BR-25, BR-28): Xưởng S4 thêm nhóm sơ cấp "LINEN - RING" với tiêu hao W 120% → thông báo BR-28; sửa
  thành 1,2% → lưu được, nhóm hiện trong tra cứu với loại "Sơ cấp", số mã đang dùng = 0; thêm lại cùng nhóm → thông báo trùng.
- [ ] AC-38 (UC-19): Màn Nhập NSM mở mặc định chỉ hiện mã "Chờ xưởng xem" và "Chưa tính được" của xưởng chọn, cũ nhất trước, kèm
  số lượng từng trạng thái.
- [ ] AC-39 (UC-22, UC-23): Xưởng sửa NSM của S4-2020 (chưa khoá) từ V 25 thành 26 → giá giảm, lịch sử giá của S4-2020 và
  S4-2020TN có dòng event "Sửa NSM" với giá cũ; màn chi tiết hiện lịch sử mới nhất trước.
- [ ] AC-40 (UC-27, UC-30, UC-31, UC-32): Lọc bảng giá Xưởng = S1, Mã kế toán = Chưa có → chỉ hiện dòng S1 chưa có mã kế toán; ô
  số liệu cập nhật theo bộ lọc; dashboard khoảng ngày không có dữ liệu hiện "Không có dữ liệu trong khoảng ngày đã chọn."
- [ ] AC-41 (UC-33): Tải file mẫu S1 → file có 7 sheet đúng tên, sheet NSM có cột C1, C2, PD, PD2, MD1, MD2, MD3, R, S, W, V và
  3 cột tỷ lệ pha PE, Viscose/other, Cotton (thành phần C1 lượt 1, C2 lượt 1, Không chải thô), chứa dữ liệu hiện tại của S1.
- [ ] AC-42 (UC-36, UC-37): Sau AC-17, danh sách lần tính lại có dòng mới nhất "Đổi định mức" với số mã đã tính; mở chi tiết →
  thấy từng dòng giá trước / sau / chênh lệch, xuất Excel được.
- [ ] AC-43 (BR-02, BR-03, BR-04): Tên "CVC 26/1 (50/50) (Re-PE 50%) MVS BCI" → chi số 26, nhóm sợi "CVC", công nghệ MVS, nhóm
  tiêu hao "CVC (50/50) (RE-PE 50%) MVS BCI"; tên "CM 40/1 COMPACT" → Ring, compact.
- [ ] AC-44 (BR-10, BR-12): Lưu NSM với mọi công đoạn = 0 → thông báo BR-10; mã không có loại đóng gói → thông báo BR-12.
- [ ] AC-45 (BR-14, BR-18, BR-21): Giá chỉ được tạo khi kiểm tra khớp đạt; chi phí đóng gói của S4-2017 (Type 3) = 4.479,605 ×
  0,2195 = 983,08 VND/kg; kết quả hiển thị làm tròn nhưng Tổng được cộng từ các số chưa làm tròn.
- [ ] AC-46 (BR-27): Nhóm sợi pha dùng chính nó (trực tiếp hoặc qua nhóm khác) làm thành phần → thông báo BR-27.
- [ ] AC-47 (BR-43): Xưởng S4 cập nhật hàng loạt sheet "2. Input tieu hao" với nhóm có group_key trùng 2 dòng → cả 2 dòng bị loại
  với lý do "Nhóm '<nhóm>' bị trùng trong file."; dòng hợp lệ khác vẫn được lưu (BR-43).
- [ ] AC-48 (BR-49): Mọi thao tác thay đổi dữ liệu (ví dụ AC-15, AC-18) có một dòng trong nhật ký với tên đăng nhập, họ tên, nội dung trước →
  sau và lý do.
- [ ] AC-49 (BR-51): SO lưu phiên bản định mức mới thiếu dòng cho "Type 2" đang hoạt động → "Thiếu định mức cho: Type 2."

- [ ] AC-50 (UC-05, UC-15, BR-60): SO đánh dấu Type 3 là mặc định của S4 → Sales chọn xưởng S4 thì ô Loại đóng gói đã là Type 3;
  Sales đổi sang Type 1 và gửi → mã lưu Type 1; đánh dấu thêm Type 1 là mặc định → thông báo BR-60.
- [ ] AC-51 (BR-60): Nhập file S4 có mã để trống loại đóng gói khi S4 đã có loại mặc định → mã vẫn "Chưa tính được" với lý do
  "Chưa có loại đóng gói.".
- [ ] AC-52 (UC-21, BR-56, BR-58): Sợi S4 pha Viscose - Ring 70% + PE Recycle - Ring 30%, cả hai chạy C3 → bảng thành phần hiện
  "C3 lượt 1 - Viscose - Ring" và "C3 lượt 2 - PE Recycle - Ring"; đổi thứ tự hai dòng → lượt đổi theo, giá không đổi.
- [ ] AC-53 (BR-56): Thêm nguyên liệu thứ 4 chạy C3 → thông báo "C3 chỉ chạy tối đa 3 nguyên liệu trong một sợi."
- [ ] AC-54 (BR-15, BR-16): Chuyển PE Recycle từ C3 sang C2 khi nguyên liệu chỉ có tiêu hao ở C3 → "Chưa tính được", lý do "C2
  lượt 1 (PE Recycle - Ring): có NSM nhưng nguyên liệu chưa khai báo tiêu hao ở C2..."; khai báo thêm tiêu hao C2 cho nguyên
  liệu → tính được, lũy kế lượt đó theo `cumulative_stages` của C2 (có PD, PD1).
- [ ] AC-55 (BR-58, BR-59, AC-01): Chuyển dữ liệu S4 theo cấu trúc mới → S4-2017 có 2 thành phần (Cotton - C1, nguyên liệu ở ô C3.3
  → C3 lượt 1) và giá vẫn 19.777,8356 VND/kg; S1-1310 vẫn 12.169,6248 VND/kg.
- [ ] AC-56 (BR-59): File S4 có 2 dòng "MODAL" chỉ khác nhau ở cột C3.1 (3,4%) và C3.2 (3,5%) → nhập thành một nhóm MODAL với C3 =
  3,4%; hai dòng trùng tên khác nhau ở cột khác → vẫn bị loại cả hai.
- [ ] AC-57 (BR-58): Sợi có nhóm tiêu hao Sơ cấp và 2 nguyên liệu cùng chạy C2 → "Chưa tính được" với lý do "C2: nhóm tiêu hao chưa
  khai báo thành phần nên chưa xác định được tiêu hao từng lượt...".
- [ ] AC-58 (BR-57): Nhóm tiêu hao "TR (65/35)" (PE Normal - Ring, Viscose - Ring) mà xưởng nhập nguyên liệu "Modal - Ring" → thông
  báo BR-57.
- [ ] AC-59 (UC-33, 5.3): Xuất file mẫu S4 → sheet tiêu hao có một cột "C3"; sheet NSM giữ cột C3.1 / C3.2 / C3.3 (lượt 1-3); mã có
  lượt 2 trên C2 có REMARK "Có thành phần chỉ sửa được trên màn hình" và tải lên lại không đổi thành phần.

- [ ] AC-60 (UC-38): Mở bất kỳ màn hình nào khi chưa có dữ liệu → danh sách xưởng, công đoạn hiện đúng, không lỗi; chức năng không hỏi chọn người thao tác.
- [ ] AC-61 (UC-40, UC-41): Gõ "CVC 30/1 (60/40)" ở Screen 2 → hiện nhóm sợi CVC, chi số 30, Ring, nhóm tiêu hao "CVC (60/40)"; sau
  một lần nhập file, Screen 6 liệt kê lần nhập đó với số dòng tạo / cập nhật / bị loại.
- [ ] AC-62 (5.6, BR-61, UC-27): Cho trước 15 file dữ liệu của app cũ được chép vào thư mục dữ liệu của app mới, khi mở Bảng giá
  thì thấy đủ 3.435 mã sợi / bản NSM (số liệu ngày 2026-09-29) với cùng mã, trạng thái, mã kế toán và số tiền như app cũ; mã
  S4-2017 có Tổng 19.777,8356 VND/kg; Screen 8 có đủ 7 dòng nhật ký; Screen 6 có 2 lần nhập file và đối
  chiếu giá cũ như app cũ; không có lần tính lại mới nào được tạo.
- [ ] AC-63 (BR-61, UC-38): Dữ liệu chép sang có công đoạn C3.1 / C3.2 / C3.3 (lưu theo cách cũ) → app mới hiện công đoạn C3 với
  lượt 1-3, thành phần nguyên liệu đúng như app cũ, giá không đổi; tạo yêu cầu S4 mới thì mã tiếp theo = số lớn nhất đã có + 1.
- [ ] AC-64 (BR-61): File `yarns.json` chép sang bị hỏng → màn hình hiện "Không đọc được dữ liệu 'yarns.json'. Vui lòng chép lại
  file này từ app cũ (thư mục data\yarn_costing)."; các màn dữ liệu nền vẫn mở được.
- [ ] AC-65 (UC-05, BR-62): Phòng SO chỉ tick "Mặc định" cho Type 2 của S4 rồi bấm "Lưu đóng gói" → hộp xác nhận ghi "Giá các mã
  không thay đổi."; sau khi lưu: "Đã lưu loại đóng gói S4. Giá các mã không thay đổi.", không có lần tính lại mới; không cần
  nhập ngày hiệu lực và lý do.
- [ ] AC-66 (UC-05, BR-62): Phòng SO đổi Phút/kg của Type 3 (đang có mã sợi dùng) từ 0,2195 thành 0,2300, nhập ngày hiệu lực
  01/10/2026 và lý do → hộp xác nhận ghi "Phút/kg của loại Type 3 (đang có mã sợi dùng) thay đổi. App sẽ tính lại toàn bộ giá xưởng
  S4 từ ngày 01/10/2026."; sau khi lưu có một lần tính lại "Đổi dữ liệu nền". Nếu bỏ trống lý do → "Vui lòng chọn ngày hiệu
  lực và nhập lý do." và không lưu.
- [ ] AC-67 (UC-05, BR-62): Đổi Phút/kg của một loại chưa có mã sợi nào dùng → hộp xác nhận ghi "Giá các mã không thay đổi.",
  không tính lại.
- [ ] AC-68 (UC-15, BR-63, BR-47): Mở Screen 2 bằng tài khoản không có vai trò Sales hoặc Phòng SO → nút "Gửi yêu cầu" bị khoá, cạnh nút hiện "Tài khoản của bạn chưa có
  vai trò cho thao tác này (quản trị viên cấp ở trang /admin)."; quản trị viên hoặc tài khoản có vai trò Sales → câu này không hiện.
- [ ] AC-69 (UC-15, BR-63): Tài khoản có vai trò Sales, chọn xưởng không có loại đóng gói chọn được → nút bị khoá với "Xưởng S1 chưa có loại đóng gói chọn được. Vui lòng báo
  Phòng SO khai báo loại đóng gói và định mức."; hết mọi lý do → nút bấm được, không còn dòng lý do.
- [ ] AC-70 (BR-64, UC-21): Cho trước nhóm sơ cấp "VISCOSE MVS" (S4) chỉ có tiêu hao chải thô C2 = 3,4% (C3 để trống), khi xưởng
  nhập NSM cho sợi dùng nhóm đó với thành phần Viscose - MVS chạy C3 (NSM 45) và bấm "Kiểm tra và xem giá" thì kiểm tra khớp đạt,
  lượt C3 dùng tiêu hao 3,4%, dòng chi tiết C3 có "Ghi chú tiêu hao" = "Tiêu hao lấy từ C2 (C3 chưa khai báo)" và giá bằng giá khi
  khai báo C3 = 3,4%.
- [ ] AC-71 (BR-64): Nhóm có C2 = 2,5% và C3 = 3,4%, nguyên liệu chạy C3 → lượt dùng 3,4% (số của dây chuyền đang chạy), không
  có ghi chú tiêu hao; chạy C2 → dùng 2,5%.
- [ ] AC-72 (BR-64, S1): Nhóm S1 chỉ có tiêu hao C1 = 2% (C2 trống), nguyên liệu chạy C2 → dùng 2% theo cách "Bình quân" của C2
  (như khi khai báo C2 = 2%), ghi chú "Tiêu hao lấy từ C1 (C2 chưa khai báo)".
- [ ] AC-73 (BR-16, BR-64): Nhóm không có tiêu hao ở cả C2 và C3, nguyên liệu Viscose - MVS chạy C3 lượt 1 → "Chưa tính được" với lý
  do "C3 lượt 1 (Viscose - MVS): có NSM nhưng nguyên liệu chưa khai báo tiêu hao ở C3 hoặc C2. Vui lòng khai báo tiêu hao chải thô
  của nguyên liệu."; với S4 C1 (không có dây chuyền tương đương) câu báo giữ như cũ.
- [ ] AC-74 (BR-64): Mã đã có giá trước khi có quy tắc này (tiêu hao khai báo đúng dây chuyền đang chạy) → một lần tính lại toàn
  bộ không làm đổi giá; bảng "Tiêu hao tính ra" của nhóm sợi pha không đổi.
- [ ] AC-75 (UC-43, BR-65): Cho trước xưởng S1 có các mã "Chưa tính được" chỉ vì thiếu tiêu hao ở C2 (có ở C1), khi Phòng SO chọn
  S1, nhập ngày hiệu lực và lý do, bấm "Tính lại các mã chưa tính được" và xác nhận thì các mã đó chuyển "Đã tính giá" (mã có mã kế
  toán chờ → "Có mã kế toán"), có dòng giá Thường + Thí nghiệm, lịch sử event "Tính lại mã chưa tính được", một lần tính lại mới
  trong "Các lần tính lại"; thông báo "Đã tính lại N mã chưa tính được của xưởng S1: M mã đã có giá, K mã vẫn chưa tính được."; các
  mã "Đã tính giá" khác không đổi.
- [ ] AC-76 (UC-43, BR-65): Xưởng không có mã "Chưa tính được" → "Xưởng S4 không có mã nào đang 'Chưa tính được'."; bỏ trống lý
  do → "Vui lòng chọn ngày hiệu lực và nhập lý do."; tài khoản chỉ có vai trò Xưởng S1 → nút bị tắt kèm chú thích BR-47.
- [ ] AC-77 (5.4, BR-64): Xuất Excel bảng giá → sheet `Chi tiet cong doan` có cột cuối "Ghi chú tiêu hao", có chữ ở các lượt lấy
  tiêu hao từ dây chuyền tương đương, trống ở các dòng khác.
- [ ] AC-78 (UC-44, 5.7): Chọn S1, loại "Khai báo thành phần sợi pha", bấm "Tải file mẫu" → file có sheet "Khai bao thanh phan"
  (mỗi nhóm tiêu hao S1 một dòng, nhóm Thứ cấp có sẵn thành phần), "Danh sach nhom", "Huong dan".
- [ ] AC-79 (UC-45, BR-67): Cho trước nhóm S1 "MODAL/POLY (52/48)" loại "Nhập từ file" và các nhóm PE, MODAL đã có, khi Phòng SO tải
  file có dòng "MODAL/POLY (52/48) | PE 48 | MODAL 52" và bấm "Kiểm tra file" thì bảng nhóm hợp lệ hiện nhóm đó chuyển Thứ cấp, tiêu
  hao mới W = 48% × W(PE) + 52% × W(MODAL), PD / PD2 cũ 0,3% → mới 0 (khi PE, MODAL không có PD / PD2); chưa lưu gì. Bấm "Lưu 1
  nhóm hợp lệ", nhập ngày hiệu lực và lý do → nhóm là Thứ cấp, có một lần tính lại "Sửa tiêu hao" và một lần nhập file loại "Khai
  báo thành phần sợi pha".
- [ ] AC-80 (BR-68): Mã S1-399 có thành phần "PE" (C1) và "Viscose/other" (C2); sau khi lưu AC-79 (PE có tiêu hao C1, MODAL có tiêu
  hao C2) → thành phần của mã đổi tên thành material_tech_key của PE và MODAL, tỷ lệ / NSM giữ nguyên, mã được tính lại và có giá.
- [ ] AC-81 (BR-68): Mã có hai thành phần cùng chạy C1 mà nhóm chỉ có một thành phần có tiêu hao C1 / C2 và tỷ lệ không khớp → mã
  "Chưa tính được" với lý do "Không ghép được thành phần '…' (C1) của mã với thành phần của nhóm tiêu hao '…'. Vui lòng chọn lại
  nguyên liệu ở màn Nhập NSM." và có tên trong bảng mã không ghép được.
- [ ] AC-82 (BR-66): File có dòng thành phần "PEE" không có ở S1 → dòng bị loại "Không tìm thấy nhóm thành phần 'PEE' ở xưởng S1.";
  dòng tổng tỷ lệ 90% → thông báo BR-27; hai dòng cùng tên nhóm → cả hai bị loại "Nhóm '…' bị trùng trong file."; dòng Tỷ lệ 1
  trống → "Thành phần 1: cần cả tên và tỷ lệ."; các dòng hợp lệ khác vẫn lưu được.
- [ ] AC-83 (BR-66, BR-67): Dòng nhóm "ABC (50/50)" chưa có trong app, Công nghệ trống → bị loại "Nhóm mới 'ABC (50/50)' cần cột
  Công nghệ là Ring hoặc MVS."; điền Công nghệ Ring → tạo nhóm Thứ cấp mới, các mã "Chưa tính được" chờ nhóm này được tính lại.
- [ ] AC-84 (BR-69): Xưởng S1 tải file có nhóm đang khoá → dòng đó bị loại với thông báo BR-24, các nhóm không khoá vẫn lưu; Phòng
  SO tải cùng file → mọi dòng hợp lệ được lưu, mã đã có mã kế toán được tính lại; Kế toán → nút tắt kèm chú thích BR-47.
- [ ] AC-85 (UC-45): Bản nháp "mau-khai-bao-thanh-phan-soi-pha-S1-20260929.xlsx" (sheet "Khai bao thanh phan S1", có thêm các cột
  gợi ý) tải lên được; các cột không đọc bị bỏ qua; dòng để trống Thành phần 1-5 không đổi gì.

## 10. Open questions (Câu hỏi mở)
- Giả định: 5 vai trò cố định (SALES, XS1, XS4, KT, SO); quản trị viên tích vai trò cho từng tài khoản ở trang `/admin` trước khi dùng.
- Giả định: Phòng SO làm được mọi thao tác của xưởng cho cả S1 và S4 (kể cả từ chối, nhập NSM, mã kế toán).
- Giả định: mọi thay đổi dữ liệu nền có ảnh hưởng đến giá (cấu hình công đoạn, hồi phế, phút/kg đóng gói, định mức) đều tính lại
  toàn bộ xưởng ngay khi lưu, với ngày hiệu lực và lý do SO nhập - như quy tắc định mức. Đổi quy trình công nghệ và tỷ giá
  không tính lại.
- Giả định: đổi hệ số thí nghiệm cập nhật dòng thí nghiệm của mọi mã cả hai xưởng, kể cả mã đã có mã kế toán.
- Giả định: một lần tính lại mà mã không đạt kiểm tra khớp → mã chuyển "Chưa tính được" nhưng giữ nguyên giá đang có (không xoá
  giá), cho đến khi tính lại thành công.
- Giả định: trên mã đã khoá vẫn được tạo dòng CK/PP mới (mỗi đơn hàng một dòng); dòng CK/PP chưa có mã kế toán được xoá, không
  sửa (muốn đổi % thì xoá và tạo dòng mới).
- Giả định: mã kế toán không kiểm tra trùng giữa các dòng (theo yêu cầu "không cần kiểm định dạng").
- Giả định: khi chuyển dữ liệu, không đọc sheet "4. Bang gia da tinh (TN x3)"; dòng thí nghiệm được app tạo lại từ giá thường
  và mã kế toán của dòng thí nghiệm để trống (kế toán / xưởng nhập lại nếu cần).
- Giả định: sợi so sánh / tự điền chép cả tỷ lệ pha; công đoạn được so sánh là các công đoạn ngoài Thô, Con, Ống, MVS (theo
  cấu hình `varies_with_count`).
- Giả định: số liệu hiển thị: VND làm tròn đến đồng, USD 4 chữ số thập phân; tính toán bên trong không làm tròn.
- Đã chốt (2026-09-25): khi chuyển dữ liệu cũ, app TÍNH LẠI TẤT CẢ mã theo dữ liệu hiện tại (kể cả mã đã có mã kế toán);
  giá cũ trong file chỉ dùng để đối chiếu (UC-35).
- Giả định: "Chuyển dữ liệu ban đầu" có thể làm nhiều lần trong giai đoạn chạy thử; mỗi lần là một lần nhập file riêng, dữ liệu
  đã có được cập nhật theo mã (không xoá dữ liệu cũ của app).
- Giả định: file tải lên tối đa 60 MB (file S1 hiện tại khoảng 40 MB) và 10.000 dòng mỗi sheet.
- Giả định: cấu hình công đoạn khởi tạo (4.4.1, 4.4.2) và hồi phế lấy đúng từ 2 file hiện tại; công đoạn "C3" trong bảng định
  mức S4 không dùng để tính (sợi viscose dùng C3.1 / C3.2 / C3.3). (Cập nhật 2026-09-28: nay C3 là một công đoạn, định mức lấy dòng "C3";
  các dòng C3.1 / C3.2 / C3.3 của sheet định mức không dùng.)
- Đã chốt (2026-09-28): C3.1 / C3.2 / C3.3 là lượt của cùng dây chuyền C3; tiêu hao chải thô theo nguyên liệu, khai báo ở dây
  chuyền nguyên liệu chạy (C2 hoặc C3); không tự điều chỉnh tiêu hao, chỉ gộp các dòng khác nhau ở C3.x (lấy số nhỏ nhất); đường
  đi sau chải thô theo cấu hình công đoạn và NSM khai báo, thiếu thì "Chưa tính được" để xưởng bổ sung; S1 C1 và C2 cùng công
  nghệ, áp dụng nhiều lượt; S4 C1 (cotton) giữ một lượt; mỗi xưởng một loại đóng gói mặc định, Sales đổi được, không tự gán cho
  dữ liệu cũ.
- Giả định: lượt được đánh theo thứ tự các dòng thành phần trên màn hình; đổi thứ tự không đổi giá.
- Đã chốt (2026-09-28): màn nhập NSM có 2 phần - bảng thành phần nguyên liệu chỉ chứa NSM chải thô (mỗi nguyên liệu một dòng);
  NSM các công đoạn còn lại (ghép sơ bộ, chải kỹ, ghép trộn, thô, con, ống, MVS) nhập một lần cho cả sợi như file Excel.
- Giả định: một sợi có tối đa 9 thành phần (3 dây chuyền × 3 lượt ở S4); thành phần "Không chải thô" không giới hạn trong số đó.
- Giả định: file mẫu / file tải lên giữ bố cục cột NSM của file Excel hiện tại (mục 5.3); thành phần không ghi được vào bố cục
  này chỉ sửa trên màn hình.
- Giả định: đổi loại đóng gói mặc định không tính lại giá và không đổi loại đóng gói của mã đã có.
- Giả định (triển khai): thêm UC-38 (dữ liệu tham chiếu), UC-39 (đã bỏ 2026-10-13), UC-40
  (nhận diện tên sợi khi gõ), UC-41 (danh sách lần nhập file) để các màn hình hiển thị được theo giao diện đã chốt; chỉ đọc
  hoặc kiểm tra, không thêm quy tắc mới.
- Giả định (triển khai): UC-21 dùng cho mã "Chờ xưởng xem" / "Chưa tính được", UC-23 dùng cho mã "Đã tính giá" (sửa NSM nhập
  sai, lịch sử ghi "Sửa NSM"); cả hai có chế độ "chỉ kiểm tra và xem giá" (không lưu) và chế độ lưu. UC-12, UC-24 và UC-34
  cũng có chế độ xem trước không lưu.
- Giả định (triển khai): khi nhập file, nhóm tiêu hao trùng tên trong cùng file bị loại tất cả các dòng trùng (đúng BR-42);
  file S4 hiện có 72 tên nhóm bị trùng (28 nhóm có số liệu khác nhau) nên nhiều nhóm sợi pha và mã S4 "Chưa tính được" cho
  đến khi SO xoá dòng trùng trong file và nhập lại (danh sách dòng bị loại có trong file kết quả nhập).
- Giả định (triển khai): dòng tiêu đề của sheet phải có ít nhất 2 tên cột cần đọc (sheet "Hoi phe": 1); dòng đánh số cột (1, 2,
  3...) bị bỏ qua; tên sheet khớp chính xác được ưu tiên hơn tên khớp không dấu (file S4 có cả "Hoi phe" và "Hồi Phế").
- Giả định (triển khai): mã trong sheet bảng giá không có ở sheet NSM và chưa có trong app bị loại; mã trùng trong sheet bảng giá
  lấy dòng đầu; công nghệ khác Ring / MVS bị loại dòng; sheet thiếu cột bắt buộc làm dừng cả file; sheet định mức thiếu mã bắt
  buộc bị bỏ qua với thông báo "Thiếu định mức cho: ...".
- Giả định (triển khai): mã kế toán của mã sợi nhập từ file chưa tính được giá được giữ chờ (mã coi như đã khoá) và gán vào dòng
  Thường khi dòng này được tạo.
- Giả định (triển khai): bảng Quy trình và bảng Đóng gói trên màn hình lưu theo kiểu "thay cả danh sách" (dòng bị xoá khỏi bảng
  sẽ bị xoá); không xoá được loại đóng gói đang có mã sợi dùng; lưu đóng gói chỉ tính lại khi phút/kg của loại đang dùng thay
  đổi.
- Giả định (triển khai): sửa nhóm tiêu hao (UC-13) tạo một lần tính lại "Sửa tiêu hao"; thêm nhóm mới (BR-40) không tạo lần tính
  lại. Số tiền lưu 10 chữ số thập phân.
- Giả định (triển khai): màn Yêu cầu chỉ liệt kê mã do Sales tạo; màn Nhập NSM mặc định chọn xưởng của tài khoản (khi tài khoản chỉ có vai trò của một xưởng); màn Nhập
  dữ liệu mặc định loại "Cập nhật hàng loạt"; nhóm Xưởng không bấm được "Kiểm tra file" ở loại "Chuyển dữ liệu ban đầu".

- Giả định (triển khai, 2026-09-28): gộp dòng tiêu hao trùng (BR-59) khi mọi cột giống nhau trừ nhóm cột C3 (gồm cả ô tên và tỷ
  lệ thành phần "Other - C3.1/2/3"); dòng trùng hoàn toàn cũng được gộp. File S4 có 74 tên nhóm trùng, gộp được 18; phần còn lại
  khác nhau ở cột khác (ví dụ nguyên liệu "PE" / "PE Normal", "S" / "S Compact") nên vẫn bị loại.
- Giả định (triển khai, 2026-09-28): nhóm Sơ cấp chỉ bị giới hạn "một nguyên liệu" khi nhóm có tên nguyên liệu và chỉ có tiêu hao
  chải thô ở tối đa một dây chuyền; ngược lại tên nguyên liệu nhập tự do (để các nhóm như của S4-2017, có tiêu hao ở C1 và C3,
  vẫn sửa được trên màn hình). So khớp tên nguyên liệu không phân biệt hoa thường, dấu, khoảng trắng.
- Giả định (triển khai, 2026-09-28): khi nhập file, tên nguyên liệu của thành phần lấy theo ô thành phần của nhóm thứ cấp; nhóm sơ
  cấp chỉ dùng tên nguyên liệu của nhóm khi sợi có đúng một ô chải thô; còn lại dùng tên ô ("Other - C3.3", "Cotton"...).
- Giả định (triển khai, 2026-09-28): nhóm không có thành phần mà có tiêu hao chải thô thì sợi cần ít nhất một thành phần có dây chuyền
  chải thô. File mẫu ghi lượt k của C3 vào cột C3.k.
- Giả định (triển khai, 2026-09-28): thông báo thêm: "Loại đóng gói mặc định phải là loại đang hoạt động."; "Dây chuyền chải thô
  '<X>' không có ở xưởng <xưởng>."; "Dây chuyền chải thô '<X>' cần số lượt tối đa từ 1 đến 3.". Cột bảng Công đoạn: "Chải thô",
  "Số lượt tối đa".
- Giả định (triển khai, 2026-09-28): dữ liệu đã lưu theo bản cũ (công đoạn C3.1-C3.3, tỷ lệ pha theo ô) được tự chuyển sang cấu trúc
  mới khi đọc; không xoá dữ liệu.

- Đã chốt (2026-09-29, chuyển sang app mới): nhóm Trang chủ "Tính Giá Sợi"; app mới chỉ có chức năng này; chuyển TOÀN BỘ dữ liệu
  Tính giá sợi của app cũ bằng cách Phòng SO chép một lần 15 file dữ liệu (mục 5.6, BR-61); ngừng nhập liệu ở app cũ ngay khi
  chép; hiện lý do nút "Gửi yêu cầu" bị khoá (BR-63); hộp xác nhận lưu đóng gói chỉ báo tính lại khi Phút/kg của loại đang có mã
  sợi dùng thay đổi (BR-62).
- Giả định: nút "Lưu đóng gói và tính lại" đổi tên thành "Lưu đóng gói" (vì phần lớn lần lưu không tính lại); ngày hiệu lực và
  lý do của thẻ Đóng gói chỉ bắt buộc khi có tính lại.
- Giả định: loại đóng gói "đang được dùng" tính cả mã "Chờ xưởng xem", "Chưa tính được", không tính mã "Đã huỷ", "Từ chối" (BR-62).
- Giả định: các "Giả định (triển khai)" phía trên đã chốt ở app cũ được giữ nguyên cho app mới (cùng cách hoạt động, để dữ liệu
  chép sang dùng tiếp được).
- Giả định: sau khi chép dữ liệu, việc Phòng SO chọn loại đóng gói mặc định cho S1 và S4, sửa các nhóm tiêu hao trùng tên trong file S4 rồi nhập lại vẫn làm trên các màn hình
  hiện có (không thêm màn hình mới).
- Giả định: menu giữ 8 mục như "Giao diện đã chốt", chưa ghi nhãn đơn vị; sẽ đổi sau khi khung sườn có menu gấp / mở và đăng nhập
  (YC-01, YC-02 trong ghi chép menu).

- Giả định (triển khai, 2026-09-29): app mới dùng lại code Tính giá sợi đã kiểm của app cũ (khung sườn hai app giống hệt), giữ
  nguyên cách tính và cách lưu, nên dữ liệu chép sang đọc được nguyên trạng. Đã thử trên bản chép dữ liệu thật ngày 2026-09-29:
  đủ 3.435 mã sợi, 1.463 nhóm tiêu hao, 4.066 dòng giá (không dòng nào đổi số tiền), 519 dòng có mã kế toán, 4.066 dòng lịch sử,
  3.258 giá cũ đối chiếu, 2 lần nhập file, 2 lần tính lại, 7 dòng nhật ký; S4-2017 = 19.777,8356 VND/kg; công đoạn S4 lưu theo
  cách cũ (C3.1-C3.3) hiện thành C3; không tạo lần tính lại nào.
- Giả định (triển khai, 2026-09-29): menu bên trái là phần khung dùng chung, không gấp / mở được và không có tiêu đề nhóm con;
  cách gần nhất trong phạm vi chức năng: sắp 8 mục theo vai trò, ghi nhãn [Chung] / [Sales] / [Xưởng] / [SO] trước tên
  (tên này cũng là tiêu đề màn hình), và khối "📂 Menu theo vai trò" gấp / mở ở đầu mỗi màn hình (mỗi nhóm cũng gấp /
  mở). Menu trái gấp / mở thật cần nâng cấp khung sườn (YC-01).
- Giả định (triển khai, 2026-09-29): UC-05 có chế độ xem trước (không lưu) để hộp xác nhận ghi đúng câu BR-62; nút xác nhận ghi
  "Lưu và tính lại" khi có tính lại, "Lưu đóng gói" khi không. Kiểm tra ngày hiệu lực / lý do chạy ngay lúc bấm "Lưu đóng gói"
  (trước khi mở hộp xác nhận).
- Giả định (triển khai, 2026-09-29): thêm UC-42 (chỉ đọc) để màn hình lấy lý do khoá nút theo BR-63. Khi nút bị khoá chỉ vì chưa
  chọn xưởng / chưa nhập tên / chưa chọn loại đóng gói (không thuộc BR-63), lời nhắc hiện khi di chuột lên nút như trước.
- Giả định (triển khai, 2026-09-29): khi file `yarns.json` hỏng, màn hình vẫn hiện dữ liệu nền (danh sách nhóm sợi để trống) kèm
  cảnh báo BR-61 ngay dưới khối menu; các màn cần dữ liệu mã sợi (Bảng giá, Yêu cầu, Nhập NSM...) hiện thông báo BR-61.

- Giả định (triển khai, 2026-09-29, sửa lỗi): trên màn Tiêu hao, ô nhập tiêu hao và tỷ lệ thành phần nhận tối đa 4 chữ số thập
  phân (theo %, ví dụ 0,395% hoặc 0,5%) và hiện đúng số đang lưu; các bảng tiêu hao chỉ xem của màn này cũng hiện 4 chữ số (ngoại
  lệ của BR-23, để thấy đúng tiêu hao đã khai báo). Các màn khác giữ cách hiện của BR-23.

- Đã chốt (2026-09-29, dây chuyền tương đương): S4 C2 ↔ C3, S1 C1 ↔ C2, S4 C1 không áp dụng; dây chuyền đang chạy có số thì luôn
  dùng số đó, chỉ khi để trống / 0 mới lấy số của dây chuyền tương đương; chi tiết tính giá ghi "Tiêu hao lấy từ <Y> (<X> chưa khai
  báo)"; thêm nút cho Phòng SO "Tính lại các mã chưa tính được" (UC-43); khi cả hai dây chuyền đều thiếu, câu báo nêu cả hai
  (BR-16, BR-64).
- Giả định: cặp dây chuyền tương đương là dữ liệu cố định theo xưởng (như danh sách dây chuyền chải thô), không sửa trên màn hình.
- Giả định: quy tắc BR-64 áp dụng ở mọi lần tính giá (nhập NSM, ĐCNSM, tính lại toàn bộ, sửa tiêu hao, nhập file, UC-43); các mã đã
  có giá không đổi giá vì đã có tiêu hao ở đúng dây chuyền đang chạy.
- Giả định: UC-43 tính cả bản NSM đã khoá (như BR-32: giá vẫn được tính lại); dòng lịch sử giá của UC-43 dùng event "Tính lại mã
  chưa tính được" cho cả dòng mới tạo lẫn dòng đã có.
- Giả định: số mã "M mã đã có giá" trong thông báo UC-43 là số bản NSM chuyển sang "Đã tính giá" / "Có mã kế toán" trong lần chạy.

- Giả định (triển khai, 2026-09-29, BR-64): AC-54 (viết trước BR-64) được hiểu theo BR-64 đã chốt sau: nguyên liệu chỉ có tiêu
  hao ở C3 mà chạy C2 thì dùng số của C3 (có ghi chú); chỉ báo "Chưa tính được" khi cả C2 và C3 đều trống (AC-73). Phần còn lại
  của AC-54 giữ nguyên (khai báo thêm C2 → dùng C2, lũy kế theo `cumulative_stages` của C2).
- Giả định (triển khai, 2026-09-29, UC-43): nút nằm ở đầu thẻ "Các lần tính lại" của Screen 5 (theo xưởng đang chọn); sau khi chạy,
  lần tính lại mới hiện trong bảng của thẻ và mở được chênh lệch như các lần tính lại khác.

- Đã chốt (2026-09-29, khai báo thành phần bằng file): tải ở Screen 6 loại "Khai báo thành phần sợi pha", cả S1 và S4, cùng một
  mẫu; nhóm Sơ cấp / Nhập từ file / Thứ cấp đều khai báo được và chuyển Thứ cấp, tên nhóm chưa có thì tạo mới; tiêu hao tính hoàn
  toàn theo thành phần (công đoạn thành phần không có tiêu hao → 0); app tự đổi tên thành phần của mã sợi (BR-68); quyền như sửa
  tiêu hao (BR-69); có xem trước, lưu bắt buộc ngày hiệu lực + lý do, tính lại mọi mã bị ảnh hưởng kể cả mã đã khoá.
- Giả định: lần tính lại của UC-45 dùng trigger / event "Sửa tiêu hao" (như sửa nhóm tiêu hao trên màn hình).
- Giả định: công nghệ của nhóm đã có không đổi qua file (cột Công nghệ chỉ dùng khi tạo nhóm mới).
- Giả định: tỷ lệ trong file tính theo % (48 = 48%); không tự hiểu 0,48 là 48%.
- Giả định: đổi tên thành phần của mã đã khoá (BR-68) được phép vì chỉ đổi tên nguyên liệu, không đổi tỷ lệ, NSM (khác với sửa NSM bị
  chặn ở BR-32).
- Giả định: tên nhóm trùng trong file khai báo bị loại cả (giống BR-42); người dùng tự sửa trùng trong Excel.

- Giả định (triển khai, 2026-09-29, UC-45): lần tính lại chỉ gồm các mã dùng nhóm được khai báo hoặc nhóm sợi pha dùng nhóm đó
  làm thành phần (BR-24); các nhóm sợi pha khác không bị tính lại tiêu hao. Mã không ghép được thành phần (BR-68) không được tính
  lại, chuyển "Chưa tính được" và giữ giá cũ.
- Giả định (triển khai, 2026-09-29, BR-68): khi một thành phần của nhóm đã được ghép với một thành phần của mã thì không dùng lại cho
  thành phần khác của cùng mã (tên nguyên liệu trong một sợi không được trùng - BR-56). Thành phần của mã có tỷ lệ 0% vẫn phải ghép
  như các thành phần khác (tài liệu không có ngoại lệ); thử trên bản chép dữ liệu thật với bản nháp S1: 95 mã có thành phần 0% / lệch
  tỷ lệ nên không ghép được.
- Giả định (triển khai, 2026-09-29, 5.7): tỷ lệ ghi "48%" hoặc "48,5" cũng đọc được (bỏ dấu %, dấu phẩy thập phân); ô chữ không phải
  số → loại dòng theo BR-66.

- Đã chốt (2026-10-13, chủ sản phẩm): bỏ hẳn cách xác nhận người thao tác riêng của chức năng; ai thao tác là tài khoản đăng nhập của
  app, các quy định theo nhóm giữ lại dưới dạng vai trò (BR-47, BR-48), nhật ký ghi tài khoản (BR-49).
- Giả định (triển khai, 2026-10-13): 5 vai trò SALES, XS1, XS4, KT, SO được khai báo cùng chức năng (mã và tên hiển thị lấy từ
  `GroupCode` của backend, cột vai trò hiện ở trang `/admin`); quản trị viên tích vai trò cho tài khoản hoặc nhóm tài khoản.
  Tài khoản không có vai trò nào vẫn xem được các màn hình đã được cấp quyền nhưng mọi nút làm thay đổi dữ liệu bị tắt.
- Giả định (triển khai, 2026-10-13): tài khoản có nhiều vai trò được làm một thao tác khi có ít nhất một vai trò cho phép thao tác đó
  và (với vai trò Xưởng) đúng xưởng; quản trị viên làm như Phòng SO; chạy bằng mã hệ thống (không có tài khoản, ví dụ kiểm thử) không bị
  chặn và ghi nhật ký "system" / "Hệ thống". Thao tác "Chuyển dữ liệu ban đầu" (BR-45) kiểm tra qua cùng quy tắc với riêng vai trò Phòng SO.
- Giả định (triển khai, 2026-10-13): các cột "người làm" đã lưu (người yêu cầu, người xử lý, người tạo / sửa, người nhập mã kế toán, người
  chạy tính lại, người nhập file, người đổi giá) ghi họ tên của tài khoản ("Hệ thống" khi không có tài khoản); dòng cũ giữ nguyên chữ
  "<nhóm> - <tên>".
- Giả định (triển khai, 2026-10-13): UC-01 và UC-39 đã bỏ (không đánh số lại các UC khác); UC-42 chỉ còn lý do về loại đóng gói của xưởng
  (kết quả không phụ thuộc người dùng nên vẫn lấy từ bộ nhớ nhanh), lý do thiếu vai trò do màn hình thêm khi tắt nút "Gửi yêu cầu".
- Giả định (triển khai, 2026-10-13): màn "Nhật ký thao tác" giữ đường dẫn cũ `nguoi-dung-nhat-ky` và nằm cùng nhóm menu "Phòng SO" để quyền
  màn hình đã cấp không bị mất; chỉ còn nhật ký (không có bảng nhóm và thành viên); không có nút xuất Excel riêng (bảng nhật ký tải CSV được).

## 11. Implementation map (filled by the AI)
| Spec item | Code |
|---|---|
| Tốc độ (2026-10-13) | 19 thao tác chỉ đọc mang `@cached_query` trong `controllers/yarn_costing_controller.py` (kết quả giữ trong RAM tới khi dữ liệu đổi); bảng dữ liệu được cache trong RAM bởi `SqlRepository` |
| Section 4 | `backend/features/yarn_costing/models/` (stage, rate_version, packaging_type, recovery_rate, process_route, exchange_rate + settings, loss_group, yarn + PriceLine + StageCostDetail, price_history, recalc_batch, legacy_price + ImportBatch, audit_log, enums); seed: `constants.py`, `repositories/*_repository.py` |
| Section 5 | `builders/workbook_reader_builder.py` (5.1, 5.2), `builders/template_file_builder.py` (5.3), `builders/file_builders.py` (5.4, 5.5), `builders/price_rows_builder.py` |
| 5.6 / BR-61 | `repositories/yarn_sql_repository.py::YarnSqlRepository` (mọi repository: bảng PostgreSQL, nhập file app cũ một lần), `repositories/legacy_conversion.py`, `exceptions.py::DataFileError`, `constants.py::DATA_FILE_UNREADABLE_MESSAGE`, `services/get_reference_data_service.py` (`data_warnings`) |
| UC-02..UC-38, UC-40..UC-45 (UC-01, UC-39 đã bỏ) | `YarnCostingController.<method>()` (bảng 2 và mục 7.1 của `docs/plans/yarn_costing-implementation-plan.md`) -> `services/<method>_service.py`; UC-42 `check_request_submit` |
| BR-01..BR-04 | `business/name_business.py` |
| BR-05..BR-08, BR-63 | `business/request_business.py` (BR-63: `RequestBusiness.submit_block_reasons`) |
| BR-09..BR-12, BR-38 | `business/nsm_business.py` |
| BR-13..BR-22 | `business/costing_business.py::CostingBusiness` |
| BR-23 | `business/display_business.py` |
| BR-24..BR-29 | `business/loss_business.py` |
| BR-30..BR-35 | `business/price_line_business.py` |
| BR-36, BR-40 | `business/recalc_business.py` |
| BR-37, BR-39, BR-54, BR-55 | `business/analysis_business.py` |
| BR-41..BR-45 | `business/import_business.py` |
| BR-47..BR-49 (BR-46 thay bằng đăng nhập) | `business/access_business.py` (`ensure_allowed`, `is_so`, `user_label`, `audit_entry`); bảng vai trò `models/access.py` (`ROLE_LABELS`, `ROLE_FACTORY`, `USE_CASE_PERMISSIONS`); vai trò của chức năng: `frontend/features/yarn_costing/manifest.py` (`roles`) |
| BR-64 (dây chuyền tương đương) | `business/costing_business.py::CostingBusiness.equivalent_line`, `declared_carding_loss`, `pass_loss_with_source`; `constants.py::EQUIVALENT_CARDING`; `models/yarn.py::StageCostDetail.loss_source_stage` / `loss_note` |
| BR-65 / UC-43 | `business/recalc_business.py::RecalcBusiness.not_priced`, `recalculate_not_priced`; `services/recalculate_not_priced_service.py`; `YarnCostingController.recalculate_not_priced` |
| BR-50..BR-52, BR-60, BR-62 | `business/master_business.py` (BR-62: `packaging_in_use`, `packaging_recalc_codes`, `packaging_confirm_text`) |
| BR-53 | `business/dashboard_business.py` |
| UC-21/23/24 luồng chung | `business/pricing_business.py` |
| BR-56..BR-58 (chải thô nhiều lượt) | `business/nsm_business.py`, `business/costing_business.py` |
| BR-59 (gộp C3.x khi nhập) | `business/import_business.py` |
| Screen 1 | `frontend/features/yarn_costing/pages/price_list_page.py::PriceListPage` |
| Screen 2 | `pages/yarn_request_page.py::YarnRequestPage` (lý do khoá nút: UC-42) |
| Screen 3 | `pages/nsm_pricing_page.py::NsmPricingPage` |
| Screen 4 | `pages/loss_group_page.py::LossGroupPage` |
| Screen 5 | `pages/master_data_page.py::MasterDataPage` (thẻ Đóng gói: `_packaging_save_button`; thẻ Các lần tính lại: `_not_priced_block` - UC-43) |
| Screen 6 | `pages/excel_import_page.py::ExcelImportPage` (loại "Khai báo thành phần sợi pha": `components/component_import.py::render_component_import`) |
| 5.7 / UC-44 / UC-45 | `builders/component_file_builder.py` (ComponentFileReaderBuilder, ComponentTemplateBuilder); `services/download_component_template_service.py`, `services/import_component_file_service.py`; `YarnCostingController.download_component_template`, `import_component_file` |
| BR-66..BR-69 | `business/component_import_business.py::ComponentImportBusiness` (`check_row` BR-66, `declared_group` BR-67, `relabel_yarn` BR-68, `plan` BR-69) |
| Screen 7 | `pages/dashboard_page.py::DashboardPage` |
| Screen 8 | `pages/user_audit_page.py::UserAuditPage` (Nhật ký thao tác; UC-02) |
| Menu theo vai trò | `manifest.py` (thứ tự) + `menu_group` của mỗi trang (menu bên trái gấp / mở của khung sườn); cảnh báo BR-61: `components/data_warnings.py` |
| Quyền theo vai trò, hộp thoại | `frontend/features/yarn_costing/components/` (permissions: tắt nút theo vai trò, dialogs, flash, display, labels, columns, recalc_diff, factory_picker) |
| Logs | mọi service ghi log các bước vào `logs/app.log` (không còn khung nhật ký trên màn hình) |
| Tests | `backend/features/yarn_costing/tests/` (conftest + helpers: tài khoản đăng nhập thử; test_calculation: khớp S4-2017 và S1-1310; test_rules; test_pricing_services; test_master_services; test_import_services; test_carding_services; test_new_app: BR-61..BR-65, UC-42, UC-43, AC-62..AC-77; test_component_import: BR-66..BR-69, UC-44, UC-45, AC-78..AC-85) |
