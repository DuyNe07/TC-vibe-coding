"""4.6 parameter set <-> DTOs: single values grouped by department, 4.6.1 discount rows, 4.6.2 % B/C rows."""

from decimal import Decimal

from backend.features.woven_costing.dto.master_dto import (
    BcRowDTO,
    DiscountRowDTO,
    OpRateRowDTO,
    ParameterSetDetailDTO,
    ParameterValueDTO,
)
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.enums import ParamGroup
from backend.features.woven_costing.models.parameter_set import (
    APPLIED_FINISHED_BC,
    APPLIED_GREIGE_BC,
    APPLIED_HCM,
    APPLIED_TCDN,
    APPLIED_WEAVING,
    LEGACY_DEFINITIONS,
    PARAMETER_DEFINITIONS,
    ParameterDefinition,
    ParameterSet,
    ParameterValues,
)
from backend.features.woven_costing.models.parameter_tables import (
    DEPARTMENT_APPLIES_TO,
    BcRow,
    DiscountRow,
    OpRateRow,
    ParameterTables,
    complete_bc_rows,
)

DISCOUNT_LABEL = "Hệ số discount đang áp dụng"
# BR-46 (2026-11-25): (label, group, is_percent) of the values applied from the tables on one costsheet
APPLIED_ROWS = {
    APPLIED_WEAVING: (DISCOUNT_LABEL, ParamGroup.WEAVING, False),
    APPLIED_HCM: (DISCOUNT_LABEL, ParamGroup.HCM, False),
    APPLIED_TCDN: (DISCOUNT_LABEL, ParamGroup.TCDN, False),
    APPLIED_GREIGE_BC: ("% B/C mộc đang áp dụng", ParamGroup.PRICE, True),
    APPLIED_FINISHED_BC: ("% B/C TP đang áp dụng", ParamGroup.PRICE, True),
}


def _value_dto(d: ParameterDefinition, default: Decimal, used: Decimal) -> ParameterValueDTO:
    return ParameterValueDTO(code=d.code, label=d.label, unit=d.unit, is_percent=d.is_percent, so_only=d.so_only,
                             default_value=default, used_value=used, group=d.group)  # fmt: skip


def parameter_rows(defaults: ParameterValues, sheet: Costsheet | None = None) -> list[ParameterValueDTO]:
    """4.6 / 4.18 rows: default value of the set and value used on the costsheet (BR-46), grouped by department;
    on a costsheet also the discount factors and % B/C applied from the tables (with the reason) and the old values
    still overridden on costsheets saved before 2026-11-25."""
    used = {o.parameter: o for o in sheet.parameter_overrides} if sheet else {}
    rows = []
    for d in PARAMETER_DEFINITIONS:
        override = used.get(d.code)
        default = override.default_value if override else defaults.get(d.code)
        rows.append(_value_dto(d, default, override.used_value if override else default))
    if sheet is None:
        return rows
    for d in LEGACY_DEFINITIONS:
        if d.code in used:
            rows.append(_value_dto(d, used[d.code].default_value, used[d.code].used_value))
    applied = {a.code: a for a in sheet.result.applied_parameters}
    for code, (label, group, percent) in APPLIED_ROWS.items():
        found, override = applied.get(code), used.get(code)
        if found is not None:
            default, value, reason = found.default_value, found.used_value, found.reason
        elif override is not None:
            default, value, reason = override.default_value, override.used_value, ""
        else:
            continue
        rows.append(ParameterValueDTO(code=code, label=label, unit="%" if percent else "", is_percent=percent,
                                      default_value=default, used_value=value, group=group,
                                      reason=reason))  # fmt: skip
    return rows


def discount_row_dto(row: DiscountRow) -> DiscountRowDTO:
    return DiscountRowDTO(
        **row.model_dump(),
        quantity_unit=row.unit,
        applies_to=DEPARTMENT_APPLIES_TO[row.department],
        reason=row.reason,
    )


def bc_row_dto(row: BcRow) -> BcRowDTO:
    return BcRowDTO(**row.model_dump())


def parameter_set_detail(parameter_set: ParameterSet) -> ParameterSetDetailDTO:
    tables = parameter_set.effective_tables()
    return ParameterSetDetailDTO(
        effective_from=parameter_set.effective_from,
        created_by=parameter_set.created_by,
        values=parameter_rows(parameter_set.values),
        discount_rows=[discount_row_dto(r) for r in tables.discount_rows],
        bc_rows=[bc_row_dto(r) for r in complete_bc_rows(tables.bc_rows)],
        op_rates=[OpRateRowDTO(stage=r.stage, rate=r.rate) for r in tables.op_rates],
        from_old_values=parameter_set.tables is None,
    )


def tables_from_dtos(
    discount_rows: list[DiscountRowDTO], bc_rows: list[BcRowDTO], op_rates: list[OpRateRowDTO] | None = None
) -> ParameterTables:
    """Rows typed by SO; a new set never interpolates (4.6.1: "bộ mới luôn No")."""
    keep = set(DiscountRow.model_fields)
    rows = [DiscountRow(**{**r.model_dump(include=keep), "interpolate": False}) for r in discount_rows]
    typed = ParameterTables(discount_rows=rows, bc_rows=[BcRow(**r.model_dump()) for r in bc_rows])
    if op_rates is not None:
        typed = typed.model_copy(update={"op_rates": [OpRateRow(stage=r.stage.strip(), rate=r.rate)
                                                      for r in op_rates if r.stage.strip()]})  # fmt: skip
    return typed
