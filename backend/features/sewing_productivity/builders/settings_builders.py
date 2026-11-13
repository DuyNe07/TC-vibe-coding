"""Goals, weekly changeovers, catalogs and filter choices -> response DTOs."""

from datetime import date, datetime

from backend.core.base import BaseBuilder
from backend.features.sewing_productivity.dto.catalog_dto import (
    CatalogsResponse,
    CustomerGroupRowDTO,
    CustomerNameDTO,
    LineMappingRowDTO,
    ProductGroupRowDTO,
    StyleProductRowDTO,
    StyleWithoutProductDTO,
    UnclassifiedProductDTO,
)
from backend.features.sewing_productivity.dto.filter_dto import FilterOptionsResponse
from backend.features.sewing_productivity.dto.goal_dto import GoalDTO, GoalListResponse
from backend.features.sewing_productivity.dto.weekly_changeover_dto import (
    WeeklyChangeoverDTO,
    WeeklyChangeoverListResponse,
)
from backend.features.sewing_productivity.models.clean_values import line_sort_key
from backend.features.sewing_productivity.models.settings_records import (
    CustomerGroupRule,
    FactoryGoal,
    LineMappingRule,
    ProductGroupRule,
    StyleProductRule,
    WeeklyChangeover,
)
from backend.features.sewing_productivity.models.upload_values import DateRange


def _goal_dto(goal: FactoryGoal) -> GoalDTO:
    return GoalDTO(
        factory=goal.factory.value,
        effective_from=goal.effective_from,
        efficiency_target=float(goal.efficiency_target),
        mo8h_target=float(goal.mo8h_target),
        efficiency_threshold=float(goal.efficiency_threshold),
        mo8h_threshold=float(goal.mo8h_threshold),
        updated_by=goal.updated_by,
    )


class GoalListBuilder(BaseBuilder[GoalListResponse]):
    def __init__(self, current: list[FactoryGoal], history: list[FactoryGoal]) -> None:
        self.current = current
        self.history = history

    def build(self) -> GoalListResponse:
        history = sorted(self.history, key=lambda goal: goal.factory.value)
        history.sort(key=lambda goal: goal.effective_from, reverse=True)
        return GoalListResponse(
            current=[_goal_dto(goal) for goal in self.current], history=[_goal_dto(goal) for goal in history]
        )


class WeeklyChangeoverListBuilder(BaseBuilder[WeeklyChangeoverListResponse]):
    def __init__(self, items: list[WeeklyChangeover]) -> None:
        self.items = items

    def build(self) -> WeeklyChangeoverListResponse:
        items = sorted(self.items, key=lambda item: item.factory.value)
        items.sort(key=lambda item: (item.from_date, item.to_date), reverse=True)
        return WeeklyChangeoverListResponse(
            items=[
                WeeklyChangeoverDTO(
                    id=item.id,
                    factory=item.factory.value,
                    from_date=item.from_date,
                    to_date=item.to_date,
                    changeover_count=item.changeover_count,
                    updated_by=item.updated_by,
                )
                for item in items
            ]
        )


class CatalogsResponseBuilder(BaseBuilder[CatalogsResponse]):
    def __init__(
        self,
        product_groups: list[ProductGroupRule],
        customer_groups: list[CustomerGroupRule],
        line_mappings: list[LineMappingRule],
        style_products: list[StyleProductRule],
        unclassified: dict[str, int],
        customer_names: list[tuple[str, str, int]],
        styles_without_name: list[tuple[str, str, int]],
    ) -> None:
        self.product_groups = product_groups
        self.customer_groups = customer_groups
        self.line_mappings = line_mappings
        self.style_products = style_products
        self.unclassified = unclassified
        self.customer_names = customer_names
        self.styles_without_name = styles_without_name

    def build(self) -> CatalogsResponse:
        lines = sorted(self.line_mappings, key=lambda rule: line_sort_key(rule.old_line))
        return CatalogsResponse(
            product_groups=[
                ProductGroupRowDTO(product_name=rule.product_name, product_group=rule.product_group)
                for rule in sorted(self.product_groups, key=lambda rule: (rule.product_group, rule.product_name))
            ],
            customer_groups=[
                CustomerGroupRowDTO(customer_name=rule.customer_name, customer_group=rule.customer_group)
                for rule in sorted(self.customer_groups, key=lambda rule: (rule.customer_group, rule.customer_name))
            ],
            line_mappings=[LineMappingRowDTO(old_line=rule.old_line, new_line=rule.new_line) for rule in lines],
            style_products=[
                StyleProductRowDTO(style=rule.style, product_name=rule.product_name)
                for rule in sorted(self.style_products, key=lambda rule: rule.style)
            ],
            unclassified_products=[
                UnclassifiedProductDTO(product_name=name, row_count=count) for name, count in self.unclassified.items()
            ],
            customer_names=[
                CustomerNameDTO(customer_name=name, customer_group=group, row_count=count)
                for name, group, count in self.customer_names
            ],
            styles_without_product=[
                StyleWithoutProductDTO(style=style, customer_name=customer, row_count=count)
                for style, customer, count in self.styles_without_name
            ],
        )


class FilterOptionsBuilder(BaseBuilder[FilterOptionsResponse]):
    def __init__(
        self,
        lines_by_factory: dict[str, list[str]],
        customer_groups: list[str],
        product_groups: list[str],
        latest_date: date | None,
        last_upload_at: datetime | None,
        default_week: DateRange,
        default_month_from: date | None,
        default_year_from: date | None = None,
    ) -> None:
        self.default_year_from = default_year_from
        self.lines_by_factory = lines_by_factory
        self.customer_groups = customer_groups
        self.product_groups = product_groups
        self.latest_date = latest_date
        self.last_upload_at = last_upload_at
        self.default_week = default_week
        self.default_month_from = default_month_from

    def build(self) -> FilterOptionsResponse:
        return FilterOptionsResponse(
            factories=list(self.lines_by_factory),
            lines_by_factory=self.lines_by_factory,
            customer_groups=self.customer_groups,
            product_groups=self.product_groups,
            latest_date=self.latest_date,
            last_upload_at=self.last_upload_at,
            default_week_from=self.default_week.from_date,
            default_week_to=self.default_week.to_date,
            default_month_from=self.default_month_from,
            default_year_from=self.default_year_from,
            has_data=self.latest_date is not None,
        )
