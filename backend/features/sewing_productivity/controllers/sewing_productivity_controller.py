"""Top layer of feature "Năng suất xưởng may". Pages call it through gateway.open(...).

One method = one use case = one service.
"""

from backend.core.base import BaseController, EmptyRequest, FileDownloadDTO, cached_query
from backend.features.sewing_productivity.dto.catalog_dto import (
    CatalogsResponse,
    SaveCatalogResponse,
    SaveCustomerGroupsRequest,
    SaveLineMappingsRequest,
    SaveProductGroupsRequest,
    SaveStyleProductsRequest,
)
from backend.features.sewing_productivity.dto.changeover_dto import (
    ChangeoverRequest,
    ChangeoverResponse,
)
from backend.features.sewing_productivity.dto.daily_dto import (
    DailyReportRequest,
    DailyReportResponse,
)
from backend.features.sewing_productivity.dto.export_dto import (
    ExportDailyRequest,
    ExportWeeklyRequest,
)
from backend.features.sewing_productivity.dto.filter_dto import (
    FilterOptionsResponse,
)
from backend.features.sewing_productivity.dto.goal_dto import (
    GoalListResponse,
    SaveGoalRequest,
    SaveGoalResponse,
)
from backend.features.sewing_productivity.dto.line_detail_dto import (
    LineDetailRequest,
    LineDetailResponse,
)
from backend.features.sewing_productivity.dto.line_mo_dto import (
    LineMoRequest,
    LineMoResponse,
)
from backend.features.sewing_productivity.dto.monthly_dto import (
    MonthlyReportRequest,
    MonthlyReportResponse,
)
from backend.features.sewing_productivity.dto.overview_dto import (
    ChartsRequest,
    ChartsResponse,
    OverviewRequest,
    OverviewResponse,
)
from backend.features.sewing_productivity.dto.upload_dto import (
    CheckUploadRequest,
    SaveUploadRequest,
    SaveUploadResponse,
    UploadCheckResponse,
    UploadLogListResponse,
)
from backend.features.sewing_productivity.dto.weekly_changeover_dto import (
    DeleteWeeklyChangeoverRequest,
    DeleteWeeklyChangeoverResponse,
    SaveWeeklyChangeoversRequest,
    SaveWeeklyChangeoversResponse,
    WeeklyChangeoverListResponse,
)
from backend.features.sewing_productivity.services.check_upload_service import CheckUploadService
from backend.features.sewing_productivity.services.delete_weekly_changeover_service import DeleteWeeklyChangeoverService
from backend.features.sewing_productivity.services.export_changeover_service import ExportChangeoverService
from backend.features.sewing_productivity.services.export_daily_report_service import ExportDailyReportService
from backend.features.sewing_productivity.services.export_line_mo_service import ExportLineMoService
from backend.features.sewing_productivity.services.export_monthly_report_service import ExportMonthlyReportService
from backend.features.sewing_productivity.services.export_weekly_report_service import ExportWeeklyReportService
from backend.features.sewing_productivity.services.get_catalogs_service import GetCatalogsService
from backend.features.sewing_productivity.services.get_changeover_service import GetChangeoverService
from backend.features.sewing_productivity.services.get_charts_service import GetChartsService
from backend.features.sewing_productivity.services.get_daily_report_service import GetDailyReportService
from backend.features.sewing_productivity.services.get_filter_options_service import GetFilterOptionsService
from backend.features.sewing_productivity.services.get_line_detail_service import GetLineDetailService
from backend.features.sewing_productivity.services.get_line_mo_service import GetLineMoService
from backend.features.sewing_productivity.services.get_monthly_report_service import GetMonthlyReportService
from backend.features.sewing_productivity.services.get_overview_service import GetOverviewService
from backend.features.sewing_productivity.services.list_goals_service import ListGoalsService
from backend.features.sewing_productivity.services.list_upload_logs_service import ListUploadLogsService
from backend.features.sewing_productivity.services.list_weekly_changeovers_service import ListWeeklyChangeoversService
from backend.features.sewing_productivity.services.save_customer_groups_service import SaveCustomerGroupsService
from backend.features.sewing_productivity.services.save_goal_service import SaveGoalService
from backend.features.sewing_productivity.services.save_line_mappings_service import SaveLineMappingsService
from backend.features.sewing_productivity.services.save_product_groups_service import SaveProductGroupsService
from backend.features.sewing_productivity.services.save_style_products_service import SaveStyleProductsService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.services.save_weekly_changeovers_service import SaveWeeklyChangeoversService


class SewingProductivityController(BaseController):
    def check_upload(self, request: CheckUploadRequest) -> UploadCheckResponse:
        """UC-01 Kiểm tra file dữ liệu."""
        return CheckUploadService().handle(request)

    def save_upload(self, request: SaveUploadRequest) -> SaveUploadResponse:
        """UC-02 Lưu dữ liệu từ file."""
        return SaveUploadService().handle(request)

    def list_upload_logs(self, request: EmptyRequest) -> UploadLogListResponse:
        """UC-03 Xem lịch sử tải file."""
        return ListUploadLogsService().handle(request)

    @cached_query
    def get_overview(self, request: OverviewRequest) -> OverviewResponse:
        """UC-04 Xem tổng quan xưởng."""
        return GetOverviewService().handle(request)

    @cached_query
    def get_charts(self, request: ChartsRequest) -> ChartsResponse:
        """UC-05 Xem biểu đồ."""
        return GetChartsService().handle(request)

    @cached_query
    def get_line_detail(self, request: LineDetailRequest) -> LineDetailResponse:
        """UC-06 Xem chi tiết chuyền."""
        return GetLineDetailService().handle(request)

    @cached_query
    def get_daily_report(self, request: DailyReportRequest) -> DailyReportResponse:
        """UC-07 Xem báo cáo ngày."""
        return GetDailyReportService().handle(request)

    @cached_query
    def get_monthly_report(self, request: MonthlyReportRequest) -> MonthlyReportResponse:
        """UC-08 Xem báo cáo tháng."""
        return GetMonthlyReportService().handle(request)

    @cached_query
    def get_line_mo(self, request: LineMoRequest) -> LineMoResponse:
        """UC-09 Xem MO theo chuyền."""
        return GetLineMoService().handle(request)

    @cached_query
    def get_changeover(self, request: ChangeoverRequest) -> ChangeoverResponse:
        """UC-10 Xem đổi mã hàng."""
        return GetChangeoverService().handle(request)

    @cached_query
    def export_weekly_report(self, request: ExportWeeklyRequest) -> FileDownloadDTO:
        """UC-11 Tải Excel báo cáo tuần."""
        return ExportWeeklyReportService().handle(request)

    @cached_query
    def export_daily_report(self, request: ExportDailyRequest) -> FileDownloadDTO:
        """UC-12 Tải Excel báo cáo ngày."""
        return ExportDailyReportService().handle(request)

    @cached_query
    def export_monthly_report(self, request: MonthlyReportRequest) -> FileDownloadDTO:
        """UC-13 Tải Excel báo cáo tháng."""
        return ExportMonthlyReportService().handle(request)

    @cached_query
    def export_line_mo(self, request: LineMoRequest) -> FileDownloadDTO:
        """UC-14 Tải Excel MO theo chuyền."""
        return ExportLineMoService().handle(request)

    @cached_query
    def export_changeover(self, request: ChangeoverRequest) -> FileDownloadDTO:
        """UC-15 Tải Excel đổi mã hàng."""
        return ExportChangeoverService().handle(request)

    def list_goals(self, request: EmptyRequest) -> GoalListResponse:
        """UC-16 Xem mục tiêu và ngưỡng."""
        return ListGoalsService().handle(request)

    def save_goal(self, request: SaveGoalRequest) -> SaveGoalResponse:
        """UC-17 Lưu mục tiêu và ngưỡng."""
        return SaveGoalService().handle(request)

    def list_weekly_changeovers(self, request: EmptyRequest) -> WeeklyChangeoverListResponse:
        """UC-18 Xem đổi mã hàng tuần đã nhập."""
        return ListWeeklyChangeoversService().handle(request)

    def save_weekly_changeovers(self, request: SaveWeeklyChangeoversRequest) -> SaveWeeklyChangeoversResponse:
        """UC-19 Lưu đổi mã hàng tuần."""
        return SaveWeeklyChangeoversService().handle(request)

    def delete_weekly_changeover(self, request: DeleteWeeklyChangeoverRequest) -> DeleteWeeklyChangeoverResponse:
        """UC-20 Xoá số đổi mã hàng tuần."""
        return DeleteWeeklyChangeoverService().handle(request)

    def get_catalogs(self, request: EmptyRequest) -> CatalogsResponse:
        """UC-21 Xem danh mục."""
        return GetCatalogsService().handle(request)

    def save_product_groups(self, request: SaveProductGroupsRequest) -> SaveCatalogResponse:
        """UC-22 Lưu nhóm sản phẩm."""
        return SaveProductGroupsService().handle(request)

    def save_customer_groups(self, request: SaveCustomerGroupsRequest) -> SaveCatalogResponse:
        """UC-23 Lưu nhóm khách hàng."""
        return SaveCustomerGroupsService().handle(request)

    def save_line_mappings(self, request: SaveLineMappingsRequest) -> SaveCatalogResponse:
        """UC-24 Lưu bảng số chuyền Fac 1."""
        return SaveLineMappingsService().handle(request)

    def save_style_products(self, request: SaveStyleProductsRequest) -> SaveCatalogResponse:
        """UC-25 Lưu tên sản phẩm theo style."""
        return SaveStyleProductsService().handle(request)

    @cached_query
    def get_filter_options(self, request: EmptyRequest) -> FilterOptionsResponse:
        """UC-26 Lấy lựa chọn bộ lọc và thời gian mặc định."""
        return GetFilterOptionsService().handle(request)
