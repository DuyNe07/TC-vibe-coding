# Tính giá vải dệt

| Feature key | `woven_costing` (= folder name in `backend/features/` and `frontend/features/`) |
|---|---|
| Home group (Nhóm trên Trang chủ) | Kinh doanh Woven |
| Icon (Biểu tượng) | 🧵 |
| Owner (Người phụ trách) | Phòng SO (sửa 2026-11-25: trước đây ghi Sales Woven (team FS)) |
| Status (Trạng thái) | Implemented |
| Run mode (Chạy ở đâu) | Server |
| Last updated | 2026-11-27 |

> Phạm vi tài liệu này: **đợt 1** của ứng dụng "Tính giá vải dệt" (dữ liệu gốc + costsheet sales HCM / TCDN + duyệt +
> danh sách tổng hợp + in nhãn). Đợt 2 (báo giá ngành Nhuộm TCDN), đợt 3 (NGC), đợt 4 (ngành xác nhận chi phí theo OC)
> sẽ được thêm vào chính chức năng này bằng Prompt 05. Nguồn: `docs/business/_sources/woven-costing-discovery.md`.
>
> File Excel gốc dùng để đối chiếu công thức (máy người dùng):
> - `D:\Vibe Coding\Woven-fabric\Format\Tinh Gia Det - HCM (Official) 2026 07 01.xlsm` (sheet CostSheet).
> - `D:\Vibe Coding\Woven-fabric\Format\Tinh Gia Det - TCDN (Official) 2026 07 01 .xlsm` (sheet CostSheet).
> - Dữ liệu gốc: `D:\Vibe Coding\Woven-fabric\Format\Master vai\` (Raw data - Peace, Raw data - WFX).
> - 4 costsheet thật để kiểm tra kết quả: `D:\Vibe Coding\Woven-fabric\Format\File kết quả\`.
>
> Ký hiệu trong công thức: `[x]` là trường dữ liệu ở mục 4; mọi tiền là VND trừ khi ghi USD; "/m" = trên 1 mét thành
> phẩm đặt hàng.

## 1. Goal (Mục tiêu)
Sales Woven (team FS1, FS2) hiện tính giá từng đơn bằng 2 file Excel có macro (nhuộm tại HCM hoặc TCDN). Mỗi đơn là
một file rời, nên không có danh sách tổng hợp, không có lịch sử phiên bản, việc duyệt làm qua email. Mỗi tháng hơn 200
đơn, hay sai ở chỗ tick sợi se / sợi hồ và ở thông số vải mới. Dữ liệu gốc thì SO phải ghép tay qua một file trung gian.

Ứng dụng thay cả 2 file. SO tải dữ liệu vải từ Peace / WFX lên và quản lý định mức, tham số có ngày hiệu lực. Sales lập
costsheet với kết quả tính đúng như Excel, được gợi ý tick Se / Hồ và cảnh báo độ co, GP%, OP%. Sau đó sales gửi trưởng
team hoặc trưởng đơn vị duyệt, gắn OC khi chốt đơn và in nhãn thông số vải. Mọi costsheet được lưu cùng phiên bản và
xem được trong một danh sách chung.

## 2. Actors (Người dùng)
| Actor | Description |
|---|---|
| Sales | Lập, lưu, sao chép costsheet; gửi duyệt; tạo phiên bản mới; nhập OC và chốt đơn; hủy; in nhãn; thêm khách hàng. Thuộc 1 team (FS1 hoặc FS2). Xem costsheet của cả team, chỉ sửa costsheet của mình |
| Trưởng team | Duyệt / trả lại costsheet của team mình; xem mọi costsheet của team. Cũng có thể lập costsheet như sales |
| Trưởng đơn vị | Duyệt / trả lại costsheet của cả 2 team; xem tất cả |
| SO (phòng SO) | Tải dữ liệu vải Peace / WFX; nhập nhanh, sửa mã vải; cập nhật tỷ giá, bộ định mức, tham số chung, hệ số theo mã hàng, ngày lễ; quản lý khách hàng. Toàn quyền trên mọi costsheet: lập (thường để thử tính năng), sửa, duyệt, mọi thao tác (sửa 2026-11-23: trước đây chỉ xem, không sửa) |
| PD | Nhập nhanh / sửa mã vải gấp (vải mới, vải thí nghiệm) |
| Quản trị viên | Tạo tài khoản đăng nhập (tên hiển thị = họ tên), cấp quyền màn hình và **vai trò** của ứng dụng trên trang `/admin`, giống ứng dụng Tính giá sợi. Vai trò: `SALES`, `TRUONG_TEAM`, `TRUONG_DON_VI`, `SO`, `PD`, và team `FS1`, `FS2` (BR-51) |

## 3. Glossary (Thuật ngữ)
| Term | Meaning |
|---|---|
| Costsheet | Phiếu tính giá 1 mã vải cho 1 đơn hàng / báo giá, gồm chi phí sợi, ngành Dệt, ngành Nhuộm, giá bán và lợi nhuận |
| Số costsheet | Mã định danh phiếu, dạng `CS-YYYY-NNNNN`; các phiên bản cùng số costsheet |
| Phiên bản | Lần sửa của một costsheet đã duyệt; v1, v2, … |
| TCFNO / mã vải | Mã vải 10 ký tự (ví dụ EM35790026) |
| Tên hàng SY | Phần đuôi sau 10 ký tự của mã trong Peace (ví dụ SN04 trong EF29500023SN04); dùng cho đợt 2 |
| Peace / WFX | 2 hệ thống quản lý thông số vải của công ty. Peace được ưu tiên |
| Mộc / Thành phẩm (TP) | Vải sau dệt chưa nhuộm / vải sau nhuộm hoàn tất |
| Hình thức bán | Mộc (bán vải mộc) / Vải Thành Phẩm (dệt + nhuộm) / Vải Nhuộm (mua mộc ngoài về nhuộm) / Gia công dệt (khách giao sợi, mình dệt ra mộc) / Gia công nhuộm (khách giao mộc, mình nhuộm) (sửa 2026-11-25: thêm 2 loại gia công) |
| Nhà máy nhuộm | HCM hoặc TCDN; quyết định cách tính chi phí nhuộm |
| Mật độ dọc / ngang | Số sợi dọc / ngang trên 10 cm (Density Warp / Density Weft) |
| Độ co | Độ co vải khi nhuộm = (mật độ ngang TP − mật độ ngang mộc) ÷ mật độ ngang TP |
| Độ co mắc | Tỷ lệ hao sợi dọc khi mắc, theo từng mã vải, mặc định 10% |
| Se | Xe sợi (sợi có độ săn T/M) |
| Hồ | Hồ sợi dọc trước khi dệt |
| T/M | Độ săn, số vòng xoắn trên 1 mét sợi |
| Spun / Filament | Sợi xơ ngắn / sợi xơ dài |
| SIM / NIM / HIM | Các loại sợi filament có nối (intermingle). SIM, NIM phải hồ; HIM không cần hồ |
| Sợi cặn | Phần sợi thừa, được thanh lý theo giá thanh lý sợi cặn |
| % B/C | Tỷ lệ hàng loại B, C (mộc và thành phẩm), được thanh lý theo giá thanh lý TP B, C |
| Hệ số số lượng | Hệ số nhân chi phí ngành Dệt theo số mét mộc |
| Định mức | Bảng chi phí chuẩn của từng công đoạn theo khoản mục, có ngày hiệu lực |
| Khoản mục | Nhân công, Khấu hao, Điện, Vật tư, Nhiên liệu, Hóa chất, CPQL (chi phí quản lý) |
| Bộ định mức | Một lần SO tải lên toàn bộ các bảng định mức, có ngày hiệu lực |
| Bộ tham số chung | Các con số cố định (S&A %, VAT %, tiêu hao…), có ngày hiệu lực |
| Ngày tính giá | Ngày sales chọn trên costsheet; quyết định tỷ giá, bộ định mức và bộ tham số được dùng |
| Main OC | Phần số OC trước dấu chấm (ví dụ KDV10-SX-LO-0726-6564) |
| Summary OC | Số OC có dấu chấm (ví dụ KDV10-SX-LO-0726-6564.1), tách theo màu / quy trình / tính năng / cấp màu |
| Loại giá | Điều kiện giao hàng: FOB, CIF, EXW, CPT, CIP, FCA |
| F&I | Chi phí vận chuyển và bảo hiểm (Freight & Insurance) |
| GP / GP% | Lãi gộp = giá bán − giá vốn; GP% = GP ÷ giá bán |
| S&A | Chi phí bán hàng và quản lý = giá vốn × tỷ lệ S&A |
| OP / OP% | Lãi hoạt động = GP − S&A − Commission − F&I − Lãi vay; OP% = OP ÷ giá bán |
| Ngày làm việc | Thứ 2 đến thứ 6, trừ ngày lễ do SO nhập |
| Blended | Cấp màu pha: chi phí = tổng (tỷ trọng × chi phí từng cấp màu), tổng tỷ trọng = 100% |
| Liên hệ TCDN | Công đoạn / tính năng cần TCDN báo giá hóa chất; khi chưa có giá thì tính 0 và cảnh báo |

## 4. Data (Dữ liệu)

### 4.1 Mã vải (Fabric)
Một dòng cho mỗi TCFNO.

| Field | Type | Required | Validation | Description | Example |
|---|---|---|---|---|---|
| tcfno | text | Yes | đúng 10 ký tự, chữ in hoa + số, duy nhất | Mã vải đã làm sạch (BR-02) | EM35790026 |
| tcfno_raw | text | No | ≤ 40 | Mã gốc trong file | GEF29500023SN04 |
| sy_item | text | No | ≤ 30 | Tên hàng SY (đuôi mã) | SN04 |
| fabric_name | text | Yes | ≤ 300 | Tên vải (Fabric) | TC34/2(65/35)SE800+CTRANG+DTY75D/36F/1 |
| structure | text | No | | Structure | EM |
| fabric_kind | text | No | | Fabric Kind | Export MULTI YARN |
| tcfno_status | text | No | | TCFNO Status (TRIAL / OFFICIAL…) | OFFICIAL |
| created_date | date | No | | Date create | 2026-07-08 |
| in_charge | text | No | | In-Charge | Vinh Khuu The |
| greige_width_cm | decimal | No | ≥ 0 | Khổ mộc (cm) | 175 |
| greige_cut_width_cm | decimal | No | ≥ 0 | Khổ cắt mộc | 175 |
| greige_gsm | decimal | No | ≥ 0 | Trọng lượng mộc g/m2 | 202.29 |
| greige_g_per_m | decimal | No | ≥ 0 | Trọng lượng mộc g/m | 354 |
| greige_warp_density | decimal | No | ≥ 0 | Mật độ dọc mộc (sợi/10 cm) | 344 |
| greige_weft_density | decimal | No | ≥ 0 | Mật độ ngang mộc (sợi/10 cm) | 205 |
| greige_shrink_warp, greige_shrink_weft | decimal | No | | Độ co dọc / ngang ghi trong hệ thống (tham khảo) | 7.5 |
| finished_width_cm, finished_cut_width_cm, finished_gsm, finished_g_per_m, finished_warp_density, finished_weft_density, finished_shrink_warp, finished_shrink_weft | decimal | No | ≥ 0 | Các thông số tương ứng của thành phẩm (nhóm "After") | 153 |
| warping_loss_rate | decimal | Yes | 0 ≤ x < 1; mặc định 0.10 | Độ co mắc | 0.10 |
| source | list: Peace / WFX / Nhập tay | Yes | | Nguồn dữ liệu hiện tại | Peace |
| remark | text | No | ≤ 500 | Ghi chú (Remark) | THONG SÔ THIET KE |
| updated_at, updated_by | datetime, text | Yes | | Lần cập nhật cuối | |

### 4.2 Thành phần sợi (Fabric yarn)
Nhiều dòng cho mỗi mã vải; thứ tự giữ như trong file.

| Field | Type | Required | Validation | Description | Example |
|---|---|---|---|---|---|
| tcfno | text | Yes | có trong 4.1 | Mã vải | EM35790026 |
| direction | list: WARP / WEFT | Yes | "Warp", "WARP", "Soi doc", "Sợi dọc" -> WARP; tương tự WEFT | Hướng sợi | WARP |
| seq | integer | Yes | 1..9 trong mỗi hướng | Số thứ tự dòng sợi trong hướng | 1 |
| full_yarn_name | text | No | | FNAME, mô tả sợi đầy đủ của vải | DTY150D/48F/1-HIM … |
| yarn_code | text | No | | YCODE | 005679 |
| yarn_name | text | Yes | | YNAME, tên sợi (có thể là sợi se ghép) | TC 50/2 (65/35) - 800T/M YD |
| rate | decimal | Yes | 0..100 | Rate, tỷ lệ % của sợi trong vải | 2.38 |
| yarn_kind | list: Sợi đơn / Sợi se | No | "Soi don" -> Sợi đơn; "Soi se" -> Sợi se | Loại sợi | Sợi se |
| raw_yarn_code | text | No | rỗng hoặc 0 -> lấy yarn_code | YCODE sợi gốc | 004311 |
| raw_yarn_name | text | Yes | rỗng -> lấy yarn_name | YNAME sợi gốc | TC50/1(65/35) |
| raw_rate | decimal | Yes | 0 hoặc rỗng -> 100 | RATE, tỷ lệ % sợi gốc trong sợi ghép | 100 |
| twist_tpm | text | No | BR-04 | Độ săn (T/M) lấy từ tên sợi | 800T/M |

### 4.3 Lần cập nhật dữ liệu vải (Fabric import log)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| imported_at | datetime | Yes | Thời điểm lưu | 2026-11-20 09:15 |
| imported_by | text | Yes | Người tải | so01 |
| file_names | text | Yes | Tên 4 file | Weaving control.xlsx; … |
| new_count, changed_count, unchanged_count, missing_yarn_count, error_count | integer | Yes | Số mã mới / thay đổi / không đổi / thiếu sợi / lỗi | 12 / 30 / 2790 / 6 / 0 |

### 4.4 Tỷ giá (Exchange rate)
| Field | Type | Required | Validation | Description | Example |
|---|---|---|---|---|---|
| month | integer | Yes | 1..12 | Tháng | 9 |
| year | integer | Yes | 2020..2100 | Năm | 2026 |
| rate | decimal | Yes | > 0 | Tỷ giá VND/USD | 26080 |
| updated_by, updated_at | text, datetime | Yes | | | |
(month, year) là duy nhất (BR-60).

### 4.5 Bộ định mức (Norm set)
Mỗi lần SO tải file định mức (mục 5, F-05) tạo một bộ định mức mới.

| Field | Type | Required | Validation | Description | Example |
|---|---|---|---|---|---|
| norm_set_code | text | Yes | tự sinh `DM-YYYYMMDD-NN`, duy nhất | Mã bộ | DM-20260101-01 |
| effective_from | date | Yes | không trùng bộ khác | Ngày hiệu lực | 2026-01-01 |
| note | text | No | ≤ 300 | Ghi chú | Định mức năm 2026 |
| uploaded_by, uploaded_at | text, datetime | Yes | | | |

Bộ định mức gồm các bảng sau (cột đúng như sheet tương ứng của F-05):

**4.5.1 Đơn giá theo phút (sheet `DonGiaPhut`)**: mỗi dòng 1 công đoạn máy:
- công đoạn: `SE - FILAMENT`, `SE - XƠ NGẮN`, `MAC`, `CONE`, `DET`, `KIEM HANG_1` (kiểm hàng bán mộc), `KIEM HANG_2`
  (kiểm hàng giao nhuộm), `BẤM ĐỐT - CARBON`;
- tốc độ máy BQ, số cọc BQ, chu vi guồng;
- thời gian hoạt động (phút/ngày);
- đơn giá theo phút của Nhân công, Khấu hao, Điện, Vật tư, Nhiên liệu, CPQL (đ/phút).

Giá trị ban đầu = sheet `DM 2025` của file HCM (ví dụ `SE - FILAMENT`: tốc độ 8.000, số cọc 256, thời gian 1.211,50
phút; đơn giá 1.019 / 350 / 347 / 87 / 0 / 134).

**4.5.2 Tham số Se (sheet `ThamSoSe`)**, cho Filament / Xơ ngắn:

| Tham số | Filament | Xơ ngắn |
|---|---|---|
| Đơn giá máy chạy (đ/phút) | 1.832,66 | 1.038,21 |
| Đơn giá chuẩn bị (đ/lần) | 460.728 | 332.623 |
| Sản lượng / lần chuẩn bị (kg) | 155 | 140 |
| TG chuẩn bị / lần (phút) | 330 | 240 |
| Số cọc | 2.048 | 4.240 |
| Số máy | 8 | 31 |
| Số ca | 3 | 3 |

Thêm 2 tham số chung: tổng nhân sự Se hiện có = 33; số giờ làm / ngày dùng tính số lần chạy máy = 22,5.

**4.5.3 Tham số Mắc / Kiểm (sheet `ThamSoMacKiem`)**:
- tổng canh chuẩn 7.800;
- số nhịp chuẩn 12;
- hệ số khi sợi dọc có se 1,97;
- tốc độ kiểm `KIEM HANG_1` 11, `KIEM HANG_2` 11 (m/phút).

**4.5.4 Định mức Hồ (sheet `DinhMucHo`)**:
- mỗi dòng: nguyên liệu hồ (DTY, PE, TC, TR, Visco, Cotton/OE, NYLON, FDY/ITY, ATY) + nhóm tổng canh;
- 6 khoản mục (đ/m): Nhân công, Khấu hao, Điện, Vật tư, Nhiên liệu, CPQL;
- Hóa chất (đ/m).

Nhóm tổng canh:
- NYLON, ATY, FDY/ITY: `<9000`, `9000:10000`, `10000:11000`, `11000:12000`, `>12000`;
- DTY: `<5000`, `5000:7000`, `7000:9000`, `9000:11000`, `>11000`;
- các nguyên liệu khác: `<5000`, `5000:7000`, `>7000`.

Giá trị ban đầu = sheet `DM Ho 2025`.

**4.5.5 Định mức Dệt (sheet `DinhMucDet`)**:
- mỗi dòng: mật độ ngang (sợi/cm, số nguyên);
- Nhân công, Khấu hao, Điện, Vật tư, Nhiên liệu, CPQL (đ/m mộc).

Giá trị ban đầu = sheet `Định mức Dệt`.

**4.5.6 Chi số (sheet `ChiSo`)**:
- hệ sợi (Filament / Spun), chi số (ví dụ `75D + CB`, `45/2`), chi số chuyển đổi (số);
- danh sách độ săn được chọn (170, 254, 300, …).

Giá trị ban đầu = sheet `Dữ liệu` / `DATAHCM`.

**4.5.7 Nhuộm HCM – định mức tiêu chuẩn (sheet `NhuomHCM_TieuChuan`)**:
- mỗi dòng: loại vải (Cotton thường, TC/CVC/TR thường, PE thường, Sọc màu, Melange) + cấp màu (Trắng, Nhạt, Trung bình,
  Đậm, Đặc biệt);
- 7 khoản mục đ/kg TP: HCTN, Tiền lương, Khấu hao, Điện, Nhiên liệu, Vật tư, Quản lý.

Giá trị ban đầu = sheet `TỔNG HỢP` dòng 5-57.

**4.5.8 Nhuộm HCM – công đoạn đặc biệt (sheet `NhuomHCM_CongDoan`)**:
- tên công đoạn (DOT LONG, RELAX_DINH HINH, MAI, WASH, COMPACT ONG, …);
- 7 khoản mục đ/kg;
- tiêu hao (%).

Giá trị ban đầu = `TỔNG HỢP` dòng 64-86 và 126-136.

**4.5.9 Nhuộm HCM – tính năng đặc biệt (sheet `NhuomHCM_TinhNang`)**:
- mỗi dòng: tính năng (CHONG TIA CUC TIM, KHANG TINH DIEN, …) + loại vải (để trống = áp cho mọi loại vải);
- hóa chất dùng (ghi chú);
- 7 khoản mục đ/kg.

Giá trị ban đầu = `TỔNG HỢP` dòng 92-117.

**4.5.10 Nhuộm TCDN – quy trình (sheet `NhuomTCDN_QuyTrinh`)**: mỗi dòng 1 mã quy trình:
- `Nhuộm tiêu chuẩn-<NL>-<cấp màu>`, hoặc tên công đoạn (Chuẩn Bị, CPB, Singeing, Enzyming, Setting, WR, …);
- thành phần nhuộm, nguyên liệu nhuộm (Khăn, Nylon, Cotton/Nylon, Poly, Cotton/Poly, Yarn dyed), cấp màu (White, Light,
  Medium, Dark, Special, All);
- quy trình chuẩn (chuỗi công đoạn);
- Hóa chất, Nhân công, Khấu hao, Điện, Nhiên liệu, Vật tư, CPQL;
- xưởng (Nhuộm / Phụ trợ), tiêu hao (%).

Riêng dòng CPB có 4 dòng theo nguyên liệu (Nylon, Cotton/Nylon, Poly, Cotton/Poly).

Đơn vị:
- Hóa chất tính cho vải 250 g/m;
- các khoản mục khác tính đ/m.

Giá trị ban đầu = sheet `Tiêu chuẩn` file TCDN.

**4.5.11 Nhuộm TCDN – hóa chất CPB / Tenter (sheet `NhuomTCDN_HoaChat`)**: mỗi dòng 1 khóa:
- các khóa: Mercerzing, Suse, CPB theo nguyên liệu, và `W/R (C6)`, `D.W/R`, `NON-PFC (C0)`, `BONGDING (W/R;DW/R)`,
  `BONGDING (NON-PFC)` kèm nhóm trọng lượng 1 (≤ 150 g/m2) / 2 (> 150 g/m2);
- chi phí hóa chất (đ/m cho vải 250 g/m).

Giá trị ban đầu = sheet `HC CPB Tenter`.

**4.5.12 Danh mục chọn (sheet `DanhMuc`)**:
- công đoạn đặc biệt HCM, tính năng đặc biệt HCM;
- tên công đoạn TCDN (sheet `Tên Công Đoạn`);
- hóa chất WR, phẩm nhuộm đặc biệt (Phẩm nhuộm AK, Cation Dye);
- nguyên liệu hồ.

**4.5.13 Spandex cộng thêm (sheet `Spandex`)** (thêm 2026-11-23):
- mỗi dòng: loại spandex (số đứng sau "SP", ví dụ 40) và số cộng thêm vào chi số chuyển đổi (≥ 0);
- loại spandex không trùng;
- giá trị ban đầu: SP 40 = 16, SP 70 = 22 (theo sheet "Dữ liệu" file Excel);
- bộ định mức lưu trước 2026-11-23 (chưa có bảng này) dùng giá trị ban đầu.

### 4.6 Bộ tham số chung (Parameter set)
Mỗi lần SO lưu tạo 1 bộ có ngày hiệu lực. Costsheet hiện các giá trị này làm **mặc định**; sales được sửa trên từng
costsheet (BR-46), trừ các dòng ghi "chỉ SO".

| Field | Type | Giá trị ban đầu | Description |
|---|---|---|---|
| effective_from | date | 2026-01-01 | Ngày hiệu lực (duy nhất) |
| sa_rate | decimal | 10,09% | Tỷ lệ S&A trên giá vốn |
| vat_rate | decimal | 8% | VAT |
| warp_loss_base | decimal | 0,82% | Tiêu hao sợi dọc cơ bản |
| warp_loss_twist | decimal | 1% | Cộng thêm khi sợi dọc có Se |
| warp_loss_size | decimal | 2,06% | Cộng thêm khi sợi dọc có Hồ |
| weft_loss_table | 6 số | Se: 6,77% @130 cm, 5,47% @175 cm, 4,77% @215 cm; không Se: 5,75%, 4,45%, 3,75% | Tiêu hao sợi ngang theo khổ mộc |
| twist_loss_offset | decimal | 1% | Trừ khi tính sản lượng Se |
| greige_bc_rate_grey | decimal | 4% | % B/C mộc khi Hình thức bán = Mộc |
| greige_bc_rate_other | decimal | 5% | % B/C mộc khi bán thành phẩm |
| finished_bc_rate_grey | decimal | 0% | % B/C TP khi Hình thức bán = Mộc |
| finished_bc_rate_other | decimal | 4% | % B/C TP khi bán thành phẩm |
| yarn_waste_price | decimal | 15.000 đ/kg | Giá thanh lý sợi cặn |
| bc_fabric_price | decimal | 5.000 đ/m | Giá thanh lý TP B, C |
| quantity_factor_table | bảng | xem BR-23 | Hệ số số lượng theo số mét mộc |
| trial_quantity_factor | decimal | 2 | Hệ số số lượng cho đơn Thí nghiệm |
| warping_extra_loss | decimal | 0,65% | Hao mắc cộng thêm |
| size_chemical_factor | decimal | 1,11 | Hệ số nhân hóa chất hồ |
| default_warping_loss | decimal | 10% | Độ co mắc mặc định cho mã mới |
| hcm_small_lot_kg | decimal | 250 kg | Dưới mức này nhuộm HCM nhân hệ số |
| hcm_small_lot_factor | decimal | 2 | Hệ số nhuộm HCM cho thí nghiệm / lô nhỏ (HCTN và Tiền lương) |
| tcdn_standard_dye_loss | decimal | 4% | Tiêu hao nhuộm tiêu chuẩn TCDN |
| tcdn_factor_large | decimal | 0,95 khi ≥ 50.000 m | Hệ số TCDN |
| tcdn_factor_dye_small | decimal | 1,2 khi ≤ 150 m | Hệ số TCDN nhuộm |
| tcdn_factor_partial_small | decimal | 1,5 khi ≤ 100 m | Hệ số TCDN partial |
| min_shrinkage | decimal | 5% (chỉ SO) | Độ co tối thiểu không cần lý do |
| gp_threshold | decimal | 15% (chỉ SO) | Ngưỡng cảnh báo GP% |
| op_threshold | decimal | 6,4% (chỉ SO) | Ngưỡng cảnh báo OP% |
| yarn_price_valid_days | integer | 5 (chỉ SO) | Số ngày làm việc giá sợi còn hiệu lực |

**Sửa 2026-11-25 – tham số chia theo ngành và gom thành bảng.** Mỗi tham số trên thuộc đúng 1 nhóm (hiển thị theo nhóm
ở Màn hình 5 và thẻ Tham số của costsheet):
- **Sợi:** warp_loss_base, warp_loss_twist, warp_loss_size, weft_loss_table, twist_loss_offset, yarn_waste_price,
  yarn_price_valid_days.
- **Dệt:** bảng discount sản lượng Dệt (4.6.1), warping_extra_loss, default_warping_loss, size_chemical_factor.
- **Nhuộm HCM:** bảng discount sản lượng Nhuộm HCM (4.6.1).
- **Nhuộm TCDN:** tcdn_standard_dye_loss, bảng discount sản lượng Nhuộm TCDN (4.6.1).
- **Giá bán & chung:** sa_rate, vat_rate, gp_threshold, op_threshold, bảng % B/C (4.6.2), bc_fabric_price,
  min_shrinkage.

Các tham số rời cũ của discount (quantity_factor_table, trial_quantity_factor, hcm_small_lot_kg, hcm_small_lot_factor,
tcdn_factor_large, tcdn_factor_dye_small, tcdn_factor_partial_small) và % B/C (greige_bc_rate_grey,
greige_bc_rate_other, finished_bc_rate_grey, finished_bc_rate_other) được thay bằng 2 bảng dưới đây. Bộ tham số lưu
trước 2026-11-25 được đọc thành bảng tương ứng với đúng số cũ.

**4.6.1 Bảng discount theo sản lượng (thêm 2026-11-25)**, mỗi dòng:

| Field | Type | Required | Validation | Description | Example |
|---|---|---|---|---|---|
| department | list: Dệt / Nhuộm HCM / Nhuộm TCDN | Yes | | Ngành | Dệt |
| condition | list: Đại trà / Thí nghiệm / Nhuộm / Partial | Yes | Dệt, HCM: Đại trà / Thí nghiệm; TCDN: Đại trà / Nhuộm / Partial | Loại đơn / điều kiện áp dụng | Đại trà |
| quantity_unit | list: m mộc / kg TP / m TP | Yes | Dệt: m mộc; HCM: kg TP; TCDN: m TP | Đơn vị sản lượng | m mộc |
| from_qty | decimal | No | ≥ 0; trống = không giới hạn dưới | Từ | 5000 |
| from_inclusive | yes-no | Yes | | Có tính đúng mốc "Từ" không (≥ hay >) | Yes |
| to_qty | decimal | No | > from_qty; trống = không giới hạn trên | Đến | 10000 |
| to_inclusive | yes-no | Yes | | Có tính đúng mốc "Đến" không (≤ hay <) | No |
| factor | decimal | Yes | > 0 | Hệ số | 1.05 |
| applies_to | text (chỉ xem) | | theo ngành | Áp dụng cho: Dệt -> Mắc Hồ, Mắc phân băng, Cone, Dệt, Kiểm; HCM -> Hóa chất thuốc nhuộm và Tiền lương; TCDN -> mọi dòng nhuộm | |
| interpolate | yes-no | Yes | mặc định No | Chia đều giữa mốc (chỉ để đọc đúng bộ tham số cũ theo kiểu Excel); bộ mới luôn No | No |

Giá trị theo quy định công ty (bảng "Thống nhất giảm giá / phụ phí theo sản lượng đơn hàng", người dùng gửi 2026-11-25),
**theo bậc, không chia đều**. Sản lượng Dệt là số mét mộc cần (BR-18).
- **Dệt – Đại trà:**
  - 1 < SL < 5.000 -> 1,1;
  - 5.000 ≤ SL < 10.000 -> 1,05;
  - 10.000 ≤ SL ≤ 20.000 -> 1;
  - 20.000 < SL < 50.000 -> 0,95;
  - 50.000 ≤ SL < 100.000 -> 0,92;
  - SL ≥ 100.000 -> 0,9.
- **Dệt – Thí nghiệm:** mọi sản lượng -> 2.
- **Nhuộm HCM:**
  - Thí nghiệm -> 2;
  - Đại trà, kg TP < 250 -> 2;
  - Đại trà, từ 250 -> 1.
- **Nhuộm TCDN:**
  - m TP ≥ 50.000 -> 0,95 (mọi điều kiện, ưu tiên trước);
  - Nhuộm, ≤ 150 m -> 1,2;
  - Partial, ≤ 100 m -> 1,5;
  - còn lại -> 1.

**4.6.2 Bảng % B/C theo hình thức bán (thêm 2026-11-25)**, mỗi dòng:
- sale_form: Mộc / Vải Thành Phẩm / Vải Nhuộm;
- greige_bc_rate: % B/C mộc;
- finished_bc_rate: % B/C thành phẩm;
- giá trị: Mộc 4% / 0%; Vải Thành Phẩm 5% / 4%; Vải Nhuộm 5% / 4%.
- (thêm 2026-11-25, gia công) 2 dòng mới: **Gia công dệt** 4% / 0% và **Gia công nhuộm** 5% / 4%; SO sửa được. Bộ tham
  số đã lưu chưa có 2 dòng này: Gia công dệt lấy dòng Mộc, Gia công nhuộm lấy dòng Vải Nhuộm (không đổi dữ liệu đã lưu).

**Bộ tham số mới (2026-11-25):**
- App tạo sẵn 1 bộ tham số hiệu lực **25/11/2026**: lấy mọi giá trị của bộ mới nhất trước đó, thay bảng discount Dệt
  bằng bảng bậc trên, và đặt yarn_waste_price = 0, bc_fabric_price = 0.
- Bộ ban đầu cài mới (seed) cũng có giá thanh lý = 0 nhưng giữ kiểu Excel cho bộ 01/01/2026.
- Không sửa bộ tham số cũ: phiếu có ngày tính giá trước 25/11/2026 giữ đúng cách tính cũ.

### 4.7 Hệ số theo mã hàng (Fabric factor)
| Field | Type | Required | Validation | Description | Example |
|---|---|---|---|---|---|
| tcfno | text | Yes | có trong 4.1 | Mã vải | ES17020213 |
| stage | list: Se / Mắc Hồ / Mắc / Cone / Dệt / Kiểm | Yes | | Công đoạn | Dệt |
| cost_item | list: Nhân công / Khấu hao / Điện / Vật tư / Nhiên liệu / Hóa chất / CPQL | Yes | | Khoản mục | Vật tư |
| multiplier | decimal | Yes | > 0, mặc định 1 | Hệ số nhân | 1.12 |
| addition | decimal | Yes | mặc định 0 | Cộng thêm (đ/đơn vị của công đoạn) | 231 |
| effective_from | date | Yes | | Hiệu lực từ | 2026-01-01 |
| active | yes-no | Yes | | Đang dùng | Yes |
| note | text | No | ≤ 300 | Ghi chú | |

Dữ liệu ban đầu: ES17020213 và ES17020413, mỗi mã 3 dòng:
- Mắc Hồ – Hóa chất ×1,5 + 0;
- Dệt – Nhân công ×1,25 + 0;
- Dệt – Vật tư ×1,12 + 231.

### 4.8 Ngày lễ (Holiday)
| Field | Type | Required | Validation | Description | Example |
|---|---|---|---|---|---|
| date | date | Yes | duy nhất | Ngày nghỉ lễ | 2026-09-02 |
| name | text | Yes | ≤ 100 | Tên ngày lễ | Quốc khánh |

### 4.9 Khách hàng (Customer)
| Field | Type | Required | Validation | Description | Example |
|---|---|---|---|---|---|
| customer_code | text | Yes | 2-8 ký tự, chữ in hoa và số, duy nhất (BR-50) | Mã khách hàng, dùng trong số costsheet | ICHI |
| name | text | Yes | 2-200 ký tự, duy nhất (so sánh không dấu, không phân biệt hoa thường, bỏ khoảng trắng thừa) | Tên khách hàng | Ichimura Sangyo |
| team | list: FS1 / FS2 / Chung | Yes | | Team phụ trách | FS1 |
| created_by, created_at | text, datetime | Yes | | Người tạo | sales05 |
| active | yes-no | Yes | | Đang dùng | Yes |

### 4.10 Người dùng và vai trò
Không lưu riêng trong ứng dụng. Lấy từ tài khoản đăng nhập:
- tên đăng nhập, tên hiển thị (họ tên);
- các vai trò quản trị viên cấp cho ứng dụng này (BR-51).

Mỗi costsheet lưu lại tên đăng nhập, họ tên và team của người lập tại thời điểm tạo.

### 4.11 Costsheet – đầu phiếu (Costsheet)
Mỗi phiên bản là một bản ghi; các phiên bản chung `costsheet_no`.

| Field | Type | Required | Validation | Description | Example |
|---|---|---|---|---|---|
| costsheet_no | text | Yes | tự sinh `CS-<mã KH>-YYYY-NNNNN` (BR-41) | Số costsheet | CS-ICHI-2026-00125 |
| version | integer | Yes | ≥ 1 | Phiên bản | 2 |
| status | list: Nháp / Chờ duyệt / Trả lại / Đã duyệt / Đã chốt đơn / Hủy / Đã thay thế | Yes | BR-30..BR-38 | Trạng thái | Đã duyệt |
| copied_from | text | No | | Số costsheet + phiên bản nguồn khi sao chép | CS-2026-00098 v1 |
| dye_plant | list: HCM / TCDN | Yes | | Nhà máy nhuộm | TCDN |
| customer_name | text | Yes | có trong 4.9 | Khách hàng | Ichimura Sangyo |
| market | list: Xuất Khẩu / Nội Địa | Yes | | Thị trường | Xuất Khẩu |
| order_type | list: Thí Nghiệm / Sản Xuất / Dự Trữ / Gia Công | Yes | | Loại đơn hàng | Sản Xuất |
| oc_no | text | No | BR-40 | Số OC (Main hoặc Summary) | KDV10-SX-EX-0826-7809.1 |
| style | text | No | ≤ 100 | Style | BANVAI-0221 |
| sale_form | list: Mộc / Vải Thành Phẩm / Vải Nhuộm / Gia công dệt / Gia công nhuộm | Yes | (sửa 2026-11-25: thêm Gia công dệt, Gia công nhuộm; phiếu đã lưu giữ giá trị cũ) | Hình thức bán | Vải Thành Phẩm |
| greige_buy_price | decimal | Có khi Vải Nhuộm | > 0 | Giá vải mộc mua ngoài (đ/m) | 21000 |
| delivery_date | date | No | | Ngày giao hàng | 2026-09-15 |
| sales_username, sales_name | text | Yes | người đăng nhập có vai trò SALES, TRUONG_TEAM hoặc SO (sửa 2026-11-23: thêm SO) | Người lập | khue.dt, Doãn Thị Khuê |
| team | list: FS1 / FS2 / SO | Yes | lấy từ vai trò team của người lập lúc tạo (BR-51); người lập chỉ có vai trò SO (không có FS1 / FS2) -> "SO" (sửa 2026-11-23: thêm giá trị SO) | Team | FS1 |
| costing_date | date | Yes | mặc định hôm nay | Ngày tính giá | 2026-08-07 |
| tcfno | text | Yes | có trong 4.1 (BR-03) | Mã vải | EF35320026 |
| order_meters | decimal | Yes | > 0 | Số lượng đặt (m TP) | 10000 |
| exchange_rate | decimal | Yes | tra theo BR-61 | Tỷ giá dùng | 26790 |
| norm_set_code | text | Yes | BR-62 | Bộ định mức dùng | DM-20260101-01 |
| parameter_set_date | date | Yes | BR-62 | Bộ tham số dùng | 2026-01-01 |
| fabric_snapshot | dữ liệu | Yes | | Bản chụp thông số 4.1 + 4.2 lúc tính | |
| fabric_overridden | yes-no | Yes | chỉ Yes được khi mã vải nguồn "Nhập tay" (BR-47) | Sales đã sửa thông số vải trên phiếu | No |
| shrinkage_exception | list: Không / Mộc khách đã ổn định / Có pre-setting | Yes | mặc định Không | Lý do ngoại lệ độ co | Không |
| shrinkage_reason | text | Có khi BR-14 cảnh báo | ≤ 300 | Lý do độ co thấp / bằng 0 | Mộc khách gửi đã ổn định |
| price_type | list: FOB / CIF / EXW / CPT / CIP / FCA | Yes | | Loại giá | CIF |
| note | text | No | ≤ 1000 | Ghi chú | |
| return_reason, cancel_reason | text | Theo BR-33, BR-36 | ≤ 500 | Lý do trả lại / hủy | |
| approved_by, approved_at | text, datetime | No | | Người, lúc duyệt | |
| created_by, created_at, updated_at | | Yes | | | |

### 4.12 Dòng sợi (Costsheet yarn line)
Tối đa 9 dòng WARP + 9 dòng WEFT, tự lấy từ 4.2 theo mã vải.

| Field | Type | Required | Validation | Description | Example |
|---|---|---|---|---|---|
| direction, seq | list, integer | Yes | | Hướng, thứ tự | WARP, 1 |
| yarn_name | text | Yes | | Tên sợi gốc (raw_yarn_name) | DTY 75D/72F/1 SIM FD |
| twist_tpm | text | No | | Độ săn | 400T/M |
| ratio | decimal | Yes | tính BR-05 | Tỷ lệ sợi trong vải (0..1) | 0.4877 |
| price_currency | list: USD / VND | Yes | | Đơn vị nhập giá | USD |
| price_input | decimal | Yes | > 0 khi ratio > 0 | Giá sales nhập (USD/kg hoặc đ/kg) | 3.95 |
| price_vnd | decimal | Yes | = price_input × tỷ giá nếu USD | Giá sợi đ/kg | 105820.5 |
| price_entered_on | date | Yes | | Ngày nhập / xác nhận giá (BR-44) | 2026-08-07 |
| waste_rate | decimal | Yes | 0 ≤ x < 1 | Tỷ lệ sợi cặn | 0.02 |
| is_twisted | yes-no | Yes | gợi ý BR-06 | Tick Se | No |
| is_sized | yes-no | Yes | gợi ý BR-07..BR-09 | Tick Hồ (chỉ sợi dọc) | Yes |
| size_suggest_reason | text | No | | Lý do app gợi ý Hồ | Tên vải có "HO" |

### 4.13 Dòng Se (Costsheet twist line)
Tối đa 9 dòng Se dọc + 9 dòng Se ngang (Excel dòng 51-68).

| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| direction | list: Dọc / Ngang | Yes | | Dọc |
| fiber_system | list: Filament / Spun | Yes | Hệ sợi; app gợi ý sẵn theo chi số (BR-83), sales chọn lại được nếu sai (sửa 2026-11-23) | Filament |
| count | text | Yes | Chi số, app gợi ý sẵn (BR-86), sales gõ lại tự do, dạng theo BR-81 (sửa 2026-11-23: trước đây chỉ chọn trong 4.5.6) | 75D + CB |
| converted_count | decimal | Yes (tính) | Chi số chuyển đổi do app tính (BR-81), lưu để tính, **không hiển thị** (giống file Excel) (thêm 2026-11-23) | 95 |
| twist | integer | Yes | Độ săn T/M, app gợi ý sẵn (BR-86), sales gõ lại 50-3.000 (BR-82) (sửa 2026-11-23) | 400 |
| quantity_kg | decimal | Yes | > 0, SL yêu cầu (kg); app gợi ý sẵn (BR-86) | 14.02 |

Chi số cone 1, 2 (4.14) cũng gõ tự do theo BR-81, không hiển thị chi số chuyển đổi (sửa 2026-11-23). (sửa
2026-11-26: chi số cone nay nằm trong bảng cone 4.14a, vẫn gõ tự do theo BR-81.)

### 4.14 Ngành Dệt – lựa chọn và gia công (Costsheet weaving input)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| size_material | list (4.5.4 nguyên liệu hồ) | Có khi có Hồ | Nguyên liệu hồ | DTY |
| warping_band | list: Có / Không | Có khi không có nguyên liệu hồ | Mắc phân băng | Không |
| cone_count_1, cone_count_2 | text (chi số) | No | (bỏ từ 2026-11-26, thay bằng bảng cone 4.14a; số đã lưu được chuyển thành dòng cone) Chi số sợi cone 1, 2; cone 1 điền sẵn theo BR-87 (sửa 2026-11-23) | 150D |
| cone_qty_1, cone_qty_2 | decimal kg | No | (bỏ từ 2026-11-26, thay bằng bảng cone 4.14a) Số lượng cone; cone 1 điền sẵn theo BR-87, hiện ngay trong ô (sửa 2026-11-23: trước đây để trống = tổng Se ngang nhưng không hiện số) | 930 |
| twist_outsourcing_price | decimal đ/kg | No | Gia công Se | 0 |
| twist_outsourcing_qty | decimal kg | No | SL gia công Se | 0 |
| size_outsourcing_price | decimal đ/m | No | Gia công Hồ | 0 |
| weaving_outsourcing_price | decimal đ/m | No | Gia công Dệt | 0 |
| other_outsourcing_price | decimal đ/m | No | Chi phí gia công khác | 0 |

### 4.14a Dòng cone (Costsheet cone line) (thêm 2026-11-26)
Mỗi dòng là 1 cone (1 lần đánh ống sợi ngang). Không giới hạn số dòng (tối đa 18, bằng số dòng Se ngang × 2).

| Field | Type | Required | Validation | Description | Example |
|---|---|---|---|---|---|
| count | text (chi số) | Có khi SL > 0 | Dạng theo BR-81 | Chi số cone; app gợi ý sẵn (BR-100), sales gõ lại tự do | 150D + 30D |
| quantity_kg | decimal kg | Yes | ≥ 0 | SL cone; app gợi ý sẵn = tổng SL các dòng Se ngang gộp vào cone (BR-100) | 76.51 |
| members | text | No (chỉ xem) | | Các dòng Se ngang gộp vào cone, app ghi khi gợi ý; dòng sales thêm thì trống | 150D (400 T/M) + 30D (400 T/M) |
| suggested | yes-no | Yes | | Dòng do app gợi ý (Yes) hay sales đã sửa / tự thêm (No) | Yes |

Costsheet lưu trước 2026-11-26: cone 1 / cone 2 có số (chi số hoặc SL) thành 1 dòng cone mỗi cone, giữ nguyên chi số và
SL; dòng có ô còn là gợi ý BR-87 thì suggested = Yes, còn lại = No. Cone trống không tạo dòng.
Danh sách các dòng gợi ý sales đã xóa được nhớ để không tạo lại (giống dòng Se, BR-86).

### 4.15 Nhuộm HCM – lựa chọn (Costsheet HCM dyeing input)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| dye_material | list: Cotton thường / TC/CVC/TR thường / PE thường / Sọc màu / Melange | Có khi không phải Mộc | Nguyên liệu nhuộm | TC/CVC/TR thường |
| color_level | list: Trắng / Nhạt / Trung bình / Đậm / Đặc biệt / Blended | Có khi không phải Mộc | Cấp màu | Đậm |
| blend_ratios | 5 decimal (Trắng, Nhạt, Trung bình, Đậm, Đặc biệt) | Có khi Blended | Tỷ trọng, tổng = 100% | 0/0/50/50/0 |
| width_type | list: 1 / 2 / 3 | Yes, mặc định 1 | Khổ đơn / đôi / ba | 1 |
| dye_loss_rate | decimal | Có khi có nhuộm tiêu chuẩn | Tiêu hao quy trình nhuộm (%) | 0.024 |
| special_stages | tối đa 7 dòng: tên (4.5.8) | No | Công đoạn đặc biệt | COMPACT |
| special_features | tối đa 6 dòng: tên (4.5.9) | No | Tính năng đặc biệt | CHONG TIA CUC TIM |
| special_costs | tối đa 2 dòng: tên + đ/kg | No | Chi phí đặc biệt (chưa có trong quy định) | |
| extra_cost_name + 7 khoản mục đ/kg | text + decimal | No | Chi phí phát sinh do ngành báo giá (báo giá riêng) | |
| extra_cost_reason | text | Có khi sales sửa số so với giá ngành báo | | |
| outsourcing_lines | tối đa 2 dòng: tên + đ/kg | No | Gia công | |

### 4.16 Nhuộm TCDN – lựa chọn (Costsheet TCDN dyeing input)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| dye_material | list: Khăn / Nylon / Cotton/Nylon / Poly / Cotton/Poly / Yarn dyed | Có khi không phải Mộc | Nguyên liệu nhuộm | Poly |
| color_level | list: White / Light / Medium / Dark / Special / All / Blended | Có khi không phải Mộc | Cấp màu | White |
| blend_ratios | 5 decimal (White, Light, Medium, Dark, Special) | Có khi Blended | Tổng = 100% | |
| special_dye | list: Phẩm nhuộm AK / Cation Dye | No | Phẩm nhuộm đặc biệt | |
| special_dye_chemical_price | decimal | Có khi chọn phẩm nhuộm đặc biệt | Giá hóa chất thuốc nhuộm (đ/m cho vải 250 g/m) | |
| wr_chemical | list: W/R (C6) / D.W/R / NON-PFC (C0) / BONGDING (W/R;DW/R) / BONGDING (NON-PFC) | No | Hóa chất WR | |
| extra_stages | tối đa 13 dòng: tên công đoạn — chỉ chọn các công đoạn có dòng riêng trong 4.5.10 (không phải dòng "Nhuộm tiêu chuẩn-…"), tức 28 công đoạn như file Excel (CPB có 4 dòng theo nguyên liệu, tính là 1) (sửa 2026-11-23: trước đây danh sách gộp cả tên ở 4.5.12 như Suse 1, Ageing room, Kuster, Dyeing, Dry không có định mức) + giá hóa chất đ/m (bắt buộc với Coating, Santa, Bonding, Soaping) | No | Công đoạn ngoài quy trình tiêu chuẩn; công đoạn lặp lại = thêm dòng | Soaping / 362 |
| special_features | tối đa 6 dòng: tên + giá hóa chất đ/m | No | Tính năng đặc biệt (chưa có giá = "liên hệ TCDN") | |
| extra_cost_type | list: Nhuộm / Partial | Có khi có chi phí phát sinh | Loại quy trình | |
| extra_cost_loss_rate | decimal | Có khi có chi phí phát sinh | Tiêu hao quy trình nhuộm | |
| extra_cost_name + 7 khoản mục đ/m | | No | Chi phí phát sinh do ngành báo giá | |
| extra_cost_reason | text | Có khi sales sửa số so với giá ngành báo | | |
| outsourcing_lines | tối đa 2 dòng: tên + đ/m + tiêu hao % | No | Gia công ngoài | |

### 4.17 Giá bán (Costsheet price)
| Field | Type | Required | Description | Example |
|---|---|---|---|---|
| sell_price_currency | list: USD / VND | Yes | | USD |
| sell_price_input | decimal | Yes, > 0 | Giá bán chưa VAT (USD/m hoặc đ/m) | 2.26 |
| cogs_extra_lines | tối đa 10 dòng: tên + đ/m + ghi chú | No | Chi phí phát sinh vào giá vốn (ví dụ Chi phí test vải) | Chi phí test vải / 300 |
| commission | decimal đ/m | Yes, ≥ 0, mặc định 0 | Commission | 0 |
| freight_insurance | decimal đ/m | Theo BR-29 | F&I hoặc phí vận chuyển | 0 |
| interest_cost | decimal đ/m | Yes, ≥ 0, mặc định 0 | Lãi vay đơn hàng trả chậm | 0 |
| ship_date | date | No | Ngày shipment | |

### 4.18 Tham số đã sửa trên costsheet (Parameter override)
| Field | Type | Description | Example |
|---|---|---|---|
| parameter | text | Tên tham số ở 4.6 | sa_rate |
| default_value | decimal | Giá trị của bộ tham số | 0.1009 |
| used_value | decimal | Giá trị sales dùng | 0.09 |

### 4.19 Lịch sử (Costsheet history)
| Field | Type | Description | Example |
|---|---|---|---|
| costsheet_no, version | | | CS-2026-00125, 2 |
| action | list: Tạo / Lưu / Gửi duyệt / Duyệt / Duyệt tự động / Trả lại / Tạo phiên bản mới / Chốt đơn / Sửa OC / Hủy / Sao chép | | Duyệt |
| by, at | text, datetime | | truong.fs1, 2026-08-08 10:02 |
| comment | text | Lý do / ghi chú | |

### 4.20 Kết quả tính (lưu cùng mỗi phiên bản, chỉ đọc)
Các trường tính ra ở BR-10..BR-29, lưu lại để costsheet cũ giữ nguyên số:
- lượng mộc, kg mộc, kg TP, hệ số số lượng, độ co, tiêu hao nhuộm;
- tiền sợi; chi phí ngành Dệt; chi phí Nhuộm;
- tổng chi phí, đơn giá (đ/m, USD/m);
- giá vốn, GP, GP%, S&A, OP, OP%, giá có VAT;
- bảng chi phí theo khoản mục (Se, Dệt, Nhuộm, đ/m);
- danh sách cảnh báo.

### 4.21 Phiếu gia công nhuộm – đầu phiếu (Dyeing job order) (thêm 2026-11-25)
Một phiếu = 1 hợp đồng / 1 lần trình, gồm nhiều dòng mã hàng (4.22). Nguồn: file "Forrmat NGC Nhuộm TCDN.xlsm".
| Field | Type | Required | Validation | Description | Example |
|---|---|---|---|---|---|
| job_no | text | Yes | tự sinh BR-96 | Số phiếu gia công | GC-SONE-2026-00001 |
| contract_no | text | No | ≤ 60 | Số hợp đồng | TCG2024-SONE |
| customer_name | text | Yes | có trong 4.9 | Khách hàng | S-ONE |
| dye_plant | list: HCM / TCDN | Yes | mặc định **TCDN** | Đơn vị gia công | TCDN |
| costing_date | date | Yes | | Ngày tính giá (lấy tỷ giá, bộ định mức, bộ tham số theo ngày này: BR-61, BR-62) | 2026-11-25 |
| exchange_rate | decimal | Yes | > 0 | Tỷ giá (lấy theo BR-61, chỉ đọc) | 26290 |
| note | text | No | ≤ 1000 | Ghi chú | |
| status, sales_username, team, approver, return_reason, cancel_reason | như 4.11 | | | Trạng thái, người lập, team, người duyệt, lý do | Nháp |
| result | chỉ đọc | | | Kết quả tính 4.23, lưu cùng phiếu (giữ số cũ như BR-39) | |

### 4.22 Dòng mã hàng gia công nhuộm (Dyeing job line) (thêm 2026-11-25)
Tối đa 30 dòng / phiếu. Mỗi dòng = 1 mã hàng / 1 OC. (sửa 2026-11-25: file NGC ghi "Số PO", app ghi "Số OC")
| Field | Type | Required | Validation | Description | Example |
|---|---|---|---|---|---|
| finished_bc_rate | decimal | Yes | 0 ≤ x < 1, mặc định **0%** | % thành phẩm B, C | 0% |
| item_code | text | Yes | ≤ 40, gõ tự do (chữ, số, dấu - . / khoảng trắng); không cần có trong 4.1 | Mã hàng (mã vải) do sales điền | DVDP-SAFM001-PA |
| style | text | No | ≤ 100 | Tên vải (Item) / Style | DVDP-SAFM001-PA |
| oc_no | text | No | ≤ 40 | Số OC (cột "Số PO" của file NGC) | KDV20-GC-EX-0926-8643 |
| odno | text | No | ≤ 40 | ODNO | 2608-7041 |
| g_per_m | decimal | Yes | > 0 | Trọng lượng g/m (thành phẩm) | 245 |
| g_per_m2 | decimal | Yes | > 0 | Trọng lượng g/m2 (chọn nhóm WR ≤ 150 / > 150) | 167 |
| shrinkage | decimal | Yes | 0 ≤ x < 1 | Độ co do sales gõ | 1% |
| quantity_m | decimal | Yes | > 0 | Số lượng (m) | 7404 |
| job_price_vnd | decimal | Yes | > 0 | Đơn giá nhận gia công (đ/m) | 7905,40 |
| tcdn_dyeing | như 4.16 (nguyên liệu, cấp màu, tỷ trọng, phẩm nhuộm đặc biệt + giá, WR, công đoạn ngoài quy trình + giá hóa chất, tính năng đặc biệt) | Khi TCDN | | Lựa chọn nhuộm TCDN | Poly; Chuẩn Bị, Coating 1861, Cire, Kiểm Trung Gian, Kiểm Hàng-Đóng Gói; UPF50+ 868 |
| stage repeat_count | integer | No | 0..9 | Số lần xử lý thêm của từng công đoạn ngoài quy trình (TCDN) | Coating 1 |
| hcm_dyeing | như 4.15 | Khi HCM | | Lựa chọn nhuộm HCM | |
| quoted_items | 7 khoản mục đ/m (Hóa chất, Nhân công, Khấu hao, Điện, Nhiên liệu, Vật tư, CPQL) | No | ≥ 0 | "Báo giá riêng từng mặt hàng": có tổng > 0 thì thay toàn bộ phần tự tính | |

### 4.23 Kết quả phiếu gia công nhuộm (chỉ đọc, lưu cùng phiếu)
- Mỗi dòng: các dòng chi phí (công đoạn / tính năng, 7 khoản mục), hệ số chiết khấu / phụ phí, Tổng định mức (đ/m), Tổng định
  mức – TP (đ/m), Thành tiền chi phí, Thành tiền giá gia công, GP, %GP, cảnh báo.
- Tổng phiếu: Tổng số lượng, Tổng chi phí, Tổng giá gia công, GP, %GP; cờ "%GP dưới ngưỡng".

### 4.24 Hệ số vận hành công đoạn TCDN (Op. Rate to costing) (thêm 2026-11-25)
Bảng trong bộ tham số (4.6), SO sửa trên Màn hình 5, có ngày hiệu lực theo bộ tham số. Công đoạn không có trong bảng
= 1. Giá trị ban đầu (theo file NGC): In Truyền Nhiệt 0,3; Santa 0,4; Bonding 0,3; Raising 0,3; Brush 0,3; Buffing 0,3;
Shearing 0,3; Coating 0,6; Cire 0,7; Heavy Cire 0,7; Kiểm Trung Gian 1; Peach 0,3. Bộ tham số đã lưu chưa có bảng này
thì dùng giá trị ban đầu. Chỉ dùng cho phiếu gia công nhuộm (BR-93); costsheet thường không đổi.

## 5. Input / output files (File nhập / xuất)

Giới hạn chung cho mọi file nhập:
- định dạng .xlsx / .xls;
- ≤ 20 MB, ≤ 50.000 dòng dữ liệu;
- tên cột so sánh không dấu, không phân biệt hoa thường, bỏ khoảng trắng thừa;
- file sai định dạng, quá giới hạn hoặc thiếu cột bắt buộc thì bị từ chối cả file (BR-70), không lưu gì.

| ID | File | Direction | Format | Columns / placeholders |
|---|---|---|---|---|
| F-01 | Peace – Weaving control | in | .xlsx, sheet đầu tiên | Xem bảng F-01 bên dưới |
| F-02 | Peace – TCFNO STANDARD | in | .xlsx, sheet đầu tiên | Xem bảng F-02 bên dưới |
| F-03 | WFX – Weaving_Control_Report | in | .xlsx, sheet đầu tiên | Như F-01, không có 4 cột TCFNO_INST, TCFNO_NO, TCFNO_SEQ, TCFNO_YEAR; thêm Use, Remark, RAW_MATERIAL ở cuối |
| F-04 | WFX – TCFNO_Standard_Report | in | .xlsx, sheet đầu tiên | Như F-02, thêm cột TPM ở cuối |
| F-05 | Bộ định mức | in / out (file mẫu) | .xlsx, 13 sheet (sửa 2026-11-23: thêm sheet `Spandex`; file 12 sheet cũ vẫn nhận) | Xem bảng F-05 bên dưới |
| F-06 | Danh sách khách hàng | in | .xlsx, sheet đầu tiên | `Team`, `Customer` (bắt buộc); `Mã KH` (không bắt buộc, thiếu thì app tự tạo theo BR-50); cột khác bỏ qua; chỉ lấy dòng Team = FS1 hoặc FS2 |
| F-07 | Nhãn thông số vải | out | .docx | Xem bảng F-07 bên dưới |
| F-08 | Danh sách costsheet | out | .xlsx, sheet `Costsheet` | Đúng các cột của bảng ở Màn hình 1, theo bộ lọc đang chọn |
| F-09 | Bảng giá gia công nhuộm (thêm 2026-11-25) | out | .xlsx, sheet `Thông tin` + sheet `Output` | Sheet `Thông tin`: đầu phiếu (Số phiếu, Số hợp đồng, Khách hàng, Đơn vị gia công, Tỷ giá, Hình thức gia công "NHẬN GIA CÔNG", Ngày tính giá, Trạng thái). Sheet `Output`: dòng TỔNG CỘNG + mỗi dòng: STT, % Thành phẩm B C, Mã vải, Tên vải / Style, Số OC, ODNO, Nguyên liệu nhuộm, Cấp màu, Tổng các quy trình, Số lượng, Tổng định mức, Tổng định mức – TP, Đơn giá nhận GC, Thành tiền (chi phí), Thành tiền (giá GC), GP, %GP, 7 khoản mục (như sheet Output file NGC) |

**F-01 / F-03 – Weaving control**
- Dòng 1 là tiêu đề.
- F-01 có thêm dòng 2 (tiêu đề phụ) và dòng 3 (dòng tổng): bỏ qua mọi dòng không có TCFNO hoặc TCFNO không chứa
  chữ cái.
- Cột bắt buộc: `TCFNO`, `Fabric`.
- Các cột lấy theo tên: `Code`, `Structure`, `Fabric Kind`, `Fabric type`, `TCFNO Status`, `Date create` (yyyy/mm/dd ở
  Peace, dd/mm/yyyy ở WFX), `In-Charge`, `Remark` (chỉ WFX).
- Nhóm mộc là 13 cột bắt đầu từ cột `Before`, theo thứ tự: Width, Cut W., Weight (g/m2), G/Mt, Density Warp, Density
  Weft, Wale, Gause, Loop, Needle, SHR-Warp, SHR-Weft, Course.
- Nhóm TP là 13 cột bắt đầu từ cột `After`, cùng thứ tự.
- Ví dụ dòng: `EM35780026 | WFTW-EM-03556 | TC34/2(65/35)SE800+CTRANG+DTY75D/36F/1+DTY 300D/96F/1SIM | EM | Export MULTI
  YARN | WOVEN FABRIC | | | 08/07/2026 | | 175 | 175 | 202.29 | 354 | 344 | 205 | … | 7.5 | 5 | …`

**F-02 / F-04 – TCFNO Standard**
- Các cột theo vị trí (vì có tên trùng):
  1. TCFNO
  2. YARN (hướng)
  3. TCFNO-YARN
  4. CONDITIONS
  5. SEARCH
  6. FCODE
  7. CSP
  8. Code
  9. FNAME
  10. YCODE
  11. YNAME
  12. Direction (số)
  13. Rate
  14. Direction (chữ)
  15. YSEL_TCFNO_YARN
  16. Loai soi
  17. YCODE (gốc)
  18. YNAME (gốc)
  19. RATE (gốc)
  20. TPM (chỉ F-04)
- Bắt buộc: cột 1, 2, 11, 13.
- Ví dụ dòng: `ED27110020 | WARP | ED27110020-WARP | | | | 2 | 062940 | DTY150D/48F/1-HIM … | 005679 | TC 50/2 (65/35) -
  800T/M YD | 1 | 2.38 | Soi doc | 2 | Soi se | 004311 | TC 50/1 (65/35) | 100`

**F-05 – Bộ định mức** (1 file, 12 sheet; tiêu đề ở dòng 1; app tạo file mẫu điền sẵn số của bộ đang hiệu lực)

| Sheet | Cột (đúng thứ tự) |
|---|---|
| `DonGiaPhut` | Công đoạn, Tốc độ máy BQ, Số cọc BQ, Chu vi guồng, Thời gian hoạt động (phút), Nhân công, Khấu hao, Điện, Vật tư, Nhiên liệu, CPQL |
| `ThamSoSe` | Tham số, Filament, Xơ ngắn (7 dòng của 4.5.2) + dòng `Tổng nhân sự Se`, `Số giờ làm/ngày` |
| `ThamSoMacKiem` | Tham số, Giá trị (Tổng canh chuẩn, Số nhịp chuẩn, Hệ số sợi dọc có se, Tốc độ kiểm hàng bán mộc, Tốc độ kiểm hàng giao nhuộm) |
| `DinhMucHo` | Nguyên liệu hồ, Nhóm tổng canh, Nhân công, Khấu hao, Điện, Vật tư, Nhiên liệu, CPQL, Hóa chất |
| `DinhMucDet` | Mật độ ngang, Nhân công, Khấu hao, Điện, Vật tư, Nhiên liệu, CPQL |
| `ChiSo` | Hệ sợi, Chi số, Chi số chuyển đổi; và bảng `Độ săn` ở cột E |
| `NhuomHCM_TieuChuan` | Loại vải, Cấp màu, HCTN, Tiền lương, Khấu hao, Điện, Nhiên liệu, Vật tư, Quản lý |
| `NhuomHCM_CongDoan` | Công đoạn, HCTN, Tiền lương, Khấu hao, Điện, Nhiên liệu, Vật tư, Quản lý, Tiêu hao (%) |
| `NhuomHCM_TinhNang` | Tính năng, Loại vải, Hóa chất sử dụng, HCTN, Tiền lương, Khấu hao, Điện, Nhiên liệu, Vật tư, Quản lý |
| `NhuomTCDN_QuyTrinh` | Mã quy trình, Thành phần nhuộm, Nguyên liệu nhuộm, Cấp màu, Quy trình chuẩn, Hóa chất, Nhân công, Khấu hao, Điện, Nhiên liệu, Vật tư, CPQL, Xưởng, Tiêu hao (%) |
| `NhuomTCDN_HoaChat` | Khóa, Nhóm trọng lượng (1/2/rỗng), Chi phí hóa chất (đ/m vải 250 g/m) |
| `DanhMuc` | Loại danh mục, Giá trị |
| `Spandex` (thêm 2026-11-23) | Loại spandex, Cộng thêm (ví dụ: 40, 16) |

Thiếu sheet `Spandex` (file 12 sheet cũ): bảng spandex lấy từ bộ đang hiệu lực. Mọi ô số phải là số ≥ 0; mỗi khóa (cột đầu, hoặc 2 cột đầu) không trùng trong sheet (BR-63).

**F-07 – Nhãn thông số vải** (Word, giống sheet PRINT: tối đa 4 nhãn / trang, 2 cột × 2 hàng; mỗi nhãn 1 mã vải)

| Placeholder (mỗi nhãn) | Nguồn |
|---|---|
| `{{tcfno}}` | 4.1 tcfno |
| `{{fabric_name}}` | 4.1 fabric_name (FABRIC) |
| `{{yarn_lines}}` | YARN SPEC: tối đa 6 dòng Warp rồi 6 dòng Weft; mỗi dòng: hướng, tên sợi (4.2 yarn_name), tỷ lệ = rate ÷ 100 × raw_rate ÷ 100 (hiện %) |
| `{{width_cm}}`, `{{width_inch}}` | WIDTH: khổ thành phẩm (cm) và round(khổ ÷ 2,54, 0) INCH |
| `{{gsm}}`, `{{g_per_m}}` | WEIGHT: g/m2 thành phẩm và g/m thành phẩm (G/MT) |
| `{{warp_density}}`, `{{weft_density}}` | DENSITY WARP / WEFT thành phẩm (/10 cm) |
| `{{remark}}` | REMARK: người in nhập khi in (có thể trống) |

Thông số lấy theo BR-75.

## 6. Use cases (Nghiệp vụ)

### UC-01: Kiểm tra dữ liệu vải Peace / WFX (chưa lưu)
- **Actor:** SO
- **Trigger:** chọn 1-4 file F-01..F-04 và bấm "Kiểm tra".
- **Preconditions:** có ít nhất 1 file Weaving control (F-01 hoặc F-03) hoặc 1 file TCFNO Standard (F-02 hoặc F-04).
- **Input:** các file; app nhận loại file theo tiêu đề cột (F-01/F-03 có cột `Before`; F-02/F-04 có cột `YNAME`; WFX
  nhận ra khi không có cột `TCFNO_INST` hoặc có cột `TPM`).
- **Main flow:**
  1. Đọc từng file, kiểm tra BR-70.
  2. Làm sạch mã (BR-02), chuẩn hóa hướng sợi, loại sợi, sợi gốc, độ săn (BR-04).
  3. Gộp theo BR-01 (ưu tiên Peace).
  4. So với dữ liệu đang lưu: mã mới / mã thay đổi / không đổi.
  5. Liệt kê mã thiếu sợi (có thông số nhưng không có dòng sợi) và mã có tổng tỷ lệ sợi khác 100% (BR-05).
- **Output:** số mã đọc được theo từng file; số mã mới / thay đổi / không đổi / thiếu sợi / lỗi; bảng chi tiết (mã, tên
  vải, nguồn, kết quả, lý do).
- **Errors:** file sai: "File <tên> không đúng mẫu: thiếu cột <tên cột>." Không có dòng hợp lệ: "Không đọc được mã vải
  nào trong file <tên>."
- **Rules applied:** BR-01, BR-02, BR-04, BR-05, BR-70

### UC-02: Lưu dữ liệu vải
- **Actor:** SO
- **Trigger:** sau UC-01, bấm "Lưu N mã".
- **Main flow:**
  1. Chạy lại UC-01.
  2. Tạo mã mới, cập nhật mã thay đổi (kể cả mã nhập tay trước đó, BR-01).
  3. Giữ nguyên độ co mắc đã có; mã mới lấy độ co mắc mặc định.
  4. Ghi nhật ký 4.3.
- **Output:** "Đã lưu: M mã mới, C mã cập nhật. S mã thiếu sợi cần kiểm tra."
- **Errors:** như UC-01.
- **Rules applied:** BR-01, BR-02, BR-03, BR-04, BR-71

### UC-03: Nhập nhanh / sửa mã vải
- **Actor:** SO, PD
- **Trigger:** bấm "Thêm mã vải" hoặc chọn 1 mã rồi "Sửa".
- **Input:**
  - các trường 4.1 (bắt buộc: tcfno, fabric_name, khổ mộc, mật độ dọc / ngang mộc, g/m mộc; với vải bán thành phẩm cần
    thêm khổ, mật độ, g/m TP);
  - danh sách sợi 4.2 (hướng, tên sợi, tỷ lệ %, loại sợi, sợi gốc, tỷ lệ sợi gốc, độ săn);
  - độ co mắc.
- **Main flow:**
  1. Kiểm tra BR-02, BR-05.
  2. Lưu với source = "Nhập tay" (khi thêm) hoặc giữ source (khi sửa).
  3. Ghi người sửa.
- **Output:** "Đã lưu mã vải <tcfno>."
- **Errors:** "Mã vải <tcfno> đã có. Hãy dùng chức năng Sửa." / thông báo của BR-02, BR-05.
- **Rules applied:** BR-02, BR-05, BR-72

### UC-04: Tra cứu mã vải
- **Actor:** SO, PD, Sales, Trưởng team, Trưởng đơn vị
- **Input:** từ khóa (mã hoặc tên vải), nguồn, có / không có sợi.
- **Output:** danh sách mã vải; chọn 1 mã để xem thông số và các dòng sợi.

### UC-05: Cập nhật tỷ giá tháng
- **Actor:** SO
- **Input:** tháng, năm, tỷ giá.
- **Main flow:** kiểm tra BR-60; thêm mới hoặc sửa tỷ giá tháng đó.
- **Output:** "Đã lưu tỷ giá tháng MM/YYYY: <tỷ giá>." Costsheet đã gửi duyệt / đã duyệt không đổi (BR-39).
- **Rules applied:** BR-39, BR-60

### UC-06: Tải file mẫu bộ định mức
- **Actor:** SO
- **Output:** file F-05 điền sẵn số của bộ định mức đang hiệu lực hôm nay; tên `bo-dinh-muc-<YYYYMMDD>.xlsx`.

### UC-07: Kiểm tra và lưu bộ định mức mới
- **Actor:** SO
- **Input:** file F-05, ngày hiệu lực, ghi chú.
- **Main flow:**
  1. Đọc 12 sheet (và sheet `Spandex` nếu có), kiểm tra BR-63, BR-70.
  2. Hiện số dòng từng sheet và các ô thay đổi so với bộ đang hiệu lực.
  3. SO bấm "Lưu bộ định mức" -> tạo 4.5.
- **Output:** "Đã lưu bộ định mức <mã>, hiệu lực từ dd/mm/yyyy."
- **Errors:** BR-63, BR-64, BR-70.
- **Rules applied:** BR-39, BR-62, BR-63, BR-64, BR-70

### UC-08: Xem bộ định mức
- **Actor:** SO, Sales, Trưởng team, Trưởng đơn vị
- **Input:** chọn bộ (mặc định bộ đang hiệu lực).
- **Output:** các bảng 4.5.1..4.5.12 của bộ đó.

### UC-09: Cập nhật bộ tham số chung
- **Actor:** SO
- **Input:** các trường 4.6 và ngày hiệu lực.
- **Main flow:** kiểm tra BR-64, BR-65; tạo bộ mới (không sửa bộ cũ đã có costsheet dùng).
- **Output:** "Đã lưu bộ tham số hiệu lực từ dd/mm/yyyy."
- **Rules applied:** BR-39, BR-64, BR-65

### UC-10: Quản lý hệ số theo mã hàng
- **Actor:** SO
- **Input:** các trường 4.7.
- **Main flow:** thêm / sửa / ngừng dùng (active = No). Không xóa hẳn.
- **Output:** "Đã lưu hệ số cho mã <tcfno>."
- **Rules applied:** BR-24

### UC-11: Quản lý ngày lễ
- **Actor:** SO
- **Input:** ngày, tên.
- **Main flow:** thêm / xóa (xóa dùng cờ xóa, khôi phục được).
- **Rules applied:** BR-44

### UC-12: Tải danh sách khách hàng ban đầu
- **Actor:** SO
- **Input:** file F-06.
- **Main flow:**
  1. Lấy dòng Team = FS1 / FS2.
  2. Bỏ dòng có tên chứa "TEAM FORECAST".
  3. Chuẩn hóa tên, bỏ trùng; lấy hoặc tự tạo mã KH (BR-50).
  4. Hiện danh sách xem trước (tên, mã KH, team); SO bấm "Lưu".
- **Output:** "Đã thêm N khách hàng, bỏ qua M tên trùng."
- **Rules applied:** BR-50, BR-70

### UC-13: Sửa khách hàng
- **Actor:** SO
- **Input:** khách hàng, tên mới, mã KH mới, team, đang dùng.
- **Main flow:**
  1. Kiểm tra BR-50.
  2. Cập nhật.
  3. Mọi costsheet Nháp / Trả lại dùng tên cũ được đổi sang tên mới; costsheet khác giữ tên đã lưu. Số costsheet đã
     tạo không đổi khi mã KH đổi.
- **Output:** "Đã cập nhật khách hàng <tên mới>."
- **Rules applied:** BR-50

### UC-14: Sửa thông số vải trên costsheet (mã nhập tay)
- **Actor:** Sales, Trưởng team (chủ phiếu)
- **Preconditions:** phiếu Nháp / Trả lại; mã vải có nguồn "Nhập tay" (chưa có trong file Peace / WFX đã tải).
- **Input:** khổ, mật độ dọc / ngang, g/m, g/m2 (mộc và TP), độ co mắc, các dòng sợi (tên, tỷ lệ, loại sợi, độ săn).
- **Main flow:**
  1. Kiểm tra BR-47, BR-05.
  2. Lưu vào bản chụp thông số của phiếu (không đổi dữ liệu gốc 4.1, 4.2).
  3. Đặt fabric_overridden = Yes; tính lại (UC-16).
- **Output:** "Đã cập nhật thông số vải cho costsheet <số>."
- **Errors:** "Mã vải <tcfno> lấy từ dữ liệu gốc Peace / WFX, không được sửa thông số."
- **Rules applied:** BR-05, BR-47

### UC-15: Tạo costsheet mới
- **Actor:** Sales, Trưởng team
- **Trigger:** bấm "Tạo costsheet".
- **Input:** nhà máy nhuộm, khách hàng, thị trường, loại đơn hàng, style, hình thức bán, ngày giao, ngày tính giá, mã vải,
  số mét, loại giá (OC có thể nhập sau).
- **Main flow:**
  1. Kiểm tra BR-03, BR-61, BR-62.
  2. Lấy thông số vải, dòng sợi (BR-05), gợi ý Se / Hồ (BR-06..BR-09).
  3. Lấy định mức, tham số mặc định.
  4. Tạo bản Nháp v1 với số costsheet mới (BR-41).
  5. Tính (UC-16).
- **Output:** màn hình costsheet ở trạng thái Nháp.
- **Errors:**
  - Mã vải không có: "Mã vải <tcfno> chưa có trong dữ liệu gốc. Liên hệ SO hoặc PD nhập nhanh mã này."
  - Chưa có tỷ giá: thông báo BR-61.
- **Rules applied:** BR-03, BR-05..BR-09, BR-41, BR-61, BR-62, BR-91 (thêm 2026-11-25)

### UC-16: Tính / tính lại costsheet
- **Actor:** Sales, Trưởng team
- **Trigger:** tự chạy mỗi khi sales đổi một ô / một lựa chọn trên phiếu (ô trong bảng: khi rời ô), và khi lưu (sửa
  2026-11-23: trước đây phải bấm nút "Tính lại"; nút này bỏ). Kết quả tự tính chưa được lưu; màn hình hiện "Có thay đổi
  chưa lưu" tới khi bấm "Lưu nháp".
- **Preconditions:** costsheet ở trạng thái Nháp hoặc Trả lại.
- **Main flow:**
  1. Lấy lại tỷ giá, bộ định mức, bộ tham số theo ngày tính giá (BR-61, BR-62).
  2. Lấy lại thông số vải hiện tại (trừ khi fabric_overridden = Yes thì giữ thông số sales đã sửa).
  3. Áp dụng các giá trị sales đã sửa (4.18).
  4. Tính BR-10..BR-29 (thêm 2026-11-26: trước bước Ngành Dệt, cập nhật bảng cone theo BR-100).
  5. Lập danh sách cảnh báo BR-80.
- **Output:** toàn bộ kết quả 4.20 và cảnh báo.
- **Rules applied:** BR-10..BR-29, BR-45, BR-46, BR-61, BR-62, BR-80, BR-89, BR-90 (thêm 2026-11-25), BR-100 (thêm
  2026-11-26)

### UC-17: Lưu nháp
- **Actor:** Sales (chủ phiếu), Trưởng team (chủ phiếu)
- **Preconditions:** Nháp hoặc Trả lại.
- **Main flow:**
  1. Kiểm tra định dạng các ô nhập (không bắt đủ dữ liệu).
  2. Tính (UC-16) và lưu.
  3. Phiếu Trả lại chuyển về Nháp.
- **Output:** "Đã lưu nháp costsheet <số> v<phiên bản>."
- **Rules applied:** BR-31, BR-34

### UC-18: Thêm khách hàng mới
- **Actor:** Sales, Trưởng team, SO
- **Trigger:** gõ tên không có trong danh sách và bấm "Thêm khách hàng".
- **Main flow:**
  1. App tìm tối đa 10 tên tương tự (BR-50).
  2. Sales chọn 1 tên có sẵn, hoặc nhập mã KH (app gợi ý sẵn theo BR-50) và bấm "Xác nhận tạo mới".
  3. Khách hàng mới dùng được ngay, team = team của người tạo.
- **Output:** "Đã thêm khách hàng <tên>."
- **Errors:** "Khách hàng <tên> đã có." (trùng sau chuẩn hóa).
- **Rules applied:** BR-50

### UC-19: Sao chép costsheet
- **Actor:** Sales, Trưởng team
- **Preconditions:** người dùng xem được phiếu nguồn (BR-52); phiếu nguồn ở bất kỳ trạng thái nào.
- **Main flow:**
  1. Tạo costsheet mới (số mới, v1, Nháp) với mọi ô nhập của phiếu nguồn.
  2. Đặt người lập = người sao chép, team = team của người đó.
  3. Ngày tính giá = hôm nay. OC, lý do trả lại / hủy để trống.
  4. Giữ giá sợi và ngày nhập giá sợi của phiếu nguồn (BR-44 sẽ kiểm tra khi gửi duyệt).
  5. Tính theo UC-16 (tỷ giá, định mức, tham số mới nhất).
  6. Ghi copied_from.
- **Output:** "Đã tạo costsheet <số mới> từ <số nguồn> v<n>." và mở phiếu mới.
- **Rules applied:** BR-41, BR-44, BR-62

### UC-20: Gửi duyệt
- **Actor:** Sales (chủ phiếu), Trưởng team (chủ phiếu)
- **Preconditions:** Nháp hoặc Trả lại.
- **Main flow:**
  1. Tính (UC-16).
  2. Kiểm tra đủ dữ liệu (BR-42), giá sợi còn hiệu lực (BR-44), lý do độ co (BR-14), dữ liệu nhuộm (BR-43).
  3. Lỗi chặn thì dừng và liệt kê.
  4. Cảnh báo GP / OP (BR-28) chỉ hiện, không chặn.
  5. Nếu là phiên bản ≥ 2 và BR-35 thỏa thì chuyển thẳng Đã duyệt (Duyệt tự động); ngược lại chuyển Chờ duyệt.
- **Output:**
  - "Đã gửi duyệt costsheet <số> v<n>. Người duyệt: <trưởng team team X> hoặc trưởng đơn vị.", hoặc
  - "Phiên bản <n> không thay đổi giá so với phiên bản đã duyệt nên được duyệt tự động."
- **Errors:** danh sách thông báo BR-42, BR-43, BR-44, BR-14.
- **Rules applied:** BR-14, BR-28, BR-30, BR-35, BR-42, BR-43, BR-44, BR-53

### UC-21: Duyệt costsheet
- **Actor:** Trưởng team (team của phiếu), Trưởng đơn vị
- **Preconditions:** Chờ duyệt; người duyệt có quyền theo BR-53.
- **Main flow:** xem phiếu, kể cả các ô tô màu (BR-14, BR-46, BR-28); bấm "Duyệt" -> Đã duyệt; ghi người, lúc duyệt.
- **Output:** "Đã duyệt costsheet <số> v<n>."
- **Rules applied:** BR-32, BR-53

### UC-22: Trả lại costsheet
- **Actor:** Trưởng team, Trưởng đơn vị
- **Preconditions:** Chờ duyệt.
- **Input:** lý do (bắt buộc).
- **Main flow:** chuyển Trả lại; lưu lý do.
- **Output:** "Đã trả lại costsheet <số> v<n>."
- **Errors:** "Vui lòng nhập lý do trả lại."
- **Rules applied:** BR-33, BR-53

### UC-23: Tạo phiên bản mới
- **Actor:** Sales (chủ phiếu), Trưởng team (chủ phiếu)
- **Preconditions:** phiên bản mới nhất ở trạng thái Đã duyệt hoặc Đã chốt đơn.
- **Main flow:**
  1. Tạo phiên bản n+1 ở trạng thái Nháp, chép mọi ô nhập.
  2. Ngày tính giá giữ nguyên; sales sửa được.
  3. Phiên bản n giữ nguyên trạng thái tới khi phiên bản n+1 được duyệt; khi đó phiên bản n chuyển Đã thay thế.
- **Output:** "Đã tạo phiên bản <n+1> của costsheet <số>."
- **Rules applied:** BR-35, BR-37

### UC-24: Nhập / sửa OC và chốt đơn
- **Actor:** Sales (chủ phiếu), Trưởng team (chủ phiếu)
- **Input:** số OC.
- **Main flow:**
  1. Kiểm tra BR-40.
  2. Ở Nháp / Trả lại / Chờ duyệt / Đã duyệt: lưu OC, không cần duyệt lại (BR-35).
  3. Bấm "Chốt đơn" (chỉ khi Đã duyệt và có OC) -> Đã chốt đơn.
  4. Ở Đã chốt đơn vẫn được sửa OC (ghi lịch sử "Sửa OC").
- **Output:** "Đã chốt đơn costsheet <số> với OC <OC>."
- **Errors:** BR-40.
- **Rules applied:** BR-36, BR-40

### UC-25: Hủy costsheet
- **Actor:** Sales (chủ phiếu), Trưởng team (chủ phiếu)
- **Preconditions:** trạng thái khác Đã chốt đơn, Hủy, Đã thay thế.
- **Input:** lý do (bắt buộc).
- **Main flow:** chuyển Hủy; phiếu chỉ còn xem / sao chép.
- **Output:** "Đã hủy costsheet <số> v<n>."
- **Errors:** "Vui lòng nhập lý do hủy." / "Costsheet đã chốt đơn không hủy được."
- **Rules applied:** BR-36

### UC-26: In nhãn thông số vải
- **Actor:** Sales, Trưởng team, Trưởng đơn vị, SO, PD
- **Trigger:** "In nhãn" trên costsheet (mã vải của phiếu), hoặc trên màn hình mã vải (nhập 1-4 mã vải).
- **Input:** mã vải, REMARK cho từng nhãn (không bắt buộc).
- **Output:** file F-07 `nhan-<tcfno đầu tiên>.docx`, tối đa 4 nhãn trên 1 trang.
- **Errors:** "Mã vải <tcfno> chưa có trong dữ liệu gốc."
- **Rules applied:** BR-75

### UC-27: Danh sách costsheet
- **Actor:** mọi vai trò (theo BR-52)
- **Input:** từ khóa (số costsheet, mã vải, OC, style), trạng thái, team, sales, khách hàng, nhà máy nhuộm, loại đơn,
  loại giá, khoảng ngày tính giá, "chỉ phiên bản mới nhất" (mặc định bật), "chỉ dưới ngưỡng GP / OP".
- **Output:** bảng ở Màn hình 1, kèm số liệu tổng hợp.
- **Rules applied:** BR-28, BR-52

### UC-28: Xuất danh sách costsheet ra Excel
- **Actor:** như UC-27
- **Output:** file F-08 `danh-sach-costsheet-<YYYYMMDD>.xlsx` theo bộ lọc đang chọn.

### UC-29: Xem costsheet
- **Actor:** mọi vai trò (theo BR-52)
- **Output:** toàn bộ costsheet (chỉ đọc nếu không được sửa), các phiên bản, lịch sử 4.19, các ô tô màu.
- **Rules applied:** BR-14, BR-28, BR-38, BR-39, BR-46, BR-52

### UC-30: Việc chờ tôi
- **Actor:** mọi vai trò
- **Output:**
  - Người duyệt: costsheet Chờ duyệt thuộc quyền duyệt.
  - Sales: phiếu của mình ở trạng thái Trả lại; phiếu Đã duyệt chưa có OC; phiếu Nháp có giá sợi hết hiệu lực
    (BR-44).
  - SO: tháng hiện tại chưa có tỷ giá; mã vải thiếu sợi.
- **Rules applied:** BR-44, BR-53

### UC-31: Xem danh sách tỷ giá
- **Actor:** SO
- **Output:** các tháng đã nhập (Tháng, Năm, Tỷ giá, Người cập nhật, Lúc cập nhật), mới nhất trên cùng.

### UC-32: Xem các bộ tham số chung
- **Actor:** SO, Sales, Trưởng team, Trưởng đơn vị
- **Output:** danh sách bộ tham số theo ngày hiệu lực và giá trị của bộ mới nhất (điền sẵn form UC-09).

### UC-33: Xem hệ số theo mã hàng
- **Actor:** SO
- **Output:** bảng 4.7.

### UC-34: Xem ngày lễ
- **Actor:** SO
- **Output:** bảng 4.8.

### UC-35: Tra cứu khách hàng
- **Actor:** SO, Sales, Trưởng team, Trưởng đơn vị
- **Input:** từ khóa.
- **Output:** bảng 4.9.

### UC-36: Xem trước danh sách khách hàng (chưa lưu)
- **Actor:** SO
- **Input:** file F-06.
- **Main flow:** bước 1-3 của UC-12, không lưu.
- **Output:** danh sách (tên, mã KH, team, kết quả: thêm / trùng).
- **Rules applied:** BR-50, BR-70

### UC-37: Kiểm tra bộ định mức (chưa lưu)
- **Actor:** SO
- **Input:** file F-05, ngày hiệu lực.
- **Main flow:** bước 1-2 của UC-07, không lưu.
- **Output:** số dòng từng sheet, ô thay đổi so với bộ đang hiệu lực, danh sách lỗi.
- **Rules applied:** BR-63, BR-64, BR-70

### UC-38: Lấy danh mục cho costsheet
- **Actor:** Sales, Trưởng team, Trưởng đơn vị, SO
- **Output:** khách hàng đang dùng, các danh sách chọn (4.5.6, 4.5.12, loại vải, cấp màu…), vai trò và team của người
  đang đăng nhập.

### UC-39: Xem lịch sử cập nhật dữ liệu vải
- **Actor:** SO
- **Output:** 5 lần cập nhật gần nhất (4.3).

### UC-40: Tạo phiếu gia công nhuộm (thêm 2026-11-25)
- **Actor:** Sales, Trưởng team, SO
- **Trigger:** Màn hình 8, bấm "Tạo phiếu gia công".
- **Input:** khách hàng, số hợp đồng, đơn vị gia công (mặc định TCDN), ngày tính giá.
- **Main flow:** kiểm tra BR-61, BR-62; tạo phiếu Nháp số mới (BR-96) với 1 dòng trống; team như BR-51.
- **Output:** phiếu Nháp mở trên Màn hình 8.
- **Rules applied:** BR-51, BR-61, BR-62, BR-96

### UC-41: Tính phiếu gia công nhuộm (thêm 2026-11-25)
- **Actor:** Sales, Trưởng team, SO
- **Trigger:** tự chạy mỗi khi sửa một ô (như UC-16), và khi lưu.
- **Main flow:** lấy tỷ giá, bộ định mức, bộ tham số theo ngày tính giá; tính từng dòng theo BR-92..BR-94; tính tổng
  BR-95; lập cảnh báo.
- **Output:** kết quả 4.23 (chưa lưu, hiện "Có thay đổi chưa lưu").
- **Rules applied:** BR-25, BR-26, BR-61, BR-62, BR-92, BR-93, BR-94, BR-95

### UC-42: Lưu nháp phiếu gia công nhuộm (thêm 2026-11-25)
- **Actor:** chủ phiếu, SO
- **Main flow:** kiểm tra BR-97 (dữ liệu dòng hợp lệ); tính (UC-41); lưu phiếu, dòng, kết quả; phiếu Trả lại chuyển về Nháp.
- **Rules applied:** BR-31, BR-34, BR-97

### UC-43: Gửi duyệt / duyệt / trả lại / hủy phiếu gia công nhuộm (thêm 2026-11-25)
- **Actor:** chủ phiếu (gửi, hủy); người duyệt theo BR-53 (duyệt, trả lại)
- **Main flow:** gửi duyệt khi đủ dữ liệu (BR-98) -> Chờ duyệt; duyệt / trả lại (lý do) / hủy (lý do) **cho cả phiếu 1 lần**;
  phiếu Chờ duyệt, Đã duyệt, Hủy không tính lại, giữ số đã lưu.
- **Rules applied:** BR-32, BR-33, BR-36 (phần lý do hủy), BR-52, BR-53, BR-98, BR-99

### UC-44: Danh sách phiếu gia công nhuộm (thêm 2026-11-25)
- **Actor:** Sales, Trưởng team, Trưởng đơn vị, SO
- **Output:** các phiếu được phép xem (BR-52): Số phiếu, Ngày tính giá, Khách hàng, Số hợp đồng, Đơn vị gia công, Số dòng,
  Tổng số lượng, Tổng giá GC, GP, %GP, Trạng thái, Sales, Người duyệt; lọc theo từ khóa (số phiếu / hợp đồng / mã hàng /
  OC), trạng thái, khách hàng, khoảng ngày.
- **Rules applied:** BR-52

### UC-45: Sao chép phiếu gia công nhuộm (thêm 2026-11-25)
- **Actor:** Sales, Trưởng team, SO
- **Main flow:** tạo phiếu Nháp mới (số mới BR-96, ngày tính giá hôm nay) với đầu phiếu và mọi dòng của phiếu gốc; tính lại.
- **Rules applied:** BR-96

### UC-46: Xuất bảng giá gia công nhuộm ra Excel (thêm 2026-11-25)
- **Actor:** ai xem được phiếu
- **Output:** file F-09 `gia-cong-<số phiếu>.xlsx` theo kết quả đang hiện.

## 7. Business rules (Quy tắc nghiệp vụ)
| ID | Rule | Error message shown to user (VI) |
|---|---|---|
| BR-01 | **Gộp Peace / WFX:** cùng 1 tcfno sau làm sạch có ở cả Peace và WFX thì lấy toàn bộ thông số và sợi từ Peace; chỉ có ở WFX thì lấy WFX. Mã đang có nguồn "Nhập tay" được ghi đè bởi dữ liệu file. Mã đang lưu nhưng không có trong file thì giữ nguyên | - |
| BR-02 | **Làm sạch TCFNO:** bỏ khoảng trắng; nếu ký tự đầu là "G" thì bỏ ký tự đó; bỏ mọi dấu chấm; tcfno = 10 ký tự đầu (in hoa); phần còn lại = sy_item. Kết quả phải đủ 10 ký tự, chỉ chữ in hoa và số. (sửa 2026-11-25: chỉ bỏ chữ "G" đầu khi mã sau khi bỏ khoảng trắng, dấu chấm dài hơn 10 ký tự; trước đây luôn bỏ, nên mã như GC12345678 bị báo sai. Thông báo giữ nguyên như cũ) | Mã vải "<mã>" không hợp lệ: cần đủ 10 ký tự chữ và số. |
| BR-03 | Mã vải trên costsheet phải có trong 4.1 | Mã vải <tcfno> chưa có trong dữ liệu gốc. Liên hệ SO hoặc PD nhập nhanh mã này. |
| BR-04 | **Chuẩn hóa sợi:** raw_yarn_code rỗng / 0 -> yarn_code; raw_yarn_name rỗng -> yarn_name; raw_rate rỗng / 0 -> 100. Độ săn: lấy cụm số đứng trước "T/M" (không phân biệt hoa thường) trong yarn_name, ví dụ "800T/M"; WFX dùng cột TPM nếu khác 0. Thứ tự seq đánh lại 1, 2, … theo thứ tự dòng trong mỗi tcfno + hướng | - |
| BR-05 | **Tỷ lệ sợi trên costsheet:** ratio = rate × raw_rate ÷ 10.000. Tổng ratio mọi dòng phải = 1 (sai lệch ≤ 0,0001) | Tỷ lệ sợi không đúng (tổng = <x>%). Vui lòng kiểm tra lại mã vải với SO / PD. |
| BR-06 | **Gợi ý Se:** dòng sợi có độ săn (twist_tpm khác rỗng) -> is_twisted gợi ý = Yes; sales sửa được | - |
| BR-07 | **Gợi ý Hồ – theo tên vải:** fabric_name (in hoa) có "HO" đứng riêng (trước và sau không phải chữ cái), hoặc chứa "SIMHO", hoặc "HOSOI" -> gợi ý Hồ, lý do "Tên vải có HO". Các từ chứa HO dính chữ khác (ví dụ "KHONG") không tính | - |
| BR-08 | **Gợi ý Hồ – theo sợi dọc**, chỉ xét sợi WARP; xét yarn_name và raw_yarn_name in hoa. Sợi là filament khi tên có số liền chữ D (ví dụ 75D, 150D/48F) hoặc chứa DTY, FDY, ATY, POY, NYLON; còn lại là spun. Gợi ý Hồ khi có ít nhất 1 sợi dọc: (a) spun có chi số ≥ 50 (chi số = số đứng trước dấu "/" đầu tiên của raw_yarn_name, ví dụ TC 50/1 -> 50), lý do "Sợi spun chi số ≥ 50"; (b) spun là Sợi đơn và không có độ săn, lý do "Sợi spun không se"; (c) filament có từ SIM hoặc NIM, lý do "Filament SIM/NIM". Filament chỉ có HIM không gợi ý | - |
| BR-09 | **Áp dụng Hồ:** gợi ý Hồ (BR-07 hoặc BR-08) thì tick Hồ cho **tất cả** dòng sợi dọc kèm lý do; sales bỏ tick được (bỏ là bỏ cho mọi sợi dọc). Sợi ngang không có tick Hồ | - |
| BR-10 | **Thông số dùng tính:** khổ mộc W, mật độ dọc mộc, mật độ ngang mộc / TP, g/m mộc / TP từ fabric_snapshot. m/kg mộc = 1000 ÷ g/m mộc; m/kg TP = 1000 ÷ g/m TP (0 nếu g/m TP = 0) | Mã vải <tcfno> thiếu <thông số>. Liên hệ SO / PD bổ sung. |
| BR-11 | **Tiêu hao sợi dọc** = warp_loss_base + warp_loss_twist × (Se ? 1 : 0) + warp_loss_size × (Hồ ? 1 : 0). Ví dụ 0,82% + 1% + 2,06% = 3,88% | - |
| BR-12 | **Tiêu hao sợi ngang** theo khổ mộc W và tick Se, nội suy tuyến tính từ weft_loss_table. Có Se: W = 175 -> 5,47%; W < 175 -> 6,77% − (6,77% − 5,47%) ÷ 45 × (W − 130); W > 175 -> 5,47% − (5,47% − 4,77%) ÷ 40 × (W − 175). Không Se: dùng 5,75%, 4,45%, 3,75% theo cùng công thức | - |
| BR-13 | **Độ co** = (mật độ ngang TP − mật độ ngang mộc) ÷ mật độ ngang TP; = 0 khi Hình thức bán = Mộc, khi mật độ ngang TP = 0, hoặc khi shrinkage_exception = "Mộc khách đã ổn định" (sửa 2026-11-25: Gia công dệt cũng = 0 như Mộc) | - |
| BR-14 | **Kiểm tra độ co:** khi Hình thức bán ≠ Mộc và độ co ≤ min_shrinkage (5%) thì sales phải chọn shrinkage_exception ≠ "Không" hoặc nhập shrinkage_reason. Phiếu có độ co ≤ 5% hoặc có ngoại lệ được tô màu cho người duyệt và đánh dấu "Độ co thấp / bằng 0" trong danh sách (sửa 2026-11-25: không kiểm tra khi Gia công dệt, như Mộc) | Độ co <x>% không lớn hơn 5%. Vui lòng chọn lý do ngoại lệ hoặc ghi lý do. |
| BR-15 | **Pre-setting:** shrinkage_exception = "Có pre-setting" chỉ là lý do cho độ co thấp (BR-14); mọi công thức tính như bình thường (quy tắc tính riêng cho pre-setting chưa chốt) | - |
| BR-16 | **% B/C:** %B/C mộc = greige_bc_rate_grey nếu Mộc, ngược lại greige_bc_rate_other; %B/C TP = finished_bc_rate_grey nếu Mộc, ngược lại finished_bc_rate_other. (sửa 2026-11-25: lấy theo bảng % B/C 4.6.2 của bộ tham số, dòng đúng hình thức bán) (sửa 2026-11-25, gia công: bộ chưa có dòng Gia công dệt / Gia công nhuộm thì lấy dòng Mộc / Vải Nhuộm) | - |
| BR-17 | **Tiêu hao nhuộm (E41):** Mộc -> 0. HCM: có chi phí phát sinh -> dye_loss_rate; ngược lại dye_loss_rate + tổng tiêu hao các công đoạn đặc biệt. TCDN: có chi phí phát sinh -> extra_cost_loss_rate; ngược lại (tcdn_standard_dye_loss nếu đã chọn nguyên liệu và cấp màu, không thì 0) + tổng tiêu hao công đoạn ngoài quy trình + tổng tiêu hao gia công ngoài (sửa 2026-11-25: Gia công dệt -> 0 như Mộc; Gia công nhuộm tính như Vải Nhuộm) | - |
| BR-18 | **Số lượng:** Số mét TP cần = order_meters ÷ (1 − %B/C TP). Số mét mộc = Số mét TP cần ÷ (1 − tiêu hao nhuộm) ÷ (1 − độ co), chia thêm (1 − %B/C mộc) nếu Hình thức bán ≠ Vải Nhuộm. Kg mộc = Số mét mộc ÷ m/kg mộc. Kg TP = Số mét TP cần ÷ m/kg TP (sửa 2026-11-25: Gia công nhuộm không chia (1 − %B/C mộc), như Vải Nhuộm; Gia công dệt tính như Mộc) | - |
| BR-19 | **Chi phí sợi** từng dòng: Lượng sợi (kg) = Kg mộc × ratio ÷ (1 − tiêu hao) ÷ (1 − waste_rate). Thành tiền = Lượng sợi × price_vnd − Kg mộc × ratio × waste_rate × yarn_waste_price. Sản lượng Se ước tính (dòng có Se) = ratio × Kg mộc ÷ (1 − (tiêu hao + waste_rate − twist_loss_offset)). Tổng chi phí sợi = tổng thành tiền (sửa 2026-11-25: Gia công dệt -> lượng sợi vẫn tính (= sợi khách cần giao), thành tiền = 0 (BR-89); Gia công nhuộm -> không tính sợi) | - |
| BR-20 | **Định mức Se** (đ/kg) cho mỗi dòng 4.13. Loại = "SE - FILAMENT" (Filament) hoặc "SE - XƠ NGẮN" (Spun); E = chi số chuyển đổi; F = độ săn. Từ 4.5.1: tốc độ G, số cọc H, thời gian I. Năng suất = (G ÷ F) × H × I × (E ÷ 9.000.000) × 2 (kg/ngày); TG máy chạy K = I ÷ năng suất (phút/kg). Từ 4.5.2: N = TG CB/lần ÷ sản lượng/lần CB; T = (đơn giá máy chạy ÷ tổng đơn giá/phút) × K; U = (đơn giá chuẩn bị ÷ TG CB/lần ÷ tổng đơn giá/phút) × N; V = T + U. Mỗi khoản mục = V × đơn giá/phút của khoản mục; riêng Nhân công nhân hệ số NC = [số giờ làm/ngày ÷ (TG CB/lần ÷ 60 + sản lượng/lần CB × K ÷ 60)] × (số máy) ÷ (round(tổng nhân sự Se ÷ tổng số cọc × số cọc) ÷ số ca). Chi số có "CB" và là Filament: cộng thêm bấm đốt = TG bấm đốt × đơn giá/phút "BẤM ĐỐT - CARBON", TG bấm đốt = 1 ÷ (tốc độ bấm đốt × số cọc bấm đốt × E ÷ 9.000.000) ÷ hiệu suất. E lấy theo BR-81, hệ sợi theo BR-83 (sửa 2026-11-23: trước đây E tra trong 4.5.6 và có lỗi "chi số không khớp hệ sợi"; nay hệ sợi tự xác định nên không còn lỗi này) | - |
| BR-21 | **Kiểm tra sản lượng Se:** tổng quantity_kg các dòng 4.13 phải bằng tổng Sản lượng Se ước tính (BR-19), chênh ≤ 0,01 kg | Tổng sản lượng Se nhập (<a> kg) khác sản lượng Se ước tính (<b> kg). Vui lòng kiểm tra lại. |
| BR-22 | **Ngành Dệt** (đ, khi Hình thức bán ≠ Vải Nhuộm; Vải Nhuộm thì toàn bộ = 0). Số mét mắc = Số mét mộc ÷ (1 − warping_extra_loss) ÷ (1 − độ co mắc của mã). Se = Σ quantity_kg × định mức Se. Gia công Se = SL × đơn giá. Mắc Hồ = Số mét mắc × (6 khoản mục + Hóa chất × size_chemical_factor) của DinhMucHo theo [nguyên liệu hồ, nhóm tổng canh]; tổng canh = mật độ dọc mộc ÷ 10 × khổ mộc, nhóm theo 4.5.4. Gia công Hồ = Số mét mắc × đơn giá. Mắc phân băng (khi "Có") = Số mét mắc × Σ khoản mục, khoản mục = đơn giá/phút "MAC" × TG mắc × hệ số se; TG mắc = số nhịp tam suất ÷ (tốc độ MAC × chu vi guồng); số nhịp tam suất = roundup(tổng canh × số nhịp chuẩn ÷ tổng canh chuẩn); hệ số se = 1,97 nếu có sợi dọc tick Se, ngược lại 1. Cone = SL cone × khoản mục, khoản mục = đơn giá/phút "CONE" × 9.000.000 ÷ (tốc độ × số cọc × chi số chuyển đổi theo BR-81 (sửa 2026-11-23)); SL cone 1 mặc định = tổng SL Se ngang. (sửa 2026-11-26: Cone = Σ các dòng bảng cone 4.14a, mỗi dòng có SL > 0 = SL × khoản mục theo chi số của dòng, tên dòng chi phí "Cone <n>" (n = thứ tự dòng trong bảng cone); dòng có SL > 0 mà trống chi số -> cảnh báo chặn "Cone dòng <n>: có <SL> kg sợi cone, vui lòng nhập chi số."; không có dòng cone -> Cone = 0. Trước đây chỉ Cone 1 + Cone 2, SL cone 1 trống = tổng SL Se ngang.) Dệt = Số mét mộc × DinhMucDet[round(mật độ ngang mộc ÷ 10)]. Kiểm = Số mét mộc × đơn giá/phút KIEM HANG_1 (Mộc) hoặc KIEM HANG_2 (khác) ÷ tốc độ kiểm. Gia công Dệt, khác = Số mét mộc × đơn giá. (sửa 2026-11-25: Gia công nhuộm -> toàn bộ = 0 như Vải Nhuộm; Gia công dệt tính đủ) | Định mức <công đoạn> không có trong bảng tra. Kiểm tra lại thông tin nhập. |
| BR-23 | **Hệ số số lượng** (L = Số mét mộc): Vải Nhuộm -> không dùng; Thí Nghiệm -> trial_quantity_factor (2); L < 5.000 -> 1,1; L = 5.000 -> 1,05; 5.000 < L < 10.000 -> 1,05 − 0,05 × (L − 5.000) ÷ 5.000; 10.000 ≤ L ≤ 20.000 -> 1; 20.000 < L < 50.000 -> 0,95 − 0,03 × (L − 20.000) ÷ 30.000; L = 50.000 -> 0,92; 50.000 < L < 100.000 -> 0,92 − 0,02 × (L − 50.000) ÷ 50.000; L ≥ 100.000 -> 0,9. Chi phí ngành Dệt = Se + Gia công Se + Gia công Hồ + Gia công Dệt + Gia công khác + (Mắc Hồ + Mắc phân băng + Cone + Dệt + Kiểm) × hệ số. (sửa 2026-11-25: hệ số lấy từ bảng discount 4.6.1 ngành Dệt của bộ tham số dùng cho phiếu — Thí Nghiệm dùng dòng "Thí nghiệm", còn lại dòng "Đại trà" có mốc chứa số mét mộc, xét đúng ≥ / > / ≤ / < theo from_inclusive / to_inclusive; theo bậc, không chia đều. Bộ tham số cũ đánh dấu interpolate = Yes thì tính chia đều như công thức Excel nêu trên, để phiếu cũ giữ số; không có dòng nào khớp -> hệ số 1 và cảnh báo "Không có hệ số sản lượng cho <SL> m mộc trong bảng discount Dệt. Liên hệ SO.") (sửa 2026-11-25: Gia công nhuộm -> không dùng, như Vải Nhuộm; Gia công dệt dùng bảng discount Dệt như phiếu thường) | - |
| BR-24 | **Hệ số theo mã hàng:** với mã vải của costsheet, mỗi dòng 4.7 active và effective_from ≤ ngày tính giá: định mức của [công đoạn, khoản mục] = định mức × multiplier + addition, trước khi nhân số lượng | - |
| BR-25 | **Nhuộm TCDN** (đ/m TP, khi không phải Mộc). Đặt `co` = độ co (BR-13). Hệ số TCDN h: số mét ≥ 50.000 -> 0,95; ngược lại nếu (đã chọn nguyên liệu và cấp màu) hoặc extra_cost_type = Nhuộm -> (≤ 150 m: 1,2; khác 1); ngược lại (≤ 100 m: 1,5; khác 1) (sửa 2026-11-25: các mốc và hệ số lấy từ bảng discount 4.6.1 ngành Nhuộm TCDN; điều kiện "Nhuộm" khi đã chọn nguyên liệu và cấp màu hoặc extra_cost_type = Nhuộm, còn lại "Partial"; dòng mốc ≥ 50.000 m xét trước). (a) Tiêu chuẩn: mã "Nhuộm tiêu chuẩn-<NL>-<cấp màu>" trong 4.5.10; Blended = Σ tỷ trọng × dòng từng cấp màu (Khăn không có White; Cotton/Nylon, Cotton/Poly không có Special). Hóa chất = (giá phẩm nhuộm đặc biệt nếu có, ngược lại Hóa chất của bảng) ÷ (1 − co) ÷ 250 × g/m mộc; 6 khoản mục khác = bảng ÷ (1 − co). (b) WR: hóa chất = NhuomTCDN_HoaChat[wr_chemical, nhóm 1 nếu g/m2 mộc ≤ 150, ngược lại 2] ÷ 250 × g/m mộc ÷ (1 − co); khoản mục = dòng "WR" ÷ (1 − co) ÷ (1 − tiêu hao). (c) Mỗi công đoạn ngoài quy trình: tiêu hao t từ bảng; với công đoạn xưởng "Phụ trợ" thì không chia (1 − co). Hóa chất: CPB = HoaChat[CPB theo NL] ÷ 250 × g/m mộc; Coating/Bonding/Santa/Soaping = giá sales nhập (chưa nhập = "liên hệ TCDN", tính 0); Suse… = HoaChat[Suse] ÷ 250 × g/m mộc; Mercerzing = HoaChat[Mercerzing] ÷ 250 × g/m mộc; khác = Hóa chất bảng ÷ (1 − co) ÷ 250 × g/m mộc; mọi trường hợp ÷ (1 − t). Khoản mục: CPB lấy dòng CPB theo NL; khác lấy bảng; ÷ (1 − co) ÷ (1 − t). (d) Tính năng đặc biệt = giá sales nhập (chưa có = "liên hệ TCDN", tính 0). (e) Mỗi dòng: chi phí/m = (hóa chất + tổng khoản mục) × h. (f) Chi phí phát sinh (khi có) = Σ 7 khoản mục × h, và khi đó tổng nhuộm chỉ gồm chi phí phát sinh + gia công ngoài. (g) Gia công ngoài = đơn giá × h. Tổng nhuộm/m = Σ dòng. (sửa 2026-11-25: Gia công dệt -> không tính nhuộm, như Mộc) | Thiếu giá hóa chất cho <công đoạn>: đang tính 0 (liên hệ TCDN). |
| BR-26 | **Nhuộm HCM** (đ/kg TP, khi không phải Mộc). k = khổ (1, 2, 3); x2 = hcm_small_lot_factor nếu Thí Nghiệm hoặc Kg TP < hcm_small_lot_kg, ngược lại 1 (sửa 2026-11-25: lấy từ bảng discount 4.6.1 ngành Nhuộm HCM: Thí Nghiệm -> dòng "Thí nghiệm", còn lại dòng "Đại trà" có mốc chứa Kg TP). (a) Tiêu chuẩn = NhuomHCM_TieuChuan[loại vải, cấp màu] (Blended = Σ tỷ trọng × từng cấp màu); HCTN và Tiền lương × x2; mọi khoản mục ÷ k. (b) Công đoạn đặc biệt: NhuomHCM_CongDoan[tên]; HCTN, Tiền lương × x2; ÷ k. (c) Tính năng đặc biệt: NhuomHCM_TinhNang[tính năng, loại vải], không có thì [tính năng, rỗng]; HCTN, Tiền lương × x2; ÷ k; không có cả hai -> lỗi. (d) Chi phí đặc biệt = đ/kg sales nhập. (e) Chi phí phát sinh (khi có) = Σ 7 khoản mục, và khi đó tổng nhuộm chỉ gồm chi phí phát sinh + gia công. (f) Gia công = đ/kg. Tổng nhuộm/kg = Σ; Tổng nhuộm/m = Tổng/kg ÷ m/kg TP. (sửa 2026-11-25: Gia công dệt -> không tính nhuộm, như Mộc) | Tính năng <tên> không có định mức cho nguyên liệu <loại vải>. |
| BR-27 | **Tổng chi phí và giá vốn:** Chi phí nhuộm = Số mét TP cần × Tổng nhuộm/m. Thanh lý B/C = (Số mét mộc − Số mét TP cần) × bc_fabric_price + (Số mét TP cần − order_meters) × bc_fabric_price. Tổng chi phí = Chi phí sợi + Chi phí ngành Dệt + Chi phí nhuộm − Thanh lý B/C; nếu Vải Nhuộm: = greige_buy_price × Số mét mộc + Chi phí nhuộm − Thanh lý B/C. Đơn giá (đ/m) = Tổng chi phí ÷ order_meters. Giá vốn = Đơn giá + Σ cogs_extra_lines. USD = đ ÷ tỷ giá. (sửa 2026-11-25: Gia công dệt -> Tổng chi phí = Chi phí ngành Dệt (BR-89); Gia công nhuộm -> Tổng chi phí = Chi phí nhuộm (BR-90); cả 2 loại Thanh lý B/C = 0) | - |
| BR-28 | **Lợi nhuận:** Giá bán (đ/m) = sell_price_input × tỷ giá nếu USD. GP = Giá bán − Giá vốn; GP% = GP ÷ Giá bán. S&A = Giá vốn × sa_rate. OP = GP − S&A − commission − freight_insurance − interest_cost; OP% = OP ÷ Giá bán. Giá có VAT = Giá bán × (1 + vat_rate). Cảnh báo (không chặn, tô màu cho người duyệt) khi GP% < gp_threshold hoặc OP% < op_threshold | GP% (<x>%) thấp hơn ngưỡng <y>%. / OP% (<x>%) thấp hơn ngưỡng <y>%. |
| BR-29 | **F&I theo loại giá:** CIF, CIP -> freight_insurance bắt buộc > 0 (F&I); CPT -> bắt buộc > 0 (phí vận chuyển); FOB, EXW, FCA -> freight_insurance = 0 và ô bị ẩn | Loại giá <loại> cần nhập chi phí vận chuyển (và bảo hiểm). |
| BR-30 | **Trạng thái:** Nháp -> Chờ duyệt (UC-20) -> Đã duyệt (UC-21) / Trả lại (UC-22); Trả lại -> Nháp (UC-17) hoặc -> Chờ duyệt (UC-20); Đã duyệt -> Đã chốt đơn (UC-24); Nháp / Chờ duyệt / Trả lại / Đã duyệt -> Hủy (UC-25); Đã duyệt / Đã chốt đơn -> Đã thay thế (khi phiên bản sau được duyệt). Chuyển khác bị từ chối | Không thể chuyển costsheet từ "<trạng thái>" sang "<trạng thái>". |
| BR-31 | Chỉ phiếu Nháp / Trả lại sửa được, và chỉ chủ phiếu hoặc người có vai trò SO sửa (sửa 2026-11-23: thêm SO) | Costsheet đang ở trạng thái <trạng thái>, không sửa được. |
| BR-32 | Duyệt chỉ khi Chờ duyệt | Costsheet không ở trạng thái Chờ duyệt. |
| BR-33 | Trả lại bắt buộc lý do (≥ 5 ký tự) | Vui lòng nhập lý do trả lại. |
| BR-34 | Lưu phiếu Trả lại chuyển về Nháp, giữ lý do trả lại để xem | - |
| BR-35 | **Duyệt lại:** phiên bản n ≥ 2 khi gửi duyệt được duyệt tự động nếu so với phiên bản đã duyệt gần nhất: Giá bán (đ/m, làm tròn đến đồng), Giá vốn (làm tròn đến đồng) và GP% (làm tròn 0,01%) đều bằng nhau. Thay đổi chỉ ở OC, ghi chú, ngày giao, style không làm đổi 3 số này | - |
| BR-36 | Hủy bắt buộc lý do; không hủy phiếu Đã chốt đơn / Hủy / Đã thay thế. Chốt đơn chỉ khi Đã duyệt và có OC hợp lệ | Vui lòng nhập lý do hủy. / Costsheet đã chốt đơn không hủy được. / Cần nhập OC trước khi chốt đơn. |
| BR-37 | Mỗi costsheet chỉ có 1 phiên bản ở trạng thái Nháp / Chờ duyệt / Trả lại cùng lúc | Costsheet <số> đang có phiên bản <n> chưa duyệt. Hãy hoàn tất phiên bản đó trước. |
| BR-38 | Phiếu Hủy / Đã thay thế chỉ xem và sao chép | - |
| BR-39 | **Giữ số cũ:** phiếu ở trạng thái Chờ duyệt, Đã duyệt, Đã chốt đơn, Hủy, Đã thay thế không tính lại; luôn hiện kết quả đã lưu (4.20). Thay đổi tỷ giá, định mức, tham số, mã vải sau đó không ảnh hưởng | - |
| BR-40 | **OC:** dạng `KDV` + 2 số + `-` + 2 chữ + `-` + 2 chữ + `-` + 4 số + `-` + số, có thể thêm `.` + số (ví dụ KDV10-SX-LO-0726-6564, KDV10-SX-LO-0726-6564.1); app bỏ khoảng trắng, dấu phẩy thừa ở cuối, phần trong ngoặc. Main OC = phần trước dấu chấm. Một OC chỉ được gắn cho 1 costsheet ở trạng thái Đã chốt đơn (phiên bản mới nhất) | OC "<OC>" sai định dạng. Ví dụ đúng: KDV10-SX-LO-0726-6564.1 / OC <OC> đã được chốt ở costsheet <số>. |
| BR-41 | Số costsheet `CS-<mã KH>-YYYY-NNNNN`: mã KH của khách hàng lúc tạo; YYYY = năm tạo; NNNNN tăng dần trong năm, chung cho mọi khách hàng, không trùng. Sao chép tạo số mới (theo khách hàng của bản sao); phiên bản mới giữ số; đổi khách hàng hoặc mã KH sau khi tạo không đổi số | - |
| BR-47 | **Sửa thông số vải trên phiếu:** chỉ khi mã vải có nguồn "Nhập tay" và phiếu Nháp / Trả lại. Mã có nguồn Peace / WFX: thông số và sợi chỉ đọc. Thông số đã sửa chỉ lưu trong phiếu, được tô màu cho người duyệt. Khi SO tải file có mã đó (nguồn đổi thành Peace / WFX), lần tính lại kế tiếp của phiếu Nháp / Trả lại bỏ thông số đã sửa và dùng dữ liệu gốc | Mã vải <tcfno> lấy từ dữ liệu gốc Peace / WFX, không được sửa thông số. |
| BR-42 | **Đủ dữ liệu khi gửi duyệt:** khách hàng, thị trường, loại đơn, hình thức bán, ngày tính giá, mã vải, số mét, loại giá, giá bán; giá sợi > 0 cho mọi dòng sợi có ratio > 0; nếu có Hồ thì có nguyên liệu hồ hoặc Mắc phân băng = Có / Không; nếu có Se thì có dòng Se (BR-21); Vải Nhuộm thì có giá mộc mua ngoài; không còn lỗi định mức (BR-20, BR-22, BR-26). (sửa 2026-11-25: Gia công dệt không cần giá sợi; Gia công nhuộm không cần giá sợi, giá mộc, Se, Hồ, Mắc phân băng) | Chưa đủ dữ liệu để gửi duyệt: <danh sách mục thiếu>. |
| BR-43 | **Dữ liệu nhuộm khi gửi duyệt** (không phải Mộc): có nguyên liệu + cấp màu, hoặc có chi phí phát sinh; Blended thì tổng tỷ trọng = 100%; HCM có nhuộm tiêu chuẩn thì có tiêu hao nhuộm; chi phí phát sinh thì có tiêu hao (HCM dye_loss_rate, TCDN extra_cost_loss_rate) và (TCDN) loại quy trình; phẩm nhuộm đặc biệt thì có giá hóa chất. Công đoạn "liên hệ TCDN" chưa có giá: cảnh báo, không chặn | Thiếu dữ liệu nhuộm: <mục>. |
| BR-44 | **Giá sợi còn hiệu lực:** khi gửi duyệt, mỗi dòng sợi có giá phải có price_entered_on cách hôm nay < yarn_price_valid_days (5) ngày làm việc. Ngày làm việc = thứ 2-6, trừ ngày lễ 4.8, đếm từ ngày sau price_entered_on đến hết hôm nay. Sửa giá, hoặc bấm "Xác nhận giá sợi hôm nay" -> price_entered_on = hôm nay | Giá sợi <tên sợi> nhập từ dd/mm/yyyy đã quá 5 ngày làm việc. Vui lòng nhập lại hoặc xác nhận giá sợi. |
| BR-45 | Giá sợi / giá bán nhập USD: price_vnd = price_input × tỷ giá của phiếu; đổi tỷ giá (khi tính lại) thì giá VND đổi theo | - |
| BR-46 | **Tham số sửa trên phiếu:** sales sửa được mọi tham số 4.6 trừ các dòng "chỉ SO"; giá trị sửa lưu theo phiếu (4.18), được tô màu và hiện giá trị mặc định bên cạnh; không bắt lý do. (sửa 2026-11-25: trên phiếu, sales sửa được **hệ số discount đang áp dụng** của từng ngành (Dệt, Nhuộm HCM, Nhuộm TCDN), **% B/C mộc / TP** đang áp dụng và 2 giá thanh lý — không sửa cả bảng; ngưỡng GP / OP, độ co tối thiểu, số ngày giá sợi chỉ SO) | - |
| BR-88 | **Bảng discount / % B/C** (thêm 2026-11-25), khi SO lưu bộ tham số: mỗi ngành + điều kiện, các khoảng mốc không chồng lên nhau (xét cả ≥ / > / ≤ / <); hệ số > 0; % B/C trong 0..1 và có đủ 3 hình thức bán (sửa 2026-11-25: 2 dòng Gia công dệt / Gia công nhuộm không bắt buộc; thiếu thì lấy theo BR-16) | Bảng discount <ngành> – <điều kiện>: khoảng <từ>–<đến> chồng lên khoảng khác. / Bảng % B/C thiếu hình thức bán <tên>. |
| BR-89 | **Gia công dệt** (thêm 2026-11-25; khách giao sợi, mình dệt ra mộc giao khách). Số lượng như Mộc: độ co = 0, tiêu hao nhuộm = 0, % B/C lấy dòng "Gia công dệt" của 4.6.2; Số mét mộc = order_meters ÷ (1 − %B/C TP) ÷ (1 − %B/C mộc). Sợi: lượng sợi từng dòng tính như BR-19 và hiện là "Sợi khách cần giao (kg)", thành tiền = 0, không bắt nhập giá sợi. Ngành Dệt tính đủ như BR-20..BR-24 (Se, gia công Se, Mắc Hồ, Mắc phân băng, Cone, Dệt, Kiểm, gia công ngoài; hệ số theo bảng discount Dệt). Nhuộm = 0. Thanh lý B/C = 0 (vải lỗi là của khách). Tổng chi phí = Chi phí ngành Dệt. Giá bán = phí gia công; GP, OP, ngưỡng như BR-28 | - |
| BR-90 | **Gia công nhuộm** (thêm 2026-11-25; khách giao mộc, mình nhuộm). Số lượng như Vải Nhuộm: Số mét mộc = Số mét TP cần ÷ (1 − tiêu hao nhuộm) ÷ (1 − độ co), không chia B/C mộc; hiện là "Mộc khách cần giao (m)". Sợi = 0, ngành Dệt = 0, không có tiền mua mộc, không bắt nhập giá mộc; không dùng hệ số số lượng Dệt. Nhuộm tính đủ như BR-25 (TCDN) / BR-26 (HCM). Thanh lý B/C = 0. Tổng chi phí = Chi phí nhuộm. Giá bán = phí gia công; GP, OP, ngưỡng như BR-28. Mỗi phiếu 1 mã vải; nhiều mã / nhiều OC trình 1 lần thuộc đợt 3 (NGC) | - |
| BR-91 | **Loại đơn khi chọn gia công** (thêm 2026-11-25): khi sales đổi Hình thức bán sang Gia công dệt hoặc Gia công nhuộm, ô Loại đơn hàng tự đặt "Gia Công"; sales sửa lại được và app giữ lựa chọn của sales. Loại đơn "Gia Công" tự nó không đổi cách tính (cách tính theo Hình thức bán) | - |
| BR-92 | **Phiếu gia công nhuộm – chi phí 1 dòng TCDN** (thêm 2026-11-25, theo file NGC). co = độ co sales gõ (4.22). (a) Nhuộm tiêu chuẩn, WR, phẩm nhuộm đặc biệt, tính năng đặc biệt: như BR-25 (a), (b), (d) với co của dòng và g/m của dòng. (b) Công đoạn ngoài quy trình (n = số lần xử lý thêm, không nhập = 0): Hóa chất = CPB -> hóa chất CPB theo nguyên liệu ÷ 250 × g/m; Santa, Bonding, Coating, Soaping -> giá hóa chất sales nhập (không chia độ co, không chia tiêu hao); Mercerizing, Suse 2 -> hóa chất bảng ÷ 250 × g/m ÷ (1 − tiêu hao); công đoạn khác -> 0; khi n > 0 hóa chất lấy từ bảng thì × n (giống file). 6 khoản còn lại = định mức bảng × (1 + n) ÷ (1 − co) ÷ (1 − tiêu hao) ÷ hệ số vận hành (4.24); công đoạn xưởng "Phụ trợ" không chia (1 − co); CPB không chia (1 − tiêu hao). (c) Mỗi dòng chi phí × hệ số chiết khấu / phụ phí h của BR-25 (số mét = số lượng của dòng; "Nhuộm" khi đã chọn nguyên liệu và cấp màu, còn lại "Partial"). (d) Tổng định mức (đ/m) = Σ các dòng chi phí. Thiếu định mức hoặc giá hóa chất: cảnh báo như BR-25 | Thiếu giá hóa chất cho <công đoạn>: đang tính 0 (liên hệ TCDN). |
| BR-93 | **Hệ số vận hành** (thêm 2026-11-25): chỉ phiếu gia công nhuộm TCDN chia 6 khoản (trừ hóa chất) của công đoạn ngoài quy trình cho hệ số 4.24 của bộ tham số; công đoạn không có trong bảng = 1; hệ số phải > 0 và ≤ 1 khi SO lưu | Hệ số vận hành <công đoạn> phải lớn hơn 0 và không quá 1. |
| BR-94 | **Phiếu gia công nhuộm – dòng HCM** (thêm 2026-11-25): tính như BR-26 với Kg TP = số lượng ÷ (1000 ÷ g/m), đ/m = đ/kg ÷ (1000 ÷ g/m); không dùng hệ số vận hành. **Báo giá riêng** (cả TCDN và HCM): 7 khoản mục quoted_items có tổng > 0 thì Tổng định mức = tổng 7 khoản đó (bỏ phần tự tính, không nhân h) | - |
| BR-95 | **Kết quả dòng và tổng** (thêm 2026-11-25): Tổng định mức – TP = Tổng định mức ÷ (1 − % B/C TP); Thành tiền chi phí = Số lượng × Tổng định mức – TP; Thành tiền giá GC = Số lượng × Đơn giá nhận GC; GP = Giá GC − chi phí; %GP = GP ÷ Thành tiền giá GC (0 khi giá GC = 0). Tổng phiếu = Σ các dòng; %GP phiếu = Σ GP ÷ Σ giá GC. Cảnh báo (không chặn) khi %GP của dòng hoặc của phiếu < gp_threshold | %GP dòng <mã hàng> (<x>%) thấp hơn ngưỡng <y>%. / %GP phiếu (<x>%) thấp hơn ngưỡng <y>%. |
| BR-96 | Số phiếu gia công `GC-<mã KH>-YYYY-NNNNN`, NNNNN tăng dần trong năm, chung mọi khách hàng | - |
| BR-97 | **Dòng hợp lệ khi lưu** (thêm 2026-11-25): mã hàng ≤ 40 ký tự, không để trống nếu dòng có số liệu; g/m, g/m2, số lượng, đơn giá ≥ 0; độ co và % B/C trong 0..< 100%; số lần xử lý thêm 0..9; tối đa 30 dòng | Dòng <n>: <tên ô> không hợp lệ. / Phiếu gia công tối đa 30 dòng. |
| BR-98 | **Đủ dữ liệu khi gửi duyệt** (thêm 2026-11-25): khách hàng, ngày tính giá, ≥ 1 dòng; mỗi dòng có mã hàng, g/m > 0, g/m2 > 0, số lượng > 0, đơn giá nhận GC > 0, và (nguyên liệu + cấp màu, hoặc ít nhất 1 công đoạn / tính năng, hoặc báo giá riêng) | Chưa đủ dữ liệu để gửi duyệt: <danh sách mục thiếu>. |
| BR-99 | **Quyền và trạng thái** (thêm 2026-11-25): phiếu gia công nhuộm dùng cùng trạng thái (Nháp, Chờ duyệt, Đã duyệt, Trả lại, Hủy) và cùng quyền xem / sửa / duyệt như costsheet (BR-30 phần Nháp -> Chờ duyệt -> Đã duyệt / Trả lại, Hủy; BR-31..BR-34, BR-52, BR-53, BR-85); không có phiên bản, OC, chốt đơn. Phiếu đã duyệt chỉ xem, xuất Excel và sao chép | Phiếu gia công đang ở trạng thái <trạng thái>, không sửa được. |
| BR-50 | **Khách hàng:** tên chuẩn hóa (bỏ dấu, in hoa, bỏ ký tự không phải chữ / số, gộp khoảng trắng) không được trùng; mã KH 2-8 ký tự chữ in hoa / số, không trùng. Mã KH tự tạo = 4 chữ cái đầu của tên chuẩn hóa (bỏ khoảng trắng), trùng thì thêm số 2, 3, … (ví dụ ICHI, ICHI2). Gợi ý tên tương tự: các tên có độ giống ≥ 60% hoặc chứa nhau sau chuẩn hóa, tối đa 10 | Khách hàng <tên> đã có. / Mã khách hàng <mã> đã dùng cho <tên>. |
| BR-51 | **Vai trò** (quản trị viên cấp trên `/admin`): SALES, TRUONG_TEAM, TRUONG_DON_VI, SO, PD; team FS1, FS2. Người có SALES hoặc TRUONG_TEAM (và không có SO) phải có đúng 1 team mới tạo được costsheet. Người có SO tạo được costsheet không cần team; có cả SO và 1 team FS1 / FS2 thì phiếu thuộc team đó, chỉ có SO thì phiếu thuộc team "SO" (sửa 2026-11-23: thêm SO) | Tài khoản của bạn chưa được gán team FS1 / FS2. Liên hệ quản trị viên. |
| BR-52 | **Quyền xem:** SALES, TRUONG_TEAM xem phiếu của team mình; TRUONG_DON_VI, SO xem tất cả (kể cả phiếu team "SO"); chỉ PD thì không xem costsheet. Chủ phiếu và SO sửa được (BR-31) (sửa 2026-11-23: trước đây SO không sửa) | Bạn không có quyền xem costsheet này. |
| BR-53 | **Quyền duyệt:** phiếu team X do người có TRUONG_TEAM + team X, hoặc TRUONG_DON_VI, hoặc SO duyệt. Trưởng team, trưởng đơn vị, SO được tự duyệt phiếu do chính mình lập. Sales không duyệt. Phiếu team "SO" do SO hoặc TRUONG_DON_VI duyệt (sửa 2026-11-23: thêm SO) | Bạn không có quyền duyệt costsheet này. |
| BR-85 | **SO toàn quyền** (thêm 2026-11-23): người có vai trò SO được làm mọi thao tác trên mọi costsheet như chủ phiếu (Tính lại, Lưu nháp, Gửi duyệt, Duyệt, Trả lại, Sao chép, Tạo phiên bản mới, Lưu OC, Chốt đơn, Hủy, In nhãn, Xác nhận giá sợi, Sửa thông số vải theo BR-47); vẫn theo luồng trạng thái BR-30 | - |
| BR-60 | Tỷ giá theo (tháng, năm) duy nhất, > 0 | Tỷ giá phải lớn hơn 0. |
| BR-61 | Tỷ giá của phiếu = tỷ giá tháng / năm của ngày tính giá; không có thì không tính được | Chưa có tỷ giá tháng MM/YYYY. Liên hệ SO cập nhật. |
| BR-62 | **Bộ định mức / tham số dùng:** bộ có effective_from ≤ ngày tính giá, gần nhất | Chưa có bộ định mức / tham số hiệu lực cho ngày dd/mm/yyyy. Liên hệ SO. |
| BR-63 | File định mức: đủ 12 sheet (sheet `Spandex` không bắt buộc; nếu có thì loại spandex là số nguyên > 0, không trùng, cộng thêm ≥ 0 (sửa 2026-11-23)), đúng cột, số ≥ 0, khóa không trùng; các khóa mà công thức cần (mọi công đoạn ở 4.5.1, mọi dòng 4.5.2-4.5.3) phải có | Sheet <sheet> dòng <n>: <lỗi>. |
| BR-64 | Ngày hiệu lực của bộ định mức / tham số không trùng bộ đã có | Đã có bộ hiệu lực từ dd/mm/yyyy. Chọn ngày khác. |
| BR-65 | Tham số tỷ lệ trong khoảng 0 ≤ x < 1; ngưỡng GP / OP trong −100%..100% | <Tham số> không hợp lệ. |
| BR-70 | File nhập: .xlsx / .xls, ≤ 20 MB, ≤ 50.000 dòng, đủ cột bắt buộc | File <tên> không đúng mẫu: thiếu cột <cột>. / File quá lớn (tối đa 20 MB, 50.000 dòng). |
| BR-71 | Lưu dữ liệu vải chỉ lưu mã hợp lệ; mã lỗi được báo lại, không chặn các mã khác | - |
| BR-72 | Mã nhập tay phải có ít nhất 1 dòng sợi WARP và 1 dòng WEFT | Cần ít nhất 1 sợi dọc và 1 sợi ngang. |
| BR-75 | **Nhãn:** theo sheet PRINT: luôn dùng thông số thành phẩm của dữ liệu gốc (khổ, g/m2, g/m, mật độ dọc / ngang), tên vải, và tối đa 6 sợi dọc + 6 sợi ngang với tỷ lệ = rate ÷ 100 × raw_rate ÷ 100. Thông số TP trống thì in trống | - |
| BR-80 | **Danh sách cảnh báo** trên phiếu: BR-05, BR-14, BR-21, BR-25 (liên hệ TCDN), BR-28, BR-44, định mức không tìm thấy, Hồ được tick nhưng chưa chọn nguyên liệu hồ / Mắc phân băng, BR-81, BR-82, BR-84 (thêm 2026-11-23; chặn gửi duyệt) | - |
| BR-81 | **Chi số chuyển đổi** (thêm 2026-11-23). Chi số (bỏ khoảng trắng thừa, in hoa) có trong danh sách 4.5.6 của bộ định mức -> lấy số của danh sách. Ngược lại tách chi số theo dấu "+" thành các phần, chi số chuyển đổi = tổng các phần: "nD" hoặc "nD/k" (filament) = n × k (không có "/k" thì k = 1); "N" hoặc "N/k" (spun, không có chữ D) = 5.316 ÷ (N ÷ k); "CB" = 20; "SP m" = số cộng thêm của spandex m (4.5.13, BR-84). n, N, m là số (cho phép số thập phân), k là số nguyên 1-9. Ví dụ: "75D/2 + CB" = 170; "20/2" = 531,6; "30 + 150D + 300D" = 627,2; "45 + 75D + SP 70" = 215,13. Phần không đúng dạng nào -> lỗi | Chi số "<chi số>" không đúng dạng. Ví dụ đúng: 75D/2 + CB, 30/2, 45 + 75D + SP 70. |
| BR-82 | **Độ săn** (thêm 2026-11-23): số nguyên từ 50 đến 3.000 T/M | Độ săn <số> không hợp lệ: phải là số nguyên từ 50 đến 3.000 T/M. |
| BR-83 | **Hệ sợi** (thêm 2026-11-23): gợi ý sẵn — chi số có chữ "D" (sau khi bỏ "SP m" và "CB") -> Filament; không có -> Spun. Sales chọn lại được; hệ sợi trên dòng (gợi ý hoặc sales chọn) dùng chọn dòng "SE - FILAMENT" / "SE - XƠ NGẮN" và tham số Se (BR-20). Gợi ý được điền khi chi số thay đổi và ô hệ sợi đang trống hoặc đang là gợi ý cũ | - |
| BR-86 | **Gợi ý dòng Se** (thêm 2026-11-23): khi phiếu chưa có dòng Se nào và có dòng sợi tick Se (bước Tính lại / tạo phiếu), app tạo sẵn 1 dòng Se cho mỗi nhóm (hướng, chi số, độ săn) của các dòng sợi tick Se: Hướng = Dọc (WARP) / Ngang (WEFT); Độ săn = số trước "T/M" của sợi; Chi số đọc từ tên sợi: mỗi phần filament "…<n>D/…/<k>" -> "nD" (thêm "/k" khi k ≥ 2), spun "<N>/<k>" -> "N/k", có "CACBON" / "CARBON" / "C.TRANG" / "C.DEN" / "C TRANG" -> thêm "+ CB"; Hệ sợi theo BR-83; SL = sản lượng Se ước tính của các dòng sợi trong nhóm (BR-19). Đọc không ra chi số thì để trống ô Chi số. Sales sửa / xóa / thêm dòng tự do; đã có dòng Se thì không tạo lại. (sửa 2026-11-23) Mỗi dòng Se ghi nhận "do app gợi ý" hay "sales đã sửa": khi tính, các dòng còn là gợi ý được tạo lại theo tick Se và sản lượng Se ước tính hiện tại (đổi tick Se, đổi số mét, đổi tỷ lệ… đều cập nhật); dòng sales đã sửa hoặc tự thêm giữ nguyên; dòng sales đã xóa không tạo lại. Phiếu có dòng Se lưu trước 2026-11-23 coi như "sales đã sửa" | - |
| BR-87 | (bỏ từ 2026-11-26, thay bằng BR-100) **Gợi ý cone** (thêm 2026-11-23): SL cone 1 điền sẵn = tổng SL các dòng Se Ngang; chi số cone 1 điền sẵn = chi số của dòng Se Ngang nếu các dòng Se Ngang chỉ có 1 chi số (nhiều chi số thì để trống để sales nhập). Giá trị gợi ý hiện ngay trong ô và tự cập nhật khi dòng Se Ngang đổi, tới khi sales tự sửa ô đó; sales sửa thì giữ số của sales. Không có Se Ngang thì để trống | - |
| BR-100 | **Gợi ý bảng cone – sợi se chung / se riêng** (thêm 2026-11-26, thay BR-87). Dựa trên các dòng Se Ngang (4.13). (a) Dòng Se Ngang là **sợi phụ** khi các dòng sợi Ngang tick Se có cùng chi số và độ săn với nó có tên chứa BR1, WHITE C, BLACK C, CARBON, CACBON, C.TRANG, C.DEN, C TRANG (carbon) hoặc SPANDEX (spandex), hoặc khi chi số của dòng chỉ là "CB" hay "SP m"; các dòng khác là **sợi chính**. (b) Mỗi sợi chính = 1 cone; các dòng Se Ngang cùng chi số và độ săn gộp làm 1 (cộng SL). (c) Mỗi sợi phụ se chung với 1 sợi chính: chọn trong các sợi chính cùng độ săn (không có thì xét mọi sợi chính) sợi có SL × (chi số chuyển đổi sợi phụ ÷ chi số chuyển đổi sợi chính) gần SL sợi phụ nhất (2 sợi se chung dài bằng nhau); không có sợi chính nào thì sợi phụ thành 1 cone riêng. (d) Cone se chung: SL = SL sợi chính + SL các sợi phụ đi kèm; chi số = chi số sợi chính, nối " + " với phần của từng sợi phụ: carbon có "CB" trong chi số -> "CB", spandex -> "SP m" (m = số D của spandex), còn lại -> chi số sợi phụ. Ví dụ "150D + 30D", "75D/2 + CB", "40/2 + SP 40". (e) Thứ tự dòng = thứ tự sợi chính trong bảng Se. (f) Có từ 2 sợi chính cùng độ săn với một sợi phụ -> cảnh báo không chặn. (g) Dòng gợi ý được tạo lại mỗi lần tính theo dòng Se Ngang hiện tại; dòng sales đã sửa hoặc tự thêm giữ nguyên; dòng gợi ý sales đã xóa không tạo lại; một cone gợi ý trùng chi số với dòng sales đã sửa thì không tạo thêm; costsheet lưu trước 2026-11-26 có cone sales đã gõ thì giữ nguyên các dòng cone, không gợi ý thêm (giống dòng Se lưu trước, BR-86). (h) Không có dòng Se Ngang -> không có dòng gợi ý; bảng cone ẩn trừ khi phiếu đã có dòng cone (giữ để không mất số) | Kiểm tra lại cone: sợi <sợi phụ> có thể se chung với <sợi chính 1> hoặc <sợi chính 2>. |
| BR-84 | **Spandex** (thêm 2026-11-23): "SP m" phải có trong bảng 4.5.13 của bộ định mức dùng cho phiếu | Chưa có số cộng thêm cho spandex SP <m>. Liên hệ SO bổ sung. |

## 8. Screens (Màn hình)

### Giao diện đã chốt (UI concept)
Chung:
- Mỗi màn hình là một mục riêng trong menu bên trái của ứng dụng, chia 2 nhóm: **Sales** (Màn hình 1, 2, 3) và **Phòng
  SO** (Màn hình 4, 5, 6, 7).
- Bảng danh sách: chỉ xem (lọc, sắp xếp, tìm), chọn 1 dòng để mở / sửa.
- Bảng trong costsheet (sợi, dòng Se, dòng nhuộm, chi phí vào giá vốn): sửa trực tiếp trong ô như Excel, rồi bấm "Tính
  lại" / "Lưu nháp".
- Không có biểu đồ.
- Hỏi lại (hộp thoại xác nhận) trước khi: Gửi duyệt, Duyệt, Trả lại, Chốt đơn, Hủy, Lưu dữ liệu vải, Lưu bộ định mức.
  Không hỏi lại với Lưu nháp, Tính lại.
- Thông báo ngắn sau mỗi thao tác thành công.

Màn hình 1 – Danh sách costsheet (trang đầu, nhóm Sales), từ trên xuống:
1. Bộ lọc:
   - Từ khóa;
   - Trạng thái (chọn nhiều);
   - Team, Sales, Khách hàng, Nhà máy nhuộm, Loại đơn, Loại giá;
   - Từ ngày – Đến ngày (90 ngày gần nhất);
   - công tắc "Chỉ phiên bản mới nhất" (bật), "Chỉ dưới ngưỡng GP/OP" (tắt);
   - (mở rộng 2026-11-23) bộ lọc Team có thêm giá trị "SO".
   - (mở rộng 2026-11-25) cột Hình thức bán có thêm Gia công dệt / Gia công nhuộm; lọc Loại đơn = "Gia Công" để xem
     riêng phiếu gia công.
2. Ô tổng hợp: Số phiếu, Chờ duyệt, Đã duyệt, Đã chốt đơn, Dưới ngưỡng GP/OP, Độ co thấp / bằng 0.
3. Bảng chỉ xem, chọn 1 dòng, cột theo thứ tự mục "Screen 1" bên dưới; trạng thái hiện dạng nhãn màu.
4. Thanh nút: "Tạo costsheet", "Mở phiếu đã chọn", "Xuất Excel".

Màn hình 2 – Costsheet (nhóm Sales), từ trên xuống:
1. Tiêu đề: số costsheet, phiên bản, nhãn trạng thái, người lập, người duyệt; ô chọn phiếu đang mở (số costsheet +
   phiên bản).
2. Ô tóm tắt: Đơn giá (đ/m), Giá vốn, Giá bán, GP%, OP% (dưới ngưỡng tô đỏ).
3. Khối Thông tin đơn (form): nhà máy nhuộm, khách hàng (+ nút "Thêm khách hàng"), thị trường, loại đơn, style, hình
   thức bán, giá mộc mua ngoài (khi Vải Nhuộm), ngày giao, ngày tính giá, mã vải, số mét, loại giá, OC, lý do ngoại lệ
   độ co, ghi chú.
4. Các thẻ:
   - Thông số vải;
   - Sợi: bảng sửa trong ô gồm đơn vị giá, giá, sợi cặn, Se, Hồ + lý do; giá thanh lý sợi cặn;
   - Ngành Dệt: bảng dòng Se sửa trong ô; lựa chọn hồ, mắc, cone, gia công; bảng chi phí công đoạn và khoản mục;
     (mở rộng 2026-11-23):
     - đầu thẻ là 2 ô "Số mét mộc", "Hệ số số lượng" kèm lý do;
     - bảng dòng Se gồm các cột như Excel: Hướng, Hệ sợi (ô chọn, gợi ý sẵn), Chi số (ô chữ, gợi ý sẵn), Độ săn (ô số,
       gợi ý sẵn), SL yêu cầu (gợi ý sẵn); sales sửa được mọi ô, thêm / xóa dòng;
     - dưới bảng có 1 dòng ghi chú ngắn: "Hệ sợi, chi số, độ săn được gợi ý sẵn, sửa lại được. Ví dụ cách ghi: 75D/2 + CB,
       30/2, 45 + 75D + SP 70." (đổi giao diện 2026-11-23: trước đây liệt kê toàn bộ chi số và độ săn hay dùng);
     - không hiện chi số chuyển đổi;
     - ô chi số cone là ô chữ;
     - bảng chi phí công đoạn thêm cột "Nhân hệ số SL", "Thành tiền sau hệ số (đ)";
   - Nhuộm: lựa chọn và các bảng dòng sửa trong ô, theo HCM hoặc TCDN; ẩn khi Mộc;
   - Giá bán & lợi nhuận;
   - Tham số;
   - Cảnh báo;
   - Lịch sử.
5. Thanh nút (chỉ hiện nút được phép): Tính lại, Lưu nháp, Gửi duyệt, Duyệt, Trả lại, Sao chép, Tạo phiên bản mới, Lưu
   OC, Chốt đơn, Hủy, In nhãn, Xác nhận giá sợi hôm nay, Sửa thông số vải. (sửa 2026-11-23: bỏ nút "Tính lại" — phiếu
   tự tính mỗi khi đổi một ô, UC-16; khi có thay đổi chưa lưu, cạnh nút "Lưu nháp" hiện dòng "Có thay đổi chưa lưu".)
- (sửa 2026-11-23) Thẻ Ngành Dệt: ô "SL cone 1" và "Chi số cone 1" hiện sẵn giá trị gợi ý (BR-87); ô công đoạn ngoài
  quy trình TCDN chỉ liệt kê 28 công đoạn có định mức.
- (sửa 2026-11-26, thay 4 ô cone ở dòng trên) Thẻ Ngành Dệt, mục "Hồ, mắc, cone, gia công": **bảng cone** sửa trong ô,
  cột Chi số cone (ô chữ), SL cone (kg), Gồm sợi (chỉ xem); sales sửa ô, thêm / xóa dòng; dưới bảng 1 dòng ghi chú
  "Cone được gợi ý theo sợi se chung / se riêng, sửa lại được." Bảng chỉ hiện khi phiếu có dòng Se Ngang hoặc đã có
  dòng cone (BR-100 h); không hiện thì không có chữ hay ô cone nào. Cảnh báo "Kiểm tra lại cone…" hiện ở đầu thẻ Ngành
  Dệt như các cảnh báo cone khác. Bảng chi phí công đoạn hiện mỗi cone 1 dòng "Cone 1", "Cone 2"… theo thứ tự bảng cone.

Đổi giao diện Màn hình 2 (2026-11-23), thay mục 4 ở trên về thứ tự thẻ và cảnh báo. Thứ tự từ trên xuống:
1. Tiêu đề.
2. Ô tóm tắt.
3. Khối Thông tin đơn.
4. Khung **"Chuỗi nhu cầu"**: bảng chỉ xem, luôn hiện giữa Thông tin đơn và các thẻ, tính ngược từ thành phẩm giao
   khách.
   - Cột: Bước, Số lượng (m), Số lượng (kg), Hao hụt áp dụng, Chi phí (đ), Chi phí/m thành phẩm (đ/m).
   - Dòng:
     1. Thành phẩm giao khách (số lượng đặt);
     2. Thành phẩm nhuộm ra (÷ B/C TP) + dòng chi phí Nhuộm;
     3. Vải mộc (÷ tiêu hao nhuộm, độ co, B/C mộc) + dòng chi phí Dệt;
     4. Sợi (tổng kg sợi; tiêu hao sợi, sợi cặn) + dòng chi phí Sợi;
     5. dòng Thanh lý B/C (trừ);
     6. dòng Tổng chi phí / Đơn giá.
   - Hình thức bán **Mộc**: bỏ các dòng Nhuộm (thành phẩm giao = vải mộc bán).
   - Hình thức bán **Vải Nhuộm**: bỏ Dệt và Sợi, thay bằng dòng "Mua mộc ngoài" (giá mộc × số mét mộc).
   - (thêm 2026-11-25) **Gia công dệt**: bỏ các dòng Nhuộm như Mộc; dòng Sợi đổi tên "Sợi khách giao", hiện số kg,
     chi phí 0. **Gia công nhuộm**: bỏ Dệt và Sợi; dòng "Mộc khách giao" hiện số mét mộc, chi phí 0. Cả 2 loại không có
     dòng Thanh lý B/C.
5. Các thẻ theo thứ tự: **Giá bán & lợi nhuận → Thông số vải → Nhuộm → Ngành Dệt → Sợi** → Tham số → Cảnh báo → Lịch
   sử.
   - Nhuộm ẩn khi Mộc; Ngành Dệt và Sợi ẩn khi Vải Nhuộm.
   - (thêm 2026-11-25) Nhuộm ẩn khi Gia công dệt; Ngành Dệt và Sợi ẩn khi Gia công nhuộm. Gia công dệt: thẻ Sợi vẫn
     hiện (để xem số kg sợi khách cần giao), có dòng ghi chú "Gia công dệt: khách giao sợi, không tính tiền sợi", giá
     sợi không bắt buộc, thành tiền 0.
   - (thêm 2026-11-25) Ô "Hình thức bán" có 5 lựa chọn; chọn Gia công dệt / Gia công nhuộm thì Loại đơn tự thành
     "Gia Công" (BR-91). Ô giá mộc mua ngoài chỉ hiện khi Vải Nhuộm. Phiếu gia công: ô giá bán ghi "Giá bán (phí gia
     công)".
   - Nội dung từng thẻ giữ như cũ.
6. **Cảnh báo hiện ngay trong thẻ liên quan**, ở đầu thẻ đó:
   - sợi, giá sợi, tỷ lệ sợi -> thẻ Sợi;
   - Se, chi số, độ săn, spandex, hồ, mắc, cone, định mức dệt -> thẻ Ngành Dệt;
   - nhuộm, liên hệ TCDN -> thẻ Nhuộm;
   - GP / OP, F&I -> thẻ Giá bán & lợi nhuận;
   - độ co, thông số vải -> thẻ Thông số vải.
   - Thẻ Cảnh báo vẫn giữ để xem tất cả một chỗ.
   - Tên thẻ có cảnh báo hiện thêm số cảnh báo, ví dụ "Sợi (2)".
7. Thanh nút: giữ nguyên.

Đổi giao diện Màn hình 2 (2026-11-27), thay mục 3, 4, 5 của đổi giao diện 2026-11-23 (cho dễ thấy chỗ nhập). Thứ tự
từ trên xuống:
1. Tiêu đề, ô tóm tắt: giữ nguyên.
2. **Dòng hướng dẫn** (chỉ khi phiếu còn sửa được): "① Điền Thông tin đơn → ② Nhập ở các thẻ ✏️ → ③ Xem Giá bán & lợi
   nhuận → ④ Lưu nháp / Gửi duyệt".
3. **Khối Thông tin đơn**, dải tiêu đề nền xanh + nhãn "Nhập liệu":
   - hiện sẵn các ô chính: Nhà máy nhuộm, Khách hàng (+ "Thêm khách hàng"), Mã vải, Số lượng đặt (m), Hình thức bán,
     Loại giá, Giá mộc mua ngoài (chỉ khi Vải Nhuộm);
   - mục thu gọn **"Thông tin thêm"** (bấm mới mở): Thị trường, Loại đơn hàng, Style, Ngày giao hàng, Ngày tính giá,
     Số OC, Lý do ngoại lệ độ co, Lý do độ co thấp / bằng 0, Ghi chú;
   - phiếu "Độ co thấp" chưa có lý do: mục "Thông tin thêm" tự mở, tiêu đề ghi thêm "Độ co thấp – cần lý do".
4. **Bỏ khung Chuỗi nhu cầu giữa trang**; Chuỗi nhu cầu thành 1 thẻ riêng (nội dung như cũ, chỉ xem).
5. Các thẻ theo thứ tự: **✏️ Giá bán & lợi nhuận → Chuỗi nhu cầu → Thông số vải → ✏️ Nhuộm → ✏️ Ngành Dệt → ✏️ Sợi
   → ✏️ Tham số → Cảnh báo → Lịch sử**. Thẻ ẩn theo hình thức bán như cũ; số cảnh báo vẫn hiện trong ngoặc.
6. Khung / bảng sửa được: dải tiêu đề nền xanh + nhãn "Nhập liệu". Khung / bảng chỉ xem (Chuỗi nhu cầu, Thông số vải
   nguồn Peace / WFX, bảng kết quả, bảng chi phí): dải xám + nhãn "Chỉ xem". Ứng dụng chỉ tô màu dải tiêu đề, không tô
   cả nền khung.
7. Phiếu chỉ xem (đã gửi duyệt, đã duyệt, đã hủy…): không hiện dòng hướng dẫn, dấu ✏️ và nhãn "Nhập liệu".
8. Khung "Tạo costsheet mới" và thanh nút: giữ nguyên.
9. (thêm 2026-11-27, sau khi dùng thử) Bảng nhập nhiều dòng (Bảng sợi, Dòng Se, Bảng cone, các bảng Nhuộm, Chi phí vào
   giá vốn, Tham số): nhập liền một mạch không phải chờ; dưới mỗi bảng có nút **"Áp dụng & tính"** để tính lại phiếu.
   Ô lẻ vẫn tự tính khi đổi. Lưu nháp / Gửi duyệt luôn lấy cả số đang nhập trong bảng.

Màn hình 3 – Việc chờ tôi (nhóm Sales):
- các bảng chỉ xem theo nhóm: Chờ tôi duyệt, Bị trả lại, Đã duyệt chưa có OC, Giá sợi hết hiệu lực, (SO) Tỷ giá tháng
  này, Mã vải thiếu sợi;
- chọn 1 dòng + "Mở".

Màn hình 4 – Dữ liệu mã vải (nhóm Phòng SO), 2 thẻ:
- **Tải Peace/WFX**: ô chọn 1-4 file; "Kiểm tra"; ô tổng hợp (mới / thay đổi / không đổi / thiếu sợi / lỗi); bảng kết
  quả có công tắc "Chỉ hiện mã mới / thay đổi / lỗi"; "Lưu N mã"; 5 lần cập nhật gần nhất.
- **Tra cứu & nhập tay**: bộ lọc (từ khóa, nguồn, chỉ mã thiếu sợi); bảng chọn 1 dòng; chi tiết thông số + sợi; nút
  "Thêm mã vải", "Sửa", "In nhãn" (1-4 mã + REMARK).

Màn hình 5 – Định mức và tham số (nhóm Phòng SO), 4 thẻ:
- **Bộ định mức**: danh sách bộ; xem từng bảng của bộ chọn (mở rộng 2026-11-23: danh sách "Bảng" có thêm "Spandex cộng
  thêm"); (sửa 2026-11-23: bỏ ô chọn "Bảng"; các bảng của bộ chọn chia thành 4 thẻ con, mỗi bảng hiện thẳng với tiêu đề:
  **Dệt** (Đơn giá theo phút, Tham số Se, Tham số Mắc / Kiểm, Định mức Hồ, Định mức Dệt, Chi số, Spandex cộng thêm),
  **Nhuộm HCM** (tiêu chuẩn, công đoạn đặc biệt, tính năng đặc biệt), **Nhuộm TCDN** (quy trình, hóa chất CPB /
  Tenter), **Danh mục chọn**); "Tải file mẫu"; tải lên + ngày hiệu lực + ghi chú ->
  kiểm tra -> "Lưu bộ định mức".
- **Tham số chung**: danh sách bộ; form điền sẵn bộ mới nhất; "Lưu bộ tham số mới". (sửa 2026-11-25:
  - chọn 1 bộ để xem (mặc định bộ mới nhất);
  - nội dung chia 5 thẻ con theo ngành: **Sợi / Dệt / Nhuộm HCM / Nhuộm TCDN / Giá bán & chung**;
  - mỗi thẻ có các ô tham số rời của ngành đó và bảng của ngành (bảng discount sản lượng ở Dệt, Nhuộm HCM, Nhuộm TCDN;
    bảng % B/C ở Giá bán & chung) — bảng sửa trong ô như Excel, thêm / xóa dòng được;
  - SO chọn ngày hiệu lực rồi bấm "Lưu bộ tham số mới" (lưu cả 5 thẻ một lần, kiểm tra BR-65, BR-88);
  - người không có SO chỉ xem.)
- **Hệ số theo mã hàng**: bảng chọn dòng; "Thêm", "Sửa", "Ngừng dùng".
- **Ngày lễ**: bảng; "Thêm", "Xóa".

Màn hình 6 – Tỷ giá (nhóm Phòng SO): form Tháng / Năm / Tỷ giá + "Lưu tỷ giá"; bảng các tháng (mới nhất trên cùng).

Màn hình 7 – Khách hàng (nhóm Phòng SO): tìm kiếm; bảng chọn dòng (Mã KH, Tên, Team, Người tạo, Ngày tạo, Đang dùng);
"Tải danh sách khách hàng" (xem trước rồi lưu); "Sửa".

Nhóm menu bên trái:
- **Sales**: Màn hình 1, 2, 3.
- **Phòng SO**: Màn hình 4, 5, 6, 7.

Quyền màn hình và vai trò do quản trị viên cấp (giống ứng dụng Tính giá sợi):

| Nhóm người dùng | Vai trò cần cấp | Màn hình |
|---|---|---|
| Sales | SALES + FS1 hoặc FS2 | 1, 2, 3, 4 (chỉ tra cứu + in nhãn), 5 (chỉ xem) |
| Trưởng team | TRUONG_TEAM + FS1 hoặc FS2 | 1, 2, 3, 4 (chỉ tra cứu + in nhãn), 5 (chỉ xem) |
| Trưởng đơn vị | TRUONG_DON_VI | 1, 2, 3, 4 (chỉ tra cứu + in nhãn), 5 (chỉ xem) |
| SO | SO | 1, 2 (chỉ xem), 3, 4, 5, 6, 7 |
| PD | PD | 3, 4 |

### Screen 1: Danh sách costsheet (landing page)
- **Purpose:** xem, lọc mọi costsheet được phép xem (UC-27); tạo mới; xuất Excel.
- **Bộ lọc:**
  - Từ khóa (text: số costsheet / mã vải / OC / style);
  - Trạng thái (chọn nhiều, mặc định tất cả trừ Đã thay thế);
  - Team, Sales, Khách hàng, Nhà máy nhuộm, Loại đơn, Loại giá;
  - Ngày tính giá từ - đến (mặc định 90 ngày gần nhất);
  - "Chỉ phiên bản mới nhất" (bật);
  - "Chỉ dưới ngưỡng GP/OP" (tắt).
- **Số liệu tổng hợp:** số phiếu; Chờ duyệt; Đã duyệt; Đã chốt đơn; Dưới ngưỡng GP/OP; Độ co thấp / bằng 0.
- **Bảng** (sắp xếp mặc định Ngày tính giá giảm dần). Cột:
  - Số costsheet, Phiên bản, Trạng thái;
  - Ngày tính giá, Sales, Team, Khách hàng, Thị trường, Loại đơn, OC, Mã vải, Hình thức bán, Nhà máy nhuộm, Loại giá;
  - Số mét;
  - Giá bán (VND/m), Giá bán (USD/m), Giá vốn (VND/m), F&I (VND/m), GP%, OP%;
  - Cảnh báo (GP/OP thấp, độ co thấp);
  - Người duyệt, Ngày duyệt.
  - Trống: "Chưa có costsheet nào phù hợp bộ lọc."
- **Actions:**
  - "Tạo costsheet" -> Màn hình 2 (UC-15);
  - chọn 1 dòng + "Mở" -> Màn hình 2 (UC-29);
  - "Xuất Excel" -> UC-28.

### Screen 2: Costsheet
- **Purpose:** lập, tính, xem, duyệt 1 costsheet (UC-15..UC-26, UC-29).
- **Khối A – Thông tin đơn:** các trường 4.11, OC, loại giá, trạng thái, số costsheet, phiên bản, người lập, người
  duyệt, lý do trả lại / hủy.
- **Khối B – Thông số vải:**
  - tên vải, nguồn dữ liệu, khổ, mật độ dọc / ngang, g/m, g/m2 (mộc và TP);
  - m/kg; độ co; độ co mắc;
  - chỉ đọc khi nguồn Peace / WFX; sửa được khi nguồn "Nhập tay" (nút "Sửa thông số vải", UC-14), ô đã sửa tô màu;
  - nút "In nhãn".
- **Khối C – Sợi:**
  - bảng dòng sợi dọc / ngang: tên sợi, T/M, tỷ lệ, đơn vị giá, giá, ngày nhập giá, sợi cặn, Se, Hồ (lý do gợi ý),
    tiêu hao, lượng sợi kg, thành tiền;
  - giá thanh lý sợi cặn;
  - tổng tỷ lệ, tổng chi phí sợi;
  - nút "Xác nhận giá sợi hôm nay".
- **Khối D – Ngành Dệt:**
  - dòng Se (4.13), sản lượng Se ước tính và chênh lệch;
  - từ 2026-11-23: các cột như file Excel: Hướng, Hệ sợi (gợi ý sẵn, chọn lại được), Chi số (gợi ý sẵn, gõ lại được),
    Độ săn (gợi ý sẵn, gõ lại được), SL yêu cầu (gợi ý sẵn); không hiện chi số chuyển đổi; dòng gợi ý theo BR-86; dòng
    lỗi BR-81 / BR-82 / BR-84 hiện thông báo ở thẻ Cảnh báo;
  - từ 2026-11-23: đầu thẻ hiện ô "Số mét mộc", "Hệ số số lượng" kèm lý do (ví dụ "Thí Nghiệm -> 2", "7.500 m -> 1,025",
    "Vải Nhuộm -> không áp dụng"); bảng công đoạn thêm cột "Nhân hệ số SL" (✓ cho Mắc Hồ, Mắc phân băng, Cone, Dệt, Kiểm
    theo BR-23) và "Thành tiền sau hệ số (đ)"; cột "Hệ số mã hàng" (BR-24) giữ nguyên;
  - nguyên liệu hồ, nhóm tổng canh, Mắc phân băng, cone (chi số gõ tự do, từ 2026-11-23), gia công;
  - bảng công đoạn: SL, định mức, thành tiền; hệ số số lượng;
  - bảng khoản mục đ/m (Se, Dệt);
  - tổng chi phí ngành Dệt, đơn giá CM.
- **Khối E – Nhuộm:** theo nhà máy nhuộm, nội dung 4.15 (HCM) hoặc 4.16 (TCDN):
  - các dòng, định mức, hệ số, tiêu hao;
  - chi phí/kg, chi phí/m;
  - tổng chi phí nhuộm.
  - Hình thức bán = Mộc: khối này ẩn. (sửa 2026-11-25: Gia công dệt cũng ẩn.)
- **Khối F – Giá bán và lợi nhuận:**
  - đơn vị và giá bán; chi phí vào giá vốn;
  - commission, F&I (ẩn / hiện theo BR-29), lãi vay;
  - bảng VND / USD: Giá bán, Giá vốn, GP, GP%, S&A, Commission, F&I, Lãi vay, OP, OP%, Giá có VAT;
  - ngưỡng GP / OP.
- **Khối G – Tham số:** bảng tham số 4.6 (mặc định / đang dùng; ô đã sửa tô màu). (sửa 2026-11-25: chia nhóm theo ngành
  Sợi / Dệt / Nhuộm HCM / Nhuộm TCDN / Giá bán & chung; ở mỗi ngành có dòng "Hệ số discount đang áp dụng" kèm lý do (ví
  dụ "Đại trà 5.000 ≤ SL < 10.000 m mộc"), sales sửa được (BR-46); % B/C hiện theo hình thức bán của phiếu.)
- **Khối H – Cảnh báo** (BR-80) và **Lịch sử / phiên bản** (4.19).
- **Ô tô màu cho người duyệt:** tham số đã sửa, thông số vải đã sửa, độ co ≤ 5% / ngoại lệ, GP / OP dưới ngưỡng, giá
  chi phí phát sinh đã sửa.
- **Actions:**
  - Theo trạng thái và vai trò; nút không được phép thì ẩn.
  - "Lưu nháp" (UC-17), "Gửi duyệt" (UC-20); UC-16 tự chạy khi đổi ô (sửa 2026-11-23: bỏ nút "Tính lại"). (sửa
    2026-11-27: các bảng nhập nhiều dòng – Bảng sợi, Dòng Se, Bảng cone, các bảng Nhuộm, Chi phí vào giá vốn, Tham số –
    nhập liền không tính sau mỗi ô; nút "Áp dụng & tính" dưới mỗi bảng chạy UC-16; Lưu nháp / Gửi duyệt luôn lấy số
    đang nhập trong bảng. Ô lẻ vẫn tự tính.)
  - "Thêm khách hàng" (UC-18), "Sao chép" (UC-19), "Sửa thông số vải" (UC-14).
  - "Duyệt" (UC-21), "Trả lại" (UC-22).
  - "Tạo phiên bản mới" (UC-23), "Lưu OC" / "Chốt đơn" (UC-24).
  - "Hủy" (UC-25), "In nhãn" (UC-26).
  - "Xác nhận giá sợi hôm nay" (UC-16 với BR-44).
- **Sau mỗi thao tác:** hiện thông báo của UC; lỗi hiện thành danh sách, mỗi lỗi 1 dòng.
- **Sắp xếp (sửa 2026-11-27):** khối Thông tin đơn chỉ hiện sẵn ô chính, các ô khác ở mục "Thông tin thêm"; Chuỗi nhu
  cầu thành thẻ riêng sau Giá bán & lợi nhuận; thẻ có ô nhập mang dấu ✏️; khung nhập có dải tiêu đề xanh "Nhập liệu",
  khung chỉ xem dải xám "Chỉ xem"; dòng hướng dẫn 4 bước ở đầu phiếu còn sửa được (chi tiết ở Giao diện đã chốt).

### Screen 3: Việc chờ tôi
- **Purpose:** UC-30.
- **Bảng theo nhóm:**
  - Chờ tôi duyệt;
  - Bị trả lại;
  - Đã duyệt chưa có OC;
  - Giá sợi hết hiệu lực;
  - SO: tỷ giá tháng này, mã vải thiếu sợi.
- **Cột:** Số costsheet, Phiên bản, Khách hàng, Mã vải, Sales, Ngày tính giá, GP%, OP%, Lý do.
- **Trống:** "Không có việc nào đang chờ bạn."
- **Actions:** chọn dòng + "Mở" -> Màn hình 2.

### Screen 4: Dữ liệu mã vải
- **Purpose:** UC-01..UC-04, UC-26 (theo mã vải).
- **Khu tải file** (SO):
  - chọn 1-4 file; nút "Kiểm tra" (UC-01);
  - kết quả: số liệu tổng hợp + bảng chi tiết, công tắc "Chỉ hiện mã mới / thay đổi / lỗi";
  - nút "Lưu N mã" (UC-02);
  - 5 lần cập nhật gần nhất (4.3).
- **Tra cứu:**
  - từ khóa, nguồn, "chỉ mã thiếu sợi";
  - bảng: Mã vải, Tên vải, Nguồn, Khổ mộc, Mật độ dọc / ngang mộc, g/m mộc, Khổ TP, g/m TP, Độ co, Độ co mắc,
    Ngày tạo, Cập nhật lúc;
  - chọn 1 mã -> xem thông số + dòng sợi.
- **Actions:**
  - "Thêm mã vải" / "Sửa" (UC-03, SO và PD);
  - "In nhãn" (UC-26: nhập 1-4 mã và REMARK).

### Screen 5: Định mức và tham số
- **Purpose:** UC-06..UC-11.
- **Bộ định mức:**
  - danh sách bộ (mã, hiệu lực từ, ghi chú, người tải);
  - chọn bộ để xem các bảng (UC-08);
  - "Tải file mẫu" (UC-06);
  - "Tải lên bộ định mức" với ngày hiệu lực, ghi chú -> kiểm tra -> "Lưu bộ định mức" (UC-07).
- **Bộ tham số chung:**
  - danh sách bộ theo ngày hiệu lực;
  - form 4.6 điền sẵn bộ mới nhất;
  - "Lưu bộ tham số mới" (UC-09).
- **Hệ số theo mã hàng:** bảng 4.7; "Thêm" / "Sửa" / "Ngừng dùng" (UC-10).
- **Ngày lễ:** bảng; "Thêm" / "Xóa" (UC-11).

### Screen 6: Tỷ giá
- **Purpose:** UC-05.
- **Form:** Tháng, Năm (mặc định tháng hiện tại), Tỷ giá.
- **Bảng:** Tháng, Năm, Tỷ giá, Người cập nhật, Lúc cập nhật (mới nhất trên cùng).
- **Actions:** "Lưu tỷ giá" (UC-05).

### Screen 7: Khách hàng
- **Purpose:** UC-12, UC-13.
- **Khách hàng:**
  - tìm kiếm; bảng (Mã KH, Tên, Team, Người tạo, Ngày tạo, Đang dùng);
  - "Tải danh sách khách hàng" (UC-12);
  - "Sửa" (UC-13).

### Screen 8: Gia công nhuộm (thêm 2026-11-25)
- **Menu:** nhóm Sales, ngay dưới "Costsheet": "Gia công nhuộm". Người xem: SALES, TRUONG_TEAM, TRUONG_DON_VI, SO.
- **Purpose:** UC-40..UC-46.
- **Phần trên – Danh sách phiếu** (UC-44): bộ lọc (từ khóa, trạng thái, khách hàng, khoảng ngày 90 ngày gần nhất); bảng
  các phiếu; chọn 1 dòng + "Mở"; nút "Tạo phiếu gia công" (UC-40: khách hàng, số hợp đồng, đơn vị gia công mặc định
  **TCDN**, ngày tính giá hôm nay).
- **Phiếu đang mở:**
  - đầu phiếu: số phiếu, trạng thái, sales, người duyệt, tỷ giá, bộ định mức / tham số; ô Khách hàng, Số hợp đồng, Đơn
    vị gia công (HCM / TCDN), Ngày tính giá, Ghi chú;
  - ô tổng: Tổng số lượng (m), Tổng chi phí, Tổng giá GC, GP, %GP (tô màu khi dưới ngưỡng);
  - **bảng dòng mã hàng** sửa trong ô (thêm / xóa dòng): % B/C, Mã hàng, Style, Số OC, ODNO, g/m, g/m2, Độ co (%), Số lượng
    (m), Đơn giá nhận GC (đ/m), Nguyên liệu nhuộm, Cấp màu; cột chỉ đọc: Tổng định mức (đ/m), Định mức TP (đ/m), Thành
    tiền chi phí, Thành tiền giá GC, GP, %GP;
  - **"Chi tiết dòng"**: chọn 1 dòng -> công đoạn ngoài quy trình (tick + giá hóa chất + số lần xử lý thêm), WR, phẩm nhuộm
    đặc biệt + giá, tỷ trọng (Blended), 2 tính năng đặc biệt, báo giá riêng 7 khoản mục (HCM: các lựa chọn 4.15); bảng
    các dòng chi phí của dòng đó (7 khoản mục, hệ số h);
  - tự tính khi đổi ô, "Có thay đổi chưa lưu"; cảnh báo hiện ngay trên bảng dòng;
  - nút: "Lưu nháp", "Gửi duyệt", "Duyệt", "Trả lại", "Hủy", "Sao chép", "Xuất Excel" (hiện theo quyền / trạng thái).
- **Màn hình 5 (sửa 2026-11-25):** thẻ con "Nhuộm TCDN" của Tham số chung có thêm bảng "Hệ số vận hành công đoạn" (4.24),
  sửa trong ô.
- **Màn hình 3 Việc chờ tôi (sửa 2026-11-25):** người duyệt thấy thêm phiếu gia công Chờ duyệt; sales thấy phiếu gia
  công bị Trả lại.

## 9. Acceptance criteria (Tiêu chí nghiệm thu)

**Dữ liệu vải**
- [ ] AC-01 (UC-01, BR-01, BR-02): Cho 4 file trong `Master vai`, khi Kiểm tra, thì mã GEF29900023 thành EF29900023;
  291 mã có ở cả 2 nguồn lấy theo Peace; 89 mã chỉ có ở WFX vẫn có.
- [ ] AC-02 (UC-02): Cho kết quả AC-01, khi Lưu, thì tra cứu ES36040126 và EL37140026 thấy đủ thông số và sợi.
- [ ] AC-03 (BR-70): Cho file thiếu cột TCFNO, khi Kiểm tra, thì hiện "File <tên> không đúng mẫu: thiếu cột TCFNO." và
  không lưu gì.
- [ ] AC-04 (UC-03, BR-01): Cho PD nhập tay mã ZZ12340026, khi sau đó SO tải file Peace có mã này, thì thông số lấy
  theo Peace và nguồn = Peace.
- [ ] AC-05 (BR-72): Cho mã nhập tay chỉ có sợi dọc, khi lưu, thì hiện "Cần ít nhất 1 sợi dọc và 1 sợi ngang."

**Gợi ý tick**
- [ ] AC-06 (BR-06, BR-08, BR-09): Cho mã EM35790026 (sợi dọc TC 34/1 sợi đơn không se), khi tạo costsheet, thì mọi
  sợi dọc tick Hồ với lý do "Sợi spun không se".
- [ ] AC-07 (BR-08): Cho mã EM04150201 (sợi dọc DTY 75D/36F HIM có 400T/M), khi tạo costsheet, thì không gợi ý Hồ và
  các sợi có T/M được tick Se.
- [ ] AC-08 (BR-07): Cho tên vải chứa "KHONG SE" và không có điều kiện BR-08, thì không gợi ý Hồ.

**Tính toán**
- [ ] AC-09 (BR-10..BR-28): Nhập lại 4 costsheet trong `File kết quả` với cùng dữ liệu và cùng các bảng định mức /
  tham số của file, thì GP% và OP% (OP chưa trừ lãi vay vì lãi vay = 0) khớp, sai lệch ≤ 0,01%:

  | File | GP% | OP% |
  |---|---|---|
  | EM3579 | 19,17% | 11,01% |
  | TM01510696 | 15,20% | 6,64% |
  | EF3532 | 19,99% | 11,92% |
  | EM04150201 | 23,02% | 15,26% |

- [ ] AC-10 (BR-23): Cho số mét mộc 7.500, thì hệ số số lượng = 1,025; cho Thí Nghiệm, thì = 2.
- [ ] AC-11 (BR-12): Cho khổ mộc 150 cm, sợi ngang có Se, thì tiêu hao = 6,19% (làm tròn 2 số).
- [ ] AC-12 (BR-24): Cho mã ES17020213, thì định mức Vật tư dệt = định mức bảng × 1,12 + 231.
- [ ] AC-13 (BR-26): Cho HCM, Thí Nghiệm, thì HCTN và Tiền lương nhuộm tiêu chuẩn gấp 2, các khoản mục khác không đổi.
- [ ] AC-14 (BR-25): Cho TCDN, công đoạn Coating chưa nhập giá, thì giá hóa chất tính 0 và hiện "Thiếu giá hóa chất
  cho Coating: đang tính 0 (liên hệ TCDN)."
- [ ] AC-15 (BR-28): Cho lãi vay 500 đ/m, thì OP giảm đúng 500 đ/m.
- [ ] AC-16 (BR-29): Cho loại giá CIF và F&I = 0, khi gửi duyệt, thì hiện "Loại giá CIF cần nhập chi phí vận chuyển
  (và bảo hiểm)."; cho FOB thì ô F&I bị ẩn.

**Độ co**
- [ ] AC-17 (BR-14): Cho độ co 3% và không chọn lý do, khi gửi duyệt, thì bị chặn với thông báo BR-14; khi chọn "Mộc
  khách đã ổn định", thì độ co = 0, gửi được và phiếu được tô màu.
- [ ] AC-18 (BR-15): Cho "Có pre-setting", thì kết quả tính giống hệt khi không chọn, và phiếu gửi duyệt được dù độ co
  ≤ 5%.

**Luồng duyệt**
- [ ] AC-19 (UC-20, BR-28): Cho GP% = 12%, khi gửi duyệt, thì hiện cảnh báo GP nhưng vẫn chuyển Chờ duyệt.
- [ ] AC-20 (UC-21, BR-53): Cho phiếu team FS1, thì Trưởng team FS1 và Trưởng đơn vị thấy nút Duyệt; Trưởng team FS2
  không thấy phiếu; sales FS1 không thấy nút Duyệt; phiếu do Trưởng team FS1 tự lập thì chính người đó duyệt được.
- [ ] AC-21 (UC-22, BR-33): Cho trả lại không lý do, thì hiện "Vui lòng nhập lý do trả lại."
- [ ] AC-22 (UC-23, BR-35): Cho phiên bản 2 chỉ đổi OC và ghi chú, khi gửi duyệt, thì được duyệt tự động và phiên bản 1
  chuyển Đã thay thế.
- [ ] AC-23 (BR-35): Cho phiên bản 2 đổi giá bán, khi gửi duyệt, thì chuyển Chờ duyệt.
- [ ] AC-24 (UC-24, BR-36, BR-40): Cho phiếu Đã duyệt, nhập "KDV10-SX-LO-0726-6564.1," thì OC lưu thành
  KDV10-SX-LO-0726-6564.1; bấm Chốt đơn -> Đã chốt đơn.
- [ ] AC-25 (BR-40): Cho OC "6564.1", thì hiện thông báo sai định dạng.
- [ ] AC-26 (BR-40): Cho OC đã chốt ở phiếu khác, khi chốt đơn, thì hiện "OC <OC> đã được chốt ở costsheet <số>."
- [ ] AC-27 (UC-25): Cho phiếu Đã chốt đơn, thì không có nút Hủy.
- [ ] AC-28 (BR-39): Cho phiếu Đã duyệt, khi SO đổi tỷ giá tháng đó, thì số trên phiếu không đổi.

**Giá sợi, sao chép, khách hàng**
- [ ] AC-29 (BR-44): Cho giá sợi nhập thứ 2 ngày 2026-11-16, gửi duyệt thứ 2 ngày 2026-11-23 (5 ngày làm việc), thì
  bị chặn; nếu có ngày lễ trong khoảng đó thì được gửi.
- [ ] AC-30 (UC-19): Cho sao chép phiếu tháng trước, thì phiếu mới có số mới, Nháp, ngày tính giá hôm nay, tỷ giá tháng
  này, OC trống.
- [ ] AC-31 (UC-18, BR-50): Cho gõ "ichimura sangyo." khi đã có "Ichimura Sangyo", thì hiện "Khách hàng Ichimura Sangyo
  đã có."; gõ "Ichimura" thì hiện danh sách tên tương tự trước khi cho tạo.
- [ ] AC-32 (BR-46): Cho sales sửa S&A từ 10,09% thành 9%, thì ô S&A tô màu, hiện mặc định 10,09%, và bản đã lưu giữ
  9%.

**Quyền, định mức, tỷ giá**
- [ ] AC-33 (BR-52): Cho sales FS2, thì danh sách không có phiếu FS1; mở bằng số phiếu FS1 thì hiện "Bạn không có
  quyền xem costsheet này."
- [ ] AC-34 (BR-61): Cho ngày tính giá tháng 12/2026 chưa có tỷ giá, thì hiện "Chưa có tỷ giá tháng 12/2026. Liên hệ
  SO cập nhật."
- [ ] AC-35 (UC-07, BR-62): Cho bộ định mức mới hiệu lực 2027-01-01, thì phiếu ngày tính giá 2026-12-31 dùng bộ cũ,
  phiếu ngày 2027-01-02 dùng bộ mới.
- [ ] AC-36 (BR-63): Cho file định mức thiếu sheet DinhMucDet, thì hiện "Sheet DinhMucDet dòng 0: thiếu sheet." và
  không lưu.
- [ ] AC-37 (UC-26, BR-75): Cho in nhãn EM19600015, thì nhãn có WIDTH 154 CM / 61 INCH, WEIGHT 234 G/M2 / 360 G/MT,
  DENSITY WARP 608 / WEFT 236, sợi dọc 1 "DTY 150D/48F/1 HIM" 38,59%; in 4 mã thì 4 nhãn trên 1 trang.
- [ ] AC-41 (UC-14, BR-47): Cho mã nguồn Peace, thì không có nút "Sửa thông số vải" và mọi ô thông số chỉ đọc; cho mã
  nguồn "Nhập tay", thì sales sửa mật độ ngang TP, độ co và chi phí tính lại, ô đã sửa tô màu, dữ liệu gốc không đổi.
- [ ] AC-42 (BR-41, BR-50): Cho khách hàng Ichimura Sangyo mã ICHI, thì costsheet mới có số dạng CS-ICHI-2026-NNNNN.
- [ ] AC-43 (BR-51): Cho tài khoản có SALES nhưng chưa có FS1 / FS2, khi tạo costsheet, thì hiện "Tài khoản của bạn
  chưa được gán team FS1 / FS2. Liên hệ quản trị viên."

**Mở rộng 2026-11-23: chi số và độ săn gõ tự do**
- [ ] AC-44 (BR-81): Cho bảng spandex ban đầu, thì công thức cho đúng chi số chuyển đổi của cả 56 chi số của sheet "Dữ
  liệu" (ví dụ "75D/2 + CB" = 170, "20/2" = 531,6, "30 + 150D + 300D" = 627,2, "60/2 + SP 40" = 193,2).
- [ ] AC-45 (BR-81, BR-83, BR-20): Cho dòng Se chi số "50D/2 + CB" (không có trong danh sách), độ săn 900, thì chi số
  chuyển đổi = 120 (dùng trong tính, không hiển thị), hệ sợi gợi ý = Filament, có định mức Se (có bấm đốt) và không có
  cảnh báo định mức; sales đổi hệ sợi sang Spun thì định mức tính theo dòng "SE - XƠ NGẮN".
- [ ] AC-57 (BR-86): Cho phiếu mới mã EF35320026 (sợi dọc "WHITE CACBON 20D/3F/1" 400T/M và "DTY 75D/72F/1 SIM FD"
  400T/M tick Se), khi Tính lại lần đầu, thì bảng dòng Se có sẵn dòng Dọc, độ săn 400, chi số đọc từ tên sợi (có "+ CB"
  cho sợi carbon), SL = sản lượng Se ước tính; sales sửa chi số / xóa dòng thì lần Tính lại sau không tạo lại dòng.
- [ ] AC-46 (BR-81): Cho chi số "75 DD", khi gửi duyệt, thì bị chặn với "Chi số "75 DD" không đúng dạng. Ví dụ đúng:
  75D/2 + CB, 30/2, 45 + 75D + SP 70."
- [ ] AC-47 (BR-82): Cho độ săn 30, thì hiện "Độ săn 30 không hợp lệ: phải là số nguyên từ 50 đến 3.000 T/M."
- [ ] AC-48 (BR-84): Cho chi số "75D + SP 20" khi bảng spandex chưa có SP 20, thì hiện "Chưa có số cộng thêm cho spandex
  SP 20. Liên hệ SO bổ sung."; SO tải bộ định mức có SP 20 = 10 thì chi số chuyển đổi = 85.
- [ ] AC-49 (BR-81): Cho chi số có trong danh sách nhưng SO đặt số chuyển đổi khác công thức, thì app dùng số của danh
  sách.
- [ ] AC-50 (UC-07, BR-63): Cho file bộ định mức 12 sheet (không có `Spandex`), thì vẫn lưu được và bảng spandex giữ SP 40
  = 16, SP 70 = 22; file có sheet `Spandex` trùng loại thì bị từ chối.
- [ ] AC-52 (BR-51, BR-85): Cho tài khoản chỉ có vai trò SO, khi Tạo costsheet, thì tạo được, team = "SO", và chính
  người đó gửi duyệt rồi Duyệt được.
- [ ] AC-53 (BR-31, BR-85): Cho phiếu Nháp của sales FS1, thì người có vai trò SO thấy và bấm được Lưu nháp, Gửi duyệt,
  Hủy; phiếu Chờ duyệt của sales thì SO bấm được Duyệt / Trả lại.
- [ ] AC-54 (BR-52): Cho phiếu team "SO", thì sales FS1 / FS2 và trưởng team không thấy phiếu; trưởng đơn vị thấy.
- [ ] AC-55 (hồi quy BR-52, BR-53): Sales FS1 vẫn không thấy phiếu FS2 và không thấy nút Duyệt; trưởng team FS1 vẫn duyệt
  được phiếu FS1.
- [ ] AC-56 (BR-23, Screen 2): Cho phiếu Thí Nghiệm, thì đầu thẻ Ngành Dệt hiện "Hệ số số lượng: 2 (Thí Nghiệm)"; bảng
  công đoạn có ✓ "Nhân hệ số SL" ở Mắc Hồ, Mắc phân băng, Cone, Dệt, Kiểm và "Thành tiền sau hệ số" = Thành tiền × 2 ở
  các dòng đó, các dòng khác bằng Thành tiền; tổng các dòng "Thành tiền sau hệ số" = Tổng chi phí ngành Dệt.
**Sửa 5 điểm (2026-11-23)**
- [ ] AC-58 (Screen 5): Mở thẻ Bộ định mức, thì thấy 4 thẻ con Dệt / Nhuộm HCM / Nhuộm TCDN / Danh mục chọn; thẻ Nhuộm
  HCM hiện 3 bảng, thẻ Nhuộm TCDN hiện 2 bảng, không cần chọn trong ô "Bảng".
- [ ] AC-59 (4.16, BR-25): Danh sách công đoạn ngoài quy trình TCDN có đúng 28 công đoạn có định mức (có Suse 2, Ageing
  room 2, Setting, Soaping; không có Suse 1, Ageing room, Kuster, Dyeing, Dry); chọn bất kỳ công đoạn nào trong danh sách
  thì không có cảnh báo "không có định mức".
- [ ] AC-60 (BR-87) (bỏ từ 2026-11-26, thay bằng AC-84..AC-88): Cho dòng Se Ngang chi số "150D" 388 kg, thì ô SL cone 1 hiện 388 và Chi số cone 1 hiện "150D";
  sales sửa SL cone 1 thành 300 thì giữ 300 khi Se Ngang đổi.
- [ ] AC-61 (UC-16): Ở thẻ Nhuộm, chọn cấp màu khác, thì chi phí nhuộm, chuỗi nhu cầu và GP% đổi ngay không cần bấm nút;
  màn hình hiện "Có thay đổi chưa lưu"; bấm "Lưu nháp" thì dòng này mất; mở lại phiếu thì thấy số đã lưu.
- [ ] AC-62 (BR-86): Cho phiếu có dòng Se do app gợi ý, khi bỏ tick Se ở 1 sợi dọc hoặc đổi số mét, thì dòng Se gợi ý cập
  nhật theo (không còn cảnh báo lệch sản lượng Se); dòng sales đã sửa SL giữ nguyên; phiếu CS-ICHI-2026-00001 (dòng Se lưu
  trước) giữ nguyên dòng Se.
**Gom bảng tham số (2026-11-25)**
- [ ] AC-63 (BR-23, 4.6.1): Cho bộ tham số hiệu lực 25/11/2026, phiếu Đại trà 7.500 m mộc thì hệ số Dệt = 1,05 (không
  phải 1,025); 20.000 m -> 1; 20.001 m -> 0,95; 50.000 m -> 0,92; 4.000 m -> 1,1; Thí nghiệm -> 2.
- [ ] AC-64 (hồi quy, 4.6.1 interpolate): Phiếu có ngày tính giá trước 25/11/2026 (dùng bộ cũ) với 7.500 m mộc vẫn ra
  1,025; 4 costsheet thật AC-09 cho đúng GP% / OP% cũ.
- [ ] AC-65 (BR-25, BR-26): Bảng discount TCDN và HCM của bộ mới cho cùng hệ số như trước (TCDN 50.000 m -> 0,95, nhuộm
  120 m -> 1,2, partial 80 m -> 1,5; HCM thí nghiệm hoặc 200 kg -> 2 cho Hóa chất thuốc nhuộm và Tiền lương).
- [ ] AC-66 (BR-16, 4.6.2): % B/C lấy theo bảng; SO đổi Vải Thành Phẩm thành 6% / 3% ở bộ mới thì phiếu Vải Thành Phẩm
  dùng 6% / 3%, phiếu Mộc không đổi.
- [ ] AC-67 (BR-88): SO lưu bộ có 2 khoảng Dệt Đại trà chồng nhau thì bị từ chối với thông báo BR-88; thiếu dòng Vải
  Nhuộm trong bảng % B/C thì bị từ chối.
- [ ] AC-68 (Màn hình 5): Thẻ Tham số chung có 5 thẻ con theo ngành; bộ 25/11/2026 có giá thanh lý sợi cặn = 0 và TP B/C
  = 0; bộ 01/01/2026 vẫn hiện số cũ.
- [ ] AC-69 (BR-46, Khối G): Trên phiếu, thẻ Tham số chia theo ngành; sales sửa hệ số discount Dệt đang áp dụng từ 1,05
  thành 1,0 thì chi phí Dệt đổi theo, ô tô màu; không sửa được ngưỡng GP / OP.
- [ ] AC-70 (BR-89): Lấy 1 phiếu Mộc, đổi Hình thức bán sang Gia công dệt (cùng số liệu). Chi phí ngành Dệt và số mét mộc
  giữ như phiếu Mộc; chi phí sợi = 0 nhưng số kg sợi từng dòng giữ như phiếu Mộc; nhuộm = 0; Thanh lý B/C = 0; Tổng chi
  phí = Chi phí ngành Dệt; gửi duyệt được khi giá sợi = 0.
- [ ] AC-71 (BR-90): Lấy 1 phiếu Vải Nhuộm (TCDN và HCM), đổi sang Gia công nhuộm. Chi phí nhuộm và số mét mộc giữ
  nguyên; không có tiền mua mộc; Thanh lý B/C = 0; Tổng chi phí = Chi phí nhuộm; gửi duyệt được khi chưa nhập giá mộc.
- [ ] AC-72 (BR-91, UC-15): Chọn Gia công dệt hoặc Gia công nhuộm thì Loại đơn tự thành "Gia Công"; sales đổi lại "Sản
  Xuất" thì app giữ "Sản Xuất" và cách tính vẫn theo Hình thức bán.
- [ ] AC-73 (BR-16, BR-88, 4.6.2): Bộ tham số đã lưu (chưa có dòng gia công): phiếu Gia công dệt dùng % B/C của dòng Mộc,
  Gia công nhuộm dùng dòng Vải Nhuộm. SO sửa dòng Gia công dệt thành 3% / 0% và lưu thì phiếu Gia công dệt dùng 3%; SO
  lưu bộ thiếu 2 dòng gia công vẫn được.
- [ ] AC-74 (Màn hình 2): Gia công dệt ẩn thẻ Nhuộm, thẻ Sợi có ghi chú và cột thành tiền 0, Chuỗi nhu cầu có dòng "Sợi
  khách giao"; Gia công nhuộm ẩn thẻ Ngành Dệt và Sợi, Chuỗi nhu cầu có dòng "Mộc khách giao"; không phiếu gia công nào
  có dòng Thanh lý B/C.
- [ ] AC-75 (hồi quy): 4 costsheet thật của AC-09 cho cùng kết quả; phiếu Mộc, Vải Thành Phẩm, Vải Nhuộm tính như trước;
  phiếu đã lưu trước mở rộng hiển thị không đổi.
- [ ] AC-76 (BR-92, BR-93, BR-95, file S-ONE): Phiếu TCDN khách S-ONE, 2 dòng DVDP-SAFM001-PA (OC ...8643: 7.404 m; OC ...8644:
  6.707 m), g/m 245, g/m2 167, độ co 1%, Poly, % B/C 0, công đoạn Chuẩn Bị, Coating (giá hóa chất 1.861), Cire, Kiểm
  Trung Gian, Kiểm Hàng-Đóng Gói, tính năng UPF50+ 868, đơn giá GC 7.905,403: mỗi dòng Tổng định mức = 4.860,52 đ/m
  (lệch ≤ 0,01), dòng chi phí Coating = 2.836,37, Cire = 414,67; tổng chi phí 68.586.774,56, tổng giá GC 111.553.141,73,
  %GP 38,52%.
- [ ] AC-77 (BR-92 n): Coating có số lần xử lý thêm 1 thì 6 khoản (trừ hóa chất) của Coating gấp đôi, hóa chất giữ 1.861.
- [ ] AC-78 (BR-94): Dòng có báo giá riêng (Hóa chất 3.000, Nhân công 500) thì Tổng định mức = 3.500 bất kể công đoạn tick.
- [ ] AC-79 (BR-94 HCM): Phiếu đơn vị HCM: dòng nhuộm tiêu chuẩn cho cùng chi phí đ/m như phiếu Gia công nhuộm 1 mã
  (Hình thức bán Gia công nhuộm, HCM) cùng thông số.
- [ ] AC-80 (UC-40, UC-43, BR-98, BR-99): Tạo phiếu thì Đơn vị gia công đã chọn TCDN; gửi duyệt khi thiếu số lượng bị
  từ chối với danh sách mục thiếu; gửi đủ -> Chờ duyệt -> trưởng team duyệt cả phiếu 1 lần; phiếu Đã duyệt không sửa
  được, sao chép ra phiếu Nháp số mới; sales team khác không thấy phiếu.
- [ ] AC-81 (UC-46): Xuất Excel ra sheet `Output` có đầu phiếu, dòng TỔNG CỘNG và đủ cột F-09, số khớp màn hình.
- [ ] AC-82 (BR-02 sửa): Nhập nhanh mã "GC12345678" được nhận đúng mã GC12345678; mã Peace "GEF29500023SN04" vẫn thành
  EF29500023; mã "C1234" vẫn báo lỗi BR-02 như cũ.
- [ ] AC-83 (hồi quy): Costsheet TCDN thường (AC-09 R2) cho cùng kết quả (không dùng hệ số vận hành); bộ tham số cũ hiện
  bảng hệ số vận hành với giá trị ban đầu.
**Bảng cone (2026-11-26)**
- [ ] AC-84 (BR-100 se chung): Cho mã EF27920021 (sợi ngang tick Se: DTY 150D/48F/1 400 T/M 3,02% và BR1 30D/6F/1
  400 T/M 0,59%), thì bảng cone có đúng 1 dòng gợi ý chi số "150D + 30D", SL = tổng SL 2 dòng Se Ngang, Gồm sợi ghi cả
  2; bảng chi phí có 1 dòng "Cone 1" với SL đó.
- [ ] AC-85 (BR-100 se riêng, nhiều cone): Cho 3 dòng Se Ngang sợi chính khác chi số (ví dụ 75D 21 kg, 150D 30 kg, 300D
  10 kg), thì bảng cone có 3 dòng theo đúng thứ tự, mỗi dòng đúng chi số và SL của dòng Se; 2 dòng Se cùng chi số và độ
  săn thì gộp 1 dòng cone, SL cộng lại (ví dụ EF15690111: EC 75D và EY 75D cùng 400 T/M -> 1 dòng "75D").
- [ ] AC-86 (BR-100 spandex, cảnh báo): Cho Se Ngang TR 40/2 800 T/M và SPANDEX 40D 800 T/M, thì 1 dòng cone "40/2 + SP
  40"; cho sợi carbon cùng độ săn với 2 sợi chính, thì carbon gộp vào sợi khớp tỷ lệ nhất và có cảnh báo "Kiểm tra lại
  cone…" (không chặn gửi duyệt).
- [ ] AC-87 (BR-100 g, 4.14a): Sales sửa SL dòng cone thành 300 thì giữ 300 khi Se Ngang đổi; sales xóa 1 dòng gợi ý thì
  tính lại không tạo lại dòng đó; sales thêm 1 dòng cone thì dòng đó được tính tiền; dòng có SL mà trống chi số -> cảnh
  báo chặn như BR-22.
- [ ] AC-88 (BR-100 h, Screen 2, hồi quy): Phiếu không có dòng Se Ngang thì thẻ Ngành Dệt không có bảng cone và tiền
  cone = 0; costsheet lưu trước 2026-11-26 có cone 1 "150D" 388 kg mở ra thấy 1 dòng cone "150D" 388 kg và cùng tiền
  cone, cùng GP% như trước (kể cả khi không có Se Ngang); phiếu Đã duyệt mở ra kết quả không đổi.
- [ ] AC-89 (Screen 2, sửa 2026-11-27): Mở 1 phiếu Nháp, thì khối Thông tin đơn hiện sẵn Nhà máy nhuộm, Khách hàng,
  Mã vải, Số lượng đặt, Hình thức bán, Loại giá; các ô Thị trường, Loại đơn hàng, Style, Ngày giao, Ngày tính giá, Số
  OC, Lý do ngoại lệ độ co, Ghi chú nằm trong mục "Thông tin thêm" đang thu gọn; sửa 1 ô trong mục đó thì phiếu tính
  lại như trước.
- [ ] AC-90 (Screen 2, sửa 2026-11-27): Phiếu "Độ co thấp" chưa có lý do, thì mục "Thông tin thêm" tự mở và tiêu đề có
  "Độ co thấp – cần lý do"; phiếu Vải Nhuộm thì ô Giá mộc mua ngoài hiện ở hàng ô chính.
- [ ] AC-91 (Screen 2, sửa 2026-11-27): Không còn khung Chuỗi nhu cầu giữa trang; thẻ thứ 2 là "Chuỗi nhu cầu" với đúng
  các dòng và số như khung cũ (kể cả dòng "Sợi khách giao" / "Mộc khách giao" của phiếu gia công).
- [ ] AC-92 (Screen 2, sửa 2026-11-27): Phiếu Nháp: có dòng hướng dẫn 4 bước; tên thẻ Giá bán & lợi nhuận, Nhuộm, Ngành
  Dệt, Sợi, Tham số có ✏️; khung Thông tin đơn và các bảng sửa được có dải xanh "Nhập liệu"; Chuỗi nhu cầu có dải xám
  "Chỉ xem". Phiếu Chờ duyệt / Đã duyệt: không có dòng hướng dẫn, không có ✏️, không có nhãn "Nhập liệu".
- [ ] AC-93 (Screen 2, hồi quy 2026-11-27): Cùng 1 phiếu trước và sau đổi giao diện cho cùng Đơn giá, Giá vốn, Giá bán,
  GP%, OP%; mọi ô nhập cũ vẫn có và sửa được; Lưu nháp, Gửi duyệt, Lưu OC vẫn chạy; số cảnh báo trên tên thẻ vẫn đúng.
- [ ] AC-94 (UC-16 sửa 2026-11-27, Screen 2): Nhập giá ở 2 dòng liền nhau của Bảng sợi thì không phải chờ, Tổng chi phí
  sợi chưa đổi; bấm "Áp dụng & tính" dưới bảng thì phiếu tính lại và Tổng chi phí sợi đổi theo giá mới; nhập vào bảng
  rồi bấm Lưu nháp không bấm "Áp dụng & tính" thì số đã nhập vẫn được tính và lưu; đổi 1 ô lẻ (ví dụ Số lượng đặt) vẫn
  tự tính như trước.
- [ ] AC-51 (hồi quy): 4 costsheet thật của AC-09 cho cùng GP% / OP% như trước; phiếu đã lưu trước mở rộng hiển thị
  không đổi; Cone chi số "150D" cho cùng định mức như trước.
- [ ] AC-38 (UC-28): Xuất Excel theo bộ lọc, file có đúng số dòng và các cột của Màn hình 1.
- [ ] AC-39 (UC-30): Cho phiếu bị trả lại, thì sales lập phiếu thấy phiếu trong "Bị trả lại".
- [ ] AC-40 (UC-12): Cho file Data_clean, thì chỉ thêm khách hàng FS1 / FS2, bỏ dòng "TEAM FORECAST" và tên trùng.

## 10. Open questions (Câu hỏi mở)
- Giả định: Tham số chung: sales sửa được trên từng phiếu mọi tham số trừ độ co tối thiểu, ngưỡng GP / OP và số ngày
  hiệu lực giá sợi (chỉ SO sửa).
- Giả định: Số costsheet dạng `CS-<mã KH>-YYYY-NNNNN`, số thứ tự chung trong năm; mã KH tự tạo từ 4 chữ cái đầu tên
  khách hàng nếu chưa có, SO sửa được.
- Giả định: Trưởng team, trưởng đơn vị được tự duyệt phiếu của chính mình.
- Giả định: Tài khoản, quyền màn hình, vai trò và team do quản trị viên cấp trên `/admin` (giống ứng dụng Tính giá
  sợi); ứng dụng không có màn hình quản lý người dùng riêng.
- Giả định: Lãi vay đơn hàng trả chậm được trừ vào OP (theo người dùng); vì vậy kết quả OP% sẽ khác file Excel cũ khi
  lãi vay > 0.
- Giả định: "Có pre-setting" tạm thời chỉ là lý do cho độ co thấp, tính như bình thường; quy tắc riêng sẽ bổ sung khi
  chốt.
- Giả định: Nhãn in giống sheet PRINT (luôn thông số thành phẩm, tối đa 4 nhãn / trang).
- Giả định: Sales chỉ sửa thông số vải trên phiếu khi mã vải nguồn "Nhập tay"; thông số sửa chỉ lưu trong phiếu, không
  đổi dữ liệu gốc.
- Giả định: Đếm 5 ngày làm việc: thứ 2-6, trừ ngày lễ SO nhập, không tính ngày nhập giá.
- Giả định: Trong đợt 1, giá hóa chất Coating / Santa / Bonding / Soaping / tính năng đặc biệt TCDN và chi phí phát
  sinh do sales nhập tay; đợt 2 sẽ lấy tự động từ báo giá ngành.
- Giả định: Bảng quy trình sản xuất tham khảo TCDN (sheet "QT sản xuất") chưa có ở đợt 1; đợt 4 tự cập nhật từ dữ liệu
  ngành.
- Giả định: Một OC chỉ được chốt ở 1 costsheet; cùng Main OC có thể có nhiều Summary OC ở các costsheet khác nhau.
- Giả định: Gửi duyệt phiên bản ≥ 2 mà không đổi giá bán, giá vốn, GP% thì duyệt tự động.
- Giả định (triển khai): Thêm UC-31..UC-39 cho các bảng và bước xem trước mà màn hình cần; các UC này chỉ áp dụng BR có
  sẵn.
- Giả định (triển khai): Khi bảng còn trống, app tạo sẵn bộ định mức, bộ tham số, hệ số mã ES17020213 / ES17020413 và
  các danh mục theo số của file Excel, hiệu lực 2026-01-01.
- Giả định (triển khai): BR-20 hệ số nhân công Se làm đúng như file Excel: chia cho số người phân bổ theo cọc
  (round(33 × số cọc ÷ tổng cọc)), không chia thêm số ca; làm theo câu chữ tài liệu thì lệch nặng so với 4 file thật.
- Giả định (triển khai): BR-20 bấm đốt carbon có tính phí (tốc độ 400, 28 cọc theo bảng định mức). Trong 4 file Excel
  thật phần này bị lỗi công thức nên bằng 0; vì vậy mã có sợi "+ CB" cho GP% thấp hơn file cũ 0,01–0,03 điểm %. Bài
  kiểm tra AC-09 đặt phí bấm đốt = 0 để so đúng với file.
- Giả định (triển khai): BR-25 mọi chi phí hóa chất công đoạn ngoài quy trình TCDN chia (1 − tiêu hao) như tài liệu;
  dòng "Kiểm trung gian" Excel tự thêm khi có WR không làm vì tài liệu không nêu.
- Giả định (triển khai): BR-27 Vải Nhuộm dùng cùng công thức thanh lý B/C cho cả HCM và TCDN.
- Giả định (triển khai): Quyền: không có người đăng nhập (chạy kiểm thử) = mọi vai trò; quản trị viên mở mọi ứng dụng =
  SO + Trưởng đơn vị. Người không có vai trò SO chỉ xem các màn hình Phòng SO (PD vẫn thêm / sửa mã vải).
- Giả định (triển khai): Ngày nhập giá sợi (BR-44) đổi thành hôm nay khi sửa giá / đơn vị giá hoặc bấm xác nhận; sao
  chép và phiên bản mới giữ ngày cũ.
- Giả định (triển khai): Tỷ lệ % hiện trên màn hình nhân 100 (ví dụ 2,4%), lưu dạng 0..1.
- Giả định (triển khai): Các thẻ trong màn hình Costsheet luôn tải sẵn (không tải khi mở thẻ) để không mất số đang gõ.
- Giả định (triển khai): "Gửi duyệt" lưu số đang nhập rồi gửi duyệt trong một lần bấm.
- Giả định (triển khai): Xuất Excel khi không có dòng nào vẫn có 1 dòng trống để giữ tiêu đề cột.
- Mở rộng 2026-11-23: chi số (dòng Se, cone) và độ săn gõ tự do; app tự đổi chi số chuyển đổi theo quy luật sheet "Dữ
  liệu" (BR-81), tự xác định hệ sợi (BR-83), thêm bảng spandex trong bộ định mức (4.5.13, BR-84), độ săn 50-3.000
  (BR-82). Phiếu đã lưu không đổi.
- Mở rộng 2026-11-23: Phòng SO toàn quyền trên costsheet (lập để thử, sửa, duyệt, tự duyệt; BR-31, BR-51..BR-53, BR-85);
  phiếu do người chỉ có vai trò SO lập thuộc team "SO", không lẫn vào FS1 / FS2. Phiếu đã lưu giữ nguyên team.
- Mở rộng 2026-11-23: Hệ số số lượng (BR-23) hiện rõ ở đầu thẻ Ngành Dệt kèm lý do, và trong bảng công đoạn (cột "Nhân
  hệ số SL", "Thành tiền sau hệ số"); cách tính không đổi.
- Giả định (triển khai, mở rộng 2026-11-23): Đọc chi số từ tên sợi (BR-86):
  - filament "…nD/fF/k" -> "nD", thêm "/k" khi k ≥ 2;
  - spun "N/1" -> "N", "N/k" -> "N/k";
  - bỏ phần tỷ lệ trong ngoặc như "(65/35)";
  - các phần nối bằng " + " theo thứ tự trong tên; có chữ carbon thì thêm " + CB";
  - ví dụ "WHITE CACBON 20D/3F/1" -> "20D + CB", "TC 45/2 (65/35)" -> "45/2".
- Giả định (triển khai, mở rộng 2026-11-23): "SP 40/2" dùng spandex 40 (bỏ "/2"), khớp chi số "40/2 + SP 40/2" của danh
  sách.
- Mở rộng 2026-11-26: bảng cone thay 2 ô cone 1 / cone 2 (4.14a); app tự xác định sợi se chung (carbon, spandex đi
  kèm sợi chính) / se riêng (các sợi chính khác nhau) và gợi ý mỗi cone 1 dòng (BR-100, thay BR-87); bảng chỉ hiện khi
  có Se Ngang. Quy luật kiểm trên 163 mã vải có ≥ 2 sợi se ngang (EF27920021 se chung, EF15690111 se riêng). Phiếu đã
  lưu giữ số cone cũ.
- Giả định (mở rộng 2026-11-26): Sợi phụ nhận biết theo tên sợi (danh sách chữ ở BR-100 a); sợi carbon / spandex có tên
  khác danh sách thì sales tự gộp trong bảng cone.
- Giả định (mở rộng 2026-11-26): Hai sợi chính khác loại nhưng cùng chi số và cùng độ săn (như EC 75D và EY 75D) gộp 1
  dòng cone vì dòng Se cũng gộp như vậy; tiền cone như nhau vì tính theo kg × định mức của chi số.
- Giả định (triển khai, mở rộng 2026-11-26): Phiếu lưu trước được chuyển sang bảng cone ngay khi mở (không cần cập
  nhật dữ liệu); lần lưu tiếp theo ghi bảng cone. Hai sợi chính cùng chi số và độ săn đã gộp 1 dòng Se (BR-86) nên
  carbon đi kèm được gộp vào cả dòng đó (ví dụ EF32090024: "150D + 20D"); sales tách lại trong bảng cone nếu cần.
- Giả định (triển khai, mở rộng 2026-11-26): Hai bài kiểm tra cũ của AC-60 (BR-87) được đổi theo BR-100 vì BR-87 đã bỏ;
  phần AC-60 vẫn đúng (1 chi số -> điền sẵn, sales sửa thì giữ) vẫn được kiểm tra.
- Mở rộng 2026-11-27: sắp xếp lại Màn hình 2 cho dễ thấy chỗ nhập: Thông tin đơn chỉ hiện ô chính + mục "Thông tin
  thêm"; Chuỗi nhu cầu thành thẻ riêng; ✏️ trên thẻ có ô nhập; dải xanh "Nhập liệu" / xám "Chỉ xem"; dòng hướng dẫn 4
  bước. Không đổi dữ liệu, quy tắc, công thức (AC-89..AC-93).
- Giả định (mở rộng 2026-11-27): "Khung nhập liệu màu khác" làm bằng dải tiêu đề nền xanh vì ứng dụng không tô được cả
  nền khung; thẻ Giá bán & lợi nhuận cũng mang ✏️ vì sales nhập giá bán ở đó.
- Mở rộng 2026-11-27 (sau khi dùng thử): nhập giá sợi phải chờ sau mỗi ô -> bảng nhập nhiều dòng nhập liền, nút "Áp
  dụng & tính" dưới bảng (người dùng chọn cách a); UC-16 sửa, AC-94.
- Giả định (triển khai, mở rộng 2026-11-23): Chi số "34/2 + CB" trong danh sách là 333 (đã làm tròn), công thức ra 332,71;
  vì số trong danh sách được ưu tiên nên kết quả không đổi.
- Giả định (triển khai, mở rộng 2026-11-23): Người có SO và cả 2 team, hoặc chỉ có SO, lập phiếu thuộc team "SO". Khách
  hàng do người chỉ có SO thêm có team "Chung".
- Giả định (triển khai, mở rộng 2026-11-23): Dòng Se gợi ý chỉ tạo 1 lần; sales xóa hết dòng thì không tạo lại.
- (thay bởi BR-89..BR-91 từ 2026-11-25) Giả định (triển khai, đổi giao diện 2026-11-23): "Chọn gia công thì không hiện Dệt và Sợi" được hiểu theo cách tính
  hiện có: chỉ khi Hình thức bán = Vải Nhuộm thì chi phí Dệt và Sợi bằng 0, nên mới ẩn 2 thẻ đó. Loại đơn hàng "Gia
  Công" hiện vẫn tính sợi và dệt như file Excel. Đơn sales gia công nhuộm (khách đưa mộc) hiện chọn Hình thức bán = Vải
  Nhuộm và giá mộc = 0. Phiếu gia công nhiều mã / nhiều OC trên 1 lần tính thuộc đợt 3 (NGC). Muốn Loại đơn "Gia Công"
  tự bỏ chi phí sợi và dệt thì cần đổi quy tắc tính (Prompt 05).
- Giả định (triển khai, đổi giao diện 2026-11-23): Thanh lý B/C hiện thành 1 dòng riêng (số âm) trong Chuỗi nhu cầu, để
  tổng khớp đơn giá.
- Mở rộng 2026-11-23 (sửa 5 điểm):
  - bảng định mức chia thẻ Dệt / Nhuộm HCM / Nhuộm TCDN / Danh mục;
  - công đoạn ngoài quy trình TCDN chỉ còn 28 công đoạn có định mức;
  - cone 1 điền sẵn SL và chi số (BR-87);
  - phiếu tự tính khi đổi ô, bỏ nút "Tính lại" (UC-16);
  - dòng Se gợi ý tự cập nhật (BR-86 sửa).
- Mở rộng 2026-11-25:
  - tham số chia theo ngành;
  - discount sản lượng thành bảng 4.6.1 theo bậc như quy định công ty (bỏ chia đều cho bộ mới);
  - % B/C thành bảng 4.6.2;
  - giá thanh lý mặc định 0;
  - tạo sẵn bộ tham số hiệu lực 25/11/2026; bộ cũ giữ nguyên.
- Mở rộng 2026-11-25 (2 loại gia công): Hình thức bán thêm Gia công dệt (chỉ tính chi phí dệt, hiện số kg sợi khách
  giao) và Gia công nhuộm (chỉ tính chi phí nhuộm, hiện số mét mộc khách giao); không trừ thanh lý B/C; % B/C có 2 dòng
  mới; chọn gia công thì Loại đơn tự thành "Gia Công". Thay giả định "đổi giao diện 2026-11-23" về Loại đơn Gia Công.
- Mở rộng 2026-11-25 (phiếu gia công nhuộm nhiều mã): Màn hình 8 mới; phiếu nhiều dòng mã hàng / OC, mã hàng và độ co
  sales gõ, tính đúng file NGC (hệ số vận hành, hóa chất công đoạn không chia độ co, số lần xử lý thêm, báo giá riêng),
  duyệt 1 lần cả phiếu, xuất Excel như sheet Output; đơn vị gia công mặc định TCDN, vẫn chọn được HCM. Gia công dệt giữ
  như costsheet thường (không nhập giá sợi). Sửa BR-02 (chữ G đầu mã).
- Giả định (mở rộng 2026-11-25, phiếu gia công): Phiếu gia công nhuộm 1 mã trên Màn hình 2 (Hình thức bán = Gia công
  nhuộm) vẫn giữ để không mất dữ liệu; cách làm chính cho hàng nhận gia công là Màn hình 8.
- Giả định (mở rộng 2026-11-25, phiếu gia công): Tỷ giá lấy theo tháng như costsheet (file NGC gõ tay); giá nhận gia
  công nhập đ/m.
- Giả định (mở rộng 2026-11-25, phiếu gia công): Hóa chất bảng × số lần xử lý thêm (không phải 1 + n) đúng như file NGC.
- Giả định (triển khai, phiếu gia công 2026-11-25): WR trên phiếu gia công tính như costsheet TCDN hiện có. Đã đối
  chiếu file NGC: giá hóa chất WR theo nhóm g/m2 và 6 khoản của dòng WR giống bộ định mức; chỉ khác 2 điểm: (1) file NGC
  không chia 6 khoản WR cho (1 − tiêu hao 1%), app có chia (lệch khoảng 4,6 đ/m); (2) file NGC tự cộng thêm chi phí
  Kiểm Trung Gian (khoảng 82 đ/m) mỗi khi có WR, app thì không (sales tick Kiểm Trung Gian nếu có). Chờ người dùng chốt.
- Giả định (triển khai, sửa lỗi 2026-11-25, người dùng chốt): WR chạy trên máy tenter nên chi phí WR vẫn ÷ (1 − 1%);
  tiêu hao nhuộm KHÔNG cộng 1% của WR (4% tiêu chuẩn = 3% nhuộm + 1% hoàn tất); chọn WR thì app tự thêm dòng "Kiểm
  trước WR" (Kiểm Trung Gian) như file TCDN (dòng 104), tiêu hao của dòng này cộng vào tiêu hao nhuộm; sales tick thêm
  Kiểm Trung Gian thì tính thêm 1 dòng như file. Áp dụng cho costsheet TCDN và phiếu gia công nhuộm TCDN.
- Giả định (triển khai, phiếu gia công 2026-11-25): Thông báo lỗi mã vải (BR-02) giữ nguyên câu cũ, vì đã được kiểm
  tra trong bài kiểm thử cũ; chỉ sửa cách bỏ chữ G.
- Giả định (triển khai, phiếu gia công 2026-11-25): Excel F-09 có 2 sheet (`Thông tin`, `Output`) thay vì đầu phiếu nằm
  trên cùng sheet Output.
- Giả định (mở rộng 2026-11-25, gia công): Mỗi phiếu gia công 1 mã vải; nhiều mã / nhiều OC trình 1 lần làm ở đợt 3
  (NGC), trước mắt dùng "Sao chép".
- Giả định (mở rộng 2026-11-25, gia công): Ngưỡng GP% / OP% của phiếu gia công dùng chung ngưỡng của bộ tham số.
- Giả định (triển khai, gia công 2026-11-25): Ở khung "Tạo costsheet mới", chọn gia công mà để Loại đơn mặc định "Sản
  Xuất" thì app lưu Loại đơn "Gia Công"; chọn Loại đơn khác thì giữ lựa chọn đó.
- Giả định (triển khai, gia công 2026-11-25): Phiếu Vải Nhuộm vẫn kiểm tra giá sợi như trước (không đổi); chỉ 2 loại gia
  công bỏ kiểm tra giá sợi và hạn giá sợi.
- Giả định (mở rộng 2026-11-25, gia công): Gia công dệt vẫn tính chi phí Se (nếu có) và gia công ngoài, vì đây là chi phí
  của ngành Dệt.
- Giả định (mở rộng 2026-11-25): Quy định ghi "loại đơn căn cứ mã OC trên ERP"; app vẫn dùng ô Loại đơn hàng sales chọn
  (chưa tự suy ra từ OC).
- Giả định (mở rộng 2026-11-25): Độ co tối thiểu giữ một số chung 5% (không tách theo nhà máy / nguyên liệu).
- Giả định (triển khai, mở rộng 2026-11-25):
  - Bộ tham số ban đầu khi cài mới (01/01/2026) giữ giá thanh lý 15.000 / 5.000 và cách chia đều kiểu Excel, để 4 costsheet thật vẫn khớp; giá thanh lý = 0 nằm ở bộ hiệu lực 25/11/2026.
  - Bộ 25/11/2026 chỉ tự tạo khi đã có bộ cũ trước ngày đó (máy đang dùng); máy cài mới thì SO tự lưu bộ mới.
  - Bảng Dệt ghi đúng "1 < SL < 5.000" nên 0–1 m mộc không khớp dòng nào: hệ số 1 kèm cảnh báo.
  - Sửa tay các tham số rời cũ trên phiếu chỉ còn tác dụng với bộ tham số lưu trước 25/11/2026.
  - Chưa chọn hình thức bán thì % B/C lấy dòng Vải Thành Phẩm.
- Giả định (triển khai, sửa 5 điểm 2026-11-23):
  - Ô cone 1 để trống luôn lấy theo gợi ý (xóa ô thì gợi ý quay lại).
  - Không gợi ý cone cho Vải Nhuộm.
  - Dòng "Có thay đổi chưa lưu" chỉ mất khi lưu, kể cả khi sales gõ lại số cũ.
  - Gợi ý dòng Se mà sales đã sửa hoặc xóa thì không tạo lại.
- Giả định (mở rộng 2026-11-23): Tự tính chạy cho cả phiếu sau mỗi thay đổi (khoảng 1 giây); nếu chậm sẽ cân nhắc quay
  lại nút bấm.
- Giả định (mở rộng 2026-11-23): Phiếu team "SO" vẫn hiện trong Danh sách costsheet và xuất Excel (lọc Team = SO để
  tách); không có màn hình hay luồng riêng cho phiếu thử.
- Giả định (mở rộng 2026-11-23): Danh sách 56 chi số và 17 độ săn cũ giữ làm gợi ý; số chuyển đổi trong danh sách được
  ưu tiên hơn công thức.
- Giả định (mở rộng 2026-11-23): Chỉ dùng hằng số 5.316 cho spun và 20 cho CB như file Excel; nếu cần đổi thì làm thành
  tham số ở lần mở rộng sau.
- Giả định (triển khai): Phần kiểm tra mẫu ("ping") do khung tạo sẵn được giữ lại (không có màn hình nào dùng) vì bài
  kiểm thử đi kèm không được phép xóa.

## 11. Implementation map (filled by the AI)
| Spec item | Code |
|---|---|
| Section 4 | `backend/features/woven_costing/models/` (fabric, master, norm_set, seed_norms, parameter_set, costsheet, costsheet_input, costsheet_result, enums, access) |
| Section 5 (F-01..F-04, F-06) | `builders/file_readers.py` |
| Section 5 (F-05) | `builders/norm_file_builders.py` |
| Section 5 (F-07, F-08) | `builders/document_builders.py` |
| UC-01..UC-39 | `WovenCostingController.<method>()` (names in `docs/plans/woven_costing-implementation-plan.md` §4) -> `services/<method>_service.py` |
| BR-01, BR-71 | `business/fabric_import_business.py` |
| BR-02..BR-04, BR-47, BR-72 | `business/fabric_business.py` |
| BR-05..BR-09 | `business/hint_business.py` |
| BR-10..BR-19, BR-21, BR-80 | `business/costing_business.py`, `quantity_business.py`, `yarn_cost_business.py` |
| BR-20 | `business/twist_business.py` |
| BR-22..BR-24 | `business/weaving_business.py`, `norm_lookup_business.py` |
| BR-25 | `business/dyeing_tcdn_business.py` |
| BR-26 | `business/dyeing_hcm_business.py` |
| BR-27..BR-29 | `business/pricing_business.py` |
| BR-30..BR-41 | `business/workflow_business.py`, `costsheet_business.py` |
| BR-42..BR-44 | `business/submission_business.py` |
| BR-45, BR-46 | `business/costsheet_business.py` |
| BR-50 | `business/customer_business.py` |
| BR-51..BR-53 | `business/access_business.py` |
| BR-60..BR-65, BR-70 | `business/master_business.py`, `norm_business.py` |
| BR-75 | `business/label_business.py` |
| BR-81..BR-84, BR-86 (mở rộng 2026-11-23) | `business/count_business.py`, `twist_business.py`, `hint_business.py`, `norm_lookup_business.py` |
| BR-85, BR-31 / BR-51..BR-53 sửa (mở rộng 2026-11-23) | `business/access_business.py`, `costsheet_business.py` |
| 4.5.13 Spandex, F-05 sheet 13 (mở rộng 2026-11-23) | `models/norm_set.py`, `builders/norm_file_builders.py`, `business/norm_business.py` |
| AC-44..AC-57 | `backend/features/woven_costing/tests/test_extension_20261123.py` |
| Đổi giao diện Màn hình 2 (2026-11-23): Chuỗi nhu cầu, cảnh báo theo thẻ | `builders/demand_chain_builder.py`, `frontend/features/woven_costing/components/costsheet_chain.py`, `pages/costsheet_page.py`; test `tests/test_ui_20261123.py` |
| Sửa 5 điểm (2026-11-23): BR-86 sửa, BR-87, UC-16 tự tính, danh sách công đoạn TCDN, bảng định mức chia thẻ; AC-58..AC-62 | `business/hint_business.py`, `weaving_business.py`, `costsheet_business.py`, `services/get_costsheet_options_service.py`, `builders/dto_builders.py`; `pages/costsheet_page.py`, `pages/norm_parameter_page.py`, `components/costsheet_weaving.py`, `costsheet_toolbar.py`, `working.py`; test `tests/test_fix5_20261123.py` |
| Mở rộng 2026-11-25: 4.6.1, 4.6.2, BR-16/23/25/26/46 sửa, BR-88; AC-63..AC-69 | `models/parameter_tables.py`, `business/discount_business.py`, `builders/parameter_builders.py`, `repositories/norm_repository.py`, `frontend/features/woven_costing/components/parameter_editor.py`, `components/costsheet_tabs.py`; test `tests/test_param_tables_20261125.py` |
| Mở rộng 2026-11-25 (gia công): 4.11 sale_form +2, 4.6.2 +2 dòng, BR-89..BR-91, BR sửa 13/14/16/17/18/19/22/23/25/26/27/42/88; AC-70..AC-75 | `models/enums.py` (NO_DYEING_FORMS, NO_WEAVING_FORMS, JOB_FORMS, BC_FALLBACK), `models/parameter_tables.py` (complete_bc_rows), `business/quantity_business.py`, `costing_business.py`, `weaving_business.py`, `dyeing_hcm_business.py`, `dyeing_tcdn_business.py`, `discount_business.py`, `submission_business.py`, `costsheet_business.py`, `builders/demand_chain_builder.py`, `costsheet_response_builder.py`, `parameter_builders.py`; `frontend/features/woven_costing/components/costsheet_order.py` (BR-91), `costsheet_price.py`, `pages/costsheet_page.py`; test `tests/test_gia_cong_20261125.py` |
| Mở rộng 2026-11-25 (phiếu gia công nhuộm): 4.21..4.24, UC-40..UC-46, BR-92..BR-99, BR-02 sửa, F-09, Screen 8; AC-76..AC-83 | `models/dyeing_job.py`, `models/parameter_tables.py` (OpRateRow), `business/dyeing_job_business.py` (DyeingJobTcdnBusiness, DyeingJobBusiness), `business/dyeing_tcdn_business.py` (stage_cost / standard_chemical), `business/fabric_business.py`, `builders/dyeing_job_builders.py`, `dto/dyeing_job_dto.py`, `repositories/dyeing_job_repository.py`, `services/*_dyeing_job*_service.py`, `services/list_my_tasks_service.py`, `migrations/0001_dyeing_job_order_table_phieu_gia_cong_.py`; `frontend/features/woven_costing/pages/dyeing_job_page.py`, `components/costsheet_dyeing.py` (job_line_dyeing), `components/parameter_editor.py`, `pages/my_tasks_page.py`; test `tests/test_dyeing_job_20261125.py` |
| Mở rộng 2026-11-26 (bảng cone): 4.14a, BR-100 (thay BR-87), BR-22 sửa phần Cone, UC-16, Screen 2 thẻ Ngành Dệt; AC-84..AC-88 (AC-60 thay thế) | `models/costsheet_input.py` (ConeLine, WeavingInput.cone_lines…), `models/costsheet.py` (Costsheet.cone_rows / cone_live: chuyển ô cone 1 / cone 2 cũ khi đọc), `business/cone_business.py` (ConeBusiness: suggest_lines, merge_lines, suggest_cone, check_warnings), `business/costsheet_business.py` (suggested_inputs), `business/weaving_business.py` (Cone 1..n), `dto/costsheet_dto.py` (ConeLineDTO), `builders/costsheet_response_builder.py`; `frontend/features/woven_costing/components/costsheet_weaving.py` (_cone_lines); test `tests/test_cone_split_20261125.py`, `tests/test_fix5_20261123.py` (AC-60 theo BR-100) |
| Đổi giao diện Màn hình 2 (2026-11-27): Thông tin đơn ô chính + "Thông tin thêm", thẻ Chuỗi nhu cầu, ✏️, dải "Nhập liệu" / "Chỉ xem", dòng hướng dẫn, bảng nhập liền + "Áp dụng & tính" (UC-16 sửa); AC-89..AC-94 | `frontend/features/woven_costing/components/marks.py` (heading, tab_label, guide, apply_table), `components/costsheet_order.py`, `components/costsheet_chain.py` (demand_chain_tab), `pages/costsheet_page.py`, `components/costsheet_price.py`, `costsheet_tabs.py`, `costsheet_weaving.py`, `costsheet_dyeing.py`; chỉ đổi màn hình nên kiểm bằng trình duyệt; hồi quy: toàn bộ test cũ (506) |
| Screen 1 | `frontend/features/woven_costing/pages/costsheet_list_page.py` |
| Screen 2 | `pages/costsheet_page.py` + `components/costsheet_*.py` |
| Screen 3 | `pages/my_tasks_page.py` |
| Screen 4 | `pages/fabric_data_page.py` |
| Screen 5 | `pages/norm_parameter_page.py` |
| Screen 6 | `pages/exchange_rate_page.py` |
| Screen 7 | `pages/customer_page.py` |
| Navigation, roles | `frontend/features/woven_costing/manifest.py` |
| Tests | `backend/features/woven_costing/tests/` (AC-09: `test_ac09_real_costsheets.py`) |
