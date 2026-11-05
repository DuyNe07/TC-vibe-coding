# yarn_costing - Mở rộng 2026-11-05 (lần 2): trạng thái "Không sản xuất" (Prompt 5)

## Yêu cầu của người dùng
Các mã không có giá trong file Excel định mức cũ là mã không sản xuất được (ví dụ S4-1731; danh sách
`bao-cao/ma-khong-co-gia-excel-S1-S4-20261105.xlsx`: S4 187 mã, S1 82 mã, trong đó 18 mã app vẫn đang ra giá). Cần đánh dấu
các mã đó để không bị hiểu là đang chờ tính giá, không còn giá trên bảng giá, không làm sai số liệu kiểm soát.

## Câu hỏi đã trả lời
| # | Câu hỏi | Trả lời |
|---|---|---|
| V1-1 | Hình thức | Trạng thái mới "Không sản xuất" |
| V1-2 | Ai làm | Phòng SO và xưởng của mã (BR-48) |
| V1-3 | Cách đánh dấu | Từng mã (nút) + hàng loạt bằng file Excel danh sách mã |
| V1-4 | Mã Không sản xuất thì | Không có trên bảng giá / file xuất; không vào Dashboard và các kiểm tra bất thường; không tính lại, không nhập NSM; không chặn yêu cầu mới cùng tên |
| V1-5 | Bỏ đánh dấu | Được; app tính lại ngay |
| V1-6 | Mã có mã kế toán | Không cho đánh dấu khi còn mã kế toán (xoá mã kế toán trước) |
| V1-7 | Lý do | Bắt buộc |
| V2-1 | Nút từng mã | Màn Nhập NSM & tính giá, cạnh nút Từ chối |
| V2-2 | File hàng loạt | Màn Nhập dữ liệu từ Excel, loại tải mới "Đánh dấu không sản xuất", 2 cột Mã + Lý do, kiểm tra thử rồi lưu; xưởng chỉ mã của xưởng mình |
| V2-3 | Bản ĐCNSM | Đánh dấu / bỏ đánh dấu mã gốc áp cho mọi bản ĐCNSM của nó |
| V2-4 | Yêu cầu "Chờ xưởng xem" | Không cho, dùng Từ chối |
| V2-5 | Mã kế toán chờ (BR-70) | Cho đánh dấu; mã chờ giữ lại, chỉ gán khi bỏ đánh dấu và tính được giá |
| V2-6 | Giá của mã đã có giá | **Xoá giá**: các dòng giá (Thường, Thí nghiệm, CK/PP) bị gỡ khỏi bảng giá; số cũ còn trong Lịch sử giá và Nhật ký thao tác (quy tắc không mất dữ liệu) |

Ghi chú S4-464: có 2 dòng trong sheet `4. Bang gia da tinh` (dòng 561 không giá, dòng 1871 có giá 17.511,71); mã kế toán
S41602000010000550FC đúng theo Excel; đã bỏ khỏi danh sách không có giá.

## Thêm / đổi
- Mới: trạng thái "Không sản xuất" (4.12), trường `not_produced_reason`, `not_produced_by`, `not_produced_at` (4.12), file 5.8,
  UC-47 (đánh dấu / bỏ đánh dấu từng mã), UC-48 (đánh dấu hàng loạt bằng file), BR-72..BR-75, AC-95..AC-102, thuật ngữ.
- Sửa (ghi rõ trong tài liệu): BR-06, BR-24, BR-36, BR-40, BR-47, BR-53, BR-62, BR-65 và UC-21, UC-23, UC-24, UC-25, UC-28,
  UC-45 không xét / từ chối mã "Không sản xuất"; Screen 3 (nút, bộ lọc), Screen 6 (loại tải mới).
- Không đổi: mọi quy tắc tính giá BR-14..BR-23, BR-37, BR-38, BR-39, BR-54, BR-71; Đã huỷ / Từ chối; mọi file nhập / xuất đang có.

## Ảnh hưởng tới dữ liệu đã lưu
- Trường mới có mặc định rỗng cho mọi mã đang có; không mã nào tự đổi trạng thái. Dữ liệu sợi lưu dạng bản ghi có trường mở
  rộng → không cần đổi bảng nếu kho lưu chấp nhận trường mới với mặc định (kiểm tra ở bước làm; cần thì thêm migration).
- Khi đánh dấu: dòng giá bị gỡ khỏi mã, mỗi dòng có Tổng > 0 được ghi Lịch sử giá (Tổng cũ → 0, sự kiện "Không sản xuất") và
  Nhật ký (trước → sau). Không xoá bản ghi nào.

## Truy vết (điền ở bước làm)
| Hạng mục | Code | Test |
|---|---|---|
| Trường mới + trạng thái | `models/yarn.py`, `models/enums.py` (mặc định trống, không migration; `migrate.py status` up to date) | mọi test |
| BR-72 / UC-47 đánh dấu | `NotProducedBusiness.family/mark_problem/mark`, `SetNotProducedService._mark` | AC-95, AC-96 |
| BR-73 chặn / bỏ qua | `pricing_business.ensure_status`, `NotProducedBusiness.ensure_active` (UC-24, UC-25), `import_business` (UC-34), BR-06, BR-53, BR-62 | AC-97 |
| BR-74 bỏ đánh dấu | `NotProducedBusiness.to_recalculate`, `SetNotProducedService._unmark` (`RecalcBusiness.recalculate`, event "Bỏ đánh dấu không sản xuất") | AC-98, AC-99 |
| BR-75 / UC-48 file | `NotProducedFileReaderBuilder`, `NotProducedBusiness.plan_file`, `ImportNotProducedFileService`, `DownloadNotProducedTemplateService` | AC-100, AC-101 |
| Screen 1 / 3 / 6 | `price_list_page.py`, `nsm_pricing_page.py`, `not_produced_import.py`, `excel_import_page.py` | chạy thử trang (AppTest, dữ liệu thật chỉ đọc): không lỗi, có nút / ô / loại tải mới |
| regression: existing tests | toàn bộ `backend/features/yarn_costing/tests/` | 232 test cũ xanh + 7 test mới = 239 passed (AC-102) |
