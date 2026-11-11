"""Top layer of feature "Tính giá sợi". Pages call it through gateway.open(...)."""

from backend.core.base import BaseController, FileDownloadDTO, cached_query
from backend.features.yarn_costing.dto.audit_dto import AuditLogListResponse, ListAuditLogRequest
from backend.features.yarn_costing.dto.common_dto import RecalcResultResponse, SaveCountResponse
from backend.features.yarn_costing.dto.dashboard_dto import (
    CheckNsmAnomaliesRequest,
    CheckPriceAnomaliesRequest,
    CheckSiroAnomaliesRequest,
    DashboardResponse,
    GetDashboardRequest,
    NsmAnomalyResponse,
    PriceAnomalyResponse,
    SiroAnomalyResponse,
)
from backend.features.yarn_costing.dto.import_dto import (
    ComponentImportResponse,
    DownloadComponentTemplateRequest,
    DownloadNotProducedTemplateRequest,
    DownloadTemplateRequest,
    GetLegacyComparisonRequest,
    ImportBatchListResponse,
    ImportComponentFileRequest,
    ImportNotProducedFileRequest,
    ImportResultResponse,
    ImportWorkbookRequest,
    LegacyComparisonResponse,
    ListImportBatchesRequest,
    NotProducedImportResponse,
)
from backend.features.yarn_costing.dto.loss_dto import (
    CreatePrimaryLossGroupRequest,
    CreateSecondaryLossGroupRequest,
    DeleteLossGroupRequest,
    ListLossGroupsRequest,
    LossGroupListResponse,
    LossGroupSaveResponse,
    UpdateLossGroupRequest,
)
from backend.features.yarn_costing.dto.master_dto import (
    AddExchangeRateRequest,
    ApplyRateVersionRequest,
    GetRecalcDiffRequest,
    ListRecalcBatchesRequest,
    RecalcBatchListResponse,
    RecalcDiffResponse,
    RecalculateNotPricedRequest,
    SavePackagingTypesRequest,
    SaveProcessRoutesRequest,
    SaveRecoveryRatesRequest,
    SaveStageConfigRequest,
    UpdateTrialFactorRequest,
)
from backend.features.yarn_costing.dto.material_dto import (
    ArrivalImportResponse,
    ArrivalListResponse,
    CalculateQuoteRequest,
    DeleteQuoteRequest,
    ExportQuotesRequest,
    GetMaterialAveragesRequest,
    GetMaterialSetupRequest,
    GetMonthlySettingRequest,
    GetQuoteFormRequest,
    GetStockOutComparisonRequest,
    ImportArrivalFileRequest,
    ImportStockFileRequest,
    ListArrivalsRequest,
    ListQuotesRequest,
    ListStockMonthsRequest,
    MaterialAveragesResponse,
    MaterialSaveResponse,
    MaterialSetupResponse,
    MonthlySettingResponse,
    QuoteFormResponse,
    QuoteListResponse,
    QuoteResponse,
    SaveArrivalLotsRequest,
    SaveArrivalMappingsRequest,
    SaveMonthlySettingRequest,
    SavePriceGroupRequest,
    SaveStockItemSettingsRequest,
    StockImportResponse,
    StockMonthListResponse,
    StockOutComparisonResponse,
)
from backend.features.yarn_costing.dto.name_dto import (
    CheckYarnNameRequest,
    ExportRenameListRequest,
    GetNameCheckRequest,
    ImportRenameFileRequest,
    NameCheckResponse,
    NameSaveResponse,
    NormalizeNamesRequest,
    NormalizeNamesResponse,
    RenameImportResponse,
    RenameYarnRequest,
    RenameYarnResponse,
    ResolvePendingResponse,
    ResolvePendingWordRequest,
    SaveNameDictionaryRequest,
    SaveNamePartsRequest,
    YarnNameCheckResponse,
)
from backend.features.yarn_costing.dto.price_dto import (
    CreateAdjustmentLineRequest,
    DeleteAdjustmentLineRequest,
    ExportPriceLinesRequest,
    ListPriceLinesRequest,
    PriceLineListResponse,
    PriceLineResponse,
    SetAccountingCodeRequest,
)
from backend.features.yarn_costing.dto.pricing_dto import (
    CorrectYarnNsmRequest,
    CreateNsmRevisionRequest,
    GetYarnDetailRequest,
    NsmSuggestionResponse,
    PricingResultResponse,
    SaveYarnNsmRequest,
    SuggestNsmRequest,
    YarnDetailResponse,
)
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest, ReferenceDataResponse
from backend.features.yarn_costing.dto.request_dto import (
    AnalyzeYarnNameRequest,
    CancelYarnRequestRequest,
    CheckRequestSubmitRequest,
    CreateYarnRequestRequest,
    ListYarnsRequest,
    NotProducedResponse,
    RejectYarnRequestRequest,
    RequestSubmitCheckResponse,
    SetNotProducedRequest,
    UpdateYarnRequestRequest,
    YarnListResponse,
    YarnNameAnalysisResponse,
    YarnResponse,
)
from backend.features.yarn_costing.dto.sales_dto import (
    AccountingComparisonResponse,
    AccountingImportResponse,
    AccountingMonthListResponse,
    ComparePriceLinesRequest,
    ComparePriceLinesResponse,
    CustomerNameListResponse,
    CustomerNameResponse,
    GetAccountingComparisonRequest,
    ImportAccountingFileRequest,
    ListAccountingMonthsRequest,
    ListCustomerNamesRequest,
    SaveCustomerNameRequest,
    SuggestYarnsRequest,
    UseExistingYarnRequest,
    UseExistingYarnResponse,
    YarnSuggestionResponse,
)
from backend.features.yarn_costing.services.add_exchange_rate_service import AddExchangeRateService
from backend.features.yarn_costing.services.analyze_yarn_name_service import AnalyzeYarnNameService
from backend.features.yarn_costing.services.apply_rate_version_service import ApplyRateVersionService
from backend.features.yarn_costing.services.calculate_quote_service import CalculateQuoteService
from backend.features.yarn_costing.services.cancel_yarn_request_service import CancelYarnRequestService
from backend.features.yarn_costing.services.check_nsm_anomalies_service import CheckNsmAnomaliesService
from backend.features.yarn_costing.services.check_price_anomalies_service import CheckPriceAnomaliesService
from backend.features.yarn_costing.services.check_request_submit_service import CheckRequestSubmitService
from backend.features.yarn_costing.services.check_siro_anomalies_service import CheckSiroAnomaliesService
from backend.features.yarn_costing.services.check_yarn_name_service import CheckYarnNameService
from backend.features.yarn_costing.services.compare_price_lines_service import ComparePriceLinesService
from backend.features.yarn_costing.services.correct_yarn_nsm_service import CorrectYarnNsmService
from backend.features.yarn_costing.services.create_adjustment_line_service import CreateAdjustmentLineService
from backend.features.yarn_costing.services.create_nsm_revision_service import CreateNsmRevisionService
from backend.features.yarn_costing.services.create_primary_loss_group_service import CreatePrimaryLossGroupService
from backend.features.yarn_costing.services.create_secondary_loss_group_service import CreateSecondaryLossGroupService
from backend.features.yarn_costing.services.create_yarn_request_service import CreateYarnRequestService
from backend.features.yarn_costing.services.delete_adjustment_line_service import DeleteAdjustmentLineService
from backend.features.yarn_costing.services.delete_loss_group_service import DeleteLossGroupService
from backend.features.yarn_costing.services.delete_quote_service import DeleteQuoteService
from backend.features.yarn_costing.services.download_component_template_service import (
    DownloadComponentTemplateService,
)
from backend.features.yarn_costing.services.download_not_produced_template_service import (
    DownloadNotProducedTemplateService,
)
from backend.features.yarn_costing.services.download_template_service import DownloadTemplateService
from backend.features.yarn_costing.services.export_price_lines_service import ExportPriceLinesService
from backend.features.yarn_costing.services.export_quotes_service import ExportQuotesService
from backend.features.yarn_costing.services.export_rename_list_service import ExportRenameListService
from backend.features.yarn_costing.services.get_accounting_comparison_service import GetAccountingComparisonService
from backend.features.yarn_costing.services.get_dashboard_service import GetDashboardService
from backend.features.yarn_costing.services.get_legacy_comparison_service import GetLegacyComparisonService
from backend.features.yarn_costing.services.get_material_averages_service import GetMaterialAveragesService
from backend.features.yarn_costing.services.get_material_setup_service import GetMaterialSetupService
from backend.features.yarn_costing.services.get_monthly_setting_service import GetMonthlySettingService
from backend.features.yarn_costing.services.get_name_check_service import GetNameCheckService
from backend.features.yarn_costing.services.get_quote_form_service import GetQuoteFormService
from backend.features.yarn_costing.services.get_recalc_diff_service import GetRecalcDiffService
from backend.features.yarn_costing.services.get_reference_data_service import GetReferenceDataService
from backend.features.yarn_costing.services.get_stock_out_comparison_service import GetStockOutComparisonService
from backend.features.yarn_costing.services.get_yarn_detail_service import GetYarnDetailService
from backend.features.yarn_costing.services.import_accounting_file_service import ImportAccountingFileService
from backend.features.yarn_costing.services.import_arrival_file_service import ImportArrivalFileService
from backend.features.yarn_costing.services.import_component_file_service import ImportComponentFileService
from backend.features.yarn_costing.services.import_not_produced_file_service import ImportNotProducedFileService
from backend.features.yarn_costing.services.import_rename_file_service import ImportRenameFileService
from backend.features.yarn_costing.services.import_stock_file_service import ImportStockFileService
from backend.features.yarn_costing.services.import_workbook_service import ImportWorkbookService
from backend.features.yarn_costing.services.list_accounting_months_service import ListAccountingMonthsService
from backend.features.yarn_costing.services.list_arrivals_service import ListArrivalsService
from backend.features.yarn_costing.services.list_audit_log_service import ListAuditLogService
from backend.features.yarn_costing.services.list_customer_names_service import ListCustomerNamesService
from backend.features.yarn_costing.services.list_import_batches_service import ListImportBatchesService
from backend.features.yarn_costing.services.list_loss_groups_service import ListLossGroupsService
from backend.features.yarn_costing.services.list_price_lines_service import ListPriceLinesService
from backend.features.yarn_costing.services.list_quotes_service import ListQuotesService
from backend.features.yarn_costing.services.list_recalc_batches_service import ListRecalcBatchesService
from backend.features.yarn_costing.services.list_stock_months_service import ListStockMonthsService
from backend.features.yarn_costing.services.list_yarns_service import ListYarnsService
from backend.features.yarn_costing.services.normalize_names_service import NormalizeNamesService
from backend.features.yarn_costing.services.recalculate_not_priced_service import RecalculateNotPricedService
from backend.features.yarn_costing.services.reject_yarn_request_service import RejectYarnRequestService
from backend.features.yarn_costing.services.rename_yarn_service import RenameYarnService
from backend.features.yarn_costing.services.resolve_pending_word_service import ResolvePendingWordService
from backend.features.yarn_costing.services.save_arrival_lots_service import SaveArrivalLotsService
from backend.features.yarn_costing.services.save_arrival_mappings_service import SaveArrivalMappingsService
from backend.features.yarn_costing.services.save_customer_name_service import SaveCustomerNameService
from backend.features.yarn_costing.services.save_monthly_setting_service import SaveMonthlySettingService
from backend.features.yarn_costing.services.save_name_dictionary_service import SaveNameDictionaryService
from backend.features.yarn_costing.services.save_name_parts_service import SaveNamePartsService
from backend.features.yarn_costing.services.save_packaging_types_service import SavePackagingTypesService
from backend.features.yarn_costing.services.save_price_group_service import SavePriceGroupService
from backend.features.yarn_costing.services.save_process_routes_service import SaveProcessRoutesService
from backend.features.yarn_costing.services.save_recovery_rates_service import SaveRecoveryRatesService
from backend.features.yarn_costing.services.save_stage_config_service import SaveStageConfigService
from backend.features.yarn_costing.services.save_stock_item_settings_service import SaveStockItemSettingsService
from backend.features.yarn_costing.services.save_yarn_nsm_service import SaveYarnNsmService
from backend.features.yarn_costing.services.set_accounting_code_service import SetAccountingCodeService
from backend.features.yarn_costing.services.set_not_produced_service import SetNotProducedService
from backend.features.yarn_costing.services.suggest_nsm_service import SuggestNsmService
from backend.features.yarn_costing.services.suggest_similar_yarns_service import SuggestSimilarYarnsService
from backend.features.yarn_costing.services.update_loss_group_service import UpdateLossGroupService
from backend.features.yarn_costing.services.update_trial_factor_service import UpdateTrialFactorService
from backend.features.yarn_costing.services.update_yarn_request_service import UpdateYarnRequestService
from backend.features.yarn_costing.services.use_existing_yarn_service import UseExistingYarnService


class YarnCostingController(BaseController):
    @cached_query
    def list_audit_log(self, request: ListAuditLogRequest) -> AuditLogListResponse:
        """UC-02 Xem nhật ký thao tác."""
        return ListAuditLogService().handle(request)

    def save_stage_config(self, request: SaveStageConfigRequest) -> RecalcResultResponse:
        """UC-03 Sửa cấu hình công đoạn."""
        return SaveStageConfigService().handle(request)

    def apply_rate_version(self, request: ApplyRateVersionRequest) -> RecalcResultResponse:
        """UC-04 Áp dụng định mức chi phí/phút mới."""
        return ApplyRateVersionService().handle(request)

    def save_packaging_types(self, request: SavePackagingTypesRequest) -> RecalcResultResponse:
        """UC-05 Khai báo loại đóng gói."""
        return SavePackagingTypesService().handle(request)

    def save_recovery_rates(self, request: SaveRecoveryRatesRequest) -> RecalcResultResponse:
        """UC-06 Khai báo hồi phế."""
        return SaveRecoveryRatesService().handle(request)

    def save_process_routes(self, request: SaveProcessRoutesRequest) -> SaveCountResponse:
        """UC-07 Khai báo quy trình công nghệ."""
        return SaveProcessRoutesService().handle(request)

    def add_exchange_rate(self, request: AddExchangeRateRequest) -> SaveCountResponse:
        """UC-08 Cập nhật tỷ giá."""
        return AddExchangeRateService().handle(request)

    def update_trial_factor(self, request: UpdateTrialFactorRequest) -> RecalcResultResponse:
        """UC-09 Cập nhật hệ số thí nghiệm."""
        return UpdateTrialFactorService().handle(request)

    @cached_query
    def list_loss_groups(self, request: ListLossGroupsRequest) -> LossGroupListResponse:
        """UC-10 Tra cứu tiêu hao."""
        return ListLossGroupsService().handle(request)

    def create_primary_loss_group(self, request: CreatePrimaryLossGroupRequest) -> LossGroupSaveResponse:
        """UC-11 Khai báo nhóm tiêu hao sơ cấp."""
        return CreatePrimaryLossGroupService().handle(request)

    def create_secondary_loss_group(self, request: CreateSecondaryLossGroupRequest) -> LossGroupSaveResponse:
        """UC-12 Khai báo nhóm tiêu hao thứ cấp."""
        return CreateSecondaryLossGroupService().handle(request)

    def update_loss_group(self, request: UpdateLossGroupRequest) -> LossGroupSaveResponse:
        """UC-13 Sửa nhóm tiêu hao."""
        return UpdateLossGroupService().handle(request)

    def delete_loss_group(self, request: DeleteLossGroupRequest) -> SaveCountResponse:
        """UC-14 Xoá nhóm tiêu hao."""
        return DeleteLossGroupService().handle(request)

    def create_yarn_request(self, request: CreateYarnRequestRequest) -> YarnResponse:
        """UC-15 Tạo yêu cầu tính giá."""
        return CreateYarnRequestService().handle(request)

    def update_yarn_request(self, request: UpdateYarnRequestRequest) -> YarnResponse:
        """UC-16 Sửa yêu cầu."""
        return UpdateYarnRequestService().handle(request)

    def cancel_yarn_request(self, request: CancelYarnRequestRequest) -> YarnResponse:
        """UC-17 Huỷ yêu cầu."""
        return CancelYarnRequestService().handle(request)

    def reject_yarn_request(self, request: RejectYarnRequestRequest) -> YarnResponse:
        """UC-18 Từ chối yêu cầu."""
        return RejectYarnRequestService().handle(request)

    @cached_query
    def list_yarns(self, request: ListYarnsRequest) -> YarnListResponse:
        """UC-19 Xem danh sách yêu cầu."""
        return ListYarnsService().handle(request)

    @cached_query
    def suggest_nsm(self, request: SuggestNsmRequest) -> NsmSuggestionResponse:
        """UC-20 Lấy NSM gợi ý (tự điền)."""
        return SuggestNsmService().handle(request)

    def save_yarn_nsm(self, request: SaveYarnNsmRequest) -> PricingResultResponse:
        """UC-21 Nhập NSM, kiểm tra và lưu giá."""
        return SaveYarnNsmService().handle(request)

    @cached_query
    def get_yarn_detail(self, request: GetYarnDetailRequest) -> YarnDetailResponse:
        """UC-22 Xem chi tiết tính giá và lịch sử."""
        return GetYarnDetailService().handle(request)

    def correct_yarn_nsm(self, request: CorrectYarnNsmRequest) -> PricingResultResponse:
        """UC-23 Sửa NSM của mã đã có giá (nhập sai)."""
        return CorrectYarnNsmService().handle(request)

    def create_nsm_revision(self, request: CreateNsmRevisionRequest) -> PricingResultResponse:
        """UC-24 Tạo bản ĐCNSM."""
        return CreateNsmRevisionService().handle(request)

    def create_adjustment_line(self, request: CreateAdjustmentLineRequest) -> PriceLineResponse:
        """UC-25 Tạo dòng chiết khấu / phụ phí."""
        return CreateAdjustmentLineService().handle(request)

    def delete_adjustment_line(self, request: DeleteAdjustmentLineRequest) -> SaveCountResponse:
        """UC-26 Xoá dòng chiết khấu / phụ phí."""
        return DeleteAdjustmentLineService().handle(request)

    @cached_query
    def list_price_lines(self, request: ListPriceLinesRequest) -> PriceLineListResponse:
        """UC-27 Tra cứu bảng giá."""
        return ListPriceLinesService().handle(request)

    def set_accounting_code(self, request: SetAccountingCodeRequest) -> PriceLineResponse:
        """UC-28 Nhập / sửa / xoá mã kế toán."""
        return SetAccountingCodeService().handle(request)

    @cached_query
    def export_price_lines(self, request: ExportPriceLinesRequest) -> FileDownloadDTO:
        """UC-29 Xuất Excel bảng giá."""
        return ExportPriceLinesService().handle(request)

    @cached_query
    def check_price_anomalies(self, request: CheckPriceAnomaliesRequest) -> PriceAnomalyResponse:
        """UC-30 Kiểm tra giá bất thường."""
        return CheckPriceAnomaliesService().handle(request)

    @cached_query
    def check_nsm_anomalies(self, request: CheckNsmAnomaliesRequest) -> NsmAnomalyResponse:
        """UC-31 Kiểm tra NSM bất thường."""
        return CheckNsmAnomaliesService().handle(request)

    @cached_query
    def check_siro_anomalies(self, request: CheckSiroAnomaliesRequest) -> SiroAnomalyResponse:
        """UC-46 Kiểm tra Siro / Compact bất thường."""
        return CheckSiroAnomaliesService().handle(request)

    @cached_query
    def get_dashboard(self, request: GetDashboardRequest) -> DashboardResponse:
        """UC-32 Xem dashboard."""
        return GetDashboardService().handle(request)

    @cached_query
    def download_template(self, request: DownloadTemplateRequest) -> FileDownloadDTO:
        """UC-33 Tải file mẫu."""
        return DownloadTemplateService().handle(request)

    def import_workbook(self, request: ImportWorkbookRequest) -> ImportResultResponse:
        """UC-34 Kiểm tra và lưu dữ liệu từ file."""
        return ImportWorkbookService().handle(request)

    @cached_query
    def get_legacy_comparison(self, request: GetLegacyComparisonRequest) -> LegacyComparisonResponse:
        """UC-35 Đối chiếu giá cũ với giá app."""
        return GetLegacyComparisonService().handle(request)

    @cached_query
    def list_recalc_batches(self, request: ListRecalcBatchesRequest) -> RecalcBatchListResponse:
        """UC-36 Xem danh sách lần tính lại toàn bộ."""
        return ListRecalcBatchesService().handle(request)

    @cached_query
    def get_recalc_diff(self, request: GetRecalcDiffRequest) -> RecalcDiffResponse:
        """UC-37 Xem chênh lệch của một lần tính lại."""
        return GetRecalcDiffService().handle(request)

    @cached_query
    def get_reference_data(self, request: GetReferenceDataRequest) -> ReferenceDataResponse:
        """UC-38 Lấy dữ liệu tham chiếu."""
        return GetReferenceDataService().handle(request)

    @cached_query
    def analyze_yarn_name(self, request: AnalyzeYarnNameRequest) -> YarnNameAnalysisResponse:
        """UC-40 Nhận diện tên sợi."""
        return AnalyzeYarnNameService().handle(request)

    @cached_query
    def list_import_batches(self, request: ListImportBatchesRequest) -> ImportBatchListResponse:
        """UC-41 Xem danh sách lần nhập file."""
        return ListImportBatchesService().handle(request)

    @cached_query
    def check_request_submit(self, request: CheckRequestSubmitRequest) -> RequestSubmitCheckResponse:
        """UC-42 Kiểm tra điều kiện gửi yêu cầu."""
        return CheckRequestSubmitService().handle(request)

    def recalculate_not_priced(self, request: RecalculateNotPricedRequest) -> RecalcResultResponse:
        """UC-43 Tính lại các mã chưa tính được."""
        return RecalculateNotPricedService().handle(request)

    @cached_query
    def download_component_template(self, request: DownloadComponentTemplateRequest) -> FileDownloadDTO:
        """UC-44 Tải file mẫu khai báo thành phần sợi pha."""
        return DownloadComponentTemplateService().handle(request)

    def import_component_file(self, request: ImportComponentFileRequest) -> ComponentImportResponse:
        """UC-45 Kiểm tra và lưu file khai báo thành phần sợi pha."""
        return ImportComponentFileService().handle(request)

    def set_not_produced(self, request: SetNotProducedRequest) -> NotProducedResponse:
        """UC-47 Đánh dấu / bỏ đánh dấu Không sản xuất."""
        return SetNotProducedService().handle(request)

    @cached_query
    def download_not_produced_template(self, request: DownloadNotProducedTemplateRequest) -> FileDownloadDTO:
        """UC-48 Tải file mẫu đánh dấu Không sản xuất."""
        return DownloadNotProducedTemplateService().handle(request)

    def import_not_produced_file(self, request: ImportNotProducedFileRequest) -> NotProducedImportResponse:
        """UC-48 Kiểm tra và lưu file đánh dấu Không sản xuất."""
        return ImportNotProducedFileService().handle(request)

    # ---- mở rộng 2026-11-10 (yêu cầu của Sales) ----
    @cached_query
    def suggest_similar_yarns(self, request: SuggestYarnsRequest) -> YarnSuggestionResponse:
        """UC-49 Gợi ý sợi tương tự khi nhập tên."""
        return SuggestSimilarYarnsService().handle(request)

    def use_existing_yarn(self, request: UseExistingYarnRequest) -> UseExistingYarnResponse:
        """UC-50 Dùng sợi có sẵn từ gợi ý."""
        return UseExistingYarnService().handle(request)

    @cached_query
    def list_customer_names(self, request: ListCustomerNamesRequest) -> CustomerNameListResponse:
        """UC-51 (xem) Tên theo khách của một sợi."""
        return ListCustomerNamesService().handle(request)

    def save_customer_name(self, request: SaveCustomerNameRequest) -> CustomerNameResponse:
        """UC-51 Thêm / sửa / xoá tên theo khách."""
        return SaveCustomerNameService().handle(request)

    @cached_query
    def compare_price_lines(self, request: ComparePriceLinesRequest) -> ComparePriceLinesResponse:
        """UC-52 So sánh 2 sợi."""
        return ComparePriceLinesService().handle(request)

    def import_accounting_file(self, request: ImportAccountingFileRequest) -> AccountingImportResponse:
        """UC-53 Tải file giá thành kế toán (file Z)."""
        return ImportAccountingFileService().handle(request)

    @cached_query
    def list_accounting_months(self, request: ListAccountingMonthsRequest) -> AccountingMonthListResponse:
        """UC-53 / UC-54 Các tháng giá thành kế toán đã lưu."""
        return ListAccountingMonthsService().handle(request)

    @cached_query
    def get_accounting_comparison(self, request: GetAccountingComparisonRequest) -> AccountingComparisonResponse:
        """UC-54 Đối chiếu giá app với giá thành kế toán."""
        return GetAccountingComparisonService().handle(request)

    # ---- đợt 2 (bổ sung 2026-11-10): đọc theo tài khoản (BR-84) nên không dùng @cached_query ----
    def get_material_setup(self, request: GetMaterialSetupRequest) -> MaterialSetupResponse:
        """UC-55 / UC-57 Nhóm giá nguyên liệu và khai báo mã kho (chỉ Sales / Phòng SO, BR-84)."""
        return GetMaterialSetupService().handle(request)

    def save_price_group(self, request: SavePriceGroupRequest) -> MaterialSaveResponse:
        """UC-55 Thêm / sửa / xoá nhóm giá nguyên liệu."""
        return SavePriceGroupService().handle(request)

    def import_stock_file(self, request: ImportStockFileRequest) -> StockImportResponse:
        """UC-56 Tải file kho tháng."""
        return ImportStockFileService().handle(request)

    def list_stock_months(self, request: ListStockMonthsRequest) -> StockMonthListResponse:
        """UC-56 Các tháng kho đã lưu."""
        return ListStockMonthsService().handle(request)

    def save_stock_item_settings(self, request: SaveStockItemSettingsRequest) -> MaterialSaveResponse:
        """UC-57 Khai báo mã kho nguyên liệu."""
        return SaveStockItemSettingsService().handle(request)

    def get_monthly_setting(self, request: GetMonthlySettingRequest) -> MonthlySettingResponse:
        """UC-58 Khai báo tháng (bản đã lưu hoặc bản nháp)."""
        return GetMonthlySettingService().handle(request)

    def save_monthly_setting(self, request: SaveMonthlySettingRequest) -> MaterialSaveResponse:
        """UC-58 Lưu khai báo tháng."""
        return SaveMonthlySettingService().handle(request)

    def get_material_averages(self, request: GetMaterialAveragesRequest) -> MaterialAveragesResponse:
        """UC-59 Bảng giá nguyên liệu bình quân tháng."""
        return GetMaterialAveragesService().handle(request)

    def import_arrival_file(self, request: ImportArrivalFileRequest) -> ArrivalImportResponse:
        """UC-60 Nhập file hàng sắp về."""
        return ImportArrivalFileService().handle(request)

    def list_arrivals(self, request: ListArrivalsRequest) -> ArrivalListResponse:
        """UC-61 Danh sách lô hàng sắp về."""
        return ListArrivalsService().handle(request)

    def save_arrival_lots(self, request: SaveArrivalLotsRequest) -> MaterialSaveResponse:
        """UC-61 Lưu thay đổi lô hàng sắp về."""
        return SaveArrivalLotsService().handle(request)

    def save_arrival_mappings(self, request: SaveArrivalMappingsRequest) -> MaterialSaveResponse:
        """UC-61 Khai báo nhóm cho nhà cung cấp + mô tả."""
        return SaveArrivalMappingsService().handle(request)

    def get_quote_form(self, request: GetQuoteFormRequest) -> QuoteFormResponse:
        """UC-62 Dữ liệu điền sẵn của khối Tính giá báo khách."""
        return GetQuoteFormService().handle(request)

    def calculate_quote(self, request: CalculateQuoteRequest) -> QuoteResponse:
        """UC-62 Tính thử / lưu giá báo khách."""
        return CalculateQuoteService().handle(request)

    def list_quotes(self, request: ListQuotesRequest) -> QuoteListResponse:
        """UC-63 Các lần tính giá báo khách."""
        return ListQuotesService().handle(request)

    def export_quotes(self, request: ExportQuotesRequest) -> FileDownloadDTO:
        """UC-63 Xuất Excel các lần tính giá báo khách."""
        return ExportQuotesService().handle(request)

    def delete_quote(self, request: DeleteQuoteRequest) -> MaterialSaveResponse:
        """UC-63 Xoá một lần tính giá báo khách."""
        return DeleteQuoteService().handle(request)

    def get_stock_out_comparison(self, request: GetStockOutComparisonRequest) -> StockOutComparisonResponse:
        """UC-64 So đơn giá xuất kho với giá bình quân."""
        return GetStockOutComparisonService().handle(request)

    # ---- tên sợi (bổ sung 2026-11-11) ----
    @cached_query
    def check_yarn_name(self, request: CheckYarnNameRequest) -> YarnNameCheckResponse:
        """BR-101 / BR-102 Tên ghép / gõ tay và kết quả kiểm tra (Screen 2, đổi tên)."""
        return CheckYarnNameService().handle(request)

    def get_name_check(self, request: GetNameCheckRequest) -> NameCheckResponse:
        """UC-65 Tên nghi sai + từ điển, chữ mới, nhóm sợi / từ khoá (khởi tạo lần đầu - BR-103)."""
        return GetNameCheckService().handle(request)

    def save_name_dictionary(self, request: SaveNameDictionaryRequest) -> NameSaveResponse:
        """UC-66 Lưu từ điển tên chuẩn."""
        return SaveNameDictionaryService().handle(request)

    def resolve_pending_word(self, request: ResolvePendingWordRequest) -> ResolvePendingResponse:
        """UC-67 Thêm chữ mới vào từ điển / sửa chữ sai trong mọi tên."""
        return ResolvePendingWordService().handle(request)

    def rename_yarn(self, request: RenameYarnRequest) -> RenameYarnResponse:
        """UC-68 Đổi tên một sợi."""
        return RenameYarnService().handle(request)

    def export_rename_list(self, request: ExportRenameListRequest) -> FileDownloadDTO:
        """UC-69 Tải danh sách tên nghi sai để sửa."""
        return ExportRenameListService().handle(request)

    def import_rename_file(self, request: ImportRenameFileRequest) -> RenameImportResponse:
        """UC-69 Đổi tên hàng loạt bằng file."""
        return ImportRenameFileService().handle(request)

    def save_name_parts(self, request: SaveNamePartsRequest) -> NameSaveResponse:
        """UC-70 Lưu nhóm sợi / từ khoá của ô ghép tên."""
        return SaveNamePartsService().handle(request)

    def normalize_names(self, request: NormalizeNamesRequest) -> NormalizeNamesResponse:
        """UC-71 Chuẩn hoá viết hoa và xử lý tên trùng."""
        return NormalizeNamesService().handle(request)
