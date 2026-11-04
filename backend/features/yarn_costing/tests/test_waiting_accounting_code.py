"""BR-70: a waiting accounting code (from the old Excel file) never locks the yarn or its loss group."""

from backend.features.yarn_costing.dto.loss_dto import ListLossGroupsRequest
from backend.features.yarn_costing.dto.pricing_dto import GetYarnDetailRequest, SaveYarnNsmRequest
from backend.features.yarn_costing.models.enums import FactoryCode, LineType, YarnStatus
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository
from backend.features.yarn_costing.services.get_yarn_detail_service import GetYarnDetailService
from backend.features.yarn_costing.services.list_loss_groups_service import ListLossGroupsService
from backend.features.yarn_costing.services.save_yarn_nsm_service import SaveYarnNsmService
from backend.features.yarn_costing.tests.helpers import (
    S4_COMPONENTS,
    S4_NAME,
    S4_NSM,
    acting_as,
    create_request,
    setup_factory,
    user_with,
)

S4 = FactoryCode.S4
WAITING = "S4260400001F900405"
CORE_KEY = "CORE (COTTON/ FDY 30D/24F/1) (70/30) MVS"


def waiting_yarn(with_loss_group: bool = True) -> str:
    """A yarn without price lines that holds a waiting accounting code (as imported from sheet 4)."""
    setup_factory(S4, with_loss_group=with_loss_group)
    code = create_request(S4_NAME)
    yarns = YarnRepository().list_all()
    yarn = next(y for y in yarns if y.yarn_code == code)
    waiting = yarn.model_copy(update={"pending_accounting_code": WAITING, "status": YarnStatus.CHUA_TINH_DUOC})
    YarnRepository().store(yarns, [waiting])
    return code


def detail(code: str):
    return GetYarnDetailService().handle(GetYarnDetailRequest(yarn_code=code)).yarn


def save(code: str):
    return SaveYarnNsmService().handle(
        SaveYarnNsmRequest(yarn_code=code, components=S4_COMPONENTS, nsm=S4_NSM, save=True)
    )


def test_waiting_code_does_not_lock_and_is_attached_when_priced() -> None:  # AC-86
    code = waiting_yarn()
    before = detail(code)
    assert not before.is_locked and before.pending_accounting_code == WAITING
    with acting_as(user_with("XS4", username="an")):
        save(code)
    yarn = next(y for y in YarnRepository().list_all() if y.yarn_code == code)
    regular = next(line for line in yarn.lines if line.line_type == LineType.THUONG)
    assert regular.accounting_code == WAITING and yarn.pending_accounting_code is None
    assert yarn.status == YarnStatus.CO_MA_KE_TOAN and yarn.is_locked
    assert detail(code).pending_accounting_code is None


def test_waiting_code_kept_when_still_not_priced() -> None:  # AC-87
    code = waiting_yarn(with_loss_group=False)
    save(code)
    yarn = detail(code)
    assert yarn.status == YarnStatus.CHUA_TINH_DUOC and yarn.pending_accounting_code == WAITING
    assert not yarn.is_locked
    save(code)  # still editable on the next try (BR-32 does not apply)


def test_waiting_code_does_not_lock_the_loss_group() -> None:  # AC-88
    waiting_yarn()
    group = next(
        g
        for g in ListLossGroupsService().handle(ListLossGroupsRequest(factory_code=S4)).items
        if g.group_key == CORE_KEY
    )
    assert group.used_count == 1 and not group.is_locked
