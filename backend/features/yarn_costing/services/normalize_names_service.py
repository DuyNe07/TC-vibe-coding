"""UC-71 Chuẩn hoá viết hoa và xử lý tên trùng, một lượt (bổ sung 2026-11-11; BR-72, BR-107, BR-108)."""

from backend.core.base import BaseService, utc_now
from backend.features.yarn_costing.builders.name_file_builders import DuplicatePlanFileBuilder
from backend.features.yarn_costing.business.access_business import AccessBusiness
from backend.features.yarn_costing.business.name_business import YarnNameBusiness
from backend.features.yarn_costing.business.name_check_business import NameCheckBusiness
from backend.features.yarn_costing.business.not_produced_business import NotProducedBusiness
from backend.features.yarn_costing.dto.name_dto import (
    DuplicateDecisionDTO,
    NameChangeDTO,
    NormalizeNamesRequest,
    NormalizeNamesResponse,
)
from backend.features.yarn_costing.models.enums import YarnStatus
from backend.features.yarn_costing.repositories.customer_name_repository import CustomerYarnNameRepository
from backend.features.yarn_costing.repositories.price_history_repository import PriceHistoryRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import AuditLogRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository

USE_CASE = "UC-71"
MSG_NOTHING = "Mọi tên đã viết hoa, không có tên trùng."


class NormalizeNamesService(BaseService[NormalizeNamesRequest, NormalizeNamesResponse]):
    def execute(self, request: NormalizeNamesRequest) -> NormalizeNamesResponse:
        access = AccessBusiness()
        access.ensure_allowed(self.current_user, USE_CASE)
        business = NameCheckBusiness()
        repo, alias_repo = YarnRepository(), CustomerYarnNameRepository()
        yarns = repo.list_all()
        aliases = alias_repo.list_all()
        alias_counts: dict[str, int] = {}
        for a in aliases:
            alias_counts[a.base_code] = alias_counts.get(a.base_code, 0) + 1
        decisions = business.duplicate_plan(yarns, alias_counts)
        drops = [d for d in decisions if not d.keep]
        dropped = {d.yarn_code for d in drops}
        changes = business.upper_changes(yarns, dropped)
        decision_dtos = [DuplicateDecisionDTO(**d.model_dump()) for d in decisions]
        response = NormalizeNamesResponse(
            message=MSG_NOTHING if not changes and not drops else "",
            rename_count=sum(1 for y in changes if y.is_base),
            group_count=len({(d.factory_code, d.upper_name) for d in decisions}),
            keep_count=sum(1 for d in decisions if d.keep),
            drop_count=len(drops),
            drop_with_code_count=sum(1 for d in drops if d.accounting_codes),
            changes=[
                NameChangeDTO(
                    factory_code=y.factory_code,
                    yarn_code=y.yarn_code,
                    old_name=y.yarn_name,
                    new_name=y.yarn_name.upper(),
                )
                for y in changes
                if y.is_base
            ],
            decisions=decision_dtos,
        )
        if not request.commit:
            plan = (
                DuplicatePlanFileBuilder(decision_dtos, f"de-xuat-ten-trung-{utc_now():%Y%m%d}.xlsx").build()
                if decisions
                else None
            )
            return response.model_copy(update={"plan_file": plan})
        if not changes and not drops:
            return response
        label = access.user_label(self.current_user)
        now = utc_now()
        audit = AuditLogRepository()
        by_id = {y.id: y for y in yarns}
        updated = {}
        history = []
        produced = NotProducedBusiness()
        names = YarnNameBusiness()
        bases = {(y.factory_code, y.yarn_code): y for y in yarns if y.is_base}
        for d in drops:
            base = bases[(d.factory_code, d.yarn_code)]
            family = produced.family(yarns, base)
            if base.status == YarnStatus.CHO_XUONG_XEM:
                changed = [
                    y.model_copy(
                        update={
                            "status": YarnStatus.TU_CHOI,
                            "reject_reason": d.reason,
                            "handled_by": label,
                            "handled_at": now,
                        }
                    )
                    for y in family
                ]
            else:  # BR-107: Không sản xuất even with an accounting code (its codes move to the kept yarn)
                changed, entries, _ = produced.mark(family, d.reason, label, now)
                history += entries
            for y in changed:
                updated[y.id] = y
            keep = bases[(d.factory_code, d.keep_code)]
            keep = updated.get(keep.id, keep)
            merged = list(dict.fromkeys([*keep.merged_accounting_codes, *d.accounting_codes]))
            updated[keep.id] = keep.model_copy(update={"merged_accounting_codes": merged})
            audit.add(
                access.audit_entry(
                    self.current_user,
                    USE_CASE,
                    d.yarn_code,
                    f"Loại do trùng tên với {d.keep_code}"
                    + (f"; mã kế toán {', '.join(d.accounting_codes)} → {d.keep_code}" if d.accounting_codes else ""),
                    d.reason,
                )
            )
            # tên theo khách: move to the kept yarn (a pair the kept yarn already has is flagged deleted)
            kept_pairs = {
                (names.comparable_name(a.customer_name), names.comparable_name(a.customer_yarn_name))
                for a in aliases
                if a.base_code == d.keep_code
            }
            for alias in [a for a in aliases if a.base_code == d.yarn_code]:
                pair = (names.comparable_name(alias.customer_name), names.comparable_name(alias.customer_yarn_name))
                if pair in kept_pairs:
                    alias_repo.delete(alias.id)
                else:
                    alias_repo.save(alias.model_copy(update={"base_code": d.keep_code}))
        for y in changes:
            current = updated.get(y.id, by_id[y.id])
            updated[y.id] = business.uppered(current, label, now)
        repo.store(yarns, list(updated.values()))
        PriceHistoryRepository().add_many(history)
        renamed = sum(1 for y in changes if y.is_base)
        audit.add(
            access.audit_entry(
                self.current_user, USE_CASE, "Tên sợi", f"Viết hoa {renamed} tên; loại {len(drops)} mã trùng tên"
            )
        )
        moved = sum(len(d.accounting_codes) for d in drops)
        self.logger.info("Names normalized: %s upper-cased, %s duplicates removed", renamed, len(drops))
        return response.model_copy(
            update={
                "committed": True,
                "message": f"Đã chuẩn hoá {renamed} tên; loại {len(drops)} mã trùng tên ({moved} mã kế toán chuyển sang mã giữ).",
            }
        )
