"""4.8 Quy trình công nghệ (Process route)."""

from pydantic import Field

from backend.core.base import BaseEntity
from backend.features.yarn_costing.models.enums import FactoryCode, Technology


class ProcessRoute(BaseEntity):
    factory_code: FactoryCode
    yarn_group: str = Field(min_length=1, max_length=100)
    technology: Technology
    component_count: int | None = Field(default=None, ge=1, le=5)
    route_text: str = Field(default="", max_length=500)
    route_stages: list[str] = Field(default_factory=list)
