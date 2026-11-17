"""Fix 2026-11-17 (Screen 13, UC-62, BR-88): ô F&I / Hệ số norm của màn Tính giá báo khách.

Màn hình lấy Hệ số norm và F&I mặc định từ form của tháng đang chọn (GetQuoteForm); trang điền lại hai ô này khi đổi tháng và
không lấy F&I = 0 của báo giá FOB khi "Dùng lại". Phần màn hình được kiểm tra bằng tests/architecture/test_pages_render.py và
chạy thử màn hình (ghi ở Fix log); ở đây kiểm tra dữ liệu mà màn hình dùng.
"""

from datetime import date
from decimal import Decimal

import pytest

from backend.features.yarn_costing.dto.material_dto import (
    CottonShareDTO,
    GetMonthlySettingRequest,
    GetQuoteFormRequest,
    Incoterm,
    ListQuotesRequest,
    SaveMonthlySettingRequest,
)
from backend.features.yarn_costing.models.exchange_rate import ExchangeRate
from backend.features.yarn_costing.repositories.exchange_rate_repository import ExchangeRateRepository
from backend.features.yarn_costing.services.calculate_quote_service import CalculateQuoteService
from backend.features.yarn_costing.services.get_monthly_setting_service import GetMonthlySettingService
from backend.features.yarn_costing.services.get_quote_form_service import GetQuoteFormService
from backend.features.yarn_costing.services.list_quotes_service import ListQuotesService
from backend.features.yarn_costing.services.save_monthly_setting_service import SaveMonthlySettingService
from backend.features.yarn_costing.tests.test_material_price import put_supima_yarn, supima_request, supima_setup

D = Decimal


@pytest.fixture(autouse=True)
def _rate() -> None:
    ExchangeRateRepository().add(ExchangeRate(effective_date=date(2026, 10, 1), rate=D(25800), created_by="test"))


def test_fix_quote_form_gives_defaults_of_the_chosen_month() -> None:
    supima_setup()
    put_supima_yarn()
    november = GetMonthlySettingService().handle(GetMonthlySettingRequest(period="2026-11"))
    SaveMonthlySettingService().handle(
        SaveMonthlySettingRequest(
            period="2026-12",
            norm_factor=D("1.15"),
            default_fi=D("0.05"),
            cotton_plan=[CottonShareDTO(origin=s.origin, percent=s.percent) for s in november.cotton_plan],
            recoveries=november.recoveries,
            supima_group_id=november.supima_group_id,
        )
    )
    forms = {p: GetQuoteFormService().handle(GetQuoteFormRequest(line_code="S4-6001", period=p)) for p in ("2026-11", "2026-12")}
    assert (forms["2026-11"].norm_factor, forms["2026-11"].default_fi) == (D("1.10"), D("0.03"))
    assert (forms["2026-12"].norm_factor, forms["2026-12"].default_fi) == (D("1.15"), D("0.05"))


def test_fix_fob_quote_stores_no_fi_cif_quote_keeps_it() -> None:
    supima_setup()
    put_supima_yarn()
    CalculateQuoteService().handle(supima_request(commit=True))  # FOB
    CalculateQuoteService().handle(supima_request(incoterm=Incoterm.CIF, fi_usd=D("0.04"), commit=True))
    saved = {q.incoterm: q for q in ListQuotesService().handle(ListQuotesRequest()).items}
    assert saved[Incoterm.FOB].fi_usd == 0 and saved[Incoterm.FOB].cif_usd is None  # "Dùng lại" không lấy số 0 này
    assert saved[Incoterm.CIF].fi_usd == D("0.04")
    assert saved[Incoterm.CIF].cif_usd == saved[Incoterm.CIF].fob_usd + D("0.04")
