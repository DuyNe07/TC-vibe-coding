"""Top layer of feature "Tính giá sợi". Pages call it through gateway.open(...)."""

from backend.core.base import BaseController, FileDownloadDTO
from backend.features.yarn_costing.dto.audit_dto import AuditLogListResponse, ListAuditLogRequest
from backend.features.yarn_costing.dto.common_dto import RecalcResultResponse, SaveCountResponse
from backend.features.yarn_costing.dto.dashboard_dto import (
    CheckNsmAnomaliesRequest,
    CheckPriceAnomaliesRequest,
    DashboardResponse,
    GetDashboardRequest,
    NsmAnomalyResponse,
    PriceAnomalyResponse,
)
from backend.features.yarn_costing.dto.import_dto import (
    ComponentImportResponse,
    DownloadComponentTemplateRequest,
    DownloadTemplateRequest,
    GetLegacyComparisonRequest,
    ImportBatchListResponse,
    ImportComponentFileRequest,
    ImportResultResponse,
    ImportWorkbookRequest,
    LegacyComparisonResponse,
    ListImportBatchesRequest,
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
    RejectYarnRequestRequest,
    RequestSubmitCheckResponse,
    UpdateYarnRequestRequest,
    YarnListResponse,
    YarnNameAnalysisResponse,
    YarnResponse,
)
from backend.features.yarn_costing.dto.user_dto import (
    ActorResponse,
    SaveUserGroupRequest,
    UserGroupResponse,
    VerifyActorRequest,
)
from backend.features.yarn_costing.services.add_exchange_rate_service import AddExchangeRateService
from backend.features.yarn_costing.services.analyze_yarn_name_service import AnalyzeYarnNameService
from backend.features.yarn_costing.services.apply_rate_version_service import ApplyRateVersionService
from backend.features.yarn_costing.services.cancel_yarn_request_service import CancelYarnRequestService
from backend.features.yarn_costing.services.check_nsm_anomalies_service import CheckNsmAnomaliesService
from backend.features.yarn_costing.services.check_price_anomalies_service import CheckPriceAnomaliesService
from backend.features.yarn_costing.services.check_request_submit_service import CheckRequestSubmitService
from backend.features.yarn_costing.services.correct_yarn_nsm_service import CorrectYarnNsmService
from backend.features.yarn_costing.services.create_adjustment_line_service import CreateAdjustmentLineService
from backend.features.yarn_costing.services.create_nsm_revision_service import CreateNsmRevisionService
from backend.features.yarn_costing.services.create_primary_loss_group_service import CreatePrimaryLossGroupService
from backend.features.yarn_costing.services.create_secondary_loss_group_service import CreateSecondaryLossGroupService
from backend.features.yarn_costing.services.create_yarn_request_service import CreateYarnRequestService
from backend.features.yarn_costing.services.delete_adjustment_line_service import DeleteAdjustmentLineService
from backend.features.yarn_costing.services.delete_loss_group_service import DeleteLossGroupService
from backend.features.yarn_costing.services.download_component_template_service import (
    DownloadComponentTemplateService,
)
from backend.features.yarn_costing.services.download_template_service import DownloadTemplateService
from backend.features.yarn_costing.services.export_price_lines_service import ExportPriceLinesService
from backend.features.yarn_costing.services.get_dashboard_service import GetDashboardService
from backend.features.yarn_costing.services.get_legacy_comparison_service import GetLegacyComparisonService
from backend.features.yarn_costing.services.get_recalc_diff_service import GetRecalcDiffService
from backend.features.yarn_costing.services.get_reference_data_service import GetReferenceDataService
from backend.features.yarn_costing.services.get_yarn_detail_service import GetYarnDetailService
from backend.features.yarn_costing.services.import_component_file_service import ImportComponentFileService
from backend.features.yarn_costing.services.import_workbook_service import ImportWorkbookService
from backend.features.yarn_costing.services.list_audit_log_service import ListAuditLogService
from backend.features.yarn_costing.services.list_import_batches_service import ListImportBatchesService
from backend.features.yarn_costing.services.list_loss_groups_service import ListLossGroupsService
from backend.features.yarn_costing.services.list_price_lines_service import ListPriceLinesService
from backend.features.yarn_costing.services.list_recalc_batches_service import ListRecalcBatchesService
from backend.features.yarn_costing.services.list_yarns_service import ListYarnsService
from backend.features.yarn_costing.services.recalculate_not_priced_service import RecalculateNotPricedService
from backend.features.yarn_costing.services.reject_yarn_request_service import RejectYarnRequestService
from backend.features.yarn_costing.services.save_packaging_types_service import SavePackagingTypesService
from backend.features.yarn_costing.services.save_process_routes_service import SaveProcessRoutesService
from backend.features.yarn_costing.services.save_recovery_rates_service import SaveRecoveryRatesService
from backend.features.yarn_costing.services.save_stage_config_service import SaveStageConfigService
from backend.features.yarn_costing.services.save_user_group_service import SaveUserGroupService
from backend.features.yarn_costing.services.save_yarn_nsm_service import SaveYarnNsmService
from backend.features.yarn_costing.services.set_accounting_code_service import SetAccountingCodeService
from backend.features.yarn_costing.services.suggest_nsm_service import SuggestNsmService
from backend.features.yarn_costing.services.update_loss_group_service import UpdateLossGroupService
from backend.features.yarn_costing.services.update_trial_factor_service import UpdateTrialFactorService
from backend.features.yarn_costing.services.update_yarn_request_service import UpdateYarnRequestService
from backend.features.yarn_costing.services.verify_actor_service import VerifyActorService


class YarnCostingController(BaseController):
    def save_user_group(self, request: SaveUserGroupRequest) -> UserGroupResponse:
        """UC-01 Khai báo nhóm người dùng và thành viên."""
        return SaveUserGroupService().handle(request)

    def list_audit_log(self, request: ListAuditLogRequest) -> AuditLogListResponse:
        """UC-02 Xem nhật ký thay đổi."""
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

    def list_yarns(self, request: ListYarnsRequest) -> YarnListResponse:
        """UC-19 Xem danh sách yêu cầu."""
        return ListYarnsService().handle(request)

    def suggest_nsm(self, request: SuggestNsmRequest) -> NsmSuggestionResponse:
        """UC-20 Lấy NSM gợi ý (tự điền)."""
        return SuggestNsmService().handle(request)

    def save_yarn_nsm(self, request: SaveYarnNsmRequest) -> PricingResultResponse:
        """UC-21 Nhập NSM, kiểm tra và lưu giá."""
        return SaveYarnNsmService().handle(request)

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

    def list_price_lines(self, request: ListPriceLinesRequest) -> PriceLineListResponse:
        """UC-27 Tra cứu bảng giá."""
        return ListPriceLinesService().handle(request)

    def set_accounting_code(self, request: SetAccountingCodeRequest) -> PriceLineResponse:
        """UC-28 Nhập / sửa / xoá mã kế toán."""
        return SetAccountingCodeService().handle(request)

    def export_price_lines(self, request: ExportPriceLinesRequest) -> FileDownloadDTO:
        """UC-29 Xuất Excel bảng giá."""
        return ExportPriceLinesService().handle(request)

    def check_price_anomalies(self, request: CheckPriceAnomaliesRequest) -> PriceAnomalyResponse:
        """UC-30 Kiểm tra giá bất thường."""
        return CheckPriceAnomaliesService().handle(request)

    def check_nsm_anomalies(self, request: CheckNsmAnomaliesRequest) -> NsmAnomalyResponse:
        """UC-31 Kiểm tra NSM bất thường."""
        return CheckNsmAnomaliesService().handle(request)

    def get_dashboard(self, request: GetDashboardRequest) -> DashboardResponse:
        """UC-32 Xem dashboard."""
        return GetDashboardService().handle(request)

    def download_template(self, request: DownloadTemplateRequest) -> FileDownloadDTO:
        """UC-33 Tải file mẫu."""
        return DownloadTemplateService().handle(request)

    def import_workbook(self, request: ImportWorkbookRequest) -> ImportResultResponse:
        """UC-34 Kiểm tra và lưu dữ liệu từ file."""
        return ImportWorkbookService().handle(request)

    def get_legacy_comparison(self, request: GetLegacyComparisonRequest) -> LegacyComparisonResponse:
        """UC-35 Đối chiếu giá cũ với giá app."""
        return GetLegacyComparisonService().handle(request)

    def list_recalc_batches(self, request: ListRecalcBatchesRequest) -> RecalcBatchListResponse:
        """UC-36 Xem danh sách lần tính lại toàn bộ."""
        return ListRecalcBatchesService().handle(request)

    def get_recalc_diff(self, request: GetRecalcDiffRequest) -> RecalcDiffResponse:
        """UC-37 Xem chênh lệch của một lần tính lại."""
        return GetRecalcDiffService().handle(request)

    def get_reference_data(self, request: GetReferenceDataRequest) -> ReferenceDataResponse:
        """UC-38 Lấy dữ liệu tham chiếu."""
        return GetReferenceDataService().handle(request)

    def verify_actor(self, request: VerifyActorRequest) -> ActorResponse:
        """UC-39 Xác thực người thao tác."""
        return VerifyActorService().handle(request)

    def analyze_yarn_name(self, request: AnalyzeYarnNameRequest) -> YarnNameAnalysisResponse:
        """UC-40 Nhận diện tên sợi."""
        return AnalyzeYarnNameService().handle(request)

    def list_import_batches(self, request: ListImportBatchesRequest) -> ImportBatchListResponse:
        """UC-41 Xem danh sách lần nhập file."""
        return ListImportBatchesService().handle(request)

    def check_request_submit(self, request: CheckRequestSubmitRequest) -> RequestSubmitCheckResponse:
        """UC-42 Kiểm tra điều kiện gửi yêu cầu."""
        return CheckRequestSubmitService().handle(request)

    def recalculate_not_priced(self, request: RecalculateNotPricedRequest) -> RecalcResultResponse:
        """UC-43 Tính lại các mã chưa tính được."""
        return RecalculateNotPricedService().handle(request)

    def download_component_template(self, request: DownloadComponentTemplateRequest) -> FileDownloadDTO:
        """UC-44 Tải file mẫu khai báo thành phần sợi pha."""
        return DownloadComponentTemplateService().handle(request)

    def import_component_file(self, request: ImportComponentFileRequest) -> ComponentImportResponse:
        """UC-45 Kiểm tra và lưu file khai báo thành phần sợi pha."""
        return ImportComponentFileService().handle(request)
