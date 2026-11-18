"""Feature "Năng suất xưởng may". Business spec: docs/business/sewing_productivity.md

Public API = the top layer only. Pages use: gateway.open(SewingProductivityController)
Layers below (services, business, builders, repositories, models) are internal to this feature.
"""

from backend.features.sewing_productivity.controllers.sewing_productivity_controller import SewingProductivityController

DEVELOPER = "thynguyen-lab"  # GitHub username of the developer: prefix of this feature's database tables

__all__ = ["SewingProductivityController"]
