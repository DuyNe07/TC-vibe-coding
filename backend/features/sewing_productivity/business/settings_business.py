"""Goals, weekly changeovers and catalogs typed by the data updater (BR-39, BR-40, BR-45, BR-46, BR-47)."""

import re

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.sewing_productivity.constants import ALL_FACTORIES, LINE_LABEL_FORMAT, MESSAGE_BR39, MESSAGE_BR45
from backend.features.sewing_productivity.models.clean_values import catalog_id, catalog_key
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.models.input_values import (
    CatalogInput,
    CatalogPair,
    GoalInput,
    WeeklyChangeoverInput,
)
from backend.features.sewing_productivity.models.settings_records import (
    CustomerGroupRule,
    FactoryGoal,
    LineMappingRule,
    ProductGroupRule,
    StyleProductRule,
    WeeklyChangeover,
)
from backend.features.sewing_productivity.models.stored_record import stable_id

_LINE_FORMAT = re.compile(r"^LINE\s+0*(\d+)$", re.IGNORECASE)


class GoalInputRule(BaseBusinessRule[GoalInput]):
    code = "BR-45"
    message = MESSAGE_BR45

    def is_satisfied_by(self, target: GoalInput) -> bool:
        levels = (target.efficiency_target, target.mo8h_target, target.efficiency_threshold, target.mo8h_threshold)
        has_key = target.factory is not None and target.effective_from is not None
        return has_key and all(level is not None and level.is_finite() and level > 0 for level in levels)


class WeeklyChangeoverRule(BaseBusinessRule[WeeklyChangeoverInput]):
    code = "BR-39"
    message = MESSAGE_BR39

    def is_satisfied_by(self, target: WeeklyChangeoverInput) -> bool:
        if target.from_date is None or target.to_date is None or target.from_date > target.to_date:
            return False
        known = {factory.value for factory in ALL_FACTORIES}
        entered = {name: count for name, count in target.counts.items() if count is not None}
        whole = all(count >= 0 and float(count).is_integer() for count in entered.values())
        return bool(entered) and set(entered) <= known and whole


class CatalogRowsRule(BaseBusinessRule[CatalogInput]):
    code = "BR-47"
    message = "Danh mục có dòng trống hoặc trùng. Hãy sửa rồi lưu lại."

    def problems(self, target: CatalogInput) -> list[str]:
        problems: list[str] = []
        seen: set[str] = set()
        for number, pair in enumerate(target.pairs, start=1):
            if not pair.key or not pair.value:
                problems.append(pair.key or pair.value or f"dòng {number}")
                continue
            key = catalog_key(pair.key)
            if key in seen:
                problems.append(pair.key)
            seen.add(key)
            if target.lines_only:
                problems.extend(text for text in (pair.key, pair.value) if not _LINE_FORMAT.match(text))
        return problems

    def is_satisfied_by(self, target: CatalogInput) -> bool:
        return not self.problems(target)

    def describe_violation(self, target: CatalogInput) -> str:
        return f"Danh mục có dòng trống hoặc trùng: {', '.join(self.problems(target))}. Hãy sửa rồi lưu lại."


class SettingsBusiness(BaseBusiness[GoalInput]):
    def rules(self) -> tuple[GoalInputRule, ...]:
        return (GoalInputRule(),)

    def to_goal(self, values: GoalInput, updated_by: str) -> FactoryGoal:
        """BR-46 the id comes from factory + effective date, so the same pair replaces the old level."""
        return FactoryGoal(
            id=stable_id(values.factory.value, values.effective_from),
            factory=values.factory,
            effective_from=values.effective_from,
            efficiency_target=values.efficiency_target,
            mo8h_target=values.mo8h_target,
            efficiency_threshold=values.efficiency_threshold,
            mo8h_threshold=values.mo8h_threshold,
            updated_by=updated_by,
        )

    def ensure_weekly(self, values: WeeklyChangeoverInput) -> None:
        """BR-39 valid period, whole numbers from 0, at least one factory."""
        WeeklyChangeoverRule().check(values)

    def to_weekly(self, values: WeeklyChangeoverInput, updated_by: str) -> list[WeeklyChangeover]:
        """BR-40 the id comes from factory + period, so the same period replaces the old number."""
        return [
            WeeklyChangeover(
                id=stable_id(name, values.from_date, values.to_date),
                factory=Factory(name),
                from_date=values.from_date,
                to_date=values.to_date,
                changeover_count=int(count),
                updated_by=updated_by,
            )
            for name, count in values.counts.items()
            if count is not None
        ]

    def catalog_pairs(self, rows: list[tuple[object, object]], lines_only: bool = False) -> CatalogInput:
        """BR-47 input: text cells trimmed; a fully empty row is ignored; line names are written `LINE <số>`."""
        pairs = []
        for key, value in rows:
            left, right = str(key or "").strip(), str(value or "").strip()
            if left or right:
                pairs.append(
                    CatalogPair(key=self._line_text(left, lines_only), value=self._line_text(right, lines_only))
                )
        return CatalogInput(pairs=tuple(pairs), lines_only=lines_only)

    @staticmethod
    def _line_text(text: str, lines_only: bool) -> str:
        match = _LINE_FORMAT.match(text) if lines_only else None
        return LINE_LABEL_FORMAT.format(int(match.group(1))) if match else text

    def ensure_catalog(self, values: CatalogInput) -> None:
        """BR-47 no empty cell, no duplicate first column, line names in the right form."""
        CatalogRowsRule().check(values)

    def product_group_rules(self, values: CatalogInput) -> list[ProductGroupRule]:
        """UC-22 catalog rows; the id comes from the name, so the same name replaces its old row."""
        return [
            ProductGroupRule(id=catalog_id(pair.key), product_name=pair.key, product_group=pair.value)
            for pair in values.pairs
        ]

    def customer_group_rules(self, values: CatalogInput) -> list[CustomerGroupRule]:
        """UC-23 catalog rows; the id comes from the name, so the same name replaces its old row."""
        return [
            CustomerGroupRule(id=catalog_id(pair.key), customer_name=pair.key, customer_group=pair.value)
            for pair in values.pairs
        ]

    def line_mapping_rules(self, values: CatalogInput) -> list[LineMappingRule]:
        """UC-24 catalog rows; the id comes from the old line, so the same line replaces its old row."""
        return [
            LineMappingRule(id=catalog_id(pair.key), old_line=pair.key, new_line=pair.value) for pair in values.pairs
        ]

    def style_product_rules(self, values: CatalogInput) -> list[StyleProductRule]:
        """UC-25 catalog rows; the id comes from the style, so the same style replaces its old row."""
        return [
            StyleProductRule(id=catalog_id(pair.key), style=pair.key, product_name=pair.value) for pair in values.pairs
        ]
