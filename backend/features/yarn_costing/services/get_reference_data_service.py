"""UC-38 Lấy dữ liệu tham chiếu (danh sách chọn, khối xác thực, thẻ dữ liệu nền); BR-61 file mã sợi hỏng -> cảnh báo."""

from datetime import date

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.dto_builders import (
    exchange_rate_dto,
    factory_dto,
    group_dto,
    packaging_row,
    rate_version_dto,
    recovery_row,
    route_row,
    stage_row,
)
from backend.features.yarn_costing.business.costing_business import CostingBusiness
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest, ReferenceDataResponse
from backend.features.yarn_costing.exceptions import DataFileError
from backend.features.yarn_costing.models.enums import FactoryCode
from backend.features.yarn_costing.repositories.exchange_rate_repository import (
    ExchangeRateRepository,
    SettingsRepository,
)
from backend.features.yarn_costing.repositories.packaging_type_repository import PackagingTypeRepository
from backend.features.yarn_costing.repositories.process_route_repository import ProcessRouteRepository
from backend.features.yarn_costing.repositories.rate_version_repository import RateVersionRepository
from backend.features.yarn_costing.repositories.recovery_rate_repository import RecoveryRateRepository
from backend.features.yarn_costing.repositories.stage_repository import StageRepository
from backend.features.yarn_costing.repositories.user_group_repository import UserGroupRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository


class GetReferenceDataService(BaseService[GetReferenceDataRequest, ReferenceDataResponse]):
    def __init__(self, repository: UserGroupRepository | None = None) -> None:
        self.repository = repository or UserGroupRepository()
        self.costing = CostingBusiness()
        self.master = MasterBusiness()

    def execute(self, request: GetReferenceDataRequest) -> ReferenceDataResponse:
        factories = [request.factory_code] if request.factory_code else list(FactoryCode)
        codes = {f.value for f in factories}
        version_repo = RateVersionRepository()
        stages, versions, packaging, recovery, routes = [], [], [], [], []
        current = None
        stage_repo, packaging_repo = StageRepository(), PackagingTypeRepository()
        factory_dtos = []
        for f in FactoryCode:
            factory_stages = stage_repo.for_factory(f.value)
            factory_version = version_repo.current(f.value)
            default = self.master.default_packaging(packaging_repo.for_factory(f.value), factory_version)
            carding = [s.stage_code for s in factory_stages if s.is_carding]
            factory_dtos.append(factory_dto(f, carding, default))
        for f in factories:
            stages += [stage_row(s) for s in stage_repo.for_factory(f.value)]
            factory_versions = version_repo.for_factory(f.value)
            versions += [rate_version_dto(v) for v in factory_versions]
            version = factory_versions[0] if factory_versions else None
            if request.factory_code is not None and version is not None:
                current = rate_version_dto(version)
            for p in packaging_repo.for_factory(f.value):
                has_rate = version is not None and version.line_for(p.code) is not None
                packaging.append(packaging_row(p, has_rate, self.master.is_selectable(p, version)))
            recovery += [recovery_row(r) for r in RecoveryRateRepository().for_factory(f.value)]
            routes += [route_row(r) for r in ProcessRouteRepository().for_factory(f.value)]
        rates = ExchangeRateRepository().list_ordered()
        current_rate = self.costing.current_exchange_rate(rates, date.today())
        warnings: list[str] = []
        try:
            yarns = YarnRepository().list_all()
        except DataFileError as exc:  # BR-61: the other reference data stays usable
            self.logger.warning("Reference data without yarn groups: %s", exc.message)
            warnings.append(exc.message)
            yarns = []
        yarn_groups = sorted({y.yarn_group for y in yarns if y.factory_code.value in codes and y.yarn_group})
        self.logger.info(
            "Reference data for %s: %s stages, %s packaging types",
            request.factory_code or "S1+S4",
            len(stages),
            len(packaging),
        )
        return ReferenceDataResponse(
            groups=[group_dto(g) for g in self.repository.list_ordered()],
            factories=factory_dtos,
            stages=stages,
            current_rate=current,
            rate_versions=versions,
            packaging=packaging,
            recovery=recovery,
            routes=routes,
            exchange_rates=[exchange_rate_dto(r) for r in rates],
            current_exchange_rate=exchange_rate_dto(current_rate) if current_rate else None,
            trial_factor=SettingsRepository().get_settings().trial_factor,
            yarn_groups=yarn_groups,
            data_warnings=warnings,
        )
