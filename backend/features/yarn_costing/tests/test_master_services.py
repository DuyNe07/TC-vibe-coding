"""Service tests of UC-01..UC-09, UC-36..UC-39 (users, audit, master data, recalculation, reference data)."""

from decimal import Decimal

import pytest

from backend.core.exceptions import AppError, BusinessRuleViolation
from backend.features.yarn_costing.dto.audit_dto import ListAuditLogRequest
from backend.features.yarn_costing.dto.common_dto import ActorDTO
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
from backend.features.yarn_costing.dto.user_dto import GroupMemberRowDTO, SaveUserGroupRequest, VerifyActorRequest
from backend.features.yarn_costing.models.enums import FactoryCode, LineType, PriceEvent, RecoveryType, Technology
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
from backend.features.yarn_costing.services.save_user_group_service import SaveUserGroupService
from backend.features.yarn_costing.services.save_yarn_nsm_service import SaveYarnNsmService
from backend.features.yarn_costing.services.update_trial_factor_service import UpdateTrialFactorService
from backend.features.yarn_costing.services.verify_actor_service import VerifyActorService
from backend.features.yarn_costing.tests.helpers import (
    S4_COMPONENTS,
    S4_NAME,
    S4_NSM,
    S4_RATES,
    SO,
    TODAY,
    create_request,
    rate_rows,
    setup_factory,
)

D = Decimal
S4 = FactoryCode.S4


def priced() -> str:
    setup_factory(S4)
    code = create_request(S4_NAME)
    SaveYarnNsmService().handle(
        SaveYarnNsmRequest(actor=SO, yarn_code=code, components=S4_COMPONENTS, nsm=S4_NSM, save=True)
    )
    return code


def regular_total() -> Decimal:
    rows = ListPriceLinesService().handle(ListPriceLinesRequest(factory_code=S4, line_types=[LineType.THUONG])).items
    return rows[0].total_vnd


# ---- UC-01, UC-02, UC-39 --------------------------------------------------------------------------------------------
def test_user_group_access_code_change_and_audit() -> None:
    assert VerifyActorService().handle(VerifyActorRequest(actor=SO)).message == "Đang thao tác: Phòng SO - Phòng SO."
    res = SaveUserGroupService().handle(
        SaveUserGroupRequest(
            actor=SO,
            group_code="SALES",
            name="Sales",
            new_access_code="SALES-2026",
            members=[GroupMemberRowDTO(name="Bình"), GroupMemberRowDTO(name="Chi", active=False)],
        )
    )
    assert (
        res.message == "Đã lưu nhóm Sales."
        and len(res.group.members) == 2
        and res.group.active_member_names == ["Bình"]
    )
    with pytest.raises(BusinessRuleViolation):  # AC-35: the old code no longer works
        VerifyActorService().handle(
            VerifyActorRequest(actor=ActorDTO(group_code="SALES", access_code="SALES0000", person_name="Bình"))
        )
    VerifyActorService().handle(
        VerifyActorRequest(actor=ActorDTO(group_code="SALES", access_code="SALES-2026", person_name="Bình"))
    )
    with pytest.raises(AppError, match="Mã nội bộ phải dài từ 4 đến 20 ký tự."):
        SaveUserGroupService().handle(
            SaveUserGroupRequest(actor=SO, group_code="SALES", name="Sales", new_access_code="ab")
        )
    with pytest.raises(AppError, match="Tên 'Bình' đã có trong nhóm."):
        SaveUserGroupService().handle(
            SaveUserGroupRequest(
                actor=SO, group_code="SALES", name="Sales", members=[GroupMemberRowDTO(name="Bình")] * 2
            )
        )
    log = ListAuditLogService().handle(ListAuditLogRequest(group_code="SO", keyword="mã nội bộ"))
    assert log.items and "SALES-2026" not in log.items[0].detail  # the access code is never logged


# ---- UC-03..UC-09, UC-36, UC-37 -------------------------------------------------------------------------------------
def test_rate_version_recalculates_and_diff_is_listed() -> None:
    priced()
    before = regular_total()
    rates = dict(S4_RATES)
    v = rates["V"]
    rates["V"] = (v[0], v[1], str(D(v[2]) * D("1.1")), v[3], v[4])  # AC-17: Điện of V +10%
    res = ApplyRateVersionService().handle(
        ApplyRateVersionRequest(
            actor=SO, factory_code=S4, rows=rate_rows(S4, rates, "Type 3"), effective_date=TODAY, reason="Tăng điện"
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
                actor=SO, factory_code=S4, rows=rate_rows(S4, rates, "Type 3")[:3], effective_date=TODAY, reason="x"
            )
        )
    with pytest.raises(BusinessRuleViolation, match="Vui lòng chọn ngày hiệu lực và nhập lý do."):
        ApplyRateVersionService().handle(
            ApplyRateVersionRequest(actor=SO, factory_code=S4, rows=rate_rows(S4, rates, "Type 3"))
        )


def test_recovery_packaging_stage_config_and_trial_factor() -> None:
    priced()
    before = regular_total()
    res = SaveRecoveryRatesService().handle(
        SaveRecoveryRatesRequest(
            actor=SO,
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
                actor=SO,
                factory_code=S4,
                rows=[RecoveryRowDTO(recovery_type=RecoveryType.CON, rate=D(1))],
                effective_date=TODAY,
                reason="x",
            )
        )
    pk = SavePackagingTypesService().handle(
        SavePackagingTypesRequest(
            actor=SO,
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
            SavePackagingTypesRequest(
                actor=SO, factory_code=S4, rows=[PackagingRowDTO(code="Type 3", minutes_per_kg=D(0))]
            )
        )
    ref = GetReferenceDataService().handle(GetReferenceDataRequest(factory_code=S4))
    type9 = next(p for p in ref.packaging if p.code == "Type 9")
    assert not type9.has_rate and not type9.selectable and ref.current_exchange_rate.rate == 25000  # type: ignore[union-attr]
    stages = [s for s in ref.stages]
    duplicate = [*stages, stages[0].model_copy(update={"sequence": 30})]
    with pytest.raises(BusinessRuleViolation, match="Mã công đoạn 'C1' đã có ở xưởng S4."):
        SaveStageConfigService().handle(
            SaveStageConfigRequest(actor=SO, factory_code=S4, rows=duplicate, effective_date=TODAY, reason="x")
        )
    ok = SaveStageConfigService().handle(
        SaveStageConfigRequest(actor=SO, factory_code=S4, rows=stages, effective_date=TODAY, reason="Giữ")
    )
    assert ok.message.startswith("Đã lưu cấu hình công đoạn S4. Đã tính lại 1 mã")
    with pytest.raises(AppError, match="Hệ số thí nghiệm phải lớn hơn 0."):  # AC-36
        UpdateTrialFactorService().handle(
            UpdateTrialFactorRequest(actor=SO, trial_factor=D(0), effective_date=TODAY, reason="x")
        )
    trial = UpdateTrialFactorService().handle(
        UpdateTrialFactorRequest(actor=SO, trial_factor=D("2.5"), effective_date=TODAY, reason="Mới")
    )
    assert trial.message == "Đã đổi hệ số thí nghiệm từ 3 thành 2,5. Đã cập nhật 1 dòng thí nghiệm."  # AC-13
    rows = ListPriceLinesService().handle(ListPriceLinesRequest(factory_code=S4)).items
    assert abs(rows[1].total_vnd - rows[0].total_vnd * D("2.5")) < D("0.001")


def test_routes_and_exchange_rate() -> None:
    setup_factory(S4)
    res = SaveProcessRoutesService().handle(
        SaveProcessRoutesRequest(
            actor=SO,
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
                actor=SO, factory_code=S4, rows=[ProcessRouteRowDTO(yarn_group="TC", technology=Technology.RING)] * 2
            )
        )
    added = AddExchangeRateService().handle(AddExchangeRateRequest(actor=SO, effective_date=TODAY, rate=D(26000)))
    assert added.message.startswith("Đã thêm tỷ giá 26.000 từ ngày")
    assert GetReferenceDataService().handle(GetReferenceDataRequest()).current_exchange_rate.rate == 26000  # type: ignore[union-attr]
    with pytest.raises(AppError, match="Tỷ giá phải lớn hơn 0."):
        AddExchangeRateService().handle(AddExchangeRateRequest(actor=SO, effective_date=TODAY, rate=D(0)))
