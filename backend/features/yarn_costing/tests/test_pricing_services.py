"""Service tests of UC-11..UC-32 (requests, NSM, prices, loss groups, accounting codes, control checks)."""

from decimal import Decimal

import pytest

from backend.core.exceptions import AppError, BusinessRuleViolation
from backend.features.yarn_costing.dto.common_dto import ActorDTO, YarnComponentDTO
from backend.features.yarn_costing.dto.dashboard_dto import (
    CheckNsmAnomaliesRequest,
    CheckPriceAnomaliesRequest,
    GetDashboardRequest,
)
from backend.features.yarn_costing.dto.loss_dto import (
    ComponentRowDTO,
    CreatePrimaryLossGroupRequest,
    CreateSecondaryLossGroupRequest,
    DeleteLossGroupRequest,
    ListLossGroupsRequest,
    UpdateLossGroupRequest,
)
from backend.features.yarn_costing.dto.price_dto import (
    CreateAdjustmentLineRequest,
    DeleteAdjustmentLineRequest,
    ExportPriceLinesRequest,
    ListPriceLinesRequest,
    SetAccountingCodeRequest,
)
from backend.features.yarn_costing.dto.pricing_dto import (
    CorrectYarnNsmRequest,
    CreateNsmRevisionRequest,
    GetYarnDetailRequest,
    SaveYarnNsmRequest,
    SuggestNsmRequest,
)
from backend.features.yarn_costing.dto.request_dto import (
    AnalyzeYarnNameRequest,
    CancelYarnRequestRequest,
    CreateYarnRequestRequest,
    ListYarnsRequest,
    RejectYarnRequestRequest,
    UpdateYarnRequestRequest,
)
from backend.features.yarn_costing.models.enums import FactoryCode, LineType, PriceEvent, Technology, YarnStatus
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.services.analyze_yarn_name_service import AnalyzeYarnNameService
from backend.features.yarn_costing.services.cancel_yarn_request_service import CancelYarnRequestService
from backend.features.yarn_costing.services.check_nsm_anomalies_service import CheckNsmAnomaliesService
from backend.features.yarn_costing.services.check_price_anomalies_service import CheckPriceAnomaliesService
from backend.features.yarn_costing.services.correct_yarn_nsm_service import CorrectYarnNsmService
from backend.features.yarn_costing.services.create_adjustment_line_service import CreateAdjustmentLineService
from backend.features.yarn_costing.services.create_nsm_revision_service import CreateNsmRevisionService
from backend.features.yarn_costing.services.create_primary_loss_group_service import CreatePrimaryLossGroupService
from backend.features.yarn_costing.services.create_secondary_loss_group_service import CreateSecondaryLossGroupService
from backend.features.yarn_costing.services.create_yarn_request_service import CreateYarnRequestService
from backend.features.yarn_costing.services.delete_adjustment_line_service import DeleteAdjustmentLineService
from backend.features.yarn_costing.services.delete_loss_group_service import DeleteLossGroupService
from backend.features.yarn_costing.services.export_price_lines_service import ExportPriceLinesService
from backend.features.yarn_costing.services.get_dashboard_service import GetDashboardService
from backend.features.yarn_costing.services.get_yarn_detail_service import GetYarnDetailService
from backend.features.yarn_costing.services.list_loss_groups_service import ListLossGroupsService
from backend.features.yarn_costing.services.list_price_lines_service import ListPriceLinesService
from backend.features.yarn_costing.services.list_yarns_service import ListYarnsService
from backend.features.yarn_costing.services.reject_yarn_request_service import RejectYarnRequestService
from backend.features.yarn_costing.services.save_yarn_nsm_service import SaveYarnNsmService
from backend.features.yarn_costing.services.set_accounting_code_service import SetAccountingCodeService
from backend.features.yarn_costing.services.suggest_nsm_service import SuggestNsmService
from backend.features.yarn_costing.services.update_loss_group_service import UpdateLossGroupService
from backend.features.yarn_costing.services.update_yarn_request_service import UpdateYarnRequestService
from backend.features.yarn_costing.tests.helpers import (
    S4_COMPONENTS,
    S4_NAME,
    S4_NSM,
    SO,
    TODAY,
    add_member,
    create_request,
    setup_factory,
)

D = Decimal

S4 = FactoryCode.S4
CORE_KEY = "CORE (COTTON/ FDY 30D/24F/1) (70/30) MVS"


def save_nsm(code: str, actor: ActorDTO = SO, save: bool = True, **kw) -> object:
    values = {"components": S4_COMPONENTS, "nsm": S4_NSM} | kw
    return SaveYarnNsmService().handle(SaveYarnNsmRequest(actor=actor, yarn_code=code, save=save, **values))


def priced_yarn() -> str:
    setup_factory(S4)
    code = create_request(S4_NAME)
    save_nsm(code)
    return code


# ---- UC-15..UC-19, UC-40 --------------------------------------------------------------------------------------------
def test_create_update_cancel_reject_requests() -> None:
    setup_factory(S4)
    sales = add_member("SALES", "SALES0000", "Bình")
    res = CreateYarnRequestService().handle(
        CreateYarnRequestRequest(actor=sales, factory_code=S4, yarn_name="CVC 30/1 (60/40)", packaging_code="Type 3")
    )
    assert res.yarn.yarn_code == "S4-2020" and res.yarn.status == YarnStatus.CHO_XUONG_XEM  # AC-03
    assert res.message == "Đã gửi yêu cầu S4-2020 - CVC 30/1 (60/40) cho Xưởng Sợi 4."
    with pytest.raises(BusinessRuleViolation, match="đã có ở mã S4-2020"):  # AC-05
        CreateYarnRequestService().handle(
            CreateYarnRequestRequest(
                actor=sales, factory_code=S4, yarn_name="cvc 30/1  (60/40)", packaging_code="Type 3"
            )
        )
    updated = UpdateYarnRequestService().handle(
        UpdateYarnRequestRequest(
            actor=sales, yarn_code="S4-2020", yarn_name="CVC 32/1 (60/40)", packaging_code="Type 3"
        )
    )
    assert updated.yarn.count == 32 and updated.message == "Đã cập nhật yêu cầu S4-2020."
    second = create_request("PE 30/1")
    CancelYarnRequestService().handle(CancelYarnRequestRequest(actor=sales, yarn_code=second))
    assert create_request("PE 40/1") == "S4-2022"  # AC-06: cancelled code not reused
    xs4 = add_member("XS4", "XS40000", "An")
    with pytest.raises(BusinessRuleViolation, match="Vui lòng nhập lý do."):  # AC-07
        RejectYarnRequestService().handle(RejectYarnRequestRequest(actor=xs4, yarn_code="S4-2022"))
    rejected = RejectYarnRequestService().handle(
        RejectYarnRequestRequest(actor=xs4, yarn_code="S4-2022", reason="Không có máy")
    )
    assert rejected.yarn.status == YarnStatus.TU_CHOI
    with pytest.raises(BusinessRuleViolation, match="Chỉ sửa hoặc huỷ"):
        CancelYarnRequestService().handle(CancelYarnRequestRequest(actor=sales, yarn_code="S4-2022"))
    listing = ListYarnsService().handle(
        ListYarnsRequest(factory_code=S4, statuses=[YarnStatus.CHO_XUONG_XEM], oldest_first=True)
    )
    assert [i.yarn_code for i in listing.items] == ["S4-2020"] and listing.status_counts["Từ chối"] == 1  # AC-38
    with pytest.raises(BusinessRuleViolation, match="chi số dạng"):  # AC-04
        create_request("CVC 30 (60/40)")


def test_analyze_yarn_name() -> None:
    setup_factory(S4)
    res = AnalyzeYarnNameService().handle(AnalyzeYarnNameRequest(factory_code=S4, yarn_name=S4_NAME))
    assert res.valid and res.loss_group_exists and res.technology == Technology.MVS and res.count == 40
    missing = AnalyzeYarnNameService().handle(AnalyzeYarnNameRequest(factory_code=S4, yarn_name="LINEN 30/1"))
    assert not missing.loss_group_exists and "chưa có ở xưởng S4" in missing.message
    assert not AnalyzeYarnNameService().handle(AnalyzeYarnNameRequest(factory_code=S4, yarn_name="LINEN")).valid


# ---- UC-21..UC-24 ---------------------------------------------------------------------------------------------------
def test_save_nsm_prices_the_yarn_and_writes_history() -> None:
    setup_factory(S4)
    code = create_request(S4_NAME)
    preview = save_nsm(code, save=False)
    assert preview.check_passed and not preview.saved and abs(preview.line.total_vnd - D("19777.8356")) < D("0.0001")  # type: ignore[attr-defined]
    res = save_nsm(code)
    assert res.saved and res.yarn.status == YarnStatus.DA_TINH_GIA  # type: ignore[attr-defined]
    assert res.message.startswith(f"Đã lưu giá {code}: 19.778 VND/kg (0,7911 USD/kg)")  # type: ignore[attr-defined]
    assert abs(res.trial_line.total_vnd - D("19777.8356") * 3) < D("0.001")  # type: ignore[attr-defined]  # BR-30
    history = PriceHistoryRepository().list_all()
    assert {h.event for h in history} == {PriceEvent.TINH_LAN_DAU} and len(history) == 2
    detail = GetYarnDetailService().handle(GetYarnDetailRequest(line_code=f"{code}TN"))
    assert [x.line_code for x in detail.lines] == [code, f"{code}TN"] and len(detail.history) == 1
    assert detail.stage_details[0].stage_code == "C1"


def test_save_nsm_without_loss_group_then_group_added_recalculates() -> None:
    setup_factory(S4)
    code = create_request("TR 30/1 (65/35)")
    components = [
        YarnComponentDTO(material_label="PE NORMAL - RING", ratio=D("0.65"), carding_stage="C2", nsm_carding=D(45)),
        YarnComponentDTO(material_label="VISCOSE - RING", ratio=D("0.35"), carding_stage="Không chải thô"),
    ]
    res = save_nsm(code, nsm={"W": D(50)}, components=components)
    assert res.yarn.status == YarnStatus.CHUA_TINH_DUOC  # type: ignore[attr-defined]  # AC-08
    assert "Chưa có nhóm tiêu hao 'TR (65/35)'" in res.message  # type: ignore[attr-defined]
    for key, losses in (("PE NORMAL - RING", {"C2": D("0.025"), "W": D("0.01")}), ("VISCOSE - RING", {"W": D("0.02")})):
        CreatePrimaryLossGroupService().handle(
            CreatePrimaryLossGroupRequest(
                actor=SO, factory_code=S4, yarn_group_label=key, technology=Technology.RING, losses=losses
            )
        )
    group_components = [
        ComponentRowDTO(component_group_key="PE NORMAL - RING", ratio=D("0.65")),
        ComponentRowDTO(component_group_key="VISCOSE - RING", ratio=D("0.35")),
    ]
    preview = CreateSecondaryLossGroupService().handle(
        CreateSecondaryLossGroupRequest(
            actor=SO,
            factory_code=S4,
            yarn_group_label="TR (65/35)",
            technology=Technology.RING,
            components=group_components,
        )
    )
    assert not preview.saved and preview.group.losses["W"] == D("0.0135")  # AC-20
    saved = CreateSecondaryLossGroupService().handle(
        CreateSecondaryLossGroupRequest(
            actor=SO,
            factory_code=S4,
            yarn_group_label="TR (65/35)",
            technology=Technology.RING,
            components=group_components,
            save=True,
        )
    )
    assert saved.recalculated_count == 1  # BR-40
    listing = ListYarnsService().handle(ListYarnsRequest(factory_code=S4, keyword=code))
    assert listing.items[0].status == YarnStatus.DA_TINH_GIA


def test_nsm_validation_permission_and_warning() -> None:
    code = priced_yarn()
    other = create_request("CORE 30/1 (COTTON/ FDY 30D/24F/1) (70/30) MVS")
    with pytest.raises(BusinessRuleViolation, match="hiện là 90,00%"):  # AC-10
        save_nsm(other, components=[S4_COMPONENTS[0].model_copy(update={"ratio": D("0.6")}), S4_COMPONENTS[1]])
    sales = add_member("SALES", "SALES0000", "Bình")
    with pytest.raises(BusinessRuleViolation, match="Nhóm 'Sales' không được thực hiện thao tác này."):  # AC-28
        save_nsm(other, actor=sales)
    xs1 = add_member("XS1", "XS10000", "Cường")
    with pytest.raises(BusinessRuleViolation, match="xưởng S1"):
        save_nsm(other, actor=xs1)
    suggestion = SuggestNsmService().handle(SuggestNsmRequest(yarn_code=other))
    assert suggestion.found and suggestion.reference_yarn_code == code and suggestion.nsm["CM"] == 50  # AC-22
    assert [(c.material_label, c.carding_stage, c.nsm_carding) for c in suggestion.components] == [
        ("Cotton", "C1", 45),
        ("Other - C3.3", "C3", 45),
    ]
    changed = {**S4_NSM, "V": D(20)}
    faster = [S4_COMPONENTS[0].model_copy(update={"nsm_carding": D(50)}), S4_COMPONENTS[1]]
    preview = save_nsm(other, save=False, nsm=changed, components=faster)
    assert preview.warning_stages == ["C1 (Cotton)"]  # type: ignore[attr-defined]  # V (MVS) not warned
    with pytest.raises(BusinessRuleViolation, match="Vui lòng nhập lý do trước khi lưu."):
        save_nsm(other, nsm=changed, components=faster)
    saved = save_nsm(other, nsm=changed, components=faster, nsm_warning_reason="Nguyên liệu khác")
    assert saved.saved  # type: ignore[attr-defined]


def test_correct_nsm_and_lock_by_accounting_code_then_revision() -> None:
    code = priced_yarn()
    corrected = CorrectYarnNsmService().handle(
        CorrectYarnNsmRequest(actor=SO, yarn_code=code, components=S4_COMPONENTS, nsm={**S4_NSM, "V": D(26)}, save=True)
    )
    assert corrected.line.total_vnd < D("19777.8356")  # type: ignore[union-attr]  # AC-39
    assert {h.event for h in PriceHistoryRepository().list_all()} == {PriceEvent.TINH_LAN_DAU, PriceEvent.SUA_NSM}
    kt = add_member("KT", "KT0000", "Dung")
    res = SetAccountingCodeService().handle(
        SetAccountingCodeRequest(actor=kt, line_code=f"{code}TN", accounting_code=" S42003 ")
    )
    assert res.line.accounting_code == "S42003" and res.message == f"Đã lưu mã kế toán cho dòng {code}TN."  # AC-15
    detail = GetYarnDetailService().handle(GetYarnDetailRequest(yarn_code=code))
    assert detail.yarn.status == YarnStatus.CO_MA_KE_TOAN and detail.yarn.is_locked
    with pytest.raises(BusinessRuleViolation, match="đã có mã kế toán nên không sửa được"):
        CorrectYarnNsmService().handle(
            CorrectYarnNsmRequest(actor=SO, yarn_code=code, components=S4_COMPONENTS, nsm=S4_NSM, save=True)
        )
    with pytest.raises(BusinessRuleViolation, match="Vui lòng nhập lý do điều chỉnh."):  # AC-16
        CreateNsmRevisionService().handle(
            CreateNsmRevisionRequest(actor=SO, source_yarn_code=code, components=S4_COMPONENTS, nsm=S4_NSM, save=True)
        )
    revision = CreateNsmRevisionService().handle(
        CreateNsmRevisionRequest(
            actor=SO,
            source_yarn_code=code,
            adjust_reason="Đơn 50 tấn",
            components=S4_COMPONENTS,
            nsm={**S4_NSM, "V": D(30)},
            save=True,
        )
    )
    assert revision.yarn.yarn_code == f"{code} (ĐCNSM1)" and revision.message.startswith(
        f"Đã tạo bản {code} (ĐCNSM1): "
    )
    cleared = SetAccountingCodeService().handle(
        SetAccountingCodeRequest(actor=kt, line_code=f"{code}TN", accounting_code="")
    )
    assert cleared.message == f"Đã xoá mã kế toán của dòng {code}TN."
    assert GetYarnDetailService().handle(GetYarnDetailRequest(yarn_code=code)).yarn.status == YarnStatus.DA_TINH_GIA
    with pytest.raises(AppError, match="Mã kế toán tối đa 100 ký tự."):
        SetAccountingCodeService().handle(SetAccountingCodeRequest(actor=kt, line_code=code, accounting_code="x" * 101))


# ---- UC-25..UC-29 ---------------------------------------------------------------------------------------------------
def test_adjustment_lines_listing_and_export() -> None:
    code = priced_yarn()
    ck = CreateAdjustmentLineService().handle(
        CreateAdjustmentLineRequest(
            actor=SO,
            yarn_code=code,
            line_type=LineType.CHIET_KHAU,
            percent=D("0.05"),
            reason="Khách lớn",
            order_ref="PO-1",
        )
    )
    assert ck.line.line_code == f"{code} (CK1)" and ck.message.startswith(f"Đã tạo dòng {code} (CK1): ")  # AC-14
    with pytest.raises(BusinessRuleViolation, match="Vui lòng nhập lý do và đơn hàng cụ thể."):
        CreateAdjustmentLineService().handle(
            CreateAdjustmentLineRequest(
                actor=SO, yarn_code=code, line_type=LineType.PHU_PHI, percent=D("0.1"), reason="x"
            )
        )
    listing = ListPriceLinesService().handle(ListPriceLinesRequest(factory_code=S4))
    assert [r.line_type for r in listing.items] == [LineType.THUONG, LineType.THI_NGHIEM, LineType.CHIET_KHAU]
    assert listing.exchange_rate == 25000 and listing.trial_factor == 3 and listing.total_count == 3
    only_regular = ListPriceLinesService().handle(
        ListPriceLinesRequest(factory_code=S4, line_types=[LineType.THUONG], has_accounting_code=False)
    )
    assert only_regular.total_count == 1  # AC-40
    file = ExportPriceLinesService().handle(ExportPriceLinesRequest(factory_code=S4, line_types=[LineType.THUONG]))
    assert file.filename.startswith("bang-gia-soi-") and file.content[:2] == b"PK"  # AC-30
    DeleteAdjustmentLineService().handle(DeleteAdjustmentLineRequest(actor=SO, line_code=f"{code} (CK1)"))  # AC-32
    assert ListPriceLinesService().handle(ListPriceLinesRequest(factory_code=S4)).total_count == 2
    with pytest.raises(BusinessRuleViolation):
        DeleteAdjustmentLineService().handle(DeleteAdjustmentLineRequest(actor=SO, line_code=code))
    waiting = create_request("PE 30/1")
    with pytest.raises(AppError, match="chưa có giá, chưa tạo được dòng CK/PP"):
        CreateAdjustmentLineService().handle(
            CreateAdjustmentLineRequest(
                actor=SO, yarn_code=waiting, line_type=LineType.PHU_PHI, percent=D("0.1"), reason="x", order_ref="y"
            )
        )


# ---- UC-10..UC-14 ---------------------------------------------------------------------------------------------------
def test_loss_groups_list_update_lock_and_delete() -> None:
    code = priced_yarn()
    with pytest.raises(BusinessRuleViolation, match="Tiêu hao phải từ 0% đến dưới 100%."):  # AC-37
        CreatePrimaryLossGroupService().handle(
            CreatePrimaryLossGroupRequest(
                actor=SO,
                factory_code=S4,
                yarn_group_label="LINEN - RING",
                technology=Technology.RING,
                losses={"W": D("1.2")},
            )
        )
    CreatePrimaryLossGroupService().handle(
        CreatePrimaryLossGroupRequest(
            actor=SO,
            factory_code=S4,
            yarn_group_label="linen - ring",
            technology=Technology.RING,
            losses={"W": D("0.012")},
        )
    )
    listing = ListLossGroupsService().handle(ListLossGroupsRequest(factory_code=S4, keyword="linen"))
    assert listing.items[0].group_key == "LINEN - RING" and listing.items[0].used_count == 0
    xs4 = add_member("XS4", "XS40000", "An")
    res = UpdateLossGroupService().handle(
        UpdateLossGroupRequest(
            actor=xs4,
            factory_code=S4,
            group_key=CORE_KEY,
            technology=Technology.MVS,
            losses={
                "V": D("0.0315"),
                "MD3": D("0.002"),
                "MD2": D("0.002"),
                "MD1": D("0.0006"),
                "CM": D("0.15"),
                "SBD": D("0.0035"),
                "C3": D("0.034"),
                "C1": D("0.075"),
            },
            reason="Đo lại",
        )
    )
    assert res.recalculated_count == 1 and "trong đó 0 mã đã có mã kế toán" in res.message  # AC-19
    SetAccountingCodeService().handle(SetAccountingCodeRequest(actor=SO, line_code=code, accounting_code="KT1"))
    with pytest.raises(BusinessRuleViolation, match="Chỉ Phòng SO được sửa."):  # AC-18
        UpdateLossGroupService().handle(
            UpdateLossGroupRequest(
                actor=xs4,
                factory_code=S4,
                group_key=CORE_KEY,
                technology=Technology.MVS,
                losses={"V": D("0.03")},
                reason="x",
            )
        )
    assert (
        ListLossGroupsService().handle(ListLossGroupsRequest(factory_code=S4, locked_only=True)).items[0].group_key
        == CORE_KEY
    )
    with pytest.raises(BusinessRuleViolation, match="đang được dùng bởi 1 mã sợi"):  # AC-31
        DeleteLossGroupService().handle(DeleteLossGroupRequest(actor=SO, factory_code=S4, group_key=CORE_KEY))
    DeleteLossGroupService().handle(DeleteLossGroupRequest(actor=SO, factory_code=S4, group_key="LINEN - RING"))
    assert all(
        i.group_key != "LINEN - RING"
        for i in ListLossGroupsService().handle(ListLossGroupsRequest(factory_code=S4)).items
    )
    assert any(
        e.action == "Sửa nhóm tiêu hao" and e.reason == "Đo lại" for e in AuditLogRepository().list_all()
    )  # AC-48


# ---- UC-30..UC-32 ---------------------------------------------------------------------------------------------------
def test_control_checks_never_fail_on_empty_data() -> None:
    assert CheckPriceAnomaliesService().handle(CheckPriceAnomaliesRequest()).pair_count == 0
    assert CheckNsmAnomaliesService().handle(CheckNsmAnomaliesRequest()).items == []
    empty = GetDashboardService().handle(GetDashboardRequest(date_from=TODAY.replace(day=1), date_to=TODAY))
    assert not empty.has_data and empty.empty_message == "Không có dữ liệu trong khoảng ngày đã chọn."  # AC-40


def test_dashboard_counts_quoted_yarns() -> None:
    priced_yarn()
    stats = GetDashboardService().handle(
        GetDashboardRequest(factory_code=S4, date_from=TODAY.replace(day=1), date_to=TODAY)
    )
    assert stats.quoted_count == 1 and stats.new_request_count == 1 and stats.fulfilment_ratio == 100
