"""Lists of values of feature "Năng suất xưởng may"."""

from enum import StrEnum


class Factory(StrEnum):
    FAC_1 = "Fac 1"
    FAC_2 = "Fac 2"
    FAC_3 = "Fac 3"
    FAC_5 = "Fac 5"
    FAC_1_HCM = "Fac 1 HCM (closed)"  # BR-98 (thêm 2026-11-13): kept for reference only, never on a screen or file


REPORT_FACTORIES = (Factory.FAC_1, Factory.FAC_2, Factory.FAC_3, Factory.FAC_5)  # BR-98: every report, filter, file


class FactoryGroup(StrEnum):
    """BR-51 a column that adds several factories together. Never stored."""

    HCM = "HCM"
    TOTAL = "Total"  # BR-58: every chosen factory, Vinh Long and HCM together


class PeriodKind(StrEnum):
    """BR-68 how Screen 4 cuts the chosen dates into periods. Never stored."""

    WEEK = "By week"
    MONTH = "By month"
    QUARTER = "By quarter"
    YEAR = "By year"


class UploadStatus(StrEnum):
    """BR-74 what happened to one upload (section 4.10). Stored: the values must never change."""

    SAVED = "Saved"
    REJECTED = "Rejected"


class Assessment(StrEnum):
    """BR-28 result, written in tables and Excel files."""

    PASSED = "Đạt"
    BELOW = "Dưới ngưỡng"
    NOT_AVAILABLE = "-"


class RankingMetric(StrEnum):
    """BR-44 metric used to rank the lines. Names on screen: BR-56 (`A` = with ratio - system, `B` = with ratio)."""

    EFFICIENCY_B = "Hiệu suất B"
    EFFICIENCY_A = "Hiệu suất A"
    NO_RATIO = "Hiệu suất (không tỉ lệ)"
    MO8H = "MO 8h"


class RowType(StrEnum):
    """Kind of a report row: one day, the whole period of a line, or the factory total."""

    DAY = "day"
    PERIOD = "period"
    TOTAL = "total"


class NumberKind(StrEnum):
    """BR-50 display format of a number."""

    INTEGER = "integer"
    PERCENT = "percent"
    MONEY = "money"
    KPI = "kpi"
    PEOPLE = "people"
