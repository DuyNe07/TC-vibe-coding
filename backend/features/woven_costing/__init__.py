"""Feature "Tính giá vải dệt". Business spec: docs/business/woven_costing.md

Public API = the top layer only. Pages use: gateway.open(WovenCostingController)
Layers below (services, business, builders, repositories, models) are internal to this feature.
"""

from backend.features.woven_costing.controllers.woven_costing_controller import WovenCostingController

DEVELOPER = "Xuan2894"  # GitHub username of the developer: prefix of this feature's database tables

__all__ = ["WovenCostingController"]
