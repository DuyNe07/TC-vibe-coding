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
