"""Extension 2026-11-27: approve from "Việc chờ tôi" - UC-47, UC-48, BR-101, BR-102, BR-103 (AC-95..AC-100)."""

from decimal import Decimal

from backend.features.woven_costing.business.approval_business import ApprovalBusiness
from backend.features.woven_costing.dto.costsheet_dto import CostsheetActionRequest, CostsheetResponse
from backend.features.woven_costing.dto.dyeing_job_dto import CreateDyeingJobRequest, DyeingJobActionRequest
from backend.features.woven_costing.dto.list_dto import BulkApproveRequest, TaskGroupDTO
from backend.features.woven_costing.models.costsheet_input import ExtraCost
from backend.features.woven_costing.models.enums import CostsheetStatus, DyePlant, HistoryAction, ShrinkageException
from backend.features.woven_costing.models.parameter_set import ParameterOverride
from backend.features.woven_costing.repositories.costsheet_repository import (
    CostsheetHistoryRepository,
    CostsheetRepository,
)
from backend.features.woven_costing.services.approve_costsheet_service import ApproveCostsheetService
from backend.features.woven_costing.services.approve_costsheets_service import ApproveCostsheetsService
from backend.features.woven_costing.services.approve_dyeing_jobs_service import ApproveDyeingJobsService
from backend.features.woven_costing.services.create_costsheet_service import CreateCostsheetService
from backend.features.woven_costing.services.create_dyeing_job_service import CreateDyeingJobService
from backend.features.woven_costing.services.list_my_tasks_service import ListMyTasksService
from backend.features.woven_costing.services.new_version_service import NewVersionService
from backend.features.woven_costing.services.return_costsheet_service import ReturnCostsheetService
from backend.features.woven_costing.services.save_draft_service import SaveDraftService
from backend.features.woven_costing.services.save_dyeing_job_service import SaveDyeingJobService
from backend.features.woven_costing.services.submit_costsheet_service import SubmitCostsheetService
from backend.features.woven_costing.services.submit_dyeing_job_service import SubmitDyeingJobService
from backend.features.woven_costing.tests.helpers import (
    LEAD_FS1,
    LEAD_FS2,
    SALES_FS1,
    SELL,
    TODAY,
    as_user,
    create_request,
    full_input,
    seed_master,
)
from backend.features.woven_costing.tests.test_dyeing_job_20261125 import _typed

D = Decimal
S = CostsheetStatus


def _submitted(sell: Decimal = SELL) -> CostsheetResponse:
    with as_user(SALES_FS1):
        created = CreateCostsheetService(today=TODAY).handle(create_request())
        SaveDraftService(today=TODAY).handle(full_input(created, sell))
        return SubmitCostsheetService(today=TODAY).handle(CostsheetActionRequest(costsheet_id=created.id))


def _group(code: str) -> TaskGroupDTO:
    tasks = ListMyTasksService(today=TODAY).handle(None)
    return next(g for g in tasks.groups if g.code == code)


def test_ac95_approve_many_costsheets_one_refused_others_approved() -> None:
    """AC-95 (UC-47, BR-102): 3 ticked, 1 approved meanwhile by someone else -> 2 approved, 1 reported."""
    seed_master()
    sheets = [_submitted() for _ in range(3)]
    with as_user(LEAD_FS1):
        ApproveCostsheetService().handle(CostsheetActionRequest(costsheet_id=sheets[0].id))
        result = ApproveCostsheetsService().handle(BulkApproveRequest(ids=[s.id for s in sheets]))
    assert len(result.approved) == 2 and result.message == "Đã duyệt 2 costsheet. 1 phiếu không duyệt được."
    assert result.failed == [f"Không duyệt được {sheets[0].costsheet_no} v1: Costsheet không ở trạng thái Chờ duyệt."]
    repo = CostsheetRepository()
    for sheet in sheets[1:]:
        stored = repo.get(sheet.id)
        assert stored is not None and stored.status == S.DA_DUYET and stored.approved_by == "lead1"
        actions = [h.action for h in CostsheetHistoryRepository().of_costsheet(sheet.costsheet_no)]
        assert actions.count(HistoryAction.APPROVE) == 1


def test_ac95_approve_many_respects_rights() -> None:
    """BR-102 / BR-53: Trưởng team FS2 cannot approve team FS1 costsheets; nothing changes."""
    seed_master()
    sheet = _submitted()
    with as_user(LEAD_FS2):
        result = ApproveCostsheetsService().handle(BulkApproveRequest(ids=[sheet.id]))
    assert result.approved == [] and "Bạn không có quyền duyệt costsheet này." in result.failed[0]
    stored = CostsheetRepository().get(sheet.id)
    assert stored is not None and stored.status == S.CHO_DUYET


def test_ac96_attention_text() -> None:
    """AC-96 (BR-101): the short "Cần chú ý" text; empty when nothing needs a look."""
    seed_master()
    sheet = CostsheetRepository().get(_submitted().id)
    assert sheet is not None
    business = ApprovalBusiness()
    clean = sheet.model_copy(update={"result": sheet.result.model_copy(update={"gp_below": False, "op_below": False,
                                                                                "low_shrinkage": False})})  # fmt: skip
    assert business.attention(clean) == ""
    flagged = clean.model_copy(
        update={
            "result": clean.result.model_copy(
                update={"gp_below": True, "gp_threshold": D("0.12"), "low_shrinkage": True, "shrinkage": D("0.03")}
            ),
            "parameter_overrides": [
                ParameterOverride(parameter="sa_rate", default_value=D("0.08"), used_value=D("0.09")),
                ParameterOverride(parameter="vat_rate", default_value=D("0.08"), used_value=D("0.1")),
            ],
        }
    )
    assert business.attention(flagged) == "GP dưới ngưỡng 12% · Độ co 3% · Sửa 2 tham số"
    more = clean.model_copy(
        update={"fabric_overridden": True, "shrinkage_exception": ShrinkageException.PRE_SETTING, "dye_plant": DyePlant.TCDN,
                "tcdn_dyeing": clean.tcdn_dyeing.model_copy(update={"extra_cost": ExtraCost(name="Phát sinh")})}
    )  # fmt: skip
    assert business.attention(more).endswith("Sửa thông số vải · Sửa chi phí phát sinh")
    assert business.attention(more).startswith("Độ co ")


def test_ac97_ac98_approval_row_columns_and_previous_version() -> None:
    """AC-97 (BR-103) and AC-98: v1 empty "trước", v2 shows the approved v1; chain costs per metre."""
    seed_master()
    first = _submitted()
    with as_user(LEAD_FS1):
        row = _group("approve").rows[0]
    assert row.prev_sell_price is None and row.prev_gp_pct is None
    assert row.team == "FS1" and row.fabric_name and row.sell_price == SELL and row.sell_currency == "USD"
    assert row.submitted_at is not None and row.cogs_vnd and row.gp_vnd is not None and row.price_with_vat
    sheet = CostsheetRepository().get(first.id)
    assert sheet is not None and sheet.order_meters
    assert row.yarn_per_m == sheet.result.yarn_total / sheet.order_meters
    assert row.weaving_per_m == sheet.result.weaving_total / sheet.order_meters
    assert row.dyeing_per_m == sheet.result.dyeing_total / sheet.order_meters
    with as_user(LEAD_FS1):
        approved = ApproveCostsheetService().handle(CostsheetActionRequest(costsheet_id=first.id))
    with as_user(SALES_FS1):
        v2 = NewVersionService(today=TODAY).handle(CostsheetActionRequest(costsheet_id=approved.id))
        SaveDraftService(today=TODAY).handle(full_input(v2, D("2.9")))
        sent = SubmitCostsheetService(today=TODAY).handle(CostsheetActionRequest(costsheet_id=v2.id))
    assert sent.status == S.CHO_DUYET
    with as_user(LEAD_FS1):
        row2 = _group("approve").rows[0]
    assert row2.version == 2 and row2.sell_price == D("2.9")
    assert row2.prev_sell_price == SELL and row2.prev_gp_pct == approved.result.gp_pct


def test_ac99_return_from_the_table_keeps_uc22() -> None:
    """AC-99: the "Trả lại" under the table is UC-22 (reason required)."""
    seed_master()
    sheet = _submitted()
    with as_user(LEAD_FS1):
        returned = ReturnCostsheetService().handle(CostsheetActionRequest(costsheet_id=sheet.id, reason="Sai giá sợi"))
    assert returned.status == S.TRA_LAI and returned.return_reason == "Sai giá sợi"


def test_ac100_approve_many_dyeing_jobs_and_other_groups_unchanged() -> None:
    """AC-100 (UC-48): 2 dyeing job orders approved at once; sales sees no approval group rows."""
    seed_master()
    ids = []
    with as_user(SALES_FS1):
        for _ in range(2):
            created = CreateDyeingJobService(today=TODAY).handle(
                CreateDyeingJobRequest(customer_name="Ichimura Sangyo")
            )
            SaveDyeingJobService().handle(_typed(created))
            SubmitDyeingJobService().handle(DyeingJobActionRequest(job_id=created.id))
            ids.append(created.id)
        assert _group("approve").rows == [] and _group("job_approve").rows == []
    with as_user(LEAD_FS1):
        rows = _group("job_approve").rows
        assert len(rows) == 2 and rows[0].dye_plant == "TCDN" and rows[0].total_quantity
        result = ApproveDyeingJobsService().handle(BulkApproveRequest(ids=ids))
        assert _group("job_approve").rows == []
    assert len(result.approved) == 2 and result.failed == [] and result.message == "Đã duyệt 2 phiếu gia công."
