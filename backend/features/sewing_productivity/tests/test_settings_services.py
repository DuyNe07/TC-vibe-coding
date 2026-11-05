"""UC-16 to UC-25: goals, weekly changeovers, catalogs, and initial values written only once."""

from datetime import date, timedelta

import pytest

from backend.core.base import EmptyRequest
from backend.core.current_user import CurrentUser, set_current_user
from backend.core.exceptions import BusinessRuleViolation
from backend.features.sewing_productivity.dto.catalog_dto import (
    CustomerGroupRowDTO,
    LineMappingRowDTO,
    ProductGroupRowDTO,
    SaveCustomerGroupsRequest,
    SaveLineMappingsRequest,
    SaveProductGroupsRequest,
    SaveStyleProductsRequest,
    StyleProductRowDTO,
)
from backend.features.sewing_productivity.dto.goal_dto import SaveGoalRequest
from backend.features.sewing_productivity.dto.line_detail_dto import LineDetailRequest, RowType
from backend.features.sewing_productivity.dto.overview_dto import OverviewRequest
from backend.features.sewing_productivity.dto.upload_dto import SaveUploadRequest
from backend.features.sewing_productivity.dto.weekly_changeover_dto import (
    DeleteWeeklyChangeoverRequest,
    SaveWeeklyChangeoversRequest,
)
from backend.features.sewing_productivity.models.enums import Factory
from backend.features.sewing_productivity.repositories.settings_repositories import (
    CustomerGroupRuleRepository,
    FactoryGoalRepository,
    LineMappingRuleRepository,
    ProductGroupRuleRepository,
    WeeklyChangeoverRepository,
)
from backend.features.sewing_productivity.services.delete_weekly_changeover_service import DeleteWeeklyChangeoverService
from backend.features.sewing_productivity.services.get_catalogs_service import GetCatalogsService
from backend.features.sewing_productivity.services.get_filter_options_service import GetFilterOptionsService
from backend.features.sewing_productivity.services.get_line_detail_service import GetLineDetailService
from backend.features.sewing_productivity.services.get_overview_service import GetOverviewService
from backend.features.sewing_productivity.services.list_goals_service import ListGoalsService
from backend.features.sewing_productivity.services.list_weekly_changeovers_service import ListWeeklyChangeoversService
from backend.features.sewing_productivity.services.save_customer_groups_service import SaveCustomerGroupsService
from backend.features.sewing_productivity.services.save_goal_service import SaveGoalService
from backend.features.sewing_productivity.services.save_line_mappings_service import SaveLineMappingsService
from backend.features.sewing_productivity.services.save_product_groups_service import SaveProductGroupsService
from backend.features.sewing_productivity.services.save_style_products_service import SaveStyleProductsService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.services.save_weekly_changeovers_service import SaveWeeklyChangeoversService
from backend.features.sewing_productivity.tests.workbook_factory import FAC1, FAC2, data_file, production

BR39 = "Hãy nhập khoảng ngày hợp lệ và số lần là số nguyên từ 0 trở lên cho ít nhất một xưởng."
BR45 = "Hãy chọn xưởng, ngày hiệu lực và nhập cả 4 mức là số lớn hơn 0."
START, END = date(2026, 10, 24), date(2026, 10, 30)


@pytest.fixture(autouse=True)
def _no_user():
    set_current_user(None)
    yield
    set_current_user(None)


def goal_request(**changes: object) -> SaveGoalRequest:
    values = {
        "factory": Factory.FAC_1,
        "effective_from": date(2026, 12, 1),
        "efficiency_target": 95,
        "mo8h_target": 40,
        "efficiency_threshold": 85,
        "mo8h_threshold": 30,
    }
    return SaveGoalRequest(**{**values, **changes})


def test_ac50_initial_goals_and_current_level() -> None:
    goals = ListGoalsService().handle(EmptyRequest())
    assert [(goal.factory, goal.efficiency_target, goal.mo8h_target) for goal in goals.current] == [
        ("Fac 1", 95, 38),
        ("Fac 2", 100, 43),
        ("Fac 3", 100, 43),
        ("Fac 5", 100, 43),
    ]
    assert goals.current[0].efficiency_threshold == 85
    assert goals.current[0].mo8h_threshold == 30
    assert goals.current[1].mo8h_threshold == 40
    assert len(goals.history) == 4


def test_ac50_same_factory_and_date_replaces_the_level() -> None:
    SaveGoalService().handle(goal_request(mo8h_target=40))
    result = SaveGoalService().handle(goal_request(mo8h_target=41))
    assert result.message == "Đã lưu mục tiêu của Fac 1, hiệu lực từ 01/12/2026."
    goals = ListGoalsService().handle(EmptyRequest())
    assert len(goals.history) == 5
    assert goals.history[0].mo8h_target == 41  # newest first


def test_future_level_is_not_current_yet() -> None:
    tomorrow = date.today() + timedelta(days=1)
    SaveGoalService().handle(goal_request(effective_from=tomorrow, mo8h_target=99))
    assert ListGoalsService().handle(EmptyRequest()).current[0].mo8h_target == 38


@pytest.mark.parametrize(
    "request_values",
    [
        {"mo8h_target": None},
        {"efficiency_target": 0},
        {"mo8h_threshold": -1},
        {"factory": None},
        {"effective_from": None},
    ],
)
def test_ac28_wrong_level_shows_br45(request_values: dict[str, object]) -> None:
    with pytest.raises(BusinessRuleViolation) as error:
        SaveGoalService().handle(goal_request(**request_values))
    assert error.value.message == BR45


def test_ac28_empty_form_reaches_br45() -> None:
    with pytest.raises(BusinessRuleViolation) as error:
        SaveGoalService().handle(SaveGoalRequest())
    assert error.value.message == BR45


def test_seeds_are_written_once_and_never_over_user_deletions() -> None:
    repository = FactoryGoalRepository()
    repository.list_seeded()
    repository.clear()
    assert repository.list_seeded() == []
    assert len(repository.list_deleted()) == 4
    products = ProductGroupRuleRepository()
    assert len(products.list_seeded()) == 34
    products.clear()
    assert products.list_seeded() == []
    customers = CustomerGroupRuleRepository()
    assert len(customers.list_seeded()) == 3
    customers.clear()
    assert customers.list_seeded() == []
    lines = LineMappingRuleRepository()
    assert len(lines.list_seeded()) == 34
    lines.clear()
    assert lines.list_seeded() == []


def test_user_edit_survives_later_reads() -> None:
    SaveProductGroupsService().handle(
        SaveProductGroupsRequest(rows=[ProductGroupRowDTO(product_name="POLO", product_group="New")])
    )
    rules = ProductGroupRuleRepository().list_seeded()
    assert [(rule.product_name, rule.product_group) for rule in rules] == [("POLO", "New")]


def test_ac32_wrong_weekly_input_shows_br39() -> None:
    for request in (
        SaveWeeklyChangeoversRequest(from_date=START, to_date=END, counts={"Fac 2": -1}),
        SaveWeeklyChangeoversRequest(from_date=END, to_date=START, counts={"Fac 2": 1}),
        SaveWeeklyChangeoversRequest(from_date=START, to_date=END, counts={"Fac 2": None}),
        SaveWeeklyChangeoversRequest(from_date=START, to_date=END, counts={"Fac 2": 1.5}),
        SaveWeeklyChangeoversRequest(to_date=END, counts={"Fac 2": 1}),
        SaveWeeklyChangeoversRequest(),
    ):
        with pytest.raises(BusinessRuleViolation) as error:
            SaveWeeklyChangeoversService().handle(request)
        assert error.value.message == BR39
    assert WeeklyChangeoverRepository().count() == 0


def test_ac47_same_period_replaces_and_delete_shows_dash() -> None:
    SaveUploadService().handle(SaveUploadRequest(file=data_file([production(START, FAC2)])))
    save = SaveWeeklyChangeoversService()
    result = save.handle(
        SaveWeeklyChangeoversRequest(from_date=START, to_date=END, counts={"Fac 2": 17, "Fac 1": None})
    )
    assert result.message == "Đã lưu số đổi mã hàng từ 24/10/2026 đến 30/10/2026."
    save.handle(SaveWeeklyChangeoversRequest(from_date=START, to_date=END, counts={"Fac 2": 18}))
    items = ListWeeklyChangeoversService().handle(EmptyRequest()).items
    assert [(item.factory, item.changeover_count) for item in items] == [("Fac 2", 18)]

    def weekly_value() -> float | None:
        overview = GetOverviewService().handle(OverviewRequest(from_date=START, to_date=END))
        return next(row for row in overview.metrics if row.metric == "Đổi mã hàng tuần").values["Fac 2"]

    assert weekly_value() == 18
    deleted = DeleteWeeklyChangeoverService().handle(DeleteWeeklyChangeoverRequest(id=items[0].id))
    assert deleted.message == "Đã xoá."
    assert ListWeeklyChangeoversService().handle(EmptyRequest()).items == []
    assert len(WeeklyChangeoverRepository().list_deleted()) == 1
    assert weekly_value() is None


def test_ac17_style_catalog_fills_rows_and_leaves_the_missing_list() -> None:
    rows = [production(START, FAC2, name=None, style="WT62I2OC", po="PO-5", customer="MI HUB")]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, target_rows=[])))
    missing = GetCatalogsService().handle(EmptyRequest()).styles_without_product
    assert [(item.style, item.customer_name, item.row_count) for item in missing] == [("WT62I2OC", "MI HUB", 1)]
    result = SaveStyleProductsService().handle(
        SaveStyleProductsRequest(rows=[StyleProductRowDTO(style="WT62I2OC", product_name="T-SHIRT")])
    )
    assert result.message == "Đã lưu tên sản phẩm."
    catalogs = GetCatalogsService().handle(EmptyRequest())
    assert catalogs.styles_without_product == []
    assert GetFilterOptionsService().handle(EmptyRequest()).product_groups == ["T-Shirt"]


def test_style_typed_as_a_number_stays_text() -> None:
    assert StyleProductRowDTO(style=796470, product_name="T-SHIRT").style == "796470"


def test_ac18_new_group_applies_to_old_days() -> None:
    rows = [production(date(2026, 3, 2), FAC2, name="VITRIOL")]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, target_rows=[], worker_rows=[])))
    catalogs = GetCatalogsService().handle(EmptyRequest())
    assert [(item.product_name, item.row_count) for item in catalogs.unclassified_products] == [("VITRIOL", 1)]
    kept = [
        ProductGroupRowDTO(product_name=row.product_name, product_group=row.product_group)
        for row in catalogs.product_groups
    ]
    result = SaveProductGroupsService().handle(
        SaveProductGroupsRequest(rows=[*kept, ProductGroupRowDTO(product_name="vitriol", product_group="Khác")])
    )
    assert result.message == "Đã lưu nhóm sản phẩm."
    assert GetCatalogsService().handle(EmptyRequest()).unclassified_products == []
    assert GetFilterOptionsService().handle(EmptyRequest()).product_groups == ["Khác"]
    assert ProductGroupRuleRepository().count() == 35


def test_ac19_saving_a_customer_group_changes_the_filter_and_customer_list() -> None:
    rows = [production(START, FAC2, customer="ELAND WORLD"), production(START, FAC2, customer="NEW BRAND", color="RED")]
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows)))
    assert GetFilterOptionsService().handle(EmptyRequest()).customer_groups == ["ELAND", "NEW BRAND"]
    result = SaveCustomerGroupsService().handle(
        SaveCustomerGroupsRequest(rows=[CustomerGroupRowDTO(customer_name="NEW BRAND", customer_group="ELAND")])
    )
    assert result.message == "Đã lưu nhóm khách hàng."
    assert GetFilterOptionsService().handle(EmptyRequest()).customer_groups == ["ELAND"]
    names = GetCatalogsService().handle(EmptyRequest()).customer_names
    assert [(item.customer_name, item.customer_group, item.row_count) for item in names] == [
        ("ELAND WORLD", "ELAND", 1),
        ("NEW BRAND", "ELAND", 1),
    ]
    assert (
        len(CustomerGroupRuleRepository().list_deleted()) == 3
    )  # the rows left out of the list are flagged, not removed


@pytest.mark.parametrize(
    ("service", "request_obj", "shown"),
    [
        (
            SaveProductGroupsService,
            SaveProductGroupsRequest(
                rows=[
                    ProductGroupRowDTO(product_name="POLO", product_group="A"),
                    ProductGroupRowDTO(product_name=" polo", product_group="B"),
                ]
            ),
            "polo",
        ),
        (
            SaveCustomerGroupsService,
            SaveCustomerGroupsRequest(rows=[CustomerGroupRowDTO(customer_name="ACME", customer_group=None)]),
            "ACME",
        ),
        (
            SaveLineMappingsService,
            SaveLineMappingsRequest(rows=[LineMappingRowDTO(old_line="LINE 1", new_line="CHUYEN 2")]),
            "CHUYEN 2",
        ),
        (
            SaveStyleProductsService,
            SaveStyleProductsRequest(rows=[StyleProductRowDTO(style=None, product_name="T-SHIRT")]),
            "T-SHIRT",
        ),
    ],
)
def test_ac48_wrong_catalog_shows_br47(service: type, request_obj: object, shown: str) -> None:
    with pytest.raises(BusinessRuleViolation) as error:
        service().handle(request_obj)
    assert error.value.message == f"Danh mục có dòng trống hoặc trùng: {shown}. Hãy sửa rồi lưu lại."


def test_ac49_line_table_applies_to_old_fac1_data() -> None:
    day = date(2026, 7, 6)
    SaveUploadService().handle(
        SaveUploadRequest(file=data_file([production(day, FAC1, "LINE 1")], target_rows=[], worker_rows=[]))
    )

    def lines() -> set[str]:
        response = GetLineDetailService().handle(LineDetailRequest(from_date=day, to_date=day, factory=Factory.FAC_1))
        return {row.line for row in response.rows if row.row_type == RowType.DAY}

    assert lines() == {"LINE 30"}
    result = SaveLineMappingsService().handle(
        SaveLineMappingsRequest(rows=[LineMappingRowDTO(old_line="line 1", new_line="Line 2")])
    )
    assert result.message == "Đã lưu bảng số chuyền."
    assert lines() == {"LINE 2"}


def test_unchanged_catalog_save_writes_nothing() -> None:
    rows = [ProductGroupRowDTO(product_name="POLO", product_group="A")]
    SaveProductGroupsService().handle(SaveProductGroupsRequest(rows=rows))
    before = ProductGroupRuleRepository().list_all()[0].updated_at
    SaveProductGroupsService().handle(SaveProductGroupsRequest(rows=rows))
    assert ProductGroupRuleRepository().list_all()[0].updated_at == before


@pytest.mark.parametrize(
    "call",
    [
        lambda: ListGoalsService().handle(EmptyRequest()),
        lambda: SaveGoalService().handle(goal_request()),
        lambda: ListWeeklyChangeoversService().handle(EmptyRequest()),
        lambda: SaveWeeklyChangeoversService().handle(
            SaveWeeklyChangeoversRequest(from_date=START, to_date=END, counts={"Fac 1": 1})
        ),
        lambda: DeleteWeeklyChangeoverService().handle(DeleteWeeklyChangeoverRequest(id="x")),
        lambda: GetCatalogsService().handle(EmptyRequest()),
        lambda: SaveProductGroupsService().handle(SaveProductGroupsRequest()),
        lambda: SaveCustomerGroupsService().handle(SaveCustomerGroupsRequest()),
        lambda: SaveLineMappingsService().handle(SaveLineMappingsRequest()),
        lambda: SaveStyleProductsService().handle(SaveStyleProductsRequest()),
    ],
)
def test_br09_only_updaters_change_or_open_settings(call: object) -> None:
    set_current_user(CurrentUser(username="viewer", permissions=frozenset({"sewing_productivity"})))
    with pytest.raises(BusinessRuleViolation) as error:
        call()
    assert error.value.message == "Bạn chưa có quyền cập nhật dữ liệu. Hãy liên hệ quản trị viên."


def test_updated_by_records_the_display_name() -> None:
    set_current_user(CurrentUser(username="an", full_name="Nguyễn Văn A", is_admin=True))
    SaveGoalService().handle(goal_request())
    assert ListGoalsService().handle(EmptyRequest()).history[0].updated_by == "Nguyễn Văn A"
