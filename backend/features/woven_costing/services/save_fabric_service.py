"""UC-03 Nhập nhanh / sửa mã vải."""

from decimal import Decimal

from backend.core.base import BaseService
from backend.core.exceptions import ConflictError, NotFoundError
from backend.features.woven_costing.business.access_business import AccessBusiness
from backend.features.woven_costing.business.fabric_business import FabricBusiness
from backend.features.woven_costing.business.hint_business import HintBusiness
from backend.features.woven_costing.dto.fabric_dto import SaveFabricRequest, SaveFabricResponse
from backend.features.woven_costing.exceptions import WovenCostingError
from backend.features.woven_costing.models.enums import FabricSource
from backend.features.woven_costing.models.fabric import Fabric, FabricSpecs, FabricYarn
from backend.features.woven_costing.repositories.fabric_repository import FabricRepository
from backend.features.woven_costing.repositories.norm_repository import ParameterSetRepository

SPEC_FIELDS = tuple(name for name in FabricSpecs.model_fields if "shrink" not in name and name != "warping_loss_rate")
REQUIRED = {
    "greige_width_cm": "khổ mộc",
    "greige_warp_density": "mật độ dọc mộc",
    "greige_weft_density": "mật độ ngang mộc",
    "greige_g_per_m": "g/m mộc",
}
HUNDRED = Decimal(100)


def renumber(yarns: list[FabricYarn]) -> list[FabricYarn]:
    counters: dict[str, int] = {}
    result = []
    for yarn in yarns:
        counters[yarn.direction] = counters.get(yarn.direction, 0) + 1
        result.append(yarn.model_copy(update={"seq": counters[yarn.direction]}))
    return result


class SaveFabricService(BaseService[SaveFabricRequest, SaveFabricResponse]):
    def __init__(self, repository: FabricRepository | None = None) -> None:
        self.repository = repository or FabricRepository()

    def execute(self, request: SaveFabricRequest) -> SaveFabricResponse:
        access = AccessBusiness()
        access.ensure_use_case(self.current_user, "UC-03")
        business = FabricBusiness()
        code = business.ensure_code(request.tcfno)
        if not request.fabric_name.strip():
            raise WovenCostingError("Vui lòng nhập tên vải.")
        missing = [label for field, label in REQUIRED.items() if not getattr(request, field)]
        if missing:
            raise WovenCostingError(f"Vui lòng nhập: {', '.join(missing)}.")
        yarns = renumber(
            [
                FabricYarn(
                    **{
                        **y.model_dump(),
                        "raw_rate": y.raw_rate or HUNDRED,
                        "raw_yarn_name": y.raw_yarn_name or y.yarn_name,
                        "twist_tpm": y.twist_tpm or business.twist_of(y.yarn_name),
                    }
                )
                for y in request.yarns
                if y.yarn_name.strip()
            ]
        )
        business.ensure_manual_yarns(yarns)
        HintBusiness().ensure_valid(sum((y.ratio for y in yarns), Decimal(0)))
        stored = self.repository.by_tcfno(code)
        defaults = ParameterSetRepository().list_with_seed()[0].values
        warping = request.warping_loss_rate if request.warping_loss_rate is not None else defaults.default_warping_loss
        specs = FabricSpecs(**{f: getattr(request, f) for f in SPEC_FIELDS}, warping_loss_rate=warping)
        user = access.display_name(self.current_user)
        if request.is_new:
            if stored is not None:
                raise ConflictError(f"Mã vải {code} đã có. Hãy dùng chức năng Sửa.")
            fabric = Fabric(
                tcfno=code,
                tcfno_raw=request.tcfno.strip()[:40],
                fabric_name=request.fabric_name.strip(),
                specs=specs,
                source=FabricSource.MANUAL,
                remark=request.remark,
                updated_by=user,
                yarns=yarns,
            )
            self.repository.add(fabric)
        else:
            if stored is None:
                raise NotFoundError(f"Mã vải {code} chưa có trong dữ liệu gốc.")
            kept = {k: getattr(stored.specs, k) for k in FabricSpecs.model_fields if "shrink" in k}
            fabric = stored.model_copy(
                update={
                    "fabric_name": request.fabric_name.strip(),
                    "specs": specs.model_copy(update=kept),
                    "remark": request.remark,
                    "updated_by": user,
                    "yarns": yarns,
                }
            )
            self.repository.update(fabric)
        self.logger.info("UC-03 saved fabric %s (new=%s, %s yarns)", code, request.is_new, len(yarns))
        return SaveFabricResponse(tcfno=code, message=f"Đã lưu mã vải {code}.")
