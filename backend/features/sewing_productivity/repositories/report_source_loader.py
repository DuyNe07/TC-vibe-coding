"""Loads everything a report reads, once per service call (tables come from the RAM cache of the repositories)."""

from backend.features.sewing_productivity.models.clean_values import CatalogSet, ReportSource, catalog_key
from backend.features.sewing_productivity.repositories.settings_repositories import (
    CustomerGroupRuleRepository,
    FactoryGoalRepository,
    LineMappingRuleRepository,
    ProductGroupRuleRepository,
    StyleProductRuleRepository,
    WeeklyChangeoverRepository,
)
from backend.features.sewing_productivity.repositories.source_repositories import (
    ProductionRecordRepository,
    TargetRecordRepository,
    UploadLogRepository,
    WorkerRecordRepository,
)


def load_catalogs() -> CatalogSet:
    """The 4 catalogs as lookups."""
    return CatalogSet.model_construct(
        product_groups={
            catalog_key(rule.product_name): rule.product_group for rule in ProductGroupRuleRepository().list_seeded()
        },
        customer_groups={
            catalog_key(rule.customer_name): rule.customer_group for rule in CustomerGroupRuleRepository().list_seeded()
        },
        line_mappings={catalog_key(rule.old_line): rule.new_line for rule in LineMappingRuleRepository().list_seeded()},
        style_products={catalog_key(rule.style): rule.product_name for rule in StyleProductRuleRepository().list_all()},
    )


def load_report_source() -> ReportSource:
    """Stored rows, flagged ones left out."""
    uploads = UploadLogRepository().list_all()
    return ReportSource.model_construct(
        production=ProductionRecordRepository().list_all(),
        targets=TargetRecordRepository().list_all(),
        workers=WorkerRecordRepository().list_all(),
        goals=FactoryGoalRepository().list_seeded(),
        weekly_changeovers=WeeklyChangeoverRepository().list_all(),
        catalogs=load_catalogs(),
        last_upload_at=max((log.uploaded_at for log in uploads), default=None),
    )
