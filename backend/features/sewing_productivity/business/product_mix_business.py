"""BR-93 to BR-96 (thêm 2026-11-13 lần 4): what the factories make and for whom - the product mix of each factory, the
top customers, the average CM price of each product group and the product mix month by month."""

from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.sewing_productivity.business.productivity_business import HUNDRED, total
from backend.features.sewing_productivity.constants import (
    MIX_OTHER_GROUP,
    MIX_TOP_CUSTOMERS,
    MIX_TOP_GROUPS,
    UNCLASSIFIED_GROUP,
)
from backend.features.sewing_productivity.models.clean_values import CleanRow
from backend.features.sewing_productivity.models.report_values import (
    CustomerOutput,
    GroupCmPrice,
    GroupShare,
    MonthGroupOutput,
    PeriodRange,
)


class ProductMixBusiness(BaseBusiness[CleanRow]):
    @staticmethod
    def top_groups(rows: Iterable[CleanRow]) -> list[str]:
        """BR-93 the 5 product groups with the most output; "Chưa phân nhóm" always goes to "Other"."""
        output: defaultdict[str, Decimal] = defaultdict(Decimal)
        for row in rows:
            if row.product_group != UNCLASSIFIED_GROUP:
                output[row.product_group] += row.quantity
        ranked = sorted(output.items(), key=lambda item: (-item[1], item[0]))
        return [group for group, value in ranked[:MIX_TOP_GROUPS] if value > 0]

    def shares(self, column: str, rows: list[CleanRow], keep: list[str] | None = None) -> list[GroupShare]:
        """BR-93 the output of each product group of one column and its share of the column (%), biggest first.
        With `keep` (the chart) the other groups are added up as "Other", in the order of `keep`."""
        output: defaultdict[str, Decimal] = defaultdict(Decimal)
        for row in rows:
            group = row.product_group if keep is None or row.product_group in keep else MIX_OTHER_GROUP
            output[group] += row.quantity
        whole = total(output.values())
        if keep is None:
            order = sorted(output, key=lambda group: (-output[group], group))
        else:
            order = [group for group in [*keep, MIX_OTHER_GROUP] if output.get(group)]
        return [
            GroupShare(
                column=column,
                group=group,
                output=output[group],
                share=output[group] * HUNDRED / whole if whole else None,
            )
            for group in order
        ]

    @staticmethod
    def top_customers(rows: Iterable[CleanRow]) -> list[CustomerOutput]:
        """BR-94 the 10 customer groups with the most output, split by factory; biggest customer first."""
        by_pair: defaultdict[tuple[str, object], Decimal] = defaultdict(Decimal)
        by_customer: defaultdict[str, Decimal] = defaultdict(Decimal)
        for row in rows:
            by_pair[(row.customer_group, row.factory)] += row.quantity
            by_customer[row.customer_group] += row.quantity
        ranked = sorted(by_customer, key=lambda customer: (-by_customer[customer], customer))[:MIX_TOP_CUSTOMERS]
        position = {customer: index for index, customer in enumerate(ranked)}
        result = [
            CustomerOutput(customer=customer, factory=factory, output=value)
            for (customer, factory), value in by_pair.items()
            if customer in position and value > 0
        ]
        return sorted(result, key=lambda item: (position[item.customer], item.factory.value))

    @staticmethod
    def cm_prices(rows: Iterable[CleanRow]) -> list[GroupCmPrice]:
        """BR-95 average CM price of each product group = CM earning / output (BR-24), highest first."""
        output: defaultdict[str, Decimal] = defaultdict(Decimal)
        earning: defaultdict[str, Decimal] = defaultdict(Decimal)
        for row in rows:
            output[row.product_group] += row.quantity
            earning[row.product_group] += row.cm_earning
        result = [
            GroupCmPrice(group=group, output=output[group], cm_price=earning[group] / output[group])
            for group in output
            if output[group] > 0
        ]
        return sorted(result, key=lambda item: (-item.cm_price, item.group))

    @staticmethod
    def monthly(rows: Iterable[CleanRow], months: list[PeriodRange], keep: list[str]) -> list[MonthGroupOutput]:
        """BR-96 the output of each month by product group (the groups of `keep`, the rest as "Other")."""
        output: defaultdict[tuple[int, str], Decimal] = defaultdict(Decimal)
        for row in rows:
            index = next(
                (i for i, month in enumerate(months) if month.from_date <= row.production_date <= month.to_date), None
            )
            if index is not None:
                group = row.product_group if row.product_group in keep else MIX_OTHER_GROUP
                output[(index, group)] += row.quantity
        groups = [
            group for group in [*keep, MIX_OTHER_GROUP] if any(output.get((i, group)) for i in range(len(months)))
        ]
        worked = [index for index in range(len(months)) if any(output.get((index, group)) for group in groups)]
        # every group in every month (0 when absent): the chart colours follow the first appearance, so they stay fixed
        return [
            MonthGroupOutput(
                month=months[index].label,
                start=months[index].from_date,
                group=group,
                output=output.get((index, group), Decimal(0)),
            )
            for index in worked
            for group in groups
        ]
