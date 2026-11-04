# UI design: yarn_costing

> **Cập nhật 2026-10-13:** khối "Người thao tác" (chọn nhóm + mã nội bộ + tên, UC-01, UC-39, BR-46, `ActorDTO`) đã
> bỏ. Người thao tác = tài khoản đăng nhập; quyền theo nhóm = vai trò của ứng dụng (SALES, XS1, XS4, KT, SO) do quản
> trị viên tick ở `/admin`; màn hình 8 là "Nhật ký thao tác". Nguồn đúng: `docs/business/yarn_costing.md` (mục 2,
> BR-46..49, mục 10). Các đoạn bên dưới còn nhắc `actor` là lịch sử, không làm theo.

Nguồn: `docs/business/yarn_costing.md` (mục 4-9, nhất là mục 8 "Giao diện đã chốt"), `docs/plans/yarn_costing-implementation-plan.md`
mục 2 (Controller contract + bảng Pages). Streamlit đã cài: **1.64.0** (kết quả kiểm tra ở mục 0.9). Không thêm thư viện;
biểu đồ dùng `st.bar_chart` / `st.line_chart`.

**Lưu ý cho UI-build:** backend được viết song song theo cùng hợp đồng. Tên method, request, response và các field chính
lấy đúng theo hợp đồng; các field phụ (tên field của `PriceLineRowDTO`, `YarnSummaryDTO`, `StageCostDTO`, `UserGroupDTO`...,
tên thành viên enum) là **giả định** - PHẢI đọc `backend/features/yarn_costing/dto/*.py` thật và sửa cho khớp. Nhãn tiếng
Việt trên màn hình giữ đúng như trong tài liệu nghiệp vụ.

## 0. Quy ước chung

### 0.1 Import chuẩn (mỗi trang chỉ import cái nó dùng)
```python
from datetime import date, timedelta
from decimal import Decimal

import streamlit as st

from backend.core.exceptions import AppError
from backend.core.gateway import gateway
from backend.features.yarn_costing import YarnCostingController
from backend.features.yarn_costing.dto.common_dto import (
    ActorDTO, FactoryCode, GroupCode, YarnStatus, LineType, LossGroupLevel, RecoveryType, Technology, ImportMode, NsmMode,
)
from backend.features.yarn_costing.dto.reference_dto import GetReferenceDataRequest, ReferenceDataResponse
from frontend.core.base_page import BasePage
from frontend.core.components import (
    data_table, download_button, editable_table, empty_state, file_upload, panel, section_title, show_error, show_success, stat_row,
)
from frontend.core.formatting import format_datetime, format_number
from frontend.features.yarn_costing.components.actor_block import render_actor_block, current_actor, clear_actor
from frontend.features.yarn_costing.components.permissions import action_state
from frontend.features.yarn_costing.components.flash import set_flash, show_flash
from frontend.features.yarn_costing.components.display import vnd, usd, pct, minutes4, rate2, fmt_date, yes_no, to_decimal, from_percent
from frontend.features.yarn_costing.components.labels import label_of, STATUS_LABELS, LINE_TYPE_LABELS, LEVEL_LABELS, ...
from frontend.features.yarn_costing.components.recalc_diff import render_recalc_diff, open_recalc_diff_dialog
```

### 0.2 Mở controller + dữ liệu tham chiếu (luôn an toàn khi tải trang)
```python
feature = gateway.open(YarnCostingController)
reference = feature.get_reference_data(GetReferenceDataRequest(factory_code=None))  # UC-38, không lỗi khi rỗng
```
Screen 5 gọi thêm `feature.get_reference_data(GetReferenceDataRequest(factory_code=<xưởng chọn>))` để có công đoạn, định mức,
đóng gói, hồi phế, quy trình của đúng xưởng.
Danh sách xưởng: `reference.factories` (`FactoryDTO{code, name, blend_slots}`); nhãn hiển thị `f"{f.code} - {f.name}"`.

**Chỉ những use case sau được gọi khi tải trang (trước khi người dùng bấm gì):** `get_reference_data`, `list_price_lines`,
`list_yarns`, `list_loss_groups`, `list_recalc_batches`, `list_import_batches`, `list_audit_log`, và ở Screen 7 các báo cáo chỉ
đọc `get_dashboard`, `check_price_anomalies`, `check_nsm_anomalies` (chỉ đọc, đầu vào mặc định luôn hợp lệ - xem giả định G6).
`analyze_yarn_name` chỉ gọi khi người dùng đã gõ tên sợi. `get_yarn_detail`, `get_recalc_diff`, `get_legacy_comparison` chỉ gọi
sau khi người dùng chọn một dòng. Mọi use case thay đổi dữ liệu chỉ chạy trong `if st.button(...)` / `st.form_submit_button` /
nút xác nhận trong hộp thoại.

### 0.3 Nhãn enum - `components/labels.py`
Enum re-export ở `dto/common_dto.py`. Giá trị enum có thể là mã (như feature internal_cost_transfer) → luôn hiển thị qua dict
nhãn; nếu giá trị enum đã là chữ tiếng Việt thì dict vẫn đúng. UI-build điền member thật:
```python
STATUS_LABELS = {YarnStatus.<CHO_XUONG_XEM>: "Chờ xưởng xem", <DA_HUY>: "Đã huỷ", <TU_CHOI>: "Từ chối",
                 <DA_TINH_GIA>: "Đã tính giá", <CHUA_TINH_DUOC>: "Chưa tính được", <CO_MA_KE_TOAN>: "Có mã kế toán"}
LINE_TYPE_LABELS = {<THUONG>: "Thường", <THI_NGHIEM>: "Thí nghiệm", <CHIET_KHAU>: "Chiết khấu", <PHU_PHI>: "Phụ phí"}
LEVEL_LABELS = {<SO_CAP>: "Sơ cấp", <THU_CAP>: "Thứ cấp", <NHAP_TU_FILE>: "Nhập từ file - chưa khai báo thành phần"}
RECOVERY_LABELS = {<KHONG>: "Không", <CHAI_THO>: "Chải thô", <THO>: "Thô", <CON>: "Con"}   # nếu enum có "Không"
TECHNOLOGY_LABELS = {<RING>: "Ring", <MVS>: "MVS"}
IMPORT_MODE_LABELS = {<CHUYEN_DU_LIEU_BAN_DAU>: "Chuyển dữ liệu ban đầu", <CAP_NHAT_HANG_LOAT>: "Cập nhật hàng loạt"}
NSM_MODE_LABELS = {<TU_NHAP>: "Tự nhập", <TU_DIEN>: "Tự điền"}
GROUP_LABELS = {GroupCode.SALES: "Sales", GroupCode.XS1: "Xưởng S1", GroupCode.XS4: "Xưởng S4", GroupCode.SO: "Phòng SO", GroupCode.KT: "Kế toán"}
STATUS_ORDER = [<CHO_XUONG_XEM>, <CHUA_TINH_DUOC>, <DA_TINH_GIA>, <CO_MA_KE_TOAN>, <TU_CHOI>, <DA_HUY>]

def label_of(labels: dict, value) -> str:          # None -> "-", giá trị lạ -> str(value)
def value_of(labels: dict, label: str | None):      # nhãn -> enum (dùng cho SelectboxColumn trong bảng sửa trong ô)
```
Widget chọn enum (`st.selectbox/multiselect/segmented_control/radio`) truyền **giá trị enum** làm options và
`format_func=lambda v: label_of(X_LABELS, v)`. Bảng sửa trong ô dùng `SelectboxColumn(options=[nhãn...])`, trước khi dựng DTO
map ngược bằng `value_of`.

### 0.4 Hiển thị số - `components/display.py` (chỉ định dạng, không phải quy tắc nghiệp vụ; BR-23)
```python
def vnd(x) -> float | None       # round(float(x), 0)      - VND/kg, làm tròn đến đồng
def usd(x) -> float | None       # round(float(x), 4)
def pct(x) -> float | None       # round(float(x) * 100, 2) - tỷ lệ / tiêu hao / hồi phế dạng %
def minutes4(x) -> float | None  # round(float(x), 4)      - phút/kg
def rate2(x) -> float | None     # round(float(x), 2)      - định mức VND/phút
def fmt_date(d) -> str           # "DD/MM/YYYY" hoặc "-"
def yes_no(b) -> str             # "Có" / "Không"
def to_decimal(x) -> Decimal     # None/"" -> Decimal("0"); còn lại Decimal(str(x))
def from_percent(x) -> Decimal   # to_decimal(x) / Decimal(100)  - ô nhập "%" -> phân số gửi backend (0.015)
def blend_text(ratios: dict[str, Decimal], slots: list[str]) -> str   # "PE 40,00% · Cotton 60,00%" (bỏ ô = 0)
```
- Bảng chỉ xem: cột tiền `NumberColumn(label, format="localized")` với giá trị `vnd(...)`; USD `NumberColumn(format="%.4f")`;
  % `NumberColumn(format="%.2f%%")` với giá trị `pct(...)`; ngày `DateColumn(format="DD/MM/YYYY")`; ngày giờ
  `DatetimeColumn(format="DD/MM/YYYY HH:mm")`.
- Bảng sửa trong ô: Decimal được đổi sang `float` khi đưa vào bảng; ô % hiển thị số % (1,5 = 1,5%) với
  `NumberColumn(format="%.2f", min_value=0.0, max_value=100.0, step=0.01)`; khi gửi đi dùng `from_percent`, còn số thường
  dùng `to_decimal`. Kiểm tra hợp lệ (tổng 100%, < 100%...) luôn do backend (BR-xx) - trang không tự kiểm.
- Mỗi bảng được dựng từ một danh sách cột (field → nhãn → column_config) viết trong page (hoặc `components/columns.py`
  nếu dùng ở 2 trang): row dict có key = **nhãn tiếng Việt**, nên dòng được chọn (`data_table(selection=...)`) đọc bằng
  nhãn, ví dụ `picked[0]["Mã dòng"]`.

### 0.5 Thông báo sau khi thao tác - `components/flash.py`
Sau một thao tác thành công trang thường `st.rerun()` để tải lại bảng, nên thông báo phải sống qua lần chạy lại:
```python
def set_flash(state: SessionState, message: str) -> None:   # state.set("flash", message)
def show_flash(state: SessionState) -> None:                # msg = state.pop("flash"); if msg: show_success(msg)
```
Mọi trang gọi `show_flash(self.state)` ngay sau khối xác thực. Mẫu cho mọi nút thay đổi dữ liệu KHÔNG hỏi lại:
```python
if st.button("<Nhãn>", type="primary", key=self.key("..."), disabled=disabled, help=help_text):
    result = feature.<method>(<Request>(actor=actor, ...))     # AppError -> BasePage tự hiện lỗi
    set_flash(self.state, result.message)
    st.rerun()
```
(Với response không có `message` - `FileDownloadDTO` - không dùng flash.)

### 0.6 Khối xác thực chung - `components/actor_block.py` (Screen 1-6, 8; UC-39)
Nhớ trong `self.state` (namespace theo feature `yarn_costing`, KHÔNG qua `self.key()`) nên dùng chung cho **mọi trang** của
chức năng trong phiên làm việc; không hỏi lại mỗi lần bấm nút; có nút "Đổi người thao tác".
```python
ACTOR_KEY = "actor"  # dict: group_code, group_name, person_name, factory_code, access_code


def current_actor(state: SessionState) -> dict | None:
    return state.get(ACTOR_KEY)


def clear_actor(state: SessionState) -> None:
    state.pop(ACTOR_KEY)


def actor_dto(state: SessionState) -> ActorDTO | None:
    info = current_actor(state)
    if not info:
        return None
    return ActorDTO(group_code=info["group_code"], access_code=info["access_code"], person_name=info["person_name"])


def render_actor_block(feature, state: SessionState, reference: ReferenceDataResponse) -> ActorDTO | None:
    """Khối 'Người thao tác'. Trả ActorDTO đã xác thực (UC-39) hoặc None."""
    info = current_actor(state)
    with panel("Người thao tác", icon="🔐"):
        if info:
            left, right = st.columns([4, 1], vertical_alignment="center")
            left.success(f"Đang thao tác: {info['group_name']} - {info['person_name']}.", icon="👤")
            if right.button("Đổi người thao tác", key=state.key("actor.change")):
                clear_actor(state)
                st.rerun()
            return actor_dto(state)
        st.caption(
            "Chọn nhóm, nhập mã nội bộ của nhóm và chọn tên của bạn. Chỉ cần làm một lần trong phiên làm việc; "
            "xem, tra cứu và xuất file không cần xác thực."
        )
        groups = [g for g in reference.groups if g.active]
        by_code = {g.code: g for g in groups}
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1], vertical_alignment="bottom")
        group_code = c1.selectbox(
            "Nhóm",
            list(by_code),
            index=None,
            placeholder="Chọn nhóm",
            format_func=lambda c: by_code[c].name,
            key=state.key("actor.group"),
        )
        access_code = c2.text_input("Mã nội bộ", type="password", key=state.key("actor.access_code"))
        names = [m.name for m in by_code[group_code].members if m.active] if group_code else []  # G2
        person_name = c3.selectbox(
            "Tên của bạn", names, index=None, placeholder="Chọn tên", disabled=not names, key=state.key("actor.person")
        )
        if c4.button(
            "Xác nhận",
            type="primary",
            key=state.key("actor.confirm"),
            disabled=not (group_code and access_code and person_name),
        ):
            actor = ActorDTO(group_code=group_code, access_code=access_code, person_name=person_name)
            try:
                result = feature.verify_actor(VerifyActorRequest(actor=actor))
            except AppError as exc:
                show_error(exc)  # thông báo BR-46; phần còn lại của trang vẫn hiện
            else:
                state.set(
                    ACTOR_KEY,
                    {
                        "group_code": result.group_code,
                        "group_name": result.group_name,
                        "person_name": result.person_name,
                        "factory_code": result.factory_code,
                        "access_code": access_code,
                    },
                )
                set_flash(state, result.message)  # "Đang thao tác: <tên nhóm> - <tên người>."
                st.rerun()
        return None
```
- Lần đầu tải trang: `reference.groups` có 5 nhóm (giả định khởi tạo) nhưng có thể chưa có thành viên → ô "Tên của bạn" bị tắt,
  không lỗi. Nếu `reference.groups` rỗng: selectbox rỗng, nút tắt - vẫn không lỗi.
- Backend vẫn kiểm tra lại BR-46 ở mỗi thao tác (mã nội bộ có thể đã bị SO đổi) → lỗi BR-46 do `BasePage` hiện; người dùng bấm
  "Đổi người thao tác" để xác thực lại.
- Khoá widget dùng `state.key("actor.*")` (giống nhau ở mọi trang, mỗi lúc chỉ 1 trang hiển thị nên không trùng).

### 0.7 Tắt nút theo quyền - `components/permissions.py` (BR-46, BR-47, BR-48 - chỉ để hiển thị; backend vẫn là nơi quyết định)
```python
UC_BY_GROUP = {   # đúng bảng BR-47
    GroupCode.SALES: {"UC-15", "UC-16", "UC-17"},
    GroupCode.XS1: {"UC-11", "UC-12", "UC-13", "UC-14", "UC-18", "UC-20", "UC-21", "UC-23", "UC-24", "UC-25", "UC-26", "UC-28", "UC-34"},
    GroupCode.XS4: <như XS1>,
    GroupCode.KT: {"UC-28"},
    GroupCode.SO: None,   # mọi UC thay đổi dữ liệu
}

def action_state(state: SessionState, uc: str, factory_code: str | None = None) -> tuple[bool, str | None]:
    """(disabled, help) cho một nút thao tác."""
    info = current_actor(state)
    if not info:
        return True, "Vui lòng chọn nhóm, nhập đúng mã nội bộ và chọn tên của bạn."          # BR-46
    allowed = UC_BY_GROUP.get(GroupCode(info["group_code"]), set())
    if allowed is not None and uc not in allowed:
        return True, f"Nhóm '{info['group_name']}' không được thực hiện thao tác này."        # BR-47
    if info.get("factory_code") and factory_code and str(info["factory_code"]) != str(factory_code):
        return True, f"Bạn chỉ được thao tác dữ liệu của xưởng {info['factory_code']}."       # BR-48
    return False, None
```
Dùng: `disabled, why = action_state(self.state, "UC-28", line_factory)` → `st.button(..., disabled=disabled, help=why)`.
Khi nút bị tắt vì quyền, thêm `st.caption(why)` ngay dưới nhóm nút (mục 8: "bị tắt kèm chú thích").
Trường hợp đặc biệt: UC-13 trên nhóm đang khoá chỉ Phòng SO (BR-24) - xem Screen 4. UC-34 của xưởng: chỉ "Cập nhật hàng loạt"
(BR-45) - backend tự bỏ qua sheet không được phép; UI chỉ tắt "Chuyển dữ liệu ban đầu" cho nhóm không phải SO.

### 0.8 Hộp thoại xác nhận (mẫu; `st.dialog`)
Dùng trước: Huỷ yêu cầu, Từ chối, Xoá nhóm tiêu hao, Xoá dòng CK/PP, mọi nút "… và tính lại" (Screen 5), "Lưu hệ số",
"Lưu thay đổi" nhóm tiêu hao, "Lưu N dòng hợp lệ". KHÔNG hỏi lại ở các nút còn lại (mục 8).
```python
def _confirm(self, title: str, question: str, confirm_label: str, action) -> None:
    @st.dialog(title)
    def _dialog() -> None:
        st.write(question)
        yes, no = st.columns(2)
        if yes.button(confirm_label, type="primary", key=self.key(f"dlg.{confirm_label}.yes")):
            try:
                message = action()            # gọi controller, trả result.message
            except AppError as exc:
                show_error(exc)               # lỗi hiện trong hộp thoại, người dùng sửa rồi thử lại
            else:
                set_flash(self.state, message)
                st.rerun()
        if no.button("Không", key=self.key(f"dlg.{confirm_label}.no")):
            st.rerun()
    _dialog()

if st.button("<Nhãn>", key=self.key("..."), disabled=disabled, help=why):
    self._confirm("<Tiêu đề>", "<Câu hỏi>", "<Nhãn xác nhận>", lambda: feature.<method>(<Request>(...)).message)
```
Giá trị form (ô nhập) được đọc TRƯỚC khi mở hộp thoại và đóng gói sẵn vào request trong lambda. Mỗi màn hình dưới đây ghi: tiêu
đề, câu hỏi, nhãn xác nhận, method.

### 0.9 Kiểm tra API Streamlit đã cài (1.64.0)
Lệnh: `.venv/Scripts/python.exe -X utf8 -c "import inspect, streamlit as st; print(st.__version__, inspect.signature(st.<fn>))"`
cho từng hàm, và `inspect.signature(st.column_config.<Col>)`; thêm kiểm tra literal `NumberFormat` và `DialogWidth`.
| Hàm | Kết quả |
|---|---|
| `st.__version__` | `1.64.0` |
| `st.data_editor` | có `column_config`, `column_order`, `disabled`, `num_rows` ("fixed"/"dynamic"/"add"/"delete"), `hide_index`, `height`, `key` (dùng qua `editable_table`) |
| `st.dataframe` | có `on_select="rerun"`, `selection_mode`, `column_config`, `column_order`, `key` (dùng qua `data_table(selection=...)`) |
| `st.dialog` | `(title, *, width="small"\|"medium"\|"large", dismissible, icon, on_dismiss)` |
| `st.form` / `st.form_submit_button` | có; submit có `type`, `disabled`, `key` |
| `st.tabs` | có (`default`, `key` có nhưng không dùng) - Screen 1 (khối chi tiết) và Screen 5 |
| `st.columns` | có `vertical_alignment` |
| `st.segmented_control` / `st.pills` | có `selection_mode`, `default`, `required`, `format_func` |
| `st.selectbox` | có `index=None`, `placeholder`, `format_func`, `disabled` |
| `st.multiselect` | có `default`, `format_func`, `placeholder` |
| `st.date_input` | có `value=None` (ngày trống), `format="DD/MM/YYYY"`, `min_value`, `max_value` |
| `st.toggle`, `st.radio(horizontal=True)` | có |
| `st.number_input` | có `min_value`, `max_value`, `value`, `step`, `format` |
| `st.text_input` | có `type="password"`, `placeholder`, `max_chars` |
| `st.text_area`, `st.button(type, help, disabled)`, `st.expander`, `st.metric(border=True)` | có |
| `st.bar_chart` / `st.line_chart` | có `x`, `y`, `x_label`, `y_label` |
| `st.download_button` | có (dùng qua `download_button`) |
| `st.file_uploader` | có `type` (dùng qua `file_upload`) |
| `st.info` / `st.warning` / `st.success` / `st.caption` | có |
| `st.column_config.NumberColumn` | có `format` (printf hoặc "localized", "percent"...), `min_value`, `max_value`, `step`, `disabled`, `required` |
| `TextColumn`, `DateColumn(format)`, `DatetimeColumn(format)`, `SelectboxColumn(options, required)`, `CheckboxColumn`, `ListColumn`, `MultiselectColumn(options)` | có |
| `st.switch_page` (qua `self.go_to`) | có |
Không có hàm/tham số nào phải bỏ. Không dùng `use_container_width` (dùng `width="stretch"` mặc định).

### 0.10 Chuyển trang có mang dữ liệu
- Screen 1 → Screen 3 ("Mở trong Nhập NSM"): `self.state.set("open_yarn", {"yarn_code": ..., "factory_code": ...})`, rồi
  `self.go_to(NsmPricingPage)`.
- Screen 3 → Screen 4 ("Khai báo tiêu hao cho nhóm này"): `self.state.set("loss_prefill", {"factory_code": ..., "group_label": yarn.loss_group_key, "technology": yarn.technology})`, rồi `self.go_to(LossGroupPage)`.
- Trang nhận `pop` giá trị đó ở đầu `render()`, và nếu cần đặt giá trị widget thì gán `st.session_state[self.key("<widget>")] = ...`
  TRƯỚC khi tạo widget.
- Import chéo trang: `from frontend.features.yarn_costing.pages.nsm_pricing_page import NsmPricingPage` (không vòng: Screen 3
  import Screen 4, Screen 1 import Screen 3; Screen 4 không import trang khác).

### 0.11 Khối chênh lệch lần tính lại - `components/recalc_diff.py` (UC-37; dùng ở Screen 5 tab "Các lần tính lại", nút "Xem chênh lệch" sau các thao tác tính lại, Screen 7)
```python
def render_recalc_diff(feature, batch_id: str, key: str) -> None:
    types = st.multiselect(
        "Loại dòng",
        list(LINE_TYPE_LABELS),
        default=[],
        format_func=lambda v: label_of(LINE_TYPE_LABELS, v),
        placeholder="Tất cả",
        key=f"{key}.types",
    )
    diff = feature.get_recalc_diff(GetRecalcDiffRequest(batch_id=batch_id, line_types=types or None))
    stat_row(
        [
            ("Dòng tăng", format_number(diff.up_count)),
            ("Dòng giảm", format_number(diff.down_count)),
            ("Không đổi", format_number(diff.unchanged_count)),
            (
                "Chênh lệch % trung bình",
                f"{format_number(pct(diff.avg_percent) if diff.avg_percent is not None else None, 2)}%",
            ),
        ]
    )
    data_table([...], column_config=..., empty_message="Không có dòng giá nào thay đổi.", key=f"{key}.table")
    download_button(diff.file, label="Xuất Excel", key=f"{key}.export")


def open_recalc_diff_dialog(feature, batch_id: str, key: str) -> None:
    @st.dialog(f"Chênh lệch lần tính lại {batch_id}", width="large")
    def _dialog() -> None:
        render_recalc_diff(feature, batch_id, key)

    _dialog()
```
Cột bảng chênh lệch (5.5): Mã dòng (`line_code`) | Tên sợi (`yarn_name`) | Loại dòng (`label_of(LINE_TYPE_LABELS, line_type)`) |
Tổng trước (`vnd(old_total)`, localized) | Tổng sau (`vnd(new_total)`, localized) | Chênh lệch (VND) (`vnd(diff_vnd)`, localized) |
Chênh lệch (%) (`pct(diff_percent)`, "%.2f%%").
Bảng các lần tính lại (UC-36, dùng ở Screen 5 và 7): Mã lần tính lại (`id`) | Xưởng | Nguyên nhân (`trigger`) | Ngày hiệu lực
(DateColumn) | Lý do | Người chạy (`run_by`) | Lúc chạy (`run_at`, DatetimeColumn) | Số mã đã tính (`yarn_count`) | Số dòng thay đổi
(`changed_line_count`) | Số mã chưa tính được (`failed_yarn_count`) - NumberColumn localized.

### 0.12 Bảng dùng chung - `components/columns.py`
- `price_line_rows(items) / PRICE_LINE_CONFIG` - mọi cột sheet `Bang gia` (5.4), theo đúng thứ tự:
  STT (số thứ tự 1..n) | Xưởng | Mã dòng | Loại dòng | Mã gốc | Tên sợi | Nhóm sợi | Chi số | Công nghệ | Nhóm tiêu hao | PE |
  Other - C3.1 | Other - C3.2 | Other - C3.3 | Viscose/other | Cotton | Nhân công | Khấu hao | Điện | Vật tư | CPQL | Tổng (VND/kg) |
  USD/kg | Tỷ giá | Loại đóng gói | Tên loại đóng gói | Ngày tính giá | Ngày hiệu lực | Trạng thái | Mã kế toán | % CK/PP |
  Lý do CK/PP | Đơn hàng.
  Field giả định của `PriceLineRowDTO`: `factory_code, line_code, line_type, yarn_code, base_code, yarn_name, yarn_group, count,
  technology, loss_group_key, blend_pe, blend_other_c31, blend_other_c32, blend_other_c33, blend_viscose_other, blend_cotton,
  labor, depreciation, electricity, materials, overhead, total_vnd, usd_per_kg, exchange_rate, packaging_code, packaging_name,
  first_priced_at, effective_date, status, accounting_code, adjustment_percent, adjustment_reason, order_ref`.
  Config: 5 khoản + Tổng + Tỷ giá `NumberColumn(format="localized")` giá trị `vnd()`; USD/kg `"%.4f"`; 6 ô tỷ lệ pha và % CK/PP
  `"%.2f%%"` giá trị `pct()` (ô không dùng = None, để trống); Chi số `NumberColumn(format="localized")`; 2 cột ngày
  `DateColumn(format="DD/MM/YYYY")`; Loại dòng / Trạng thái / Công nghệ qua dict nhãn. Cột "Mã dòng" `pinned=True`.
- `stage_cost_rows(details) / STAGE_COST_CONFIG` (4.14, cũng là sheet `Chi tiet cong doan`): STT (`sequence`) | Công đoạn | Tên công
  đoạn | NSM (kg/giờ) (localized; đóng gói trống) | Thời gian chạy máy (phút/kg) (`minutes4`, "%.4f") | Tiêu hao (`pct`, "%.2f%%") |
  Tiêu hao lũy kế (`pct`) | Định mức (VND/phút) (`rate2`, "%.2f") | Chi phí/kg (`vnd`, localized) | Nhân công | Khấu hao | Điện |
  Vật tư | CPQL (`vnd`, localized).
- `yarn_summary_rows(items) / YARN_SUMMARY_CONFIG` (UC-19): Mã | Xưởng | Tên sợi | Loại đóng gói | Trạng thái | Người tạo | Ngày tạo
  (DatetimeColumn) | Người xử lý | Ngày xử lý (DatetimeColumn) | Lý do từ chối / chưa tính được (`reject_reason` hoặc
  `"; ".join(status_reasons)`) | Tổng (VND/kg) (`vnd`, localized) | USD/kg ("%.4f"). Field giả định: `yarn_code, factory_code,
  yarn_name, packaging_code, status, requested_by, requested_at, handled_by, handled_at, reject_reason, status_reasons,
  total_vnd, usd_per_kg`.
- `history_rows(history)` (4.15, mới nhất trước): Mã dòng | Lúc thay đổi (DatetimeColumn) | Người thao tác | Nguyên nhân (`event`) |
  Lần tính lại (`batch_id`) | Ngày hiệu lực | Tổng cũ | Tổng mới | Nhân công cũ … CPQL cũ | Nhân công mới … CPQL mới (`vnd`,
  localized) | Lý do.

---

## Screen 1: `PriceListPage` (landing, không slug)
- **Title / icon:** "Bảng giá đã tính" / 💰
- **Description:** "Xem, lọc, xuất bảng giá sợi; nhập mã kế toán, tạo / xoá dòng chiết khấu - phụ phí và xem chi tiết, lịch sử giá."
- **Sketch:**
  ```
  ┌ 🔐 Người thao tác: [Nhóm▼][Mã nội bộ][Tên▼][Xác nhận]  | hoặc "Đang thao tác: ..." [Đổi người thao tác] ┐
  ├ 🔎 Bộ lọc: Xưởng▼ | Loại dòng▼▼ | Trạng thái▼▼ | Công nghệ (Tất cả|Ring|MVS) | Nhóm sợi▼ | Mã kế toán (Tất cả|Có|Chưa có)
  │            Ngày tính giá từ | đến | Từ khoá                                                              │
  │ ℹ️ Tỷ giá đang dùng: 25.000 VND/USD (từ 01/01/2026) · Hệ số thí nghiệm: 3                                 │
  │ [Tổng dòng] [Có mã kế toán] [Chưa tính được] [Chờ xưởng xem]                                           │
  ├ 📋 Bảng giá (chọn 1 dòng) - đủ 33 cột sheet Bang gia                                                     │
  │ [Xuất Excel] [Kiểm tra giá bất thường]   → (tải file) / kết quả giá bất thường                          │
  ├ 🧾 Dòng đang chọn: S4-2020 (CK1)                                                                        │
  │  tabs: Thông tin mã | Chi tiết công đoạn | Dòng giá & bản ĐCNSM | Lịch sử giá                          │
  │  Mã kế toán [____] [Lưu mã kế toán]   [Thêm CK/PP ▸ form]   [Xoá dòng CK/PP]   [Mở trong Nhập NSM]         │
  └──────────────────────────────────────────────────────────────────────────────────────────────┘
  ```
- **First load / no data:** `get_reference_data` + `list_price_lines` với bộ lọc mặc định (không lỗi khi rỗng) → ô số liệu = 0,
  bảng hiện `empty_state` "Chưa có giá nào phù hợp bộ lọc.", khối dòng chọn không hiện. Tỷ giá chưa có → dòng thông tin ghi
  "Chưa có tỷ giá."
- **Blocks:**
  1. `actor = render_actor_block(feature, self.state, reference)`; `show_flash(self.state)`.
  2. `with panel("Bộ lọc", icon="🔎"):` hai hàng `st.columns(4)`:
     - "Xưởng": `st.selectbox("Xưởng", ["Tất cả", *codes], format_func=lambda c: c if c == "Tất cả" else factory_label(c), key=self.key("f_factory"))` - mặc định Tất cả (→ `None` trong request).
       Quy ước chung cho mọi ô "Tất cả": dùng chuỗi "Tất cả" làm lựa chọn đầu (không dùng `None` trong options), đổi thành `None` khi dựng request.
     - "Loại dòng": `st.multiselect("Loại dòng", list(LINE_TYPE_LABELS), default=list(LINE_TYPE_LABELS), format_func=..., key=self.key("f_line_types"))` - mặc định tất cả.
     - "Trạng thái": `st.multiselect("Trạng thái", STATUS_ORDER, default=[], placeholder="Tất cả", format_func=..., key=self.key("f_statuses"))`.
     - "Công nghệ": `st.segmented_control("Công nghệ", ["Tất cả", *list(TECHNOLOGY_LABELS)], default="Tất cả", format_func=..., key=self.key("f_tech"))` (None → Tất cả).
     - "Nhóm sợi": `st.selectbox("Nhóm sợi", ["Tất cả", *reference.yarn_groups], key=self.key("f_group"))`.
     - "Mã kế toán": `st.segmented_control("Mã kế toán", ["Tất cả", "Có", "Chưa có"], default="Tất cả", key=self.key("f_acc"))` → `has_accounting_code = {"Có": True, "Chưa có": False}.get(v)`.
     - "Ngày tính giá từ" / "đến": `st.date_input(..., value=None, format="DD/MM/YYYY", key=self.key("f_from"/"f_to"))`.
     - "Từ khoá": `st.text_input("Từ khoá", placeholder="Mã dòng, tên sợi, mã kế toán", key=self.key("f_keyword"))`.
     - `request = ListPriceLinesRequest(factory_code=..., line_types=types or None, statuses=statuses or None, technology=..., yarn_group=..., has_accounting_code=..., priced_from=..., priced_to=..., keyword=keyword)`.
  3. `data = feature.list_price_lines(request)`.
     `st.info(f"Tỷ giá đang dùng: {format_number(data.exchange_rate)} VND/USD (từ {fmt_date(data.exchange_rate_date)}) · Hệ số thí nghiệm: {format_number(data.trial_factor, 2)}", icon="💱")`
     (nếu `data.exchange_rate is None`: "Chưa có tỷ giá. · Hệ số thí nghiệm: …").
  4. `stat_row([("Tổng dòng", total_count), ("Có mã kế toán", with_accounting_code_count), ("Chưa tính được", not_priced_count), ("Chờ xưởng xem", waiting_count)])` (định dạng `format_number`).
  5. `with panel("Bảng giá", icon="📋"):` `picked = data_table(price_line_rows(data.items), column_config=PRICE_LINE_CONFIG, selection="single", key=self.key("lines"), empty_message="Chưa có giá nào phù hợp bộ lọc.")`
     (thứ tự: backend sắp theo Xưởng, Mã gốc, Loại dòng; trang giữ nguyên thứ tự).
     Hàng nút `st.columns([1, 1, 4])`:
     - "Xuất Excel" (UC-29, không cần xác thực): `if st.button("Xuất Excel", icon="📤", key=self.key("export"))`:
       `self.state.set("price_export", feature.export_price_lines(ExportPriceLinesRequest(**request.model_dump())))`.
       Nếu `self.state.get("price_export")`: `download_button(file, label="Tải file Excel", key=self.key("export_dl"), primary=True)`.
     - "Kiểm tra giá bất thường" (UC-30): `if st.button(...)`: `self.state.set("price_anomaly", feature.check_price_anomalies(CheckPriceAnomaliesRequest(factory_code=<xưởng lọc>)))`.
       Kết quả (nếu có trong state) hiện ngay dưới bảng: `section_title("Giá bất thường", "⚠️")`,
       `stat_row([("Nhóm vi phạm", group_count), ("Cặp vi phạm", pair_count)])`, bảng anomaly (cột như Screen 7 mục 6),
       `empty_message="Không có cặp mã nào vi phạm."`; nút nhỏ "Ẩn kết quả" (`state.pop`).
  6. **Khối dòng đang chọn** (chỉ khi `picked`): `line_code = picked[0]["Mã dòng"]`;
     `detail = feature.get_yarn_detail(GetYarnDetailRequest(yarn_code=None, line_code=line_code))`;
     `line = next(l for l in detail.lines if l.line_code == line_code)`; `y = detail.yarn`.
     `with panel(f"Dòng đang chọn: {line_code}", icon="🧾"):` `st.tabs(["Thông tin mã", "Chi tiết công đoạn", "Dòng giá & bản ĐCNSM", "Lịch sử giá"])`:
     - Thông tin mã: 3 cột `st.markdown` dạng "**Nhãn:** giá trị": Mã (`y.yarn_code`), Tên sợi, Nhóm sợi, Chi số, Công nghệ, Compact
       (`yes_no(y.is_compact)`), Nhóm tiêu hao, Đóng gói, Tỷ lệ pha (`blend_text(y.blend_ratios, detail.blend_slots)`), Trạng thái,
       Khoá (`yes_no(y.is_locked)`), Sợi so sánh (`y.reference_yarn_code or "-"`), Lý do khác sợi cùng nhóm, Lý do ĐCNSM
       (nếu có), Ngày tính giá, Ngày hiệu lực. `y.status_reasons` → `st.warning` liệt kê từng lý do. Bảng NSM chỉ xem từ
       `detail.stages`: Công đoạn | Tên công đoạn | NSM (kg/giờ).
     - Chi tiết công đoạn: `data_table(stage_cost_rows(detail.stage_details), column_config=STAGE_COST_CONFIG, empty_message="Mã này chưa có chi tiết tính giá.", key=self.key("d_stages"))`.
     - Dòng giá & bản ĐCNSM: bảng `detail.lines` (Mã dòng | Loại dòng | 5 khoản | Tổng (VND/kg) | USD/kg | % CK/PP | Lý do CK/PP |
       Đơn hàng | Mã kế toán), rồi `section_title("Các bản ĐCNSM cùng mã gốc")` + `data_table(yarn_summary_rows(detail.revisions), empty_message="Chưa có bản ĐCNSM.")`.
     - Lịch sử giá: `data_table(history_rows(detail.history), empty_message="Chưa có lịch sử giá.")` (mới nhất trước - backend
       sắp; nếu không, trang sắp theo `changed_at` giảm dần).
     Dưới tabs, hàng thao tác:
     - **Mã kế toán (UC-28):** `acc = st.text_input("Mã kế toán", value=line.accounting_code or "", max_chars=100, key=self.key(f"acc.{line_code}"))` (khoá gồm mã dòng để giá trị mặc định đổi theo dòng),
       `disabled, why = action_state(self.state, "UC-28", y.factory_code)`, nút "Lưu mã kế toán" (primary, không hỏi lại) →
       `feature.set_accounting_code(SetAccountingCodeRequest(actor=actor, line_code=line_code, accounting_code=acc))` → flash
       `result.message` ("Đã lưu mã kế toán cho dòng …" / "Đã xoá mã kế toán của dòng …") → `st.rerun()`. `st.caption("Để trống rồi bấm Lưu = xoá mã kế toán.")`.
     - **Thêm CK/PP (UC-25):** `with st.expander("Thêm CK/PP", icon="➕"):` `with st.form(self.key(f"adj_form.{y.yarn_code}")):`
       "Loại" `st.radio("Loại", [<CHIET_KHAU>, <PHU_PHI>], format_func=..., horizontal=True)`;
       "% chiết khấu / phụ phí" `st.number_input(min_value=0.0, max_value=100.0, value=0.0, step=0.5, format="%.2f", help="Ví dụ 5 = 5%")`;
       "Lý do" `st.text_area(max_chars=500)`; "Đơn hàng" `st.text_input(max_chars=100, placeholder="Ví dụ: PO-2026-118")`;
       `st.form_submit_button("Lưu dòng CK/PP", type="primary", disabled=<action_state UC-25>)` →
       `feature.create_adjustment_line(CreateAdjustmentLineRequest(actor=actor, yarn_code=y.yarn_code, line_type=t, percent=from_percent(p), reason=r, order_ref=o))` → flash → rerun. Không hỏi lại.
     - **Xoá dòng CK/PP (UC-26):** chỉ hiện khi `line.line_type` là Chiết khấu / Phụ phí. Tắt (help: "Dòng <mã> đã có mã kế toán, không xoá được.")
       khi `line.accounting_code`; ngoài ra theo `action_state("UC-26", y.factory_code)`. Hộp thoại: tiêu đề "Xác nhận xoá dòng CK/PP",
       câu hỏi `f"Xoá dòng {line_code}? Lịch sử giá của dòng vẫn được giữ; số thứ tự CK/PP không dùng lại."`, nút "Xoá dòng",
       gọi `feature.delete_adjustment_line(DeleteAdjustmentLineRequest(actor=actor, line_code=line_code))`.
     - **Mở trong Nhập NSM:** `st.button("Mở trong Nhập NSM", icon="🧮")` → mục 0.10 (không cần xác thực).
- **After actions:** thông báo của UC (flash) ở đầu trang; bảng tải lại; bảng giữ khoá `self.key("lines")` nên dòng đang chọn vẫn
  được chọn (miễn thứ tự dòng không đổi).

## Screen 2: `YarnRequestPage` (`yeu-cau-tinh-gia`)
- **Title / icon:** "Yêu cầu tính giá" / 📝
- **Description:** "Sales tạo, sửa, huỷ yêu cầu tính giá sợi mới và theo dõi trạng thái."
- **Sketch:**
  ```
  ┌ 🔐 Người thao tác ─────────────────────────────────────────────────────┐
  ├ 📝 Tạo yêu cầu: Xưởng▼ | Tên sợi [CVC 30/1 (60/40) MVS] | Loại đóng gói▼            │
  │   App nhận ra: Nhóm sợi CVC · Chi số 30 · Công nghệ MVS · Compact Không · Nhóm tiêu hao CVC (60/40) MVS │
  │   ⚠️ (nếu nhóm tiêu hao chưa có / tên sai / trùng tên)            [Gửi yêu cầu]       │
  ├ 🔎 Bộ lọc: Xưởng▼ | Trạng thái▼▼ | Ngày tạo từ | đến | Từ khoá                    │
  ├ 📋 Danh sách yêu cầu (chọn 1 dòng)                                                │
  ├ ✏️ Yêu cầu S4-2020: Tên sợi [...] | Loại đóng gói▼   [Lưu sửa đổi] [Huỷ yêu cầu]     │
  └──────────────────────────────────────────────────────────────────────────┘
  ```
- **First load / no data:** chỉ `get_reference_data` + `list_yarns` (30 ngày gần nhất). Tên sợi trống → không gọi
  `analyze_yarn_name`, không hiện dòng "App nhận ra". Bảng rỗng → "Chưa có yêu cầu nào.".
- **Blocks:**
  1. Khối xác thực; `show_flash`.
  2. `with panel("Tạo yêu cầu tính giá", icon="📝"):` `st.columns([1, 3, 2])` (không dùng `st.form` vì "App nhận ra" phải cập nhật
     ngay khi gõ):
     - "Xưởng": `st.selectbox("Xưởng", codes, index=None, placeholder="Chọn xưởng", format_func=factory_label, key=self.key("new_factory"))`.
     - "Tên sợi": `st.text_input("Tên sợi", max_chars=200, placeholder="Ví dụ: CVC 30/1 (60/40) MVS", key=self.key("new_name"))`.
     - "Loại đóng gói": `st.selectbox("Loại đóng gói", options, index=None, placeholder="Chọn loại đóng gói", format_func=lambda c: f"{c} - {name}", disabled=not factory, key=self.key(f"new_pack.{factory}"))`
       với `options = [p.code for p in reference.packaging if p.factory_code == factory and p.active and <p.has_rate>]` (BR-52 - chỉ
       loại đang dùng và có định mức; field `has_rate` là giả định G3).
     - "App nhận ra" (UC-40): nếu `factory and name.strip()`:
       `a = feature.analyze_yarn_name(AnalyzeYarnNameRequest(factory_code=factory, yarn_name=name))`;
       nếu `a.valid`: `st.markdown(f"**App nhận ra:** Nhóm sợi **{a.yarn_group}** · Chi số **{format_number(a.count, 2 if a.count % 1 else 0)}** · Công nghệ **{label_of(TECHNOLOGY_LABELS, a.technology)}** · Compact **{yes_no(a.is_compact)}** · Nhóm tiêu hao **{a.loss_group_key}**")`;
       `if not a.loss_group_exists: st.warning(f"Nhóm tiêu hao '{a.loss_group_key}' chưa có ở xưởng {factory}. Yêu cầu vẫn gửi được; xưởng cần khai báo tiêu hao trước khi tính giá.", icon="⚠️")`;
       nếu `not a.valid` hoặc `a.duplicate_code`: `st.warning(a.message, icon="⚠️")` (thông báo BR-01 / BR-06 do backend soạn).
     - "Gửi yêu cầu" (UC-15, primary, không hỏi lại): `disabled = action_state("UC-15")[0] or not (factory and name.strip() and pack)` →
       `feature.create_yarn_request(CreateYarnRequestRequest(actor=actor, factory_code=factory, yarn_name=name, packaging_code=pack))`
       → flash `result.message` ("Đã gửi yêu cầu <mã> - <tên sợi> cho <xưởng>.") → `st.session_state.pop(self.key("new_name"), None)` → `st.rerun()`.
  3. `with panel("Bộ lọc", icon="🔎"):` `st.columns(5)`: "Xưởng" (Tất cả / S1 / S4), "Trạng thái" multiselect (mặc định trống = tất
     cả), "Ngày tạo từ" (mặc định `date.today() - timedelta(days=30)`), "Ngày tạo đến" (mặc định hôm nay), "Từ khoá" (placeholder
     "Mã hoặc tên sợi").
     `data = feature.list_yarns(ListYarnsRequest(factory_code=..., statuses=... or None, date_from=..., date_to=..., keyword=..., origin=<"Yêu cầu Sales">))` (G4).
  4. `with panel("Danh sách yêu cầu", icon="📋"):` `picked = data_table(yarn_summary_rows(items_newest_first), column_config=YARN_SUMMARY_CONFIG, selection="single", key=self.key("requests"), empty_message="Chưa có yêu cầu nào.")`
     (mới nhất trước: sắp theo `requested_at` giảm dần nếu backend chưa sắp).
  5. Khối sửa (chỉ khi `picked`): `code = picked[0]["Mã"]`, `item = <YarnSummaryDTO có yarn_code == code>`.
     `with panel(f"Yêu cầu {code}", icon="✏️"):`
     - Nếu trạng thái khác "Chờ xưởng xem": `st.info(f"Chỉ sửa hoặc huỷ được yêu cầu đang 'Chờ xưởng xem'. Yêu cầu {code} đang ở trạng thái '{label}'.")` và 2 nút tắt (BR-07).
     - "Tên sợi" `st.text_input(value=item.yarn_name, max_chars=200, key=self.key(f"edit_name.{code}"))`; "Loại đóng gói"
       `st.selectbox(options của xưởng item.factory_code, index=<vị trí item.packaging_code hoặc None>, key=self.key(f"edit_pack.{code}"))`.
       `st.caption("Không đổi được xưởng; muốn đổi xưởng hãy huỷ và tạo yêu cầu mới.")`.
     - "Lưu sửa đổi" (UC-16, không hỏi lại) → `update_yarn_request(UpdateYarnRequestRequest(actor=actor, yarn_code=code, yarn_name=..., packaging_code=...))` → flash → rerun.
     - "Huỷ yêu cầu" (UC-17) → hộp thoại "Xác nhận huỷ yêu cầu", câu hỏi `f"Huỷ yêu cầu {code} - {item.yarn_name}? Mã {code} sẽ không được dùng lại."`,
       nút "Huỷ yêu cầu", gọi `cancel_yarn_request(CancelYarnRequestRequest(actor=actor, yarn_code=code))`.
     - Quyền: `action_state("UC-16")`, `action_state("UC-17")`.
- **After actions:** thông báo có mã mới; yêu cầu mới ở đầu danh sách (bảng tải lại khi rerun).

## Screen 3: `NsmPricingPage` (`nhap-nsm-tinh-gia`)
- **Title / icon:** "Nhập NSM & tính giá" / 🧮
- **Description:** "Xưởng xử lý yêu cầu: nhập năng suất máy và tỷ lệ pha, kiểm tra, xem và lưu giá, tạo bản ĐCNSM hoặc từ chối."
- **Sketch:**
  ```
  ┌ 🔐 Người thao tác ─────────────────────────────────────────────────────────┐
  │ Xưởng: (S1 | S4)                                                                  │
  │ [Chờ xưởng xem][Chưa tính được][Đã tính giá][Có mã kế toán][Từ chối][Đã huỷ]        │
  ├ 🔎 Trạng thái▼▼ (mặc định Chờ xưởng xem + Chưa tính được) | Từ khoá                   │
  ├ 📋 Mã cần xử lý (chọn 1 dòng, cũ nhất trước)                                          │
  ├ 🧵 Mã đang mở: S4-2020 - CVC 30/1 (60/40) MVS  [chế độ: Sửa NSM | Tạo bản ĐCNSM]      │
  │  thông tin mã ... ⚠️ lý do chưa tính được / BR-32 nếu khoá                              │
  │  Cách nhập (Tự nhập | Tự điền) [Lấy NSM từ sợi cùng nhóm]  Sợi so sánh: S4-1988 ...    │
  │  Tỷ lệ pha (%):  [PE] [Other - C3.1] [Other - C3.2] [Other - C3.3] [Cotton]            │
  │  Bảng NSM: Công đoạn | Tên công đoạn | NSM (kg/giờ) ✎ | NSM sợi so sánh              │
  │  (Lý do khác sợi cùng nhóm)  (Lý do điều chỉnh - chế độ ĐCNSM)                          │
  │  [Kiểm tra và xem giá] [Lưu NSM và giá] [Tạo bản ĐCNSM] [Khai báo tiêu hao cho nhóm này] │
  │  Lý do từ chối [____] [Từ chối]                                                       │
  ├ 📊 Kết quả: kiểm tra khớp; bảng chi tiết công đoạn; 5 khoản; Tổng VND/kg; USD/kg; giá TN │
  └────────────────────────────────────────────────────────────────────────────┘
  ```
- **First load / no data:** `get_reference_data` + `list_yarns` (mặc định lọc) → ô số liệu = 0, bảng "Không có mã nào cần xử lý."
  (G7); khối mã đang mở không hiện (không gọi `get_yarn_detail`).
- **Blocks:**
  0. Nhận chuyển trang: `pending = self.state.pop("open_yarn")`; nếu có: `st.session_state[self.key("factory")] = pending["factory_code"]`,
     `self.state.set("nsm_open_code", pending["yarn_code"])`.
  1. Khối xác thực; `show_flash`.
  2. "Xưởng": `factory = st.segmented_control("Xưởng", codes, default=<xưởng của actor nếu XS1/XS4, ngược lại codes[0]>, required=True, format_func=factory_label, key=self.key("factory"))`.
  3. `data = feature.list_yarns(ListYarnsRequest(factory_code=factory, statuses=statuses or None, keyword=keyword))`
     (bộ lọc ở bước 4 đọc trước bằng widget đặt trong panel - thứ tự hiển thị: ô số liệu rồi bộ lọc; dùng `st.container()` giữ chỗ
     cho `stat_row` rồi điền sau).
     `stat_row([(label_of(STATUS_LABELS, s), format_number(data.status_counts.get(str(s), 0))) for s in STATUS_ORDER])` - số lượng mỗi
     trạng thái của xưởng chọn (G5).
  4. `with panel("Bộ lọc", icon="🔎"):` "Trạng thái" `st.multiselect(STATUS_ORDER, default=[<CHO_XUONG_XEM>, <CHUA_TINH_DUOC>], format_func=..., key=self.key(f"statuses.{factory}"))`; "Từ khoá".
  5. `with panel("Mã cần xử lý", icon="📋"):` bảng `yarn_summary_rows` sắp theo `requested_at` tăng dần (cũ nhất trước) với cột: Mã |
     Tên sợi | Loại đóng gói | Trạng thái | Người tạo | Ngày tạo | Lý do từ chối / chưa tính được | Tổng (VND/kg);
     `picked = data_table(..., selection="single", key=self.key(f"yarns.{factory}"), empty_message="Không có mã nào cần xử lý.")`.
     Mã mở: `code = picked[0]["Mã"] if picked else self.state.get("nsm_open_code")`; nếu `picked`: `self.state.set("nsm_open_code", code)`.
     Không có `code` → dừng (return).
  6. `detail = feature.get_yarn_detail(GetYarnDetailRequest(yarn_code=code, line_code=None))`; `y = detail.yarn`. Nếu
     `y.factory_code != factory` → `self.state.pop("nsm_open_code")`, return.
     Trạng thái form (trong `self.state`, theo mã): `mode = self.state.get(f"mode.{code}", "edit")` ("edit" | "revision"),
     `ver = self.state.get(f"ver.{code}", 0)` (tăng khi cần làm mới bảng/ô nhập), `prefill = self.state.get(f"prefill.{code}")`
     (kết quả UC-20), `result = self.state.get(f"result.{code}")` (kết quả kiểm tra gần nhất).
  7. `with panel(f"Mã đang mở: {y.yarn_code} - {y.yarn_name}", icon="🧵"):`
     - Thông tin mã (3 cột): Tên sợi, Nhóm sợi, Chi số, Công nghệ, Nhóm tiêu hao, Đóng gói, Trạng thái, Khoá (`yes_no(y.is_locked)`);
       `y.status_reasons` → `st.warning("\n".join(f"- {r}" for r in y.status_reasons))` (lý do chưa tính được).
     - Nút "Đóng mã" (tertiary) → `self.state.pop("nsm_open_code")`, rerun.
     - Trạng thái cuối (Đã huỷ / Từ chối): `st.info(f"Mã {y.yarn_code} ở trạng thái '{label}' - không nhập NSM được.")`, không hiện form, return.
     - Mã khoá (`y.is_locked`) và `mode == "edit"`: `st.warning(f"Mã {y.yarn_code} đã có mã kế toán nên không sửa được. Muốn điều chỉnh NSM, hãy tạo bản ĐCNSM.")` (BR-32).
     - Chế độ ĐCNSM: `st.info(f"Đang tạo bản ĐCNSM từ {y.yarn_code}. Bản gốc giữ nguyên.")` + nút "Quay lại sửa bản đang mở" (tertiary → `mode="edit"`, xoá `result`).
     - **Cách nhập:** `nsm_mode = st.segmented_control("Cách nhập", [<TU_NHAP>, <TU_DIEN>], default=<TU_NHAP>, required=True, format_func=..., key=self.key(f"nsm_mode.{code}"))`
       (mặc định Tự nhập theo Screen 3). Khi Tự điền: nút "Lấy NSM từ sợi cùng nhóm" (UC-20; quyền `action_state("UC-20", factory)`) →
       `s = feature.suggest_nsm(SuggestNsmRequest(yarn_code=code))`; nếu `s.found`: `self.state.set(f"prefill.{code}", s.model_dump())`, `ver += 1`, flash `s.message` (nếu trống: `f"Đã điền NSM từ {s.reference_yarn_code} - {s.reference_yarn_name}."`), rerun;
       nếu không: `st.warning(s.message)` ("Chưa có sợi cùng nhóm để tự điền. Vui lòng nhập NSM.") - form giữ nguyên.
       Khi có prefill: `st.caption(f"Sợi so sánh: {s.reference_yarn_code} - {s.reference_yarn_name} (chi số {s.reference_count})")`.
     - **Tỷ lệ pha (%):** `cols = st.columns(len(detail.blend_slots))`; mỗi ô
       `cols[i].number_input(f"{slot} (%)", min_value=0.0, max_value=100.0, step=1.0, format="%.2f", value=pct(<prefill.blend_ratios hoặc y.blend_ratios>.get(slot, 0)) or 0.0, key=self.key(f"blend.{code}.{mode}.{ver}.{slot}"))`.
     - **Bảng NSM sửa trong ô:** rows từ `detail.stages` (đã lọc theo BR-13 ở backend, không có F):
       `{"Công đoạn": st.stage_code, "Tên công đoạn": st.stage_name, "NSM (kg/giờ)": float(<prefill.nsm.get(code) nếu có prefill, ngược lại st.nsm> or 0), "NSM sợi so sánh": float(<prefill.nsm.get(...) nếu có prefill, ngược lại st.reference_nsm>) or None}`;
       `rows = editable_table(rows, key=self.key(f"nsm_grid.{code}.{mode}.{ver}"), columns=["Công đoạn", "Tên công đoạn", "NSM (kg/giờ)", "NSM sợi so sánh"], disabled=["Công đoạn", "Tên công đoạn", "NSM sợi so sánh"], column_config={"NSM (kg/giờ)": NumberColumn("NSM (kg/giờ)", min_value=0.0, step=0.1, format="localized"), "NSM sợi so sánh": NumberColumn(format="localized")})`.
       `st.caption("Để trống hoặc 0 = sợi không chạy công đoạn đó. Công đoạn đóng gói F luôn được tính theo loại đóng gói.")`.
     - **Lý do khác sợi cùng nhóm:** hiện khi `result and result.warning_stages` hoặc `y.nsm_warning_reason`:
       `st.text_area("Lý do khác sợi cùng nhóm", value=y.nsm_warning_reason or "", max_chars=500, key=self.key(f"warn_reason.{code}.{mode}"))`.
     - **Lý do điều chỉnh** (chỉ chế độ ĐCNSM): `st.text_area("Lý do điều chỉnh", max_chars=500, key=self.key(f"adjust_reason.{code}"))`.
     - Dựng dữ liệu gửi: `blend = {slot: from_percent(v)}`, `nsm = {r["Công đoạn"]: to_decimal(r["NSM (kg/giờ)"]) for r in rows}`,
       `ref_code = prefill["reference_yarn_code"] if prefill else y.reference_yarn_code`.
     - **Nút (chế độ edit):** method theo trạng thái (giả định mục 10 của tài liệu): "Chờ xưởng xem" / "Chưa tính được" →
       `save_yarn_nsm` (UC-21, `SaveYarnNsmRequest`); "Đã tính giá" → `correct_yarn_nsm` (UC-23, `CorrectYarnNsmRequest`, cùng field).
       `req(save) = <Request>(actor=actor, yarn_code=code, blend_ratios=blend, nsm=nsm, nsm_mode=nsm_mode, reference_yarn_code=ref_code, nsm_warning_reason=warn_reason, save=save)`.
       Quyền: `action_state("UC-21" | "UC-23", factory)`; thêm tắt khi `y.is_locked` (help = thông báo BR-32).
       - "Kiểm tra và xem giá" → `self.state.set(f"result.{code}", feature.<method>(req(False)))`, rerun (hiện khối kết quả).
       - "Lưu NSM và giá" (primary, không hỏi lại) → `r = feature.<method>(req(True))`; nếu `r.saved`: flash `r.message`
         ("Đã lưu giá …" hoặc "Đã lưu NSM … nhưng chưa tính được giá: …"), lưu `result`, `ver` giữ nguyên, rerun; nếu `not r.saved`
         (cần lý do BR-38): lưu `result`, `st.warning(r.message)` (không rerun).
       - "Tạo bản ĐCNSM" (UC-24, hiện khi `detail.lines` không rỗng - bản đã có giá, bất kể khoá; quyền `action_state("UC-24", factory)`)
         → `self.state.set(f"mode.{code}", "revision")`, xoá `result`, rerun (form chép sẵn tên, đóng gói, tỷ lệ pha, NSM của bản đang mở).
       - "Khai báo tiêu hao cho nhóm này": hiện khi mã thiếu nhóm tiêu hao - `a = feature.analyze_yarn_name(AnalyzeYarnNameRequest(factory_code=factory, yarn_name=y.yarn_name))` và `not a.loss_group_exists`
         → mục 0.10 (`loss_prefill`) → `self.go_to(LossGroupPage)`.
     - **Nút (chế độ revision):** `rev(save) = CreateNsmRevisionRequest(actor=actor, source_yarn_code=code, adjust_reason=adjust_reason, blend_ratios=blend, nsm=nsm, nsm_warning_reason=warn_reason, save=save)`;
       quyền `action_state("UC-24", factory)` (không xét khoá).
       - "Kiểm tra và xem giá" → `create_nsm_revision(rev(False))` → lưu `result`.
       - "Lưu bản ĐCNSM" (primary, không hỏi lại) → `r = create_nsm_revision(rev(True))`; nếu `r.saved`: flash `r.message`
         ("Đã tạo bản <mã ĐCNSM>: <tổng> VND/kg."), `self.state.set("nsm_open_code", r.yarn.yarn_code)`, `mode.{code}` = "edit", rerun
         (mở luôn bản mới); không saved → như trên.
     - **Từ chối (UC-18):** chỉ khi trạng thái "Chờ xưởng xem": `reason = st.text_input("Lý do từ chối", max_chars=500, key=self.key(f"reject_reason.{code}"))`;
       nút "Từ chối" tắt khi `not reason.strip()` hoặc `action_state("UC-18", factory)` → hộp thoại "Xác nhận từ chối yêu cầu",
       câu hỏi `f"Từ chối yêu cầu {code} - {y.yarn_name}? Sales sẽ thấy lý do bạn nhập."`, nút "Từ chối",
       gọi `reject_yarn_request(RejectYarnRequestRequest(actor=actor, yarn_code=code, reason=reason))`.
  8. **Khối kết quả** (khi `result`): `with panel("Kết quả tính giá", icon="📊"):`
     - Kiểm tra khớp: `result.check_passed` → `st.success("Kiểm tra khớp: đạt.")`; ngược lại `st.warning("Kiểm tra khớp: chưa đạt.\n" + "\n".join(f"- {x}" for x in result.reasons))`.
     - `result.warning_stages` → `st.warning(f"NSM khác sợi cùng nhóm ({result.reference_yarn_code}) ở công đoạn: {', '.join(result.warning_stages)}. Vui lòng nhập lý do trước khi lưu.")` (BR-38).
     - `data_table(stage_cost_rows(result.stage_details), column_config=STAGE_COST_CONFIG, empty_message="Chưa có chi tiết tính giá.", key=self.key(f"res_stages.{code}"))`.
     - Nếu `result.line`: `stat_row([("Nhân công", …), ("Khấu hao", …), ("Điện", …), ("Vật tư", …), ("CPQL", …)])` (VND/kg, `format_number(vnd(x))`);
       `stat_row([("Tổng (VND/kg)", format_number(vnd(line.total_vnd))), ("USD/kg", format_number(usd(line.usd_per_kg), 4)), ("Giá thí nghiệm (VND/kg)", format_number(vnd(result.trial_line.total_vnd)) if result.trial_line else "-")])`.
       `st.caption("Kết quả hiển thị đã làm tròn; Tổng được cộng từ các số chưa làm tròn.")`.
- **After actions:** thông báo của UC; mã chuyển trạng thái trong danh sách (bảng tải lại); khối kết quả vẫn hiện kết quả vừa tính.

## Screen 4: `LossGroupPage` (`tieu-hao`)
- **Title / icon:** "Tiêu hao" / 📉
- **Description:** "Tra cứu, khai báo, sửa và xoá nhóm tiêu hao sơ cấp, sợi pha của từng xưởng."
- **Sketch:**
  ```
  ┌ 🔐 Người thao tác ──────────────────────────────────────────────────────┐
  ├ 🔎 Xưởng (S1|S4) | Loại▼ | Từ khoá | [ ] Chỉ nhóm đang khoá                       │
  ├ 📋 Nhóm tiêu hao (chọn 1 dòng): Nhóm | Nguyên liệu | Công nghệ | Loại | Thành phần | C1 (%) ... | Đang khoá | Số mã │
  │ [Thêm nhóm sơ cấp] [Thêm nhóm sợi pha]                                        │
  ├ ➕ Form thêm (sơ cấp: bảng tiêu hao | sợi pha: bảng thành phần + [Xem tiêu hao tính ra]) [Lưu nhóm] │
  ├ ✏️ Nhóm đang chọn: ⚠️ Nhóm đang khoá ... | bảng tiêu hao / thành phần | Ngày hiệu lực | Lý do │
  │   Mã đang dùng nhóm | [Lưu thay đổi] [Xoá nhóm]                                  │
  └────────────────────────────────────────────────────────────────────────┘
  ```
- **First load / no data:** `get_reference_data` + `list_loss_groups` → bảng "Chưa có nhóm tiêu hao nào."; hai nút thêm vẫn hiện
  (tắt khi chưa xác thực).
- **Blocks:**
  0. `prefill = self.state.pop("loss_prefill")`; nếu có: `st.session_state[self.key("factory")] = prefill["factory_code"]`,
     `self.state.set("loss_form", "new_secondary")`, `self.state.set("loss_prefill_data", prefill)`.
  1. Khối xác thực; `show_flash`.
  2. `with panel("Bộ lọc", icon="🔎"):` "Xưởng" segmented (S1/S4, required, mặc định xưởng của actor hoặc codes[0], `key=self.key("factory")`);
     "Loại" `st.selectbox(["Tất cả", *LEVEL_LABELS], format_func=lambda v: v if v == "Tất cả" else label_of(LEVEL_LABELS, v))` (→ `None` khi "Tất cả");
     "Từ khoá"; `st.toggle("Chỉ nhóm đang khoá", value=False)`.
     `data = feature.list_loss_groups(ListLossGroupsRequest(factory_code=factory, level=level, keyword=keyword, locked_only=locked_only))`;
     `all_groups = feature.list_loss_groups(ListLossGroupsRequest(factory_code=factory))` (danh sách chọn thành phần, không lọc).
  3. `with panel("Nhóm tiêu hao", icon="📋"):` rows: Nhóm (`group_key`) | Nguyên liệu | Công nghệ | Loại | Thành phần
     (`"; ".join(f"{c.component_group_key} {format_number(pct(c.ratio), 2)}%")`) | một cột cho mỗi `data.stage_codes`: `f"{s} (%)"` = `pct(g.losses.get(s))`
     (`"%.2f%%"`) | Đang khoá (`yes_no`) | Số mã đang dùng (`len(g.used_by_codes)`).
     `picked = data_table(rows, column_config=..., selection="single", key=self.key(f"groups.{factory}"), empty_message="Chưa có nhóm tiêu hao nào.")`.
     Hàng nút: "Thêm nhóm sơ cấp" (`action_state("UC-11", factory)`) → `self.state.set("loss_form", "new_primary")`; "Thêm nhóm sợi pha"
     (`action_state("UC-12", factory)`) → `"new_secondary"`; không gọi backend, chỉ mở form (rerun).
  4. **Form thêm nhóm sơ cấp** (`loss_form == "new_primary"`): `with panel("Thêm nhóm sơ cấp", icon="➕"):`
     "Nhóm sợi" `text_input(max_chars=200, placeholder="Ví dụ: PE NORMAL - RING")`; "Nguyên liệu" `text_input(max_chars=200)`;
     "Công nghệ" `segmented_control([<RING>, <MVS>], default=<RING>, required=True)`;
     bảng tiêu hao sửa trong ô: `editable_table([{"Công đoạn": s, "Tiêu hao (%)": 0.0} for s in data.stage_codes], key=self.key(f"new_primary_losses.{factory}"), disabled=["Công đoạn"], column_config={"Tiêu hao (%)": NumberColumn(min_value=0.0, max_value=100.0, step=0.01, format="%.2f")})`;
     nút "Lưu nhóm" (primary, không hỏi lại) → `create_primary_loss_group(CreatePrimaryLossGroupRequest(actor=actor, factory_code=factory, yarn_group_label=..., material=..., technology=..., losses={r["Công đoạn"]: from_percent(r["Tiêu hao (%)"])}))`
     → flash `result.message` ("Đã thêm nhóm tiêu hao '…'. Đã tính lại N mã đang chờ tiêu hao.") → `self.state.pop("loss_form")` → rerun.
     Nút "Đóng" (tertiary) → pop `loss_form`.
  5. **Form thêm nhóm sợi pha** (`loss_form == "new_secondary"`): `with panel("Thêm nhóm sợi pha", icon="➕"):`
     "Nhóm sợi" (mặc định `loss_prefill_data["group_label"]` nếu có), "Nguyên liệu", "Công nghệ" (mặc định từ prefill);
     bảng thành phần sửa trong ô: `editable_table([], key=self.key(f"new_components.{factory}"), columns=["Nhóm thành phần", "Tỷ lệ (%)"], allow_add_delete=True, column_config={"Nhóm thành phần": SelectboxColumn(options=[g.group_key for g in all_groups.items], required=True), "Tỷ lệ (%)": NumberColumn(min_value=0.0, max_value=100.0, step=0.01, format="%.2f")})`
     (`st.caption("Từ 1 đến 5 thành phần, tổng tỷ lệ 100%.")`); `components = [ComponentRowDTO(component_group_key=r["Nhóm thành phần"], ratio=from_percent(r["Tỷ lệ (%)"])) for r in rows if r["Nhóm thành phần"]]`.
     - "Xem tiêu hao tính ra" (UC-12 xem trước) → `p = create_secondary_loss_group(CreateSecondaryLossGroupRequest(..., components=components, save=False))`
       → `self.state.set(f"secondary_preview.{factory}", p.group)` → bảng chỉ xem "Tiêu hao tính ra": Công đoạn | Tiêu hao (%) (`pct(p.group.losses[s])`).
     - "Lưu nhóm" (primary, không hỏi lại) → `save=True` → flash `result.message` → pop form, prefill và preview → rerun.
     - Nút "Đóng".
  6. **Nhóm đang chọn** (khi `picked` và không mở form thêm): `g = <LossGroupDTO có group_key == picked[0]["Nhóm"]>`.
     `with panel(f"Nhóm: {g.group_key}", icon="✏️"):`
     - `g.is_locked` → `st.warning(f"Nhóm đang khoá: đang được dùng cho sợi đã có mã kế toán ({', '.join(g.locked_codes[:5])}). Chỉ Phòng SO được sửa.")`.
     - "Nguyên liệu" (value `g.material`), "Công nghệ" (default `g.technology`) - khoá widget gồm `g.group_key`.
     - Sơ cấp / Nhập từ file: bảng tiêu hao sửa trong ô `[{"Công đoạn": s, "Tiêu hao (%)": pct(g.losses.get(s, 0))} for s in data.stage_codes]`, `disabled=["Công đoạn"]`.
       Với "Nhập từ file": thêm `st.toggle("Khai báo thành phần (chuyển thành nhóm sợi pha)", key=...)`; bật → hiện bảng thành phần (như 5) thay cho bảng tiêu hao.
     - Thứ cấp: bảng thành phần sửa trong ô (rows từ `g.components`, `allow_add_delete=True`, options = mọi nhóm trừ chính nó) + bảng
       "Tiêu hao tính ra" chỉ xem từ `g.losses`.
     - "Ngày hiệu lực" `date_input(value=date.today(), format="DD/MM/YYYY")`; "Lý do" `text_area(max_chars=500)` (bắt buộc - backend kiểm).
     - "Mã đang dùng nhóm": `data_table([{"Mã sợi": c, "Đã có mã kế toán": yes_no(c in g.locked_codes)} for c in g.used_by_codes], empty_message="Chưa có mã sợi nào dùng nhóm này.")`.
     - "Lưu thay đổi" (UC-13): quyền `action_state("UC-13", factory)`; thêm: nếu `g.is_locked` và nhóm actor không phải SO → tắt, help =
       thông báo BR-24 `f"Nhóm tiêu hao '{g.group_key}' đang được dùng cho sợi đã có mã kế toán ({…5 mã}). Chỉ Phòng SO được sửa."`.
       Hộp thoại "Xác nhận sửa nhóm tiêu hao", câu hỏi `f"Lưu thay đổi nhóm '{g.group_key}'? App sẽ tính lại mọi mã đang dùng nhóm này và các nhóm sợi pha dùng nó ({len(g.used_by_codes)} mã dùng trực tiếp)."`,
       nút "Lưu và tính lại", gọi `update_loss_group(UpdateLossGroupRequest(actor=actor, factory_code=factory, group_key=g.group_key, material=..., technology=..., losses=<dict hoặc None>, components=<list hoặc None>, reason=reason, effective_date=eff))`
       (gửi `losses` với Sơ cấp / Nhập từ file; gửi `components` (và `losses=None`) với Thứ cấp hoặc khi bật công tắc khai báo thành phần).
     - "Xoá nhóm" (UC-14, `action_state("UC-14", factory)`) → hộp thoại "Xác nhận xoá nhóm tiêu hao", câu hỏi
       `f"Xoá nhóm '{g.group_key}'? Chỉ xoá được nhóm không có mã sợi nào dùng và không là thành phần của nhóm khác."`, nút "Xoá nhóm",
       gọi `delete_loss_group(DeleteLossGroupRequest(actor=actor, factory_code=factory, group_key=g.group_key))`.
- **After actions:** thông báo của UC kèm số mã đã tính lại (flash); bảng tải lại.

## Screen 5: `MasterDataPage` (`du-lieu-nen`)
- **Title / icon:** "Dữ liệu nền & định mức" / ⚙️
- **Description:** "Phòng SO quản lý cấu hình công đoạn, định mức chi phí/phút, đóng gói, hồi phế, quy trình, tỷ giá, hệ số thí nghiệm và xem các lần tính lại."
- **Sketch:**
  ```
  ┌ 🔐 Người thao tác ──────────────────────────────────────────────────────┐
  │ Xưởng: (S1 | S4)                                   [Xem chênh lệch] (sau khi tính lại) │
  │ tabs: Công đoạn | Định mức | Đóng gói | Hồi phế | Quy trình | Tỷ giá & hệ số TN | Các lần tính lại │
  │  [bảng sửa trong ô, thêm/xoá dòng]                                               │
  │  Ngày hiệu lực [dd/mm/yyyy]  Lý do [__________]   [Lưu … và tính lại]            │
  └────────────────────────────────────────────────────────────────────────┘
  ```
- **First load / no data:** `get_reference_data(None)` + `get_reference_data(factory)` + `list_recalc_batches(factory)`; bảng dữ liệu nền có
  dữ liệu khởi tạo (4.4.1/4.4.2) hoặc rỗng (bảng sửa trong ô vẫn hiện tiêu đề cột nhờ `columns=`); không có định mức → bảng định mức
  điền sẵn mã (mỗi công đoạn trừ F + mỗi loại đóng gói đang hoạt động) với 0; không có tỷ giá → "Chưa có tỷ giá.".
- **Chung cho trang:**
  - Khối xác thực; `show_flash`. Mọi nút thay đổi dữ liệu: `action_state(self.state, "UC-0x")` (chỉ Phòng SO).
  - "Xưởng": segmented S1/S4 (required, mặc định codes[0], `key=self.key("factory")`); `ref = feature.get_reference_data(GetReferenceDataRequest(factory_code=factory))`.
  - Sau một thao tác có tính lại thành công: `self.state.set("last_batch_id", result.batch.id)` (nếu `result.batch`); đầu trang hiện
    `st.button("Xem chênh lệch", icon="🔍")` → `open_recalc_diff_dialog(feature, batch_id, self.key("last_diff"))` (UC-37) và nút "Ẩn".
  - Khối ngày hiệu lực + lý do (dùng lại, mỗi tab một bộ khoá):
    `eff = st.date_input("Ngày hiệu lực", value=date.today(), format="DD/MM/YYYY", key=self.key(f"{tab}.eff.{factory}"))`,
    `reason = st.text_input("Lý do", max_chars=500, key=self.key(f"{tab}.reason.{factory}"))`.
  - Mọi nút "… và tính lại" → hộp thoại (mục 0.8), câu hỏi chung:
    `f"<Việc> {factory} và tính lại toàn bộ giá của xưởng với ngày hiệu lực {fmt_date(eff)}? Mọi mã (kể cả mã đã có mã kế toán) sẽ được tính lại."`.
    Sau khi xong: flash `result.message` ("… Đã tính lại N mã, M mã chưa tính được."), lưu `last_batch_id`, rerun.
  - Khoá bảng sửa trong ô gồm xưởng: `self.key(f"<tab>_grid.{factory}")`.
- **Tab "Công đoạn" (UC-03):** `editable_table(rows, allow_add_delete=True, columns=[…])`, cột theo 4.4:
  Thứ tự (`sequence`, `NumberColumn(min_value=1, step=1, format="%d", required=True)`) | Mã công đoạn (`TextColumn(max_chars=20, required=True)`) |
  Tên công đoạn (`TextColumn(max_chars=100)`) | Nhóm công đoạn (`TextColumn(max_chars=20)`) | Đóng gói (`CheckboxColumn`) |
  Hồi phế (`SelectboxColumn(options=["Không","Chải thô","Thô","Con"])`) | Ô tỷ lệ pha (`SelectboxColumn(options=["Không", *factory.blend_slots])`) |
  Công đoạn ghép (`CheckboxColumn`) | Cách tính thứ cấp (`SelectboxColumn(options=["Bình quân","Cộng thẳng"])`) |
  Công đoạn cộng lũy kế (`MultiselectColumn(options=[mã công đoạn của xưởng])`) | NSM đổi theo chi số (`CheckboxColumn`) |
  Nguồn định mức (`SelectboxColumn(options=["Chính công đoạn","Loại đóng gói"])`).
  Map ngược nhãn → enum và tên cột → field `StageRowDTO` (`sequence, stage_code, stage_name, stage_group, is_packaging, recovery_type, blend_slot, is_merge_stage, secondary_method, cumulative_stages, varies_with_count, rate_code_source` - giả định).
  Ngày hiệu lực + Lý do; nút "Lưu cấu hình và tính lại" → hộp thoại "Xác nhận lưu cấu hình công đoạn", nút xác nhận "Lưu và tính lại",
  gọi `save_stage_config(SaveStageConfigRequest(actor=actor, factory_code=factory, rows=[StageRowDTO(...)], effective_date=eff, reason=reason))`.
- **Tab "Định mức" (UC-04):** `st.caption(f"Phiên bản đang dùng: {cur.id} · hiệu lực {fmt_date(cur.effective_date)} · áp dụng bởi {cur.created_by} lúc {format_datetime(cur.created_at)} · Lý do: {cur.reason}")` (hoặc "Chưa có định mức.").
  `editable_table(rows, allow_add_delete=True)`, cột 4.5.1: Mã định mức (`rate_code`, TextColumn required) | Nhân công | Khấu hao | Điện | Vật tư | CPQL
  (`NumberColumn(min_value=0.0, step=0.0001, format="%.4f")`, đơn vị VND/phút) | Tổng (VND/phút) (`total_rate`, chỉ xem, `"%.2f"`,
  tính bởi backend - không cập nhật khi đang sửa) | Ghi chú (`TextColumn(max_chars=200)`).
  Ngày hiệu lực + Lý do; nút "Áp dụng định mức và tính lại toàn bộ" → hộp thoại "Xác nhận áp dụng định mức mới", nút "Áp dụng và tính lại",
  gọi `apply_rate_version(ApplyRateVersionRequest(actor, factory_code, rows=[RateLineRowDTO(...)], effective_date, reason))`.
  Dưới bảng: `section_title("Các phiên bản định mức")` + `data_table(ref.rate_versions → Mã phiên bản | Ngày hiệu lực | Lý do | Người áp dụng | Lúc áp dụng | Số dòng, selection="single", key=…, empty_message="Chưa có phiên bản định mức nào.")`;
  chọn một phiên bản → bảng chỉ xem các dòng của phiên bản đó (cùng cột như trên).
- **Tab "Đóng gói" (UC-05):** `editable_table(allow_add_delete=True)`: Mã loại (`code`, TextColumn required, max 20) | Tên loại đóng gói (`name`, max 200) |
  Khối lượng (kg) (`weight_kg`, localized) | Số công (`man_days`, "%.4f") | Phút/kg (`minutes_per_kg`, "%.4f", required) | Đang dùng (`active`, CheckboxColumn, mặc định True) |
  Có định mức (chỉ xem, nếu DTO có - G3). Ngày hiệu lực + Lý do; nút "Lưu đóng gói và tính lại" → hộp thoại "Xác nhận lưu loại đóng gói",
  nút "Lưu và tính lại", gọi `save_packaging_types(SavePackagingTypesRequest(...))`.
  `st.caption("Loại đóng gói mới cần có định mức chi phí/phút (thẻ Định mức) trước khi Sales chọn được.")`.
- **Tab "Hồi phế" (UC-06):** `editable_table` 3 dòng cố định: Loại hồi phế (chỉ xem: Chải thô / Thô / Con) | Tỷ lệ (%) (`pct(rate)`,
  `NumberColumn(min_value=0.0, max_value=100.0, step=0.01, format="%.2f")`). Ngày hiệu lực + Lý do; nút "Lưu hồi phế và tính lại" →
  hộp thoại "Xác nhận lưu hồi phế", nút "Lưu và tính lại", gọi `save_recovery_rates(SaveRecoveryRatesRequest(..., rows=[RecoveryRowDTO(recovery_type=…, rate=from_percent(…))]))`.
- **Tab "Quy trình" (UC-07):** `editable_table(allow_add_delete=True)`: Nhóm sợi (`yarn_group`, required) | Công nghệ (`SelectboxColumn(["Ring","MVS"], required=True)`) |
  Số thành phần (`component_count`, `NumberColumn(min_value=1, max_value=5, step=1, format="%d")`) | Quy trình (`route_text`, TextColumn max 500,
  ví dụ "B2 - C1 - C2 - SBD - PD - LF - CM - MD1 - MD2 - MD3 - R - S - W - F") | Công đoạn nhận ra (`", ".join(route_stages)`, chỉ xem - backend tính, BR-13).
  Không có ngày / lý do. Nút "Lưu quy trình" (primary, không hỏi lại) → `save_process_routes(SaveProcessRoutesRequest(actor, factory_code, rows))` → flash → rerun.
- **Tab "Tỷ giá & hệ số TN" (UC-08, UC-09)** - dùng chung S1 và S4 (`st.caption("Tỷ giá và hệ số thí nghiệm dùng chung cho S1 và S4.")`):
  - `with panel("Tỷ giá", icon="💱"):` `st.info(f"Tỷ giá đang dùng: {format_number(cur.rate)} VND/USD từ {fmt_date(cur.effective_date)}")` (hoặc "Chưa có tỷ giá.");
    `data_table(reference.exchange_rates → Ngày áp dụng | Tỷ giá (localized) | Ghi chú | Người nhập | Lúc nhập, empty_message="Chưa có tỷ giá nào.")`;
    `with st.form(self.key("rate_form")):` "Ngày áp dụng" (`date_input`, hôm nay), "Tỷ giá (VND/USD)" (`number_input(min_value=0.0, value=float(cur.rate) if cur else 0.0, step=100.0, format="%.2f")`),
    "Ghi chú" (max 200), `form_submit_button("Thêm tỷ giá", type="primary", disabled=<UC-08>)` → `add_exchange_rate(AddExchangeRateRequest(actor, effective_date, rate=to_decimal(x), note))` → flash → rerun (không hỏi lại).
  - `with panel("Hệ số thí nghiệm", icon="🧪"):` "Hệ số thí nghiệm" (`number_input(min_value=0.0, value=float(reference.trial_factor), step=0.1, format="%.2f")`), Ngày hiệu lực, Lý do;
    nút "Lưu hệ số" → hộp thoại "Xác nhận đổi hệ số thí nghiệm", câu hỏi `f"Đổi hệ số thí nghiệm từ {cũ} thành {mới}? App sẽ cập nhật dòng thí nghiệm của mọi mã ở cả hai xưởng (kể cả mã đã có mã kế toán)."`,
    nút "Lưu hệ số", gọi `update_trial_factor(UpdateTrialFactorRequest(actor, trial_factor=to_decimal(x), effective_date, reason))`.
- **Tab "Các lần tính lại" (UC-36, UC-37):** `batches = feature.list_recalc_batches(ListRecalcBatchesRequest(factory_code=factory))`;
  `data_table(<bảng lần tính lại mục 0.11>, selection="single", key=self.key(f"batches.{factory}"), empty_message="Chưa có lần tính lại nào.")`;
  chọn một dòng → `render_recalc_diff(feature, batch_id, self.key(f"diff.{batch_id}"))` (bảng chênh lệch + "Xuất Excel").
- **After actions:** thông báo kèm số mã đã tính lại; nút "Xem chênh lệch" → UC-37.

## Screen 6: `ExcelImportPage` (`nhap-du-lieu-excel`)
- **Title / icon:** "Nhập dữ liệu từ Excel" / 📥
- **Description:** "Tải file mẫu, chuyển dữ liệu cũ từ file Excel, cập nhật hàng loạt NSM và tiêu hao, đối chiếu giá cũ với giá app."
- **Sketch:**
  ```
  ┌ 🔐 Người thao tác ──────────────────────────────────────────────────────┐
  ├ ⚙️ Xưởng (S1|S4) | Loại tải (Chuyển dữ liệu ban đầu | Cập nhật hàng loạt) | Ngày chốt | [Tải file mẫu] │
  ├ 📤 Ô tải file (.xlsx .xlsm .xls)  [Kiểm tra file]                                │
  ├ 📊 [Dòng hợp lệ][Bị loại][Số sheet]  bảng từng sheet  bảng dòng bị loại [x] Chỉ hiện dòng lỗi │
  │   [Lưu N dòng hợp lệ] [Tải kết quả nhập file]                                     │
  ├ 🗂️ Các lần nhập (chọn 1 dòng)                                                     │
  ├ ⚖️ Đối chiếu giá cũ: [Khớp][Lệch][Chưa tính được] [x] Chỉ hiện mã lệch trên 1 VND/kg  bảng  [Xuất Excel] │
  └────────────────────────────────────────────────────────────────────────┘
  ```
- **First load / no data:** `get_reference_data` + `list_import_batches` → chưa có file: nút "Kiểm tra file" tắt, không có khối kết quả;
  bảng lần nhập "Chưa có lần nhập file nào."; không có khối đối chiếu.
- **Blocks:**
  1. Khối xác thực; `show_flash`.
  2. `with panel("Chọn dữ liệu", icon="⚙️"):` `st.columns([1, 2, 1, 1], vertical_alignment="bottom")`:
     "Xưởng" (segmented S1/S4, required, mặc định xưởng của actor hoặc codes[0]); "Loại tải"
     `st.radio("Loại tải", [<CHUYEN_DU_LIEU_BAN_DAU>, <CAP_NHAT_HANG_LOAT>], index=1, horizontal=True, format_func=...)` (mặc định Cập nhật
     hàng loạt - G8); "Ngày chốt" (`date_input(value=date.today(), format="DD/MM/YYYY")`); nút "Tải file mẫu" (UC-33, không cần xác thực)
     → `self.state.set(f"template.{factory}", feature.download_template(DownloadTemplateRequest(factory_code=factory)))` → khi có trong state:
     `download_button(file, label="Tải file mẫu về máy", key=self.key(f"template_dl.{factory}"))`.
     Nếu nhóm actor không phải SO: `st.caption("Xưởng chỉ được 'Cập nhật hàng loạt' sheet '1. Input NSM' và '2. Input tieu hao' của xưởng mình; các sheet khác sẽ bị bỏ qua.")` (BR-45),
     và loại "Chuyển dữ liệu ban đầu" làm nút "Kiểm tra file" tắt với help "Sheet … chỉ Phòng SO được cập nhật" → dùng câu: "Chuyển dữ liệu ban đầu chỉ Phòng SO được thực hiện." (G9).
  3. `with panel("Tải file", icon="📤"):` `file = file_upload("File Excel", types=[".xlsx", ".xlsm", ".xls"], key=self.key("file"), help="Tối đa 60 MB, mỗi sheet tối đa 10.000 dòng.")`;
     nút "Kiểm tra file" (UC-34 xem trước; `action_state("UC-34", factory)`; tắt khi `file is None`) →
     `preview = feature.import_workbook(ImportWorkbookRequest(actor=actor, factory_code=factory, mode=mode, cutoff_date=cutoff, file=file, commit=False))`
     → `self.state.set("import_preview", {"sig": (file.filename, len(file.content), factory, str(mode), cutoff.isoformat()), "result": preview})`.
     Kết quả xem trước chỉ hiện khi `sig` khớp với file / lựa chọn hiện tại (đổi file hoặc lựa chọn → phải kiểm tra lại).
  4. **Khối kết quả** (`with panel("Kết quả kiểm tra file", icon="📊"):`):
     - `st.info(preview.message)` nếu có.
     - `stat_row([("Dòng hợp lệ", valid_count), ("Dòng bị loại", len(rejected_rows)), ("Sheet đã đọc", len(sheets))])`.
     - Bảng từng sheet: Sheet | Đọc | Tạo | Cập nhật | Bị loại (NumberColumn localized) | Ghi chú (`skipped_message`, ví dụ "Sheet '…' chỉ Phòng SO được cập nhật, đã bỏ qua.").
     - Bảng dòng bị loại: `only_errors = st.toggle("Chỉ hiện dòng lỗi", value=True)`; rows = mỗi `RejectedRowDTO` → Sheet | Dòng (`excel_row`) | Mã / nhóm (`key`) | Lý do;
       khi tắt công tắc: thêm các dòng thông báo cấp sheet (sheet có `skipped_message`, cột Dòng trống) - G10.
       `empty_message="Không có dòng nào bị loại."`.
     - "Tải kết quả nhập file": nếu `result_file`: `download_button(result_file, label="Tải kết quả nhập file", key=...)`.
     - `f"Lưu {preview.valid_count} dòng hợp lệ"` (primary; tắt khi `valid_count == 0` hoặc không có quyền) → hộp thoại "Xác nhận lưu dữ liệu từ file",
       câu hỏi `f"Lưu {n} dòng hợp lệ từ file {file.filename}? App sẽ lưu dữ liệu cho xưởng {factory} và tính lại toàn bộ giá của xưởng với ngày hiệu lực {fmt_date(cutoff)}."`,
       nút "Lưu dữ liệu", gọi `r = import_workbook(ImportWorkbookRequest(..., commit=True))`; thành công → `self.state.set("import_committed", r)`, `self.state.pop("import_preview")`,
       nếu `r.import_id`: `self.state.set("selected_import_id", r.import_id)`; flash `r.message` ("Đã nhập file …: tạo X, cập nhật Y, bị loại Z dòng. Đã tính giá N mã, M mã chưa tính được."); rerun.
     - Sau khi lưu (state `import_committed`): hiện bảng sheet + "Tải kết quả nhập file" của lần lưu, và nút "Đối chiếu giá cũ" → chọn lần nhập đó (khối 6).
  5. `with panel("Các lần nhập", icon="🗂️"):` `batches = feature.list_import_batches(ListImportBatchesRequest(factory_code=factory))`;
     bảng: Mã lần nhập | Xưởng | Loại | Ngày chốt (DateColumn) | Tên file | Người nhập | Lúc nhập (DatetimeColumn) | Tạo | Cập nhật | Bị loại;
     `picked = data_table(..., selection="single", key=self.key(f"imports.{factory}"), empty_message="Chưa có lần nhập file nào.")`.
     `import_id = picked[0]["Mã lần nhập"] if picked else self.state.get("selected_import_id")`.
  6. **Đối chiếu giá cũ (UC-35)** (khi có `import_id`): `with panel(f"Đối chiếu giá cũ - {import_id}", icon="⚖️"):`
     `only = st.toggle("Chỉ hiện mã lệch trên 1 VND/kg", value=False, key=...)`;
     `cmp = feature.get_legacy_comparison(GetLegacyComparisonRequest(import_id=import_id, only_mismatch=only))`;
     `stat_row([("Mã khớp", matched_count), ("Mã lệch", mismatched_count), ("Mã chưa tính được", not_priced_count)])`;
     bảng: Mã | Tên sợi | Tổng cũ | Tổng app | Chênh lệch (VND) (`vnd`, localized) | Chênh lệch (%) (`"%.2f%%"`, None → trống = "-") | Nhân công cũ … CPQL cũ |
     Nhân công mới … CPQL mới | Trạng thái; `empty_message="Lần nhập này không có giá cũ để đối chiếu."` (G7);
     `download_button(cmp.file, label="Xuất Excel", key=self.key(f"cmp_dl.{import_id}"))`.
- **After actions:** thông báo UC-34; lần nhập mới ở đầu danh sách (backend sắp mới nhất trước) và được chọn sẵn cho đối chiếu.

## Screen 7: `DashboardPage` (`dashboard`)
- **Title / icon:** "Dashboard kiểm soát" / 📊
- **Description:** "Theo dõi hiệu quả báo giá, khả năng đáp ứng, chênh lệch lần tính lại, sai lệch giá và NSM bất thường."
- **Không có khối xác thực** (không có thao tác thay đổi dữ liệu).
- **Sketch:**
  ```
  ┌ 🔎 Xưởng (Cả hai | S1 | S4) | Từ ngày | Đến ngày                                            ┐
  │ [Sợi báo giá][Sợi có đơn hàng (x%)][Yêu cầu mới][Khả năng đáp ứng %][Đang chờ xưởng xem]          │
  │ ▇ Yêu cầu mới theo tuần (cột)          ╱ Khả năng đáp ứng theo tuần (đường)                      │
  │ Số dòng giá theo trạng thái: [Chờ xưởng xem][Chưa tính được][Đã tính giá][Có mã kế toán]...       │
  │ 🔁 Lần tính lại gần nhất: TL-S4-005 ... [Dòng tăng][Dòng giảm][Chênh lệch % TB] [Xem chi tiết]    │
  │ ⚠️ Sai lệch giá: [Nhóm vi phạm][Cặp vi phạm] bảng                                              │
  │ 🧪 NSM bất thường: bảng                                                                    │
  └───────────────────────────────────────────────────────────────────────────┘
  ```
- **First load / no data:** bộ lọc mặc định (Cả hai; ngày 1 tháng hiện tại → hôm nay) → `get_dashboard`, `check_price_anomalies`,
  `check_nsm_anomalies` (chỉ đọc, G6) → ô số liệu 0 / "-", thay biểu đồ bằng `empty_state("Không có dữ liệu trong khoảng ngày đã chọn.")`, các bảng rỗng.
- **Blocks:**
  1. `with panel("Bộ lọc", icon="🔎"):` "Xưởng" `st.segmented_control("Xưởng", ["Cả hai", *codes], default="Cả hai", key=...)`
     → `factory = None if v in (None, "Cả hai") else v` (bỏ chọn cũng = Cả hai); "Từ ngày" `date_input(value=date.today().replace(day=1), format="DD/MM/YYYY")`; "Đến ngày" `date_input(value=date.today())`.
     Nếu `date_from > date_to`: `st.warning("Từ ngày phải trước hoặc bằng Đến ngày.")` và dừng (không gọi backend).
  2. `d = feature.get_dashboard(GetDashboardRequest(factory_code=factory, date_from=date_from, date_to=date_to))`.
     `stat_row([("Sợi báo giá", format_number(d.quoted_count)), ("Sợi có đơn hàng", f"{format_number(d.ordered_count)} ({_pct_text(d.ordered_ratio)})"), ("Yêu cầu mới", format_number(d.new_request_count)), ("Khả năng đáp ứng", _pct_text(d.fulfilment_ratio)), ("Đang chờ xưởng xem", format_number(d.waiting_count))])`
     với `_pct_text(x) = "-" if x is None else f"{format_number(pct(x), 2)}%"` (G11: tỷ lệ trả về dạng phân số).
  3. Biểu đồ (chỉ ở Screen 7): nếu `d.weekly` rỗng hoặc mọi `new_requests == 0` và `d.quoted_count == 0` → `empty_state("Không có dữ liệu trong khoảng ngày đã chọn.")`;
     ngược lại `frame = pd.DataFrame([{"Tuần": fmt_date(w.week_start), "Yêu cầu mới": w.new_requests, "Khả năng đáp ứng (%)": pct(w.fulfilment_ratio)} for w in d.weekly])`;
     `left, right = st.columns(2)`; `left.markdown("**Yêu cầu mới theo tuần**")` + `left.bar_chart(frame, x="Tuần", y="Yêu cầu mới", x_label="Tuần", y_label="Số yêu cầu")`;
     `right.markdown("**Khả năng đáp ứng theo tuần**")` + `right.line_chart(frame, x="Tuần", y="Khả năng đáp ứng (%)", x_label="Tuần", y_label="%")`.
     (Nhãn tuần dạng "dd/mm/yyyy" của ngày đầu tuần; `sort=False` không cần vì bar_chart sắp theo x chuỗi - dùng nhãn `yyyy-mm-dd` nếu thứ tự sai; G12.)
  4. `section_title("Số dòng giá theo trạng thái")` + `stat_row([(label_of(STATUS_LABELS, s), format_number(d.status_counts.get(str(s), 0))) for s in STATUS_ORDER if s not in (<DA_HUY>, <TU_CHOI>)])`.
  5. `with panel("Lần tính lại gần nhất", icon="🔁"):` nếu `d.last_batch`: `st.caption(f"{b.id} · {b.trigger} · hiệu lực {fmt_date(b.effective_date)} · {b.run_by} lúc {format_datetime(b.run_at)}")`;
     `stat_row([("Dòng tăng", d.last_batch_up), ("Dòng giảm", d.last_batch_down), ("Chênh lệch % trung bình", _pct_text(d.last_batch_avg_percent))])`;
     nút "Xem chi tiết" → `open_recalc_diff_dialog(feature, b.id, self.key("dash_diff"))` (UC-37). Không có → `empty_state("Không có lần tính lại nào trong khoảng ngày đã chọn.")`.
  6. `with panel("Sai lệch giá", icon="⚠️"):` `pa = feature.check_price_anomalies(CheckPriceAnomaliesRequest(factory_code=factory))`;
     `stat_row([("Nhóm vi phạm", pa.group_count), ("Cặp vi phạm", pa.pair_count)])`; bảng (UC-30): Công nghệ | Nhóm sợi | Nhóm tiêu hao |
     Mã trước | Chi số trước | Giá trước (`vnd`, localized) | Mã sau | Chi số sau | Giá sau | Lý do sai; `empty_message="Không có cặp mã nào vi phạm."`.
  7. `with panel("NSM bất thường", icon="🧪"):` `na = feature.check_nsm_anomalies(CheckNsmAnomaliesRequest(factory_code=factory))`; bảng (UC-31):
     Công nghệ | Nhóm tiêu hao | Công đoạn | Giá trị phổ biến | Mã khác biệt | NSM của mã | Lý do đã ghi; `empty_message="Không có NSM bất thường."`.

## Screen 8: `UserAuditPage` (`nguoi-dung-nhat-ky`)
- **Title / icon:** "Người dùng & nhật ký" / 👥
- **Description:** "Phòng SO khai báo nhóm người dùng, mã nội bộ và thành viên; mọi người xem nhật ký thay đổi."
- **Sketch:**
  ```
  ┌ 🔐 Người thao tác ───────────────────────────────────────────────────┐
  ├ 👥 Nhóm người dùng (chọn 1 dòng): Mã nhóm | Tên nhóm | Xưởng | Đang hoạt động | Số thành viên │
  ├ ✏️ Nhóm Xưởng S4: Tên nhóm | Mã nội bộ mới (để trống = giữ mã cũ) | [x] Còn hoạt động        │
  │   Thành viên (sửa trong ô, thêm/xoá dòng): Tên | Còn hoạt động          [Lưu nhóm]         │
  ├ 📜 Nhật ký: Từ ngày | Đến ngày | Nhóm▼ | Từ khoá   bảng                                    │
  └─────────────────────────────────────────────────────────────────────┘
  ```
- **First load / no data:** `get_reference_data` (5 nhóm) + `list_audit_log` (30 ngày gần nhất) → bảng nhật ký "Chưa có nhật ký nào." (G7).
- **Blocks:**
  1. Khối xác thực; `show_flash`.
  2. `with panel("Nhóm người dùng", icon="👥"):` bảng từ `reference.groups`: Mã nhóm (`code`) | Tên nhóm | Xưởng (`factory_code or "-"`) | Đang hoạt động (`yes_no`) |
     Số thành viên (`len(g.members)`); mã nội bộ KHÔNG hiển thị. `picked = data_table(..., selection="single", key=self.key("groups"), empty_message="Chưa có nhóm người dùng.")`.
  3. Khối sửa (khi `picked`): `g = <nhóm có code == picked[0]["Mã nhóm"]>`; `with panel(f"Nhóm {g.name}", icon="✏️"):`
     "Tên nhóm" (`text_input(value=g.name, max_chars=100, key=self.key(f"g_name.{g.code}"))`); "Mã nội bộ mới"
     (`text_input(type="password", placeholder="Để trống = giữ mã cũ", max_chars=20, key=...)`, `st.caption("Mã nội bộ dài từ 4 đến 20 ký tự.")`);
     "Còn hoạt động" (`st.toggle(value=g.active)`);
     "Thành viên": `editable_table([{"Tên": m.name, "Còn hoạt động": m.active} for m in g.members], key=self.key(f"members.{g.code}"), columns=["Tên", "Còn hoạt động"], allow_add_delete=True, column_config={"Tên": TextColumn(max_chars=100, required=True), "Còn hoạt động": CheckboxColumn(default=True)})`;
     nút "Lưu nhóm" (UC-01, `action_state("UC-01")`, không hỏi lại) →
     `save_user_group(SaveUserGroupRequest(actor=actor, group_code=g.code, name=name, new_access_code=new_code.strip() or None, active=active, members=[GroupMemberRowDTO(name=r["Tên"], active=bool(r["Còn hoạt động"]) if r["Còn hoạt động"] is not None else True) for r in rows if r["Tên"]]))`
     → flash `result.message` ("Đã lưu nhóm <tên nhóm>."); nếu đã đổi mã nội bộ của CHÍNH nhóm người đang thao tác → `clear_actor(self.state)` và
     flash thêm câu "Mã nội bộ nhóm của bạn đã đổi, vui lòng xác thực lại." → rerun.
  4. `with panel("Nhật ký thay đổi", icon="📜"):` `st.columns(4)`: "Từ ngày" (mặc định hôm nay - 30 ngày), "Đến ngày" (hôm nay), "Nhóm"
     (`selectbox(["Tất cả", *codes], format_func=lambda c: c if c == "Tất cả" else <tên nhóm>)`, → `None` khi "Tất cả"), "Từ khoá";
     `log = feature.list_audit_log(ListAuditLogRequest(date_from=..., date_to=..., group_code=..., keyword=...))`;
     bảng (UC-02, mới nhất trước): Lúc (`at`, DatetimeColumn) | Nhóm | Người | Thao tác | Đối tượng | Nội dung | Lý do;
     `data_table(..., empty_message="Chưa có nhật ký nào.", key=self.key("audit"))`.

---

## Thứ tự trang trong manifest (= menu)
`pages=(PriceListPage, YarnRequestPage, NsmPricingPage, LossGroupPage, MasterDataPage, ExcelImportPage, DashboardPage, UserAuditPage)`
Tệp trang: `pages/price_list_page.py`, `yarn_request_page.py`, `nsm_pricing_page.py`, `loss_group_page.py`, `master_data_page.py`,
`excel_import_page.py`, `dashboard_page.py`, `user_audit_page.py`. Xoá `pages/main_page.py` (trang scaffold dùng `ping`).
Components: `components/actor_block.py`, `permissions.py`, `flash.py`, `display.py`, `labels.py`, `columns.py`, `recalc_diff.py`.

## Đối chiếu mục 8 (mọi phần tử đều có)
| Mục 8 | Nơi thiết kế |
|---|---|
| Menu 8 mục đúng thứ tự | Thứ tự trang trong manifest |
| Xác thực 1 lần / phiên, "Đổi người thao tác", Screen 1-6, 8 | 0.6; khối 1 mỗi trang (Screen 7 không có) |
| Nút không có quyền bị tắt kèm chú thích (BR-47, BR-48) | 0.7 |
| Bảng danh sách chỉ xem + chọn 1 dòng → khối chi tiết bên dưới | `data_table(selection="single")` ở Screen 1-6, 8 |
| Ô số liệu Screen 1, 3, 6, 7; biểu đồ chỉ Screen 7 | `stat_row` các trang đó; `bar_chart` / `line_chart` Screen 7 |
| Hộp thoại xác nhận (danh sách mục 8) | 0.8 + từng nút: Huỷ yêu cầu (S2), Từ chối (S3), Xoá nhóm / Lưu thay đổi (S4), Xoá dòng CK/PP (S1), mọi "… và tính lại" + "Lưu hệ số" (S5), "Lưu N dòng hợp lệ" (S6) |
| Không hỏi lại (Gửi yêu cầu, Lưu sửa đổi, Lưu NSM và giá, Lưu bản ĐCNSM, Lưu dòng CK/PP, Lưu mã kế toán, Lưu nhóm tiêu hao mới, Lưu quy trình, Thêm tỷ giá, Lưu nhóm người dùng) | nút trực tiếp, mẫu 0.5 |
| Screen 1 đủ mọi cột sheet Bang gia | 0.12 `price_line_rows` |
| Screen 3 bảng NSM sửa trong ô + NSM sợi so sánh chỉ xem; chế độ ĐCNSM | Screen 3 khối 7 |
| Screen 4 bảng tiêu hao / thành phần sửa trong ô, tiêu hao tính ra chỉ xem | Screen 4 khối 4-6 |
| Screen 5 tabs + bảng sửa trong ô + ngày hiệu lực + lý do; Quy trình không ngày/lý do; phiên bản định mức; tỷ giá chỉ xem + form; các lần tính lại → chênh lệch + Xuất Excel | Screen 5 |
| Screen 6 công tắc "Chỉ hiện dòng lỗi", "Chỉ hiện mã lệch trên 1 VND/kg" | Screen 6 khối 4, 6 |
| Screen 8 bảng thành viên sửa trong ô, mã nội bộ mới để trống = giữ | Screen 8 khối 3 |
| Khung nhật ký cuối trang | `BasePage` (show_log_panel = True) |

## Giả định khi thiết kế (UI-build đối chiếu với backend thật)
- G1: Tên field phụ của các DTO (mục 0.12, `StageRowDTO`, `RateLineRowDTO`, `PackagingRowDTO`, `RecoveryRowDTO`, `ProcessRouteRowDTO`,
  `LossGroupDTO`, `YarnDTO`, `PriceHistoryDTO`, `RecalcDiffRowDTO`, `LegacyComparisonRowDTO`, `PriceAnomalyDTO`, `NsmAnomalyDTO`, `ImportBatchDTO`,
  `AuditLogDTO`) và tên member enum là giả định; nhãn hiển thị giữ nguyên.
- G2: `UserGroupDTO` có `code, name, factory_code, active, members: list[GroupMemberRowDTO{name, active}]` (khối xác thực chỉ lấy thành viên
  đang hoạt động; Screen 8 cần cả thành viên đã tắt). Nếu DTO chỉ có `member_names`, khối xác thực dùng `member_names`; Screen 8 báo lead
  thiếu danh sách thành viên đầy đủ.
- G3: `PackagingRowDTO` có cờ cho biết đã có định mức (`has_rate`); nếu không có, Screen 2 lọc theo `active` và backend chặn bằng BR-12/BR-52.
- G4: Screen 2 lọc `origin` = "Yêu cầu Sales" (chỉ hiện yêu cầu của Sales, không hiện bản ĐCNSM / nhập từ file).
- G5: `YarnListResponse.status_counts` đếm theo mọi trạng thái của xưởng lọc (không phụ thuộc bộ lọc trạng thái), khoá = giá trị enum dạng chuỗi.
- G6: `get_dashboard`, `check_price_anomalies`, `check_nsm_anomalies` là báo cáo chỉ đọc, không lỗi khi chưa có dữ liệu → được gọi khi tải
  Screen 7 (tài liệu chốt các bảng hiện thẳng, không có nút). Nếu một hàm vẫn ném lỗi khi rỗng, UI-build bọc `try/except AppError` và hiện `empty_state`.
- G7: Câu rỗng không có trong tài liệu, tự đặt: "Không có mã nào cần xử lý.", "Không có cặp mã nào vi phạm.", "Không có NSM bất thường.",
  "Lần nhập này không có giá cũ để đối chiếu.", "Chưa có nhật ký nào.", "Không có dòng nào bị loại.", "Chưa có lần tính lại nào." và
  câu cảnh báo nhóm tiêu hao chưa có ở Screen 2.
- G8: Screen 6 mặc định "Cập nhật hàng loạt" (an toàn hơn; tài liệu không nêu mặc định). Screen 5, 6 mặc định xưởng đầu tiên / xưởng của nhóm.
- G9: Nhóm Xưởng chọn "Chuyển dữ liệu ban đầu" → nút "Kiểm tra file" tắt kèm chú thích (BR-45); backend vẫn kiểm tra.
- G10: Công tắc "Chỉ hiện dòng lỗi" (bật mặc định) chỉ hiện dòng Excel bị loại; tắt thì hiện thêm thông báo cấp sheet (sheet bị bỏ qua).
- G11: Mọi tỷ lệ trả về là phân số (0.75 = 75%) như hợp đồng; trang nhân 100 chỉ để hiển thị, chia 100 khi gửi ô "%".
- G12: Biểu đồ theo tuần dùng nhãn ngày đầu tuần; nếu thứ tự trục sai, dùng nhãn `yyyy-mm-dd`.
- G13: Screen 3 sắp "cũ nhất trước", Screen 2 "mới nhất trước" theo `requested_at` ngay tại trang nếu backend trả thứ tự khác (chỉ sắp xếp hiển thị).
- G14: "Tạo bản ĐCNSM" hiện khi bản đang mở đã có dòng giá (`detail.lines` không rỗng); "Khai báo tiêu hao cho nhóm này" hiện khi
  `analyze_yarn_name(...).loss_group_exists` là False.
- G15: UC-21 cho mã "Chờ xưởng xem" / "Chưa tính được", UC-23 cho mã "Đã tính giá" (theo giả định triển khai mục 10); mã "Có mã kế toán"
  chỉ được tạo ĐCNSM.
- G16: "Lịch sử giá" trong khối dòng chọn hiện `detail.history` (mọi dòng của bản NSM, có cột Mã dòng); nếu backend đã lọc theo dòng thì giữ nguyên.

## 7. Bổ sung 2026-09-29 (app mới)
- **Menu trái** (`manifest.py`): thứ tự PriceListPage → DashboardPage → YarnRequestPage → NsmPricingPage → LossGroupPage →
  MasterDataPage → ExcelImportPage → UserAuditPage; tiêu đề trang có nhãn nhóm: "[Chung] Bảng giá đã tính", "[Chung] Dashboard
  kiểm soát", "[Sales] Yêu cầu tính giá", "[Xưởng] Nhập NSM & tính giá", "[Xưởng] Tiêu hao", "[SO] Dữ liệu nền & định mức",
  "[SO] Nhập dữ liệu từ Excel", "[SO] Người dùng & nhật ký"; group "Tính Giá Sợi".
- **Menu theo nhóm người dùng** (`components/group_menu.py::render_group_menu(page, reference)`), gọi ngay sau
  `get_reference_data` ở đầu mọi trang: `st.expander("📂 Menu theo nhóm người dùng", expanded=False)` chứa 5
  `st.expander` lồng (Streamlit 1.64 cho phép): 🌐 Dùng chung, 🛒 Sales, 🏭 Xưởng sợi, 🗂️ Phòng SO, 🧾 Kế toán; nhóm có màn đang
  mở `expanded=True`; mỗi dòng `self.link_to(Page, label=..., icon=...)`, màn đang mở là chữ đậm "(đang mở)". Sau khối:
  `st.warning` cho mỗi `reference.data_warnings` (BR-61).
- **Screen 2**: dưới "App nhận ra": `feature.check_request_submit(CheckRequestSubmitRequest(group_code, factory_code))`;
  `st.columns([1, 4])`: nút "Gửi yêu cầu" (tắt khi `not allowed` hoặc thiếu xưởng / tên / đóng gói) | `st.caption("🔒 <lý do>")`
  cho mỗi lý do BR-63.
- **Screen 5 thẻ Đóng gói**: caption "Ngày hiệu lực và lý do chỉ bắt buộc khi…"; nút "Lưu đóng gói" → `save_packaging_types(
  preview=True)` (lỗi → `show_error`) → `confirm_dialog("Xác nhận lưu loại đóng gói", "Lưu loại đóng gói của xưởng <X>?
  <confirm_text>", "Lưu và tính lại" | "Lưu đóng gói")` → `save_packaging_types(preview=False)` → thông báo UC-05.
