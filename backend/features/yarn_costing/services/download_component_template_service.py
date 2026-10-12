"""UC-44 Tải file mẫu khai báo thành phần sợi pha (5.7)."""

from collections import Counter

from backend.core.base import BaseService, FileDownloadDTO
from backend.features.yarn_costing.builders.component_file_builder import ComponentTemplateBuilder
from backend.features.yarn_costing.dto.import_dto import DownloadComponentTemplateRequest
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class DownloadComponentTemplateService(BaseService[DownloadComponentTemplateRequest, FileDownloadDTO]):
    def __init__(self, repository: LossGroupRepository | None = None) -> None:
        self.repository = repository or LossGroupRepository()

    def execute(self, request: DownloadComponentTemplateRequest) -> FileDownloadDTO:
        factory = request.factory_code
        groups = self.repository.for_factory(factory.value)
        usage = Counter(y.loss_group_key for y in YarnRepository().list_all() if y.factory_code == factory)
        file = ComponentTemplateBuilder(factory, groups, dict(usage)).build()
        self.logger.info("Component template %s: %s loss groups", factory, len(groups))
        return file
