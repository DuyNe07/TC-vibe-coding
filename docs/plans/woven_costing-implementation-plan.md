# Implementation plan - woven_costing (Tính giá vải dệt), đợt 1

## 1. Summary
Ứng dụng "Tính giá vải dệt" thay 2 file Excel tính giá HCM / TCDN.
- SO tải dữ liệu vải Peace / WFX, quản lý tỷ giá, bộ định mức, tham số chung có ngày hiệu lực, hệ số theo mã hàng,
  ngày lễ, khách hàng.
- Sales lập costsheet (sợi, ngành Dệt, nhuộm HCM / TCDN, giá bán, lợi nhuận), gửi duyệt, tạo phiên bản, chốt đơn với
  OC, in nhãn.
- Trưởng team / trưởng đơn vị duyệt.
- Mọi người xem danh sách tổng hợp, xuất Excel.

UI concept, một dòng mỗi màn hình (nhóm menu Sales: 1-3, Phòng SO: 4-7):
1. Danh sách costsheet: bộ lọc + ô tổng hợp + bảng chọn dòng + Tạo / Mở / Xuất Excel.
2. Costsheet: tiêu đề + ô tóm tắt + form thông tin đơn + thẻ (Thông số vải, Sợi, Ngành Dệt, Nhuộm, Giá bán, Tham số,
   Cảnh báo, Lịch sử) + thanh nút theo trạng thái; bảng dòng sửa trong ô.
3. Việc chờ tôi: các bảng theo nhóm, chọn dòng + Mở.
4. Dữ liệu mã vải: thẻ Tải Peace/WFX, thẻ Tra cứu & nhập tay.
5. Định mức và tham số: thẻ Bộ định mức, Tham số chung, Hệ số theo mã hàng, Ngày lễ.
6. Tỷ giá: form + bảng.
7. Khách hàng: tìm + bảng + tải danh sách + sửa.

Hỏi lại (dialog) trước Gửi duyệt, Duyệt, Trả lại, Chốt đơn, Hủy, Lưu dữ liệu vải, Lưu bộ định mức.

## 2. Scaffold (done)
`.venv/Scripts/python.exe -X utf8 scripts/new_feature.py woven_costing --title "Tính giá vải dệt" --developer Xuan2894
--prefix xuan2894 --description "..." --icon "🧵" --group "Kinh doanh Woven" --owner "Sales Woven (team FS)"`

Bảng dữ liệu: `xuan2894__woven_costing__<name>`; URL `/soteam-woven-costing` (đổi 2026-11-25 từ `/xuan2894-woven-costing`
theo yêu cầu người dùng, giống app tính giá sợi `/soteam-yarn-costing`; bảng dữ liệu không đổi).

## 3. Reference material (absolute paths, read-only)
- Excel HCM: `D:/Vibe Coding/Woven-fabric/Format/Tinh Gia Det - HCM (Official) 2026 07 01.xlsm` (sheet CostSheet, DM *,
  Định mức Dệt, TỔNG HỢP, DATAHCM, Dữ liệu, PRINT).
- Excel TCDN: `D:/Vibe Coding/Woven-fabric/Format/Tinh Gia Det - TCDN (Official) 2026 07 01 .xlsm` (CostSheet, Tiêu chuẩn,
  HC CPB Tenter, Tên Công Đoạn, DATA1).
- Raw master files: `D:/Vibe Coding/Woven-fabric/Format/Master vai/Raw data - Peace/*.xlsx`,
  `.../Raw data - WFX/*.xlsx`.
- Real costsheets for AC-09: `D:/Vibe Coding/Woven-fabric/Format/File kết quả/*.xlsm`.
- Cell-by-cell formula dumps (text, "cell<TAB>formula<TAB>=> value"):
  `C:/Users/ADMIN/AppData/Local/Temp/claude/2402ece84ee0c194/a2465582-cadd-408e-bf46-a8231a32b5c1/scratchpad/dump/HCM__CostSheet.txt`,
  `.../dump/TCDN__CostSheet.txt`, `.../formulas_full.txt` (DM Se, DM 2025, DM Mac Kiem, dyeing rows, TỔNG HỢP, Tiêu
  chuẩn, HC CPB Tenter), `.../res/R1HCM__CostSheet.txt` … `R4TCDN__CostSheet.txt` (the 4 real files).

## 4. Controller contract (`WovenCostingController`, `backend/features/woven_costing/__init__.py`)
Roles (manifest `roles`, admin ticks on `/admin`):
- `SALES` (Sales), `TRUONG_TEAM` (Trưởng team), `TRUONG_DON_VI` (Trưởng đơn vị), `SO` (Phòng SO), `PD` (PD);
- `FS1` (Team FS1), `FS2` (Team FS2).

`current_user is None` (tests) = mọi quyền. Admin không có vai trò tự động; admin (all_apps) coi như SO + TRUONG_DON_VI.
Role codes / labels live in `dto/common_dto.py` (`ROLE_LABELS`, `RoleCode`) so the manifest imports them.

Ký hiệu cột Cache: C = `@cached_query`.

| UC | Method | Request / Response (file) | Cache |
|---|---|---|---|
| UC-01 | `preview_fabric_import` | `PreviewFabricImportRequest(files: list[UploadedFileDTO])` / `FabricImportPreviewResponse(counts…, rows)` (`fabric_dto.py`) | |
| UC-02 | `save_fabric_import` | same request / `FabricImportSaveResponse(new_count, changed_count, missing_yarn_count, message)` | |
| UC-03 | `save_fabric` | `SaveFabricRequest(is_new, fabric fields, yarns: list[FabricYarnDTO])` / `SaveFabricResponse(tcfno, message)` | |
| UC-04 | `search_fabrics` | `SearchFabricsRequest(keyword, source, missing_yarn_only, selected_tcfno)` / `SearchFabricsResponse(rows, detail)` | C |
| UC-05 | `save_exchange_rate` | `SaveExchangeRateRequest(month, year, rate)` / `MessageResponse` (`master_dto.py`) | |
| UC-06 | `download_norm_template` | `EmptyRequest` / `FileDownloadDTO` | C |
| UC-07 | `save_norm_set` | `SaveNormSetRequest(file, effective_from, note)` / `SaveNormSetResponse` | |
| UC-08 | `view_norm_set` | `ViewNormSetRequest(norm_set_code optional)` / `NormSetResponse(sets list, selected tables)` | C |
| UC-09 | `save_parameter_set` | `SaveParameterSetRequest(effective_from, values…)` / `MessageResponse` | |
| UC-10 | `save_fabric_factor` | `SaveFabricFactorRequest(id optional, fields)` / `MessageResponse` | |
| UC-11 | `save_holiday` | `SaveHolidayRequest(action add/delete, date, name)` / `MessageResponse` | |
| UC-12 | `save_customer_import` | `CustomerImportRequest(file)` / `CustomerImportResponse(added, skipped, rows)` | |
| UC-13 | `update_customer` | `UpdateCustomerRequest(id, name, customer_code, team, active)` / `MessageResponse` | |
| UC-14 | `update_fabric_override` | `UpdateFabricOverrideRequest(costsheet_id, specs, yarns)` / `CostsheetResponse` (`costsheet_dto.py`) | |
| UC-15 | `create_costsheet` | `CreateCostsheetRequest(header fields)` / `CostsheetResponse` | |
| UC-16 | `calculate_costsheet` | `CostsheetInputRequest(costsheet_id optional, full input)` / `CostsheetResponse` (not saved) | |
| UC-17 | `save_draft` | `CostsheetInputRequest(… , confirm_yarn_prices: bool)` / `CostsheetResponse` | |
| UC-18 | `add_customer` | `AddCustomerRequest(name, customer_code, confirm_new)` / `AddCustomerResponse(created, similar)` | |
| UC-19 | `copy_costsheet` | `CostsheetActionRequest(costsheet_id)` / `CostsheetResponse` | |
| UC-20 | `submit_costsheet` | `CostsheetActionRequest(costsheet_id)` / `CostsheetResponse(+ warnings, auto_approved)` | |
| UC-21 | `approve_costsheet` | `CostsheetActionRequest` / `CostsheetResponse` | |
| UC-22 | `return_costsheet` | `CostsheetActionRequest(costsheet_id, reason)` / `CostsheetResponse` | |
| UC-23 | `new_version` | `CostsheetActionRequest` / `CostsheetResponse` | |
| UC-24 | `save_oc` | `SaveOcRequest(costsheet_id, oc_no, close_order: bool)` / `CostsheetResponse` | |
| UC-25 | `cancel_costsheet` | `CostsheetActionRequest(costsheet_id, reason)` / `CostsheetResponse` | |
| UC-26 | `print_label` | `PrintLabelRequest(labels: list[LabelInputDTO(tcfno, remark)])` / `FileDownloadDTO` | |
| UC-27 | `list_costsheets` | `ListCostsheetsRequest(filters…)` / `CostsheetListResponse(rows, kpis)` (`list_dto.py`) | |
| UC-28 | `export_costsheets` | same request / `FileDownloadDTO` | |
| UC-29 | `get_costsheet` | `GetCostsheetRequest(costsheet_id or costsheet_no + version)` / `CostsheetResponse` (+ versions, history, allowed_actions) | |
| UC-30 | `list_my_tasks` | `EmptyRequest` / `MyTasksResponse(groups)` | |
| UC-31 | `list_exchange_rates` | `EmptyRequest` / `ExchangeRateListResponse` | C |
| UC-32 | `list_parameter_sets` | `EmptyRequest` / `ParameterSetListResponse(sets, latest)` | C |
| UC-33 | `list_fabric_factors` | `EmptyRequest` / `FabricFactorListResponse` | C |
| UC-34 | `list_holidays` | `EmptyRequest` / `HolidayListResponse` | C |
| UC-35 | `list_customers` | `ListCustomersRequest(keyword)` / `CustomerListResponse` | C |
| UC-36 | `preview_customer_import` | `CustomerImportRequest(file)` / `CustomerImportResponse` (nothing saved) | |
| UC-37 | `preview_norm_set` | `SaveNormSetRequest` / `NormSetPreviewResponse(sheet counts, changes, errors)` | |
| UC-38 | `get_costsheet_options` | `EmptyRequest` / `CostsheetOptionsResponse(customers, lists of values, current user roles/team)` | |
| UC-39 | `list_fabric_imports` | `EmptyRequest` / `FabricImportLogResponse(last 5)` | C |

`list_costsheets`, `get_costsheet`, `list_my_tasks`, `get_costsheet_options` depend on the current user, so they are
not cached.

Pages (`frontend/features/woven_costing/pages/`):

| Page class | Slug | Screen | Menu group |
|---|---|---|---|
| `CostsheetListPage` | (landing) | 1 | Sales |
| `CostsheetPage` | `costsheet` | 2 | Sales |
| `MyTasksPage` | `viec-cho-toi` | 3 | Sales |
| `FabricDataPage` | `ma-vai` | 4 | Phòng SO |
| `NormParameterPage` | `dinh-muc` | 5 | Phòng SO |
| `ExchangeRatePage` | `ty-gia` | 6 | Phòng SO |
| `CustomerPage` | `khach-hang` | 7 | Phòng SO |

## 5. Requirement Traceability Matrix
Status is ticked by the lead after verification.

| Spec item | Description (VI) | Code element | Test | Status |
|---|---|---|---|---|
| 4.1-4.3 | Mã vải, sợi, nhật ký tải | models/fabric.py, fabric_import.py | test_master_services.py | ✅ |
| 4.4, 4.7-4.9 | Tỷ giá, hệ số, ngày lễ, khách hàng | models/master.py | test_master_services.py | ✅ |
| 4.5 | Bộ định mức (12 bảng) | models/norm_set.py, seed_norms.py | test_master_services.py, test_calculation.py | ✅ |
| 4.6 | Bộ tham số | models/parameter_set.py | test_master_services.py | ✅ |
| 4.11-4.20 | Costsheet | models/costsheet*.py | test_costsheet_flow.py | ✅ |
| F-01..F-04, F-06 | File Peace / WFX, khách hàng | builders/file_readers.py | test_master_services.py | ✅ |
| F-05 | Bộ định mức | builders/norm_file_builders.py | test_master_services.py | ✅ |
| F-07, F-08 | Nhãn Word, danh sách Excel | builders/document_builders.py | test_costsheet_flow.py | ✅ |
| UC-01..UC-39 | xem mục 4 | controller + services/ | test_costsheet_flow.py, test_master_services.py | ✅ |
| BR-01..BR-80 | xem tài liệu mục 7 | business/*.py | test_rules.py, test_calculation.py | ✅ |
| AC-01..AC-43 | xem tài liệu mục 9 | | test_ac09_real_costsheets.py + các test trên; giao diện: test_pages_render | ✅ |
| Screens 1-7 | xem UI concept | frontend/features/woven_costing/pages/*.py | tests/architecture/test_pages_render.py | ✅ |

## 6. Steps
- ✅ Step 0 UI concept recorded
- ✅ Scaffold
- ✅ Backend (section 9) - ALL CHECKS PASSED
- ✅ UI design (section 10)
- ✅ UI build (section 11) - ALL CHECKS PASSED
- ✅ Gateway registration check (39 use cases + ping)
- ✅ Navigation check (7 pages, landing = CostsheetListPage, 2 menu groups, roles)
- ✅ Scaffold ping: kept (its scaffold test may not be deleted); no page calls it
- ✅ Document updated (sections 10, 11, Status = Implemented)
- ✅ Verify (Step 5): ALL CHECKS PASSED (417 tests), APP IS HEALTHY
- ✅ Report

## 7. Implementation assumptions
- UC-31..UC-39 thêm cho các bảng / thao tác màn hình cần (chỉ đọc hoặc xem trước), áp dụng BR có sẵn.
- Initial data: bộ định mức, bộ tham số, hệ số ES1702…, danh mục được tạo sẵn từ số của file Excel khi bảng còn trống
  (seed, hiệu lực 2026-01-01).

## Fix log
- `check.py --fix` reformatted 5 files of other parts of the repo.
  - Cause: `ruff format .` runs over the whole repository.
  - Fix: restored the 5 files with the user's approval; later formatting runs only on the feature folders.
  - Verification: git status shows no change outside the feature except the registry line.
- Removing the scaffold ping test was refused (tests may not be deleted).
  - Fix: restored the ping DTO, service and controller method; no page uses them.
  - Verification: ALL CHECKS PASSED.
- doctor reported "Database is not up to date" (core and yarn_costing pending on the local database).
  - Fix: ran scripts/migrate.py.
  - Verification: APP IS HEALTHY.
- run.ps1 created `.env` from `.env.example` with empty Postgres values and stopped at the migration (POSTGRES_PORT
  empty).
  - Cause: environment, not feature code.
  - Fix: removed that unchanged template copy, so the local default database is used again.
  - Verification: doctor app check health ok.

## Notes
- Branch: lệnh `git checkout -b … origin/dev` ban đầu bị từ chối vì file `docs/plans/business-analysis-plan.md`
  (Prompt 1) trùng tên file đã có trên dev.
- Đã đổi tên file đó thành `docs/plans/woven_costing-business-analysis-plan.md` rồi tạo nhánh
  `vibe/xuan2894-woven_costing-2011`.
- Đổi giao diện Màn hình 2 (2026-11-23): khung "Chuỗi nhu cầu" hiện chữ "None" ở ô trống -> cột số của bảng hiện ô
  rỗng thành "None" -> chuyển 4 cột số của khung sang chữ đã định dạng kiểu Việt Nam (ô rỗng để trống) -> kiểm tra
  trên trình duyệt + ALL CHECKS PASSED.
- 2026-11-25 | WR (TCDN, costsheet và phiếu gia công nhuộm) thiếu dòng Kiểm trung gian, tiêu hao nhuộm cộng thêm 1% WR
  | so với file "Tinh Gia Det - TCDN" (dòng 91, 104, ô E41): file tự thêm dòng "Kiểm trước WR" (Kiểm Trung Gian) khi
  chọn WR và cộng tiêu hao dòng đó; không cộng 1% tenter của WR (đã nằm trong 4%) | thêm dòng "Kiểm trước WR", tiêu hao
  nhuộm cộng tiêu hao Kiểm Trung Gian thay cho WR; giữ chia chi phí WR cho (1 − 1%) theo người dùng; màn hình nhắc
  "không cần chọn Kiểm Trung Gian nữa" | test_fix_wr_20261125.py (4 test) | ALL CHECKS PASSED (476), APP IS HEALTHY,
  trình duyệt: chọn WR thì tự tính lại.
- 2026-11-25 | Màn hình 8: gõ g/m (hoặc chọn WR) trước khi gõ mã hàng thì dòng biến mất; ô chữ trống hiện "None" |
  dòng chỉ được giữ khi có mã hàng / số lượng / đơn giá | giữ dòng khi có bất kỳ ô hoặc lựa chọn nhuộm nào; ô chữ trống
  để rỗng | test_fix_job_lines_20261125.py (3 test) | ALL CHECKS PASSED (479), APP IS HEALTHY; trình duyệt (tab riêng,
  không lưu): GC-CONG84 gõ g/m 245 giữ dòng, chọn D.W/R hiện dòng "Kiểm trước WR"; CS-ICHI-2026-00001 chọn W/R (C6):
  có dòng "Kiểm trước WR", tiêu hao nhuộm giữ 4%.
