"""Costsheet services UC-15..UC-25, UC-27..UC-30 with real repositories (empty SQLite per test)."""

from datetime import date
from decimal import Decimal

import pytest

from backend.core.current_user import CurrentUser
from backend.core.exceptions import AppError, BusinessRuleViolation
from backend.features.woven_costing.dto.costsheet_dto import (
    CostsheetActionRequest,
    CostsheetResponse,
    GetCostsheetRequest,
    ParameterOverrideDTO,
    SaveOcRequest,
)
from backend.features.woven_costing.dto.list_dto import ListCostsheetsRequest
from backend.features.woven_costing.exceptions import CostsheetValidationError
from backend.features.woven_costing.models.enums import CostsheetAction, CostsheetStatus, PriceType
from backend.features.woven_costing.models.master import ExchangeRate
from backend.features.woven_costing.repositories.master_repository import ExchangeRateRepository
from backend.features.woven_costing.services.approve_costsheet_service import ApproveCostsheetService
from backend.features.woven_costing.services.calculate_costsheet_service import CalculateCostsheetService
from backend.features.woven_costing.services.cancel_costsheet_service import CancelCostsheetService
from backend.features.woven_costing.services.copy_costsheet_service import CopyCostsheetService
from backend.features.woven_costing.services.create_costsheet_service import CreateCostsheetService
from backend.features.woven_costing.services.export_costsheets_service import ExportCostsheetsService
from backend.features.woven_costing.services.get_costsheet_service import GetCostsheetService
from backend.features.woven_costing.services.list_costsheets_service import ListCostsheetsService
from backend.features.woven_costing.services.list_my_tasks_service import ListMyTasksService
from backend.features.woven_costing.services.new_version_service import NewVersionService
from backend.features.woven_costing.services.return_costsheet_service import ReturnCostsheetService
from backend.features.woven_costing.services.save_draft_service import SaveDraftService
from backend.features.woven_costing.services.save_oc_service import SaveOcService
from backend.features.woven_costing.services.submit_costsheet_service import SubmitCostsheetService
from backend.features.woven_costing.tests.helpers import (
    HEAD,
    LEAD_FS1,
    LEAD_FS2,
    SALES_FS1,
    SALES_FS2,
    SELL,
    TODAY,
    as_user,
    create_request,
    full_input,
    seed_master,
    user,
)

D = Decimal


def _draft(sell: Decimal = SELL, who: CurrentUser = SALES_FS1, **changes: object) -> CostsheetResponse:
    with as_user(who):
        created = CreateCostsheetService(today=TODAY).handle(create_request())
        return SaveDraftService(today=TODAY).handle(full_input(created, sell, **changes))


def _submitted(sell: Decimal = SELL, **changes: object) -> CostsheetResponse:
    draft = _draft(sell, **changes)
    with as_user(SALES_FS1):
        return SubmitCostsheetService(today=TODAY).handle(CostsheetActionRequest(costsheet_id=draft.id))


def _approved() -> CostsheetResponse:
    sheet = _submitted()
    with as_user(LEAD_FS1):
        return ApproveCostsheetService().handle(CostsheetActionRequest(costsheet_id=sheet.id))


def test_create_costsheet_number_hints_and_calculation() -> None:
    """UC-15, AC-42 (CS-ICHI-2026-NNNNN), AC-06 (Hồ suggested: "Sợi spun không se")."""
    seed_master()
    with as_user(SALES_FS1):
        sheet = CreateCostsheetService(today=TODAY).handle(create_request())
    assert sheet.costsheet_no == "CS-ICHI-2026-00001"
    assert sheet.status == CostsheetStatus.NHAP and sheet.version == 1 and sheet.team == "FS1"
    warp = [y for y in sheet.yarn_lines if y.direction == "WARP"]
    assert all(y.is_sized for y in warp) and "Sợi spun không se" in warp[0].size_suggest_reason
    assert next(y for y in warp if y.seq == 2).is_twisted  # BR-06
    assert sheet.result.calculated and sheet.exchange_rate == D(26000)
    assert CostsheetAction.SAVE_DRAFT in sheet.allowed_actions
    assert CostsheetAction.EDIT_FABRIC not in sheet.allowed_actions  # AC-41: Peace fabric


def test_create_needs_team_and_fabric_and_rate() -> None:
    """AC-43 (BR-51), BR-03, AC-34 (BR-61)."""
    seed_master()
    with as_user(user("sales9", "SALES")), pytest.raises(BusinessRuleViolation) as no_team:
        CreateCostsheetService(today=TODAY).handle(create_request())
    assert "chưa được gán team FS1 / FS2" in no_team.value.message
    with as_user(SALES_FS1), pytest.raises(BusinessRuleViolation) as no_fabric:
        CreateCostsheetService(today=TODAY).handle(create_request(tcfno="ZZ99990000"))
    assert "chưa có trong dữ liệu gốc" in no_fabric.value.message
    with as_user(SALES_FS1), pytest.raises(BusinessRuleViolation) as no_rate:
        CreateCostsheetService(today=TODAY).handle(create_request(costing_date=date(2026, 12, 5)))
    assert no_rate.value.message == "Chưa có tỷ giá tháng 12/2026. Liên hệ SO cập nhật."


def test_calculate_never_saves_and_handles_missing_inputs() -> None:
    """UC-16: a response even without price / costsheet; BR-46 override kept with its default (AC-32)."""
    seed_master()
    draft = _draft()
    with as_user(SALES_FS1):
        request = full_input(
            draft, D("2.6"), parameter_overrides=[ParameterOverrideDTO(code="sa_rate", used_value=D("0.09"))]
        )
        calc = CalculateCostsheetService(today=TODAY).handle(request)
        empty = CalculateCostsheetService(today=TODAY).handle(
            full_input(draft).model_copy(update={"costsheet_id": None, "tcfno": "XX00000000"})
        )
    sa = next(p for p in calc.parameters if p.code == "sa_rate")
    assert sa.used_value == D("0.09") and sa.default_value == D("0.1009") and not calc.saved
    assert not empty.result.calculated and any(w.code == "BR-03" for w in empty.warnings)
    with as_user(SALES_FS1):
        saved = SaveDraftService(today=TODAY).handle(request)
    assert next(p for p in saved.parameters if p.code == "sa_rate").used_value == D("0.09")


def test_submit_with_low_gp_warns_but_sends() -> None:
    """AC-19 / UC-20: GP below the threshold is a warning only."""
    seed_master()
    sheet = _submitted(sell=D("1.6"))
    assert sheet.status == CostsheetStatus.CHO_DUYET
    assert any(w.code == "BR-28" and "GP%" in w.message for w in sheet.warnings)
    assert "Người duyệt: trưởng team FS1 hoặc trưởng đơn vị" in sheet.message


def test_submit_blocked_by_freight_and_missing_price() -> None:
    """AC-16 (BR-29) and BR-42 in one error with every message (details)."""
    seed_master()
    draft = _draft(price_type=PriceType.CIF)
    with as_user(SALES_FS1), pytest.raises(CostsheetValidationError) as error:
        SubmitCostsheetService(today=TODAY).handle(CostsheetActionRequest(costsheet_id=draft.id))
    assert "Loại giá CIF cần nhập chi phí vận chuyển (và bảo hiểm)." in error.value.details


def test_submit_blocked_by_old_yarn_price_unless_holiday() -> None:
    """AC-29: price typed Monday 16/11, sent Monday 23/11 = 5 working days -> blocked."""
    seed_master()
    with as_user(SALES_FS1):
        created = CreateCostsheetService(today=date(2026, 11, 16)).handle(create_request())
        draft = SaveDraftService(today=date(2026, 11, 16)).handle(full_input(created))
        with pytest.raises(CostsheetValidationError) as error:
            SubmitCostsheetService(today=date(2026, 11, 23)).handle(CostsheetActionRequest(costsheet_id=draft.id))
    assert any("đã quá 5 ngày làm việc" in m for m in error.value.details)


def test_approval_rights_and_return() -> None:
    """AC-20 (BR-53) and AC-21 (BR-33)."""
    seed_master()
    sheet = _submitted()
    with as_user(SALES_FS1):
        assert (
            CostsheetAction.APPROVE
            not in GetCostsheetService().handle(GetCostsheetRequest(costsheet_id=sheet.id)).allowed_actions
        )
    with as_user(HEAD):
        assert (
            CostsheetAction.APPROVE
            in GetCostsheetService().handle(GetCostsheetRequest(costsheet_id=sheet.id)).allowed_actions
        )
    with as_user(LEAD_FS2), pytest.raises(BusinessRuleViolation) as hidden:
        GetCostsheetService().handle(GetCostsheetRequest(costsheet_no=sheet.costsheet_no))
    assert hidden.value.message == "Bạn không có quyền xem costsheet này."
    with as_user(LEAD_FS1), pytest.raises(BusinessRuleViolation) as no_reason:
        ReturnCostsheetService().handle(CostsheetActionRequest(costsheet_id=sheet.id, reason=""))
    assert no_reason.value.message == "Vui lòng nhập lý do trả lại."
    with as_user(LEAD_FS1):
        returned = ReturnCostsheetService().handle(CostsheetActionRequest(costsheet_id=sheet.id, reason="Giá sợi cao"))
    assert returned.status == CostsheetStatus.TRA_LAI
    with as_user(SALES_FS1):
        tasks = ListMyTasksService(today=TODAY).handle(None)  # AC-39
    assert any(g.code == "returned" and g.rows for g in tasks.groups)


def test_team_lead_approves_own_costsheet() -> None:
    """AC-20: a costsheet created by Trưởng team FS1 is approved by that person."""
    seed_master()
    draft = _draft(who=LEAD_FS1)
    with as_user(LEAD_FS1):
        sent = SubmitCostsheetService(today=TODAY).handle(CostsheetActionRequest(costsheet_id=draft.id))
        approved = ApproveCostsheetService().handle(CostsheetActionRequest(costsheet_id=sent.id))
    assert approved.status == CostsheetStatus.DA_DUYET


def test_new_version_auto_approved_when_price_unchanged() -> None:
    """AC-22 and AC-23 (BR-35), UC-23."""
    seed_master()
    approved = _approved()
    with as_user(SALES_FS1):
        v2 = NewVersionService(today=TODAY).handle(CostsheetActionRequest(costsheet_id=approved.id))
        assert v2.version == 2 and v2.status == CostsheetStatus.NHAP
        same = full_input(v2, note="Chỉ đổi ghi chú")
        SaveDraftService(today=TODAY).handle(same)
        auto = SubmitCostsheetService(today=TODAY).handle(CostsheetActionRequest(costsheet_id=v2.id))
    assert auto.auto_approved and auto.status == CostsheetStatus.DA_DUYET
    assert {v.version: v.status for v in auto.versions}[1] == CostsheetStatus.DA_THAY_THE
    with as_user(SALES_FS1):
        v3 = NewVersionService(today=TODAY).handle(CostsheetActionRequest(costsheet_id=auto.id))
        SaveDraftService(today=TODAY).handle(full_input(v3, D("2.9")))
        pending = SubmitCostsheetService(today=TODAY).handle(CostsheetActionRequest(costsheet_id=v3.id))
    assert pending.status == CostsheetStatus.CHO_DUYET and not pending.auto_approved


def test_oc_and_close_order() -> None:
    """AC-24, AC-25, AC-26 (BR-40), AC-27 (no Hủy once closed)."""
    seed_master()
    approved = _approved()
    with as_user(SALES_FS1):
        with pytest.raises(BusinessRuleViolation) as bad:
            SaveOcService().handle(SaveOcRequest(costsheet_id=approved.id, oc_no="6564.1"))
        assert "sai định dạng" in bad.value.message
        closed = SaveOcService().handle(
            SaveOcRequest(costsheet_id=approved.id, oc_no="KDV10-SX-LO-0726-6564.1,", close_order=True)
        )
    assert closed.input.oc_no == "KDV10-SX-LO-0726-6564.1" and closed.status == CostsheetStatus.DA_CHOT_DON
    assert CostsheetAction.CANCEL not in closed.allowed_actions
    other = _approved()
    with as_user(SALES_FS1), pytest.raises(BusinessRuleViolation) as taken:
        SaveOcService().handle(SaveOcRequest(costsheet_id=other.id, oc_no="KDV10-SX-LO-0726-6564.1", close_order=True))
    assert taken.value.message == f"OC KDV10-SX-LO-0726-6564.1 đã được chốt ở costsheet {closed.costsheet_no}."


def test_cancel_needs_reason() -> None:
    """UC-25, BR-36."""
    seed_master()
    draft = _draft()
    with as_user(SALES_FS1):
        with pytest.raises(BusinessRuleViolation) as error:
            CancelCostsheetService().handle(CostsheetActionRequest(costsheet_id=draft.id, reason=" "))
        assert error.value.message == "Vui lòng nhập lý do hủy."
        cancelled = CancelCostsheetService().handle(CostsheetActionRequest(costsheet_id=draft.id, reason="Khách hủy"))
    assert cancelled.status == CostsheetStatus.HUY and CostsheetAction.COPY in cancelled.allowed_actions


def test_approved_numbers_do_not_change_with_new_rate() -> None:
    """AC-28 (BR-39): a later rate change does not touch an approved costsheet."""
    seed_master()
    approved = _approved()
    stored = ExchangeRateRepository().for_month(11, 2026)
    ExchangeRateRepository().update(stored.model_copy(update={"rate": D(27000)}))
    with as_user(SALES_FS1):
        again = CalculateCostsheetService(today=TODAY).handle(full_input(approved))
    assert again.exchange_rate == D(26000) and again.result.cogs_vnd == approved.result.cogs_vnd


def test_copy_takes_today_and_new_number() -> None:
    """AC-30 (UC-19)."""
    seed_master(rate_months=((10, 2026), (11, 2026)))
    with as_user(SALES_FS1):
        old = CreateCostsheetService(today=date(2026, 10, 10)).handle(
            create_request(costing_date=date(2026, 10, 10), oc_no="KDV10-SX-LO-0726-6564")
        )
        copy = CopyCostsheetService(today=TODAY).handle(CostsheetActionRequest(costsheet_id=old.id))
    assert copy.costsheet_no == "CS-ICHI-2026-00002" and copy.status == CostsheetStatus.NHAP
    assert copy.input.costing_date == TODAY and copy.input.oc_no == "" and copy.copied_from == f"{old.costsheet_no} v1"


def test_list_visibility_kpis_and_export() -> None:
    """AC-33 (BR-52), UC-27 KPIs, AC-38 (F-08 rows and columns)."""
    seed_master()
    _submitted()
    with as_user(SALES_FS2):
        assert ListCostsheetsService().handle(ListCostsheetsRequest()).rows == []
    with as_user(SALES_FS1):
        listed = ListCostsheetsService().handle(ListCostsheetsRequest())
        file = ExportCostsheetsService(today=TODAY).handle(ListCostsheetsRequest())
    assert listed.kpis.total == 1 and listed.kpis.pending == 1
    from backend.shared.file_io import ExcelReader

    rows = ExcelReader(sheet_name="Costsheet").read(file.content)
    assert len(rows) == 1 and list(rows[0])[:3] == ["Số costsheet", "Phiên bản", "Trạng thái"]
    assert file.filename == "danh-sach-costsheet-20261120.xlsx"


def test_read_use_cases_with_empty_database() -> None:
    """Pages load with no data and no user."""
    assert ListCostsheetsService().handle(ListCostsheetsRequest()).rows == []
    assert ListMyTasksService(today=TODAY).handle(None).groups
    with pytest.raises(AppError):
        GetCostsheetService().handle(GetCostsheetRequest(costsheet_no="CS-X-2026-00001"))


def test_rate_month_is_used() -> None:
    """BR-61: the rate of the costing month."""
    seed_master()
    ExchangeRateRepository().add(ExchangeRate(month=10, year=2026, rate=D(25000)))
    with as_user(SALES_FS1):
        sheet = CreateCostsheetService(today=TODAY).handle(create_request(costing_date=date(2026, 10, 3)))
    assert sheet.exchange_rate == D(25000)
