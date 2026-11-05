# Kế hoạch triển khai: Năng suất xưởng may (`sewing_productivity`)

## 1. Tóm tắt
App gồm 9 màn hình, chia 2 nhóm menu. Người cập nhật tải file `Data sewing`, app làm sạch và lưu dữ liệu, rồi mọi người xem báo cáo tuần, ngày, tháng, MO theo chuyền, đổi mã hàng và biểu đồ theo khoảng thời gian. Mục tiêu, ngưỡng và danh mục do người cập nhật sửa. Tài liệu nghiệp vụ là `docs/business/sewing_productivity.md`.

### Giao diện theo màn hình
| Màn hình | Slug | Lớp trang | Giao diện |
|---|---|---|---|
| Tổng quan | (trang đầu) | `OverviewPage` | Bộ lọc, bảng chỉ số 4 xưởng, nút Excel, 5 biểu đồ; không có ô số liệu |
| Chi tiết chuyền | `line-detail` | `LineDetailPage` | Bộ lọc, bảng chuyền theo ngày, bảng xưởng theo ngày, nút Excel |
| Báo cáo ngày | `daily` | `DailyReportPage` | Chọn ngày, bảng xưởng, chọn xưởng, bảng chuyền, nút Excel |
| Báo cáo tháng | `monthly` | `MonthlyReportPage` | Bộ lọc, mỗi xưởng một bảng, nút Excel |
| MO theo chuyền | `line-mo` | `LineMoPage` | Bộ lọc, 5 thẻ, nút Excel |
| Đổi mã hàng | `changeover` | `ChangeoverPage` | Bộ lọc, 4 thẻ, nút Excel |
| Cập nhật dữ liệu | `data-update` | `DataUpdatePage` | Tải file 2 bước, form đổi mã hàng tuần, chọn dòng để xoá, lịch sử |
| Mục tiêu và ngưỡng | `goals` | `GoalsPage` | Bảng đang áp dụng, form, lịch sử |
| Danh mục | `catalogs` | `CatalogsPage` | 4 thẻ, mỗi thẻ một bảng sửa trực tiếp |

## 2. Lệnh tạo chức năng
```
.venv/Scripts/python.exe -X utf8 scripts/new_feature.py sewing_productivity --title "Năng suất xưởng may" --developer thynguyen-lab --prefix thynguyen --description "Theo dõi và phân tích năng suất các xưởng may theo khoảng thời gian bất kỳ." --icon "🧵" --group "Sản xuất" --owner "Nhóm PI - SO"
```

## 3. Hợp đồng điều khiển (`SewingProductivityController`)
File DTO nằm trong `backend/features/sewing_productivity/dto/`. Mỗi nghiệp vụ là một phương thức, một dịch vụ. `@cached_query` cho các nghiệp vụ chỉ đọc không phụ thuộc người dùng.

| UC | Phương thức | Request | Response | DTO file | Cached |
|---|---|---|---|---|---|
| UC-01 | `check_upload` | `CheckUploadRequest(file: UploadedFileDTO)` | `UploadCheckResponse(read_rows, valid_rows, skipped_rows, from_date, to_date, stored_rows_in_range, skipped: list[SkippedRowDTO], warnings: list[UploadWarningDTO], can_save)` | `upload_dto.py` | Không |
| UC-02 | `save_upload` | `SaveUploadRequest(file: UploadedFileDTO)` | `SaveUploadResponse(saved_rows, to_date, message)` | `upload_dto.py` | Không |
| UC-03 | `list_upload_logs` | `EmptyRequest` | `UploadLogListResponse(items: list[UploadLogDTO])` | `upload_dto.py` | Không |
| UC-04 | `get_overview` | `OverviewRequest(from_date, to_date, factories, customer_groups, product_groups)` | `OverviewResponse(metrics: list[OverviewMetricDTO], note, has_data)` | `overview_dto.py` | Có |
| UC-05 | `get_charts` | `ChartsRequest(from_date, to_date, factories, customer_groups, product_groups, ranking_metric)` | `ChartsResponse(efficiency_a, efficiency_b, mo8h, output_vs_target, top_lines, bottom_lines, not_applicable_message)` | `overview_dto.py` | Có |
| UC-06 | `get_line_detail` | `LineDetailRequest(from_date, to_date, factory, lines, customer_groups, product_groups)` | `LineDetailResponse(rows: list[LineDetailRowDTO], factory_days: list[FactoryDayDTO], note, has_data)` | `line_detail_dto.py` | Có |
| UC-07 | `get_daily_report` | `DailyReportRequest(report_date, factory)` | `DailyReportResponse(metrics, lines: list[DailyLineRowDTO], has_data)` | `daily_dto.py` | Có |
| UC-08 | `get_monthly_report` | `MonthlyReportRequest(from_date, to_date, factories)` | `MonthlyReportResponse(factories: list[MonthlyFactoryDTO], has_data)` | `monthly_dto.py` | Có |
| UC-09 | `get_line_mo` | `LineMoRequest(from_date, to_date, factory, lines)` | `LineMoResponse(dates, tables: list[LineMoTableDTO], has_data)` | `line_mo_dto.py` | Có |
| UC-10 | `get_changeover` | `ChangeoverRequest(from_date, to_date, factories, lines)` | `ChangeoverResponse(by_factory, by_month, by_line, details, has_data)` | `changeover_dto.py` | Có |
| UC-11 | `export_weekly_report` | `ExportWeeklyRequest(from_date, to_date, factories, customer_groups, product_groups)` | `FileDownloadDTO` | `export_dto.py` | Có |
| UC-12 | `export_daily_report` | `ExportDailyRequest(report_date)` | `FileDownloadDTO` | `export_dto.py` | Có |
| UC-13 | `export_monthly_report` | `MonthlyReportRequest` | `FileDownloadDTO` | `monthly_dto.py` | Có |
| UC-14 | `export_line_mo` | `LineMoRequest` | `FileDownloadDTO` | `line_mo_dto.py` | Có |
| UC-15 | `export_changeover` | `ChangeoverRequest` | `FileDownloadDTO` | `changeover_dto.py` | Có |
| UC-16 | `list_goals` | `EmptyRequest` | `GoalListResponse(current: list[GoalDTO], history: list[GoalDTO])` | `goal_dto.py` | Không |
| UC-17 | `save_goal` | `SaveGoalRequest(factory, effective_from, efficiency_target, mo8h_target, efficiency_threshold, mo8h_threshold)` | `SaveGoalResponse(message)` | `goal_dto.py` | Không |
| UC-18 | `list_weekly_changeovers` | `EmptyRequest` | `WeeklyChangeoverListResponse(items: list[WeeklyChangeoverDTO])` | `weekly_changeover_dto.py` | Không |
| UC-19 | `save_weekly_changeovers` | `SaveWeeklyChangeoversRequest(from_date, to_date, counts: dict[str, int \| None])` | `SaveWeeklyChangeoversResponse(message)` | `weekly_changeover_dto.py` | Không |
| UC-20 | `delete_weekly_changeover` | `DeleteWeeklyChangeoverRequest(id)` | `DeleteWeeklyChangeoverResponse(message)` | `weekly_changeover_dto.py` | Không |
| UC-21 | `get_catalogs` | `EmptyRequest` | `CatalogsResponse(product_groups, customer_groups, line_mappings, style_products, unclassified_products, customer_names, styles_without_product)` | `catalog_dto.py` | Không |
| UC-22 | `save_product_groups` | `SaveProductGroupsRequest(rows)` | `SaveCatalogResponse(message)` | `catalog_dto.py` | Không |
| UC-23 | `save_customer_groups` | `SaveCustomerGroupsRequest(rows)` | `SaveCatalogResponse(message)` | `catalog_dto.py` | Không |
| UC-24 | `save_line_mappings` | `SaveLineMappingsRequest(rows)` | `SaveCatalogResponse(message)` | `catalog_dto.py` | Không |
| UC-25 | `save_style_products` | `SaveStyleProductsRequest(rows)` | `SaveCatalogResponse(message)` | `catalog_dto.py` | Không |
| UC-26 | `get_filter_options` | `EmptyRequest` | `FilterOptionsResponse(factories, lines_by_factory, customer_groups, product_groups, latest_date, last_upload_at, default_week_from, default_week_to, default_month_from, has_data)` | `filter_dto.py` | Có |

## 4. Quyết định kỹ thuật
- **Dữ liệu gốc và dữ liệu làm sạch:** chỉ lưu giá trị từ file. Chuyền chuẩn, nhóm khách hàng, tên và nhóm sản phẩm được tính khi đọc, nên danh mục đổi là báo cáo đổi ngay.
- **Mã dòng cố định:** mã của một dòng được tính từ các cột nhận diện ở mục 4.1 của tài liệu, kể cả thứ tự xuất hiện. Tải lại file chỉ ghi các dòng đổi, dòng không còn trong khoảng được đánh dấu xoá.
- **Vai trò:** manifest khai báo `roles=(("UPDATER", "Người cập nhật dữ liệu"),)`.
- **Tên viết tắt:** tên GitHub `thynguyen-lab`, tên viết tắt địa chỉ `thynguyen`.

## 5. Bảng theo dõi yêu cầu
| Spec item | Description (VI) | Code element | Test | Status |
|---|---|---|---|---|
| UC-01 | Kiểm tra file dữ liệu | `check_upload` -> `CheckUploadService` | `test_upload_services.py::test_ac07_check_saves_nothing_and_reports_the_period` | ✅ |
| UC-02 | Lưu dữ liệu từ file | `save_upload` -> `SaveUploadService` | `test_reports.py::test_ac23_no_target_at_all_efficiency_a_is_dash_and_b_stays` | ✅ |
| UC-03 | Xem lịch sử tải file | `list_upload_logs` -> `ListUploadLogsService` | `test_upload_services.py::test_ac12_user_without_role_cannot_save_and_data_stays` | ✅ |
| UC-04 | Xem tổng quan xưởng | `get_overview` -> `GetOverviewService` | `test_settings_services.py::test_ac47_same_period_replaces_and_delete_shows_dash` | ✅ |
| UC-05 | Xem biểu đồ | `get_charts` -> `GetChartsService` | `test_reports.py::test_ac41_charts_and_ranking` | ✅ |
| UC-06 | Xem chi tiết chuyền | `get_line_detail` -> `GetLineDetailService` | `test_reports.py::test_ac14_ac25_line_detail_rows` | ✅ |
| UC-07 | Xem báo cáo ngày | `get_daily_report` -> `GetDailyReportService` | `test_reports.py::test_ac37_ac38_daily_report` | ✅ |
| UC-08 | Xem báo cáo tháng | `get_monthly_report` -> `GetMonthlyReportService` | `test_reports.py::test_ac39_monthly_report_with_total_row` | ✅ |
| UC-09 | Xem MO theo chuyền | `get_line_mo` -> `GetLineMoService` | `test_reports.py::test_ac40_line_mo_tables` | ✅ |
| UC-10 | Xem đổi mã hàng | `get_changeover` -> `GetChangeoverService` | `test_reports.py::test_changeover_service_uses_the_whole_stored_history` | ✅ |
| UC-11 | Tải Excel báo cáo tuần | `export_weekly_report` -> `ExportWeeklyReportService` | `test_reports.py::test_ac43_weekly_excel_file` | ✅ |
| UC-12 | Tải Excel báo cáo ngày | `export_daily_report` -> `ExportDailyReportService` | `test_reports.py::test_ac44_daily_monthly_mo_changeover_files_have_the_right_sheets` | ✅ |
| UC-13 | Tải Excel báo cáo tháng | `export_monthly_report` -> `ExportMonthlyReportService` | `test_reports.py::test_ac44_daily_monthly_mo_changeover_files_have_the_right_sheets` | ✅ |
| UC-14 | Tải Excel MO theo chuyền | `export_line_mo` -> `ExportLineMoService` | `test_reports.py::test_ac44_daily_monthly_mo_changeover_files_have_the_right_sheets` | ✅ |
| UC-15 | Tải Excel đổi mã hàng | `export_changeover` -> `ExportChangeoverService` | `test_reports.py::test_ac44_daily_monthly_mo_changeover_files_have_the_right_sheets` | ✅ |
| UC-16 | Xem mục tiêu và ngưỡng | `list_goals` -> `ListGoalsService` | `test_settings_services.py::test_ac50_initial_goals_and_current_level` | ✅ |
| UC-17 | Lưu mục tiêu và ngưỡng | `save_goal` -> `SaveGoalService` | `test_reports.py::test_ac27_period_compares_with_level_of_the_last_day` | ✅ |
| UC-18 | Xem đổi mã hàng tuần đã nhập | `list_weekly_changeovers` -> `ListWeeklyChangeoversService` | `test_settings_services.py::test_ac47_same_period_replaces_and_delete_shows_dash` | ✅ |
| UC-19 | Lưu đổi mã hàng tuần | `save_weekly_changeovers` -> `SaveWeeklyChangeoversService` | `test_reports.py::test_ac31_weekly_number_only_on_the_exact_period` | ✅ |
| UC-20 | Xoá số đổi mã hàng tuần | `delete_weekly_changeover` -> `DeleteWeeklyChangeoverService` | `test_settings_services.py::test_ac47_same_period_replaces_and_delete_shows_dash` | ✅ |
| UC-21 | Xem danh mục | `get_catalogs` -> `GetCatalogsService` | `test_settings_services.py::test_ac17_style_catalog_fills_rows_and_leaves_the_missing_list` | ✅ |
| UC-22 | Lưu nhóm sản phẩm | `save_product_groups` -> `SaveProductGroupsService` | `test_settings_services.py::test_user_edit_survives_later_reads` | ✅ |
| UC-23 | Lưu nhóm khách hàng | `save_customer_groups` -> `SaveCustomerGroupsService` | `test_settings_services.py::test_ac19_saving_a_customer_group_changes_the_filter_and_customer_list` | ✅ |
| UC-24 | Lưu bảng số chuyền Fac 1 | `save_line_mappings` -> `SaveLineMappingsService` | `test_settings_services.py::test_ac49_line_table_applies_to_old_fac1_data` | ✅ |
| UC-25 | Lưu tên sản phẩm theo style | `save_style_products` -> `SaveStyleProductsService` | `test_settings_services.py::test_ac17_style_catalog_fills_rows_and_leaves_the_missing_list` | ✅ |
| UC-26 | Lấy lựa chọn bộ lọc và thời gian mặc định | `get_filter_options` -> `GetFilterOptionsService` | `test_reports.py::test_ac45_no_data_at_all` | ✅ |
| BR-01 | File phải là .xlsx, không quá 50 MB, mỗi sheet không quá 200.000 dòng | `exceptions.py::UploadFileError` | `test_business_rules.py::test_br01_rule` | ✅ |
| BR-02 | File phải có đủ 3 sheet `Production data`, `Target system`, `Worker` | `business/upload_business.py::UploadBusiness.ensure_sheets` | `test_business_rules.py::test_br02_rule` | ✅ |
| BR-03 | Mỗi sheet phải có đủ cột bắt buộc ở mục 5.1 | `builders/upload_read_builders.py::RawWorkbookBuilder._missing` | `test_business_rules.py::test_br03_rule` | ✅ |
| BR-04 | `Production data` phải có ít nhất 1 dòng hợp lệ và có ít nhất một ô mụ | `builders/upload_read_builders.py::RawWorkbookBuilder._missing` | `test_business_rules.py::test_br04_rule` | ✅ |
| BR-05 | Dòng sản lượng hợp lệ khi có ngày đúng định dạng, xưởng, khách hàng, s | `business/upload_business.py::UploadBusiness.parse` | `test_business_rules.py::test_br05_rule` | ✅ |
| BR-06 | Xưởng được đổi tên: `SVL-Factory 2` = Fac 1, `SHCM-Factory 2` = Fac 2, | `business/upload_business.py::UploadBusiness.parse` | `test_business_rules.py::test_br06_rule` | ✅ |
| BR-07 | Khi lưu, mỗi sheet thay dữ liệu đang có trong khoảng từ ngày đầu đến n | `business/upload_business.py::UploadBusiness.replacement_writes` | `test_upload_services.py::test_br07_deleted_by_records_the_user` | ✅ |
| BR-08 | Cảnh báo không chặn việc lưu, gồm: số dòng thiếu SMV hoặc thiếu mục ti | `business/catalog_business.py::CatalogBusiness.warnings` | `test_upload_services.py::test_ac11_newest_day_without_smv_workers_and_targets_warns_and_saves` | ✅ |
| BR-09 | Chỉ người có vai trò `UPDATER` hoặc quản trị viên được tải file, sửa m | `business/access_rules.py::UpdaterRoleRule` | `test_business_rules.py::test_br09_rule` | ✅ |
| BR-10 | Tên chuyền được chuẩn hoá thành `LINE <số>`, không phân biệt hoa thườn | `business/cleaning_business.py::CleaningBusiness.standard_line` | `test_business_rules.py::test_br10_standard_line` | ✅ |
| BR-11 | Dữ liệu Fac 1 có ngày trước 07/07/2026 được đổi tên chuyền theo bảng s | `business/cleaning_business.py::CleaningBusiness.current_line` | `test_business_rules.py::test_ac15_br11_fac1_line_mapping_only_before_cutover` | ✅ |
| BR-12 | Mã đơn gốc = mã đơn bỏ khoảng trắng hai đầu và bỏ phần số sau dấu chấm | `business/cleaning_business.py::base_po_number` | `test_business_rules.py::test_br12_base_order` | ✅ |
| BR-13 | Tên sản phẩm trống được điền theo thứ tự: bảng tên sản phẩm theo style | `business/catalog_business.py::CatalogBusiness.styles_without_name` | `test_business_rules.py::test_ac16_br13_empty_name_is_filled_in_order` | ✅ |
| BR-14 | Nhóm sản phẩm lấy theo danh mục (không phân biệt hoa thường). Tên khôn | `business/catalog_business.py::CatalogBusiness.unclassified_names` | `test_business_rules.py::test_br14_product_group` | ✅ |
| BR-15 | Nhóm khách hàng lấy theo danh mục trước. Nếu không có: tên bắt đầu bằn | `business/catalog_business.py::CatalogBusiness.customer_names` | `test_business_rules.py::test_ac19_br15_customer_group` | ✅ |
| BR-16 | Dòng `Target system` có dạng `<xưởng> - Sewing Line <số>`: SFVL = Fac  | `business/upload_business.py::UploadBusiness.parse` | `test_business_rules.py::test_br16_rule` | ✅ |
| BR-17 | Tiền CM = sản lượng × giá CM. Không làm tròn khi tính | `business/cleaning_business.py::CleaningBusiness.cm_earning` | `test_business_rules.py::test_br17_cm_earning_is_not_rounded` | ✅ |
| BR-18 | Hiệu suất A = tổng sản lượng / tổng mục tiêu A, chỉ tính các ngày và c | `business/line_report_business.py::LineReportBusiness._days_by_line` | `test_business_rules.py::test_br18_efficiency_a_uses_the_same_scope_on_both_sides` | ✅ |
| BR-19 | Hiệu suất B = tổng sản lượng / tổng mục tiêu B, bỏ các dòng thiếu mục  | `business/line_report_business.py::LineReportBusiness.factory_total_row` | `test_business_rules.py::test_br19_efficiency_b_leaves_out_rows_without_target_b` | ✅ |
| BR-20 | Giờ làm chuyền trong ngày = trung bình giờ làm các dòng của chuyền. Gi | `business/line_report_business.py::LineReportBusiness.factory_total_row` | `test_business_rules.py::test_br20_hours_are_averages_of_averages` | ✅ |
| BR-21 | Số người chuyền trong ngày = trung bình số người các dòng của chuyền | `business/line_report_business.py::LineReportBusiness.day_rows` | `test_business_rules.py::test_br21_people_of_a_line_is_an_average` | ✅ |
| BR-22 | MO 8h của chuyền trong ngày = tiền CM của chuyền / số người × 8 / giờ  | `business/line_report_business.py::LineReportBusiness.line_rows` | `test_business_rules.py::test_br22_line_mo8h` | ✅ |
| BR-23 | MO của xưởng trong ngày = tiền CM / số thợ. MO 8h của xưởng trong ngày | `business/line_report_business.py::LineReportBusiness.factory_total_row` | `test_business_rules.py::test_br23_factory_mo` | ✅ |
| BR-24 | Giá CM trung bình = tổng tiền CM / tổng sản lượng | `business/productivity_business.py::ProductivityBusiness.average_cm_price` | `test_business_rules.py::test_ac51_br24_average_price` | ✅ |
| BR-25 | Tỷ lệ đúng sở trường = 1 − tổng mục tiêu A dòng trái sở trường / tổng  | `business/productivity_business.py::ProductivityBusiness.strength_match` | `test_business_rules.py::test_br25_strength_match` | ✅ |
| BR-26 | Mức mục tiêu, ngưỡng của một ngày là mức có ngày hiệu lực gần nhất, kh | `business/productivity_business.py::ProductivityBusiness.goal_on` | `test_business_rules.py::test_ac27_br26_level_of_a_day` | ✅ |
| BR-27 | % so với mục tiêu = thực tế / mục tiêu. Áp cho hiệu suất A, hiệu suất  | `business/line_report_business.py::LineReportBusiness.line_rows` | `test_business_rules.py::test_br27_percent_of_target` | ✅ |
| BR-28 | Hiệu suất dưới ngưỡng hiệu suất hoặc MO 8h dưới ngưỡng MO 8h thì đánh  | `builders/display.py::is_below` | `test_business_rules.py::test_ac29_ac30_br28_boundaries` | ✅ |
| BR-29 | Khi lọc khách hàng hoặc sản phẩm: sản lượng, tiền CM, giá CM trung bìn | `business/filter_business.py::FilterBusiness.apply_groups` | `test_business_rules.py::test_br29_filter_rows` | ✅ |
| BR-30 | Từ ngày phải không sau đến ngày | `business/filter_business.py::DateRangeRule` | `test_business_rules.py::test_br30_period_order` | ✅ |
| BR-31 | Thời gian mặc định: Screen 1, 2 lấy tuần thứ Bảy đến thứ Sáu đầy đủ gầ | `business/filter_business.py::FilterBusiness.default_week` | `test_business_rules.py::test_ac46_br31_default_week` | ✅ |
| BR-32 | Số lần đổi KPI: với mỗi chuyền, lấy các mã đơn gốc có ngày đầu tiên tr | `business/changeover_business.py::ChangeoverBusiness.usable_rows` | `test_changeover.py::test_br32_order_first_seen_before_the_period_is_not_counted` | ✅ |
| BR-33 | Số ngày làm việc = số ngày xưởng có sản lượng trong khoảng đã chọn | `business/changeover_business.py::ChangeoverBusiness.working_days` | `test_changeover.py::test_ac33_logic_br33_br34_br35_kpi` | ✅ |
| BR-34 | Số chuyền = số chuyền của xưởng có sản lượng trong khoảng đã chọn | `business/changeover_business.py::ChangeoverBusiness.line_count` | `test_changeover.py::test_ac33_logic_br33_br34_br35_kpi` | ✅ |
| BR-35 | KPI đổi mã hàng = số lần đổi KPI / số ngày làm việc / số chuyền | `business/changeover_business.py::ChangeoverBusiness.kpi` | `test_changeover.py::test_ac33_logic_br33_br34_br35_kpi` | ✅ |
| BR-36 | Số lần đổi gồm cả lên lại: với mỗi chuyền và mỗi ngày trong khoảng, mộ | `business/changeover_business.py::ChangeoverBusiness.usable_rows` | `test_changeover.py::test_br36_previous_working_day_is_read_before_the_period` | ✅ |
| BR-37 | Dòng thiếu SMV không được tính vào BR-32 và BR-36 | `business/changeover_business.py::ChangeoverBusiness.usable_rows` | `test_changeover.py::test_br37_rows_without_smv_are_left_out` | ✅ |
| BR-38 | Đổi mã hàng tuần chỉ hiện khi khoảng đã chọn trùng đúng từ ngày và đến | `business/changeover_business.py::ChangeoverBusiness.weekly_count` | `test_changeover.py::test_br38_br41_weekly_number_only_for_the_exact_period` | ✅ |
| BR-39 | Khi nhập đổi mã hàng tuần: từ ngày không sau đến ngày; số lần là số ng | `business/settings_business.py::WeeklyChangeoverRule` | `test_business_rules.py::test_br39_rule` | ✅ |
| BR-40 | Trùng xưởng, từ ngày và đến ngày thì số mới thay số cũ | `business/settings_business.py::SettingsBusiness.to_weekly` | `test_settings_services.py::test_ac47_same_period_replaces_and_delete_shows_dash` | ✅ |
| BR-41 | Đổi mã hàng tuần trên chuyền = đổi mã hàng tuần / số chuyền theo BR-34 | `business/changeover_business.py::ChangeoverBusiness.weekly_per_line` | `test_changeover.py::test_br38_br41_weekly_number_only_for_the_exact_period` | ✅ |
| BR-42 | Báo cáo ngày: mục tiêu sản lượng lấy nguyên tổng `Daily Target (SMV)`; | `business/report_business.py::ReportBusiness.daily_summary` | `test_reports.py::test_ac37_ac38_daily_report` | ✅ |
| BR-43 | Sản lượng trái sở trường của chuyền = tổng sản lượng các dòng `Match l | `business/line_report_business.py::LineReportBusiness.day_rows` | `test_reports.py::test_daily_report_mismatched_output` | ✅ |
| BR-44 | Xếp hạng chuyền theo chỉ số đã chọn trong khoảng đã chọn, mặc định hiệ | `business/report_business.py::ReportBusiness.line_ranking` | `test_reports.py::test_br44_ranking_keeps_ten_lines_and_drops_dashes` | ✅ |
| BR-45 | Khi lưu mục tiêu: có xưởng và ngày hiệu lực; 4 giá trị đều là số > 0 | `business/settings_business.py::GoalInputRule` | `test_business_rules.py::test_br45_rule` | ✅ |
| BR-46 | Trùng xưởng và ngày hiệu lực thì mức mới thay mức cũ | `business/settings_business.py::SettingsBusiness.to_goal` | `test_settings_services.py::test_ac50_initial_goals_and_current_level` | ✅ |
| BR-47 | Danh mục: cột đầu và cột giá trị không được trống; cột đầu không được  | `business/settings_business.py::CatalogRowsRule` | `test_business_rules.py::test_br47_rule` | ✅ |
| BR-48 | Dòng Tổng báo cáo tháng theo xưởng: tổng tiền CM, tổng sản lượng, tổng | `business/line_report_business.py::LineReportBusiness.day_total_row` | `test_reports.py::test_ac40_line_mo_tables` | ✅ |
| BR-49 | File Excel xuất: mỗi báo cáo một sheet; tiêu đề in đậm, có nền màu, lu | `builders/display.py::excel_value` | `test_reports.py::test_ac43_weekly_excel_file` | ✅ |
| BR-50 | Hiển thị: sản lượng và mục tiêu là số nguyên; hiệu suất và các tỷ lệ t | `builders/display.py::excel_value` | `test_reports.py::test_ac43_weekly_excel_file` | ✅ |
| BR-01 | `business/<file>.py::<RuleClass>` | `exceptions.py::UploadFileError` | `test_business_rules.py::test_br01_rule` | ✅ |
| AC-01 | Given người có vai trò `UPDATER`, When tải file `.pdf`, Then thấy thông báo BR-0 | Theo UC và BR liên quan | `test_upload_services.py::test_ac01_pdf_is_refused_with_br01` | ✅ |
| AC-02 | Given file thiếu sheet `Worker`, When kiểm tra, Then thấy "File thiếu sheet: Wor | Theo UC và BR liên quan | `test_upload_services.py::test_ac02_missing_sheet_keeps_stored_data` | ✅ |
| AC-03 | Given sheet `Production data` thiếu cột `Price`, When kiểm tra, Then thấy thông  | Theo UC và BR liên quan | `test_upload_services.py::test_ac03_missing_column_names_sheet_and_column` | ✅ |
| AC-04 | Given file chưa có kết quả công thức, When kiểm tra, Then thấy thông báo BR-04. | Theo UC và BR liên quan | `test_upload_services.py::test_ac04_file_without_formula_results` | ✅ |
| AC-05 | Given file có một dòng thiếu mã đơn, When kiểm tra, Then dòng đó được liệt kê vớ | Theo UC và BR liên quan | `test_upload_services.py::test_ac05_row_without_order_is_listed_and_others_stay_valid` | ✅ |
| AC-06 | Given file có xưởng lạ, When kiểm tra, Then dòng đó được liệt kê với thông báo B | Theo UC và BR liên quan | `test_upload_services.py::test_ac06_unknown_factory_is_listed` | ✅ |
| AC-07 | Given file `Data sewing 2026.xlsx` đúng mẫu, When bấm "Kiểm tra file", Then chưa | Theo UC và BR liên quan | `test_upload_services.py::test_ac07_check_saves_nothing_and_reports_the_period` | ✅ |
| AC-08 | Given đã lưu file đến ngày 04/11, When tải file có giá CM ngày cũ đã đổi, Then b | Theo UC và BR liên quan | `test_upload_services.py::test_ac08_new_price_updates_old_day_without_new_rows` | ✅ |
| AC-09 | Given đã có dữ liệu 2026, When lưu file chỉ có các ngày năm 2027, Then dữ liệu 2 | Theo UC và BR liên quan | `test_upload_services.py::test_ac09_other_period_keeps_stored_data` | ✅ |
| AC-10 | Given một dòng có trong file trước nhưng không còn trong file mới, cùng khoảng n | Theo UC và BR liên quan | `test_upload_services.py::test_ac10_row_gone_from_the_file_is_flagged_and_kept` | ✅ |
| AC-11 | Given ngày 04/11 có 45 dòng thiếu SMV và chưa có `Worker`, `Target system`, When | Theo UC và BR liên quan | `test_upload_services.py::test_ac11_newest_day_without_smv_workers_and_targets_warns_and_saves` | ✅ |
| AC-12 | Given người không có vai trò `UPDATER`, When gọi việc lưu file, Then thấy thông  | Theo UC và BR liên quan | `test_upload_services.py::test_ac12_user_without_role_cannot_save_and_data_stays` | ✅ |
| AC-13 | Given sau khi lưu, When mở Screen 7, Then lịch sử có thời điểm, người tải, tên f | Theo UC và BR liên quan | `test_upload_services.py::test_ac13_history_records_who_when_and_what` | ✅ |
| AC-14 | Given dữ liệu Fac 1 có `Line 1` và `LINE 1` cùng sau 07/07/2026, When xem chi ti | Theo UC và BR liên quan | `test_reports.py::test_ac14_ac25_line_detail_rows` | ✅ |
| AC-15 | Given dòng Fac 1 ngày 06/07/2026 ở `LINE 1`, When xem báo cáo, Then dòng đó thuộ | Theo UC và BR liên quan | `test_business_rules.py::test_ac15_br11_fac1_line_mapping_only_before_cutover` | ✅ |
| AC-16 | Given dòng trống tên sản phẩm có mã đơn gốc đã có tên trong dữ liệu, When lưu fi | Theo UC và BR liên quan | `test_business_rules.py::test_ac16_br13_empty_name_is_filled_in_order` | ✅ |
| AC-17 | Given style không tra được tên, When người cập nhật nhập tên ở Screen 9 và bấm " | Theo UC và BR liên quan | `test_settings_services.py::test_ac17_style_catalog_fills_rows_and_leaves_the_missing_list` | ✅ |
| AC-18 | Given tên `VITRIOL`, When xem Screen 9, Then tên này nằm trong danh sách chưa ph | Theo UC và BR liên quan | `test_settings_services.py::test_ac18_new_group_applies_to_old_days` | ✅ |
| AC-19 | Given các tên `ELAND WORLD`, `ELAND SPORT`, `ELAND WORLD/SPAO (QR)`, `MI HUB LIM | Theo UC và BR liên quan | `test_business_rules.py::test_ac19_br15_customer_group` | ✅ |
| AC-20 | Given chọn 24/10/2026–30/10/2026, When xem Screen 1, Then sản lượng, mục tiêu A  | Theo UC và BR liên quan | `test_reports.py::test_overview_numbers_are_hand_checked` | ✅ |
| AC-21 | Given cùng khoảng ngày, When xem Screen 1, Then hiệu suất B là: Fac 1 92,5%; Fac | Theo UC và BR liên quan | `test_reports.py::test_overview_numbers_are_hand_checked` | ✅ |
| AC-22 | Given cùng khoảng ngày, When xem Screen 1, Then tỷ lệ đúng sở trường là: Fac 1 8 | Theo UC và BR liên quan | `test_reports.py::test_overview_numbers_are_hand_checked` | ✅ |
| AC-23 | Given chọn 01/10/2026–10/10/2026, When xem Screen 1, Then hiệu suất A chỉ tính t | Theo UC và BR liên quan | `test_reports.py::test_ac23_note_when_some_days_have_no_target` | ✅ |
| AC-24 | Given lọc nhóm khách hàng ELAND, When xem Screen 1, Then sản lượng, tiền CM và h | Theo UC và BR liên quan | `test_reports.py::test_ac24_customer_filter_applies_br29` | ✅ |
| AC-25 | Given chọn 24/10/2026–30/10/2026, When xem Screen 2 với LINE 1 Fac 1, Then MO 8h | Theo UC và BR liên quan | `test_reports.py::test_ac14_ac25_line_detail_rows` | ✅ |
| AC-26 | Given chọn 24/10/2026–30/10/2026, When xem Screen 1, Then MO 8h Fac 3 khoảng 43, | Theo UC và BR liên quan | `test_reports.py::test_ac26_period_mo8h_uses_only_days_with_workers` | ✅ |
| AC-27 | Given mục tiêu MO 8h Fac 1 là 38, When lưu mức 40 hiệu lực từ 01/12/2026, Then s | Theo UC và BR liên quan | `test_business_rules.py::test_ac27_br26_level_of_a_day` | ✅ |
| AC-28 | Given bỏ trống một mức hoặc nhập 0 ở Screen 8, When bấm "Lưu mức mới", Then thấy | Theo UC và BR liên quan | `test_settings_services.py::test_ac28_wrong_level_shows_br45` | ✅ |
| AC-29 | Given hiệu suất của một chuyền Fac 2 là 89,9%, When xem báo cáo, Then có dấu 🔴 v | Theo UC và BR liên quan | `test_business_rules.py::test_ac29_ac30_br28_boundaries` | ✅ |
| AC-30 | Given MO 8h của một chuyền Fac 2 là 39,9, When xem báo cáo, Then có dấu 🔴. Given | Theo UC và BR liên quan | `test_business_rules.py::test_ac29_ac30_br28_boundaries` | ✅ |
| AC-31 | Given đã nhập Fac 2 = 17 cho 24/10/2026–30/10/2026, When chọn đúng khoảng đó, Th | Theo UC và BR liên quan | `test_reports.py::test_ac31_weekly_number_only_on_the_exact_period` | ✅ |
| AC-32 | Given nhập số lần là -1 hoặc từ ngày sau đến ngày, When bấm "Lưu số đổi mã hàng" | Theo UC và BR liên quan | `test_settings_services.py::test_ac32_wrong_weekly_input_shows_br39` | ✅ |
| AC-33 | Given dữ liệu file KPI, chọn 01/10/2026–31/10/2026, When xem Screen 6, Then số l | Theo UC và BR liên quan | `test_changeover.py::test_ac33_logic_br33_br34_br35_kpi` | ✅ |
| AC-34 | Given cùng dữ liệu, When xem Screen 6, Then số lần đổi gồm cả lên lại là Fac 1 = | Theo UC và BR liên quan | `test_changeover.py::test_ac34_rerun_ignores_days_after_the_period` | ✅ |
| AC-35 | Given một chuyền chạy cặp SMV + CM ở ngày 1, không chạy ở ngày 2, 3, chạy lại ở  | Theo UC và BR liên quan | `test_changeover.py::test_ac35_rerun_counts_again_and_kpi_does_not` | ✅ |
| AC-36 | Given chuyền chạy một cặp SMV + CM thứ Bảy và thứ Hai, nghỉ Chủ nhật, When xem S | Theo UC và BR liên quan | `test_changeover.py::test_ac36_day_off_is_not_a_gap` | ✅ |
| AC-37 | Given ngày 03/11/2026, When xem Screen 3, Then mục tiêu sản lượng Fac 2 = 9.863  | Theo UC và BR liên quan | `test_reports.py::test_ac37_ac38_daily_report` | ✅ |
| AC-38 | Given mở Screen 3 với Fac 1, When xem bảng chuyền, Then mọi chuyền có sản lượng  | Theo UC và BR liên quan | `test_reports.py::test_ac37_ac38_daily_report` | ✅ |
| AC-39 | Given chọn tháng 10/2026, When xem Screen 4, Then mỗi xưởng có các ngày có dữ li | Theo UC và BR liên quan | `test_reports.py::test_ac39_monthly_report_with_total_row` | ✅ |
| AC-40 | Given chọn Fac 2, When xem Screen 5, Then có 5 bảng, dòng Tổng MO 8h trong ngày  | Theo UC và BR liên quan | `test_reports.py::test_ac40_line_mo_tables` | ✅ |
| AC-41 | Given chọn khoảng thời gian bất kỳ, When xem Screen 1, Then có 5 biểu đồ theo UC | Theo UC và BR liên quan | `test_reports.py::test_ac41_charts_and_ranking` | ✅ |
| AC-42 | Given từ ngày sau đến ngày, When xem một báo cáo, Then thấy thông báo BR-30. | Theo UC và BR liên quan | `test_reports.py::test_ac42_wrong_period_shows_br30` | ✅ |
| AC-43 | Given bấm "Tải Excel báo cáo tuần", When mở file, Then có sheet `Tong quan`, `Fa | Theo UC và BR liên quan | `test_reports.py::test_ac43_weekly_excel_file` | ✅ |
| AC-44 | Given bấm "Tải Excel" ở Screen 3, 4, 5, 6, When mở file, Then có đúng các sheet  | Theo UC và BR liên quan | `test_reports.py::test_ac44_daily_monthly_mo_changeover_files_have_the_right_sheets` | ✅ |
| AC-45 | Given chưa có dữ liệu, When mở Screen 1, Then thấy "Chưa có dữ liệu. Người cập n | Theo UC và BR liên quan | `test_reports.py::test_ac45_no_data_at_all` | ✅ |
| AC-46 | Given mở Screen 1 với dữ liệu đến 04/11/2026, When chưa đổi bộ lọc, Then khoảng  | Theo UC và BR liên quan | `test_business_rules.py::test_ac46_br31_default_week` | ✅ |
| AC-47 | Given đã có Fac 2 = 17 cho 24/10–30/10, When lưu lại số 18 cùng khoảng, Then dan | Theo UC và BR liên quan | `test_settings_services.py::test_ac47_same_period_replaces_and_delete_shows_dash` | ✅ |
| AC-48 | Given danh mục có hai dòng trùng tên hoặc tên chuyền sai dạng, When bấm lưu, The | Theo UC và BR liên quan | `test_settings_services.py::test_ac48_wrong_catalog_shows_br47` | ✅ |
| AC-49 | Given bảng số chuyền đổi `LINE 1` thành `LINE 2`, When bấm "Lưu bảng số chuyền", | Theo UC và BR liên quan | `test_settings_services.py::test_ac49_line_table_applies_to_old_fac1_data` | ✅ |
| AC-50 | Given mở Screen 8, When xem, Then thấy mức đang áp dụng của 4 xưởng và lịch sử.  | Theo UC và BR liên quan | `test_settings_services.py::test_ac50_initial_goals_and_current_level` | ✅ |
| AC-51 | Given chọn 24/10/2026–30/10/2026, When xem Screen 1, Then giá CM trung bình của  | Theo UC và BR liên quan | `test_business_rules.py::test_ac51_br24_average_price` | ✅ |
| AC-52 | Given dữ liệu mới nhất ngày 04/11/2026, When mở Screen 3, Then ngày mặc định là  | Theo UC và BR liên quan | `test_business_rules.py::test_ac52_br31_default_month` | ✅ |
| Field production_date | Ngày sản xuất, từ `adj Date` | `models/` | Test đọc file và báo cáo | ✅ |
| Field factory | Xưởng, đổi từ `Factory` theo BR-06 | `models/` | Test đọc file và báo cáo | ✅ |
| Field customer_name | Tên khách hàng trong file | `models/` | Test đọc file và báo cáo | ✅ |
| Field customer_group | Nhóm khách hàng theo BR-15 | `models/` | Test đọc file và báo cáo | ✅ |
| Field style | Mã style, số được giữ dạng chữ | `models/` | Test đọc file và báo cáo | ✅ |
| Field po_number | Mã đơn trong file | `models/` | Test đọc file và báo cáo | ✅ |
| Field base_po | Mã đơn gốc theo BR-12 | `models/` | Test đọc file và báo cáo | ✅ |
| Field product_name | Tên sản phẩm sau khi điền theo BR-13 | `models/` | Test đọc file và báo cáo | ✅ |
| Field product_group | Nhóm sản phẩm theo BR-14 | `models/` | Test đọc file và báo cáo | ✅ |
| Field color | Màu | `models/` | Test đọc file và báo cáo | ✅ |
| Field source_line | Tên chuyền trong file | `models/` | Test đọc file và báo cáo | ✅ |
| Field line | Tên chuyền chuẩn theo BR-10, BR-11 | `models/` | Test đọc file và báo cáo | ✅ |
| Field quantity | Sản lượng (cái), từ `Product Inline Quantiy` | `models/` | Test đọc file và báo cáo | ✅ |
| Field cm_price | Giá CM (USD/cái), từ `Price` | `models/` | Test đọc file và báo cáo | ✅ |
| Field cm_earning | Tiền CM = quantity × cm_price (BR-17) | `models/` | Test đọc file và báo cáo | ✅ |
| Field working_hours | Giờ làm, từ `Revised OT 2` | `models/` | Test đọc file và báo cáo | ✅ |
| Field sewers | Số người, từ `REVISE MO` | `models/` | Test đọc file và báo cáo | ✅ |
| Field smv | SMV | `models/` | Test đọc file và báo cáo | ✅ |
| Field standard_output | Mục tiêu B, từ `Standard output of SMV (have efficiency ratio)` | `models/` | Test đọc file và báo cáo | ✅ |
| Field is_mismatched | Có khi `Match line strength` = `Trái sở trường` | `models/` | Test đọc file và báo cáo | ✅ |
| Field target_date | Ngày, từ `Date` | `models/` | Test đọc file và báo cáo | ✅ |
| Field factory | Xưởng, từ phần đầu của `Line` theo BR-16 | `models/` | Test đọc file và báo cáo | ✅ |
| Field line | Chuyền, từ phần cuối của `Line` theo BR-16 | `models/` | Test đọc file và báo cáo | ✅ |
| Field base_po | Mã đơn gốc, từ `PO` | `models/` | Test đọc file và báo cáo | ✅ |
| Field style | Style | `models/` | Test đọc file và báo cáo | ✅ |
| Field item_name | Tên sản phẩm, từ `Items` | `models/` | Test đọc file và báo cáo | ✅ |
| Field daily_target_qty | Mục tiêu A (cái), từ `Daily Target (SMV)` | `models/` | Test đọc file và báo cáo | ✅ |
| Field daily_target_cm | Mục tiêu tiền CM (USD), từ `Daily Target (CM)` | `models/` | Test đọc file và báo cáo | ✅ |
| Field is_mismatched | Có khi `Expertise` = `Mismatched Strength` | `models/` | Test đọc file và báo cáo | ✅ |
| Field work_date | Ngày | `models/` | Test đọc file và báo cáo | ✅ |
| Field factory | Xưởng | `models/` | Test đọc file và báo cáo | ✅ |
| Field direct_sewers | Số thợ may trực tiếp | `models/` | Test đọc file và báo cáo | ✅ |
| Field factory | Xưởng | `models/` | Test đọc file và báo cáo | ✅ |
| Field effective_from | Ngày hiệu lực | `models/` | Test đọc file và báo cáo | ✅ |
| Field efficiency_target | Mục tiêu hiệu suất, áp cho cả A và B | `models/` | Test đọc file và báo cáo | ✅ |
| Field mo8h_target | Mục tiêu MO 8h | `models/` | Test đọc file và báo cáo | ✅ |
| Field efficiency_threshold | Ngưỡng cảnh báo hiệu suất | `models/` | Test đọc file và báo cáo | ✅ |
| Field mo8h_threshold | Ngưỡng cảnh báo MO 8h | `models/` | Test đọc file và báo cáo | ✅ |
| Field updated_by | Người lưu | `models/` | Test đọc file và báo cáo | ✅ |
| Field factory | Xưởng | `models/` | Test đọc file và báo cáo | ✅ |
| Field from_date | Từ ngày | `models/` | Test đọc file và báo cáo | ✅ |
| Field to_date | Đến ngày | `models/` | Test đọc file và báo cáo | ✅ |
| Field changeover_count | Số lần xưởng cung cấp | `models/` | Test đọc file và báo cáo | ✅ |
| Field updated_by | Người lưu | `models/` | Test đọc file và báo cáo | ✅ |
| Field product_name | Tên sản phẩm | `models/` | Test đọc file và báo cáo | ✅ |
| Field product_group | Nhóm sản phẩm; có thể thêm nhóm mới | `models/` | Test đọc file và báo cáo | ✅ |
| Field customer_name | Tên khách trong file | `models/` | Test đọc file và báo cáo | ✅ |
| Field customer_group | Nhóm khách | `models/` | Test đọc file và báo cáo | ✅ |
| Field old_line | Tên chuyền cũ | `models/` | Test đọc file và báo cáo | ✅ |
| Field new_line | Tên chuyền hiện nay | `models/` | Test đọc file và báo cáo | ✅ |
| Field style | Style | `models/` | Test đọc file và báo cáo | ✅ |
| Field product_name | Tên sản phẩm | `models/` | Test đọc file và báo cáo | ✅ |
| Field uploaded_at | Thời điểm lưu | `models/` | Test đọc file và báo cáo | ✅ |
| Field uploaded_by | Người tải | `models/` | Test đọc file và báo cáo | ✅ |
| Field file_name | Tên file | `models/` | Test đọc file và báo cáo | ✅ |
| Field from_date | Ngày đầu trong file | `models/` | Test đọc file và báo cáo | ✅ |
| Field to_date | Ngày cuối trong file | `models/` | Test đọc file và báo cáo | ✅ |
| Field saved_rows | Số dòng sản lượng đã lưu | `models/` | Test đọc file và báo cáo | ✅ |
| Field skipped_rows | Số dòng bị bỏ qua | `models/` | Test đọc file và báo cáo | ✅ |

## 6. Các bước
- [x] Step 0 UI concept recorded
- [x] Scaffold
- [x] Backend - ALL CHECKS PASSED
- [x] UI design
- [x] UI build - ALL CHECKS PASSED
- [x] Gateway registration check
- [x] Navigation check
- [x] Scaffold ping removed
- [x] Document updated
- [x] Verify
- [x] Report

## 7. Giả định khi triển khai
- Tên viết tắt của người làm là `thynguyen`, lấy từ tài khoản GitHub `thynguyen-lab`, vì tên viết tắt chỉ gồm chữ thường và số.
- Câu 4 và câu 6 của lượt hỏi giao diện để trống nên dùng đề xuất.

## Fix log
- Hai ô Ngày đầu, Ngày cuối ở màn hình Cập nhật dữ liệu bị cắt chữ -> 5 ô xếp một hàng quá hẹp -> tách ngày thành một hàng riêng trong `upload_blocks.py` -> `check.py` đạt.
- File `.env` tạo từ `.env.example` làm app không khởi động (`POSTGRES_PORT` trống không phải số) -> nguyên nhân nằm ở cấu hình dùng chung của dự án, không thuộc chức năng này -> không sửa, báo trong báo cáo cuối; khi kiểm tra chỉ đặt biến môi trường tạm cho lần chạy.
- Không xoá được `backend/features/sewing_productivity/tests/test_ping_service.py` vì lệnh xoá bị chặn -> viết lại file này thành test kiểm tra controller không còn `ping` và có đúng 26 nghiệp vụ -> test đạt.
- Số lần đổi KPI tháng 10 trên file thật ra Fac 1 = 71, Fac 2 = 72, Fac 3 = 131 thay vì 69, 68, 129 -> app đếm cả cặp SMV + CM của các ngày sau ngày đầu của đơn, nên SMV được sửa giữa chừng tính thành lần đổi mới -> chỉ đọc cặp ở ngày đầu tiên của đơn trong `ChangeoverBusiness.kpi_rows`, thêm test hồi quy `test_br32_only_the_first_day_of_an_order_counts` -> chạy lại trên file thật.
