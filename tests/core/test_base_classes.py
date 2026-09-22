"""Contract tests of the framework base classes and logging (independent of any real feature)."""

from decimal import Decimal

import pytest

from backend.core.base import (
    BaseBusiness,
    BaseBusinessRule,
    BaseController,
    BaseEntity,
    BaseRequestDTO,
    BaseResponseDTO,
    BaseService,
    InMemoryRepository,
    JsonFileRepository,
)
from backend.core.exceptions import BusinessRuleViolation, ConfigurationError, ConflictError, NotFoundError
from backend.core.gateway import Gateway, GatewayMiddleware
from backend.core.logger import get_logger, log_file_path, read_log_entries


class Item(BaseEntity):
    name: str
    price: Decimal = Decimal(1)


class ItemRepo(InMemoryRepository[Item]):
    pass


class ItemFileRepo(JsonFileRepository[Item]):
    storage_file = "items.json"


class EchoRequest(BaseRequestDTO):
    text: str


class EchoResponse(BaseResponseDTO):
    text: str


class EchoService(BaseService[EchoRequest, EchoResponse]):
    def execute(self, request: EchoRequest) -> EchoResponse:
        return EchoResponse(text=request.text.upper())


class PositivePriceRule(BaseBusinessRule[Item]):
    code = "BR-01"
    message = "Giá phải > 0"

    def is_satisfied_by(self, target: Item) -> bool:
        return target.price > 0


class ItemBusiness(BaseBusiness[Item]):
    def rules(self):
        return (PositivePriceRule(),)


def test_repository_crud(tmp_path) -> None:
    for repo in (ItemRepo(), ItemFileRepo(file_path=tmp_path / "items.json")):
        item = repo.add(Item(name="a"))
        with pytest.raises(ConflictError):
            repo.add(item)
        item.name = "b"
        repo.update(item)
        assert repo.get_or_raise(item.id).name == "b"
        repo.delete(item.id)
        with pytest.raises(NotFoundError):
            repo.get_or_raise(item.id)


def test_json_repository_persists(tmp_path) -> None:
    ItemFileRepo(file_path=tmp_path / "x.json").save(Item(name="kept", price=Decimal("2.5")))
    assert ItemFileRepo(file_path=tmp_path / "x.json").list_all()[0].price == Decimal("2.5")


def test_service_accepts_dto_or_dict_and_validates() -> None:
    assert EchoService().handle({"text": "hi"}).text == "HI"
    assert EchoService().handle(EchoRequest(text="yo")).text == "YO"


def test_service_cannot_override_handle() -> None:
    with pytest.raises(ConfigurationError):

        class BadService(BaseService[EchoRequest, EchoResponse]):  # noqa: F841
            def handle(self, payload=None):
                return None

            def execute(self, request):
                return None


def test_rule_requires_code_format() -> None:
    with pytest.raises(ConfigurationError):

        class BadRule(BaseBusinessRule[Item]):  # noqa: F841
            code = "rule1"
            message = "x"

            def is_satisfied_by(self, target: Item) -> bool:
                return True


def test_business_collects_violations() -> None:
    with pytest.raises(BusinessRuleViolation) as info:
        ItemBusiness().ensure_valid(Item(name="a", price=Decimal(0)))
    assert info.value.violations[0].rule_code == "BR-01"


class EchoController(BaseController):
    def echo(self, request: EchoRequest) -> EchoResponse:
        return EchoService().handle(request)


def test_gateway_routes_actions_to_the_controller() -> None:
    echo = Gateway().open(EchoController)
    assert echo.echo(EchoRequest(text="ok")).text == "OK"
    with pytest.raises(AttributeError):
        echo.logger  # noqa: B018 - only use-case methods are exposed


def test_gateway_middlewares_wrap_every_call() -> None:
    seen: list[str] = []

    class Audit(GatewayMiddleware):
        def handle(self, call, proceed):
            seen.append(call.name)
            return proceed(call)

    gateway = Gateway()
    gateway.use(Audit())
    gateway.open(EchoController).echo(EchoRequest(text="x"))
    assert seen == ["EchoController.echo"]


def test_log_entries_are_written_and_filtered(tmp_path, monkeypatch) -> None:
    get_logger("backend.features.demo.services.x").warning("demo warning")
    get_logger("backend.features.other.services.y").info("other info")
    for handler in get_logger("x").parent.handlers:
        handler.flush()
    assert log_file_path().exists()
    demo = read_log_entries("demo", min_level="INFO")
    assert demo and demo[-1].message == "demo warning"
    assert all("other" not in e.source for e in demo)


def test_page_render_harness_detects_a_crashing_page() -> None:
    from streamlit.testing.v1 import AppTest

    def script() -> None:
        from frontend.core.base_page import BasePage

        class BrokenPage(BasePage):
            title = "Broken"

            def render_header(self) -> None:
                pass

            def render(self) -> None:
                raise RuntimeError("boom")

        BrokenPage("demo_feature").run()

    app = AppTest.from_function(script, default_timeout=60)
    app.run()
    assert app.error, "a crashing page must show an error box that the render test can detect"


def test_frame_to_records_gives_dto_ready_values() -> None:
    import numpy as np
    import pandas as pd

    from frontend.core.components import frame_to_records

    frame = pd.DataFrame(
        {"qty": [1, 2], "price": [2.5, None], "name": ["a", None], "day": [pd.Timestamp("2026-01-02"), pd.NaT]}
    )
    first, second = frame_to_records(frame)
    assert first == {"qty": 1, "price": 2.5, "name": "a", "day": pd.Timestamp("2026-01-02").to_pydatetime()}
    assert type(first["qty"]) is int and not isinstance(first["qty"], np.integer)
    assert second == {"qty": 2, "price": None, "name": None, "day": None}


def test_excel_like_tables_render() -> None:
    from streamlit.testing.v1 import AppTest

    def script() -> None:
        import streamlit as st

        from frontend.core.components import data_table, editable_table

        rows = [{"code": "A", "qty": 1}, {"code": "B", "qty": None}]
        picked = data_table(rows, selection="single", key="pick")
        edited = editable_table(rows, key="edit", disabled=["code"])
        empty = editable_table([], key="empty", columns=["code", "qty"], allow_add_delete=True)
        st.write(f"picked={len(picked)} edited={edited} empty={len(empty)}")

    app = AppTest.from_function(script, default_timeout=60)
    app.run()
    assert not app.exception and not app.error
    assert "picked=0" in app.markdown[0].value
    assert "{'code': 'B', 'qty': None}" in app.markdown[0].value
    assert "empty=0" in app.markdown[0].value
