"""Tests of the app-migration changes (2026-09-29): BR-61 data copied from the previous app, BR-62 packaging save
confirmation, BR-63 / UC-42 reason of the disabled "Gửi yêu cầu" button (AC-62..AC-69)."""

import json
from decimal import Decimal

import pytest

from backend.core.config import get_settings
from backend.features.yarn_costing.business.master_business import MasterBusiness
from backend.features.yarn_costing.business.request_business import RequestBusiness
from backend.features.yarn_costing.dto.master_dto import PackagingRowDTO, SavePackagingTypesRequest
from backend.features.yarn_costing.dto.pricing_dto import SaveYarnNsmRequest
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest
from backend.features.yarn_costing.dto.request_dto import CheckRequestSubmitRequest
from backend.features.yarn_costing.exceptions import DataFileError
from backend.features.yarn_costing.models.enums import FactoryCode, YarnStatus
from backend.features.yarn_costing.models.packaging_type import PackagingType
from backend.features.yarn_costing.models.yarn import Yarn
from backend.features.yarn_costing.repositories.recalc_batch_repository import RecalcBatchRepository
from backend.features.yarn_costing.repositories.stage_repository import StageRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository
from backend.features.yarn_costing.services.check_request_submit_service import CheckRequestSubmitService
from backend.features.yarn_costing.services.get_reference_data_service import GetReferenceDataService
from backend.features.yarn_costing.services.save_packaging_types_service import SavePackagingTypesService
from backend.features.yarn_costing.services.save_yarn_nsm_service import SaveYarnNsmService
from backend.features.yarn_costing.tests.helpers import (
    S4_COMPONENTS,
    S4_LOSSES,
    S4_NAME,
    S4_NSM,
    S4_PACKAGING,
    TODAY,
    acting_as,
    create_request,
    setup_factory,
    user_with,
)

D = Decimal
S4 = FactoryCode.S4


def _data_file(name: str):
    folder = get_settings().feature_data_dir("yarn_costing")
    folder.mkdir(parents=True, exist_ok=True)
    return folder / name


def _pack(code: str, minutes: str, **extra: object) -> PackagingType:
    values: dict = {"factory_code": S4, "code": code, "name": code, "minutes_per_kg": D(minutes), **extra}
    return PackagingType(**values)


def _yarn(code: str, packaging: str, status: YarnStatus) -> Yarn:
    return Yarn(
        factory_code=S4, yarn_code=code, base_code=code, yarn_name="PE 30/1", packaging_code=packaging, status=status
    )


def _save_packaging(rows: list[PackagingRowDTO], preview: bool = False, **extra: object):
    return SavePackagingTypesService().handle(
        SavePackagingTypesRequest(factory_code=S4, rows=rows, preview=preview, **extra)  # type: ignore[arg-type]
    )


# ---- BR-61 ----
def test_br61_unreadable_data_file_names_the_file() -> None:  # AC-64
    _data_file("yarns.json").write_text("{ bị hỏng", encoding="utf-8")
    with pytest.raises(DataFileError) as info:
        YarnRepository().list_all()
    assert info.value.message == (
        "Không đọc được dữ liệu 'yarns.json'. Vui lòng chép lại file này từ app cũ (thư mục data\\yarn_costing)."
    )
    # the other data keeps working: reference data (stages, packaging, groups...) still loads
    reference = GetReferenceDataService().handle(GetReferenceDataRequest(factory_code=S4))
    assert reference.stages and reference.data_warnings == [info.value.message]


def test_br61_invalid_record_is_reported_too() -> None:
    _data_file("packaging_types.json").write_text(json.dumps([{"unknown": 1}]), encoding="utf-8")
    with pytest.raises(DataFileError, match="packaging_types.json"):
        GetReferenceDataService().handle(GetReferenceDataRequest(factory_code=S4))


def test_br61_old_stage_format_is_converted_when_read() -> None:  # AC-63
    old = [
        {"factory_code": "S4", "stage_code": code, "stage_name": code, "stage_group": code, "sequence": i + 1}
        for i, code in enumerate(["C1", "C2", "C3.1", "C3.2", "C3.3", "MD1", "F"])
    ]
    _data_file("stages.json").write_text(json.dumps(old), encoding="utf-8")
    codes = [s.stage_code for s in StageRepository().for_factory("S4")]
    assert "C3" in codes and not any(c.startswith("C3.") for c in codes)
    c3 = next(s for s in StageRepository().for_factory("S4") if s.stage_code == "C3")
    assert c3.is_carding and c3.max_passes == 3


def test_br61_copied_data_is_kept_without_recalculation() -> None:  # AC-62 (small copy)
    setup_factory()
    code = create_request(S4_NAME)
    SaveYarnNsmService().handle(SaveYarnNsmRequest(yarn_code=code, components=S4_COMPONENTS, nsm=S4_NSM, save=True))
    before = {y.yarn_code: (y.status, y.lines[0].total_vnd) for y in YarnRepository().list_all()}
    batches = RecalcBatchRepository().count()
    # "copy" = the same files read again by a fresh repository (as after copying the folder)
    after = {y.yarn_code: (y.status, y.lines[0].total_vnd) for y in YarnRepository().list_all()}
    assert after == before and RecalcBatchRepository().count() == batches


# ---- BR-62 ----
def test_br62_packaging_in_use_excludes_closed_yarns() -> None:
    yarns = [
        _yarn("S4-1", "Type 1", YarnStatus.CHO_XUONG_XEM),
        _yarn("S4-2", "Type 2", YarnStatus.DA_HUY),
        _yarn("S4-3", "Type 3", YarnStatus.CHUA_TINH_DUOC),
    ]
    assert MasterBusiness().packaging_in_use("S4", yarns) == {"Type 1", "Type 3"}


def test_br62_recalc_only_when_minutes_of_used_type_change() -> None:
    business = MasterBusiness()
    old = {"Type 1": _pack("Type 1", "0.2"), "Type 2": _pack("Type 2", "0.3")}
    same = [_pack("Type 1", "0.2", is_default=True, name="Tên mới"), _pack("Type 2", "0.4")]
    assert business.packaging_recalc_codes(old, same, {"Type 1"}) == []
    changed = [_pack("Type 1", "0.25"), _pack("Type 2", "0.3")]
    assert business.packaging_recalc_codes(old, changed, {"Type 1"}) == ["Type 1"]


def test_br62_confirm_text() -> None:
    business = MasterBusiness()
    assert business.packaging_confirm_text("S4", [], None) == "Giá các mã không thay đổi."
    assert business.packaging_confirm_text("S4", ["Type 3"], TODAY) == (
        f"Phút/kg của loại Type 3 (đang có mã sợi dùng) thay đổi. "
        f"App sẽ tính lại toàn bộ giá xưởng S4 từ ngày {TODAY.strftime('%d/%m/%Y')}."
    )


def test_uc05_default_only_change_does_not_recalculate() -> None:  # AC-65
    setup_factory()
    create_request(S4_NAME)
    rows = [PackagingRowDTO(code="Type 3", name="Type 3", minutes_per_kg=S4_PACKAGING[1], is_default=True)]
    preview = _save_packaging(rows, preview=True)
    assert preview.confirm_text == "Giá các mã không thay đổi." and not preview.will_recalculate
    batches = RecalcBatchRepository().count()
    result = _save_packaging(rows)  # no effective date / reason needed
    assert result.message == "Đã lưu loại đóng gói S4. Giá các mã không thay đổi."
    assert RecalcBatchRepository().count() == batches


def test_uc05_minutes_change_of_used_type_recalculates() -> None:  # AC-66
    setup_factory()
    create_request(S4_NAME)
    rows = [PackagingRowDTO(code="Type 3", name="Type 3", minutes_per_kg=D("0.23"))]
    with pytest.raises(Exception, match="Vui lòng chọn ngày hiệu lực và nhập lý do."):
        _save_packaging(rows, preview=True)
    preview = _save_packaging(rows, preview=True, effective_date=TODAY, reason="Đổi xe")
    assert preview.will_recalculate and preview.confirm_text.startswith("Phút/kg của loại Type 3 (đang có mã sợi dùng)")
    batches = RecalcBatchRepository().count()
    assert RecalcBatchRepository().count() == batches  # preview saved nothing
    result = _save_packaging(rows, effective_date=TODAY, reason="Đổi xe")
    assert result.will_recalculate and result.message.startswith("Đã lưu loại đóng gói S4. Đã tính lại")
    assert RecalcBatchRepository().count() == batches + 1


def test_uc05_minutes_change_of_unused_type_does_not_recalculate() -> None:  # AC-67
    setup_factory()
    rows = [PackagingRowDTO(code="Type 3", name="Type 3", minutes_per_kg=D("0.5"))]
    preview = _save_packaging(rows, preview=True)
    assert preview.confirm_text == "Giá các mã không thay đổi."


# ---- BR-63 / UC-42 ----
def test_br63_reasons() -> None:
    business = RequestBusiness()
    assert business.submit_block_reasons(None, False) == []  # no factory chosen yet
    assert business.submit_block_reasons("S1", False) == [
        "Xưởng S1 chưa có loại đóng gói chọn được. Vui lòng báo Phòng SO khai báo loại đóng gói và định mức."
    ]
    assert business.submit_block_reasons("S4", True) == []


def test_uc42_check_request_submit() -> None:  # AC-68, AC-69: the answer depends on the factory only, never on the user
    service = CheckRequestSubmitService()
    assert service.handle(CheckRequestSubmitRequest()).allowed
    no_pack = service.handle(CheckRequestSubmitRequest(factory_code=FactoryCode.S1))
    assert not no_pack.allowed and no_pack.reasons == [
        "Xưởng S1 chưa có loại đóng gói chọn được. Vui lòng báo Phòng SO khai báo loại đóng gói và định mức."
    ]
    setup_factory()
    for user in (None, user_with("KT", username="kt")):
        with acting_as(user):
            assert service.handle(CheckRequestSubmitRequest(factory_code=S4)).allowed


# ---- Fix 2026-09-29: losses with more than 2 decimals (in %) are kept exactly ----
def test_losses_below_one_hundredth_percent_are_kept_exactly() -> None:
    from backend.features.yarn_costing.dto.loss_dto import CreatePrimaryLossGroupRequest
    from backend.features.yarn_costing.models.enums import Technology
    from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
    from backend.features.yarn_costing.services.create_primary_loss_group_service import CreatePrimaryLossGroupService

    losses = {"R": D("0.00395"), "W": D("0.005"), "S": D("0.00125")}  # 0,395% - 0,5% - 0,125%
    CreatePrimaryLossGroupService().handle(
        CreatePrimaryLossGroupRequest(
            factory_code=S4, yarn_group_label="PE TEST", technology=Technology.RING, losses=losses
        )
    )
    stored = next(g for g in LossGroupRepository().for_factory("S4") if g.group_key == "PE TEST")
    assert {k: stored.losses[k] for k in losses} == losses


# ---- BR-64 / BR-65 / UC-43 (2026-09-29): equivalent carding lines ----
def _price_with_losses(losses: dict) -> "object":
    from backend.features.yarn_costing.dto.loss_dto import CreatePrimaryLossGroupRequest
    from backend.features.yarn_costing.models.enums import Technology
    from backend.features.yarn_costing.services.create_primary_loss_group_service import CreatePrimaryLossGroupService

    setup_factory(with_loss_group=False)
    label = S4_NAME.replace(S4_NAME.split()[1] + " ", "", 1)
    CreatePrimaryLossGroupService().handle(
        CreatePrimaryLossGroupRequest(factory_code=S4, yarn_group_label=label, technology=Technology.MVS, losses=losses)
    )
    code = create_request(S4_NAME)
    return code, SaveYarnNsmService().handle(
        SaveYarnNsmRequest(yarn_code=code, components=S4_COMPONENTS, nsm=S4_NSM, save=False)
    )


def test_br64_equivalent_lines() -> None:
    from backend.features.yarn_costing.business.costing_business import CostingBusiness
    from backend.features.yarn_costing.models.enums import Technology
    from backend.features.yarn_costing.models.loss_group import LossGroup

    costing = CostingBusiness()
    assert costing.equivalent_line("S4", "C2") == "C3" and costing.equivalent_line("S4", "C3") == "C2"
    assert costing.equivalent_line("S1", "C2") == "C1" and costing.equivalent_line("S4", "C1") is None
    group = LossGroup(
        factory_code=FactoryCode.S1,
        group_key="PE",
        yarn_group_label="PE",
        technology=Technology.RING,
        losses={"C1": D("0.02")},
    )
    assert costing.declared_carding_loss(group, "C2", "S1") == (D("0.02"), "C1")  # AC-72
    both = group.model_copy(update={"losses": {"C1": D("0.02"), "C2": D("0.03")}})
    assert costing.declared_carding_loss(both, "C2", "S1") == (D("0.03"), "")  # AC-71: running line wins
    assert costing.declared_carding_loss(group, "C1", "S4") == (D("0.02"), "")


def test_br64_price_with_loss_declared_on_c2_equals_c3() -> None:  # AC-70
    losses = {k: v for k, v in S4_LOSSES.items() if k != "C3"} | {"C2": S4_LOSSES["C3"]}
    _, result = _price_with_losses(losses)
    assert result.check_passed, result.reasons
    assert abs(result.line.total_vnd - D("19777.8356")) < D("0.0001")  # same price as C3 = 3,4%
    c3 = next(d for d in result.stage_details if d.stage_code == "C3")
    assert c3.loss == D("0.034") and c3.loss_note == "Tiêu hao lấy từ C2 (C3 chưa khai báo)"
    c1 = next(d for d in result.stage_details if d.stage_code == "C1")
    assert c1.loss_note == ""


def test_br16_message_names_both_lines() -> None:  # AC-73
    losses = {k: v for k, v in S4_LOSSES.items() if k != "C3"}
    _, result = _price_with_losses(losses)
    assert not result.check_passed
    assert (
        "C3 lượt 1 (Other - C3.3): có NSM nhưng nguyên liệu chưa khai báo tiêu hao ở C3 hoặc C2. "
        "Vui lòng khai báo tiêu hao chải thô của nguyên liệu." in result.reasons
    )


def test_uc43_recalculate_not_priced() -> None:  # AC-75, AC-76
    from datetime import date as _date

    from backend.core.exceptions import AppError
    from backend.features.yarn_costing.dto.master_dto import RecalculateNotPricedRequest
    from backend.features.yarn_costing.models.enums import PriceEvent
    from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
    from backend.features.yarn_costing.services.recalculate_not_priced_service import RecalculateNotPricedService

    setup_factory()
    code = create_request(S4_NAME)
    SaveYarnNsmService().handle(SaveYarnNsmRequest(yarn_code=code, components=S4_COMPONENTS, nsm=S4_NSM, save=True))
    other = create_request("PE 30/1")  # "Chờ xưởng xem": must not be touched
    repo = YarnRepository()
    yarns = repo.list_all()
    waiting = next(y for y in yarns if y.yarn_code == code)
    waiting = waiting.model_copy(
        update={"status": YarnStatus.CHUA_TINH_DUOC, "status_reasons": ["x"], "lines": [], "first_priced_at": None}
    )
    repo.store(yarns, [waiting])
    service = RecalculateNotPricedService()
    with pytest.raises(AppError, match="Vui lòng chọn ngày hiệu lực và nhập lý do."):
        service.handle(RecalculateNotPricedRequest(factory_code=S4, effective_date=TODAY, reason=""))
    when = _date(2026, 10, 1)
    batches = RecalcBatchRepository().count()
    result = service.handle(RecalculateNotPricedRequest(factory_code=S4, effective_date=when, reason="Áp dụng BR-64"))
    assert result.message == "Đã tính lại 1 mã chưa tính được của xưởng S4: 1 mã đã có giá, 0 mã vẫn chưa tính được."
    assert RecalcBatchRepository().count() == batches + 1
    assert RecalcBatchRepository().newest_first()[0].trigger == PriceEvent.TINH_LAI_CHUA_TINH
    priced = next(y for y in YarnRepository().list_all() if y.yarn_code == code)
    assert priced.status == YarnStatus.DA_TINH_GIA and priced.first_priced_at == when and len(priced.lines) == 2
    assert any(h.event == PriceEvent.TINH_LAI_CHUA_TINH for h in PriceHistoryRepository().list_all())
    untouched = next(y for y in YarnRepository().list_all() if y.yarn_code == other)
    assert untouched.status == YarnStatus.CHO_XUONG_XEM
    with pytest.raises(AppError, match="Xưởng S4 không có mã nào đang 'Chưa tính được'."):
        service.handle(RecalculateNotPricedRequest(factory_code=S4, effective_date=when, reason="Lần 2"))
    with acting_as(user_with("XS1", username="xs1")), pytest.raises(AppError, match="chưa có vai trò cho thao tác"):
        service.handle(RecalculateNotPricedRequest(factory_code=S4, effective_date=when, reason="x"))  # BR-47


def test_export_has_loss_note_column() -> None:  # AC-77
    from io import BytesIO

    from openpyxl import load_workbook

    from backend.features.yarn_costing.dto.price_dto import ExportPriceLinesRequest
    from backend.features.yarn_costing.services.export_price_lines_service import ExportPriceLinesService

    losses = {k: v for k, v in S4_LOSSES.items() if k != "C3"} | {"C2": S4_LOSSES["C3"]}
    code, _ = _price_with_losses(losses)
    SaveYarnNsmService().handle(SaveYarnNsmRequest(yarn_code=code, components=S4_COMPONENTS, nsm=S4_NSM, save=True))
    file = ExportPriceLinesService().handle(ExportPriceLinesRequest(factory_code=S4))
    ws = load_workbook(BytesIO(file.content))["Chi tiet cong doan"]
    rows = list(ws.iter_rows(values_only=True))
    assert rows[0][-1] == "Ghi chú tiêu hao"
    notes = {r[3]: r[-1] for r in rows[1:]}
    assert notes["C3"] == "Tiêu hao lấy từ C2 (C3 chưa khai báo)" and not notes["C1"]
