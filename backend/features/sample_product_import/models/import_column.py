from backend.core.base import BaseValueObject


class ImportColumn(BaseValueObject):
    """One column of the Excel import template."""

    field: str
    header: str
    required: bool
    aliases: tuple[str, ...] = ()
