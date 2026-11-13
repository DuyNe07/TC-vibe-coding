"""BR-70, BR-71, UC-29 (sửa 2026-11-08): the cards of Screen 4 (AC-87 to AC-90)."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from backend.features.sewing_productivity.builders.period_builders import PeriodReportResponseBuilder
from backend.features.sewing_productivity.business.period_business import PeriodBusiness
from backend.features.sewing_productivity.dto.display_names import HCM_COLUMN, TOTAL_COLUMN
from backend.features.sewing_productivity.dto.monthly_dto import MonthlyReportRequest, PeriodKind, PeriodMetricDTO
from backend.features.sewing_productivity.dto.overview_dto import Factory, OverviewRequest
from backend.features.sewing_productivity.dto.upload_dto import SaveUploadRequest
from backend.features.sewing_productivity.models.enums import Assessment
from backend.features.sewing_productivity.models.report_values import FactorySummary, PeriodRange, PeriodSummaries
from backend.features.sewing_productivity.services.get_monthly_report_service import GetMonthlyReportService
from backend.features.sewing_productivity.services.get_overview_service import GetOverviewService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.tests.workbook_factory import FAC2, FAC3, data_file, production, worker

WEEK_42 = date(2026, 10, 10)  # Saturday
WEEK_43 = date(2026, 10, 17)
FACTORIES = [Factory.FAC_2, Factory.FAC_3]


def _range(label: str, first: date, last: date) -> PeriodRange:
    return PeriodRange(label=label, from_date=first, to_date=last)


def test_br71_an_unfinished_week_is_compared_with_the_same_days_of_the_week_before():
    last = _range("W45 (31.10–05.11)", date(2026, 10, 31), date(2026, 11, 5))
    previous = _range("W44 (24.10–30.10)", date(2026, 10, 24), date(2026, 10, 30))
    days = PeriodBusiness().comparison_range(last, previous)
    assert (days.label, days.from_date, days.to_date) == (
        "vs W44 (24.10–29.10)",
        date(2026, 10, 24),
        date(2026, 10, 29),
    )


def test_br71_a_full_period_is_compared_with_the_whole_period_before():
    business = PeriodBusiness()
    week = business.comparison_range(
        _range("W44 (24.10–30.10)", date(2026, 10, 24), date(2026, 10, 30)),
        _range("W43 (17.10–23.10)", date(2026, 10, 17), date(2026, 10, 23)),
    )
    assert week.label == "vs W43 (17.10–23.10)"
    month = business.comparison_range(
        _range("Oct 2026", date(2026, 10, 1), date(2026, 10, 31)),
        _range("Sep 2026", date(2026, 9, 1), date(2026, 9, 30)),
    )
    assert (month.label, month.to_date) == ("vs Sep 2026 (01.09–30.09)", date(2026, 9, 30))
    started = business.comparison_range(
        _range("Nov 2026 (01.11–05.11)", date(2026, 11, 1), date(2026, 11, 5)),
        _range("Oct 2026", date(2026, 10, 1), date(2026, 10, 31)),
    )
    assert started.label == "vs Oct 2026 (01.10–05.10)"


def test_br70_rise_is_good_only_for_mo8h_efficiency_output_revenue():
    business = PeriodBusiness()
    assert [business.rising_is_good(field) for field in ("mo8h", "efficiency_b", "output", "cm_earning")] == [True] * 4
    for field in ("direct_workers", "average_cm_price", "average_smv", "average_hours"):
        assert business.rising_is_good(field) is None


def _load_two_weeks() -> None:
    rows, workers = [], []
    for offset in range(14):
        day = WEEK_42 + timedelta(days=offset)
        if day.weekday() == 6:  # no work on Sunday
            continue
        rows.append(production(day, FAC2, qty=400 + offset * 10, price=1.2, sewers=20, hours=8, smv=10))
        rows.append(production(day, FAC3, qty=300, price=1.5, sewers=25, hours=9, smv=20, standard=280))
        workers.append(worker(day, sf2=300, sf3=380))
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, [], workers)))


def _metric(to_date: date, name: str, kind: PeriodKind = PeriodKind.WEEK, from_date: date = WEEK_42) -> PeriodMetricDTO:
    request = MonthlyReportRequest(from_date=from_date, to_date=to_date, factories=FACTORIES, period_kind=kind)
    report = GetMonthlyReportService().handle(request)
    return next(metric for metric in report.period_metrics if metric.metric == name)


def _overview_output(from_date: date, to_date: date) -> dict[str, float | None]:
    response = GetOverviewService().handle(OverviewRequest(from_date=from_date, to_date=to_date, factories=FACTORIES))
    return next(metric.values for metric in response.metrics if metric.metric == "Sản lượng")


def test_ac87_cards_show_the_last_period_and_its_change_on_the_same_days():
    _load_two_weeks()
    last_day = WEEK_43 + timedelta(days=3)  # W43 has 4 days: 17.10–20.10
    output = _metric(last_day, "Sản lượng")
    assert output.compare_label == "vs W42 (10.10–13.10)"
    assert [card.column for card in output.cards] == ["Fac 2", "Fac 3", HCM_COLUMN, TOTAL_COLUMN]
    now = _overview_output(WEEK_43, last_day)
    before = _overview_output(WEEK_42, WEEK_42 + timedelta(days=3))
    for card in output.cards:
        assert card.value == pytest.approx(output.rows[-1].values[card.column])
        assert card.change == pytest.approx(now[card.column] - before[card.column]), card.column
    assert output.rising_is_good is True
    assert _metric(last_day, "SMV bình quân").rising_is_good is None


def test_ac89_a_full_last_week_is_compared_with_the_whole_week_before():
    _load_two_weeks()
    output = _metric(WEEK_43 + timedelta(days=6), "Sản lượng")
    assert output.compare_label == "vs W42 (10.10–16.10)"
    fac2 = next(card for card in output.cards if card.column == "Fac 2")
    assert fac2.change == pytest.approx(6 * 70)  # 6 working days, each 70 pieces more a week later


def test_ac90_one_period_has_cards_without_arrows():
    _load_two_weeks()
    output = _metric(WEEK_43 + timedelta(days=6), "Sản lượng", PeriodKind.YEAR)
    assert output.compare_label == ""
    assert output.cards
    assert all(card.change is None and card.value is not None for card in output.cards)


def test_ac102_br77_direct_labor_cards_follow_screen_1_and_are_not_coloured():
    _load_two_weeks()
    last_day = WEEK_43 + timedelta(days=3)
    labor = _metric(last_day, "%Direct labor")
    response = GetOverviewService().handle(OverviewRequest(from_date=WEEK_43, to_date=last_day, factories=FACTORIES))
    screen_1 = next(card.values for card in response.cards if card.metric == "%Direct labor")
    assert [card.column for card in labor.cards] == ["Fac 2", "Fac 3", HCM_COLUMN, TOTAL_COLUMN]
    for card in labor.cards:
        assert card.value == pytest.approx(screen_1[card.column]), card.column
    assert labor.compare_label == "vs W42 (10.10–13.10)"
    assert labor.rising_is_good is None
    assert (labor.decimals, labor.suffix) == (1, "%")


def test_ac91_cards_keep_the_red_mark_of_the_last_row():
    week = _range("W45 (31.10–05.11)", date(2026, 10, 31), date(2026, 11, 5))
    below = FactorySummary(
        factory=Factory.FAC_2, mo8h=Decimal(30), output=Decimal(100), mo8h_assessment=Assessment.BELOW
    )
    report = PeriodReportResponseBuilder([PeriodSummaries(period=week, summaries=[below])]).build()
    by_name = {metric.metric: metric for metric in report.period_metrics}
    assert by_name["MO 8h"].cards[0].below is True
    assert by_name["Sản lượng"].cards[0].below is False
    assert by_name["MO 8h"].cards[0].change is None
