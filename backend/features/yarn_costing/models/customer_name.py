"""4.20 Tên theo khách (bổ sung 2026-11-10): one name a customer uses for a yarn, attached to its base code."""

from pydantic import Field

from backend.core.base import BaseEntity


class CustomerYarnName(BaseEntity):
    base_code: str = Field(min_length=1, max_length=60)
    customer_name: str = Field(min_length=1, max_length=100)
    customer_yarn_name: str = Field(min_length=1, max_length=200)
    note: str = ""
    created_by: str = ""
    updated_by: str = ""
