"""Mở rộng 2026-11-19: đổi tên sợi sang nhóm tiêu hao đã có (BR-105 sửa, UC-68, UC-69) - AC-166..AC-169."""

from io import BytesIO

import pytest
from openpyxl import Workbook

from backend.core.base import UploadedFileDTO
from backend.core.exceptions import AppError
from backend.features.yarn_costing.dto.loss_dto import CreatePrimaryLossGroupRequest
from backend.features.yarn_costing.dto.name_dto import ImportRenameFileRequest, RenameYarnRequest
from backend.features.yarn_costing.dto.pricing_dto import SaveYarnNsmRequest
from backend.features.yarn_costing.models.enums import FactoryCode, Technology, YarnStatus
from backend.features.yarn_costing.models.yarn import Yarn
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository
from backend.features.yarn_costing.services.create_primary_loss_group_service import CreatePrimaryLossGroupService
from backend.features.yarn_costing.services.import_rename_file_service import ImportRenameFileService
from backend.features.yarn_costing.services.rename_yarn_service import RenameYarnService
from backend.features.yarn_costing.services.save_yarn_nsm_service import SaveYarnNsmService
from backend.features.yarn_costing.tests.helpers import (
    S4_COMPONENTS,
    S4_LOSSES,
    S4_NAME,
    S4_NSM,
    create_request,
    setup_factory,
)

S4 = FactoryCode.S4
GROUP = "CORE (COTTON/ FDY 30D/24F/1) (70/30) MVS"  # made by setup_factory (complete losses)
WRONG = "CORE 40/1 (COTON/ FDY 30D/24F/1) (70/30) MVS"  # misspelt: its loss group does not exist


def yarn(code: str) -> Yarn:
    return next(y for y in YarnRepository().list_all() if y.yarn_code == code)


def group_keys() -> set[str]:
    return {g.group_key for g in LossGroupRepository().list_all() if g.factory_code == S4}


def add_group(label: str, without_v: bool = False) -> None:
    losses = {k: v for k, v in S4_LOSSES.items() if not (without_v and k == "V")}
    CreatePrimaryLossGroupService().handle(
        CreatePrimaryLossGroupRequest(factory_code=S4, yarn_group_label=label, technology=Technology.MVS, losses=losses)
    )


def waiting_yarn(name: str) -> str:
    code = create_request(name)
    SaveYarnNsmService().handle(SaveYarnNsmRequest(yarn_code=code, save=True, components=S4_COMPONENTS, nsm=S4_NSM))
    assert yarn(code).status == YarnStatus.CHUA_TINH_DUOC
    return code


# ---- AC-166 ----
def test_ac166_unpriced_yarn_joins_existing_group_and_gets_priced() -> None:
    setup_factory(S4)
    code = waiting_yarn(WRONG)
    before = group_keys()
    assert GROUP in before and "CORE (COTON/ FDY 30D/24F/1) (70/30) MVS" not in before
    done = RenameYarnService().handle(RenameYarnRequest(yarn_code=code, new_name=S4_NAME, reason="sai chính tả"))
    renamed = yarn(code)
    assert renamed.yarn_name == S4_NAME and renamed.loss_group_key == GROUP
    assert renamed.status == YarnStatus.DA_TINH_GIA and renamed.regular_line is not None
    assert f"sợi dùng nhóm tiêu hao '{GROUP}' đã có; đã tính giá:" in done.message
    assert done.message.endswith(" đ/kg.")
    assert group_keys() == before  # no loss group renamed or deleted


# ---- AC-167 ----
def test_ac167_priced_yarn_still_refused() -> None:
    setup_factory(S4)
    code = create_request(S4_NAME)
    SaveYarnNsmService().handle(SaveYarnNsmRequest(yarn_code=code, save=True, components=S4_COMPONENTS, nsm=S4_NSM))
    assert yarn(code).status == YarnStatus.DA_TINH_GIA
    add_group("CORE (COTTON/ FDY 30D/24F/1) (60/40) MVS")
    total = yarn(code).regular_line.total_vnd
    with pytest.raises(AppError, match="Nhóm tiêu hao 'CORE \\(COTTON/ FDY 30D/24F/1\\) \\(60/40\\) MVS' đã có"):
        RenameYarnService().handle(
            RenameYarnRequest(yarn_code=code, new_name="CORE 40/1 (COTTON/ FDY 30D/24F/1) (60/40) MVS", reason="x")
        )
    kept = yarn(code)
    assert kept.yarn_name == S4_NAME and kept.loss_group_key == GROUP and kept.regular_line.total_vnd == total


# ---- AC-168 ----
def test_ac168_old_group_exists_new_group_incomplete_stays_waiting() -> None:
    setup_factory(S4)
    old_key = "CORE (COTTON/ FDY 30D/24F/1) (65/35) MVS"
    new_key = "CORE (COTTON/ FDY 30D/24F/1) (60/40) MVS"
    add_group(old_key, without_v=True)
    add_group(new_key, without_v=True)
    code = waiting_yarn("CORE 40/1 (COTTON/ FDY 30D/24F/1) (65/35) MVS")
    done = RenameYarnService().handle(
        RenameYarnRequest(yarn_code=code, new_name="CORE 40/1 (COTTON/ FDY 30D/24F/1) (60/40) MVS", reason="sai tỷ lệ")
    )
    renamed = yarn(code)
    assert renamed.loss_group_key == new_key and renamed.status == YarnStatus.CHUA_TINH_DUOC
    assert any("V" in r for r in renamed.status_reasons)
    assert f"sợi dùng nhóm tiêu hao '{new_key}' đã có; vẫn chưa tính được:" in done.message
    assert old_key in group_keys() and new_key in group_keys()


# ---- AC-169 ----
def test_ac169_rename_by_file_joins_existing_group() -> None:
    setup_factory(S4)
    code = waiting_yarn(WRONG)
    book = Workbook()
    ws = book.active
    ws.title = "Sua ten"
    ws.append(["Xưởng", "Mã", "Tên mới", "Lý do sửa"])
    ws.append(["S4", code, S4_NAME, "sai chính tả"])
    stream = BytesIO()
    book.save(stream)
    file = UploadedFileDTO(filename="sua-ten.xlsx", content=stream.getvalue())
    preview = ImportRenameFileService().handle(ImportRenameFileRequest(file=file))
    assert [r.new_loss_group for r in preview.valid] == [GROUP] and yarn(code).status == YarnStatus.CHUA_TINH_DUOC
    done = ImportRenameFileService().handle(ImportRenameFileRequest(file=file, commit=True))
    assert done.message == "Đã đổi tên 1 sợi, bị loại 0 dòng. Đã tính giá 1 mã dùng nhóm tiêu hao đã có."
    assert yarn(code).status == YarnStatus.DA_TINH_GIA and yarn(code).loss_group_key == GROUP
    # the other BR-105 cases (K' = K, K' new → group renamed) stay covered by test_yarn_name.py (AC-136..AC-138)
