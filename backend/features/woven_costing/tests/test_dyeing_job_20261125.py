"""Extension 2026-11-25 (b): dyeing job order "phiếu gia công nhuộm" (file NGC), BR-92..BR-99, AC-76..AC-83."""

from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import load_workbook

from backend.core.exceptions import AppError, BusinessRuleViolation
from backend.features.woven_costing.builders.parameter_builders import parameter_set_detail
from backend.features.woven_costing.business.costing_business import CostingBusiness
from backend.features.woven_costing.business.discount_business import DiscountBusiness
from backend.features.woven_costing.business.dyeing_job_business import DyeingJobBusiness
from backend.features.woven_costing.business.fabric_business import FabricBusiness
from backend.features.woven_costing.dto.costsheet_dto import TcdnDyeingInputDTO, TcdnStageInputDTO
from backend.features.woven_costing.dto.dyeing_job_dto import (
    CreateDyeingJobRequest,
    DyeingJobActionRequest,
    DyeingJobInputRequest,
    DyeingJobLineDTO,
    GetDyeingJobRequest,
    ListDyeingJobsRequest,
)
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.costing_context import CostingContext
from backend.features.woven_costing.models.costsheet_input import NamedCost, TcdnDyeingInput, TcdnStageInput
from backend.features.woven_costing.models.dyeing_job import DyeingJob, DyeingJobLine
from backend.features.woven_costing.models.enums import CostsheetStatus, DyePlant, SaleForm
from backend.features.woven_costing.models.norm_set import initial_tables
from backend.features.woven_costing.models.parameter_set import ParameterValues, initial_parameter_set, legacy_tables
from backend.features.woven_costing.models.parameter_tables import OpRateRow
from backend.features.woven_costing.services.approve_dyeing_job_service import ApproveDyeingJobService
from backend.features.woven_costing.services.copy_dyeing_job_service import CopyDyeingJobService
from backend.features.woven_costing.services.create_dyeing_job_service import CreateDyeingJobService
from backend.features.woven_costing.services.export_dyeing_job_service import ExportDyeingJobService
from backend.features.woven_costing.services.get_dyeing_job_service import GetDyeingJobService
from backend.features.woven_costing.services.list_dyeing_jobs_service import ListDyeingJobsService
from backend.features.woven_costing.services.save_dyeing_job_service import SaveDyeingJobService
from backend.features.woven_costing.services.submit_dyeing_job_service import SubmitDyeingJobService
from backend.features.woven_costing.tests.helpers import LEAD_FS1, SALES_FS1, SALES_FS2, TODAY, as_user, seed_master
from backend.features.woven_costing.tests.test_ac09_real_costsheets import R3

D = Decimal
P = ParameterValues()
STAGES = ["Chuẩn Bị", "Coating", "Cire", "Kiểm Trung Gian", "Kiểm Hàng-Đóng Gói"]
TOLERANCE = D("0.01")


def _sone_line(oc: str, qty: int, **changes: object) -> DyeingJobLine:
    """One row of the S-ONE file (DVDP-SAFM001-PA)."""
    stages = [TcdnStageInput(name=n, chemical_price=D(1861) if n == "Coating" else None) for n in STAGES]
    line = DyeingJobLine(item_code="DVDP-SAFM001-PA", oc_no=oc, g_per_m=D(245), g_per_m2=D(167),
                         shrinkage=D("0.01"), quantity_m=D(qty), job_price_vnd=D("7905.403"),
                         tcdn_dyeing=TcdnDyeingInput(dye_material="Poly", extra_stages=stages,
                                                     special_features=[NamedCost(name="UPF50+", amount=D(868))]))  # fmt: skip
    return line.model_copy(update=changes)


def _job(*lines: DyeingJobLine, plant: DyePlant = DyePlant.TCDN) -> DyeingJob:
    return DyeingJob(job_no="GC-SONE-2026-00001", costing_date=TODAY, dye_plant=plant, lines=list(lines))


def _calc(job: DyeingJob):  # type: ignore[no-untyped-def]
    return DyeingJobBusiness().calculate(job, initial_tables(), P, legacy_tables(P))


def test_ac76_sone_file_numbers() -> None:
    """BR-92 / BR-93 / BR-95: same numbers as the S-ONE file (Output sheet)."""
    result = _calc(_job(_sone_line("KDV20-GC-EX-0926-8643", 7404), _sone_line("KDV20-GC-EX-0926-8644", 6707)))
    for line in result.lines:
        assert abs(line.cost_per_m - D("4860.518358794666")) <= TOLERANCE
        per_stage = {c.name: c.per_m for c in line.cost_lines}
        assert abs(per_stage["Coating"] - D("2836.3714059582608")) <= TOLERANCE
        assert abs(per_stage["Cire"] - D("414.67")) <= TOLERANCE
        assert per_stage["UPF50+"] == 868
    assert abs(result.total_cost - D("68586774.56095153")) <= TOLERANCE
    assert abs(result.total_revenue - D("111553141.733")) <= TOLERANCE
    assert abs(result.gp_pct - D("0.3851650119804562")) <= D("0.000001")
    assert not result.gp_below


def test_ac77_repeat_count_doubles_items_not_typed_chemical() -> None:
    once = _calc(_job(_sone_line("A", 1000))).lines[0]
    stages = [s.model_copy(update={"repeat_count": 1}) if s.name == "Coating" else s
              for s in _sone_line("A", 1000).tcdn_dyeing.extra_stages]  # fmt: skip
    line = _sone_line("A", 1000)
    twice = _calc(_job(line.model_copy(update={"tcdn_dyeing": line.tcdn_dyeing.model_copy(
        update={"extra_stages": stages})}))).lines[0]  # fmt: skip
    a = next(c for c in once.cost_lines if c.name == "Coating")
    b = next(c for c in twice.cost_lines if c.name == "Coating")
    assert b.items.chemical == a.items.chemical == 1861
    assert abs(b.items.total_without_chemical - 2 * a.items.total_without_chemical) <= TOLERANCE


def test_ac78_quoted_items_replace_the_calculation() -> None:
    line = _sone_line("A", 1000, quoted_items=CostItems(chemical=D(3000), labor=D(500)))
    result = _calc(_job(line)).lines[0]
    assert result.quoted and result.cost_per_m == 3500


def test_ac79_hcm_line_matches_the_single_code_dyeing_job() -> None:
    """BR-94: a HCM line gives the same đ/m as a costsheet "Gia công nhuộm" (HCM) with the same inputs."""
    sheet = R3.model_copy(update={"sale_form": SaleForm.DYEING_JOB})
    single = CostingBusiness().calculate(CostingContext(costsheet=sheet, tables=initial_tables(), params=P))
    specs = sheet.fabric_snapshot.specs
    line = DyeingJobLine(item_code="X", g_per_m=specs.finished_g_per_m, g_per_m2=specs.finished_gsm,
                         quantity_m=single.finished_meters_needed, job_price_vnd=D(1), hcm_dyeing=sheet.hcm_dyeing)  # fmt: skip
    job_line = _calc(_job(line, plant=DyePlant.HCM)).lines[0]
    assert single.dyeing_per_m > 0
    assert abs(job_line.cost_per_m - single.dyeing_per_m) <= TOLERANCE


def _typed(response, **line_changes) -> DyeingJobInputRequest:  # type: ignore[no-untyped-def]
    stages = [TcdnStageInputDTO(name="Chuẩn Bị"), TcdnStageInputDTO(name="Coating", chemical_price=D(1861))]
    line = DyeingJobLineDTO(item_code="DVDP-SAFM001-PA", oc_no="KDV20-GC-EX-0926-8643", odno="2608-7041",
                            g_per_m=D(245), g_per_m2=D(167), shrinkage=D("0.01"), quantity_m=D(7404),
                            job_price_vnd=D("7905.403"),
                            tcdn_dyeing=TcdnDyeingInputDTO(dye_material="Poly", extra_stages=stages))  # fmt: skip
    data = response.input.model_dump() | {"lines": [line.model_copy(update=line_changes)]}
    return DyeingJobInputRequest(job_id=response.id, **data)


def test_ac80_flow_create_submit_approve_copy() -> None:
    seed_master()
    with as_user(SALES_FS1):
        created = CreateDyeingJobService(today=TODAY).handle(CreateDyeingJobRequest(customer_name="Ichimura Sangyo"))
        assert created.input.dye_plant == DyePlant.TCDN and created.job_no == "GC-ICHI-2026-00001"
        with pytest.raises(AppError) as missing:
            SubmitDyeingJobService().handle(
                DyeingJobActionRequest(job_id=created.id, input=_typed(created, quantity_m=None))
            )
        assert "số lượng" in missing.value.message
        saved = SaveDyeingJobService().handle(_typed(created))
        assert saved.lines[0].cost_per_m > 0 and saved.status == CostsheetStatus.NHAP
        sent = SubmitDyeingJobService().handle(DyeingJobActionRequest(job_id=created.id))
    assert sent.status == CostsheetStatus.CHO_DUYET
    with as_user(SALES_FS2), pytest.raises(BusinessRuleViolation):
        GetDyeingJobService().handle(GetDyeingJobRequest(job_id=created.id))
    with as_user(LEAD_FS1):
        approved = ApproveDyeingJobService().handle(DyeingJobActionRequest(job_id=created.id))
    assert approved.status == CostsheetStatus.DA_DUYET and not approved.editable
    with as_user(SALES_FS1):
        with pytest.raises(BusinessRuleViolation):
            SaveDyeingJobService().handle(_typed(approved))
        copy = CopyDyeingJobService(today=TODAY).handle(DyeingJobActionRequest(job_id=created.id))
        listed = ListDyeingJobsService().handle(ListDyeingJobsRequest(keyword="8643"))
    assert copy.status == CostsheetStatus.NHAP and copy.job_no == "GC-ICHI-2026-00002"
    assert copy.copied_from == created.job_no and len(copy.lines) == 1
    assert {r.job_no for r in listed.rows} == {created.job_no, copy.job_no}


def test_ac81_excel_like_the_output_sheet() -> None:
    seed_master()
    with as_user(SALES_FS1):
        created = CreateDyeingJobService(today=TODAY).handle(CreateDyeingJobRequest(customer_name="Ichimura Sangyo"))
        saved = SaveDyeingJobService().handle(_typed(created))
        file = ExportDyeingJobService().handle(GetDyeingJobRequest(job_id=created.id))
    book = load_workbook(BytesIO(file.content))
    assert book.sheetnames == ["Thông tin", "Output"]
    rows = list(book["Output"].iter_rows(values_only=True))
    header = list(rows[0])
    assert rows[1][0] == "TỔNG CỘNG" and rows[2][header.index("Số OC")] == "KDV20-GC-EX-0926-8643"
    assert rows[2][header.index("Tổng định mức (VND)")] == round(float(saved.lines[0].cost_per_m), 2)


def test_ac82_codes_starting_with_g() -> None:
    fabric = FabricBusiness()
    assert fabric.ensure_code("GC12345678") == "GC12345678"
    assert fabric.clean_code("GEF29500023SN04") == ("EF29500023", "SN04")
    with pytest.raises(BusinessRuleViolation):
        fabric.ensure_code("C1234")


def test_ac83_operation_rates_and_regression() -> None:
    rates = {r.stage: r.rate for r in legacy_tables(P).op_rates}
    assert rates["Coating"] == D("0.6") and rates["Cire"] == D("0.7") and len(rates) == 12
    assert len(parameter_set_detail(initial_parameter_set()).op_rates) == 12
    bad = legacy_tables(P).model_copy(update={"op_rates": [OpRateRow(stage="Coating", rate=D("1.5"))]})
    assert any("Hệ số vận hành Coating" in e for e in DiscountBusiness().table_errors(bad))
    # a normal TCDN costsheet stage keeps the old rule (no operation rate): Coating labor not divided by 0.6
    job_line = _calc(_job(_sone_line("A", 1000))).lines[0]
    job_coating = next(c for c in job_line.cost_lines if c.name == "Coating")
    assert job_coating.items.labor > 0
    assert date(2026, 11, 25) >= TODAY
