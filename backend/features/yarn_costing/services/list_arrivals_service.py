"""UC-61 (đợt 2): danh sách lô hàng sắp về, khai báo nhóm của các cặp nhà cung cấp + mô tả, các lần nhập file."""

from decimal import Decimal

from backend.core.base import BaseService
from backend.features.yarn_costing.builders.material_dto_builders import group_dto
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.material_stock_business import MaterialStockBusiness
from backend.features.yarn_costing.dto.material_dto import (
    ArrivalImportDTO,
    ArrivalListResponse,
    ArrivalLotDTO,
    ArrivalMappingDTO,
    ListArrivalsRequest,
)
from backend.features.yarn_costing.models.enums import MaterialDecision, MaterialMarket
from backend.features.yarn_costing.repositories.material_price_repository import (
    ArrivalImportRepository,
    ArrivalLotRepository,
    ArrivalMappingRepository,
    MaterialPriceGroupRepository,
)

USE_CASE = "UC-61"


class ListArrivalsService(BaseService[ListArrivalsRequest, ArrivalListResponse]):
    def execute(self, request: ListArrivalsRequest) -> ArrivalListResponse:
        AccessBusiness().ensure_material_access(self.current_user, USE_CASE)
        business = MaterialStockBusiness()
        groups = {g.id: g for g in MaterialPriceGroupRepository().list_all()}
        mappings = ArrivalMappingRepository().by_key()
        all_lots = sorted(ArrivalLotRepository().list_all(), key=lambda lot: (lot.eta_warehouse, lot.supplier))
        months = sorted({f"{lot.eta_warehouse:%Y-%m}" for lot in all_lots}, reverse=True)
        lots: list[ArrivalLotDTO] = []
        pair_counts: dict[tuple[str, str], int] = {}
        for lot in all_lots:
            key = business.mapping_key(lot.supplier, lot.description)
            pair_counts[key] = pair_counts.get(key, 0) + 1
            mapping = mappings.get(key)
            decision = mapping.decision if mapping else MaterialDecision.CHUA_KHAI_BAO
            group_id = mapping.price_group_id if mapping and decision == MaterialDecision.THEO_NHOM else None
            if request.factory_code and lot.factory_code != request.factory_code:
                continue
            if request.month and f"{lot.eta_warehouse:%Y-%m}" != request.month:
                continue
            if request.group_id and group_id != request.group_id:
                continue
            if request.market and lot.market not in (request.market, MaterialMarket.CHUNG):
                continue
            if request.only_unmapped and decision != MaterialDecision.CHUA_KHAI_BAO:
                continue
            lots.append(
                ArrivalLotDTO(
                    id=lot.id,
                    supplier=lot.supplier,
                    commodity=lot.commodity,
                    description=lot.description,
                    spec=lot.spec,
                    contract_no=lot.contract_no,
                    contract_date=lot.contract_date,
                    quantity=lot.quantity,
                    unit_price=lot.unit_price,
                    price_currency=lot.price_currency,
                    receiving_price=lot.receiving_price,
                    term=lot.term,
                    origin_country=lot.origin_country,
                    eta_warehouse=lot.eta_warehouse,
                    warehouse=lot.warehouse,
                    factory_code=lot.factory_code,
                    market=lot.market,
                    note=lot.note,
                    group_name=groups[group_id].name if group_id in groups else decision.value,  # type: ignore[index]
                    decision=decision,
                    from_file=lot.import_id is not None,
                )
            )
        mapping_rows = sorted(
            (
                ArrivalMappingDTO(
                    supplier_key=m.supplier_key,
                    description_key=m.description_key,
                    supplier=m.supplier,
                    description=m.description,
                    lot_count=pair_counts.get(key, 0),
                    decision=m.decision,
                    price_group_id=m.price_group_id,
                )
                for key, m in mappings.items()
                if pair_counts.get(key, 0) > 0
            ),
            key=lambda m: (m.decision != MaterialDecision.CHUA_KHAI_BAO, m.supplier, m.description),
        )
        imports = sorted(ArrivalImportRepository().list_all(), key=lambda i: i.created_at, reverse=True)
        return ArrivalListResponse(
            lots=lots,
            mappings=mapping_rows,
            imports=[
                ArrivalImportDTO(
                    file_name=i.file_name,
                    sheet_name=i.sheet_name,
                    lot_count=i.lot_count,
                    rejected_count=i.rejected_count,
                    imported_by=i.imported_by,
                    imported_at=i.created_at,
                )
                for i in imports
            ],
            months=months,
            groups=[group_dto(g) for g in sorted(groups.values(), key=lambda g: g.name.casefold())],
            total_qty=sum((lot.quantity for lot in lots), Decimal(0)),
            unmapped_count=sum(1 for lot in lots if lot.decision == MaterialDecision.CHUA_KHAI_BAO),
        )
