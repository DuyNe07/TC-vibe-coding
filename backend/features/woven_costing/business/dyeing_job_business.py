"""Dyeing job order ("phiếu gia công nhuộm", file NGC, 2026-11-25): BR-92..BR-98 (BR-99 reuses the costsheet rules)."""

from collections.abc import Sequence
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.core.current_user import CurrentUser
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.costsheet_business import CostsheetBusiness
from backend.features.woven_costing.business.dyeing_hcm_business import DyeingHcmBusiness
from backend.features.woven_costing.business.dyeing_tcdn_business import DyeingTcdnBusiness, contact_warning
from backend.features.woven_costing.business.numbers import ONE, ZERO, div, num, same_text
from backend.features.woven_costing.constants import (
    TCDN_AUX_WORKSHOP,
    TCDN_CPB,
    TCDN_MERCERIZING,
    TCDN_PRICED_STAGES,
    TCDN_SUSE,
)
from backend.features.woven_costing.models.access import CREATORS
from backend.features.woven_costing.models.checks import Check
from backend.features.woven_costing.models.cost_items import CostItems
from backend.features.woven_costing.models.costing_context import CostingContext
from backend.features.woven_costing.models.costing_data import CostingData
from backend.features.woven_costing.models.costsheet import Costsheet, FabricSnapshot
from backend.features.woven_costing.models.costsheet_input import TcdnStageInput
from backend.features.woven_costing.models.costsheet_result import CostWarning, DyeingLine
from backend.features.woven_costing.models.dyeing_job import (
    MAX_JOB_LINES,
    DyeingJob,
    DyeingJobLine,
    DyeingJobLineResult,
    DyeingJobResult,
)
from backend.features.woven_costing.models.enums import CostsheetAction, CostsheetStatus, DyePlant, OrderType, SaleForm
from backend.features.woven_costing.models.fabric import FabricSpecs
from backend.features.woven_costing.models.norm_set import NormTables
from backend.features.woven_costing.models.parameter_set import ParameterValues
from backend.features.woven_costing.models.parameter_tables import ParameterTables

JOB_PREFIX = "GC"
JOB_SEQ_DIGITS = 5
THOUSAND = Decimal(1000)
MAX_REPEAT = 9
ITEM_CODE_MAX = 40


class JobLinesRule(BaseBusinessRule[Check]):
    """Target text = every invalid cell, one per line."""

    code = "BR-97"
    message = "Dòng gia công không hợp lệ."
    field = "lines"

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return target.text


class JobSubmitRule(BaseBusinessRule[Check]):
    code = "BR-98"
    message = "Chưa đủ dữ liệu để gửi duyệt."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Chưa đủ dữ liệu để gửi duyệt: {target.text}."


class JobEditableRule(BaseBusinessRule[Check]):
    code = "BR-99"
    message = "Phiếu gia công không sửa được."

    def is_satisfied_by(self, target: Check) -> bool:
        return target.ok

    def describe_violation(self, target: Check) -> str:
        return f"Phiếu gia công đang ở trạng thái {target.text}, không sửa được."


class DyeingJobTcdnBusiness(DyeingTcdnBusiness):
    """BR-92 / BR-93: the TCDN rules of the NGC file (operation rate, typed chemical as is, repeat count)."""

    def __init__(self, context: CostingContext, op_rates: dict[str, Decimal]) -> None:
        super().__init__(context)
        self.op_rates = {name.strip().casefold(): rate for name, rate in op_rates.items()}

    def op_rate(self, name: str) -> Decimal:
        rate = self.op_rates.get(name.strip().casefold(), ONE)
        return rate if rate > 0 else ONE

    def standard_chemical(self, table_chemical: Decimal, shrink: Decimal) -> Decimal:
        """NGC: a special dye price is used as typed; the table chemical / (1 - co) / 250 x g/m."""
        if self.input.special_dye:
            return num(self.input.special_dye_chemical_price)
        return self.per_weight(div(table_chemical, ONE - shrink))

    def stage_cost(
        self, stage: TcdnStageInput, shrink: Decimal, warnings: list[CostWarning]
    ) -> tuple[CostItems, Decimal] | None:
        """BR-92 (b): chemical by stage (typed price as is), 6 items x (1 + n) / (1 - co) / (1 - loss) / op rate."""
        name, material = stage.name, self.input.dye_material
        row = self.lookup.tcdn_process(name, material)
        if row is None:
            return super().stage_cost(stage, shrink, warnings)  # same "missing norm" warning
        loss = row.loss_rate
        repeat = Decimal(stage.repeat_count)
        times = repeat if repeat > 0 else ONE  # the file multiplies a table chemical by n (not 1 + n)
        cpb = same_text(name, TCDN_CPB)
        lowered = name.strip().casefold()
        if cpb:
            chem_row = self.lookup.tcdn_chemical(f"{TCDN_CPB} {material}")
            chemical = self.per_weight(chem_row.cost) * times if chem_row else ZERO
        elif any(lowered.startswith(s.casefold()) for s in TCDN_PRICED_STAGES):
            chemical = num(stage.chemical_price)
            if stage.chemical_price is None:
                warnings.append(contact_warning(name))
        elif lowered.startswith(TCDN_SUSE.casefold()) or same_text(name, TCDN_MERCERIZING):
            key = TCDN_SUSE if lowered.startswith(TCDN_SUSE.casefold()) else TCDN_MERCERIZING
            chem_row = self.lookup.tcdn_chemical(key)
            chemical = div(self.per_weight(chem_row.cost), ONE - loss) * times if chem_row else ZERO
        else:
            chemical = ZERO
        div_co = ONE if row.workshop == TCDN_AUX_WORKSHOP else ONE - shrink
        div_loss = ONE if cpb else ONE - loss
        scale = div(div(div(ONE + repeat, div_co), div_loss), self.op_rate(name))
        items = row.items.model_copy(update={"chemical": ZERO}).scaled(scale)
        return items.model_copy(update={"chemical": chemical}), loss


class DyeingJobBusiness(BaseBusiness[Check]):
    def rules(self) -> Sequence[BaseBusinessRule[Check]]:
        return (JobLinesRule(),)

    # ---- BR-96 ----------------------------------------------------------------------------------------------------
    def job_number(self, customer_code: str, year: int, existing: list[str]) -> str:
        """GC-<customer code>-YYYY-NNNNN, NNNNN increasing in the year for every customer."""
        sequences = []
        for number in existing:
            parts = number.split("-")
            if len(parts) >= 4 and parts[-2] == str(year) and parts[-1].isdigit():
                sequences.append(int(parts[-1]))
        return f"{JOB_PREFIX}-{customer_code}-{year}-{max(sequences, default=0) + 1:0{JOB_SEQ_DIGITS}d}"

    # ---- BR-97 / BR-98 / BR-99 ------------------------------------------------------------------------------------
    def ensure_editable(self, job: DyeingJob) -> None:
        JobEditableRule().check(Check(ok=job.is_editable_status, text=job.status.value))

    def line_errors(self, lines: list[DyeingJobLine]) -> list[str]:
        """BR-97: cells of the lines that have data."""
        errors: list[str] = []
        if len(lines) > MAX_JOB_LINES:
            errors.append(f"Phiếu gia công tối đa {MAX_JOB_LINES} dòng.")
        for index, line in enumerate(lines, start=1):
            bad = []
            if len(line.item_code.strip()) > ITEM_CODE_MAX:
                bad.append("Mã hàng (tối đa 40 ký tự)")
            for label, value in (("g/m", line.g_per_m), ("g/m2", line.g_per_m2), ("Số lượng", line.quantity_m),
                                 ("Đơn giá nhận GC", line.job_price_vnd)):  # fmt: skip
                if value is not None and value < 0:
                    bad.append(label)
            if not ZERO <= line.shrinkage < ONE:
                bad.append("Độ co")
            if not ZERO <= line.finished_bc_rate < ONE:
                bad.append("% B/C")
            if any(not 0 <= s.repeat_count <= MAX_REPEAT for s in line.tcdn_dyeing.extra_stages):
                bad.append("Số lần xử lý thêm")
            errors += [f"Dòng {index}: {label} không hợp lệ." for label in bad]
        return errors

    def check_lines(self, lines: list[DyeingJobLine]) -> None:
        errors = self.line_errors(lines)
        JobLinesRule().check(Check(ok=not errors, text="\n".join(errors)))

    def missing_data(self, job: DyeingJob) -> list[str]:
        """BR-98."""
        missing = []
        if not job.customer_name:
            missing.append("khách hàng")
        lines = [ln for ln in job.lines if ln.has_data]
        if not lines:
            missing.append("ít nhất 1 dòng mã hàng")
        for index, line in enumerate(job.lines, start=1):
            if not line.has_data:
                continue
            need = {"mã hàng": line.item_code.strip(), "g/m": num(line.g_per_m) > 0, "g/m2": num(line.g_per_m2) > 0,
                    "số lượng": num(line.quantity_m) > 0, "đơn giá nhận GC": num(line.job_price_vnd) > 0}  # fmt: skip
            gaps = [label for label, ok in need.items() if not ok]
            if not self.has_dyeing(job.dye_plant, line):
                gaps.append("nguyên liệu + cấp màu, công đoạn hoặc báo giá riêng")
            if gaps:
                missing.append(f"dòng {index} ({', '.join(gaps)})")
        return missing

    def ensure_submittable(self, job: DyeingJob) -> None:
        missing = self.missing_data(job)
        JobSubmitRule().check(Check(ok=not missing, text="; ".join(missing)))

    def has_dyeing(self, plant: DyePlant, line: DyeingJobLine) -> bool:
        if line.quoted_items.total > 0:
            return True
        if plant == DyePlant.TCDN:
            dye = line.tcdn_dyeing
            return bool((dye.dye_material and dye.color_level) or any(s.name for s in dye.extra_stages)
                        or any(f.name for f in dye.special_features) or dye.wr_chemical)  # fmt: skip
        hcm = line.hcm_dyeing
        return bool((hcm.dye_material and hcm.color_level) or any(s for s in hcm.special_stages)
                    or any(f for f in hcm.special_features))  # fmt: skip

    # ---- BR-92..BR-95 ---------------------------------------------------------------------------------------------
    def context(self, job: DyeingJob, line: DyeingJobLine, tables: NormTables, params: ParameterValues,
                param_tables: ParameterTables) -> CostingContext:  # fmt: skip
        """A costsheet-shaped view of one line so the BR-25 / BR-26 rules can be reused."""
        g, gsm = line.g_per_m, line.g_per_m2
        specs = FabricSpecs(greige_g_per_m=g, finished_g_per_m=g, greige_gsm=gsm, finished_gsm=gsm)
        sheet = Costsheet(
            costsheet_no=job.job_no,
            costing_date=job.costing_date,
            tcfno=line.item_code,
            fabric_snapshot=FabricSnapshot(tcfno=line.item_code, specs=specs),
            dye_plant=job.dye_plant,
            sale_form=SaleForm.DYEING_JOB,
            order_type=OrderType.OUTSOURCE,
            order_meters=line.quantity_m,
            tcdn_dyeing=line.tcdn_dyeing,
            hcm_dyeing=line.hcm_dyeing,
        )
        return CostingContext(costsheet=sheet, tables=tables, params=params, param_tables=param_tables)

    def process_text(self, plant: DyePlant, line: DyeingJobLine) -> str:
        """Output "TỔNG CÁC QUY TRÌNH": the stages and features of the line."""
        if plant == DyePlant.HCM:
            names = [s for s in line.hcm_dyeing.special_stages if s]
            return " - ".join(names)
        parts = [f"{s.name} {1 + s.repeat_count}" for s in line.tcdn_dyeing.extra_stages if s.name]
        return " - ".join(parts)

    def line_result(self, job: DyeingJob, line: DyeingJobLine, tables: NormTables, params: ParameterValues,
                    param_tables: ParameterTables) -> DyeingJobLineResult:  # fmt: skip
        """BR-92 / BR-94 / BR-95 for one line."""
        qty, price = num(line.quantity_m), num(line.job_price_vnd)
        warnings: list[CostWarning] = []
        lines: list[DyeingLine] = []
        factor = ONE
        if line.quoted_items.total > 0:  # BR-94 "Báo giá riêng"
            items, per_m, quoted = line.quoted_items, line.quoted_items.total, True
            lines = [DyeingLine(group="Báo giá riêng", name="Báo giá riêng", items=items, per_m=per_m)]
        elif num(line.g_per_m) <= 0:
            items, per_m, quoted = CostItems(), ZERO, False
        else:
            quoted = False
            context = self.context(job, line, tables, params, param_tables)
            m_per_kg = div(THOUSAND, num(line.g_per_m))
            if job.dye_plant == DyePlant.TCDN:
                rates = {r.stage: r.rate for r in param_tables.op_rates}
                outcome = DyeingJobTcdnBusiness(context, rates).calculate(line.shrinkage, m_per_kg)
            else:
                outcome = DyeingHcmBusiness(context).calculate(div(qty, m_per_kg), m_per_kg)
            items, per_m, factor = outcome.items_per_m, outcome.per_m, outcome.factor
            lines, warnings = outcome.lines, list(outcome.warnings)
        per_m_finished = div(per_m, ONE - line.finished_bc_rate)
        cost, revenue = qty * per_m_finished, qty * price
        gp = revenue - cost
        gp_pct = div(gp, revenue)
        below = revenue > 0 and gp_pct < params.gp_threshold
        if below:
            message = (
                f"%GP dòng {line.item_code} ({gp_pct * 100:.2f}%) thấp hơn ngưỡng {params.gp_threshold * 100:.2f}%."
            )
            warnings.append(CostWarning(code="BR-95", message=message))
        return DyeingJobLineResult(cost_lines=lines, items=items, factor=factor, quoted=quoted, cost_per_m=per_m,
                                   cost_per_m_finished=per_m_finished, total_cost=cost, revenue=revenue, gp=gp,
                                   gp_pct=gp_pct, gp_below=below, process_text=self.process_text(job.dye_plant, line),
                                   warnings=warnings)  # fmt: skip

    def calculate(self, job: DyeingJob, tables: NormTables, params: ParameterValues,
                  param_tables: ParameterTables) -> DyeingJobResult:  # fmt: skip
        """BR-95: every line then the totals of the job order."""
        results = [self.line_result(job, line, tables, params, param_tables) for line in job.lines]
        cost = sum((r.total_cost for r in results), ZERO)
        revenue = sum((r.revenue for r in results), ZERO)
        qty = sum((num(line.quantity_m) for line in job.lines), ZERO)
        gp = revenue - cost
        gp_pct = div(gp, revenue)
        below = revenue > 0 and gp_pct < params.gp_threshold
        warnings = [w for r in results for w in r.warnings]
        if below:
            message = f"%GP phiếu ({gp_pct * 100:.2f}%) thấp hơn ngưỡng {params.gp_threshold * 100:.2f}%."
            warnings.append(CostWarning(code="BR-95", message=message))
        return DyeingJobResult(calculated=True, lines=results, total_quantity=qty, total_cost=cost,
                               total_revenue=revenue, gp=gp, gp_pct=gp_pct, gp_threshold=params.gp_threshold,
                               gp_below=below, warnings=warnings)  # fmt: skip

    def copy_lines(self, job: DyeingJob) -> list[DyeingJobLine]:
        return [line.model_copy(deep=True) for line in job.lines]

    def recalculate(self, job: DyeingJob, data: CostingData) -> DyeingJob:
        """UC-41: rate, norm set and parameter set of the costing date (BR-61, BR-62), then BR-92..BR-95."""
        sheets = CostsheetBusiness()
        day = job.costing_date
        rate = sheets.rate_on(data, day)
        norms = sheets.norm_set_on(data, day)
        params = sheets.parameter_set_on(data, day)
        job = job.model_copy(update={"exchange_rate": rate, "norm_set_code": norms.norm_set_code,
                                     "parameter_set_date": params.effective_from})  # fmt: skip
        result = self.calculate(job, norms.tables, params.values, params.effective_tables())
        return job.model_copy(update={"result": result})

    # ---- BR-99 ----------------------------------------------------------------------------------------------------
    def is_editable(self, job: DyeingJob, user: CurrentUser | None) -> bool:
        return job.is_editable_status and AccessBusiness().can_edit(user, job)

    def allowed_actions(self, job: DyeingJob, user: CurrentUser | None) -> list[CostsheetAction]:
        """Buttons of Screen 8 by status and rights (same rights as a costsheet)."""
        access, a, s = AccessBusiness(), CostsheetAction, CostsheetStatus
        actions: list[CostsheetAction] = []
        edit = access.can_edit(user, job)
        if job.is_editable_status and edit:
            actions += [a.RECALCULATE, a.SAVE_DRAFT, a.SUBMIT]
        if job.status == s.CHO_DUYET and access.can_approve(user, job):
            actions += [a.APPROVE, a.RETURN]
        if edit and job.status in (s.NHAP, s.TRA_LAI, s.CHO_DUYET, s.DA_DUYET):
            actions.append(a.CANCEL)
        if access.has_any(user, CREATORS):
            actions.append(a.COPY)
        return actions
