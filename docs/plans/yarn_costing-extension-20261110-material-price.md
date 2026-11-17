# yarn_costing - mở rộng 2026-11-10 (đợt 2): giá nguyên liệu bình quân và giá báo khách

Nguồn: `docs/business/_sources/yarn_costing-material-price-discovery.md`; file mẫu trong
`D:\Vibe Coding\Spinning\New data`: `GIÁ SỢI 4 THÁNG 10.xlsx` (nhập - xuất - tồn kho S4 tháng 10/2026),
`Giá nguyên liệu.xlsx` (cách Sales tính giá bình quân tháng 11), `Ke hoach xo ve NM - 06.11.xlsx` (theo dõi xơ sắp về).

## 1. Thêm / đổi gì
| # | Nội dung | Mục / UC / BR / AC |
|---|---|---|
| 1 | Nhóm giá nguyên liệu: Cotton theo xuất xứ (USA / Brazil / Australia), xơ theo nhà cung cấp; nhóm cố định "Cotton (phương án)" | 4.22, UC-55, BR-85 |
| 2 | Tải file kho S4 hằng tháng (tồn, nhập, xuất của nguyên liệu, sợi thành phẩm, phụ liệu); tải lại cùng tháng thì thay | 4.24, 5.10, UC-56, BR-86, BR-87, AC-118, AC-119 |
| 3 | Khai báo mã kho nguyên liệu: nhóm giá hoặc "Không tính", Nội địa / Xuất khẩu / Chung (gợi ý theo đuôi mã); mã mới hiện ra để khai báo thêm | 4.23, UC-57, BR-86, BR-87 |
| 4 | Khai báo tháng: hồi phế USD/kg theo nhóm (trừ), phương án pha bông, hệ số norm mặc định 110%, F&I mặc định 0,03; tháng mới tự chép từ tháng trước | 4.25, UC-58, BR-88, AC-122, AC-123 |
| 5 | Tỷ giá theo tháng (dùng cho phần đợt 2): tỷ giá của tháng M = mốc mới nhất đến cuối tháng M | 4.9 (sửa), BR-89 |
| 6 | Bảng giá nguyên liệu bình quân tháng (tồn cuối tháng trước + hàng về trong tháng, trừ hồi phế; cotton theo phương án) | UC-59, BR-92, AC-120, AC-121 |
| 7 | Màn "Nguyên liệu sắp về": nhập file theo mẫu sheet "Update Fiber arrival" (+ cột Giá nhập kho), sửa tay, ghép nhà cung cấp + mô tả → nhóm giá | 4.26, 4.27, 5.11, UC-60, UC-61, BR-90, BR-91, AC-124, AC-125 |
| 8 | Màn "Tính giá báo khách": chọn dòng giá, Thường / Thí nghiệm, Nội địa / Xuất khẩu, mã kế toán (gợi ý / dán), khách, SL đơn, nhóm giá từng thành phần (gợi ý), hệ số, GP %, Commission %, FOB / CIF, F&I → giá NL, giá vốn mới, bình quân với sợi tồn, FOB, CIF; lưu, danh sách, xuất Excel | 4.28, 5.12, UC-62, UC-63, BR-93..BR-98, AC-126..AC-129 |
| 9 | So đơn giá xuất kho với giá bình quân: nguyên liệu (với giá BQ nhóm) và sợi thành phẩm (với giá vốn lần tính báo khách gần nhất) | UC-64, BR-99, AC-131 |
| 10 | Quyền: mọi phần đợt 2 (cả xem) chỉ Sales, Phòng SO, quản trị viên | BR-84, BR-47 (sửa), AC-130 |

## 2. Ảnh hưởng tới cái đang có
- Không đổi cách tính chi phí gia công, trạng thái, khoá, lịch sử giá, file nhập / xuất hiện có, màn So sánh 2 sợi, Đối chiếu
  giá kế toán (AC-132).
- Tỷ giá (4.9, UC-08, BR-22) giữ nguyên: giá USD trên bảng giá vẫn dùng tỷ giá đang dùng. Phần đợt 2 dùng tỷ giá của tháng tính
  (BR-89); Phòng SO khai báo tỷ giá tháng bằng ngày áp dụng = ngày 1 của tháng.
- "Hồi phế" cũ (4.7, tỷ lệ chạy lại trong chi phí chế biến) không đổi; phần mới gọi là **"Hồi phế nguyên liệu (USD/kg)"**.
- Menu nhóm **Sales** thêm 3 màn (Giá nguyên liệu, Nguyên liệu sắp về, Tính giá báo khách); quản trị viên tích quyền màn hình
  ở `/admin` cho Sales / Phòng SO.

## 3. Dữ liệu đã lưu
- Mọi bảng mới (4.22-4.28) ban đầu trống; không thêm trường vào bảng cũ, không cần chuyển đổi dữ liệu cũ.
- Tải lại tháng kho / nhập lại file hàng sắp về: bản cũ đặt cờ xoá (`is_deleted`), không xoá thật. Xoá nhóm giá, lô, lần tính
  báo giá = cờ xoá.

## 4. Câu hỏi đã trả lời (2026-11-10)
- Hồi phế trừ khỏi giá BQ, theo nhóm, hằng tháng; nội địa / xuất khẩu chọn mỗi lần tính; nhóm giá từng thành phần Sales chọn,
  app gợi ý (3a); hệ số mặc định 110%, Sales đổi được; SL bình quân với sợi tồn = SL đơn hàng Sales nhập; màn hàng sắp về (nhập
  tay + Excel); chỉ kho S4; khai báo mã kho do Sales làm, mã mới hiện ra; tỷ giá theo app.
- Thêm: Thường / Thí nghiệm (= norm dòng Thường / Thí nghiệm); FOB / CIF; F&I mặc định 0,03 USD/kg sửa được; Commission % trên
  giá bán; GP % trên giá bán; FOB = giá vốn ÷ (1 − GP − Commission), CIF = FOB + F&I.
- Tỷ giá theo tháng; sợi tồn ghép 18 ký tự đầu; có lưu lần tính.
- Vòng 1: chỉ Sales + Phòng SO xem (1a); tháng tính M dùng file kho tháng M−1, hàng về kho S4 trong M, tỷ giá M (2); hàng sắp
  về đọc thẳng file theo dõi + cột Giá nhập kho, trống = giá mua (4b); nội dung lưu như đề xuất (5); so nguyên liệu và sợi thành
  phẩm, bỏ phụ liệu (6); tiêu hao theo từng thành phần (7).
- Vòng 2: so sợi thành phẩm với lần tính gần nhất cùng mã kế toán, Sales chọn mã kế toán khi tính (gợi ý theo tên / dán tay)
  (1a); một mẫu file theo sheet "Update Fiber arrival", cotton cũng ghi vào đó (2); lô chỉ ghi "MILL 4" dùng chung cho nội địa
  và xuất khẩu (3a); ghép NCC + mô tả → nhóm, cặp mới hiện ra (4); nhập lại lấy theo file (5a); giá nhập kho đã gồm logistic,
  không khai báo logistic (6b); đơn giá > 100 hiểu là VND (7); khai báo tháng tự chép từ tháng trước.

## 5. Giả định (chờ xác nhận cùng tài liệu)
- Đổi giá trị kho (VND) và giá VND của hàng về sang USD bằng tỷ giá của tháng tính M (BR-89).
- Tiêu hao sản xuất của một thành phần = tiêu hao lũy kế (BR-19) của lượt chải thô của thành phần; thành phần không chải thô =
  tiêu hao lũy kế lớn nhất trong các công đoạn của sợi (BR-94).
- Sợi tồn: cộng mọi dòng "Do cty sx" cùng 18 ký tự đầu (cả đuôi D và E) của file kho tháng M−1 (BR-95).
- So giá xuất nguyên liệu tháng M với giá BQ tháng M (cần file kho tháng M−1); tháng đầu tiên chưa có thì ghi "chưa có giá BQ".
- Lần tính báo giá đã lưu không đổi khi dữ liệu nền đổi; muốn số mới thì tính lần mới.

## 6. Truy vết khi làm (Prompt 5 Step 6)
| Mục | Mã | Kiểm thử |
|---|---|---|
| BR-84 (kể cả xem) | `business/access_business.py::ensure_material_access`, `models/access.py` | AC-130 |
| BR-85, UC-55 | `business/material_price_business.py::ensure_group_valid`, `services/save_price_group_service.py` | AC-123 |
| BR-86, BR-87, UC-56, 5.10 | `business/material_stock_business.py`, `builders/material_file_builders.py::StockFileReaderBuilder`, `services/import_stock_file_service.py` | AC-118, AC-119 |
| UC-57 | `services/save_stock_item_settings_service.py`, `services/get_material_setup_service.py` | AC-123 |
| BR-88, UC-58 | `MaterialPriceBusiness.draft / setting_of / ensure_setting_valid`, `services/get_monthly_setting_service.py`, `services/save_monthly_setting_service.py` | AC-122, AC-123 |
| BR-89 | `MaterialPriceBusiness.rate_of_month` | AC-128, AC-132 |
| BR-92, UC-59 | `MaterialPriceBusiness.averages / month_view`, `services/get_material_averages_service.py` | AC-120, AC-121, AC-125 |
| BR-90, BR-91, UC-60, UC-61, 5.11 | `MaterialStockBusiness.check_lot / read_arrival_rows / new_mappings`, `ArrivalFileReaderBuilder`, services import / list / save lots / save mappings | AC-124, AC-125 |
| BR-93..BR-98, UC-62 | `business/quote_business.py`, `services/get_quote_form_service.py`, `services/calculate_quote_service.py` | AC-126, AC-127, AC-128 |
| BR-97, UC-63, 5.12 | `services/list_quotes_service.py`, `export_quotes_service.py`, `delete_quote_service.py`, `QuoteExportFileBuilder` | AC-129 |
| BR-99, UC-64 | `MaterialPriceBusiness.compare_stock_out`, `services/get_stock_out_comparison_service.py` | AC-131 |
| Screen 11-13 | `pages/material_price_page.py`, `pages/arrival_page.py`, `pages/quote_page.py`, `components/material_ui.py`, `manifest.py` | chạy thử không trình duyệt với 3 file thật |
| regression: existing tests | toàn bộ kiểm thử cũ giữ xanh | `scripts/check.py` → ALL CHECKS PASSED, AC-132 |
