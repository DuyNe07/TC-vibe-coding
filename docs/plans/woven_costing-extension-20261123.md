# Extension 2026-11-23 - woven_costing: tự đổi chi số, độ săn và chi số gõ tự do

## Thêm / thay đổi
- Sales gõ chi số bất kỳ (dòng Se, chi số cone 1, 2). App tự đổi ra "chi số chuyển đổi" theo quy luật của sheet "Dữ
  liệu" file Excel (BR-81).
  - Chi số có trong danh sách 4.5.6 thì dùng số của danh sách; không có thì dùng công thức.
- Bảng "Spandex cộng thêm" là sheet mới `Spandex` trong file bộ định mức, có ngày hiệu lực cùng bộ định mức.
  - Ban đầu: SP 40 = 16, SP 70 = 22.
  - SP chưa có trong bảng thì báo lỗi (BR-84).
- Độ săn gõ số nguyên 50-3.000 T/M (BR-82). Danh sách cũ giữ làm gợi ý.
- Hệ sợi tự xác định từ chi số: có chữ "D" là Filament, không có là Spun (BR-83).
  - Sửa 4.13 fiber_system và BR-20: không còn lỗi "chi số không khớp hệ sợi", vì không còn nhập hệ sợi.
- Hiện cột "Chi số chuyển đổi" trong bảng dòng Se và cạnh ô chi số cone.

## Ảnh hưởng tới phần đã có
- UC-16, UC-17, UC-20 dùng BR-81..BR-84 khi tính.
- UC-06, UC-07, UC-08, UC-37: file bộ định mức thêm sheet thứ 13 `Spandex`.
  - File 12 sheet cũ vẫn nhận; khi đó bảng spandex lấy từ bộ đang hiệu lực.
- BR-20: bỏ phần kiểm tra chi số / hệ sợi (thay bằng BR-83); phần tính định mức giữ nguyên.
- BR-22 (Cone): số chuyển đổi lấy theo BR-81.
- BR-63: kiểm tra thêm sheet `Spandex`.
- Screen 2 (thẻ Ngành Dệt), Screen 5 (xem bảng Spandex).
- AC-09 (4 file thật) phải giữ nguyên kết quả.

## Dữ liệu đã lưu
- Costsheet đã lưu giữ nguyên kết quả (BR-39).
- Dòng Se đã lưu có fiber_system: giữ để đọc. Khi tính lại, hệ sợi lấy theo BR-83, cho cùng kết quả vì dữ liệu cũ đều
  hợp lệ.
- Bộ định mức đã lưu chưa có bảng spandex: mặc định SP 40 = 16, SP 70 = 22 (trường mới có giá trị mặc định, không cần
  chuyển đổi dữ liệu).
- Công thức khớp 56/56 chi số đang có, nên phiếu Nháp tính lại không đổi kết quả.

## Câu hỏi đã trả lời (2026-11-23, "theo đề xuất")
1. Độ săn: số nguyên 50-3.000 T/M; danh sách cũ làm gợi ý.
2. Hệ sợi tự xác định từ chi số.
3. Spandex: sheet `Spandex` trong file bộ định mức.
4. Chi số có trong danh sách: dùng số của danh sách.
5. Hiện cột "Chi số chuyển đổi"; chi số sai dạng thì báo lỗi.
6. Phiếu đã lưu không đổi.

## Traceability (mới / đổi)
| Spec item | Code element | Test | Status |
|---|---|---|---|
| 4.5.13 Spandex, F-05 sheet 13 | models/norm_set.py, builders/norm_file_builders.py | test_master_services | ✅ |
| 4.13 (sửa) | models/costsheet.py, dto | test_costsheet_flow | ✅ |
| BR-81..BR-84, BR-20 / BR-22 / BR-63 (sửa) | business/count_business.py (mới), twist/weaving/norm | test_rules, test_calculation | ✅ |
| Screen 2, Screen 5 | components/costsheet_weaving.py, pages/norm_parameter_page.py | test_pages_render | ✅ |
| AC-44..AC-51 | | tests | ✅ |
| regression: existing tests (AC-09 …) | | toàn bộ test cũ | ✅ |

## Bổ sung (2026-11-23): Phòng SO toàn quyền trên costsheet
- Người có vai trò SO được lập costsheet (thường để thử), sửa mọi phiếu, duyệt mọi phiếu và tự duyệt phiếu của mình
  (BR-31, BR-51, BR-52, BR-53 sửa; BR-85 mới).
- Phiếu do người chỉ có vai trò SO lập thuộc team "SO". Sales FS1 / FS2 và trưởng team không thấy; trưởng đơn vị và SO
  thấy.
- Ảnh hưởng: danh sách giá trị team thêm "SO" (4.11), không đổi dữ liệu đã lưu; nút trên Screen 2 hiện cho SO theo
  BR-85; bộ lọc Team có thêm giá trị "SO".
- AC mới: AC-52..AC-55 (có hồi quy quyền sales / trưởng team).
- Câu trả lời của người dùng: (1) SO lập phiếu chủ yếu để thử tính năng; (2) SO tự duyệt; (3) SO toàn quyền.

## Bổ sung (2026-11-23): Hiện rõ hệ số số lượng
- Hiện trạng: hệ số đã tính đúng (BR-23), nhưng chỉ hiện ở 1 ô cuối thẻ Ngành Dệt. Bảng công đoạn không cho biết dòng
  nào nhân hệ số; cột "Thành tiền" là trước hệ số. Phiếu thử CS-ICHI-2026-00001: 12.720 m mộc -> hệ số 1.
- Thay đổi (chỉ hiển thị, không đổi cách tính):
  - ô "Hệ số số lượng" kèm lý do ở đầu thẻ;
  - cột "Nhân hệ số SL" và "Thành tiền sau hệ số (đ)" trong bảng công đoạn.
- AC mới: AC-56.

## Vòng giao diện (2026-11-23)
1. Chi số, độ săn: gõ tự do; app gợi ý sẵn trong ô (dòng Se tạo sẵn từ sợi tick Se - BR-86), sales sửa lại.
2. Không hiện chi số chuyển đổi (giống Excel). Hệ sợi gợi ý sẵn, sales chọn lại được (BR-83 sửa).
3. Hệ số số lượng ở đầu thẻ Ngành Dệt.
4. Spandex trong danh sách "Bảng" của bộ định mức.
5. Bộ lọc Team thêm "SO".
- AC thêm: AC-57 (gợi ý dòng Se). AC-45 sửa (không hiển thị chi số chuyển đổi; đổi hệ sợi).

## Traceability bổ sung
| Spec item | Code element | Test | Status |
|---|---|---|---|
| BR-31, BR-51..BR-53 (sửa), BR-85 | business/access_business.py, costsheet_business.py (allowed actions) | test_costsheet_flow | ✅ |
| BR-86 | business/hint_business.py hoặc count_business.py | test_rules | ✅ |
| Hiển thị hệ số SL (AC-56) | dto StageCostDTO (+ applies_quantity_factor, amount_after_factor), quantity_factor_reason; costsheet_weaving.py | test_calculation, render | ✅ |
| AC-52..AC-57 | | tests | ✅ |

## Ghi nhận cho lần mở rộng sau (người dùng nói 2026-11-23, chưa làm)
- Sales gia công có 2 loại:
  - Nhận gia công dệt: chỉ tính chi phí dệt, bỏ chi phí sợi và nhuộm.
  - Gia công nhuộm: bỏ chi phí dệt và sợi; thường trình nhiều đơn hàng một lần (nhiều mã hàng, mỗi mã 1 OC) -> đợt 3
    (NGC).
- Đây là thay đổi cách tính (quy tắc), nên làm bằng Prompt 05, không thuộc lần đổi giao diện Màn hình 2.

## Sửa 5 điểm (2026-11-23, Prompt 05)
1. Screen 5: bảng định mức chia 4 thẻ con (Dệt / Nhuộm HCM / Nhuộm TCDN / Danh mục), bỏ ô chọn "Bảng". AC-58.
2. Lỗi: danh sách công đoạn ngoài quy trình TCDN gộp cả tên sheet "Tên Công Đoạn" không có định mức (Suse 1, Ageing room,
   Kuster, Dyeing, Dry...). Sửa: chỉ 28 công đoạn (CPB 4 dòng tính là 1) có dòng trong 4.5.10 như Excel (trùng các cột tick file NGC). AC-59.
3. BR-87 mới: cone 1 điền sẵn SL = tổng Se ngang và chi số khi Se ngang 1 chi số; hiện trong ô; giữ số sales sửa.
   AC-60.
4. UC-16: tự tính mỗi khi đổi ô, bỏ nút "Tính lại", hiện "Có thay đổi chưa lưu". AC-61.
5. BR-86 sửa: dòng Se gợi ý tự cập nhật theo tick Se / sản lượng; dòng sales sửa giữ nguyên; dòng cũ coi như đã sửa.
   AC-62.
- Dữ liệu cũ: không đổi; trường mới (đánh dấu dòng Se gợi ý / đã sửa, cone gợi ý / đã sửa) có giá trị mặc định = "sales
  đã sửa" cho dòng cũ.
- Giao diện: người dùng đã chọn trong hội thoại (chia thẻ định mức, tự tính kiểu Excel, điền sẵn trong ô) -> bỏ qua
  vòng hỏi giao diện riêng.
- Hồi quy: toàn bộ test cũ, AC-09.

## Mở rộng 2026-11-25: tham số theo ngành, bảng discount, bảng % B/C, giá thanh lý = 0 (Prompt 05)
- Người dùng: discount theo sản lượng là "Thống nhất giảm giá / phụ phí theo sản lượng đơn hàng" -> theo bậc, không
  chia đều (ảnh gửi 2026-11-25); thí nghiệm x2; các câu khác "theo đề xuất".
- Thêm 4.6.1 bảng discount (ngành, điều kiện, mốc ≥/>/≤/<, hệ số, interpolate cho bộ cũ), 4.6.2 bảng % B/C theo hình
  thức bán, BR-88 kiểm tra bảng.
- Sửa BR-16, BR-23, BR-25, BR-26 (lấy từ bảng), BR-46 (sales sửa hệ số đang áp dụng).
- Sửa Màn hình 5 (5 thẻ con theo ngành) và Khối G (nhóm theo ngành).
- Dữ liệu cũ: bộ tham số cũ đọc thành bảng với đúng số cũ (Dệt interpolate = Yes); tạo sẵn bộ hiệu lực 25/11/2026 (bảng
  bậc, 2 giá thanh lý = 0). Phiếu trước 25/11/2026 giữ số; AC-09 giữ.
- AC mới: AC-63..AC-69.
- Ảnh hưởng hồi quy: AC-09, AC-10 (7.500 m -> 1,025 vẫn đúng với bộ cũ), AC-56.
- Giao diện: đã chốt trong hội thoại (chia 5 thẻ con theo ngành, bảng sửa trong ô) -> bỏ vòng hỏi giao diện riêng.
