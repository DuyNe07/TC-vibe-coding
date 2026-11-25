"""UC-16 recalculation of a costsheet (BR-39, BR-45..BR-47, BR-61, BR-62, BR-44 warnings) and the buttons
allowed by status, role and owner (Screen 2)."""

from collections.abc import Sequence
from datetime import date
from decimal import Decimal

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.core.current_user import CurrentUser
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.costing_business import CostingBusiness
from backend.features.woven_costing.business.fabric_business import FabricBusiness, FabricExistsRule
from backend.features.woven_costing.business.hint_business import WEFT_TWIST, HintBusiness
from backend.features.woven_costing.business.master_business import MasterBusiness
from backend.features.woven_costing.business.submission_business import SubmissionBusiness
from backend.features.woven_costing.business.workflow_business import WorkflowBusiness
from backend.features.woven_costing.business.yarn_cost_business import YarnCostBusiness
from backend.features.woven_costing.constants import MAX_TWIST_LINES
from backend.features.woven_costing.exceptions import WovenCostingError
from backend.features.woven_costing.models.access import CREATORS, USE_CASE_ROLES
from backend.features.woven_costing.models.checks import Check
from backend.features.woven_costing.models.costing_context import CostingContext
from backend.features.woven_costing.models.costing_data import CostingData
from backend.features.woven_costing.models.costsheet import APPROVED_STATUSES, Costsheet
from backend.features.woven_costing.models.costsheet_input import TwistLine
from backend.features.woven_costing.models.costsheet_result import CostsheetResult, CostWarning
from backend.features.woven_costing.models.enums import NO_WEAVING_FORMS, CostsheetAction, CostsheetStatus, FabricSource
from backend.features.woven_costing.models.norm_set import NormSet
from backend.features.woven_costing.models.parameter_set import APPLIED_CODES, ParameterSet

A = CostsheetAction
S = CostsheetStatus
OC_STATUSES = (S.NHAP, S.TRA_LAI, S.CHO_DUYET, S.DA_DUYET, S.DA_CHOT_DON)
NOT_CANCELLABLE = (S.DA_CHOT_DON, S.HUY, S.DA_THAY_THE)


class CostsheetBusiness(BaseBusiness[Costsheet]):
    def rules(self) -> Sequence[BaseBusinessRule[Costsheet]]:
        return ()

    def norm_set_on(self, data: CostingData, day: date) -> NormSet:
        """BR-62: norm set with effective_from <= costing date, the latest."""
        found = max(
            (s for s in data.norm_sets if s.effective_from <= day), key=lambda s: s.effective_from, default=None
        )
        MasterBusiness().ensure_in_force(found, day)
        assert found is not None  # guarded above
        return found

    def parameter_set_on(self, data: CostingData, day: date) -> ParameterSet:
        """BR-62: parameter set with effective_from <= costing date, the latest."""
        found = max(
            (s for s in data.parameter_sets if s.effective_from <= day), key=lambda s: s.effective_from, default=None
        )
        MasterBusiness().ensure_in_force(found, day)
        assert found is not None  # guarded above
        return found

    def rate_on(self, data: CostingData, day: date) -> Decimal:
        """BR-61: rate of the month / year of the costing date."""
        rate = next((r for r in data.rates if r.month == day.month and r.year == day.year), None)
        return MasterBusiness().ensure_rate_exists(rate, day)

    def refresh_fabric(self, sheet: Costsheet, data: CostingData) -> Costsheet:
        """UC-16 step 2 / BR-47: take the current fabric data, unless sales overrode a "Nhập tay" fabric; a fabric
        that now comes from Peace / WFX drops the overridden values."""
        fabric = data.fabric
        if fabric is None or fabric.tcfno != sheet.tcfno:
            return sheet
        if sheet.fabric_overridden and fabric.source == FabricSource.MANUAL:
            return sheet
        snapshot = FabricBusiness().snapshot(fabric)
        lines = HintBusiness().build_yarn_lines(snapshot, sheet.yarn_lines)
        return sheet.model_copy(update={"fabric_snapshot": snapshot, "fabric_overridden": False, "yarn_lines": lines})

    def recalculate(
        self,
        sheet: Costsheet,
        data: CostingData,
        today: date,
        wanted_overrides: dict[str, Decimal] | None = None,
    ) -> Costsheet:
        """UC-16: rate, norm set and parameter set of the costing date (BR-61, BR-62), current fabric, overrides
        (BR-46), BR-45 USD prices, BR-10..BR-29 and the BR-80 warnings (BR-44 included)."""
        day = sheet.costing_date
        rate = self.rate_on(data, day)
        norms = self.norm_set_on(data, day)
        params = self.parameter_set_on(data, day)
        sheet = self.refresh_fabric(sheet, data)
        wanted = (
            wanted_overrides
            if wanted_overrides is not None
            else {o.parameter: o.used_value for o in sheet.parameter_overrides}
        )
        values, overrides = MasterBusiness().apply_overrides(params.values, wanted)
        applied = {code: value for code, value in wanted.items() if code in APPLIED_CODES}
        previous = {o.parameter: o for o in sheet.parameter_overrides}
        prices = YarnCostBusiness()
        yarn_lines = [line.model_copy(update={"price_vnd": prices.price_vnd(line, rate)}) for line in sheet.yarn_lines]
        sheet = sheet.model_copy(
            update={
                "exchange_rate": rate,
                "norm_set_code": norms.norm_set_code,
                "parameter_set_date": params.effective_from,
                "parameter_overrides": overrides,
                "yarn_lines": yarn_lines,
                "twist_lines": HintBusiness().fill_fiber_systems(sheet.twist_lines),
            }
        )
        context = CostingContext(costsheet=sheet, tables=norms.tables, params=values, factors=data.factors,
                                 param_tables=params.tables, applied_overrides=applied)  # fmt: skip
        result = CostingBusiness().calculate(context)
        suggested = self.suggested_inputs(sheet, result)
        if suggested != sheet:
            sheet = suggested
            context = context.model_copy(update={"costsheet": sheet})
            result = CostingBusiness().calculate(context)
        kept = MasterBusiness().applied_overrides(applied, result.applied_parameters, previous)
        sheet = sheet.model_copy(update={"parameter_overrides": overrides + kept})
        holidays = {h.date for h in data.holidays}
        expired = SubmissionBusiness().expired_prices(sheet, today, holidays, int(values.yarn_price_valid_days))
        warnings = result.warnings + [CostWarning(code="BR-44", message=m) for m in expired]
        return sheet.model_copy(update={"result": result.model_copy(update={"warnings": warnings})})

    def suggested_inputs(self, sheet: Costsheet, result: CostsheetResult) -> Costsheet:
        """BR-86 Se lines then BR-87 cone 1 suggestion (not for Vải Nhuộm, only once the costsheet is calculated:
        the Se suggestion needs the estimated Se output of BR-19)."""
        if not result.calculated or sheet.sale_form in NO_WEAVING_FORMS:
            return sheet
        sheet = self.suggested_twist_lines(sheet, result)
        return sheet.model_copy(update={"weaving": HintBusiness().suggest_cone(sheet.weaving, sheet.twist_lines)})

    def suggested_twist_lines(self, sheet: Costsheet, result: CostsheetResult) -> Costsheet:
        """BR-86 (changed 2026-11-23): on a costsheet started without Se lines ("live"), the lines still suggested are
        rebuilt at each calculation from the yarn lines ticked Se and the estimated Se output; lines typed / edited by
        sales are kept; suggestions sales deleted are not made again. Costsheets whose Se lines were stored before
        (not live) keep their lines as they are."""
        live = sheet.twist_lines_live or (not sheet.twist_lines and not sheet.twist_lines_suggested)
        if not live:
            return sheet
        hints = HintBusiness()
        estimates = {(r.direction.value, r.seq): r.twist_estimate_kg for r in result.yarn_lines}
        fresh = hints.suggest_twist_lines(sheet.yarn_lines, estimates)
        lines, skips = hints.merge_twist_lines(
            sheet.twist_lines, sheet.twist_suggestions, sheet.twist_suggestion_skips, fresh
        )
        lines = self.capped_twist_lines(lines)
        offered = [line for line in lines if line.suggested]
        return sheet.model_copy(
            update={
                "twist_lines": lines,
                "twist_lines_live": True,
                "twist_lines_suggested": sheet.twist_lines_suggested or bool(offered),
                "twist_suggestions": offered,
                "twist_suggestion_skips": skips,
            }
        )

    def capped_twist_lines(self, lines: list[TwistLine]) -> list[TwistLine]:
        """4.13: at most 9 Dọc then 9 Ngang lines."""
        warp = [line for line in lines if line.direction != WEFT_TWIST][:MAX_TWIST_LINES]
        weft = [line for line in lines if line.direction == WEFT_TWIST][:MAX_TWIST_LINES]
        return warp + weft

    def check_header(self, sheet: Costsheet, customer_names: list[str], fabric_exists: bool) -> None:
        """4.11: the customer is in the customer list (4.9) and the fabric code exists (BR-02, BR-03)."""
        if sheet.customer_name and sheet.customer_name not in customer_names:
            raise WovenCostingError(f"Khách hàng {sheet.customer_name} chưa có. Hãy thêm khách hàng trước.")
        fabric = FabricBusiness()
        code = fabric.ensure_code(sheet.tcfno)
        FabricExistsRule().check(Check(ok=fabric_exists, text=code))

    def superseded(self, approved: Costsheet, versions: list[Costsheet]) -> list[Costsheet]:
        """UC-23 step 3 / BR-30: when version n+1 is approved, older approved / closed versions -> Đã thay thế."""
        return [
            v.model_copy(update={"status": S.DA_THAY_THE})
            for v in versions
            if v.version < approved.version and v.status in APPROVED_STATUSES
        ]

    def is_editable(self, sheet: Costsheet, user: CurrentUser | None) -> bool:
        """BR-31: Nháp / Trả lại and the owner, or a user with the SO role (BR-85)."""
        return sheet.is_editable_status and AccessBusiness().can_edit(user, sheet)

    def allowed_actions(
        self, sheet: Costsheet, user: CurrentUser | None, versions: list[Costsheet], source: FabricSource | None
    ) -> list[CostsheetAction]:
        """Buttons of Screen 2 by status, role and owner (BR-31, BR-36..BR-38, BR-47, BR-53, AC-20, AC-27, AC-41);
        a user with the SO role gets every button of the owner (BR-85)."""
        access = AccessBusiness()
        owner = access.can_edit(user, sheet)
        actions: list[CostsheetAction] = []
        if self.is_editable(sheet, user):
            actions += [A.RECALCULATE, A.SAVE_DRAFT, A.SUBMIT, A.CONFIRM_YARN_PRICES, A.ADD_CUSTOMER]
            if (source or sheet.fabric_snapshot.source) == FabricSource.MANUAL:
                actions.append(A.EDIT_FABRIC)
        if sheet.status == S.CHO_DUYET and access.can_approve(user, sheet):
            actions += [A.APPROVE, A.RETURN]
        if access.has_any(user, CREATORS):
            actions.append(A.COPY)
        latest = max((v.version for v in versions), default=sheet.version)
        no_open = WorkflowBusiness().open_version(versions) is None
        if owner and sheet.version == latest and sheet.status in APPROVED_STATUSES and no_open:
            actions.append(A.NEW_VERSION)
        if owner and sheet.status in OC_STATUSES:
            actions.append(A.SAVE_OC)
        if owner and sheet.status == S.DA_DUYET:
            actions.append(A.CLOSE_ORDER)
        if owner and sheet.status not in NOT_CANCELLABLE:
            actions.append(A.CANCEL)
        if access.has_any(user, USE_CASE_ROLES["UC-26"]):
            actions.append(A.PRINT_LABEL)
        return actions
