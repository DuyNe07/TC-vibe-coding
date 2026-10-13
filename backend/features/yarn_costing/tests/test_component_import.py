"""UC-44 / UC-45 Khai báo thành phần sợi pha bằng file (BR-66..BR-69, AC-78..AC-85)."""

from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import Workbook, load_workbook

from backend.core.base import UploadedFileDTO
from backend.core.exceptions import AppError
from backend.features.yarn_costing.dto.import_dto import DownloadComponentTemplateRequest, ImportComponentFileRequest
from backend.features.yarn_costing.dto.loss_dto import CreatePrimaryLossGroupRequest
from backend.features.yarn_costing.dto.pricing_dto import SaveYarnNsmRequest
from backend.features.yarn_costing.models.enums import (
    FactoryCode,
    ImportMode,
    LossGroupLevel,
    PriceEvent,
    Technology,
    YarnStatus,
)
from backend.features.yarn_costing.repositories.legacy_price_repository import ImportBatchRepository
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.recalc_batch_repository import RecalcBatchRepository
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository
from backend.features.yarn_costing.services.create_primary_loss_group_service import CreatePrimaryLossGroupService
from backend.features.yarn_costing.services.download_component_template_service import DownloadComponentTemplateService
from backend.features.yarn_costing.services.import_component_file_service import ImportComponentFileService
from backend.features.yarn_costing.services.save_yarn_nsm_service import SaveYarnNsmService
from backend.features.yarn_costing.tests.helpers import (
    S1_COMPONENTS,
    S1_NAME,
    S1_NSM,
    TODAY,
    acting_as,
    create_request,
    setup_factory,
    user_with,
)

D = Decimal
S1 = FactoryCode.S1
HEADER = ["STT", "Nhóm sợi pha", "Công nghệ", "Loại hiện tại trong app", "Số mã đang dùng"]
for _k in range(1, 6):
    HEADER += [f"Thành phần {_k}", f"Tỷ lệ {_k} (%)"]
HEADER += ["Tổng tỷ lệ (%)", "Tiêu hao hiện tại (%)"]
GROUP = "TC (60/40) MVS"  # the S1 reference group created by setup_factory (Sơ cấp, C1 = 1,68%)


def workbook(rows: list[list], sheet: str = "Khai bao thanh phan", header: list[str] | None = None) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(header or HEADER)
    for row in rows:
        ws.append(row)
    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def row(group: str, *pairs: object, tech: str = "") -> list:
    cells = [None, group, tech, None, None, *pairs]
    return cells + [None] * (len(HEADER) - len(cells))


def run(content: bytes, commit: bool = False, reason: str = "Khai báo thành phần") -> object:
    return ImportComponentFileService().handle(
        ImportComponentFileRequest(
            factory_code=S1,
            file=UploadedFileDTO(filename="thanh-phan.xlsx", content=content),
            effective_date=TODAY,
            reason=reason,
            commit=commit,
        )
    )


def primary(label: str, material: str, losses: dict) -> None:
    CreatePrimaryLossGroupService().handle(
        CreatePrimaryLossGroupRequest(
            factory_code=S1,
            yarn_group_label=label,
            material=material,
            technology=Technology.MVS,
            losses=losses,
        )
    )


def priced_s1() -> str:
    setup_factory(S1)
    primary("PE MVS", "PE", {"C1": D("0.028"), "V": D("0.02"), "MD1": D("0.002"), "MD2": D("0.002"), "MD3": D("0.002")})
    primary("CM MVS", "CM", {"V": D("0.05"), "MD1": D("0.01"), "MD2": D("0.01"), "MD3": D("0.01")})
    code = create_request(S1_NAME, S1, "Type 1")
    SaveYarnNsmService().handle(SaveYarnNsmRequest(yarn_code=code, components=S1_COMPONENTS, nsm=S1_NSM, save=True))
    return code


def group(key: str):
    return next(g for g in LossGroupRepository().for_factory("S1") if g.group_key == key)


def test_template_lists_groups() -> None:  # AC-78
    priced_s1()
    file = DownloadComponentTemplateService().handle(DownloadComponentTemplateRequest(factory_code=S1))
    book = load_workbook(BytesIO(file.content))
    assert book.sheetnames == ["Khai bao thanh phan", "Danh sach nhom", "Huong dan"]
    rows = list(book["Khai bao thanh phan"].iter_rows(values_only=True))
    assert list(rows[0]) == HEADER
    assert rows[1][1] == GROUP and rows[1][4] == 1  # most used first
    assert {r[0] for r in book["Danh sach nhom"].iter_rows(min_row=2, values_only=True)} >= {"PE MVS", "CM MVS", GROUP}


def test_declare_components_relabels_and_recalculates() -> None:  # AC-79, AC-80
    code = priced_s1()
    content = workbook([row(GROUP, "PE MVS", 60, "CM MVS", 40)])
    preview = run(content)
    assert not preview.committed and preview.valid_count == 1 and preview.affected_count == 1
    g = preview.groups[0]
    assert g.old_level == "Sơ cấp" and g.new_level == "Thứ cấp" and g.components_text == "PE MVS 60,00%; CM MVS 40,00%"
    assert g.new_losses["V"] == D("0.02") * D("0.6") + D("0.05") * D("0.4")  # S1 V: Bình quân
    assert group(GROUP).level == LossGroupLevel.SO_CAP  # nothing saved by the check
    batches = RecalcBatchRepository().count()
    result = run(content, commit=True)
    assert result.committed and result.message.startswith("Đã khai báo thành phần cho 1 nhóm (tạo mới 0 nhóm)")
    saved = group(GROUP)
    assert saved.level == LossGroupLevel.THU_CAP and [c.component_group_key for c in saved.components] == [
        "PE MVS",
        "CM MVS",
    ]
    yarn = next(y for y in YarnRepository().list_all() if y.yarn_code == code)
    assert [c.material_label for c in yarn.components] == ["PE - MVS", "Cotton"]  # BR-68: ratio / NSM unchanged
    assert yarn.components[0].ratio == D("0.6") and yarn.components[0].nsm_carding == D(18)
    assert yarn.status == YarnStatus.DA_TINH_GIA, yarn.status_reasons
    assert RecalcBatchRepository().count() == batches + 1
    assert RecalcBatchRepository().newest_first()[0].trigger == PriceEvent.SUA_TIEU_HAO
    assert ImportBatchRepository().newest_first()[0].mode == ImportMode.THANH_PHAN


def test_unmatched_component_makes_the_yarn_waiting() -> None:  # AC-81
    code = priced_s1()
    primary("VISCOSE MVS", "Viscose", {"C2": D("0.03"), "V": D("0.02")})
    run(
        workbook([row(GROUP, "VISCOSE MVS", 60, "CM MVS", 40)]), commit=True
    )  # no component runs C1 / C2 of the PE line
    yarn = next(y for y in YarnRepository().list_all() if y.yarn_code == code)
    # PE on C1 → only VISCOSE (C2, equivalent of C1 in S1) is a candidate → matched
    assert yarn.components[0].material_label == "Viscose - MVS"
    content = workbook([row(GROUP, "CM MVS", 100)])
    result = run(content, commit=True)
    assert result.unmatched_count == 1 and result.unmatched[0].carding_stage == "C1"
    yarn = next(y for y in YarnRepository().list_all() if y.yarn_code == code)
    assert yarn.status == YarnStatus.CHUA_TINH_DUOC
    assert yarn.status_reasons == [
        f"Không ghép được thành phần 'Viscose - MVS' (C1) của mã với thành phần của nhóm tiêu hao '{GROUP}'. "
        "Vui lòng chọn lại nguyên liệu ở màn Nhập NSM."
    ]
    assert yarn.lines  # price kept


def test_row_checks() -> None:  # AC-82, AC-83
    priced_s1()
    content = workbook(
        [
            row(GROUP, "PEE", 100),
            row("A (50/50)", "PE MVS", 50, "CM MVS", 40, tech="Ring"),
            row("B (50/50)", "PE MVS", 50, tech="Ring"),
            row("B (50/50)", "PE MVS", 100, tech="Ring"),
            row("C (50/50)", "PE MVS", None, "CM MVS", 100, tech="Ring"),
            row("D (50/50)", "PE MVS", 50, "CM MVS", 50),
            row("E (50/50)", "PE MVS", 50, "CM MVS", 50, tech="ring"),
            row("F (50/50)", "PE MVS", "abc", tech="Ring"),
        ]
    )
    result = run(content)
    reasons = {r.excel_row: r.reason for r in result.rejected_rows}
    assert reasons[2] == "Không tìm thấy nhóm thành phần 'PEE' ở xưởng S1."
    assert reasons[3] == "Tổng tỷ lệ thành phần phải bằng 100% (hiện là 90,00%)."
    assert reasons[4] == reasons[5] == "Nhóm 'B (50/50)' bị trùng trong file."
    assert reasons[6] == "Thành phần 1: cần cả tên và tỷ lệ."
    assert reasons[7] == "Nhóm mới 'D (50/50)' cần cột Công nghệ là Ring hoặc MVS."
    assert reasons[9] == "Tỷ lệ 1 phải là số % lớn hơn 0 và không quá 100."
    assert result.valid_count == 1 and result.created_count == 1  # E (50/50): a new secondary group
    run(content, commit=True)
    assert group("E (50/50)").level == LossGroupLevel.THU_CAP and group("E (50/50)").technology == Technology.RING
    with pytest.raises(AppError, match="Vui lòng chọn ngày hiệu lực và nhập lý do."):
        run(content, commit=True, reason="")


def test_permissions_and_locked_groups() -> None:  # AC-84
    code = priced_s1()
    yarns = YarnRepository().list_all()
    yarn = next(y for y in yarns if y.yarn_code == code)
    locked = yarn.model_copy(update={"pending_accounting_code": "KT-1"})
    YarnRepository().store(yarns, [locked])
    xs1 = user_with("XS1", username="xs1")
    content = workbook([row(GROUP, "PE MVS", 60, "CM MVS", 40)])
    with acting_as(xs1):
        result = run(content)
    assert result.valid_count == 0 and result.rejected_rows[0].reason.startswith(
        f"Nhóm tiêu hao '{GROUP}' đang được dùng"
    )
    assert run(content).valid_count == 1  # Phòng SO may change a locked group
    with (
        acting_as(user_with("KT", username="kt")),
        pytest.raises(AppError, match="chưa có vai trò cho thao tác"),
    ):  # BR-47
        run(content)
    with (
        acting_as(user_with("XS4", username="xs4")),
        pytest.raises(AppError, match="chỉ được thao tác dữ liệu của xưởng S4"),
    ):
        run(content)  # BR-48: the file is for S1


def test_draft_file_with_extra_columns() -> None:  # AC-85
    priced_s1()
    header = [*HEADER[:5], "Dòng trong file S1", *HEADER[5:], "Gợi ý từ công thức Excel", "Ghi chú gợi ý"]
    rows = [
        [1, GROUP, "MVS", "Sơ cấp", 1, 325, "PE MVS", 60, "CM MVS", 40, *[None] * 7, "=...", "x"],
        [2, "PE MVS", "MVS", "Sơ cấp", 0, 6, *[None] * 11, "", "Số gõ tay"],
    ]
    result = run(workbook(rows, sheet="Khai bao thanh phan S1", header=header))
    assert result.valid_count == 1 and not result.rejected_rows


def test_file_without_the_sheet() -> None:
    priced_s1()
    with pytest.raises(AppError, match="File không có sheet 'Khai bao thanh phan'. Vui lòng dùng file mẫu."):
        run(workbook([row(GROUP, "PE MVS", 100)], sheet="Sheet1"))
