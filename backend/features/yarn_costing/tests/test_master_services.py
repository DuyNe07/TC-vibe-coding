"""Service tests of UC-02..UC-09, UC-36..UC-38 (audit log, master data, recalculation, reference data)."""

import json
from decimal import Decimal

import pytest

from backend.core.config import get_settings
from backend.core.exceptions import AppError, BusinessRuleViolation
from backend.features.yarn_costing.dto.audit_dto import ListAuditLogRequest
from backend.features.yarn_costing.dto.master_dto import (
    AddExchangeRateRequest,
    ApplyRateVersionRequest,
    GetRecalcDiffRequest,
    ListRecalcBatchesRequest,
    PackagingRowDTO,
    ProcessRouteRowDTO,
    RecoveryRowDTO,
    SavePackagingTypesRequest,
    SaveProcessRoutesRequest,
    SaveRecoveryRatesRequest,
    SaveStageConfigRequest,
    UpdateTrialFactorRequest,
)
from backend.features.yarn_costing.dto.price_dto import ListPriceLinesRequest
from backend.features.yarn_costing.dto.pricing_dto import SaveYarnNsmRequest
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest
from backend.features.yarn_costing.models.enums import FactoryCode, LineType, PriceEvent, RecoveryType, Technology
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.services.add_exchange_rate_service import AddExchangeRateService
from backend.features.yarn_costing.services.apply_rate_version_service import ApplyRateVersionService
from backend.features.yarn_costing.services.get_recalc_diff_service import GetRecalcDiffService
from backend.features.yarn_costing.services.get_reference_data_service import GetReferenceDataService
from backend.features.yarn_costing.services.list_audit_log_service import ListAuditLogService
from backend.features.yarn_costing.services.list_price_lines_service import ListPriceLinesService
from backend.features.yarn_costing.services.list_recalc_batches_service import ListRecalcBatchesService
from backend.features.yarn_costing.services.save_packaging_types_service import SavePackagingTypesService
from backend.features.yarn_costing.services.save_process_routes_service import SaveProcessRoutesService
from backend.features.yarn_costing.services.save_recovery_rates_service import SaveRecoveryRatesService
from backend.features.yarn_costing.services.save_stage_config_service import SaveStageConfigService
from backend.features.yarn_costing.services.save_yarn_nsm_service import SaveYarnNsmService
from backend.features.yarn_costing.services.update_trial_factor_service import UpdateTrialFactorService
from backend.features.yarn_costing.tests.helpers import (
    S4_COMPONENTS,
    S4_NAME,
    S4_NSM,
    S4_RATES,
    TODAY,
    acting_as,
    create_request,
    rate_rows,
    setup_factory,
    user_with,
)

D = Decimal
S4 = FactoryCode.S4


def priced() -> str:
    setup_factory(S4)
    code = create_request(S4_NAME)
    SaveYarnNsmService().handle(SaveYarnNsmRequest(yarn_code=code, components=S4_COMPONENTS, nsm=S4_NSM, save=True))
    return code


def regular_total() -> Decimal:
    rows = ListPriceLinesService().handle(ListPriceLinesRequest(factory_code=S4, line_types=[LineType.THUONG])).items
    return rows[0].total_vnd


# ---- UC-02, BR-49 ---------------------------------------------------------------------------------------------------
def test_audit_log_records_the_logged_in_account_and_filters() -> None:
    priced()  # done by the logged-in Phòng SO account
    first = ListAuditLogService().handle(ListAuditLogRequest())
    assert first.items and {(e.username, e.display_name) for e in first.items} == {("so", "Phòng SO")}
    with acting_as(None):  # system code: no account
        AddExchangeRateService().handle(AddExchangeRateRequest(effective_date=TODAY, rate=D(26000)))
    with acting_as(user_with("SO", username="binh", full_name="Bình")):
        AddExchangeRateService().handle(AddExchangeRateRequest(effective_date=TODAY, rate=D(26500)))
    with acting_as(user_with("SO", username="chi")):  # no full name: the username is shown
        AddExchangeRateService().handle(AddExchangeRateRequest(effective_date=TODAY, rate=D(27000)))
    log = ListAuditLogService().handle(ListAuditLogRequest())
    assert log.usernames == ["binh", "chi", "so", "system"]
    assert "Cập nhật tỷ giá" in log.actions and "Khai báo loại đóng gói" in log.actions
    system = ListAuditLogService().handle(ListAuditLogRequest(username="system")).items
    assert [(e.username, e.display_name) for e in system] == [("system", "Hệ thống")]
    rates = ListAuditLogService().handle(ListAuditLogRequest(action="Cập nhật tỷ giá")).items
    assert [e.username for e in rates] == ["chi", "binh", "system"]  # newest first
    assert [e.display_name for e in rates] == ["chi", "Bình", "Hệ thống"]
    assert [e.username for e in ListAuditLogService().handle(ListAuditLogRequest(keyword="bình")).items] == ["binh"]
    assert not ListAuditLogService().handle(ListAuditLogRequest(date_from=TODAY.replace(year=TODAY.year + 1))).items


def test_legacy_audit_log_rows_are_converted() -> None:  # BR-61: rows of the previous app had group + person name
    folder = get_settings().data_dir / "yarn_costing"
    folder.mkdir(parents=True)
    old = {
        "id": "a1",
        "at": "2026-09-01T03:00:00+00:00",
        "group_code": "XS4",
        "person_name": "An",
        "action": "Sửa nhóm tiêu hao",
        "object_ref": "S4 / TR",
        "detail": "W: 1,00% → 1,20%",
        "reason": "x",
    }
    (folder / "audit_log.json").write_text(json.dumps([old]), encoding="utf-8")
    [entry] = AuditLogRepository().list_all()
    assert (entry.username, entry.display_name, entry.action) == ("", "Xưởng S4 - An", "Sửa nhóm tiêu hao")


# ---- UC-03..UC-09, UC-36, UC-37 -------------------------------------------------------------------------------------
def test_rate_version_recalculates_and_diff_is_listed() -> None:
    priced()
    before = regular_total()
    rates = dict(S4_RATES)
    v = rates["V"]
    rates["V"] = (v[0], v[1], str(D(v[2]) * D("1.1")), v[3], v[4])  # AC-17: Điện of V +10%
    res = ApplyRateVersionService().handle(
        ApplyRateVersionRequest(
            factory_code=S4, rows=rate_rows(S4, rates, "Type 3"), effective_date=TODAY, reason="Tăng điện"
        )
    )
    assert res.recalculated_count == 1 and "Đã áp dụng định mức mới cho S4" in res.message
    assert regular_total() > before
    batches = ListRecalcBatchesService().handle(ListRecalcBatchesRequest(factory_code=S4)).items
    assert batches[0].trigger == PriceEvent.DOI_DINH_MUC  # AC-42
    diff = GetRecalcDiffService().handle(GetRecalcDiffRequest(batch_id=batches[0].batch_id))
    assert diff.up_count == 2 and diff.items[0].diff_vnd > 0 and diff.file.content[:2] == b"PK"
    with pytest.raises(BusinessRuleViolation, match="Thiếu định mức cho"):
        ApplyRateVersionService().handle(
            ApplyRateVersionRequest(
                factory_code=S4, rows=rate_rows(S4, rates, "Type 3")[:3], effective_date=TODAY, reason="x"
            )
        )
    with pytest.raises(BusinessRuleViolation, match="Vui lòng chọn ngày hiệu lực và nhập lý do."):
        ApplyRateVersionService().handle(ApplyRateVersionRequest(factory_code=S4, rows=rate_rows(S4, rates, "Type 3")))


def test_recovery_packaging_stage_config_and_trial_factor() -> None:
    priced()
    before = regular_total()
    res = SaveRecoveryRatesService().handle(
        SaveRecoveryRatesRequest(
            factory_code=S4,
            rows=[RecoveryRowDTO(recovery_type=RecoveryType.CHAI_THO, rate=D("0.02"))],
            effective_date=TODAY,
            reason="Đo lại",
        )
    )
    assert res.recalculated_count == 1 and regular_total() > before  # AC-33
    with pytest.raises(AppError, match="Tỷ lệ hồi phế phải từ 0% đến dưới 100%."):
        SaveRecoveryRatesService().handle(
            SaveRecoveryRatesRequest(
                factory_code=S4,
                rows=[RecoveryRowDTO(recovery_type=RecoveryType.CON, rate=D(1))],
                effective_date=TODAY,
                reason="x",
            )
        )
    pk = SavePackagingTypesService().handle(
        SavePackagingTypesRequest(
            factory_code=S4,
            effective_date=TODAY,
            reason="Đổi xe",
            rows=[
                PackagingRowDTO(code="Type 3", name="Xe", minutes_per_kg=D("0.3")),
                PackagingRowDTO(code="Type 9", name="Mới", minutes_per_kg=D("0.1")),
            ],
        )
    )
    assert pk.batch is not None and "Loại đóng gói Type 9 chưa có định mức" in pk.message
    with pytest.raises(AppError, match="Phút/kg phải lớn hơn 0."):
        SavePackagingTypesService().handle(
            SavePackagingTypesRequest(factory_code=S4, rows=[PackagingRowDTO(code="Type 3", minutes_per_kg=D(0))])
        )
    ref = GetReferenceDataService().handle(GetReferenceDataRequest(factory_code=S4))
    type9 = next(p for p in ref.packaging if p.code == "Type 9")
    assert not type9.has_rate and not type9.selectable and ref.current_exchange_rate.rate == 25000  # type: ignore[union-attr]
    stages = [s for s in ref.stages]
    duplicate = [*stages, stages[0].model_copy(update={"sequence": 30})]
    with pytest.raises(BusinessRuleViolation, match="Mã công đoạn 'C1' đã có ở xưởng S4."):
        SaveStageConfigService().handle(
            SaveStageConfigRequest(factory_code=S4, rows=duplicate, effective_date=TODAY, reason="x")
        )
    ok = SaveStageConfigService().handle(
        SaveStageConfigRequest(factory_code=S4, rows=stages, effective_date=TODAY, reason="Giữ")
    )
    assert ok.message.startswith("Đã lưu cấu hình công đoạn S4. Đã tính lại 1 mã")
    with pytest.raises(AppError, match="Hệ số thí nghiệm phải lớn hơn 0."):  # AC-36
        UpdateTrialFactorService().handle(UpdateTrialFactorRequest(trial_factor=D(0), effective_date=TODAY, reason="x"))
    trial = UpdateTrialFactorService().handle(
        UpdateTrialFactorRequest(trial_factor=D("2.5"), effective_date=TODAY, reason="Mới")
    )
    assert trial.message == "Đã đổi hệ số thí nghiệm từ 3 thành 2,5. Đã cập nhật 1 dòng thí nghiệm."  # AC-13
    rows = ListPriceLinesService().handle(ListPriceLinesRequest(factory_code=S4)).items
    assert abs(rows[1].total_vnd - rows[0].total_vnd * D("2.5")) < D("0.001")


def test_routes_and_exchange_rate() -> None:
    setup_factory(S4)
    res = SaveProcessRoutesService().handle(
        SaveProcessRoutesRequest(
            factory_code=S4,
            rows=[
                ProcessRouteRowDTO(
                    yarn_group="tc",
                    technology=Technology.RING,
                    route_text="B2 - C1 - C2 - SBD - PD - LF - CM - MD1 - MD2 - MD3 - R - S - W - F",
                )
            ],
        )
    )
    assert res.message == "Đã lưu quy trình TC - Ring."
    route = GetReferenceDataService().handle(GetReferenceDataRequest(factory_code=S4)).routes[0]
    assert "S Compact" in route.route_stages and "B2" not in route.route_stages  # AC-34
    with pytest.raises(AppError, match="đã có"):
        SaveProcessRoutesService().handle(
            SaveProcessRoutesRequest(
                factory_code=S4, rows=[ProcessRouteRowDTO(yarn_group="TC", technology=Technology.RING)] * 2
            )
        )
    added = AddExchangeRateService().handle(AddExchangeRateRequest(effective_date=TODAY, rate=D(26000)))
    assert added.message.startswith("Đã thêm tỷ giá 26.000 từ ngày")
    assert GetReferenceDataService().handle(GetReferenceDataRequest()).current_exchange_rate.rate == 26000  # type: ignore[union-attr]
    with pytest.raises(AppError, match="Tỷ giá phải lớn hơn 0."):
        AddExchangeRateService().handle(AddExchangeRateRequest(effective_date=TODAY, rate=D(0)))
