"""Loads everything the price calculation needs for one factory, reading each storage file once."""

from backend.features.yarn_costing.models.costing import FactoryData
from backend.features.yarn_costing.models.enums import FactoryCode
from backend.features.yarn_costing.repositories.exchange_rate_repository import SettingsRepository
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.packaging_type_repository import PackagingTypeRepository
from backend.features.yarn_costing.repositories.process_route_repository import ProcessRouteRepository
from backend.features.yarn_costing.repositories.rate_version_repository import RateVersionRepository
from backend.features.yarn_costing.repositories.recovery_rate_repository import RecoveryRateRepository
from backend.features.yarn_costing.repositories.stage_repository import StageRepository


def load_factory_data(factory_code: FactoryCode) -> FactoryData:
    """Stages, current rate version, packaging, recovery rates, loss groups, routes and trial factor of a factory."""
    code = factory_code.value
    version = RateVersionRepository().current(code)
    return FactoryData(
        factory_code=factory_code,
        stages=StageRepository().for_factory(code),
        recovery={r.recovery_type.value: r.rate for r in RecoveryRateRepository().for_factory(code)},
        rate_version=version,
        rates={line.rate_code: line for line in version.lines} if version else {},
        packaging={p.code: p for p in PackagingTypeRepository().for_factory(code)},
        loss_groups={g.group_key: g for g in LossGroupRepository().for_factory(code)},
        routes=ProcessRouteRepository().for_factory(code),
        trial_factor=SettingsRepository().get_settings().trial_factor,
    )
