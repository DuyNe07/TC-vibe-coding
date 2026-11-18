"""Cleaning computed when reading (BR-10 to BR-15, BR-17), so a catalog edit changes every report at once."""

import re
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal

from backend.core.base import BaseBusiness
from backend.features.sewing_productivity.constants import (
    ELAND_GROUP,
    ELAND_PREFIX,
    FAC1_LINE_CUTOVER,
    LINE_LABEL_FORMAT,
    UNCLASSIFIED_GROUP,
)
from backend.features.sewing_productivity.models.clean_values import CatalogSet, CleanRow, NameLookup, catalog_key
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.models.source_records import ProductionRecord, TargetRecord

_LINE_TEXT = re.compile(r"^\s*(?:LINE)?\s*[-_.]?\s*0*(\d+)\s*$", re.IGNORECASE)
_PO_SUFFIX = re.compile(r"\.\d+$")


def base_po_number(po_number: str) -> str:
    """BR-12 base order number: spaces at both ends and the number after the last dot are removed."""
    return _PO_SUFFIX.sub("", po_number.strip())


def _most_frequent(names: Counter[str]) -> str:
    """BR-13 the most frequent name; on a tie the first in alphabetical order."""
    return min(names.items(), key=lambda item: (-item[1], item[0]))[0]


class CleaningBusiness(BaseBusiness[ProductionRecord]):
    def standard_line(self, source_line: str) -> str:
        """BR-10 line name written `LINE <số>`, whatever the case. Text without a number stays as it is, in capitals."""
        match = _LINE_TEXT.match(source_line)
        return LINE_LABEL_FORMAT.format(int(match.group(1))) if match else " ".join(source_line.upper().split())

    def current_line(self, factory: Factory, day: date, standard_line: str, catalogs: CatalogSet) -> str:
        """BR-11 Fac 1 data before 07/07/2026 uses the line mapping; a line not in the table keeps its name."""
        if factory != Factory.FAC_1 or day >= FAC1_LINE_CUTOVER:
            return standard_line
        return catalogs.line_mappings.get(catalog_key(standard_line), standard_line)

    def base_po(self, po_number: str) -> str:
        """BR-12 base order number of a production row."""
        return base_po_number(po_number)

    def name_lookup(self, production: list[ProductionRecord], targets: list[TargetRecord]) -> NameLookup:
        """BR-13 which name each order and style carries, in the production data and in `Target system`."""
        by_po: defaultdict[str, Counter[str]] = defaultdict(Counter)
        by_style: defaultdict[str, Counter[str]] = defaultdict(Counter)
        for record in production:
            if record.product_name:
                by_po[base_po_number(record.po_number)][record.product_name] += 1
                by_style[record.style][record.product_name] += 1
        target_by_po: defaultdict[str, Counter[str]] = defaultdict(Counter)
        target_by_style: defaultdict[str, Counter[str]] = defaultdict(Counter)
        for target in targets:
            if target.item_name:
                if target.base_po:
                    target_by_po[target.base_po][target.item_name] += 1
                if target.style:
                    target_by_style[target.style][target.item_name] += 1
        return NameLookup.model_construct(
            by_base_po={key: _most_frequent(names) for key, names in by_po.items()},
            by_style={key: _most_frequent(names) for key, names in by_style.items()},
            target_by_base_po={key: _most_frequent(names) for key, names in target_by_po.items()},
            target_by_style={key: _most_frequent(names) for key, names in target_by_style.items()},
        )

    def product_name(self, record: ProductionRecord, lookup: NameLookup, catalogs: CatalogSet) -> str | None:
        """BR-13 an empty name is filled from: style catalog; same order; same style; same order then style in Target."""
        if record.product_name:
            return record.product_name
        base_po = base_po_number(record.po_number)
        return (
            catalogs.style_products.get(catalog_key(record.style))
            or lookup.by_base_po.get(base_po)
            or lookup.by_style.get(record.style)
            or lookup.target_by_base_po.get(base_po)
            or lookup.target_by_style.get(record.style)
        )

    def product_group(self, product_name: str | None, catalogs: CatalogSet) -> str:
        """BR-14 group from the catalog, ignoring case; unknown or empty names are "Chưa phân nhóm"."""
        if not product_name:
            return UNCLASSIFIED_GROUP
        return catalogs.product_groups.get(catalog_key(product_name), UNCLASSIFIED_GROUP)

    def customer_group(self, customer_name: str, catalogs: CatalogSet) -> str:
        """BR-15 group from the catalog first; then ELAND by prefix; else the name itself, in capitals."""
        group = catalogs.customer_groups.get(catalog_key(customer_name))
        if group:
            return group
        name = customer_name.strip().upper()
        return ELAND_GROUP if name.startswith(ELAND_PREFIX) else name

    def cm_earning(self, record: ProductionRecord) -> Decimal:
        """BR-17 CM earning = quantity x CM price, not rounded."""
        return record.quantity * record.cm_price

    def clean(self, records: list[ProductionRecord], lookup: NameLookup, catalogs: CatalogSet) -> list[CleanRow]:
        """The cleaned view of the given rows (built without re-validating: about 32 000 rows per report)."""
        rows: list[CleanRow] = []
        for record in records:
            name = self.product_name(record, lookup, catalogs)
            line = self.current_line(
                record.factory, record.production_date, self.standard_line(record.source_line), catalogs
            )
            rows.append(
                CleanRow.model_construct(
                    production_date=record.production_date,
                    factory=record.factory,
                    customer_name=record.customer_name,
                    customer_group=self.customer_group(record.customer_name, catalogs),
                    style=record.style,
                    po_number=record.po_number,
                    base_po=base_po_number(record.po_number),
                    product_name=name,
                    product_group=self.product_group(name, catalogs),
                    color=record.color,
                    line=line,
                    quantity=record.quantity,
                    cm_price=record.cm_price,
                    cm_earning=self.cm_earning(record),
                    working_hours=record.working_hours,
                    sewers=record.sewers,
                    smv=record.smv,
                    standard_output=record.standard_output,
                    standard_output_no_ratio=record.standard_output_no_ratio,
                    is_mismatched=record.is_mismatched,
                )
            )
        return rows
