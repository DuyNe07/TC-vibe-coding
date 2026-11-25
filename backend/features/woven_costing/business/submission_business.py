"""UC-20 checks before sending for approval: BR-42 complete data, BR-43 dyeing data, BR-44 yarn price age,
BR-14 shrinkage reason, BR-29 F&I. Also the BR-44 working-day count used by "Việc chờ tôi"."""

from collections.abc import Sequence
from datetime import date, timedelta

from backend.core.base import BaseBusiness, BaseBusinessRule
from backend.features.woven_costing.business.numbers import ONE, ZERO, num
from backend.features.woven_costing.business.pricing_business import PricingBusiness
from backend.features.woven_costing.constants import BLENDED, RATIO_TOLERANCE
from backend.features.woven_costing.models.checks import Check, YarnPriceAge
from backend.features.woven_costing.models.costsheet import Costsheet
from backend.features.woven_costing.models.enums import JOB_FORMS, NO_DYEING_FORMS, DyePlant, SaleForm

WEEKEND = (5, 6)
BLOCKING_CODES = (
    "BR-05", "BR-10", "BR-14", "BR-20", "BR-21", "BR-22", "BR-25", "BR-26", "BR-80", "BR-81", "BR-82", "BR-84",
)  # fmt: skip


class CompleteDataRule(BaseBusinessRule[Check]):
    """Target items = missing parts."""

    code = "BR-42"
    message = "Chưa đủ dữ liệu để gửi duyệt."

    def is_satisfied_by(self, target: Check) -> bool:
        return not target.items

    def describe_violation(self, target: Check) -> str:
        return f"Chưa đủ dữ liệu để gửi duyệt: {', '.join(target.items)}."


class DyeingDataRule(BaseBusinessRule[Check]):
    code = "BR-43"
    message = "Thiếu dữ liệu nhuộm."

    def is_satisfied_by(self, target: Check) -> bool:
        return not target.items

    def describe_violation(self, target: Check) -> str:
        return f"Thiếu dữ liệu nhuộm: {', '.join(target.items)}."


class YarnPriceAgeRule(BaseBusinessRule[YarnPriceAge]):
    code = "BR-44"
    message = "Giá sợi đã quá số ngày làm việc. Vui lòng nhập lại hoặc xác nhận giá sợi."

    def is_satisfied_by(self, target: YarnPriceAge) -> bool:
        return target.entered_on is not None and target.working_days < target.valid_days

    def describe_violation(self, target: YarnPriceAge) -> str:
        day = target.entered_on.strftime("%d/%m/%Y") if target.entered_on else "(chưa có ngày)"
        return (
            f"Giá sợi {target.yarn_name} nhập từ {day} đã quá {target.valid_days} ngày làm việc. "
            "Vui lòng nhập lại hoặc xác nhận giá sợi."
        )


class SubmissionBusiness(BaseBusiness[Check]):
    def rules(self) -> Sequence[BaseBusinessRule[Check]]:
        return (CompleteDataRule(), DyeingDataRule())

    def working_days(self, since: date, today: date, holidays: set[date]) -> int:
        """BR-44: Monday-Friday, without holidays, from the day after ``since`` to today included."""
        days, current = 0, since + timedelta(days=1)
        while current <= today:
            if current.weekday() not in WEEKEND and current not in holidays:
                days += 1
            current += timedelta(days=1)
        return days

    def expired_prices(self, sheet: Costsheet, today: date, holidays: set[date], valid_days: int) -> list[str]:
        """BR-44 messages of the yarn prices that are too old."""
        rule = YarnPriceAgeRule()
        messages: list[str] = []
        if sheet.sale_form in JOB_FORMS:  # no yarn cost on a job order (BR-89, BR-90)
            return messages
        for line in sheet.yarn_lines:
            if line.ratio <= 0 or num(line.price_input) <= 0:
                continue
            age = self.working_days(line.price_entered_on, today, holidays) if line.price_entered_on else 0
            target = YarnPriceAge(yarn_name=line.yarn_name, entered_on=line.price_entered_on, working_days=age,
                                  valid_days=valid_days)  # fmt: skip
            if not rule.is_satisfied_by(target):
                messages.append(rule.describe_violation(target))
        return messages

    def missing_data(self, sheet: Costsheet) -> list[str]:
        """BR-42: header, prices, Hồ choice, Se lines, greige price of Vải Nhuộm."""
        missing = []
        header = {
            "khách hàng": sheet.customer_name, "thị trường": sheet.market, "loại đơn": sheet.order_type,
            "hình thức bán": sheet.sale_form, "ngày tính giá": sheet.costing_date, "mã vải": sheet.tcfno,
            "số mét": num(sheet.order_meters) > 0, "loại giá": sheet.price_type,
            "giá bán": num(sheet.price.sell_price_input) > 0,
        }  # fmt: skip
        missing += [label for label, value in header.items() if not value]
        no_price = [ln.yarn_name for ln in sheet.yarn_lines if ln.ratio > 0 and num(ln.price_input) <= 0]
        if sheet.sale_form in JOB_FORMS:  # BR-42 (2026-11-25): the job orders have no yarn cost
            no_price = []
        if no_price:
            missing.append(f"giá sợi ({', '.join(no_price)})")
        weaving = sheet.sale_form != SaleForm.DYEING_JOB  # BR-42 (2026-11-25): no Se / Hồ on Gia công nhuộm
        if (
            weaving
            and any(ln.is_sized for ln in sheet.yarn_lines)
            and not (sheet.weaving.size_material or sheet.weaving.warping_band)
        ):
            missing.append("nguyên liệu hồ hoặc Mắc phân băng (Có / Không)")
        if (
            weaving
            and any(ln.is_twisted for ln in sheet.yarn_lines)
            and not any(num(t.quantity_kg) > 0 for t in sheet.twist_lines)
        ):
            missing.append("dòng Se")
        if sheet.sale_form == SaleForm.DYED and num(sheet.greige_buy_price) <= 0:
            missing.append("giá vải mộc mua ngoài")
        return missing

    def missing_dyeing(self, sheet: Costsheet) -> list[str]:
        """BR-43 (not Mộc)."""
        if sheet.sale_form is None or sheet.sale_form in NO_DYEING_FORMS:
            return []
        dye = sheet.tcdn_dyeing if sheet.dye_plant == DyePlant.TCDN else sheet.hcm_dyeing
        extra = dye.extra_cost is not None and dye.extra_cost.items.total > 0
        standard = bool(dye.dye_material and dye.color_level)
        missing = []
        if not standard and not extra:
            missing.append("nguyên liệu nhuộm + cấp màu, hoặc chi phí phát sinh")
        blend_total = sum((num(r) for r in dye.blend_ratios), ZERO)
        if standard and dye.color_level == BLENDED and abs(blend_total - ONE) > RATIO_TOLERANCE:
            missing.append("tổng tỷ trọng cấp màu phải bằng 100%")
        if sheet.dye_plant == DyePlant.HCM:
            if (standard or extra) and sheet.hcm_dyeing.dye_loss_rate is None:
                missing.append("tiêu hao nhuộm")
        else:
            tcdn = sheet.tcdn_dyeing
            if extra and tcdn.extra_cost_loss_rate is None:
                missing.append("tiêu hao quy trình nhuộm của chi phí phát sinh")
            if extra and tcdn.extra_cost_type is None:
                missing.append("loại quy trình (Nhuộm / Partial)")
            if tcdn.special_dye and tcdn.special_dye_chemical_price is None:
                missing.append("giá hóa chất thuốc nhuộm của phẩm nhuộm đặc biệt")
        return missing

    def submit_errors(self, sheet: Costsheet, today: date, holidays: set[date], valid_days: int) -> list[str]:
        """UC-20 step 2: every blocking message (BR-42, BR-43, BR-44, BR-14, BR-29 and the calculation errors)."""
        errors: list[str] = []
        for rule, items in (
            (CompleteDataRule(), self.missing_data(sheet)),
            (DyeingDataRule(), self.missing_dyeing(sheet)),
        ):
            violation = rule.evaluate(Check(ok=not items, items=items))
            if violation is not None:
                errors.append(violation.message)
        errors += self.expired_prices(sheet, today, holidays, valid_days)
        pricing = PricingBusiness()
        errors += [v.message for v in pricing.collect_violations(
            pricing.freight_check(sheet.price_type, sheet.price.freight_insurance))]  # fmt: skip
        errors += [w.message for w in sheet.result.warnings if w.blocking and w.code in BLOCKING_CODES]
        return list(dict.fromkeys(errors))
