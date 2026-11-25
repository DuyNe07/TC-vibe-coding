"""F-07 content of one fabric label (sheet PRINT)."""

from pydantic import Field

from backend.core.base import BaseValueObject


class FabricLabel(BaseValueObject):
    tcfno: str
    fabric_name: str = ""
    yarn_lines: list[str] = Field(default_factory=list)
    width_cm: str = ""
    width_inch: str = ""
    gsm: str = ""
    g_per_m: str = ""
    warp_density: str = ""
    weft_density: str = ""
    remark: str = ""
