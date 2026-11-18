"""UC-29, BR-68, BR-69: the period report of Screen 4 (AC-81 to AC-84)."""

from datetime import date, timedelta

import pytest

from backend.features.sewing_productivity.business.filter_business import FilterBusiness
from backend.features.sewing_productivity.business.period_business import PeriodBusiness
from backend.features.sewing_productivity.dto.display_names import HCM_COLUMN, TOTAL_COLUMN
from backend.features.sewing_productivity.dto.monthly_dto import (
    CHANGEOVER_PER_LINE_DAY,
    MonthlyReportRequest,
    PeriodKind,
)
from backend.features.sewing_productivity.dto.overview_dto import Factory, OverviewRequest
from backend.features.sewing_productivity.dto.upload_dto import SaveUploadRequest
from backend.features.sewing_productivity.services.get_monthly_report_service import GetMonthlyReportService
from backend.features.sewing_productivity.services.get_overview_service import GetOverviewService
from backend.features.sewing_productivity.services.save_upload_service import SaveUploadService
from backend.features.sewing_productivity.tests.workbook_factory import FAC2, FAC3, data_file, production, worker

WEEK_42 = date(2026, 10, 10)  # Saturday
WEEK_43 = date(2026, 10, 17)


def _labels(from_date: date, to_date: date, kind: PeriodKind) -> list[str]:
    return [period.label for period in PeriodBusiness().periods(from_date, to_date, kind)]


def test_br68_weeks_run_saturday_to_friday_and_take_the_iso_week_of_their_friday():
    assert _labels(date(2026, 10, 10), date(2026, 10, 23), PeriodKind.WEEK) == [
        "W42 (10.10–16.10)",
        "W43 (17.10–23.10)",
    ]
    assert _labels(date(2026, 10, 12), date(2026, 10, 20), PeriodKind.WEEK) == [
        "W42 (12.10–16.10)",
        "W43 (17.10–20.10)",
    ]


def test_ac82_months_quarters_years_cut_to_the_chosen_days():
    start, end = date(2026, 9, 15), date(2026, 10, 23)
    assert _labels(start, end, PeriodKind.MONTH) == ["Sep 2026 (15.09–30.09)", "Oct 2026 (01.10–23.10)"]
    assert _labels(start, end, PeriodKind.QUARTER) == ["Q3 2026 (15.09–30.09)", "Q4 2026 (01.10–23.10)"]
    assert _labels(start, end, PeriodKind.YEAR) == ["2026 (15.09–23.10)"]
    assert _labels(date(2026, 1, 1), date(2026, 3, 31), PeriodKind.QUARTER) == ["Q1 2026"]
    assert _labels(date(2025, 12, 1), date(2026, 2, 28), PeriodKind.MONTH) == ["Dec 2025", "Jan 2026", "Feb 2026"]


def test_br31_screen4_starts_on_first_january():
    assert FilterBusiness().default_year_start(date(2026, 11, 5)) == date(2026, 1, 1)


def _load_two_weeks() -> None:
    rows, workers = [], []
    for offset in range(14):
        day = WEEK_42 + timedelta(days=offset)
        if day.weekday() == 6:  # no work on Sunday
            continue
        rows.append(production(day, FAC2, qty=400 + offset, price=1.2, sewers=20, hours=8 + offset % 3, smv=10))
        rows.append(production(day, FAC3, qty=300, price=1.5, sewers=25, hours=9, smv=20, standard=280))
        workers.append(worker(day, sf2=300 + offset, sf3=380))
    SaveUploadService().handle(SaveUploadRequest(file=data_file(rows, [], workers)))


def _period(from_date: date, to_date: date, kind: PeriodKind = PeriodKind.WEEK):
    request = MonthlyReportRequest(
        from_date=from_date, to_date=to_date, factories=[Factory.FAC_2, Factory.FAC_3], period_kind=kind
    )
    return GetMonthlyReportService().handle(request)


def _overview(from_date: date, to_date: date) -> dict[str, dict[str, float | None]]:
    response = GetOverviewService().handle(
        OverviewRequest(from_date=from_date, to_date=to_date, factories=[Factory.FAC_2, Factory.FAC_3])
    )
    return {metric.metric: metric.values for metric in [*response.metrics, *response.cards]}


def test_ac81_ac84_each_week_has_the_figures_of_screen_1_for_its_days():
    _load_two_weeks()
    report = _period(WEEK_42, WEEK_43 + timedelta(days=6))
    assert report.columns == ["Fac 2", "Fac 3", HCM_COLUMN, TOTAL_COLUMN]
    overview = _overview(WEEK_43, WEEK_43 + timedelta(days=6))
    for metric in report.period_metrics:
        assert [row.period for row in metric.rows] == ["W42 (10.10–16.10)", "W43 (17.10–23.10)"]
        if metric.metric in ("Direct worker", CHANGEOVER_PER_LINE_DAY):  # BR-89: Changeover/line/day not on Screen 1
            continue
        week_43 = metric.rows[1].values
        for column in report.columns:
            assert week_43[column] == pytest.approx(overview[metric.metric][column]), (metric.metric, column)


def test_ac83_direct_worker_is_the_average_per_day_and_groups_add_up():
    _load_two_weeks()
    report = _period(WEEK_43, WEEK_43 + timedelta(days=6))
    direct = next(metric for metric in report.period_metrics if metric.metric == "Direct worker")
    values = direct.rows[0].values
    worked = [offset for offset in range(7, 14) if (WEEK_42 + timedelta(days=offset)).weekday() != 6]
    fac2 = sum(300 + offset for offset in worked) / len(worked)
    assert values["Fac 2"] == pytest.approx(fac2)
    assert values["Fac 3"] == pytest.approx(380)
    assert values[HCM_COLUMN] == pytest.approx(fac2 + 380)


def test_period_without_production_is_left_out_and_month_view_adds_the_weeks():
    _load_two_weeks()
    weeks = _period(date(2026, 10, 3), WEEK_43 + timedelta(days=6))  # W41 has no production
    assert [row.period for row in weeks.period_metrics[0].rows] == ["W42 (10.10–16.10)", "W43 (17.10–23.10)"]
    month = _period(date(2026, 10, 1), date(2026, 10, 31), PeriodKind.MONTH)
    output = next(metric for metric in month.period_metrics if metric.metric == "Sản lượng")
    assert [row.period for row in output.rows] == ["Oct 2026"]
    assert output.rows[0].values[TOTAL_COLUMN] == pytest.approx(
        _overview(WEEK_42, WEEK_43 + timedelta(days=6))["Sản lượng"][TOTAL_COLUMN]
    )


def test_day_by_day_report_still_answers_without_a_period_kind():
    _load_two_weeks()
    response = GetMonthlyReportService().handle(MonthlyReportRequest(from_date=WEEK_42, to_date=WEEK_43))
    assert response.factories
    assert response.period_metrics == []
