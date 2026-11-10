"""Model → DTO of đợt 2 (bổ sung 2026-11-10)."""

from collections.abc import Sequence
from decimal import Decimal

from backend.features.yarn_costing.dto.material_dto import (
    AverageRowDTO,
    AverageSourceDTO,
    PriceGroupDTO,
    QuoteComponentDTO,
    QuoteDTO,
    StockOutRowDTO,
)
from backend.features.yarn_costing.models.material_price import (
    COTTON_PLAN_ID,
    COTTON_PLAN_NAME,
    GroupAverage,
    MaterialPriceGroup,
    Quote,
    StockOutCompareRow,
)


def group_dto(group: MaterialPriceGroup, code_count: int = 0) -> PriceGroupDTO:
    return PriceGroupDTO(
        id=group.id, name=group.name, kind=group.kind, origin=group.origin, note=group.note, code_count=code_count
    )


def group_options(groups: Sequence[MaterialPriceGroup]) -> list[PriceGroupDTO]:
    """Cotton (phương án) first, then the 4.22 groups by name."""
    ordered = sorted(groups, key=lambda g: g.name.casefold())
    return [PriceGroupDTO(id=COTTON_PLAN_ID, name=COTTON_PLAN_NAME), *(group_dto(g) for g in ordered)]


def average_dto(average: GroupAverage, rate: Decimal) -> AverageRowDTO:
    return AverageRowDTO(
        group_id=average.group_id,
        group_name=average.group_name,
        market=average.market,
        stock_qty=average.stock_qty,
        stock_unit=average.stock_value / average.stock_qty if average.stock_qty > 0 else None,
        arrival_qty=average.arrival_qty,
        arrival_unit=average.arrival_value / average.arrival_qty if average.arrival_qty > 0 else None,
        total_qty=average.total_qty,
        average=average.average,
        recovery=average.recovery,
        net_usd=average.net,
        net_vnd=average.net * rate if average.net is not None else None,
        note=average.note,
        sources=[
            AverageSourceDTO(
                kind=s.kind, code=s.code, name=s.name, market=s.market, quantity=s.quantity, unit_usd=s.unit_usd
            )
            for s in average.sources
        ],
    )


def quote_dto(quote: Quote) -> QuoteDTO:
    return QuoteDTO(
        id=quote.id,
        quote_no=quote.quote_no,
        period=quote.period,
        line_code=quote.line_code,
        price_kind=quote.price_kind,
        yarn_name=quote.yarn_name,
        accounting_code=quote.accounting_code,
        customer_name=quote.customer_name,
        market=quote.market,
        order_qty=quote.order_qty,
        norm_factor=quote.norm_factor,
        gp_percent=quote.gp_percent,
        commission_percent=quote.commission_percent,
        incoterm=quote.incoterm,
        fi_usd=quote.fi_usd,
        exchange_rate=quote.exchange_rate,
        norm_vnd=quote.norm_vnd,
        material_usd=quote.material_usd,
        norm_usd=quote.norm_usd,
        new_cost_usd=quote.new_cost_usd,
        stock_qty=quote.stock_qty,
        stock_cost_usd=quote.stock_cost_usd,
        avg_cost_usd=quote.avg_cost_usd,
        fob_usd=quote.fob_usd,
        cif_usd=quote.cif_usd,
        components=[QuoteComponentDTO(**c.model_dump()) for c in quote.components],
        note=quote.note,
        created_by=quote.created_by,
        created_at=quote.created_at if quote.quote_no else None,
    )


def stock_out_dto(row: StockOutCompareRow) -> StockOutRowDTO:
    return StockOutRowDTO(**row.model_dump())
