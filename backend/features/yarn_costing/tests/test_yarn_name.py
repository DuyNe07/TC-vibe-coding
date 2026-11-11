"""Tên sợi (bổ sung 2026-11-11): BR-100..BR-109, UC-65..UC-71 - AC-133..AC-146."""

from decimal import Decimal
from io import BytesIO

import pytest
from openpyxl import Workbook, load_workbook

from backend.core.base import UploadedFileDTO
from backend.core.exceptions import AppError
from backend.features.yarn_costing.dto.name_dto import (
    CheckYarnNameRequest,
    ExportRenameListRequest,
    GetNameCheckRequest,
    ImportRenameFileRequest,
    NamePartDTO,
    NameWordDTO,
    NormalizeNamesRequest,
    RenameYarnRequest,
    ResolvePendingWordRequest,
    SaveNameDictionaryRequest,
    SaveNamePartsRequest,
)
from backend.features.yarn_costing.dto.price_dto import ListPriceLinesRequest
from backend.features.yarn_costing.dto.request_dto import CreateYarnRequestRequest
from backend.features.yarn_costing.dto.sales_dto import SuggestYarnsRequest
from backend.features.yarn_costing.models.customer_name import CustomerYarnName
from backend.features.yarn_costing.models.enums import (
    FactoryCode,
    LineType,
    NameIssueKind,
    NameMode,
    NamePartKind,
    NamePartSource,
    NameWordKind,
    NameWordSource,
    PendingWordStatus,
    Technology,
    YarnStatus,
)
from backend.features.yarn_costing.models.loss_group import LossComponent, LossGroup, LossGroupLevel
from backend.features.yarn_costing.models.yarn import CostBreakdown, PriceLine, Yarn, YarnComponent
from backend.features.yarn_costing.repositories.customer_name_repository import CustomerYarnNameRepository
from backend.features.yarn_costing.repositories.loss_group_repository import LossGroupRepository
from backend.features.yarn_costing.repositories.name_check_repository import (
    NamePartRepository,
    NameWordRepository,
    PendingWordRepository,
)
from backend.features.yarn_costing.repositories.yarn_repository import YarnRepository
from backend.features.yarn_costing.services.check_yarn_name_service import CheckYarnNameService
from backend.features.yarn_costing.services.create_yarn_request_service import CreateYarnRequestService
from backend.features.yarn_costing.services.export_rename_list_service import ExportRenameListService
from backend.features.yarn_costing.services.get_name_check_service import GetNameCheckService
from backend.features.yarn_costing.services.import_rename_file_service import ImportRenameFileService
from backend.features.yarn_costing.services.list_price_lines_service import ListPriceLinesService
from backend.features.yarn_costing.services.normalize_names_service import NormalizeNamesService
from backend.features.yarn_costing.services.rename_yarn_service import RenameYarnService
from backend.features.yarn_costing.services.resolve_pending_word_service import ResolvePendingWordService
from backend.features.yarn_costing.services.save_name_dictionary_service import SaveNameDictionaryService
from backend.features.yarn_costing.services.save_name_parts_service import SaveNamePartsService
from backend.features.yarn_costing.services.suggest_similar_yarns_service import SuggestSimilarYarnsService
from backend.features.yarn_costing.tests.helpers import acting_as, setup_factory, user_with

D = Decimal
S1, S4 = FactoryCode.S1, FactoryCode.S4
SALES = user_with("SALES", username="sales", full_name="Sales A")
KT = user_with("KT", username="kt", full_name="Kế toán")


def put(
    code: str,
    name: str,
    factory: FactoryCode = S4,
    status: YarnStatus = YarnStatus.DA_TINH_GIA,
    accounting_code: str | None = None,
    loss_key: str = "",
    components: list[YarnComponent] | None = None,
    revision_of: str = "",
) -> Yarn:
    priced = status in (YarnStatus.DA_TINH_GIA, YarnStatus.CO_MA_KE_TOAN)
    lines = [
        PriceLine(
            line_code=code,
            line_type=LineType.THUONG,
            cost=CostBreakdown(labor=D(20000)),
            accounting_code=accounting_code,
        )
    ]
    yarn = Yarn(
        factory_code=factory,
        yarn_code=code,
        base_code=revision_of or code,
        revision_no=1 if revision_of else 0,
        yarn_name=name,
        loss_group_key=loss_key,
        status=status,
        lines=lines if priced else [],
        components=components or [],
    )
    YarnRepository().save_many([yarn])
    return yarn


def words(*standard: str, wrong: dict[str, str] | None = None) -> None:
    rows = [NameWordDTO(word=w, kind=NameWordKind.CHUAN) for w in standard]
    rows += [NameWordDTO(word=w, kind=NameWordKind.SAI, correct_word=c) for w, c in (wrong or {}).items()]
    SaveNameDictionaryService().handle(SaveNameDictionaryRequest(words=rows))


def yarn(code: str) -> Yarn:
    return next(y for y in YarnRepository().list_all() if y.yarn_code == code)


def check_page(**kwargs):
    return GetNameCheckService().handle(GetNameCheckRequest(**kwargs))


# ---- AC-133: BR-103, UC-66 ----
def test_ac133_dictionary_initialised_then_edited() -> None:
    for i in range(5):
        put(f"S4-{100 + i}", f"COTTON/MODAL {20 + i}/1 (50/50)")
    put("S4-200", "COTTTON 30/1")
    page = check_page()
    found = {w.word: w for w in page.words}
    assert found["COTTON"].source == NameWordSource.KHOI_TAO and "COTTTON" not in found
    assert any(g.text == "COTTON/MODAL" and g.fiber_count == 2 for g in page.groups)
    rows = [*page.words, NameWordDTO(word="cotttton", kind=NameWordKind.SAI, correct_word="cotton")]
    assert "1 chữ thêm" in SaveNameDictionaryService().handle(SaveNameDictionaryRequest(words=rows)).message
    assert NameWordRepository().misspellings() == {"COTTTTON": "COTTON"}
    with pytest.raises(AppError, match="Chữ 'COTTON' bị trùng."):
        SaveNameDictionaryService().handle(
            SaveNameDictionaryRequest(words=[*rows, NameWordDTO(word="COTTON", kind=NameWordKind.CHUAN)])
        )
    with pytest.raises(AppError, match="Chữ 'XYZ' là cách viết sai, vui lòng chọn chữ đúng."):
        SaveNameDictionaryService().handle(
            SaveNameDictionaryRequest(words=[*rows, NameWordDTO(word="XYZ", kind=NameWordKind.SAI)])
        )
    # a second open does not initialise again
    assert len(check_page().words) == len(rows)


# ---- AC-134: BR-100, UC-65 ----
def test_ac134_suspect_names() -> None:
    words("COTTON", "MODAL", "BAMBOO", "SIRO", "COMPACT", "CVC", "FDY")
    put("S4-1", "Cottton/modal 40/1 (50/50)")
    put("S4-2", "BAMBO 40/1 SIRO COMPACT")
    put("S4-3", "CVC 16/1 (")
    put("S4-4", "CVC 30/1 (60/30)")
    put("S4-5", "CVC 30/1 XYZQ (FDY 50D/32F/1)")
    put("S4-6", "Cvc 31/1 (60/40)")
    put("S4-7", "CVC 31/1 (60/40)")
    page = check_page()
    rows = {s.yarn_code: s for s in page.suspects}
    assert set(rows["S4-1"].issues) >= {NameIssueKind.CHU_LA, NameIssueKind.CHU_THUONG}
    assert rows["S4-1"].suggested_name == "COTTON/MODAL 40/1 (50/50)"
    assert rows["S4-2"].suggested_name == "BAMBOO 40/1 SIRO COMPACT"
    assert NameIssueKind.NGOAC in rows["S4-3"].issues
    assert NameIssueKind.TY_LE in rows["S4-4"].issues
    assert NameIssueKind.CHU_LA in rows["S4-5"].issues and NameIssueKind.NGOAC not in rows["S4-5"].issues
    assert "XYZQ" in rows["S4-5"].detail and "FDY" not in rows["S4-5"].detail
    assert rows["S4-5"].suggested_name == "CVC 30/1 XYZQ (FDY 50D/32F/1)"  # no suggestion, 50D/32F not a word
    assert NameIssueKind.TRUNG in rows["S4-6"].issues and NameIssueKind.TRUNG in rows["S4-7"].issues
    assert page.counts[NameIssueKind.TRUNG.value] == 2
    only = check_page(issues=[NameIssueKind.NGOAC])
    assert [s.yarn_code for s in only.suspects] == ["S4-3"]


# ---- AC-135: BR-101, BR-104, UC-15 ----
def test_ac135_request_name_checks() -> None:
    setup_factory(S4, with_loss_group=False)
    words("COTTON", "PE", "CVC", wrong={"COTTTON": "COTTON"})
    service = CreateYarnRequestService()

    def send(name: str, reason: str = ""):
        return service.handle(
            CreateYarnRequestRequest(
                factory_code=S4, yarn_name=name, packaging_code="Type 3", unknown_word_reason=reason
            )
        )

    with pytest.raises(AppError, match="Tên sợi bị thiếu hoặc thừa dấu ngoặc."):
        send("CVC 30/1 (60/40")
    with pytest.raises(AppError, match=r"Tỷ lệ '60/30' cộng lại 90, phải bằng 100."):
        send("CVC 30/1 (60/30)")
    with pytest.raises(AppError, match="Tên có chữ chưa có trong từ điển: COTTTON"):
        send("COTTTON/PE 30/1 (60/40)")
    live = CheckYarnNameService().handle(CheckYarnNameRequest(yarn_name="cottttton/pe 30/1 (60/40)"))
    assert [(u.word, u.suggestion) for u in live.unknown] == [("COTTTTTON", "")]  # 3 letters away: no suggestion
    live = CheckYarnNameService().handle(CheckYarnNameRequest(yarn_name="cotttn/pe 30/1 (60/40)"))
    assert live.unknown[0].suggestion == "COTTON"
    assert live.suggested_name == "COTTON/PE 30/1 (60/40)"
    assert send("COTTON/PE 30/1 (60/40)").yarn.yarn_name == "COTTON/PE 30/1 (60/40)"
    made = send("HEALCA/PE 30/1 (50/50)", reason="Tên thương hiệu xơ mới")
    assert made.yarn.unknown_word_reason == "Tên thương hiệu xơ mới"
    pending = PendingWordRepository().by_word()["HEALCA"]
    assert pending.count == 1 and pending.status == PendingWordStatus.CHO_DUYET
    assert pending.uses[0].yarn_code == made.yarn.yarn_code
    assert send("cvc 30/1").yarn.yarn_name == "CVC 30/1"


def test_ac135_no_dictionary_no_word_check() -> None:
    setup_factory(S4, with_loss_group=False)
    created = CreateYarnRequestService().handle(
        CreateYarnRequestRequest(factory_code=S4, yarn_name="Anything 30/1", packaging_code="Type 3")
    )
    assert created.yarn.yarn_name == "ANYTHING 30/1" and created.yarn.unknown_word_reason == ""


# ---- AC-136 / AC-137: BR-105, BR-108, BR-109 ----
def bambo_setup() -> None:
    words("BAMBOO", "BAMBO", "SIRO", "COMPACT", "CVC", "PE")
    LossGroupRepository().save_many(
        [
            LossGroup(
                factory_code=S4,
                group_key="BAMBO SIRO COMPACT",
                yarn_group_label="BAMBO SIRO COMPACT",
                technology=Technology.RING,
            ),
            LossGroup(
                factory_code=S4,
                group_key="BAMBO/PE (50/50)",
                yarn_group_label="BAMBO/PE (50/50)",
                technology=Technology.RING,
                level=LossGroupLevel.THU_CAP,
                components=[LossComponent(component_group_key="BAMBO SIRO COMPACT", ratio=D("0.5"))],
            ),
        ]
    )
    put(
        "S4-875",
        "BAMBO 40/1 SIRO COMPACT",
        loss_key="BAMBO SIRO COMPACT",
        status=YarnStatus.CO_MA_KE_TOAN,
        accounting_code="S4X",
    )
    put("S4-875 (ĐCNSM1)", "BAMBO 40/1 SIRO COMPACT", loss_key="BAMBO SIRO COMPACT", revision_of="S4-875")
    put(
        "S4-900",
        "BAMBO/PE 40/1 (50/50)",
        loss_key="BAMBO/PE (50/50)",
        components=[YarnComponent(material_label="BAMBO SIRO COMPACT", ratio=D("0.5"))],
    )


def test_ac136_rename_one_yarn() -> None:
    bambo_setup()
    preview = RenameYarnService().handle(
        RenameYarnRequest(yarn_code="S4-875", new_name="bamboo 40/1 siro compact", reason="sai chính tả", preview=True)
    )
    assert (preview.old_loss_group, preview.new_loss_group) == ("BAMBO SIRO COMPACT", "BAMBOO SIRO COMPACT")
    assert yarn("S4-875").yarn_name == "BAMBO 40/1 SIRO COMPACT"  # preview saves nothing
    done = RenameYarnService().handle(
        RenameYarnRequest(yarn_code="S4-875", new_name="bamboo 40/1 siro compact", reason="sai chính tả")
    )
    assert done.message == "Đã đổi tên S4-875: 'BAMBO 40/1 SIRO COMPACT' → 'BAMBOO 40/1 SIRO COMPACT'."
    for code in ("S4-875", "S4-875 (ĐCNSM1)"):
        renamed = yarn(code)
        assert renamed.yarn_name == "BAMBOO 40/1 SIRO COMPACT" and renamed.loss_group_key == "BAMBOO SIRO COMPACT"
        assert (
            renamed.old_names[-1].name == "BAMBO 40/1 SIRO COMPACT" and renamed.old_names[-1].reason == "sai chính tả"
        )
    assert yarn("S4-875").regular_line.total_vnd == D(20000)
    keys = {g.group_key: g for g in LossGroupRepository().list_all()}
    assert "BAMBOO SIRO COMPACT" in keys and "BAMBO SIRO COMPACT" not in keys
    assert keys["BAMBO/PE (50/50)"].components[0].component_group_key == "BAMBOO SIRO COMPACT"
    assert yarn("S4-900").components[0].material_label == "BAMBOO SIRO COMPACT"
    with pytest.raises(AppError, match="Đổi tên làm đổi chi số - hãy tạo yêu cầu mới."):
        RenameYarnService().handle(
            RenameYarnRequest(yarn_code="S4-875", new_name="BAMBOO 30/1 SIRO COMPACT", reason="x")
        )
    put("S4-901", "PE 40/1 SIRO COMPACT", loss_key="PE SIRO COMPACT")
    with pytest.raises(AppError, match="đã có ở mã S4-901"):
        RenameYarnService().handle(RenameYarnRequest(yarn_code="S4-875", new_name="PE 40/1 SIRO COMPACT", reason="x"))
    with pytest.raises(AppError, match="Vui lòng nhập lý do."):
        RenameYarnService().handle(RenameYarnRequest(yarn_code="S4-900", new_name="BAMBOO/PE 40/1 (50/50)"))


def test_ac136_shared_loss_group_refused() -> None:
    bambo_setup()
    put("S4-876", "BAMBO 30/1 SIRO COMPACT", loss_key="BAMBO SIRO COMPACT")
    with pytest.raises(AppError, match="Nhóm tiêu hao 'BAMBO SIRO COMPACT' còn dùng cho 1 sợi khác"):
        RenameYarnService().handle(
            RenameYarnRequest(yarn_code="S4-876", new_name="BAMBOO 30/1 SIRO COMPACT", reason="x")
        )


def test_ac137_sales_rights_and_old_name_search() -> None:
    bambo_setup()
    put("S4-950", "CVC 30/1 (6O/40)", status=YarnStatus.CHUA_TINH_DUOC)
    with acting_as(SALES):
        RenameYarnService().handle(
            RenameYarnRequest(yarn_code="S4-950", new_name="CVC 30/1 (60/40)", reason="gõ nhầm chữ O")
        )
        with pytest.raises(AppError, match="Sales chỉ đổi được tên sợi chưa tính giá"):
            RenameYarnService().handle(
                RenameYarnRequest(yarn_code="S4-875", new_name="BAMBOO 40/1 SIRO COMPACT", reason="x")
            )
    RenameYarnService().handle(RenameYarnRequest(yarn_code="S4-875", new_name="BAMBOO 40/1 SIRO COMPACT", reason="x"))
    found = ListPriceLinesService().handle(ListPriceLinesRequest(keyword="bambo 40/1"))
    assert [r.line_code for r in found.items] == ["S4-875", "S4-875 (ĐCNSM1)"]  # the NSM revision was renamed too
    assert found.items[0].old_names_text == "BAMBO 40/1 SIRO COMPACT"
    same = SuggestSimilarYarnsService().handle(
        SuggestYarnsRequest(yarn_name="BAMBO 40/1 SIRO COMPACT", factory_code=S4)
    )
    assert [s.yarn_code for s in same.same] == ["S4-875"]


# ---- AC-138: UC-69, 5.13 ----
def test_ac138_rename_by_file() -> None:
    bambo_setup()
    put("S4-960", "CVC 30/1 (6O/40)", status=YarnStatus.CHUA_TINH_DUOC)
    put("S4-961", "TC 30/1 (65/35)")
    exported = ExportRenameListService().handle(ExportRenameListRequest())
    sheet = load_workbook(BytesIO(exported.content))["Sua ten"]
    header = [c.value for c in sheet[1]]
    assert header[-2:] == ["Tên mới", "Lý do sửa"] and sheet.max_row >= 2
    book = Workbook()
    ws = book.active
    ws.title = "Sua ten"
    ws.append(["Xưởng", "Mã", "Tên mới", "Lý do sửa"])
    ws.append(["S4", "S4-960", "CVC 30/1 (60/40)", "gõ nhầm"])
    ws.append(["S4", "S4-961", "TC 30/1 (65/35) MVS", ""])
    ws.append(["S4", "S4-875", "BAMBOO 30/1 SIRO COMPACT", "sai"])
    ws.append(["S4", "S4-999", "", ""])
    stream = BytesIO()
    book.save(stream)
    file = UploadedFileDTO(filename="sua-ten.xlsx", content=stream.getvalue())
    preview = ImportRenameFileService().handle(ImportRenameFileRequest(file=file))
    assert [r.yarn_code for r in preview.valid] == ["S4-960"]
    reasons = {r.key: r.reason for r in preview.rejected_rows}
    assert reasons["S4-961"] == "Vui lòng nhập lý do." and "chi số" in reasons["S4-875"]
    assert yarn("S4-960").yarn_name == "CVC 30/1 (6O/40)"
    done = ImportRenameFileService().handle(ImportRenameFileRequest(file=file, commit=True))
    assert done.message == "Đã đổi tên 1 sợi, bị loại 2 dòng."
    assert yarn("S4-960").yarn_name == "CVC 30/1 (60/40)" and yarn("S4-961").yarn_name == "TC 30/1 (65/35)"


# ---- AC-139: BR-104 ----
def test_ac139_word_added_when_yarn_priced() -> None:
    setup_factory(S4, with_loss_group=False)
    words("PE")
    made = CreateYarnRequestService().handle(
        CreateYarnRequestRequest(
            factory_code=S4, yarn_name="HEALCA/PE 30/1 (50/50)", packaging_code="Type 3", unknown_word_reason="mới"
        )
    )
    check_page()
    assert PendingWordRepository().by_word()["HEALCA"].status == PendingWordStatus.CHO_DUYET
    priced = yarn(made.yarn.yarn_code).model_copy(update={"status": YarnStatus.DA_TINH_GIA})
    YarnRepository().save(priced)
    page = check_page()
    assert next(w for w in page.words if w.word == "HEALCA").source == NameWordSource.TU_THEM
    assert PendingWordRepository().by_word()["HEALCA"].status == PendingWordStatus.TU_THEM


# ---- AC-140: BR-106, UC-67 ----
def test_ac140_fix_word_everywhere() -> None:
    words("COTTON", "VISCOSE", "RING")
    LossGroupRepository().save_many(
        [
            LossGroup(
                factory_code=S4,
                group_key="VICOSE",
                yarn_group_label="VICOSE",
                material="VICOSE",
                technology=Technology.RING,
            ),
            LossGroup(
                factory_code=S4,
                group_key="COTTON/VICOSE (50/50)",
                yarn_group_label="COTTON/VICOSE (50/50)",
                technology=Technology.RING,
                level=LossGroupLevel.THU_CAP,
                components=[LossComponent(component_group_key="VICOSE", ratio=D("0.5"))],
            ),
        ]
    )
    put(
        "S4-300",
        "COTTON/VICOSE 30/1 (50/50)",
        loss_key="COTTON/VICOSE (50/50)",
        components=[YarnComponent(material_label="VICOSE - Ring", ratio=D("0.5"))],
    )
    PendingWordRepository().record(["VICOSE"], "S4-300", "Sales A", "")
    pending = PendingWordRepository().by_word()["VICOSE"]
    preview = ResolvePendingWordService().handle(
        ResolvePendingWordRequest(pending_id=pending.id, correct_word="viscose", preview=True)
    )
    assert (preview.yarn_count, preview.group_count) == (1, 2)
    done = ResolvePendingWordService().handle(ResolvePendingWordRequest(pending_id=pending.id, correct_word="VISCOSE"))
    assert done.message == "Đã sửa 'VICOSE' thành 'VISCOSE' trong 1 tên sợi và 2 nhóm tiêu hao."
    fixed = yarn("S4-300")
    assert fixed.yarn_name == "COTTON/VISCOSE 30/1 (50/50)" and fixed.loss_group_key == "COTTON/VISCOSE (50/50)"
    assert fixed.components[0].material_label == "VISCOSE - Ring" and fixed.regular_line.total_vnd == D(20000)
    groups = {g.group_key: g for g in LossGroupRepository().list_all()}
    assert groups["VISCOSE"].material == "VISCOSE"
    assert groups["COTTON/VISCOSE (50/50)"].components[0].component_group_key == "VISCOSE"
    assert NameWordRepository().misspellings()["VICOSE"] == "VISCOSE"
    assert PendingWordRepository().by_word()["VICOSE"].status == PendingWordStatus.DA_SUA


def test_ac140_clash_changes_nothing() -> None:
    words("COTTON", "VISCOSE")
    put("S4-301", "COTTON/VICOSE 30/1 (50/50)")
    put("S4-302", "COTTON/VISCOSE 30/1 (50/50)")
    PendingWordRepository().record(["VICOSE"], "S4-301", "Sales A", "")
    pending = PendingWordRepository().by_word()["VICOSE"]
    with pytest.raises(AppError, match="Không sửa được vì sẽ trùng: COTTON/VISCOSE 30/1"):
        ResolvePendingWordService().handle(ResolvePendingWordRequest(pending_id=pending.id, correct_word="VISCOSE"))
    assert yarn("S4-301").yarn_name == "COTTON/VICOSE 30/1 (50/50)"
    added = ResolvePendingWordService().handle(ResolvePendingWordRequest(pending_id=pending.id))
    assert added.message == "Đã thêm 'VICOSE' vào từ điển." and "VICOSE" in NameWordRepository().standard()


# ---- AC-141 / AC-142: BR-102, UC-70 ----
def parts_setup() -> None:
    parts = [
        NamePartDTO(kind=NamePartKind.NHOM, text="CVC", fiber_count=2),
        NamePartDTO(kind=NamePartKind.NHOM, text="PE", fiber_count=1),
        NamePartDTO(kind=NamePartKind.TU_KHOA, text="SIRO", sequence=10),
        NamePartDTO(kind=NamePartKind.TU_KHOA, text="COMPACT", sequence=20),
        NamePartDTO(kind=NamePartKind.TU_KHOA, text="BCI", sequence=30),
        NamePartDTO(kind=NamePartKind.TU_KHOA, text="MVS", sequence=40),
    ]
    SaveNamePartsService().handle(SaveNamePartsRequest(parts=parts))


def test_ac141_name_builder() -> None:
    parts_setup()
    build = CheckYarnNameService()
    res = build.handle(
        CheckYarnNameRequest(
            mode=NameMode.GHEP, group="CVC", count=D(30), ratios=[D(60), D(40)], keywords=["BCI", "SIRO", "COMPACT"]
        )
    )
    assert res.name == "CVC 30/1 (60/40) SIRO COMPACT BCI" and res.problem == ""
    assert (
        build.handle(CheckYarnNameRequest(mode=NameMode.GHEP, group="PE", count=D(30), keywords=["MVS"])).name
        == "PE 30/1 MVS"
    )
    bad = build.handle(CheckYarnNameRequest(mode=NameMode.GHEP, group="CVC", count=D(30), ratios=[D(60), D(30)]))
    assert bad.problem == "Tổng tỷ lệ phải bằng 100 (hiện là 90)." and bad.name == ""
    assert (
        build.handle(CheckYarnNameRequest(mode=NameMode.GHEP, group="", count=D(30))).problem
        == "Vui lòng chọn nhóm sợi."
    )
    with pytest.raises(AppError, match="Nhóm 'CVC' bị trùng."):
        SaveNamePartsService().handle(
            SaveNamePartsRequest(
                parts=[NamePartDTO(kind=NamePartKind.NHOM, text="CVC"), NamePartDTO(kind=NamePartKind.NHOM, text="cvc")]
            )
        )


def test_ac142_unknown_group_added_by_sales() -> None:
    setup_factory(S4, with_loss_group=False)
    parts_setup()
    with acting_as(SALES):
        CreateYarnRequestService().handle(
            CreateYarnRequestRequest(
                factory_code=S4, yarn_name="HEMP/LINEN 20/1 (50/50)", packaging_code="Type 3", name_mode="Gõ tay"
            )
        )
    added = next(p for p in NamePartRepository().groups() if p.text == "HEMP/LINEN")
    assert added.fiber_count == 2 and added.source == NamePartSource.SALES_MOI and not added.reviewed
    assert any(g.text == "HEMP/LINEN" and not g.reviewed for g in check_page().groups)


# ---- AC-143 / AC-144: BR-107, BR-108 ----
def test_ac143_normalize_and_duplicates() -> None:
    put("S4-10", "Cotton/Modal 40/1 (50/50)")
    put("S4-11", "COTTON/MODAL 40/1 (50/50)", status=YarnStatus.CO_MA_KE_TOAN, accounting_code="S4AAA")
    put("S4-12", "Tc 30/1 (65/35)")
    CustomerYarnNameRepository().add(
        CustomerYarnName(base_code="S4-10", customer_name="ABC", customer_yarn_name="CM 40")
    )
    preview = NormalizeNamesService().handle(NormalizeNamesRequest())
    assert (preview.group_count, preview.keep_count, preview.drop_count) == (1, 1, 1)
    keep = next(d for d in preview.decisions if d.keep)
    drop = next(d for d in preview.decisions if not d.keep)
    assert keep.yarn_code == "S4-11" and drop.yarn_code == "S4-10" and drop.reason == "Trùng tên với S4-11"
    assert preview.plan_file is not None and [c.yarn_code for c in preview.changes] == ["S4-12"]
    assert yarn("S4-12").yarn_name == "Tc 30/1 (65/35)"
    done = NormalizeNamesService().handle(NormalizeNamesRequest(commit=True))
    assert done.committed and done.message.startswith("Đã chuẩn hoá 1 tên; loại 1 mã trùng tên")
    dropped = yarn("S4-10")
    assert dropped.status == YarnStatus.KHONG_SAN_XUAT and dropped.not_produced_reason == "Trùng tên với S4-11"
    assert dropped.yarn_name == "Cotton/Modal 40/1 (50/50)"
    assert yarn("S4-12").yarn_name == "TC 30/1 (65/35)" and yarn("S4-12").old_names[0].name == "Tc 30/1 (65/35)"
    assert CustomerYarnNameRepository().list_all()[0].base_code == "S4-11"
    again = NormalizeNamesService().handle(NormalizeNamesRequest())
    assert again.message == "Mọi tên đã viết hoa, không có tên trùng."


def test_ac144_duplicate_with_accounting_code_moved() -> None:
    put("S41603600010000000FC", "CM 36/1", status=YarnStatus.CO_MA_KE_TOAN, accounting_code="S41603600010000000FC")
    put("S41603600010000000", "CM 36/1 ", status=YarnStatus.CO_MA_KE_TOAN, accounting_code="S41603600010000000")
    put("S4-21", "PE 30/1", status=YarnStatus.CHO_XUONG_XEM)
    put("S4-22", "pe 30/1", status=YarnStatus.CHO_XUONG_XEM)
    NormalizeNamesService().handle(NormalizeNamesRequest(commit=True))
    dropped = yarn("S41603600010000000")  # same conditions: the code created first (…FC) is kept
    assert dropped.status == YarnStatus.KHONG_SAN_XUAT and dropped.lines == []
    assert yarn("S41603600010000000FC").merged_accounting_codes == ["S41603600010000000"]
    assert yarn("S4-22").status == YarnStatus.TU_CHOI and yarn("S4-22").reject_reason == "Trùng tên với S4-21"
    found = ListPriceLinesService().handle(ListPriceLinesRequest(keyword="S41603600010000000"))
    assert [r.line_code for r in found.items] == ["S41603600010000000FC"]
    assert found.items[0].merged_accounting_codes == ["S41603600010000000"]


# ---- AC-145: BR-109 ----
def test_ac145_rights() -> None:
    bambo_setup()
    with acting_as(SALES):
        assert check_page().words
        with pytest.raises(AppError, match="chưa có vai trò"):
            SaveNameDictionaryService().handle(SaveNameDictionaryRequest(words=[]))
        with pytest.raises(AppError, match="chưa có vai trò"):
            NormalizeNamesService().handle(NormalizeNamesRequest())
    with acting_as(KT):
        with pytest.raises(AppError, match="chưa có vai trò"):
            RenameYarnService().handle(
                RenameYarnRequest(yarn_code="S4-900", new_name="BAMBOO/PE 40/1 (50/50)", reason="x")
            )
        with pytest.raises(AppError, match="chưa có vai trò"):
            check_page()


# ---- AC-146: existing behaviour ----
def test_ac146_valid_request_unchanged() -> None:
    setup_factory(S4, with_loss_group=False)
    words("CVC", "MVS")
    created = CreateYarnRequestService().handle(
        CreateYarnRequestRequest(factory_code=S4, yarn_name="CVC 30/1 (60/40) MVS", packaging_code="Type 3")
    )
    assert created.yarn.unknown_word_reason == "" and created.yarn.status == YarnStatus.CHO_XUONG_XEM
    assert PendingWordRepository().list_all() == []
    with pytest.raises(AppError, match="đã có ở mã"):
        CreateYarnRequestService().handle(
            CreateYarnRequestRequest(factory_code=S4, yarn_name="cvc 30/1 (60/40) mvs", packaging_code="Type 3")
        )


# ---- Fix 2026-11-11: any yarn can be renamed, not only the suspect ones; the picker shows the current name ----
def test_fix_rename_any_yarn_listed_with_current_name() -> None:
    from backend.features.yarn_costing.dto.request_dto import ListYarnsRequest
    from backend.features.yarn_costing.services.list_yarns_service import ListYarnsService

    words("CVC", "MVS", "PE")
    put("S4-970", "CVC 30/1 (60/40) MVS", loss_key="CVC (60/40) MVS")
    assert all(s.yarn_code != "S4-970" for s in check_page(issues=[]).suspects)  # a correct name: not a suspect
    listed = {y.yarn_code: y for y in ListYarnsService().handle(ListYarnsRequest()).items}
    assert listed["S4-970"].yarn_name == "CVC 30/1 (60/40) MVS"
    assert listed["S4-970"].loss_group_key == "CVC (60/40) MVS"
    done = RenameYarnService().handle(
        RenameYarnRequest(yarn_code="S4-970", new_name="CVC 30/1 (60/40) MVS PE", reason="theo khách")
    )
    assert done.saved and yarn("S4-970").yarn_name == "CVC 30/1 (60/40) MVS PE"
