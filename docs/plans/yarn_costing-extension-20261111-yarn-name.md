# yarn_costing - mở rộng 2026-11-11: kiểm tra chính tả, sửa tên sợi, chặn sai khi Sales nhập

Nguồn: `docs/business/_sources/yarn_costing-yarn-name-discovery.md`; rà dữ liệu thật 2026-11-11 (3.054 mã gốc): chữ sai
(COTTTON, VICOSE, RECYLE, CATINONIC, BAMBO, MODACRY), 5 tên thiếu / thừa ngoặc, 136 tên app chưa đọc được thành phần, 660 tên
có chữ thường, 93 nhóm (188 mã) trùng tên sau khi viết hoa. Đề xuất giữ / loại đã gửi và được đồng ý:
`docs/plans/yarn_costing-de-xuat-ten-trung-20261111.xlsx`.

## 1. Thêm / đổi gì
| # | Nội dung | Mục / UC / BR / AC |
|---|---|---|
| 1 | Từ điển tên chuẩn (chữ chuẩn + cách viết sai), khởi tạo từ chữ dùng ≥ 3 lần, Phòng SO quản lý | 4.29, UC-66, BR-100, BR-103, AC-133 |
| 2 | Bảng "Tên nghi sai": chữ lạ + gợi ý, ngoặc, tỷ lệ, không đọc được, trùng tên | UC-65, BR-100, AC-134 |
| 3 | Chữ mới chờ duyệt: app tự ghi lại; Phòng SO "Thêm vào từ điển" / "Sai, sửa thành"; tự thêm khi sợi được tính giá | 4.30, UC-67, BR-104, BR-106, AC-139, AC-140 |
| 4 | Đổi tên một sợi (lý do, tên cũ giữ để tìm, nhóm tiêu hao đổi theo khi chỉ sợi đó dùng) | 4.12 (thêm trường), UC-68, BR-105, BR-108, AC-136, AC-137 |
| 5 | Đổi tên hàng loạt bằng Excel | 5.13, UC-69, AC-138 |
| 6 | Ô ghép tên + nhóm sợi / từ khoá; nhóm lạ Sales gõ tay được app tự thêm (đánh dấu "mới") | 4.31, UC-70, BR-102, BR-103, AC-141, AC-142 |
| 7 | Gửi / sửa yêu cầu: chặn thiếu ngoặc, tỷ lệ ≠ 100; chữ lạ phải chọn gợi ý hoặc ghi lý do; tên viết hoa | UC-15, UC-16 (sửa), BR-101, AC-135 |
| 8 | Chuẩn hoá viết hoa một lượt + xử lý tên trùng (giữ 1, loại còn lại = Không sản xuất / Từ chối, chuyển tên theo khách + mã kế toán) | UC-71, BR-107, AC-143, AC-144 |
| 9 | Quyền | BR-109, AC-145 |

## 2. Ảnh hưởng tới cái đang có
- UC-15 / UC-16: form có ô ghép tên (mặc định) và chế độ gõ tay; thêm kiểm tra BR-101; tên lưu viết hoa. BR-01, BR-06, BR-76..BR-78
  giữ nguyên.
- BR-72 (Không sản xuất) giữ nguyên cho thao tác thường; riêng loại mã trùng tên (BR-107) được đánh dấu cả mã có mã kế toán.
- BR-82 (ghép mã kế toán), tìm kiếm ở bảng giá / so sánh 2 sợi / tính giá báo khách, gợi ý Trùng (BR-77) dùng thêm tên cũ và mã kế
  toán gộp (BR-108).
- Đổi tên không đổi giá, mã tính giá, mã kế toán; không tính lại giá.
- Menu nhóm "Phòng SO" thêm màn "Kiểm tra tên sợi" (Sales cũng mở được, thao tác theo BR-109).

## 3. Dữ liệu đã lưu
- 4.12 thêm `old_names` (mặc định rỗng), `unknown_word_reason` (mặc định trống), `merged_accounting_codes` (mặc định rỗng),
  `name_mode` (mặc định trống = tên cũ) - mã cũ đọc được, không cần chuyển đổi.
- Bảng mới 4.29, 4.30, 4.31: lần mở đầu tiên khởi tạo theo BR-103.
- Chuẩn hoá viết hoa (UC-71) đổi `yarn_name` của 660 mã (tên cũ lưu vào `old_names`), loại 95 mã trùng theo đề xuất; mọi thay đổi
  ghi nhật ký; không xoá gì.

## 4. Câu hỏi đã trả lời (2026-11-11)
- Sửa tên sợi đã tính giá: chỉ Phòng SO (1a); sợi chưa tính giá: Phòng SO + Sales (1b). Sợi có mã kế toán: sửa được, có lý do,
  chỉ Phòng SO (2a+b). Chữ lạ khi gửi: chọn gợi ý hoặc ghi lý do (3b). Ô ghép tên: có (4a). Viết hoa toàn bộ, đổi một lượt (5a).
- Từ điển do Phòng SO quản lý, khởi tạo tự động (1a). Sửa chữ sai sửa cả tên nhóm tiêu hao (2a). Tên trùng: giữ 1, loại còn lại theo
  đề xuất (3a; 13 mã có mã kế toán: loại và chuyển mã kế toán sang mã giữ - a); "loại" = Không sản xuất (đúng). Đổi tên trùng sợi
  khác cùng xưởng: chặn (4). Ô ghép tên như đề xuất, nhóm sợi lạ app tự thêm (5). Viết hoa một lượt có xem trước (6). Chữ mới:
  app tự ghi lại, Phòng SO duyệt + tự thêm khi tính giá (7c).

## 5. Giả định
- Chữ = chuỗi chữ cái (không có chữ số) dài ≥ 2 trong tên đã viết hoa, bỏ dấu; mã kỹ thuật có chữ số (50D, 32F, 1.2D) không kiểm tra.
- Đổi tên không được làm đổi chi số, công nghệ (MVS / Ring), loại compact - các thứ đó làm đổi giá, phải tạo yêu cầu mới.
- Mã trùng đang "Chờ xưởng xem" được loại bằng Từ chối (lý do trùng tên); mã Đã huỷ / Từ chối không cần loại.

## 6. Truy vết khi làm (Prompt 5 Step 6)
| Mục | Mã | Kiểm thử |
|---|---|---|
| BR-100, UC-65 | `NameCheckBusiness.check / suspects`, `services/get_name_check_service.py` | AC-134 |
| BR-101, UC-15 / UC-16 | `ensure_request_name`, `services/create_yarn_request_service.py`, `update_yarn_request_service.py`, `check_yarn_name_service.py` | AC-135, AC-146 |
| BR-102, UC-70 | `build_name`, `new_group`, `services/save_name_parts_service.py`, `components/name_input.py` | AC-141, AC-142 |
| BR-103, UC-66 | `initial_words`, `initial_parts`, `ensure_dictionary`, `services/save_name_dictionary_service.py` | AC-133 |
| BR-104, UC-67 | `PendingWordRepository.record`, `GetNameCheckService._auto_add`, `services/resolve_pending_word_service.py` | AC-135, AC-139 |
| BR-105, UC-68 / UC-69 | `plan_rename`, `loss_group_change`, `renamed_group`, `services/rename_yarn_service.py`, `import_rename_file_service.py`, `export_rename_list_service.py` | AC-136, AC-137, AC-138 |
| BR-106 | `replace_everywhere` | AC-140 |
| BR-107, UC-71 | `duplicate_plan`, `upper_changes`, `services/normalize_names_service.py` | AC-143, AC-144 |
| BR-108 | price rows search, blend suggest, accounting lines_by_code, quote suggestions | AC-137, AC-144 |
| BR-109 | `models/access.py`, `ensure_can_rename` | AC-137, AC-145 |
| regression: existing tests | toàn bộ kiểm thử cũ giữ xanh | `scripts/check.py` → ALL CHECKS PASSED |
