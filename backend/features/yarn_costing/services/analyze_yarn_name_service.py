"""UC-40 Nhận diện tên sợi (BR-01..BR-04, BR-06), không lưu gì."""

from backend.core.base import BaseService
from backend.features.yarn_costing.business.name_business import YarnNameBusiness, YarnNameRule, collapse_spaces
from backend.features.yarn_costing.business.request_business import DuplicateNameRule
from backend.features.yarn_costing.dto.request_dto import AnalyzeYarnNameRequest, YarnNameAnalysisResponse
from backend.features.yarn_costing.models.yarn import Yarn
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class AnalyzeYarnNameService(BaseService[AnalyzeYarnNameRequest, YarnNameAnalysisResponse]):
    def __init__(self, repository: YarnRepository | None = None) -> None:
        self.repository = repository or YarnRepository()
        self.names = YarnNameBusiness()

    def execute(self, request: AnalyzeYarnNameRequest) -> YarnNameAnalysisResponse:
        name = collapse_spaces(request.yarn_name)
        parsed = self.names.analyze(name)
        if not parsed.valid:
            return YarnNameAnalysisResponse(valid=False, message=YarnNameRule.message if name else "")
        exists = any(
            g.group_key == parsed.loss_group_key for g in LossGroupRepository().for_factory(request.factory_code.value)
        )
        probe = Yarn(factory_code=request.factory_code, yarn_code="?", base_code="?", yarn_name=name)
        duplicate = DuplicateNameRule(self.repository.list_all()).duplicate_of(probe)
        message = (
            "" if exists else f"Nhóm tiêu hao '{parsed.loss_group_key}' chưa có ở xưởng {request.factory_code.value}."
        )
        if duplicate is not None:
            message = DuplicateNameRule(self.repository.list_all()).describe_violation(probe)
        self.logger.info("Yarn name analysed: %r -> %s (loss group exists=%s)", name, parsed.loss_group_key, exists)
        return YarnNameAnalysisResponse(
            valid=True,
            message=message,
            yarn_group=parsed.yarn_group,
            count=parsed.count,
            technology=self.names.technology(name),
            is_compact=parsed.is_compact,
            loss_group_key=parsed.loss_group_key,
            loss_group_exists=exists,
            duplicate_code=duplicate.yarn_code if duplicate else None,
        )
