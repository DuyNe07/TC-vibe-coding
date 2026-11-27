"""Top layer of feature "Tính giá vải dệt". Pages call it through gateway.open(...). One method = one use case."""

from backend.core.base import BaseController, EmptyRequest, FileDownloadDTO, cached_query
from backend.features.woven_costing.dto.common_dto import (
    MessageResponse,
)
from backend.features.woven_costing.dto.costsheet_dto import (
    CostsheetActionRequest,
    CostsheetInputRequest,
    CostsheetResponse,
    CreateCostsheetRequest,
    GetCostsheetRequest,
    SaveOcRequest,
    UpdateFabricOverrideRequest,
)
from backend.features.woven_costing.dto.dyeing_job_dto import (
    CreateDyeingJobRequest,
    DyeingJobActionRequest,
    DyeingJobInputRequest,
    DyeingJobListResponse,
    DyeingJobResponse,
    GetDyeingJobRequest,
    ListDyeingJobsRequest,
)
from backend.features.woven_costing.dto.fabric_dto import (
    FabricImportLogResponse,
    FabricImportPreviewResponse,
    FabricImportSaveResponse,
    PreviewFabricImportRequest,
    PrintLabelRequest,
    SaveFabricRequest,
    SaveFabricResponse,
    SearchFabricsRequest,
    SearchFabricsResponse,
)
from backend.features.woven_costing.dto.list_dto import (
    AddCustomerRequest,
    AddCustomerResponse,
    BulkApproveRequest,
    BulkApproveResponse,
    CostsheetListResponse,
    CostsheetOptionsResponse,
    ListCostsheetsRequest,
    MyTasksResponse,
)
from backend.features.woven_costing.dto.master_dto import (
    CustomerImportRequest,
    CustomerImportResponse,
    CustomerListResponse,
    ExchangeRateListResponse,
    FabricFactorListResponse,
    HolidayListResponse,
    ListCustomersRequest,
    NormSetPreviewResponse,
    NormSetResponse,
    ParameterSetListResponse,
    SaveExchangeRateRequest,
    SaveFabricFactorRequest,
    SaveHolidayRequest,
    SaveNormSetRequest,
    SaveNormSetResponse,
    SaveParameterSetRequest,
    UpdateCustomerRequest,
    ViewNormSetRequest,
)
from backend.features.woven_costing.dto.ping_dto import PingRequest, PingResponse
from backend.features.woven_costing.services.add_customer_service import AddCustomerService
from backend.features.woven_costing.services.approve_costsheet_service import ApproveCostsheetService
from backend.features.woven_costing.services.approve_costsheets_service import ApproveCostsheetsService
from backend.features.woven_costing.services.approve_dyeing_job_service import ApproveDyeingJobService
from backend.features.woven_costing.services.approve_dyeing_jobs_service import ApproveDyeingJobsService
from backend.features.woven_costing.services.calculate_costsheet_service import CalculateCostsheetService
from backend.features.woven_costing.services.calculate_dyeing_job_service import CalculateDyeingJobService
from backend.features.woven_costing.services.cancel_costsheet_service import CancelCostsheetService
from backend.features.woven_costing.services.cancel_dyeing_job_service import CancelDyeingJobService
from backend.features.woven_costing.services.copy_costsheet_service import CopyCostsheetService
from backend.features.woven_costing.services.copy_dyeing_job_service import CopyDyeingJobService
from backend.features.woven_costing.services.create_costsheet_service import CreateCostsheetService
from backend.features.woven_costing.services.create_dyeing_job_service import CreateDyeingJobService
from backend.features.woven_costing.services.download_norm_template_service import DownloadNormTemplateService
from backend.features.woven_costing.services.export_costsheets_service import ExportCostsheetsService
from backend.features.woven_costing.services.export_dyeing_job_service import ExportDyeingJobService
from backend.features.woven_costing.services.get_costsheet_options_service import GetCostsheetOptionsService
from backend.features.woven_costing.services.get_costsheet_service import GetCostsheetService
from backend.features.woven_costing.services.get_dyeing_job_service import GetDyeingJobService
from backend.features.woven_costing.services.list_costsheets_service import ListCostsheetsService
from backend.features.woven_costing.services.list_customers_service import ListCustomersService
from backend.features.woven_costing.services.list_dyeing_jobs_service import ListDyeingJobsService
from backend.features.woven_costing.services.list_exchange_rates_service import ListExchangeRatesService
from backend.features.woven_costing.services.list_fabric_factors_service import ListFabricFactorsService
from backend.features.woven_costing.services.list_fabric_imports_service import ListFabricImportsService
from backend.features.woven_costing.services.list_holidays_service import ListHolidaysService
from backend.features.woven_costing.services.list_my_tasks_service import ListMyTasksService
from backend.features.woven_costing.services.list_parameter_sets_service import ListParameterSetsService
from backend.features.woven_costing.services.new_version_service import NewVersionService
from backend.features.woven_costing.services.ping_service import PingService
from backend.features.woven_costing.services.preview_customer_import_service import PreviewCustomerImportService
from backend.features.woven_costing.services.preview_fabric_import_service import PreviewFabricImportService
from backend.features.woven_costing.services.preview_norm_set_service import PreviewNormSetService
from backend.features.woven_costing.services.print_label_service import PrintLabelService
from backend.features.woven_costing.services.return_costsheet_service import ReturnCostsheetService
from backend.features.woven_costing.services.return_dyeing_job_service import ReturnDyeingJobService
from backend.features.woven_costing.services.save_customer_import_service import SaveCustomerImportService
from backend.features.woven_costing.services.save_draft_service import SaveDraftService
from backend.features.woven_costing.services.save_dyeing_job_service import SaveDyeingJobService
from backend.features.woven_costing.services.save_exchange_rate_service import SaveExchangeRateService
from backend.features.woven_costing.services.save_fabric_factor_service import SaveFabricFactorService
from backend.features.woven_costing.services.save_fabric_import_service import SaveFabricImportService
from backend.features.woven_costing.services.save_fabric_service import SaveFabricService
from backend.features.woven_costing.services.save_holiday_service import SaveHolidayService
from backend.features.woven_costing.services.save_norm_set_service import SaveNormSetService
from backend.features.woven_costing.services.save_oc_service import SaveOcService
from backend.features.woven_costing.services.save_parameter_set_service import SaveParameterSetService
from backend.features.woven_costing.services.search_fabrics_service import SearchFabricsService
from backend.features.woven_costing.services.submit_costsheet_service import SubmitCostsheetService
from backend.features.woven_costing.services.submit_dyeing_job_service import SubmitDyeingJobService
from backend.features.woven_costing.services.update_customer_service import UpdateCustomerService
from backend.features.woven_costing.services.update_fabric_override_service import UpdateFabricOverrideService
from backend.features.woven_costing.services.view_norm_set_service import ViewNormSetService


class WovenCostingController(BaseController):
    def ping(self, request: PingRequest) -> PingResponse:
        """Kiểm tra kết nối backend (scaffold)."""
        return PingService().handle(request)

    def preview_fabric_import(self, request: PreviewFabricImportRequest) -> FabricImportPreviewResponse:
        """UC-01 Kiểm tra dữ liệu vải Peace / WFX."""
        return PreviewFabricImportService().handle(request)

    def save_fabric_import(self, request: PreviewFabricImportRequest) -> FabricImportSaveResponse:
        """UC-02 Lưu dữ liệu vải."""
        return SaveFabricImportService().handle(request)

    def save_fabric(self, request: SaveFabricRequest) -> SaveFabricResponse:
        """UC-03 Nhập nhanh / sửa mã vải."""
        return SaveFabricService().handle(request)

    @cached_query
    def search_fabrics(self, request: SearchFabricsRequest) -> SearchFabricsResponse:
        """UC-04 Tra cứu mã vải."""
        return SearchFabricsService().handle(request)

    def save_exchange_rate(self, request: SaveExchangeRateRequest) -> MessageResponse:
        """UC-05 Cập nhật tỷ giá tháng."""
        return SaveExchangeRateService().handle(request)

    @cached_query
    def download_norm_template(self, request: EmptyRequest) -> FileDownloadDTO:
        """UC-06 Tải file mẫu bộ định mức."""
        return DownloadNormTemplateService().handle(request)

    def save_norm_set(self, request: SaveNormSetRequest) -> SaveNormSetResponse:
        """UC-07 Kiểm tra và lưu bộ định mức mới."""
        return SaveNormSetService().handle(request)

    @cached_query
    def view_norm_set(self, request: ViewNormSetRequest) -> NormSetResponse:
        """UC-08 Xem bộ định mức."""
        return ViewNormSetService().handle(request)

    def save_parameter_set(self, request: SaveParameterSetRequest) -> MessageResponse:
        """UC-09 Cập nhật bộ tham số chung."""
        return SaveParameterSetService().handle(request)

    def save_fabric_factor(self, request: SaveFabricFactorRequest) -> MessageResponse:
        """UC-10 Quản lý hệ số theo mã hàng."""
        return SaveFabricFactorService().handle(request)

    def save_holiday(self, request: SaveHolidayRequest) -> MessageResponse:
        """UC-11 Quản lý ngày lễ."""
        return SaveHolidayService().handle(request)

    def save_customer_import(self, request: CustomerImportRequest) -> CustomerImportResponse:
        """UC-12 Tải danh sách khách hàng ban đầu."""
        return SaveCustomerImportService().handle(request)

    def update_customer(self, request: UpdateCustomerRequest) -> MessageResponse:
        """UC-13 Sửa khách hàng."""
        return UpdateCustomerService().handle(request)

    def update_fabric_override(self, request: UpdateFabricOverrideRequest) -> CostsheetResponse:
        """UC-14 Sửa thông số vải trên costsheet (mã nhập tay)."""
        return UpdateFabricOverrideService().handle(request)

    def create_costsheet(self, request: CreateCostsheetRequest) -> CostsheetResponse:
        """UC-15 Tạo costsheet mới."""
        return CreateCostsheetService().handle(request)

    def calculate_costsheet(self, request: CostsheetInputRequest) -> CostsheetResponse:
        """UC-16 Tính / tính lại costsheet."""
        return CalculateCostsheetService().handle(request)

    def save_draft(self, request: CostsheetInputRequest) -> CostsheetResponse:
        """UC-17 Lưu nháp."""
        return SaveDraftService().handle(request)

    def add_customer(self, request: AddCustomerRequest) -> AddCustomerResponse:
        """UC-18 Thêm khách hàng mới."""
        return AddCustomerService().handle(request)

    def copy_costsheet(self, request: CostsheetActionRequest) -> CostsheetResponse:
        """UC-19 Sao chép costsheet."""
        return CopyCostsheetService().handle(request)

    def submit_costsheet(self, request: CostsheetActionRequest) -> CostsheetResponse:
        """UC-20 Gửi duyệt."""
        return SubmitCostsheetService().handle(request)

    def approve_costsheet(self, request: CostsheetActionRequest) -> CostsheetResponse:
        """UC-21 Duyệt costsheet."""
        return ApproveCostsheetService().handle(request)

    def return_costsheet(self, request: CostsheetActionRequest) -> CostsheetResponse:
        """UC-22 Trả lại costsheet."""
        return ReturnCostsheetService().handle(request)

    def new_version(self, request: CostsheetActionRequest) -> CostsheetResponse:
        """UC-23 Tạo phiên bản mới."""
        return NewVersionService().handle(request)

    def save_oc(self, request: SaveOcRequest) -> CostsheetResponse:
        """UC-24 Nhập / sửa OC và chốt đơn."""
        return SaveOcService().handle(request)

    def cancel_costsheet(self, request: CostsheetActionRequest) -> CostsheetResponse:
        """UC-25 Hủy costsheet."""
        return CancelCostsheetService().handle(request)

    def print_label(self, request: PrintLabelRequest) -> FileDownloadDTO:
        """UC-26 In nhãn thông số vải."""
        return PrintLabelService().handle(request)

    def list_costsheets(self, request: ListCostsheetsRequest) -> CostsheetListResponse:
        """UC-27 Danh sách costsheet."""
        return ListCostsheetsService().handle(request)

    def export_costsheets(self, request: ListCostsheetsRequest) -> FileDownloadDTO:
        """UC-28 Xuất danh sách costsheet ra Excel."""
        return ExportCostsheetsService().handle(request)

    def get_costsheet(self, request: GetCostsheetRequest) -> CostsheetResponse:
        """UC-29 Xem costsheet."""
        return GetCostsheetService().handle(request)

    def list_my_tasks(self, request: EmptyRequest) -> MyTasksResponse:
        """UC-30 Việc chờ tôi."""
        return ListMyTasksService().handle(request)

    @cached_query
    def list_exchange_rates(self, request: EmptyRequest) -> ExchangeRateListResponse:
        """UC-31 Xem danh sách tỷ giá."""
        return ListExchangeRatesService().handle(request)

    @cached_query
    def list_parameter_sets(self, request: EmptyRequest) -> ParameterSetListResponse:
        """UC-32 Xem các bộ tham số chung."""
        return ListParameterSetsService().handle(request)

    @cached_query
    def list_fabric_factors(self, request: EmptyRequest) -> FabricFactorListResponse:
        """UC-33 Xem hệ số theo mã hàng."""
        return ListFabricFactorsService().handle(request)

    @cached_query
    def list_holidays(self, request: EmptyRequest) -> HolidayListResponse:
        """UC-34 Xem ngày lễ."""
        return ListHolidaysService().handle(request)

    @cached_query
    def list_customers(self, request: ListCustomersRequest) -> CustomerListResponse:
        """UC-35 Tra cứu khách hàng."""
        return ListCustomersService().handle(request)

    def preview_customer_import(self, request: CustomerImportRequest) -> CustomerImportResponse:
        """UC-36 Xem trước danh sách khách hàng (chưa lưu)."""
        return PreviewCustomerImportService().handle(request)

    def preview_norm_set(self, request: SaveNormSetRequest) -> NormSetPreviewResponse:
        """UC-37 Kiểm tra bộ định mức (chưa lưu)."""
        return PreviewNormSetService().handle(request)

    def get_costsheet_options(self, request: EmptyRequest) -> CostsheetOptionsResponse:
        """UC-38 Lấy danh mục cho costsheet."""
        return GetCostsheetOptionsService().handle(request)

    @cached_query
    def list_fabric_imports(self, request: EmptyRequest) -> FabricImportLogResponse:
        """UC-39 Xem lịch sử cập nhật dữ liệu vải."""
        return ListFabricImportsService().handle(request)

    # ---- 2026-11-25 dyeing job order ("phiếu gia công nhuộm", Screen 8) -------------------------------------------
    def create_dyeing_job(self, request: CreateDyeingJobRequest) -> DyeingJobResponse:
        """UC-40 Tạo phiếu gia công nhuộm."""
        return CreateDyeingJobService().handle(request)

    def calculate_dyeing_job(self, request: DyeingJobInputRequest) -> DyeingJobResponse:
        """UC-41 Tính phiếu gia công nhuộm (chưa lưu)."""
        return CalculateDyeingJobService().handle(request)

    def save_dyeing_job(self, request: DyeingJobInputRequest) -> DyeingJobResponse:
        """UC-42 Lưu nháp phiếu gia công nhuộm."""
        return SaveDyeingJobService().handle(request)

    def submit_dyeing_job(self, request: DyeingJobActionRequest) -> DyeingJobResponse:
        """UC-43 Gửi duyệt phiếu gia công nhuộm."""
        return SubmitDyeingJobService().handle(request)

    def approve_dyeing_job(self, request: DyeingJobActionRequest) -> DyeingJobResponse:
        """UC-43 Duyệt phiếu gia công nhuộm."""
        return ApproveDyeingJobService().handle(request)

    def return_dyeing_job(self, request: DyeingJobActionRequest) -> DyeingJobResponse:
        """UC-43 Trả lại phiếu gia công nhuộm."""
        return ReturnDyeingJobService().handle(request)

    def cancel_dyeing_job(self, request: DyeingJobActionRequest) -> DyeingJobResponse:
        """UC-43 Hủy phiếu gia công nhuộm."""
        return CancelDyeingJobService().handle(request)

    def list_dyeing_jobs(self, request: ListDyeingJobsRequest) -> DyeingJobListResponse:
        """UC-44 Danh sách phiếu gia công nhuộm."""
        return ListDyeingJobsService().handle(request)

    def get_dyeing_job(self, request: GetDyeingJobRequest) -> DyeingJobResponse:
        """UC-44 Xem phiếu gia công nhuộm."""
        return GetDyeingJobService().handle(request)

    def copy_dyeing_job(self, request: DyeingJobActionRequest) -> DyeingJobResponse:
        """UC-45 Sao chép phiếu gia công nhuộm."""
        return CopyDyeingJobService().handle(request)

    def export_dyeing_job(self, request: GetDyeingJobRequest) -> FileDownloadDTO:
        """UC-46 Xuất bảng giá gia công nhuộm ra Excel."""
        return ExportDyeingJobService().handle(request)

    def approve_costsheets(self, request: BulkApproveRequest) -> BulkApproveResponse:
        """UC-47 Duyệt nhiều costsheet một lần (2026-11-27)."""
        return ApproveCostsheetsService().handle(request)

    def approve_dyeing_jobs(self, request: BulkApproveRequest) -> BulkApproveResponse:
        """UC-48 Duyệt nhiều phiếu gia công nhuộm một lần (2026-11-27)."""
        return ApproveDyeingJobsService().handle(request)
