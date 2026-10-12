"""UC-33 Tải file mẫu (5.3) với dữ liệu hiện tại của xưởng."""

from backend.core.base import BaseService, FileDownloadDTO
from backend.features.yarn_costing.builders.template_file_builder import TemplateFileBuilder
from backend.features.yarn_costing.dto.import_dto import DownloadTemplateRequest
from backend.features.yarn_costing.models.enums import YarnStatus
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.packaging_type_repository import PackagingTypeRepository
from backend.features.yarn_costing.repositories.process_route_repository import ProcessRouteRepository
from backend.features.yarn_costing.repositories.rate_version_repository import RateVersionRepository
from backend.features.yarn_costing.repositories.recovery_rate_repository import RecoveryRateRepository
from backend.features.yarn_costing.repositories.stage_repository import StageRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

WITH_NSM = (YarnStatus.DA_TINH_GIA, YarnStatus.CO_MA_KE_TOAN, YarnStatus.CHUA_TINH_DUOC)


class DownloadTemplateService(BaseService[DownloadTemplateRequest, FileDownloadDTO]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()

    def execute(self, request: DownloadTemplateRequest) -> FileDownloadDTO:
        f = request.factory_code
        yarns = sorted(
            (y for y in self.repository.list_all() if y.factory_code == f and y.status in WITH_NSM),
            key=lambda y: y.requested_at,
        )
        self.logger.info("Template %s with %s yarns", f, len(yarns))
        return TemplateFileBuilder(
            f,
            StageRepository().for_factory(f.value),
            RateVersionRepository().current(f.value),
            PackagingTypeRepository().for_factory(f.value),
            RecoveryRateRepository().for_factory(f.value),
            ProcessRouteRepository().for_factory(f.value),
            LossGroupRepository().for_factory(f.value),
            yarns,
        ).build()
