# Implementation plan: yarn_costing

## 0. Summary
Chức năng "Tính giá sợi" thay thế hai file Excel tính giá sợi S1 / S4: Sales tạo yêu cầu (mã tự sinh), xưởng nhập NSM +
tỷ lệ pha, app kiểm tra khớp rồi tính chi phí sản xuất/kg (5 khoản, VND, USD), tự tạo dòng thí nghiệm, CK/PP, ĐCNSM; kế
toán / xưởng nhập mã kế toán để khoá; Phòng SO quản lý dữ liệu nền, tính lại toàn bộ, chuyển dữ liệu cũ từ file Excel và theo
dõi dashboard. Công thức đã được đối chiếu với file thật (S4-2017 = 19.777,8356; S1-1310 = 12.169,6248 VND/kg).

UI concept (1 dòng / màn hình):
1. Bảng giá đã tính (landing) - bộ lọc, tỷ giá + hệ số, 4 KPI, bảng chọn dòng đầy đủ cột, Xuất Excel, kiểm tra giá bất thường, khối dòng chọn (chi tiết, lịch sử, mã kế toán, CK/PP).
2. Yêu cầu tính giá - form tạo + "App nhận ra", bộ lọc, bảng chọn dòng, khối sửa / huỷ.
3. Nhập NSM & tính giá - KPI trạng thái, bảng mã chọn dòng, tỷ lệ pha, bảng NSM sửa trong ô, kiểm tra / lưu / ĐCNSM / từ chối, khối kết quả.
4. Tiêu hao - bộ lọc, bảng nhóm chọn dòng, bảng tiêu hao / thành phần sửa trong ô, thêm / lưu / xoá.
5. Dữ liệu nền & định mức - tabs: Công đoạn | Định mức | Đóng gói | Hồi phế | Quy trình | Tỷ giá & hệ số TN | Các lần tính lại (bảng sửa trong ô + ngày hiệu lực + lý do).
6. Nhập dữ liệu từ Excel - tải mẫu, kiểm tra, kết quả, lưu, các lần nhập, đối chiếu giá cũ.
7. Dashboard kiểm soát - 5 KPI, 2 biểu đồ theo tuần, KPI trạng thái, chênh lệch lần tính lại, sai lệch giá, NSM bất thường.
8. Người dùng & nhật ký - bảng nhóm chọn dòng, bảng thành viên sửa trong ô, nhật ký.

## 1. Scaffold command
```
.venv/Scripts/python.exe -X utf8 scripts/new_feature.py yarn_costing --title "Tính giá sợi" --description "Thay thế hoàn toàn file Excel tính giá sợi của Xưởng Sợi 1 và Sợi 4: từ yêu cầu của Sales đến bảng giá có mã kế toán." --icon "🧵" --group "Tính Giá Sợi" --owner "Phòng SO"
```

## 2. Controller contract (binding for Backend + UI-build)
`YarnCostingController` (`backend/features/yarn_costing/controllers/yarn_costing_controller.py`).
Common DTOs (`dto/common_dto.py`): `ActorDTO{group_code: str, access_code: str, person_name: str}`; enums re-exported from
models: `FactoryCode(S1,S4)`, `GroupCode(SALES,XS1,XS4,SO,KT)`, `YarnStatus`, `LineType`, `LossGroupLevel`,
`RecoveryType`, `Technology`, `ImportMode`, `NsmMode`. Every mutating request has `actor: ActorDTO` as first field.
All money / rates / ratios are `Decimal`; ratios and losses are fractions (0.015 = 1,5%).

| # | Method | Request (dto file) | Response | UC |
|---|---|---|---|---|
| 1 | `save_user_group` | `SaveUserGroupRequest{actor, group_code, name, new_access_code: str\|None, active: bool, members: list[GroupMemberRowDTO{name, active}]}` (user_dto.py) | `UserGroupResponse{group: UserGroupDTO}` | UC-01 |
| 2 | `list_audit_log` | `ListAuditLogRequest{date_from: date\|None, date_to: date\|None, group_code: str\|None, keyword=""}` (audit_dto.py) | `AuditLogListResponse{items: list[AuditLogDTO]}` | UC-02 |
| 3 | `save_stage_config` | `SaveStageConfigRequest{actor, factory_code, rows: list[StageRowDTO], effective_date: date, reason}` (master_dto.py) | `RecalcResultResponse{message, batch: RecalcBatchDTO\|None}` | UC-03 |
| 4 | `apply_rate_version` | `ApplyRateVersionRequest{actor, factory_code, rows: list[RateLineRowDTO], effective_date, reason}` | `RecalcResultResponse` | UC-04 |
| 5 | `save_packaging_types` | `SavePackagingTypesRequest{actor, factory_code, rows: list[PackagingRowDTO], effective_date, reason}` | `RecalcResultResponse` | UC-05 |
| 6 | `save_recovery_rates` | `SaveRecoveryRatesRequest{actor, factory_code, rows: list[RecoveryRowDTO], effective_date, reason}` | `RecalcResultResponse` | UC-06 |
| 7 | `save_process_routes` | `SaveProcessRoutesRequest{actor, factory_code, rows: list[ProcessRouteRowDTO]}` | `SaveCountResponse{message, saved_count}` | UC-07 |
| 8 | `add_exchange_rate` | `AddExchangeRateRequest{actor, effective_date, rate: Decimal, note=""}` | `SaveCountResponse` | UC-08 |
| 9 | `update_trial_factor` | `UpdateTrialFactorRequest{actor, trial_factor: Decimal, effective_date, reason}` | `RecalcResultResponse` | UC-09 |
| 10 | `list_loss_groups` | `ListLossGroupsRequest{factory_code, level: LossGroupLevel\|None, keyword="", locked_only=False}` (loss_dto.py) | `LossGroupListResponse{items: list[LossGroupDTO], stage_codes: list[str]}` (LossGroupDTO has losses dict, components list, is_locked, used_by_codes, locked_codes) | UC-10 |
| 11 | `create_primary_loss_group` | `CreatePrimaryLossGroupRequest{actor, factory_code, yarn_group_label, material="", technology, losses: dict[str, Decimal]}` | `LossGroupSaveResponse{message, group: LossGroupDTO, recalculated_count}` | UC-11 |
| 12 | `create_secondary_loss_group` | `CreateSecondaryLossGroupRequest{actor, factory_code, yarn_group_label, material="", technology, components: list[ComponentRowDTO{component_group_key, ratio}], save: bool}` | `LossGroupSaveResponse` (save=False → preview: group with computed losses, nothing stored) | UC-12 |
| 13 | `update_loss_group` | `UpdateLossGroupRequest{actor, factory_code, group_key, material, technology, losses: dict[str, Decimal]\|None, components: list[ComponentRowDTO]\|None, reason, effective_date: date\|None}` | `LossGroupSaveResponse` | UC-13 |
| 14 | `delete_loss_group` | `DeleteLossGroupRequest{actor, factory_code, group_key}` | `SaveCountResponse` | UC-14 |
| 15 | `create_yarn_request` | `CreateYarnRequestRequest{actor, factory_code, yarn_name, packaging_code}` (request_dto.py) | `YarnResponse{message, yarn: YarnDTO}` | UC-15 |
| 16 | `update_yarn_request` | `UpdateYarnRequestRequest{actor, yarn_code, yarn_name, packaging_code}` | `YarnResponse` | UC-16 |
| 17 | `cancel_yarn_request` | `CancelYarnRequestRequest{actor, yarn_code}` | `YarnResponse` | UC-17 |
| 18 | `reject_yarn_request` | `RejectYarnRequestRequest{actor, yarn_code, reason}` | `YarnResponse` | UC-18 |
| 19 | `list_yarns` | `ListYarnsRequest{factory_code: FactoryCode\|None, statuses: list[YarnStatus]\|None, date_from, date_to, keyword="", origin: str\|None}` | `YarnListResponse{items: list[YarnSummaryDTO], status_counts: dict[str, int]}` | UC-19 |
| 20 | `suggest_nsm` | `SuggestNsmRequest{yarn_code}` (pricing_dto.py) | `NsmSuggestionResponse{found: bool, message, reference_yarn_code, reference_yarn_name, reference_count, nsm: dict[str, Decimal], blend_ratios: dict[str, Decimal]}` | UC-20 |
| 21 | `save_yarn_nsm` | `SaveYarnNsmRequest{actor, yarn_code, blend_ratios: dict[str, Decimal], nsm: dict[str, Decimal], nsm_mode, reference_yarn_code: str\|None, nsm_warning_reason="", save: bool}` | `PricingResultResponse{message, saved: bool, check_passed: bool, reasons: list[str], warning_stages: list[str], reference_yarn_code, stage_details: list[StageCostDTO], line: PriceLineDTO\|None, trial_line: PriceLineDTO\|None, yarn: YarnDTO}` | UC-21 |
| 22 | `get_yarn_detail` | `GetYarnDetailRequest{yarn_code: str\|None, line_code: str\|None}` | `YarnDetailResponse{yarn: YarnDTO, stages: list[StageInputDTO{stage_code, stage_name, nsm, reference_nsm}], stage_details: list[StageCostDTO], lines: list[PriceLineDTO], revisions: list[YarnSummaryDTO], history: list[PriceHistoryDTO], blend_slots: list[str]}` | UC-22 |
| 23 | `correct_yarn_nsm` | `CorrectYarnNsmRequest` (same fields as SaveYarnNsmRequest) | `PricingResultResponse` | UC-23 |
| 24 | `create_nsm_revision` | `CreateNsmRevisionRequest{actor, source_yarn_code, adjust_reason, blend_ratios, nsm, nsm_warning_reason="", save: bool}` | `PricingResultResponse` | UC-24 |
| 25 | `create_adjustment_line` | `CreateAdjustmentLineRequest{actor, yarn_code, line_type: LineType(Chiết khấu/Phụ phí), percent: Decimal (0.05 = 5%), reason, order_ref}` (price_dto.py) | `PriceLineResponse{message, line: PriceLineDTO}` | UC-25 |
| 26 | `delete_adjustment_line` | `DeleteAdjustmentLineRequest{actor, line_code}` | `SaveCountResponse` | UC-26 |
| 27 | `list_price_lines` | `ListPriceLinesRequest{factory_code\|None, line_types: list[LineType]\|None, statuses: list[YarnStatus]\|None, technology\|None, yarn_group\|None, has_accounting_code: bool\|None, priced_from, priced_to, keyword=""}` | `PriceLineListResponse{items: list[PriceLineRowDTO], total_count, with_accounting_code_count, not_priced_count, waiting_count, exchange_rate, exchange_rate_date, trial_factor}` | UC-27 |
| 28 | `set_accounting_code` | `SetAccountingCodeRequest{actor, line_code, accounting_code: str}` ("" = xoá) | `PriceLineResponse` | UC-28 |
| 29 | `export_price_lines` | `ExportPriceLinesRequest(ListPriceLinesRequest)` | `FileDownloadDTO` | UC-29 |
| 30 | `check_price_anomalies` | `CheckPriceAnomaliesRequest{factory_code\|None}` (dashboard_dto.py) | `PriceAnomalyResponse{items: list[PriceAnomalyDTO], group_count, pair_count}` | UC-30 |
| 31 | `check_nsm_anomalies` | `CheckNsmAnomaliesRequest{factory_code\|None}` | `NsmAnomalyResponse{items: list[NsmAnomalyDTO]}` | UC-31 |
| 32 | `get_dashboard` | `GetDashboardRequest{factory_code\|None, date_from: date, date_to: date}` | `DashboardResponse{quoted_count, ordered_count, ordered_ratio: Decimal\|None, new_request_count, fulfilment_ratio: Decimal\|None, waiting_count, weekly: list[WeeklyStatDTO{week_start, new_requests, fulfilment_ratio}], status_counts: dict[str,int], last_batch: RecalcBatchDTO\|None, last_batch_up, last_batch_down, last_batch_avg_percent}` | UC-32 |
| 33 | `download_template` | `DownloadTemplateRequest{factory_code}` (import_dto.py) | `FileDownloadDTO` | UC-33 |
| 34 | `import_workbook` | `ImportWorkbookRequest{actor, factory_code, mode: ImportMode, cutoff_date: date, file: UploadedFileDTO, commit: bool}` | `ImportResultResponse{message, committed: bool, sheets: list[SheetResultDTO{sheet, read, created, updated, rejected, skipped_message}], rejected_rows: list[RejectedRowDTO{sheet, excel_row, key, reason}], valid_count, import_id: str\|None, result_file: FileDownloadDTO\|None}` | UC-34 |
| 35 | `get_legacy_comparison` | `GetLegacyComparisonRequest{import_id, only_mismatch=False}` | `LegacyComparisonResponse{items: list[LegacyComparisonRowDTO], matched_count, mismatched_count, not_priced_count}` | UC-35 (export: `export_legacy_comparison`? - NO: the response includes `file: FileDownloadDTO` for "Xuất Excel") |
| 36 | `list_recalc_batches` | `ListRecalcBatchesRequest{factory_code\|None}` (master_dto.py) | `RecalcBatchListResponse{items: list[RecalcBatchDTO]}` | UC-36 |
| 37 | `get_recalc_diff` | `GetRecalcDiffRequest{batch_id, line_types: list[LineType]\|None}` | `RecalcDiffResponse{batch, items: list[RecalcDiffRowDTO], up_count, down_count, unchanged_count, avg_percent, file: FileDownloadDTO}` | UC-37 |
| 38 | `get_reference_data` | `GetReferenceDataRequest{factory_code: FactoryCode\|None}` (reference_dto.py) | `ReferenceDataResponse{groups: list[UserGroupDTO], factories: list[FactoryDTO{code, name, blend_slots}], stages: list[StageRowDTO], current_rate: RateVersionDTO\|None, rate_versions: list[RateVersionDTO], packaging: list[PackagingRowDTO], recovery: list[RecoveryRowDTO], routes: list[ProcessRouteRowDTO], exchange_rates: list[ExchangeRateDTO], current_exchange_rate: ExchangeRateDTO\|None, trial_factor, yarn_groups: list[str]}` | UC-38 |
| 39 | `verify_actor` | `VerifyActorRequest{actor}` (user_dto.py) | `ActorResponse{message, group_code, group_name, person_name, factory_code}` | UC-39 |
| 40 | `analyze_yarn_name` | `AnalyzeYarnNameRequest{factory_code, yarn_name}` (request_dto.py) | `YarnNameAnalysisResponse{valid, message, yarn_group, count, technology, is_compact, loss_group_key, loss_group_exists, duplicate_code: str\|None}` | UC-40 |
| 41 | `list_import_batches` | `ListImportBatchesRequest{factory_code\|None}` (import_dto.py) | `ImportBatchListResponse{items: list[ImportBatchDTO]}` | UC-41 |

`PriceLineRowDTO` = one row of sheet `Bang gia` (5.4) with every column (english snake_case names). `YarnDTO` = every field of
model 4.12 + `is_locked`. `StageCostDTO` = fields of 4.14.

### Pages (frontend/features/yarn_costing/pages/)
| Page class | Slug | Screen |
|---|---|---|
| `PriceListPage` | (landing) | Screen 1 Bảng giá đã tính |
| `YarnRequestPage` | `yeu-cau-tinh-gia` | Screen 2 |
| `NsmPricingPage` | `nhap-nsm-tinh-gia` | Screen 3 |
| `LossGroupPage` | `tieu-hao` | Screen 4 |
| `MasterDataPage` | `du-lieu-nen` | Screen 5 |
| `ExcelImportPage` | `nhap-du-lieu-excel` | Screen 6 |
| `DashboardPage` | `dashboard` | Screen 7 |
| `UserAuditPage` | `nguoi-dung-nhat-ky` | Screen 8 |

## 3. Requirement Traceability Matrix
Status: ☐ = todo, ✅ = implemented + tested. (Filled in by the lead after the build.)

### 3.1 Data (section 4)
| Spec item | Description (VI) | Code element | Test | Status |
|---|---|---|---|---|
| 4.1 UserGroup (code, name, factory_code, access_code, active) | Nhóm người dùng | models/user_group.py::UserGroup | tests/test_user_services.py | ✅ |
| 4.2 GroupMember (group_code, name, active) | Thành viên | models/user_group.py::GroupMember | tests/test_user_services.py | ✅ |
| 4.3 Factory (code, name, blend_slots, code_prefix) | Xưởng | constants.py::FACTORIES | tests/test_calculation.py | ✅ |
| 4.4 Stage (13 trường) + seed 4.4.1 / 4.4.2 | Công đoạn + cấu hình | models/stage.py, constants.py::SEED_STAGES | tests/test_calculation.py | ✅ |
| 4.5 RateVersion + 4.5.1 RateLine | Định mức | models/rate_version.py | tests/test_master_services.py | ✅ |
| 4.6 PackagingType | Đóng gói | models/packaging_type.py | tests/test_master_services.py | ✅ |
| 4.7 RecoveryRate | Hồi phế | models/recovery_rate.py | tests/test_master_services.py | ✅ |
| 4.8 ProcessRoute (+ route_stages) | Quy trình công nghệ | models/process_route.py | tests/test_rules.py | ✅ |
| 4.9 ExchangeRate | Tỷ giá | models/exchange_rate.py | tests/test_master_services.py | ✅ |
| 4.10 Settings (trial_factor) | Tham số | models/settings.py | tests/test_master_services.py | ✅ |
| 4.11 LossGroup (12 trường) | Nhóm tiêu hao | models/loss_group.py | tests/test_loss_services.py | ✅ |
| 4.12 Yarn (30 trường) + trạng thái | Mã sợi / bản NSM | models/yarn.py | tests/test_request_services.py, tests/test_pricing_services.py | ✅ |
| 4.13 PriceLine | Dòng bảng giá | models/yarn.py::PriceLine | tests/test_price_services.py | ✅ |
| 4.14 StageCostDetail | Chi tiết tính giá | models/yarn.py::StageCostDetail | tests/test_calculation.py | ✅ |
| 4.15 PriceHistory | Lịch sử giá | models/price_history.py | tests/test_pricing_services.py | ✅ |
| 4.16 RecalcBatch | Lần tính lại | models/recalc_batch.py | tests/test_master_services.py | ✅ |
| 4.17 LegacyPrice | Giá cũ đối chiếu | models/legacy_price.py | tests/test_import_services.py | ✅ |
| 4.18 ImportBatch | Lần nhập file | models/import_batch.py | tests/test_import_services.py | ✅ |
| 4.19 AuditLog | Nhật ký | models/audit_log.py | tests/test_user_services.py | ✅ |

### 3.2 Files (section 5)
| Spec item | Description (VI) | Code element | Test | Status |
|---|---|---|---|---|
| 5.1 / BR-41 | Quy định file tải lên | builders/workbook_reader_builder.py | tests/test_import_services.py | ✅ |
| 5.2 7 sheet + cột | Đọc sheet | builders/workbook_reader_builder.py | tests/test_import_services.py | ✅ |
| 5.3 File mẫu | Tải mẫu | builders/template_file_builder.py | tests/test_import_services.py | ✅ |
| 5.4 Bảng giá (2 sheet) | Xuất bảng giá | builders/price_export_file_builder.py | tests/test_price_services.py | ✅ |
| 5.5 Đối chiếu / chênh lệch / kết quả nhập | Xuất khác | builders/*_file_builder.py | tests/test_import_services.py, tests/test_master_services.py | ✅ |

### 3.3 Use cases / Business rules / Acceptance criteria
| Spec item | Description (VI) | Code element | Test | Status |
|---|---|---|---|---|
| UC-01..UC-41 | 41 use case | controller method (bảng 2) + services/<name>_service.py | tests/test_*_services.py | ✅ |
| BR-01..BR-13, BR-45 (xác thực), BR-46..BR-48 | Quy tắc kiểm tra | business/*_rules.py (BaseBusinessRule, code = BR-xx) | tests/test_rules.py | ✅ |
| BR-14..BR-23 | Công thức tính giá | business/costing_business.py::CostingBusiness | tests/test_calculation.py | ✅ |
| BR-24..BR-29 | Tiêu hao | business/loss_business.py | tests/test_loss_services.py | ✅ |
| BR-30..BR-36 | Dòng giá, khoá, tính lại | business/price_line_business.py, business/recalc_business.py | tests/test_pricing_services.py | ✅ |
| BR-37..BR-39, BR-53..BR-55 | Sợi so sánh, cảnh báo, dashboard, bất thường, đối chiếu | business/analysis_business.py | tests/test_dashboard_services.py | ✅ |
| BR-40..BR-45 | Nhập file | business/import_business.py | tests/test_import_services.py | ✅ |
| BR-49..BR-52 | Nhật ký, dữ liệu nền | business/master_business.py | tests/test_master_services.py | ✅ |
| AC-01, AC-12 | Khớp số với file thật (S4-2017, S1-1310) | business/costing_business.py | tests/test_calculation.py::test_s4_2017 / test_s1_1310 | ✅ |
| AC-02..AC-49 | Tiêu chí nghiệm thu | services + pages | tests/test_*_services.py, page render test | ✅ |

### 3.4 Screens (section 8) - UI concept
| Spec item | Description (VI) | Code element | Test | Status |
|---|---|---|---|---|
| Menu 8 mục | Thứ tự menu | frontend/features/yarn_costing/manifest.py | tests/architecture/test_pages_render.py | ✅ |
| Xác thực nhớ trong phiên | Khối xác thực | frontend/features/yarn_costing/components/actor_block.py | page render test | ✅ |
| Screen 1..8 | 8 trang | pages/*.py (bảng trang ở mục 2) | page render test | ✅ |
| Hộp thoại xác nhận | st.dialog trước các thao tác đã chốt | pages/*.py | page render test | ✅ |

## 4. Fix log
(symptom -> cause -> fix -> verification)
- Sub-agent backend bị dừng 2 lần giữa chừng do phiên kết thúc -> chưa có tests/lint -> tiếp tục từ file đã có -> ALL CHECKS PASSED.
- Lint (N817 `Decimal as D`, thứ tự import) -> sai quy ước ruff -> sửa import -> ruff OK.
- UI: SIM102 (if lồng nhau) trong nsm_pricing_page.py -> gộp điều kiện -> ALL CHECKS PASSED.
- Dashboard hiện "Sợi có đơn hàng 190 (2.227,43%)" -> backend trả tỷ lệ đã nhân 100, trang nhân 100 lần nữa (cũng ở chênh lệch % lần tính lại và đối chiếu giá cũ) -> thêm `percent_value/percent_text` (giá trị đã là %) trong components/display.py và dùng cho các chỗ đó -> ALL CHECKS PASSED, APP IS HEALTHY.
- Kiểm tra trên trình duyệt: nút "Xác nhận" xác thực có vẻ bị tắt -> do thao tác tự động gõ nhầm ô khi phóng to khung nhìn, không phải lỗi app (AppTest headless xác nhận hoạt động) -> thao tác lại ở kích thước thường -> xác thực thành công; hộp thoại "Lưu hồi phế và tính lại" chạy đúng (tính lại 1.318 mã S1).


## 5. Checkboxes
- [x] Step 0 UI concept recorded
- [x] Scaffold
- [x] Backend (section 9) - ALL CHECKS PASSED
- [x] UI design (section 10)
- [x] UI build (section 11) - ALL CHECKS PASSED
- [x] Gateway registration check
- [x] Navigation check
- [x] Scaffold ping removed
- [x] Document updated
- [x] Verify (Step 5)
- [x] Report

## Implementation assumptions (mirrors document section 10)
- UC-38..UC-41 thêm cho giao diện (chỉ đọc / kiểm tra).
- UC-21 (mã chờ / chưa tính được) và UC-23 (mã đã tính giá) là hai method riêng; UC-12/21/23/24/34 có cờ xem trước.

## 6. Bổ sung 2026-09-28: đóng gói mặc định + chải thô nhiều lượt (BR-56..BR-60, AC-50..AC-61)
Tóm tắt: mỗi xưởng một loại đóng gói mặc định (điền sẵn ở Screen 2); bỏ C3.1/C3.2/C3.3 → công đoạn C3; S4 C2/C3 và S1 C1/C2
là dây chuyền chải thô nhiều lượt (tối đa 3), S4 C1 một lượt; sợi có bảng thành phần nguyên liệu (nguyên liệu, tỷ lệ, dây
chuyền, lượt tự đánh, NSM chải thô); NSM công đoạn khác nhập một lần. Giá của dữ liệu cũ phải giữ nguyên (S4-2017, S1-1310).

UI concept thay đổi: Screen 2 điền sẵn đóng gói mặc định; Screen 3 hai bảng sửa trong ô (① thành phần nguyên liệu ở trên, ②
NSM công đoạn khác ở dưới), kết quả có cột Nguyên liệu / Lượt; Screen 5 thẻ Đóng gói có cột "Mặc định"; Screen 1 cột "Thành
phần" dạng chữ.

### 6.1 Contract changes (binding)
| Item | Change |
|---|---|
| `YarnComponentDTO` (new, pricing_dto.py) | `{material_label: str, ratio: Decimal, carding_stage: str ("" = Không chải thô), pass_no: int\|None (output), nsm_carding: Decimal\|None, reference_nsm: Decimal\|None (output)}` |
| `SaveYarnNsmRequest`, `CorrectYarnNsmRequest`, `CreateNsmRevisionRequest` | `blend_ratios` → `components: list[YarnComponentDTO]`; `nsm` = only non-carding stages |
| `NsmSuggestionResponse` | `blend_ratios` → `components: list[YarnComponentDTO]` |
| `YarnDetailResponse` | `blend_slots` → `carding_stages: list[str]`; add `components: list[YarnComponentDTO]` (prefilled per BR-57/4.12.1 when the yarn has none), `material_options: list[str]` (material_tech_key of the loss group components, empty = free text), `stages` = non-carding stages only |
| `PricingResultResponse` | add `components` (with pass_no); `StageCostDTO` add `material_label: str = ""`, `pass_no: int\|None` |
| `PackagingRowDTO` | add `is_default: bool = False` |
| `FactoryDTO` | `blend_slots` → `carding_stages`; add `default_packaging_code: str\|None` |
| `StageRowDTO` | add `is_carding: bool`, `max_passes: int\|None`; `blend_slot` values: "Không" / "Tỷ lệ của lượt" / "Tỷ lệ dây chuyền <X>" |
| `PriceLineRowDTO` | ratio columns (pe, other_c31..c33, viscose_other, cotton) → `components_text: str` |
| Stored data | repositories convert old stored data (S4 stages C3.1..C3.3 → C3; yarn `blend_ratios` + carding nsm → `components`; packaging without `is_default`) - never delete data |

### 6.2 Checkboxes
- [x] Step 0 UI concept recorded
- [x] Backend - ALL CHECKS PASSED
- [x] UI build - ALL CHECKS PASSED
- [x] Gateway / navigation check
- [x] Document updated
- [x] Verify (Step 5)
- [x] Report

### 6.3 Fix log (2026-09-28)
- Page render test master_data_page.py lỗi (FactoryDTO.blend_slots không còn) -> DTO đổi sang carding_stages -> UI dùng
  carding_stages + cột mới -> ALL CHECKS PASSED (271 passed).
- Nhập thử file thật (thư mục tạm): S4 tính được 966 mã (trước 795), khớp giá cũ 607 / lệch 354 (56 lệch do nhóm được gộp lấy
  C3 thấp nhất); S1 1061 mã, khớp 1015 / lệch 46; S4-2017 vẫn 19.777,8356. Đóng gói mặc định S4 = Type 3 điền sẵn đúng trên
  trình duyệt; chọn 2 loại mặc định báo đúng thông báo BR-60.

## 7. Chuyển sang app mới 2026-09-29 (BR-61..BR-63, UC-42, AC-62..AC-69)
Tóm tắt: app mới (`D:\Vibe Coding\Spinning\TC-vibe-coding`) có khung sườn giống hệt app cũ (`D:\Vibe Coding\TC-vibe-coding`,
đã so sánh `backend/core`, `backend/shared`, `frontend/core`, `tests`, `scripts`, `requirements.txt`: không khác). Cách làm:
scaffold `yarn_costing`, thay nội dung bằng code đã kiểm của app cũ (giữ nguyên cách tính và cách lưu để đọc được dữ liệu chép
sang - BR-61), rồi thêm các điểm mới. Mục 1-6 ở trên là lịch sử của app cũ, vẫn đúng cho phần giữ nguyên.
Vai trò: làm tuần tự bởi lead (backend → UI), không chạy sub-agent song song, vì phần lớn là chuyển code đã có và các thay đổi
nhỏ, chạm cùng các file.

UI concept thay đổi (1 dòng / màn hình): mọi màn có khối "📂 Menu theo nhóm người dùng" (mở rộng / thu gọn, 5 nhóm cũng mở
rộng / thu gọn); menu trái sắp theo nhóm người dùng, nhãn [Chung] / [Sales] / [Xưởng] / [SO]; Screen 2 hiện lý do khoá nút
"Gửi yêu cầu" (BR-63); Screen 5 thẻ Đóng gói: nút "Lưu đóng gói", hộp xác nhận theo BR-62.

### 7.1 Contract changes (binding)
| Item | Change |
|---|---|
| `SavePackagingTypesRequest` | add `preview: bool = False`; `effective_date: date \| None`, `reason: str = ""` (chỉ bắt buộc khi có tính lại) |
| `RecalcResultResponse` | add `will_recalculate: bool = False`, `confirm_text: str = ""` (preview của UC-05) |
| UC-42 `check_request_submit` (new) | `CheckRequestSubmitRequest{authenticated: bool, group_code: str\|None, factory_code: FactoryCode\|None}` (request_dto.py) → `RequestSubmitCheckResponse{allowed: bool, reasons: list[str]}` |
| BR-61 | `repositories/safe_json_repository.py::SafeJsonRepository` (mọi repository kế thừa) → `DataFileError` với thông báo BR-61 (`business/master_business.py::MasterBusiness.data_file_message`) |
| BR-62 | `business/master_business.py::MasterBusiness.packaging_recalc_codes`, `packaging_confirm_text` |
| BR-63 | `business/request_business.py::RequestBusiness.submit_block_reasons` |
| Manifest | group "Tính Giá Sợi"; thứ tự trang theo nhóm người dùng; tiêu đề có nhãn nhóm |
| Menu theo nhóm | `frontend/features/yarn_costing/components/group_menu.py::render_group_menu` (gọi đầu mỗi trang) |

### 7.2 Traceability (mới)
| Spec item | Description (VI) | Code element | Test | Status |
|---|---|---|---|---|
| 5.6 / BR-61 | Đọc dữ liệu chép từ app cũ, file hỏng báo rõ | repositories/safe_json_repository.py, repositories/legacy_conversion.py | tests/test_migration.py | ✅ |
| BR-62 | Tính lại khi lưu đóng gói + nội dung hộp xác nhận | business/master_business.py, services/save_packaging_types_service.py | tests/test_rules.py, tests/test_master_services.py | ✅ |
| BR-63 / UC-42 | Lý do khoá nút Gửi yêu cầu | business/request_business.py, services/check_request_submit_service.py | tests/test_rules.py, tests/test_request_submit.py | ✅ |
| AC-62..AC-64 | Dữ liệu chép sang giữ nguyên, C3.x chuyển đúng, file hỏng | như trên | tests/test_migration.py + kiểm tra với bản chép dữ liệu thật | ✅ |
| AC-65..AC-67 | Hộp xác nhận đóng gói | như BR-62 | tests/test_master_services.py | ✅ |
| AC-68, AC-69 | Lý do khoá nút | như BR-63 | tests/test_request_submit.py | ✅ |
| Menu theo nhóm | Khối mở rộng / thu gọn + menu trái theo nhóm | components/group_menu.py, manifest.py | page render test | ✅ |

### 7.3 Checkboxes
- [x] Step 0 UI concept recorded
- [x] Scaffold
- [x] Chuyển code app cũ
- [x] Backend (BR-61..BR-63, UC-42) - ALL CHECKS PASSED
- [x] UI design (mục 7 của ui-design)
- [x] UI build - ALL CHECKS PASSED
- [x] Gateway registration check
- [x] Navigation check
- [x] Scaffold ping removed
- [x] Document updated
- [x] Verify (Step 5)
- [x] Report

### 7.4 Fix log (2026-09-29)
- Nhập sai chuỗi `data\yarn_costing` qua heredoc -> `\y` thành escape lỗi, import constants hỏng -> sửa thành hai dấu `\` trong mã nguồn
  -> import OK, ALL CHECKS PASSED.
- BR-61: file `yarns.json` hỏng làm cả dữ liệu tham chiếu (UC-38) lỗi, màn dữ liệu nền không mở được -> UC-38 đọc danh sách
  nhóm sợi từ mã sợi -> bắt `DataFileError` ở phần này, trả `data_warnings` -> test_br61_unreadable_data_file_names_the_file đạt.
- Kiểm tra trên trình duyệt: ô chọn nhóm / tên nhận giá trị nhưng ô mã nội bộ bị xoá khi trang tải lại -> thao tác tự động quá
  nhanh, không phải lỗi app -> nhập lại mã rồi bấm Xác nhận -> "Đang thao tác: Phòng SO - Phòng SO."
- Kiểm tra với bản chép dữ liệu thật (thư mục tạm): 3.435 mã, 4.066 dòng giá không đổi số tiền, S4-2017 = 19.777,8356; hộp
  xác nhận đóng gói "Giá các mã không thay đổi."; lý do khoá nút Gửi yêu cầu hiện đúng; logs/app.log không có ERROR.
- 2026-09-29 | Màn Tiêu hao: tiêu hao chỉ hiện / nhập được 2 chữ số thập phân (theo %), không nhập đúng được các mức như
  0,5% / 0,395% | Ô nhập và bảng tiêu hao làm tròn số hiện ra 2 chữ số (hàm `pct`), ô nhập bước 0,01, định dạng "%.2f" ->
  0,395% hiện 0,40% và lưu lại sẽ đổi số thật | Ô nhập tiêu hao / tỷ lệ: bước 0,0001, định dạng "%.4f", hiện đúng số đang lưu
  (`components/display.py::pct_exact`); bảng tiêu hao chỉ xem của màn Tiêu hao hiện 4 chữ số ("%.4f%%") | test_new_app.py ::
  test_losses_below_one_hundredth_percent_are_kept_exactly | ALL CHECKS PASSED, APP IS HEALTHY, trình duyệt: nhóm S4
  "P/C (65/35) (RE-PE 65%)" hiện R = 0,3950%, DCM / S = 0,5000%

## 8. Dây chuyền tương đương 2026-09-29 (BR-64, BR-65, UC-43, AC-70..AC-77)
Tóm tắt: khi nguyên liệu chạy dây chuyền chải thô X mà nhóm tiêu hao chỉ khai báo ở dây chuyền tương đương Y (S4 C2 ↔ C3, S1
C1 ↔ C2), app dùng số của Y và ghi chú; nút Phòng SO "Tính lại các mã chưa tính được". Step 0 bỏ qua (người dùng đã trả lời
câu hỏi giao diện trong cùng cuộc trò chuyện; hai thay đổi nằm trong cách giao diện đã chốt). Làm tuần tự bởi lead.

### 8.1 Contract changes (binding)
| Item | Change |
|---|---|
| UC-43 `recalculate_not_priced` | `RecalculateNotPricedRequest{actor, factory_code, effective_date, reason}` (master_dto.py) → `RecalcResultResponse` |
| `StageCostDTO` | add `loss_note: str = ""` |
| `StageCostDetail` (stored) | add `loss_source_stage: str = ""` (default → dữ liệu cũ đọc được) |
| `PriceEvent` | add `TINH_LAI_CHUA_TINH = "Tính lại mã chưa tính được"` |
| Export 5.4 | sheet `Chi tiet cong doan` thêm cột cuối "Ghi chú tiêu hao" |

### 8.2 Traceability
| Spec item | Code element | Test | Status |
|---|---|---|---|
| BR-64, 4.3 `equivalent_carding` | costing_business.py `equivalent_line`, `declared_carding_loss`, `pass_loss_with_source`; constants `EQUIVALENT_CARDING` | test_new_app.py :: test_br64_equivalent_lines, test_br64_price_with_loss_declared_on_c2_equals_c3 | ✅ |
| BR-16 câu mới | costing_business.py `_carding_reasons` | test_br16_message_names_both_lines; test_rules.py :: test_br58_pass_loss_and_br15_carding_checks | ✅ |
| 4.14 `loss_source_stage`, `loss_note` | models/yarn.py `StageCostDetail`; dto_builders; columns.py `stage_cost_rows` | test_br64_price_with_loss_declared_on_c2_equals_c3 | ✅ |
| 5.4 cột Ghi chú tiêu hao | builders/file_builders.py | test_export_has_loss_note_column | ✅ |
| BR-65, UC-43, 4.15/4.16 event | recalc_business.py, recalculate_not_priced_service.py, price_line_business.py, controller | test_uc43_recalculate_not_priced | ✅ |
| Screen 5 nút UC-43 | master_data_page.py `_not_priced_block` | page render test | ✅ |
| AC-70..AC-77 | như trên | như trên (AC-74: không đổi giá các mã đã có giá - test_calculation / test_carding_services giữ nguyên kết quả) | ✅ |

### 8.3 Checkboxes
- [x] Step 0 UI concept recorded (bổ sung vào khối "Giao diện đã chốt")
- [x] Backend - ALL CHECKS PASSED
- [x] UI build - ALL CHECKS PASSED
- [x] Gateway registration check
- [x] Navigation check
- [x] Document updated
- [x] Verify (Step 5)
- [x] Report

### 8.4 Fix log
- test_rules.py :: test_br58_pass_loss_and_br15_carding_checks hỏng (AC-54 mong đợi "chưa khai báo tiêu hao ở C2") -> AC-54 viết
  trước BR-64, BR-64 chốt sau cho dùng số của C3 -> cập nhật test theo BR-64 (dùng 3%, có ghi chú) + kiểm tra câu mới khi cả hai
  trống (AC-73), ghi Giả định (triển khai) ở mục 10 -> 170 passed.
- Thêm `TINH_LAI_CHUA_TINH` nhầm vào `YarnOrigin` (cùng giá trị "Nhập từ file" ở hai enum) -> AttributeError -> chuyển sang
  `PriceEvent` -> ALL CHECKS PASSED.
- Dòng giá mới của UC-43 ghi lịch sử "Tính lần đầu" thay vì "Tính lại mã chưa tính được" -> `_set_line` chỉ giữ event của nhập
  file -> giữ cả event UC-43 -> test_uc43_recalculate_not_priced đạt.

## 9. Khai báo thành phần sợi pha bằng file 2026-09-29 (UC-44, UC-45, BR-66..BR-69, AC-78..AC-85)
Tóm tắt: Screen 6 thêm loại tải "Khai báo thành phần sợi pha": tải mẫu (UC-44), kiểm tra / lưu file (UC-45) chuyển nhóm tiêu hao
thành nhóm sợi pha, tiêu hao tính theo thành phần, đổi tên thành phần của mã, tính lại mã bị ảnh hưởng. Step 0 bỏ qua (người dùng
đã trả lời câu hỏi giao diện trong cùng cuộc trò chuyện; khối mới theo đúng cách đã chốt). Làm tuần tự bởi lead.

### 9.1 Contract (binding)
| Method | Request (import_dto.py) | Response | UC |
|---|---|---|---|
| `download_component_template` | `DownloadComponentTemplateRequest{factory_code}` | `FileDownloadDTO` | UC-44 |
| `import_component_file` | `ImportComponentFileRequest{actor, factory_code, file, effective_date, reason, commit}` | `ComponentImportResponse{message, committed, valid_count, created_count, rejected_count, affected_count, unmatched_count, groups: list[ComponentGroupResultDTO], rejected_rows, unmatched: list[UnmatchedYarnDTO], stage_codes, import_id, batch_id, result_file}` | UC-45 |
`ImportMode` thêm `THANH_PHAN = "Khai báo thành phần sợi pha"`.

### 9.2 Traceability
| Spec item | Code element | Test | Status |
|---|---|---|---|
| 5.7 đọc file (sheet, cột, bỏ qua dòng trống, cột thừa) | builders/component_file_builder.py :: ComponentFileReaderBuilder | test_component_import.py :: test_draft_file_with_extra_columns, test_file_without_the_sheet | ✅ |
| 5.7 file mẫu (3 sheet, danh sách chọn) | ComponentTemplateBuilder; download_component_template_service.py | test_template_lists_groups | ✅ |
| BR-66 | component_import_business.py :: check_row, plan | test_row_checks | ✅ |
| BR-67 | declared_group, plan (BR-26 recompute giới hạn nhóm bị ảnh hưởng) | test_declare_components_relabels_and_recalculates, test_row_checks | ✅ |
| BR-68 | relabel_yarn; service (Chưa tính được + lý do, giữ giá) | test_declare_components_relabels_and_recalculates, test_unmatched_component_makes_the_yarn_waiting | ✅ |
| BR-69 | plan (khoá → loại dòng), access.verify UC-45, permissions.py | test_permissions_and_locked_groups | ✅ |
| UC-45 lưu: batch "Sửa tiêu hao", lần nhập loại mới, nhật ký, file kết quả | import_component_file_service.py | test_declare_components_relabels_and_recalculates | ✅ |
| Screen 6 khối mới | components/component_import.py; pages/excel_import_page.py | page render test + kiểm tra trình duyệt | ✅ |
| AC-78..AC-85 | như trên | như trên | ✅ |

### 9.3 Checkboxes
- [x] Step 0 UI concept recorded (bổ sung vào khối "Giao diện đã chốt")
- [x] Backend - ALL CHECKS PASSED
- [x] UI build - ALL CHECKS PASSED
- [x] Gateway registration check (45 phương thức = UC-01..UC-45)
- [x] Navigation check
- [x] Document updated
- [x] Verify (Step 5)
- [x] Report

### 9.4 Fix log
- test_component_import :: components_text mong đợi "60%" nhưng app hiện "60,00%" (BR-23: % 2 chữ số) -> sửa giá trị mong đợi của test
  mới theo BR-23 -> 7 passed.
- Kế hoạch nhập ban đầu tính lại mọi nhóm sợi pha của xưởng (recompute_secondaries trả cả nhóm không liên quan có tiêu hao lưu khác
  số tính lại) -> giới hạn trong các nhóm bị ảnh hưởng (BR-24) -> các nhóm khác không đổi.
- Thử trên bản chép dữ liệu thật với bản nháp S1: 255 nhóm hợp lệ, 245 dòng bị loại (230 vì thiếu nhóm thành phần, chủ yếu PE), 354
  mã bị ảnh hưởng, 95 mã không ghép được (thành phần tỷ lệ 0% còn NSM trong dữ liệu cũ S1), 95 mã đổi giá (trung bình −0,21%, từ
  −2,91% đến −0,01%); dữ liệu thật không đổi.
