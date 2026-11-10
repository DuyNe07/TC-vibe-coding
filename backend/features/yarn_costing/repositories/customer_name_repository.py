"""Table xuan2894__yarn_costing__customer_yarn_name: 4.20 Tên theo khách (bổ sung 2026-11-10)."""

from backend.features.yarn_costing.models.customer_name import CustomerYarnName
from backend.features.yarn_costing.repositories.yarn_sql_repository import YarnSqlRepository


class CustomerYarnNameRepository(YarnSqlRepository[CustomerYarnName]):
    pass
