"""Tables edited by the data updater. Initial values are written only to a table that never had a row."""

from backend.core.base import SqlRepository
from backend.features.sewing_productivity.constants import (
    CUSTOMER_GROUP_SEED,
    GOAL_SEED,
    GOAL_SEED_FROM,
    LINE_LABEL_FORMAT,
    LINE_MAPPING_SEED,
    PRODUCT_GROUP_SEED,
    SYSTEM_USER,
)
from backend.features.sewing_productivity.models.clean_values import catalog_id
from backend.features.sewing_productivity.models.settings_records import (
    CustomerGroupRule,
    FactoryGoal,
    LineMappingRule,
    ProductGroupRule,
    StyleProductRule,
    WeeklyChangeover,
)
from backend.features.sewing_productivity.models.stored_record import stable_id


class FactoryGoalRepository(SqlRepository[FactoryGoal]):
    def list_seeded(self) -> list[FactoryGoal]:
        """Section 4.4: flagged rows count as rows, so user deletions are never overwritten."""
        if not self.list_all() and not self.list_deleted():
            self.save_many(
                FactoryGoal(
                    id=stable_id(factory.value, GOAL_SEED_FROM),
                    factory=factory,
                    effective_from=GOAL_SEED_FROM,
                    efficiency_target=efficiency_target,
                    mo8h_target=mo8h_target,
                    efficiency_threshold=efficiency_threshold,
                    mo8h_threshold=mo8h_threshold,
                    updated_by=SYSTEM_USER,
                )
                for factory, efficiency_target, mo8h_target, efficiency_threshold, mo8h_threshold in GOAL_SEED
            )
        return self.list_all()


class WeeklyChangeoverRepository(SqlRepository[WeeklyChangeover]):
    pass


class ProductGroupRuleRepository(SqlRepository[ProductGroupRule]):
    def list_seeded(self) -> list[ProductGroupRule]:
        """Section 4.6, written once."""
        if not self.list_all() and not self.list_deleted():
            self.save_many(
                ProductGroupRule(id=catalog_id(name), product_name=name, product_group=group)
                for group, names in PRODUCT_GROUP_SEED.items()
                for name in names
            )
        return self.list_all()


class CustomerGroupRuleRepository(SqlRepository[CustomerGroupRule]):
    def list_seeded(self) -> list[CustomerGroupRule]:
        """Section 4.7, written once."""
        if not self.list_all() and not self.list_deleted():
            self.save_many(
                CustomerGroupRule(id=catalog_id(name), customer_name=name, customer_group=group)
                for name, group in CUSTOMER_GROUP_SEED.items()
            )
        return self.list_all()


class LineMappingRuleRepository(SqlRepository[LineMappingRule]):
    def list_seeded(self) -> list[LineMappingRule]:
        """Section 4.8, written once."""
        if not self.list_all() and not self.list_deleted():
            self.save_many(
                LineMappingRule(
                    id=catalog_id(LINE_LABEL_FORMAT.format(old)),
                    old_line=LINE_LABEL_FORMAT.format(old),
                    new_line=LINE_LABEL_FORMAT.format(new),
                )
                for old, new in LINE_MAPPING_SEED
            )
        return self.list_all()


class StyleProductRuleRepository(SqlRepository[StyleProductRule]):
    pass
