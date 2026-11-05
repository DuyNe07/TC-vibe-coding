"""UC-03: upload history, newest first."""

from backend.core.base import BaseService, EmptyRequest
from backend.features.sewing_productivity.builders.upload_response_builders import UploadLogListBuilder
from backend.features.sewing_productivity.business.access_rules import AccessBusiness
from backend.features.sewing_productivity.dto.upload_dto import UploadLogListResponse
from backend.features.sewing_productivity.repositories.source_repositories import UploadLogRepository


class ListUploadLogsService(BaseService[EmptyRequest, UploadLogListResponse]):
    def __init__(self, repository: UploadLogRepository | None = None) -> None:
        self.repository = repository or UploadLogRepository()
        self.access = AccessBusiness()

    def execute(self, request: EmptyRequest) -> UploadLogListResponse:
        self.access.ensure_valid(self.current_user)
        logs = self.repository.list_all()
        self.logger.info("Listed %s upload logs", len(logs))
        return UploadLogListBuilder(logs).build()
