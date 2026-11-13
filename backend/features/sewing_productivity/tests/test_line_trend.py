"""BR-90 (mở rộng 2026-11-13 lần 2): the "Line trend" of one line by week / month / year. AC-125 to AC-127."""

from datetime import date

import pytest

from backend.core.current_user import CurrentUser, set_current_user
from backend.features.sewing_productivity.dto.line_detail_dto import Factory, LineDetailRequest, PeriodKind
from backend.features.sewing_productivity.dto.upload_dto import SaveUploadRequest
from backend.features.sewing_productivity.services.get_line_detail_service import GetLineDetailService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.tests.workbook_factory import FAC2, data_file, production, worker

DAYS = [date(2026, 9, 15), date(2026, 9, 16), date(2026, 10, 24), date(2026, 10, 27), date(2026, 10, 30)]
LINE = "LINE 25"


@pytest.fixture(autouse=True)
def _updater():
    set_current_user(CurrentUser(username="an", is_admin=True))
    yield
    set_current_user(None)


def _load() -> None:
    rows = []
    for index, day in enumerate(DAYS):
        rows.append(production(day, FAC2, line=LINE, qty=400 + index * 10, standard=450, price=1.05, sewers=20))
        rows.append(
            production(day, FAC2, line=LINE, qty=100, standard=150, price=2, sewers=20, customer="MCC", po="PO-M.1")
        )
        rows.append(production(day, FAC2, line="LINE 3", qty=300, po="PO-3.1"))  # another line: never in the trend
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, [], [worker(day, sf2=60) for day in DAYS])))


def _request(from_date: date, to_date: date, **options) -> LineDetailRequest:
    return LineDetailRequest(from_date=from_date, to_date=to_date, factory=Factory.FAC_2, **options)


def _row(from_date: date, to_date: date, **options):
    detail = GetLineDetailService().handle(_request(from_date, to_date, **options))
    return {row.line: row for row in detail.line_overview}[LINE]


def test_ac125_br90_months_of_the_year_match_the_line_detail_row():
    _load()
    trend = GetLineDetailService().handle(
        _request(date(2026, 10, 24), date(2026, 10, 30), trend_line=LINE, trend_kind=PeriodKind.MONTH)
    )
    assert trend.has_data is True
    assert trend.line_overview == []  # only the trend is asked
    assert [point.period for point in trend.trend] == ["Sep 2026", "Oct 2026 (01.10–30.10)"]
    october = trend.trend[-1]
    row = _row(date(2026, 10, 1), date(2026, 10, 30))
    assert (october.output, october.efficiency, october.mo8h) == pytest.approx((row.output, row.efficiency, row.mo8h))
    assert october.start == date(2026, 10, 1)


def test_ac126_br90_weeks_end_on_the_chosen_day_and_match_the_week():
    _load()
    trend = GetLineDetailService().handle(_request(date(2026, 10, 24), date(2026, 10, 30), trend_line=LINE))
    assert trend.trend[-1].period == "W44 (24.10–30.10)"
    assert len(trend.trend) == 2  # weeks without output on the line are left out
    row = _row(date(2026, 10, 24), date(2026, 10, 30))
    last = trend.trend[-1]
    assert (last.output, last.efficiency, last.mo8h) == pytest.approx((row.output, row.efficiency, row.mo8h))
    assert last.efficiency_below == row.efficiency_below


def test_ac130_br91_by_week_shows_the_last_26_weeks_and_by_month_starts_on_first_january():
    _load()
    SaveUploadService().handle(  # one more day in March, more than 26 weeks before 30/10
        SaveUploadRequest(
            file=data_file([production(date(2026, 3, 2), FAC2, line=LINE, qty=50)], [], [worker(date(2026, 3, 2))])
        )
    )
    weeks = GetLineDetailService().handle(_request(date(2026, 10, 24), date(2026, 10, 30), trend_line=LINE)).trend
    assert [point.period for point in weeks] == ["W38 (12.09–18.09)", "W44 (24.10–30.10)"]  # March is left out
    months = (
        GetLineDetailService()
        .handle(_request(date(2026, 10, 24), date(2026, 10, 30), trend_line=LINE, trend_kind=PeriodKind.MONTH))
        .trend
    )
    assert months[0].period == "Mar 2026"


def test_ac127_br90_customer_filter_keeps_output_and_efficiency_and_hides_mo8h():
    _load()
    trend = GetLineDetailService().handle(
        _request(
            date(2026, 10, 24), date(2026, 10, 30), trend_line=LINE, trend_kind=PeriodKind.YEAR, customer_groups=["MCC"]
        )
    )
    year = trend.trend[-1]
    assert year.output == 500  # 5 days x 100 MCC pieces
    assert year.efficiency == pytest.approx(500 / 750 * 100)
    assert year.mo8h is None
