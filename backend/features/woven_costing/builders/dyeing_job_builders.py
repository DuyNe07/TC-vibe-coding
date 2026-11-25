"""Dyeing job order (2026-11-25): typed cells -> model, model -> Screen 8 response / list rows, F-09 Excel."""

from decimal import Decimal

from backend.core.base import BaseBuilder, FileDownloadDTO, MimeType
from backend.features.woven_costing.builders.costsheet_input_builder import hcm_input, tcdn_input
from backend.features.woven_costing.builders.costsheet_response_builder import _extra
from backend.features.woven_costing.dto.common_dto import WarningDTO
from backend.features.woven_costing.dto.costsheet_dto import DyeingLineDTO
from backend.features.woven_costing.dto.dyeing_job_dto import (
    CostItemsDTO,
    DyeingJobInputDTO,
    DyeingJobLineDTO,
    DyeingJobLineResultDTO,
    DyeingJobResponse,
    DyeingJobRowDTO,
)
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.costsheet_result import DyeingLine
from backend.features.woven_costing.models.dyeing_job import MAX_JOB_LINES, DyeingJob, DyeingJobLine
from backend.features.woven_costing.models.enums import CostsheetAction
from backend.shared.file_io import ExcelWriter

ZERO = Decimal(0)
ONE = Decimal(1)
JOB_KIND = "NHẬN GIA CÔNG"


def _rate(value: Decimal | None) -> Decimal:
    """A % typed in 0..1; anything outside is kept for BR-97 to report."""
    return value if value is not None else ZERO


def line_from_dto(dto: DyeingJobLineDTO) -> DyeingJobLine:
    return DyeingJobLine(
        finished_bc_rate=_rate(dto.finished_bc_rate),
        item_code=dto.item_code.strip(),
        style=dto.style.strip(),
        oc_no=dto.oc_no.strip(),
        odno=dto.odno.strip(),
        g_per_m=dto.g_per_m,
        g_per_m2=dto.g_per_m2,
        shrinkage=_rate(dto.shrinkage),
        quantity_m=dto.quantity_m,
        job_price_vnd=dto.job_price_vnd,
        tcdn_dyeing=tcdn_input(dto.tcdn_dyeing),
        hcm_dyeing=hcm_input(dto.hcm_dyeing),
        quoted_items=CostItems(**{k: v or ZERO for k, v in dto.quoted_items.model_dump().items()}),
    )


def _kept(line: DyeingJobLine) -> bool:
    """A line is kept as soon as one cell or one dyeing choice is typed (fix 2026-11-25)."""
    blank = DyeingJobLine()
    return (
        line.has_data
        or line.tcdn_dyeing != blank.tcdn_dyeing
        or line.hcm_dyeing != blank.hcm_dyeing
        or line.quoted_items.total > 0
    )


def line_dto(line: DyeingJobLine) -> DyeingJobLineDTO:
    tcdn = line.tcdn_dyeing.model_dump()
    tcdn["extra_cost"] = _extra(line.tcdn_dyeing.extra_cost)
    hcm = line.hcm_dyeing.model_dump()
    hcm["extra_cost"] = _extra(line.hcm_dyeing.extra_cost)
    return DyeingJobLineDTO(
        **line.model_dump(exclude={"tcdn_dyeing", "hcm_dyeing", "quoted_items"}),
        tcdn_dyeing=tcdn,
        hcm_dyeing=hcm,
        quoted_items=CostItemsDTO(**line.quoted_items.as_dict()),
    )


def input_dto(job: DyeingJob) -> DyeingJobInputDTO:
    return DyeingJobInputDTO(
        contract_no=job.contract_no,
        customer_name=job.customer_name,
        dye_plant=job.dye_plant,
        costing_date=job.costing_date,
        note=job.note,
        lines=[line_dto(line) for line in job.lines],
    )


def apply_input(job: DyeingJob, typed: DyeingJobInputDTO) -> DyeingJob:
    """UC-41 / UC-42: header + lines typed on Screen 8 (empty rows dropped, at most 30 kept for BR-97 to report)."""
    lines = [line_from_dto(line) for line in typed.lines]
    lines = [line for line in lines if _kept(line)][: MAX_JOB_LINES + 1]
    return job.model_copy(
        update={
            "contract_no": typed.contract_no.strip()[:60],
            "customer_name": typed.customer_name.strip() or job.customer_name,
            "dye_plant": typed.dye_plant,
            "costing_date": typed.costing_date or job.costing_date,
            "note": typed.note.strip()[:1000],
            "lines": lines,
        }
    )


def _cost_line(d: DyeingLine) -> DyeingLineDTO:
    return DyeingLineDTO(group=d.group, name=d.name, factor=d.factor, loss_rate=d.loss_rate, per_kg=d.per_kg,
                         per_m=d.per_m, note=d.note, **d.items.as_dict())  # fmt: skip


class DyeingJobResponseBuilder(BaseBuilder[DyeingJobResponse]):
    def __init__(
        self,
        job: DyeingJob,
        actions: list[CostsheetAction] | None = None,
        editable: bool = False,
        message: str = "",
    ) -> None:
        self.job = job
        self.actions = actions or []
        self.editable = editable
        self.message = message

    def build(self) -> DyeingJobResponse:
        j, r = self.job, self.job.result
        lines = [
            DyeingJobLineResultDTO(
                cost_lines=[_cost_line(c) for c in x.cost_lines],
                items=CostItemsDTO(**x.items.as_dict()),
                **x.model_dump(exclude={"cost_lines", "items", "warnings"}),
            )
            for x in r.lines
        ]
        return DyeingJobResponse(
            id=j.id,
            job_no=j.job_no,
            status=j.status,
            editable=self.editable,
            allowed_actions=self.actions,
            input=input_dto(j),
            exchange_rate=j.exchange_rate,
            norm_set_code=j.norm_set_code,
            parameter_set_date=j.parameter_set_date,
            sales_name=j.sales_name,
            team=j.team,
            approved_by_name=j.approved_by_name,
            approved_at=j.approved_at,
            return_reason=j.return_reason,
            cancel_reason=j.cancel_reason,
            copied_from=j.copied_from,
            calculated=r.calculated,
            lines=lines,
            total_quantity=r.total_quantity,
            total_cost=r.total_cost,
            total_revenue=r.total_revenue,
            gp=r.gp,
            gp_pct=r.gp_pct,
            gp_threshold=r.gp_threshold,
            gp_below=r.gp_below,
            warnings=[WarningDTO(code=w.code, message=w.message, blocking=w.blocking) for w in r.warnings],
            message=self.message,
        )


class DyeingJobRowsBuilder(BaseBuilder[list[DyeingJobRowDTO]]):
    """UC-44 list rows."""

    def __init__(self, jobs: list[DyeingJob]) -> None:
        self.jobs = jobs

    def build(self) -> list[DyeingJobRowDTO]:
        return [
            DyeingJobRowDTO(
                id=j.id,
                job_no=j.job_no,
                status=j.status,
                costing_date=j.costing_date,
                customer_name=j.customer_name,
                contract_no=j.contract_no,
                dye_plant=j.dye_plant,
                line_count=len(j.lines),
                total_quantity=j.result.total_quantity,
                total_revenue=j.result.total_revenue,
                gp=j.result.gp,
                gp_pct=j.result.gp_pct,
                gp_below=j.result.gp_below,
                sales_name=j.sales_name,
                approved_by_name=j.approved_by_name,
            )
            for j in self.jobs
        ]


def _money(value: Decimal, digits: int = 2) -> float:
    return round(float(value), digits)


class DyeingJobExcelBuilder(BaseBuilder[FileDownloadDTO]):
    """F-09: sheet "Thông tin" (header) and sheet "Output" (TỔNG CỘNG + one row per line, like the NGC file)."""

    def __init__(self, job: DyeingJob) -> None:
        self.job = job

    def build(self) -> FileDownloadDTO:
        j, r = self.job, self.job.result
        header = [
            {"Mục": "Số phiếu", "Giá trị": j.job_no},
            {"Mục": "Số Hợp Đồng", "Giá trị": j.contract_no},
            {"Mục": "Khách hàng", "Giá trị": j.customer_name},
            {"Mục": "Đơn vị Gia công", "Giá trị": j.dye_plant.value},
            {"Mục": "Tỷ giá", "Giá trị": float(j.exchange_rate)},
            {"Mục": "Hình thức Gia công", "Giá trị": JOB_KIND},
            {"Mục": "Ngày tính giá", "Giá trị": f"{j.costing_date:%d/%m/%Y}"},
            {"Mục": "Trạng thái", "Giá trị": j.status.value},
        ]
        rows: list[dict[str, object]] = []
        for index, (line, res) in enumerate(zip(j.lines, r.lines, strict=False), start=1):
            items = res.items
            rows.append({
                "STT": index,
                "% Thành phẩm B, C": _money(line.finished_bc_rate * 100),
                "Mã vải": line.item_code,
                "Tên vải (Item) / Style": line.style,
                "Số OC": line.oc_no,
                "ODNO": line.odno,
                "Nguyên liệu nhuộm": self._material(line),
                "Cấp màu": self._color(line),
                "TỔNG CÁC QUY TRÌNH": res.process_text,
                "Số lượng": float(line.quantity_m or 0),
                "Tổng định mức (VND)": _money(res.cost_per_m),
                "Tổng định mức - TP (VND)": _money(res.cost_per_m_finished),
                "Đơn giá nhận GC (VND)": _money(line.job_price_vnd or ZERO, 3),
                "Thành tiền (chi phí)": _money(res.total_cost),
                "Thành tiền (Giá GC)": _money(res.revenue),
                "GP": _money(res.gp),
                "%GP": _money(res.gp_pct * 100),
                "Hoá Chất": _money(items.chemical),
                "Nhân công": _money(items.labor),
                "Khấu hao": _money(items.depreciation),
                "Điện": _money(items.power),
                "Nhiên liệu": _money(items.fuel),
                "Vật tư": _money(items.material),
                "CPQL": _money(items.overhead),
            })  # fmt: skip
        columns = (
            list(rows[0]) if rows else ["STT", "Số lượng", "Thành tiền (chi phí)", "Thành tiền (Giá GC)", "GP", "%GP"]
        )
        rows.insert(0, dict.fromkeys(columns) | self._total_row())
        content = ExcelWriter().write({"Thông tin": header, "Output": rows})
        return FileDownloadDTO(filename=f"gia-cong-{j.job_no}.xlsx", content=content, mime_type=MimeType.XLSX)

    def _total_row(self) -> dict[str, object | None]:
        r = self.job.result
        return {"STT": "TỔNG CỘNG", "Số lượng": float(r.total_quantity), "Thành tiền (chi phí)": _money(r.total_cost),
                "Thành tiền (Giá GC)": _money(r.total_revenue), "GP": _money(r.gp),
                "%GP": _money(r.gp_pct * 100)}  # fmt: skip

    def _material(self, line: DyeingJobLine) -> str:
        return line.tcdn_dyeing.dye_material if self.job.dye_plant.value == "TCDN" else line.hcm_dyeing.dye_material

    def _color(self, line: DyeingJobLine) -> str:
        return line.tcdn_dyeing.color_level if self.job.dye_plant.value == "TCDN" else line.hcm_dyeing.color_level
