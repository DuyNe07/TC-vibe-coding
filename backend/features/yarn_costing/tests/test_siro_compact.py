"""BR-71 / UC-46 Siro / Compact bất thường (mở rộng 2026-11-05): AC-90..AC-94."""

from decimal import Decimal

from backend.features.yarn_costing.business.analysis_business import AnalysisBusiness
from backend.features.yarn_costing.business.siro_compact_business import CONVERTED_BASELINE, SiroCompactBusiness
from backend.features.yarn_costing.dto.dashboard_dto import CheckSiroAnomaliesRequest
from backend.features.yarn_costing.models.enums import FactoryCode, YarnStatus
from backend.features.yarn_costing.services.check_siro_anomalies_service import CheckSiroAnomaliesService
from backend.features.yarn_costing.tests.test_rules import regular, yarn

D = Decimal
S1 = FactoryCode.S1
BUSINESS = SiroCompactBusiness()


def spun(code: str, name: str, nsm: str, factory: FactoryCode = FactoryCode.S4, total: str = "20000", **extra):
    stage = "S Compact" if factory == FactoryCode.S4 and "COMPACT" in name.upper() else "S"
    return yarn(code, name, factory_code=factory, nsm={stage: D(nsm)}, lines=[regular(code, total)], **extra)


def test_kind_from_name() -> None:
    assert BUSINESS.kind_of("CM 30/1") == "Thường"
    assert BUSINESS.kind_of("CM 30/1 siro") == "Siro / Compact"
    assert BUSINESS.kind_of("CM 30/1 COMPACT LOW TWIST") == "Siro / Compact"
    assert BUSINESS.kind_of("CM 30/1 SEMI SIRO COMPACT AA") == "Siro Compact"


def test_ac90_nsm_against_normal_yarn_s1() -> None:
    ys = [
        spun("S1-1", "CM 30/1", "10.0", S1),
        spun("S1-2", "CM 30/1 SIRO", "9.5", S1),
        spun("S1-3", "CM 30/1 COMPACT", "9.0", S1),
        spun("S1-4", "CM 30/1 SIRO COMPACT", "9.0", S1),
    ]
    items = BUSINESS.nsm_anomalies(ys)
    assert [(i.yarn_code, i.standard_nsm, i.diff_percent, i.baseline) for i in items] == [
        ("S1-3", D("9.5000"), D("-5.26"), "S1-1")
    ]


def test_ac91_converted_baseline_s4() -> None:
    compact = spun("S4-1", "CVC 40/1 (60/40) COMPACT", "9.5")
    siro_compact = spun("S4-2", "CVC 40/1 (60/40) SIRO COMPACT", "8.5")
    items = BUSINESS.nsm_anomalies([compact, siro_compact])
    assert [(i.yarn_code, i.standard_nsm, i.diff_percent, i.baseline) for i in items] == [
        ("S4-2", D("9.0000"), D("-5.56"), CONVERTED_BASELINE)
    ]
    near = siro_compact.model_copy(update={"nsm": {"S Compact": D("8.95")}})
    assert BUSINESS.nsm_anomalies([compact, near]) == []


def test_ac92_price_not_higher() -> None:
    ys = [
        spun("S4-1", "TC 30/1 (65/35)", "8", total="20000"),
        spun("S4-2", "TC 30/1 (65/35) SIRO", "7.6", total="19800"),
        spun("S4-3", "TC 30/1 (65/35) SIRO COMPACT", "7.2", total="20500"),
    ]
    items = BUSINESS.price_anomalies(ys)
    assert [(i.yarn_code, i.compare_code, i.reason) for i in items] == [
        ("S4-2", "S4-1", "Sợi Siro / Compact nhưng giá không cao hơn sợi Thường")
    ]
    assert BUSINESS.nsm_anomalies(ys) == []


def test_ac93_out_of_scope_yarns_not_compared() -> None:
    base = spun("S4-1", "CM 30/1", "10")
    others = [
        spun("S4-2", "CM 40/1 SIRO", "5", total="1"),  # khác chi số
        spun("S4-3", "CD 30/1 SIRO", "5", total="1"),  # khác nhóm sợi
        spun("S4-4", "CM 30/1 SIRO", "5", S1, total="1"),  # khác xưởng
        spun("S4-5", "CM 30/1 SIRO", "5", total="1", status=YarnStatus.CHUA_TINH_DUOC),  # chưa có giá
        spun("S4-6", "CM 30/1 SIRO", "5", total="1", revision_no=1, base_code="S4-1"),  # bản ĐCNSM
        yarn("S4-7", "CM 30/1 COMPACT MVS", nsm={"V": D(1)}, lines=[regular("S4-7", "1")]),  # MVS
    ]
    assert BUSINESS.nsm_anomalies([base, *others]) == []
    assert BUSINESS.price_anomalies([base, *others]) == []


def test_ac94_old_checks_unchanged() -> None:
    a = yarn("S4-1", "CVC 30/1 (60/40)", lines=[regular("S4-1", "20000")])
    b = yarn("S4-2", "CVC 40/1 (60/40)", lines=[regular("S4-2", "19500")])
    assert [i.reason for i in AnalysisBusiness().price_anomalies([a, b])] == ["Chi số cao hơn nhưng giá không cao hơn"]


def test_uc46_service_empty_message() -> None:
    class Repo:
        def list_all(self):
            return [spun("S4-1", "CM 30/1", "10"), spun("S4-2", "CM 30/1 SIRO", "9.5", total="21000")]

    result = CheckSiroAnomaliesService(repository=Repo()).handle(CheckSiroAnomaliesRequest(factory_code=FactoryCode.S4))
    assert result.nsm_items == [] and result.price_items == []
    assert result.empty_message == "Không có mã Siro / Compact bất thường."
