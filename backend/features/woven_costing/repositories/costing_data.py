"""Loads every stored table a costsheet calculation needs (one place for the costsheet services)."""

from backend.features.woven_costing.models.costing_data import CostingData
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.costsheet_view import CostsheetView
from backend.features.woven_costing.models.parameter_set import ParameterValues
from backend.features.woven_costing.repositories.costsheet_repository import (
    CostsheetHistoryRepository,
    CostsheetRepository,
)
from backend.features.woven_costing.repositories.fabric_repository import FabricRepository
from backend.features.woven_costing.repositories.master_repository import (
    ExchangeRateRepository,
    FabricFactorRepository,
    HolidayRepository,
)
from backend.features.woven_costing.repositories.norm_repository import NormSetRepository, ParameterSetRepository


def load_costing_data(tcfno: str) -> CostingData:
    return CostingData(
        fabric=FabricRepository().by_tcfno(tcfno) if tcfno else None,
        rates=ExchangeRateRepository().list_all(),
        norm_sets=NormSetRepository().list_with_seed(),
        parameter_sets=ParameterSetRepository().list_with_seed(),
        factors=[f for f in FabricFactorRepository().list_with_seed() if f.tcfno == tcfno],
        holidays=HolidayRepository().list_all(),
    )


def load_costsheet_view(sheet: Costsheet) -> CostsheetView:
    """Versions, history, the default parameter values of the costing date and the current fabric source."""
    params = ParameterSetRepository().effective_on(sheet.costing_date)
    fabric = FabricRepository().by_tcfno(sheet.tcfno)
    return CostsheetView(
        versions=CostsheetRepository().versions(sheet.costsheet_no) or [sheet],
        history=CostsheetHistoryRepository().of_costsheet(sheet.costsheet_no),
        defaults=params.values if params else ParameterValues(),
        fabric_source=fabric.source if fabric else None,
    )
