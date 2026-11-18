# Kế hoạch phân tích nghiệp vụ - chuyển "Tính giá sợi" sang app mới

| Ngày | 2026-09-29 |
|---|---|
| Nguồn chính | `docs/business/_sources/tinh-gia-soi-discovery.md`, `docs/business/_sources/sap-xep-menu-theo-don-vi-discovery.md`, `docs/business/yarn_costing.md` (bản chép từ app cũ) |
| Loại việc | CẬP NHẬT tài liệu đã có (giữ nguyên nội dung còn đúng) |

## 1. Chia chức năng
Một chức năng duy nhất (như ghi chép mục 7 và mục "Việc còn lại" - app mới chỉ có Tính giá sợi):

| Mục | Nội dung |
|---|---|
| feature_key | `yarn_costing` (giữ nguyên; chưa có thư mục code trong app mới) |
| Tên hiển thị | Tính giá sợi |
| Nhóm Trang chủ | **cần chốt** (không còn là "Tài chính - Kế toán"; đề xuất "Giá thành sợi" theo ghi chép menu) |
| Biểu tượng | 🧵 |
| Người phụ trách | Phòng SO |
| Mục tiêu | Thay thế hoàn toàn 2 file Excel tính giá sợi S1/S4, từ yêu cầu của Sales đến bảng giá cho kế toán |
| Người dùng | Sales, Xưởng S1, Xưởng S4, Phòng SO, Kế toán, người xem |
| UC / BR / dữ liệu / file / màn hình | Giữ UC-01..UC-41, BR-01..BR-60, mục 4.1-4.19, file 5.1-5.5, Screen 1-8 của tài liệu hiện có |

## 2. Những thay đổi dự kiến trong tài liệu
| # | Thay đổi | Nguồn |
|---|---|---|
| T-01 | Đổi nhóm Trang chủ | "Việc còn lại" ý 1; ghi chép menu mục 5 |
| T-02 | Trạng thái `Implemented` → `Draft` → `Ready for implementation`; ngày cập nhật 2026-09-29 | app mới chưa có code |
| T-03 | Mục 11: đưa về các dòng mẫu (code của app cũ không có ở đây) | quy tắc tài liệu |
| T-04 | Hộp xác nhận "Lưu đóng gói và tính lại": chỉ cảnh báo tính lại khi Phút/kg của loại đang được mã sợi dùng thay đổi; ngược lại ghi "Giá các mã không thay đổi" | "Việc còn lại" ý 3 |
| T-05 | (tuỳ chọn) Hiện lý do nút "Gửi yêu cầu" bị khoá ngay cạnh nút | "Việc còn lại" ý 4 |
| T-06 | Bỏ giả định "tự chuyển dữ liệu đã lưu theo bản cũ" (app mới bắt đầu trống, dữ liệu nhập lại từ Excel) | "Việc còn lại" ý 5 |
| T-07 | Menu giữ như cũ (chưa ghi nhãn đơn vị) cho đến khi khung sườn nâng cấp | ghi chép menu mục 8b |
| T-08 | Khối "Giao diện đã chốt" của app cũ giữ làm đề xuất cho Prompt 2 | mục 8 tài liệu |

## 3. Bảng nguồn (source inventory)
| S-xx | Nội dung | Nguồn |
|---|---|---|
| S-01 | Sales gửi yêu cầu, 5-10 mã/ngày | discovery 1 |
| S-02 | 2 file Excel S1/S4, quy trình 5 bước, lỗi hiện có | discovery 1 |
| S-03 | Thay thế hoàn toàn, giá chỉ là chi phí gia công | discovery 2 |
| S-04 | Sheet Dinh muc (phut), 1. Input NSM, 2. Input tieu hao, Hoi phe, Dong goi, QTCN, tỷ giá | discovery 3 |
| S-05 | Bảng giá, xuất Excel, chi tiết 1 mã, dashboard | discovery 4 |
| S-06..S-23 | QT-01..QT-18 | discovery 5 |
| S-24 | Quy mô 3.400 mã, 20-30 người | discovery 6 |
| S-25 | 7 màn hình + người dùng & nhật ký, 3 đợt | discovery 7 |
| S-26 | Khả năng / cách thay thế đã đồng ý | discovery 8 |
| S-27 | Loại đóng gói mặc định theo xưởng | discovery bổ sung 28/09 |
| S-28 | Chải thô nhiều lượt, bỏ C3.1/C3.2/C3.3 | discovery bổ sung 28/09 |
| S-29 | Nhóm Trang chủ mới, chỉ 1 chức năng | "Việc còn lại" ý 1-2 |
| S-30 | Lỗi hộp xác nhận đóng gói | "Việc còn lại" ý 3 |
| S-31 | Lý do nút "Gửi yêu cầu" bị khoá | "Việc còn lại" ý 4 |
| S-32 | Việc SO làm sau khi nhập dữ liệu | "Việc còn lại" ý 5 |
| S-33 | Menu theo đơn vị, chờ khung sườn | discovery menu 5, 8b |
| S-34 | Toàn bộ UC/BR/AC/giả định đã chốt ở app cũ | `yarn_costing.md` |

## 4. Câu hỏi (vòng 1)
1. Tên nhóm trên Trang chủ.
2. Có làm phần hiện lý do nút "Gửi yêu cầu" bị khoá không.
3. File Excel gốc S1/S4 để đối chiếu giá.
4. Dữ liệu ở app cũ: bắt đầu trống và nhập lại từ Excel hay không.

## 5. Trả lời
- Vòng 1 (2026-09-29): 1 → nhóm Trang chủ "Tính Giá Sợi"; 2 → (a) hiện lý do nút "Gửi yêu cầu" bị khoá; 3 → (b) chuyển dữ
  liệu đã nhập ở app cũ sang; 4 → (a) đặt 2 file Excel thật vào `_sources` (chưa thấy file, nhắc người dùng).
- Vòng 2 - câu hỏi: vị trí app cũ; phạm vi dữ liệu chuyển; cách chuyển; ngày ngừng dùng app cũ; file "Check loss S1 - S4.xlsx".
- Vòng 2 (2026-09-29): 5 → app cũ ở `D:\Vibe Coding\TC-vibe-coding` (dữ liệu: `data\yarn_costing\`, 15 file, có phần lưu theo
  cách cũ C3.1-C3.3); 6 → (a) chuyển tất cả; 7 → (a) chép một lần; 8 → (a) ngừng nhập ở app cũ khi chép; 9 → (b) bỏ qua.
- File Excel `.xlsm` S1/S4: người dùng chọn đặt vào `_sources` nhưng chưa có; không bắt buộc cho tài liệu (giá cũ đối chiếu đã
  có trong dữ liệu app cũ).

## 6. Bảng đối chiếu nguồn
| S-xx | Nội dung | Covered by |
|---|---|---|
| S-01..S-05 | Công việc hiện tại, mong muốn, dữ liệu vào / ra | Mục 1, 4, 5.2-5.5, UC-15..UC-37 |
| S-06..S-23 | QT-01..QT-18 | BR-01..BR-60 (xem mục 11 app cũ), UC-01..UC-41 |
| S-24 | Quy mô | 5.1 (giới hạn file), Giả định mục 10 |
| S-25 | Màn hình | Mục 8 Screen 1-8 |
| S-26 | Khả năng / cách thay thế | UC-39 (xác thực), UC-04/BR-36 (bấm nút tính lại), UC-34 |
| S-27 | Đóng gói mặc định | BR-60, UC-05, UC-15 |
| S-28 | Chải thô nhiều lượt | BR-56..BR-59, 4.4, 4.12.1 |
| S-29 | Nhóm Trang chủ "Tính Giá Sợi", 1 chức năng | Header, mục 1, mục 10 |
| S-30 | Hộp xác nhận đóng gói | BR-62, UC-05, Screen 5, AC-65..AC-67 |
| S-31 | Lý do khoá nút "Gửi yêu cầu" | BR-63, UC-15, Screen 2, AC-68, AC-69 |
| S-32 | Việc SO làm sau khi chuyển | Mục 10 (Giả định) |
| S-33 | Menu theo đơn vị (chờ khung sườn) | Mục 8 ghi chú, mục 10 |
| S-34 | Nội dung đã chốt ở app cũ | Giữ nguyên toàn bộ mục 1-10 |
| S-35 | Chuyển dữ liệu app cũ (chép một lần, giữ nguyên, đọc cách lưu cũ) | 5.6, BR-61, UC-38, AC-62..AC-64 |

---

# Cập nhật 2026-09-29 (lần 2): dùng tiêu hao chải thô của dây chuyền tương đương (C2 ↔ C3)

## 1. Phạm vi
Cập nhật chức năng `yarn_costing` (Tính giá sợi), không thêm chức năng mới. Thay đổi quy tắc BR-58 (tiêu hao của một lượt chải
thô): khi nguyên liệu chạy dây chuyền X mà nhóm tiêu hao chỉ khai báo tiêu hao chải thô ở dây chuyền cùng công nghệ Y, app dùng
số của Y thay vì báo "Chưa tính được".

## 2. Nguồn
| S-xx | Nội dung | Nguồn |
|---|---|---|
| S-36 | Muốn chuyển tiêu hao đã khai báo cho C2 sang C3 khi sợi pha chạy C3 thay vì C2, và ngược lại | tin nhắn người dùng 2026-09-29 |
| S-37 | C2 và C3 (S4) cùng công nghệ, chạy thay nhau được; S1 C1 và C2 cùng công nghệ; S4 C1 (cotton) giữ một lượt | discovery "Bổ sung 2026-09-28", mục 10 tài liệu |
| S-38 | Điểm để ngỏ: "tiêu hao chải thô của một nguyên liệu giống nhau dù chạy C2 hay C3" | discovery "Bổ sung 2026-09-28" |
| S-39 | Hiện có 164 lý do "chưa khai báo tiêu hao ở <dây chuyền>" (S4 59, S1 105); ít nhất 13 mã S1 tính được nhờ quy tắc mới | đếm trên dữ liệu 2026-09-29 |

## 3. Câu hỏi (vòng 1)
1. Cặp dây chuyền dùng thay nhau. 2. Khi có cả hai số. 3. Ghi chú trong chi tiết tính giá. 4. Tính lại các mã đang chờ.
5. Mã đã có giá / đã khoá. 6. Câu báo khi cả hai dây chuyền đều thiếu.

## 4. Trả lời
- Vòng 1 (2026-09-29): 1a, 2a, 3a, 4a, 5a (toàn bộ đề xuất).

## 5. Bảng đối chiếu nguồn
| S-xx | Nội dung | Covered by |
|---|---|---|
| S-36 | Dùng tiêu hao C2 cho C3 và ngược lại | BR-64, BR-58 (sửa), 4.14 `loss_source_stage` / `loss_note`, AC-70..AC-72 |
| S-37 | Cặp dây chuyền cùng công nghệ | Glossary "Dây chuyền tương đương", 4.3 `equivalent_carding`, BR-64 |
| S-38 | Điểm để ngỏ về tiêu hao giống nhau dù chạy C2 / C3 | BR-64, mục 10 "Đã chốt" |
| S-39 | Mã đang chờ vì thiếu tiêu hao ở dây chuyền đang chạy | UC-43, BR-65, Screen 5, AC-75, AC-76 |
| Trả lời 3a | Ghi chú trong chi tiết tính giá / Excel | 4.14, 5.4, Screen 1 và 3, AC-70, AC-77 |
| Trả lời 5a | Câu báo khi cả hai dây chuyền thiếu | BR-16, AC-73 |

---

# Cập nhật 2026-09-29 (lần 3): khai báo thành phần sợi pha bằng file Excel (S1)

## 1. Phạm vi
Cập nhật `yarn_costing`. Thêm cách khai báo thành phần + tỷ lệ cho nhiều nhóm tiêu hao sợi pha cùng lúc bằng file Excel (mẫu
đã gửi bản nháp `mau-khai-bao-thanh-phan-soi-pha-S1-20260929.xlsx`), để nhóm pha của S1 (hiện là "Nhập từ file - chưa khai báo
thành phần" hoặc "Sơ cấp", dùng số chết) tính tiêu hao theo thành phần như S4.

## 2. Nguồn
| S-xx | Nội dung | Nguồn |
|---|---|---|
| S-40 | Muốn file mẫu khai báo thành phần sợi pha S1 kèm danh sách nhóm, khai báo bằng Excel | tin nhắn 2026-09-29 |
| S-41 | S1: 499 nhóm "Nhập từ file" (khoảng 379 tên dạng pha), 296 "Sơ cấp" (khoảng 174 tên dạng pha), 0 nhóm Thứ cấp | dữ liệu app 2026-09-29 |
| S-42 | Công thức S1 dạng tỷ lệ × dòng thành phần, chép thẳng (=H65), tỷ lệ gõ tay; 1 nhóm trỏ nhầm dòng 1 | file S1 sheet "2. Input tieu hao" |
| S-43 | Mã sợi S1 ghi thành phần theo tên ô ("PE", "Viscose/other", "Cotton"); 1.323 mã, 331 mã đã khoá | dữ liệu app 2026-09-29 |
| S-44 | Nhóm PE của S1 chưa có trong app (trùng 5 dòng); người dùng tự sửa trùng ngoài Excel | tin nhắn 2026-09-29 |

## 3. Câu hỏi (vòng 1)
1. Nơi tải file. 2. Xưởng áp dụng. 3. Nhóm được khai báo / tạo mới. 4. Công đoạn thành phần không có tiêu hao. 5. Thành phần của
mã sợi sau khi đổi nhóm. 6. Ai được tải, nhóm đang khoá. 7. Xem trước và tính lại.

## 4. Trả lời
- Vòng 1 (2026-09-29): 1a, 2a, 3a, 4a, 5a, 6a, 7a (toàn bộ đề xuất).

## 5. Bảng đối chiếu nguồn
| S-xx | Nội dung | Covered by |
|---|---|---|
| S-40 | File mẫu + khai báo thành phần bằng Excel | 5.7, UC-44, UC-45, Screen 6, AC-78, AC-85 |
| S-41 | Nhóm S1 Nhập từ file / Sơ cấp → Thứ cấp | BR-67, AC-79 |
| S-42 | Gợi ý từ công thức (bản nháp) | 5.7 (bản nháp tải lên được), AC-85 |
| S-43 | Thành phần mã sợi theo tên ô, mã đã khoá | BR-68, AC-80, AC-81, mục 10 |
| S-44 | Nhóm PE chưa có, trùng tên người dùng tự sửa | BR-66 (không tìm thấy thành phần, trùng tên), mục 10 |
| Trả lời 4a | Tiêu hao tính hoàn toàn theo thành phần | BR-67, AC-79 |
| Trả lời 6a | Quyền như sửa tiêu hao | BR-69, BR-47, AC-84 |
| Trả lời 7a | Xem trước, ngày hiệu lực + lý do, tính lại | UC-45, AC-79 |

# Cập nhật 2026-11-03 (lần 4): mã có mã kế toán chờ nhưng chưa có giá

## 1. Phạm vi
Cập nhật tài liệu `docs/business/yarn_costing.md` (chức năng Tính giá sợi, giữ feature_key `yarn_costing`, nhóm Trang chủ,
biểu tượng, người phụ trách như cũ). Không thêm chức năng mới.

## 2. Nguồn
| ID | Nội dung | Nguồn |
|---|---|---|
| S-01 | S4-1032 không sửa được NSM vì "đã có mã kế toán", dù mã chưa từng có giá (trạng thái Chưa tính được) | tin nhắn người dùng 2026-11-03 |
| S-02 | Màn Nhập NSM & tính giá không có nút "Tạo bản ĐCNSM" cho S4-1032 | tin nhắn người dùng 2026-11-03 |
| S-03 | Mã kế toán của mã nhập từ file chưa tính được giá được giữ chờ, mã coi như đã khoá, gán vào dòng Thường khi dòng được tạo | tài liệu mục 10 (Giả định triển khai) |
| S-04 | BR-32: bản NSM khoá khi có dòng giá có mã kế toán; UC-23/UC-24: mã khoá hiện nút "Tạo bản ĐCNSM", tạo ĐCNSM "bất kể khoá" | tài liệu BR-32, UC-23, UC-24 |
| S-05 | Dữ liệu ngày 2026-11-03: 166 mã có mã kế toán chờ, chưa có dòng giá (S4: 158, S1: 8), tất cả "Chưa tính được"; 99 nhóm tiêu hao được các mã này dùng, 96 nhóm "đang khoá" (BR-24) chỉ vì các mã này | dữ liệu app |

## 3. Câu hỏi (vòng 1)
1. Mã có mã kế toán chờ (chưa có giá): (a) cho sửa NSM, tỷ lệ pha, nguyên liệu, đóng gói như mã chưa khoá; mã kế toán vẫn chờ
   và tự gắn vào dòng Thường khi tính được giá (đề xuất); (b) giữ khoá như hiện nay, chỉ cho tạo bản ĐCNSM.
2. Ai được sửa các mã này: (a) như mã bình thường: xưởng của mã và Phòng SO (đề xuất); (b) chỉ Phòng SO.
3. Nhóm tiêu hao chỉ "đang khoá" vì các mã có mã kế toán chờ (96 nhóm): (a) không coi là khoá nữa, xưởng tự sửa được (đề xuất);
   (b) vẫn khoá, chỉ Phòng SO sửa.
4. Nút "Tạo bản ĐCNSM": (a) hiện cho mọi mã đã khoá hoặc đã có giá, kể cả mã chưa có giá nhưng có mã kế toán chờ (đề xuất, đúng
   UC-24); (b) chỉ hiện khi mã đã có giá.
5. Mã kế toán chờ: (a) hiện trên khối thông tin mã ở màn Nhập NSM ("Mã kế toán chờ: …"), không sửa được trên màn hình (đề xuất);
   (b) hiện và cho Kế toán / Phòng SO sửa hoặc xoá; (c) không hiện.

## 4. Trả lời
1. a - mã có mã kế toán chờ sửa được như mã chưa khoá; mã chờ gán vào dòng Thường khi tính được giá lần đầu.
2. a - xưởng của mã và Phòng SO.
3. a - mã kế toán chờ không làm nhóm tiêu hao "đang khoá".
4. b - nút "Tạo bản ĐCNSM" chỉ hiện khi mã đã có dòng giá.
5. a - hiện "Mã kế toán chờ: <mã>" trên màn Nhập NSM, chỉ xem.

## 5. Bảng đối chiếu nguồn
| S-xx | Nội dung | Được ghi ở |
|---|---|---|
| S-01 | Mã chưa có giá bị khoá vì mã kế toán chờ | BR-70, BR-32, mục 4.12 (`is_locked`, `pending_accounting_code`), UC-21, UC-23, AC-86, AC-87 |
| S-02 | Nút "Tạo bản ĐCNSM" | BR-70, UC-24, Screen 3, AC-89 |
| S-03 | Mã kế toán chờ gán vào dòng Thường | BR-70, UC-21 bước 4, bảng trạng thái 4.12, mục 3 (Thuật ngữ), mục 10 |
| S-04 | BR-32 / UC-23 / UC-24 | BR-32, UC-23, UC-24 |
| S-05 | 96 nhóm tiêu hao "đang khoá" vì mã chờ | BR-24, BR-70, AC-88 |


---

# Kế hoạch phân tích nghiệp vụ: Năng suất xưởng may

| Ngày | 2026-11-05 |
|---|---|
| Nguồn chính | [docs/business/_sources/nang-suat-xuong-may-discovery.md](../business/_sources/nang-suat-xuong-may-discovery.md) |
| Trạng thái | Người dùng đã xác nhận tài liệu ngày 2026-11-05 |

Người dùng đã xác nhận ghi chép tìm hiểu ngày 2026-11-05, kèm theo 3 điểm về đổi mã hàng ở S-16 và S-17. Bước này chỉ được sửa tài liệu nghiệp vụ và kế hoạch này, nên ghi chép gốc giữ nguyên và việc xác nhận được ghi tại đây.

## 1. Chia chức năng

**Một chức năng duy nhất**, vì mọi màn hình dùng chung một bộ dữ liệu.

| Mục | Nội dung |
|---|---|
| Feature key | `sewing_productivity` |
| Tên hiển thị | Năng suất xưởng may |
| Nhóm Trang chủ | Sản xuất |
| Biểu tượng | 🧵 |
| Người phụ trách | Nhóm PI - SO |
| Mục tiêu | Theo dõi và phân tích năng suất các xưởng may theo khoảng thời gian bất kỳ, thay cho báo cáo Excel làm tay |
| Người dùng | Người cập nhật dữ liệu (tải file, sửa mục tiêu, danh mục, nhập đổi mã hàng tuần); Người xem (xem, lọc, tải báo cáo) |

**Phạm vi tài liệu này là đợt 1.** Đợt 2 (phân tích khách hàng) và đợt 3 (dữ liệu 2025) làm sau bằng `docs/prompt/05-extend-feature.md`, đúng thứ tự người dùng đã đồng ý.

### Nghiệp vụ dự kiến

| Nhóm | Nghiệp vụ |
|---|---|
| Dữ liệu | Kiểm tra file tải lên; lưu dữ liệu từ file; xem lịch sử tải file |
| Thiết lập | Xem và sửa mục tiêu, ngưỡng theo ngày hiệu lực; nhập đổi mã hàng theo tuần |
| Danh mục | Xem và sửa nhóm sản phẩm, nhóm khách hàng, bảng số chuyền Fac 1; bổ sung tên sản phẩm cho style chưa tra được |
| Báo cáo | Tổng quan xưởng; chi tiết chuyền; báo cáo ngày; báo cáo tháng; MO 8h theo chuyền; đổi mã hàng; biểu đồ |
| Xuất file | Tải Excel cho từng báo cáo |

### Màn hình dự kiến

1. Tổng quan 4 xưởng (trang đầu) và biểu đồ
2. Chi tiết theo chuyền
3. Báo cáo ngày
4. Báo cáo tháng
5. MO 8h theo chuyền
6. Đổi mã hàng
7. Cập nhật dữ liệu
8. Mục tiêu và ngưỡng
9. Danh mục

## 2. Bảng nguồn

| ID | Nội dung | Nguồn |
|---|---|---|
| S-01 | Dữ liệu đầu vào là file Excel, mỗi ngày thêm khoảng 150 dòng; ngày cũ có thể bị sửa | Tin nhắn, `Data sewing 2026.xlsx` |
| S-02 | Không tự đọc SharePoint hay máy cá nhân; người phụ trách tải file lên | Ghi chép mục 8 |
| S-03 | Sheet `Production data`, `Target system`, `Worker` là dữ liệu đầu vào | `Data sewing 2026.xlsx` |
| S-04 | Hiệu suất cách A cho báo cáo tuần, từ `Target system`, để trống trước 03/10/2026 | Tin nhắn, ghi chép mục 5 |
| S-05 | Hiệu suất cách B cho KPI, lấy thẳng số trong file | Tin nhắn, ghi chép mục 5 |
| S-06 | Mục tiêu theo xưởng do người phụ trách sửa, có ngày hiệu lực | Tin nhắn |
| S-07 | Ngưỡng HCM 90% và MO $40; Vĩnh Long 85% và MO $30; áp cho cả hai hiệu suất | Tin nhắn |
| S-08 | Công thức MO 8h của chuyền và của xưởng | Báo cáo tuần `Fac 1-detailed` |
| S-09 | Tỷ lệ đúng sở trường tính từ `Target system` | Báo cáo tuần `Overall`, `Target system` |
| S-10 | Báo cáo tuần: tổng quan và chi tiết chuyền theo ngày | `Sewing - Weekly Fac report` |
| S-11 | Báo cáo ngày, bỏ Cutting | `Daily Report Sewing`, tin nhắn |
| S-12 | Báo cáo tháng | `Report final` |
| S-13 | MO 8h theo chuyền | `MO` |
| S-14 | Biểu đồ: hiệu suất và MO theo ngày, thực tế so với mục tiêu, xếp hạng chuyền | Tin nhắn |
| S-15 | Đổi mã hàng theo tuần do xưởng cung cấp, người phụ trách nhập tay | Tin nhắn |
| S-16 | Số lần đổi KPI: bỏ phần sau dấu chấm cuối, lấy ngày đầu tiên trên chuyền, mỗi cặp SMV + CM chỉ tính một lần trong khoảng; KPI = số lần / số ngày làm việc / số chuyền của xưởng | Tin nhắn, `Data sewing 2026 - KPI CHANGEOVER.xlsx` |
| S-17 | Số riêng "gồm cả lên lại", theo cặp SMV + CM; ví dụ ngày 1 lên, ngày 4 lên lại là tổng 2 lần; không thay số KPI | Tin nhắn |
| S-18 | Bộ lọc thời gian, xưởng, chuyền, khách hàng, sản phẩm | Tin nhắn |
| S-19 | Tên chuyền không phân biệt hoa thường; số chuyền Fac 1 trước 07/07/2026 quy về tên hiện nay | Tin nhắn, `Daily Report Sewing` |
| S-20 | 7 nhóm sản phẩm; tên trống tra theo mã đơn, style, `Target system`; file gốc giữ nguyên | Tin nhắn, báo cáo tuần |
| S-21 | Gộp khách hàng ELAND, MIHUB; màn hình danh mục do người phụ trách sửa | Tin nhắn |
| S-22 | Mọi người đăng nhập để xem, chỉ người phụ trách sửa | Tin nhắn |
| S-23 | Excel tải về: mỗi báo cáo một sheet, cột Đánh giá, không tô màu | Tin nhắn |
| S-24 | Dấu màu cạnh con số theo ngưỡng | Tin nhắn |
| S-25 | Đợt 2 và đợt 3 làm sau | Tin nhắn |

## 3. Kết quả kiểm tra thêm trên dữ liệu

- **Ngày làm việc:** số ngày có sản lượng khớp file KPI ở các tháng, trừ Fac 1 tháng 8 (25 so với 24).
- **Số chuyền:** số chuyền có sản lượng là 14, 19, 15 cho Fac 2, 3, 5; Fac 1 từ 29 đến 33. Tháng 1, 2, 3, 4, 8, 9, 10 của Fac 1 đã khớp file KPI.
- **Giờ làm của xưởng:** `Working Hours` lấy trung bình giờ của từng chuyền trong ngày.
- **Mục tiêu báo cáo ngày:** Daily Target (SMV) của Fac 2 ngày 03/11 là 9.863, báo cáo lại ghi `=9863-869+702`. Target MO dùng số gõ tay như `=(16700/C16)*8/9.12`.
- **Dòng trùng:** 51 dòng trùng ngày, xưởng, chuyền, mã đơn, màu; đa số khác sản lượng, chỉ 2 dòng giống hệt.
- **Ngày mới nhất chưa đủ số:** ngày 04/11 có 45 dòng thiếu SMV, chưa có `Worker` và `Target system`.
- **Cột bắt buộc:** không có dòng nào thiếu ngày, xưởng, chuyền, mã đơn, sản lượng, giá, số người, giờ làm.

## 4. Câu hỏi vòng 1

1. Xử lý file tải lên và dòng lỗi.
2. Xử lý ngày mới nhất chưa đủ số.
3. Khoảng thời gian trải qua 03/10/2026 với hiệu suất cách A.
4. Bộ lọc khách hàng và sản phẩm ảnh hưởng đến chỉ số nào.
5. Cách chọn tuần và cách nhập đổi mã hàng theo tuần.
6. Mục tiêu và ngưỡng: áp cho hiệu suất nào, sửa thế nào.
7. Nguồn mục tiêu trong báo cáo ngày.
8. Tách chuyền cũ và mới của Fac 1, cột trái sở trường.
9. Chỉ số của từng biểu đồ và xếp hạng chuyền.
10. Danh mục ban đầu cho sản phẩm và khách hàng.
11. Cách đếm số ngày làm việc và số chuyền.

Người dùng trả lời "ok hết" ngày 2026-11-05: đồng ý toàn bộ đề xuất của 11 câu. Các câu trả lời đã nằm trong [tài liệu nghiệp vụ](../business/sewing_productivity.md).

## 5. Bảng đối chiếu nguồn

| S-xx | Nội dung | Covered by |
|---|---|---|
| S-01 | File Excel, ngày cũ có thể bị sửa | Mục 5.1, UC-02, BR-07, AC-08 |
| S-02 | Tải file lên thay cho đọc SharePoint | Mục 10, UC-01, UC-02, Screen 7 |
| S-03 | 3 sheet đầu vào | Mục 4.1–4.3, mục 5.1, BR-02, BR-03 |
| S-04 | Hiệu suất A | BR-18, UC-04, AC-20, AC-23 |
| S-05 | Hiệu suất B | Mục 4.1, BR-19, UC-04, AC-21 |
| S-06 | Mục tiêu có ngày hiệu lực | Mục 4.4, BR-26, BR-27, BR-45, BR-46, UC-16, UC-17, AC-27 |
| S-07 | Ngưỡng cảnh báo | Mục 4.4, BR-28, AC-29, AC-30 |
| S-08 | Công thức MO 8h | BR-20 đến BR-23, BR-48, AC-25, AC-26 |
| S-09 | Tỷ lệ đúng sở trường | BR-25, AC-22 |
| S-10 | Báo cáo tuần | UC-04, UC-06, UC-11, Screen 1, Screen 2 |
| S-11 | Báo cáo ngày, bỏ Cutting | UC-07, UC-12, BR-42, BR-43, Screen 3 |
| S-12 | Báo cáo tháng | UC-08, UC-13, BR-48, Screen 4 |
| S-13 | MO theo chuyền | UC-09, UC-14, BR-48, Screen 5 |
| S-14 | Biểu đồ | UC-05, BR-44, Screen 1, AC-41 |
| S-15 | Đổi mã hàng tuần nhập tay | Mục 4.5, UC-18, UC-19, UC-20, BR-38 đến BR-41, AC-31, AC-32, AC-47 |
| S-16 | KPI đổi mã hàng | BR-12, BR-32 đến BR-35, BR-37, UC-10, UC-15, AC-33 |
| S-17 | Số gồm cả lên lại | BR-36, UC-10, AC-34, AC-35, AC-36 |
| S-18 | Bộ lọc | BR-29, BR-30, BR-31, UC-26, mục 8, AC-24 |
| S-19 | Chuẩn hoá và quy đổi số chuyền | Mục 4.8, BR-10, BR-11, UC-24, AC-14, AC-15, AC-49 |
| S-20 | Nhóm sản phẩm, tra tên trống | Mục 4.6, mục 4.9, BR-13, BR-14, UC-22, UC-25, AC-16, AC-17, AC-18 |
| S-21 | Nhóm khách hàng, màn hình danh mục | Mục 4.7, BR-15, UC-21, UC-23, Screen 9, AC-19 |
| S-22 | Quyền xem và sửa | Mục 2, BR-09, mục 8, AC-12 |
| S-23 | Excel tải về | Mục 5.2, BR-49, UC-11 đến UC-15, AC-43, AC-44 |
| S-24 | Dấu màu theo ngưỡng | BR-28, mục 8, AC-29 |
| S-25 | Đợt 2 và đợt 3 làm sau | Mục 10 |

## 6. Tự rà soát

- Mọi BR đều nằm trong ít nhất một UC; mọi UC đều nằm trên một màn hình; mọi nút đều dẫn tới một UC.
- Mọi cột của file đều có trường dữ liệu tương ứng; mọi trường đều được dùng trong UC, màn hình hoặc file.
- Mọi UC đều có AC, kể cả luồng lỗi.
- Số trong AC-20 đến AC-22, AC-25, AC-26, AC-33 và AC-34 đã được tính thử từ các file mẫu.
