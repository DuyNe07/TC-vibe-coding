"""Each validation rule (passing + failing) and each calculation rule, without files or a database."""

from datetime import date
from decimal import Decimal

import pytest

from backend.core.exceptions import BusinessRuleViolation
from backend.features.sewing_productivity.business.access_rules import AccessBusiness, UpdaterRoleRule
from backend.features.sewing_productivity.business.cleaning_business import CleaningBusiness
from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.productivity_business import ProductivityBusiness
from backend.features.sewing_productivity.business.settings_business import (
    CatalogRowsRule,
    GoalInputRule,
    SettingsBusiness,
    WeeklyChangeoverRule,
)
from backend.features.sewing_productivity.business.upload_rules import (
    FormulaResultsRule,
    KnownFactoryRule,
    ProductionRowRule,
    RequiredColumnsRule,
    RequiredSheetsRule,
    TargetRowRule,
    UploadFileRule,
)
from backend.features.sewing_productivity.constants import LINE_LABEL_FORMAT, LINE_MAPPING_SEED
from backend.features.sewing_productivity.models.clean_values import CatalogSet, NameLookup, catalog_key
from backend.features.sewing_productivity.models.enums import Assessment, Factory
from backend.features.sewing_productivity.models.input_values import GoalInput, WeeklyChangeoverInput
from backend.features.sewing_productivity.models.settings_records import FactoryGoal
from backend.features.sewing_productivity.models.source_records import ProductionRecord, TargetRecord
from backend.features.sewing_productivity.models.upload_values import (
    ProductionResultFacts,
    RawProductionRow,
    RawTargetRow,
    SheetColumns,
    SheetNames,
    UploadFileFacts,
)
from backend.features.sewing_productivity.tests.workbook_factory import clean_row

LINES = CatalogSet(
    line_mappings={
        catalog_key(LINE_LABEL_FORMAT.format(old)): LINE_LABEL_FORMAT.format(new) for old, new in LINE_MAPPING_SEED
    }
)
CATALOGS = CatalogSet(
    product_groups={"polo shirt": "Polo"},
    customer_groups={"mi hub limited": "MIHUB"},
    style_products={"wt62i2oc": "T-SHIRT"},
)


def record(**changes: object) -> ProductionRecord:
    values = {
        "production_date": date(2026, 10, 24),
        "factory": Factory.FAC_2,
        "customer_name": "ELAND WORLD",
        "style": "S1",
        "po_number": "PO-1.1",
        "source_line": "LINE 1",
        "quantity": Decimal(100),
        "cm_price": Decimal(1),
        "working_hours": Decimal(8),
        "sewers": Decimal(10),
    }
    return ProductionRecord(**{**values, **changes})


def valid_raw(**changes: object) -> RawProductionRow:
    values = {
        "row_number": 3,
        "production_date": date(2026, 10, 24),
        "factory_text": "SHCM-Factory 2",
        "customer_name": "C",
        "style": "S",
        "po_number": "P",
        "source_line": "LINE 1",
        "quantity": Decimal(0),
        "cm_price": Decimal(1),
        "sewers": Decimal(1),
        "working_hours": Decimal(1),
    }
    return RawProductionRow(**{**values, **changes})


def goal(efficiency_threshold: str = "90", mo8h_threshold: str = "40", start: date = date(2026, 1, 1)) -> FactoryGoal:
    return FactoryGoal(
        factory=Factory.FAC_2,
        effective_from=start,
        efficiency_target=Decimal(100),
        mo8h_target=Decimal(43),
        efficiency_threshold=Decimal(efficiency_threshold),
        mo8h_threshold=Decimal(mo8h_threshold),
        updated_by="x",
    )


def test_br01_rule() -> None:
    rule = UploadFileRule()
    assert rule.is_satisfied_by(UploadFileFacts(extension=".xlsx", size_mb=50))
    assert not rule.is_satisfied_by(UploadFileFacts(extension=".xlsx", size_mb=50.1))
    assert not rule.is_satisfied_by(UploadFileFacts(extension=".pdf", size_mb=1))


def test_br02_rule() -> None:
    rule = RequiredSheetsRule()
    assert rule.is_satisfied_by(SheetNames())
    assert "File thiếu sheet: Worker." in rule.evaluate(SheetNames(missing=("Worker",))).message


def test_br03_rule() -> None:
    rule = RequiredColumnsRule()
    assert rule.is_satisfied_by(SheetColumns(sheet="Worker"))
    assert (
        "Sheet Worker thiếu cột: SF2, SF3."
        in rule.evaluate(SheetColumns(sheet="Worker", missing=("SF2", "SF3"))).message
    )


def test_br04_rule() -> None:
    rule = FormulaResultsRule()
    assert rule.is_satisfied_by(ProductionResultFacts(valid_rows=1, standard_output_cells=1))
    assert not rule.is_satisfied_by(ProductionResultFacts(valid_rows=1, standard_output_cells=0))
    assert not rule.is_satisfied_by(ProductionResultFacts(valid_rows=0, standard_output_cells=0))


def test_br05_rule() -> None:
    rule = ProductionRowRule()
    assert rule.is_satisfied_by(valid_raw())  # quantity 0 is valid
    bad = valid_raw(quantity=Decimal(-1), cm_price=Decimal(0), production_date=None)
    assert rule.evaluate(bad).message == "Dòng 3: thiếu hoặc sai adj Date, Product Inline Quantiy, Price."


def test_br06_rule() -> None:
    rule = KnownFactoryRule()
    for name in ("SVL-Factory 2", "shcm-factory 3", " SHCM-Factory 5 "):
        assert rule.is_satisfied_by(valid_raw(factory_text=name))
    assert rule.evaluate(valid_raw(factory_text="ABC")).message == 'Dòng 3: chưa nhận diện được xưởng "ABC".'


def test_br09_rule() -> None:
    from backend.core.current_user import CurrentUser

    rule = UpdaterRoleRule()
    assert rule.is_satisfied_by(None)
    assert rule.is_satisfied_by(CurrentUser(username="a", is_admin=True))
    assert rule.is_satisfied_by(CurrentUser(username="m", is_master=True))
    assert rule.is_satisfied_by(CurrentUser(username="u", permissions=frozenset({"sewing_productivity/@UPDATER"})))
    assert not rule.is_satisfied_by(CurrentUser(username="v", permissions=frozenset({"sewing_productivity"})))
    assert not rule.is_satisfied_by(CurrentUser(username="o", permissions=frozenset({"other_app/@UPDATER"})))
    assert AccessBusiness().saved_by(None) == "Hệ thống"


def test_br10_standard_line() -> None:
    cleaning = CleaningBusiness()
    assert cleaning.standard_line("Line 1") == "LINE 1"
    assert cleaning.standard_line("LINE 01") == "LINE 1"
    assert cleaning.standard_line(" line12 ") == "LINE 12"
    assert cleaning.standard_line("Line A") == "LINE A"


def test_ac15_br11_fac1_line_mapping_only_before_cutover() -> None:
    cleaning = CleaningBusiness()
    assert cleaning.current_line(Factory.FAC_1, date(2026, 7, 6), "LINE 1", LINES) == "LINE 30"
    assert cleaning.current_line(Factory.FAC_1, date(2026, 7, 7), "LINE 1", LINES) == "LINE 1"
    assert cleaning.current_line(Factory.FAC_2, date(2026, 7, 6), "LINE 1", LINES) == "LINE 1"
    assert cleaning.current_line(Factory.FAC_1, date(2026, 7, 6), "LINE 99", LINES) == "LINE 99"


def test_br12_base_order() -> None:
    cleaning = CleaningBusiness()
    assert cleaning.base_po(" XKA30-SX-EX-0826-7598.1 ") == "XKA30-SX-EX-0826-7598"
    assert cleaning.base_po("XKA21.5-A") == "XKA21.5-A"
    assert cleaning.base_po("PO-1") == "PO-1"


def test_ac16_br13_empty_name_is_filled_in_order() -> None:
    cleaning = CleaningBusiness()
    empty = record(product_name=None, style="WT62I2OC", po_number="PO-7.2")
    lookup = NameLookup(
        by_base_po={"PO-7": "FROM ORDER"},
        by_style={"WT62I2OC": "FROM STYLE"},
        target_by_base_po={"PO-7": "TARGET ORDER"},
        target_by_style={"WT62I2OC": "TARGET STYLE"},
    )
    assert cleaning.product_name(empty, lookup, CATALOGS) == "T-SHIRT"  # style catalog first
    assert cleaning.product_name(empty, lookup, CatalogSet()) == "FROM ORDER"
    assert cleaning.product_name(empty, NameLookup(by_style={"WT62I2OC": "FROM STYLE"}), CatalogSet()) == "FROM STYLE"
    assert cleaning.product_name(empty, NameLookup(target_by_base_po={"PO-7": "T"}), CatalogSet()) == "T"
    assert cleaning.product_name(empty, NameLookup(target_by_style={"WT62I2OC": "U"}), CatalogSet()) == "U"
    assert cleaning.product_name(empty, NameLookup(), CatalogSet()) is None
    assert cleaning.product_name(record(product_name="POLO"), lookup, CATALOGS) == "POLO"  # a name in the file stays


def test_br13_most_frequent_name_then_alphabetical() -> None:
    cleaning = CleaningBusiness()
    rows = [
        record(product_name="B", po_number="PO-1.1"),
        record(product_name="B", po_number="PO-1.2"),
        record(product_name="A", po_number="PO-1.3"),
        record(product_name="Z", po_number="PO-2.1", style="S2"),
        record(product_name="Y", po_number="PO-2.2", style="S2"),
    ]
    lookup = cleaning.name_lookup(rows, [])
    assert lookup.by_base_po["PO-1"] == "B"
    assert lookup.by_base_po["PO-2"] == "Y"
    target = TargetRecord(
        target_date=date(2026, 10, 24),
        factory=Factory.FAC_2,
        line="LINE 1",
        base_po="PO-9",
        item_name="DRESS",
        daily_target_qty=Decimal(1),
    )
    assert cleaning.name_lookup([], [target]).target_by_base_po == {"PO-9": "DRESS"}


def test_br14_product_group() -> None:
    cleaning = CleaningBusiness()
    assert cleaning.product_group(" polo SHIRT ", CATALOGS) == "Polo"
    assert cleaning.product_group("VITRIOL", CATALOGS) == "Chưa phân nhóm"
    assert cleaning.product_group(None, CATALOGS) == "Chưa phân nhóm"


def test_ac19_br15_customer_group() -> None:
    cleaning = CleaningBusiness()
    assert cleaning.customer_group("MI HUB LIMITED", CATALOGS) == "MIHUB"
    assert cleaning.customer_group("ELAND WORLD/SPAO (QR)", CATALOGS) == "ELAND"
    assert cleaning.customer_group("eland sport", CATALOGS) == "ELAND"
    assert cleaning.customer_group(" Mark's Work ", CATALOGS) == "MARK'S WORK"
    catalog_first = CatalogSet(customer_groups={"eland world": "KHÁC"})
    assert cleaning.customer_group("ELAND WORLD", catalog_first) == "KHÁC"


def test_br16_rule() -> None:
    rule = TargetRowRule()
    good = RawTargetRow(
        row_number=2, line_text="SF2 - Sewing Line 01", target_date=date(2026, 10, 24), daily_target_qty=Decimal(0)
    )
    assert rule.is_satisfied_by(good)
    bad = RawTargetRow(row_number=5, line_text="SF9 - Sewing Line 1", daily_target_qty=Decimal(-1))
    assert rule.evaluate(bad).message == "Sheet Target system, dòng 5: sai Line, Date, Daily Target (SMV)."


def test_br17_cm_earning_is_not_rounded() -> None:
    assert CleaningBusiness().cm_earning(record(quantity=Decimal(680), cm_price=Decimal("1.13"))) == Decimal("768.40")


def test_br18_efficiency_a_uses_the_same_scope_on_both_sides() -> None:
    calc = ProductivityBusiness()
    day = date(2026, 10, 24)
    target_map = {(Factory.FAC_2, "LINE 1", day): Decimal(200)}
    rows = [clean_row(day, "LINE 1", qty="100"), clean_row(day, "LINE 2", qty="999")]
    assert calc.output_in_target_scope(rows, target_map) == Decimal(100)
    assert calc.efficiency_a(Decimal(100), Decimal(200)) == Decimal(50)
    assert calc.efficiency_a(Decimal(100), None) is None


def test_br19_efficiency_b_leaves_out_rows_without_target_b() -> None:
    calc = ProductivityBusiness()
    day = date(2026, 10, 24)
    with_b = clean_row(day, qty="50")
    without_b = clean_row(day, qty="999").model_copy(update={"standard_output": None})
    assert calc.efficiency_b([with_b, without_b]) == Decimal(50)
    assert calc.target_b([with_b, without_b]) == Decimal(100)
    assert calc.efficiency_b([without_b]) is None
    assert calc.target_b([without_b]) is None


def test_br20_hours_are_averages_of_averages() -> None:
    calc = ProductivityBusiness()
    day = date(2026, 10, 24)
    rows = [
        clean_row(day, "LINE 1").model_copy(update={"working_hours": Decimal(8)}),
        clean_row(day, "LINE 1").model_copy(update={"working_hours": Decimal(10)}),
        clean_row(day, "LINE 2").model_copy(update={"working_hours": Decimal(6)}),
    ]
    line_hours = calc.line_hours(rows)
    assert line_hours[(Factory.FAC_2, "LINE 1", day)] == Decimal(9)
    assert calc.factory_day_hours(line_hours)[(Factory.FAC_2, day)] == Decimal("7.5")
    assert calc.factory_period_hours([Decimal(9), Decimal(8)]) == Decimal("8.5")


def test_br21_people_of_a_line_is_an_average() -> None:
    day = date(2026, 10, 24)
    rows = [
        clean_row(day).model_copy(update={"sewers": Decimal(24)}),
        clean_row(day).model_copy(update={"sewers": Decimal(26)}),
    ]
    assert ProductivityBusiness().line_sewers(rows)[(Factory.FAC_2, "LINE 1", day)] == Decimal(25)


def test_br22_line_mo8h() -> None:
    calc = ProductivityBusiness()
    assert calc.line_mo8h(Decimal(400), Decimal(10), Decimal(8)) == Decimal(40)
    assert calc.line_mo8h(Decimal(400), None, Decimal(8)) is None
    assert calc.line_period_mo8h([Decimal(10), Decimal(40), None]) == Decimal(25)


def test_br23_factory_mo() -> None:
    calc = ProductivityBusiness()
    assert calc.factory_mo(Decimal(400), Decimal(40)) == Decimal(10)
    assert calc.factory_mo(Decimal(400), None) is None
    assert calc.factory_mo8h(Decimal(400), Decimal(40), Decimal(10)) == Decimal(8)
    assert calc.factory_mo8h(Decimal(400), None, Decimal(10)) is None


def test_ac51_br24_average_price() -> None:
    calc = ProductivityBusiness()
    assert calc.average_cm_price(Decimal(300), Decimal(150)) == Decimal(2)
    assert calc.average_cm_price(Decimal(0), Decimal(0)) is None


def test_br25_strength_match() -> None:
    calc = ProductivityBusiness()
    common = {"target_date": date(2026, 10, 24), "factory": Factory.FAC_2, "line": "LINE 1"}
    rows = [
        TargetRecord(daily_target_qty=Decimal(300), is_mismatched=True, **common),
        TargetRecord(daily_target_qty=Decimal(700), **common),
    ]
    assert calc.strength_match(rows) == Decimal(70)
    assert calc.strength_match([]) is None


def test_ac27_br26_level_of_a_day() -> None:
    calc = ProductivityBusiness()
    old, new = goal(start=date(2026, 1, 1)), goal(start=date(2026, 12, 1))
    assert calc.goal_on([old, new], date(2026, 11, 30)) is old
    assert calc.goal_on([old, new], date(2026, 12, 1)) is new
    assert calc.goal_on([old, new], date(2025, 12, 31)) is None


def test_br27_percent_of_target() -> None:
    calc = ProductivityBusiness()
    assert calc.percent_of_target(Decimal(45), Decimal(90)) == Decimal(50)
    assert calc.percent_of_target(None, Decimal(90)) is None
    assert calc.percent_of_target(Decimal(45), None) is None


@pytest.mark.parametrize(
    ("value", "threshold", "expected"),
    [
        ("89.9", "90", Assessment.BELOW),  # AC-29 Fac 2
        ("85.0", "85", Assessment.PASSED),  # AC-29 Fac 1
        ("39.9", "40", Assessment.BELOW),  # AC-30 Fac 2
        ("30.0", "30", Assessment.PASSED),  # AC-30 Fac 1
    ],
)
def test_ac29_ac30_br28_boundaries(value: str, threshold: str, expected: Assessment) -> None:
    assert ProductivityBusiness().assess(Decimal(value), Decimal(threshold)) == expected


def test_br28_no_number_means_no_assessment() -> None:
    assert ProductivityBusiness().assess(None, Decimal(30)) == Assessment.NOT_AVAILABLE
    assert ProductivityBusiness().assess_mo8h(Decimal(30), None) == Assessment.NOT_AVAILABLE


def test_br29_filter_rows() -> None:
    business = FilterBusiness()
    day = date(2026, 10, 24)
    eland = clean_row(day).model_copy(update={"customer_group": "ELAND"})
    other = clean_row(day).model_copy(update={"customer_group": "MIHUB", "product_group": "Polo"})
    assert business.apply_groups([eland, other], {"ELAND"}, set()) == [eland]
    assert business.apply_groups([eland, other], set(), {"Polo"}) == [other]
    assert business.apply_groups([eland, other], set(), set()) == [eland, other]


def test_br30_period_order() -> None:
    business = FilterBusiness()
    business.ensure_period(date(2026, 10, 24), date(2026, 10, 24))
    with pytest.raises(BusinessRuleViolation) as error:
        business.ensure_period(date(2026, 10, 25), date(2026, 10, 24))
    assert error.value.message == "Từ ngày không được sau đến ngày. Hãy chọn lại khoảng thời gian."


@pytest.mark.parametrize(
    ("latest", "start", "end"),
    [
        (date(2026, 11, 4), date(2026, 10, 24), date(2026, 10, 30)),  # AC-46, a Wednesday
        (date(2026, 10, 30), date(2026, 10, 24), date(2026, 10, 30)),  # the newest day is a Friday
        (date(2026, 10, 31), date(2026, 10, 24), date(2026, 10, 30)),  # the newest day is a Saturday
    ],
)
def test_ac46_br31_default_week(latest: date, start: date, end: date) -> None:
    week = FilterBusiness().default_week(latest)
    assert (week.from_date, week.to_date) == (start, end)


def test_ac52_br31_default_month() -> None:
    assert FilterBusiness().default_month_start(date(2026, 11, 4)) == date(2026, 11, 1)


def test_br39_rule() -> None:
    rule = WeeklyChangeoverRule()
    start, end = date(2026, 10, 24), date(2026, 10, 30)
    assert rule.is_satisfied_by(WeeklyChangeoverInput(from_date=start, to_date=end, counts={"Fac 2": 0, "Fac 1": None}))
    for values in (
        WeeklyChangeoverInput(from_date=start, to_date=end, counts={"Fac 2": -1}),
        WeeklyChangeoverInput(from_date=start, to_date=end, counts={"Fac 2": 1.5}),
        WeeklyChangeoverInput(from_date=end, to_date=start, counts={"Fac 2": 1}),
        WeeklyChangeoverInput(from_date=start, to_date=end, counts={"Fac 2": None}),
        WeeklyChangeoverInput(from_date=None, to_date=end, counts={"Fac 2": 1}),
        WeeklyChangeoverInput(from_date=start, to_date=end, counts={"Fac 9": 1}),
    ):
        assert not rule.is_satisfied_by(values)


def test_br45_rule() -> None:
    rule = GoalInputRule()
    levels = {
        "efficiency_target": Decimal(1),
        "mo8h_target": Decimal(1),
        "efficiency_threshold": Decimal(1),
        "mo8h_threshold": Decimal(1),
    }
    good = {"factory": Factory.FAC_1, "effective_from": date(2026, 1, 1), **levels}
    assert rule.is_satisfied_by(GoalInput(**good))
    assert not rule.is_satisfied_by(GoalInput())
    assert not rule.is_satisfied_by(GoalInput(**{**good, "factory": None}))
    assert not rule.is_satisfied_by(GoalInput(**{**good, "mo8h_target": Decimal(0)}))
    assert not rule.is_satisfied_by(GoalInput(**{**good, "mo8h_threshold": None}))


def test_br47_rule() -> None:
    settings = SettingsBusiness()
    rule = CatalogRowsRule()
    assert rule.is_satisfied_by(settings.catalog_pairs([("A", "1"), ("B", "1")]))
    assert rule.is_satisfied_by(settings.catalog_pairs([(None, None), ("A", "1")]))  # a fully empty row is ignored
    duplicate = settings.catalog_pairs([("POLO", "1"), (" polo ", "2")])
    assert rule.evaluate(duplicate).message == "Danh mục có dòng trống hoặc trùng: polo. Hãy sửa rồi lưu lại."
    assert "trống hoặc trùng: A." in rule.evaluate(settings.catalog_pairs([("A", None)])).message
    assert "trống hoặc trùng: B." in rule.evaluate(settings.catalog_pairs([(None, "B")])).message
    wrong_line = settings.catalog_pairs([("LINE 1", "CHUYEN 2")], lines_only=True)
    assert "CHUYEN 2" in rule.evaluate(wrong_line).message
    tidy = settings.catalog_pairs([("line 01", "Line 2")], lines_only=True)
    assert rule.is_satisfied_by(tidy)
    assert (tidy.pairs[0].key, tidy.pairs[0].value) == ("LINE 1", "LINE 2")
