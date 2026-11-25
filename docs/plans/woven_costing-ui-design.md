# UI design: woven_costing (Tính giá vải dệt), đợt 1

Nguồn: `docs/business/woven_costing.md` (mục 4-9, nhất là mục 8 "Giao diện đã chốt"), `docs/plans/woven_costing-implementation-plan.md`
mục 4 (Controller contract + bảng Pages). Streamlit đã cài: **1.64.0** (kết quả kiểm tra ở mục 0.10). Không thêm thư viện,
không HTML/CSS, không biểu đồ (UI concept: "Không có biểu đồ").

**Lưu ý cho UI-build:** backend được viết song song theo cùng hợp đồng. Tên method, request, response lấy đúng hợp đồng.
Các field phụ (tên field bên trong DTO, tên thành viên enum) là **đề xuất** của bản thiết kế này, liệt kê đầy đủ ở mục 9
"Fields the UI expects from the backend". PHẢI đọc `backend/features/woven_costing/dto/*.py` thật và sửa cho khớp; nhãn
tiếng Việt trên màn hình giữ đúng tài liệu nghiệp vụ.

## 0. Quy ước chung

### 0.1 Import chuẩn (mỗi trang chỉ import cái nó dùng)
```python
from datetime import date, timedelta
from decimal import Decimal

import streamlit as st

from backend.core.base import EmptyRequest            # nếu backend export ở đây; nếu không: dto của feature
from backend.core.exceptions import AppError
from backend.core.gateway import gateway
from backend.features.woven_costing import WovenCostingController
from backend.features.woven_costing.dto.common_dto import RoleCode, ROLE_LABELS, CostsheetStatus, CostsheetAction, ...
from backend.features.woven_costing.dto.costsheet_dto import (
    CostsheetActionRequest, CostsheetInputRequest, CostsheetResponse, CreateCostsheetRequest, GetCostsheetRequest,
    SaveOcRequest, UpdateFabricOverrideRequest, AddCustomerRequest, PrintLabelRequest, LabelInputDTO, ...
)
from backend.features.woven_costing.dto.list_dto import ListCostsheetsRequest, CostsheetListResponse, MyTasksResponse
from backend.features.woven_costing.dto.fabric_dto import PreviewFabricImportRequest, SaveFabricRequest, SearchFabricsRequest, FabricYarnDTO
from backend.features.woven_costing.dto.master_dto import (
    SaveExchangeRateRequest, SaveNormSetRequest, ViewNormSetRequest, SaveParameterSetRequest, SaveFabricFactorRequest,
    SaveHolidayRequest, CustomerImportRequest, UpdateCustomerRequest, ListCustomersRequest, ...
)
from frontend.core.base_page import BasePage
from frontend.core.components import (
    data_table, download_button, editable_table, empty_state, file_upload, panel, section_title, show_error, show_success, stat_row,
)
from frontend.core.formatting import format_currency, format_datetime, format_number
```

### 0.2 Thành phần riêng của feature (`frontend/features/woven_costing/components/`, hàm thường, không class)
| File | Hàm | Việc |
|---|---|---|
| `flash.py` | `set_flash(state, message, warnings=())`, `show_flash(state)` | Thông báo thành công sống qua lần `st.rerun()` sau thao tác: `show_success(message)` + mỗi cảnh báo 1 `st.warning(...)`. Gọi `show_flash(self.state)` ĐẦU mỗi `render()` |
| `errors.py` | `show_error_list(exc: AppError)` | `st.error(exc.message, icon="⚠️")`; nếu `exc.details` là list/tuple -> mỗi mục 1 dòng `st.markdown("- " + item)` (mục 8: "lỗi hiện thành danh sách, mỗi lỗi 1 dòng"); dict -> mỗi giá trị 1 dòng |
| `dialogs.py` | `confirm_dialog(state, key, title, question, confirm_label, action, reason_label=None, on_done=None)` | Hộp thoại xác nhận (mục 0.6) |
| `roles.py` | `my_roles(feature_key) -> set[str] \| None`, `has_any(feature_key, *codes) -> bool` | Đọc `self.current_user.roles_in("woven_costing")`; `None` (chưa đăng nhập / test) hoặc `is_admin` -> coi như mọi vai trò. **Chỉ để ẩn/tắt nút**, backend quyết định |
| `labels.py` | `STATUS_COLORS`, `STATUS_ICONS`, `status_badge(status)`, `pct_text(x)`, `vnd(x)`, `usd(x)`, `to_pct(x)`, `from_pct(x)`, `dec(x)` | Hiển thị: tỷ lệ 0..1 <-> % (x100), số VN, badge trạng thái |
| `navigation.py` | `open_costsheet(page, costsheet_id)`, `new_costsheet(page)` | Ghi state chung rồi `page.go_to(CostsheetPage)` (mục 0.5). File này import `CostsheetPage`; trang 1 và 3 import file này -> không vòng import |
| `seed.py` | `seed(key, value)` | `st.session_state.setdefault(key, value)` trước khi vẽ widget, rồi vẽ widget KHÔNG truyền `value=`/`index=` (tránh cảnh báo "default value + Session State API") |
| `multi_upload.py` | `multi_file_upload(label, types, key, max_files=4) -> list[UploadedFileDTO]` | `st.file_uploader(..., accept_multiple_files=True)` -> list `UploadedFileDTO(filename, content=f.getvalue(), mime_type=f.type)`; quá 4 file -> `st.warning("Chỉ chọn tối đa 4 file.")` và trả 4 file đầu |
| `costsheet_form.py` | các hàm vẽ khối A..H của Screen 2 và `build_input_request(...)` | Mục 2 |
| `fabric_form.py` | `fabric_dialog(...)` | Hộp thoại Thêm / Sửa mã vải (Screen 4) |
| `label_dialog.py` | `label_dialog(feature, tcfnos, key)` | Hộp thoại In nhãn (Screen 2 và 4) |

### 0.3 Badge trạng thái costsheet
Trạng thái là enum `CostsheetStatus` (giá trị = chữ tiếng Việt của 4.11). Màu (dùng ở `st.badge` và ở cột bảng):

| Trạng thái | color | icon |
|---|---|---|
| Nháp | `gray` | `:material/edit_note:` |
| Chờ duyệt | `orange` | `:material/hourglass_top:` |
| Trả lại | `red` | `:material/undo:` |
| Đã duyệt | `green` | `:material/check:` |
| Đã chốt đơn | `blue` | `:material/verified:` |
| Hủy | `gray` | `:material/block:` |
| Đã thay thế | `violet` | `:material/history:` |

Trong bảng chỉ xem (Screen 1, 3, lịch sử phiên bản), cột Trạng thái là **nhãn màu** dùng
`st.column_config.MultiselectColumn("Trạng thái", options=[...7 trạng thái...], color=[...7 màu theo thứ tự...])`; giá trị
ô là list 1 phần tử `[row.status.value]`. (MultiselectColumn có `color=` trong 1.64.0 - đã kiểm tra.) Nếu khi chạy thực tế
màu không hiện ở `st.dataframe`, đổi sang `TextColumn` với chữ có emoji đầu (`"🟢 Đã duyệt"`) - ghi `Giả định (triển khai)`.

### 0.4 Định dạng số trong bảng
- Tiền VND: `st.column_config.NumberColumn(label, format="localized")` (giá trị làm tròn đồng ở backend hoặc `round(x)`).
- USD: `NumberColumn(label, format="%.4f")`.
- Tỷ lệ (0..1 trong DTO): bảng hiển thị **đã nhân 100**, nhãn có "(%)", `NumberColumn(format="%.2f")`; khi gửi lại backend
  chia 100 (`from_pct`). Đây chỉ là đổi đơn vị hiển thị, không phải tính toán nghiệp vụ.
- Ngày: `DateColumn(label, format="DD/MM/YYYY")`; ngày giờ: `DatetimeColumn(label, format="DD/MM/YYYY HH:mm")`.
- `st.date_input(..., format="DD/MM/YYYY")` cho mọi ô ngày.
- Ngoài bảng: `format_number(x, 0)`, `format_number(x, 2)`, `format_currency(x)`.
- "Ô tô màu cho người duyệt" (không có CSS): trong bảng dùng cột cờ `"⚑"` (TextColumn hẹp, giá trị `"🟠"` hoặc `""`)
  và ngoài bảng dùng `:orange[...]` / `:orange-badge[Đã sửa]` / `:red-badge[Dưới ngưỡng]`.

### 0.5 State dùng chung giữa các trang (namespaced `self.state`, feature `woven_costing`)
| Khóa | Kiểu | Ai ghi | Ý nghĩa |
|---|---|---|---|
| `cs.open_id` | `str \| None` | Screen 1, 3, Screen 2 | id phiếu (phiên bản) đang mở trên Screen 2 |
| `cs.working` | `CostsheetResponse \| None` | Screen 2 | "bản đang làm": response cuối cùng nhận được (get / calculate / save / thao tác). Mọi widget của Screen 2 được gieo từ đây |
| `cs.rev` | `int` | Screen 2 | tăng 1 mỗi lần `cs.working` được thay -> mọi key widget của Screen 2 có hậu tố `.{id}.{rev}` nên được gieo lại |
| `cs.dirty` | `bool` | Screen 2 | `True` sau "Tính lại" (đã tính nhưng chưa lưu) |
| `cs.pending_customer` | `str \| None` | hộp thoại Thêm khách hàng | tên KH mới, áp vào ô Khách hàng ở lần chạy sau, trước khi ô được vẽ |
| `flash`, `flash_warnings` | `str`, `list[str]` | mọi trang | thông báo sau thao tác (`flash.py`) |

`navigation.open_costsheet(page, cid)`: `state.set("cs.open_id", cid)`, `state.pop("cs.working")`, `state.set("cs.dirty", False)`,
`page.go_to(CostsheetPage)`. `navigation.new_costsheet(page)`: `open_id=None`, pop working, `go_to(CostsheetPage)`.

### 0.6 Hộp thoại xác nhận (`components/dialogs.py`)
UI concept: hỏi lại trước **Gửi duyệt, Duyệt, Trả lại, Chốt đơn, Hủy, Lưu dữ liệu vải, Lưu bộ định mức**; KHÔNG hỏi lại với
Lưu nháp, Tính lại (và các thao tác khác).
```python
def confirm_dialog(state, key, title, question, confirm_label, action, reason_label=None, on_done=None) -> None:
    user = get_current_user()  # hộp thoại tự chạy lại riêng -> giữ tài khoản (bài học yarn_costing 2026-11-13)

    @st.dialog(title, width="medium")
    def _dialog() -> None:
        set_current_user(user)
        st.write(question)
        reason = st.text_area(reason_label, max_chars=500, key=f"{key}.reason") if reason_label else None
        with st.container(horizontal=True, gap="small"):
            yes = st.button(confirm_label, type="primary", key=f"{key}.yes")
            no = st.button("Không", key=f"{key}.no")
        if yes:
            try:
                with st.spinner("Đang xử lý, vui lòng chờ…"):
                    message, warnings = action(reason)  # gọi controller, trả (thông báo, cảnh báo)
            except AppError as exc:
                show_error_list(exc)  # lỗi hiện ngay trong hộp thoại, sửa rồi thử lại
            except PydanticValidationError as exc:
                show_error_list(InvalidInputError.from_pydantic(exc))
            else:
                set_flash(state, message, warnings)
                if on_done:
                    on_done()
                st.rerun()
        if no:
            st.rerun()

    _dialog()
```
Gọi bên trong `if st.button(...)`. Lý do trả lại / hủy: page KHÔNG tự kiểm tra độ dài; backend trả lỗi BR-33 / BR-36
("Vui lòng nhập lý do trả lại." / "Vui lòng nhập lý do hủy.") và lỗi hiện trong hộp thoại.

### 0.7 Use case được gọi khi tải trang (trước khi người dùng bấm gì)
Chỉ các use case **chỉ đọc, không lỗi khi dữ liệu trống**: `get_costsheet_options`, `list_costsheets`, `list_my_tasks`,
`search_fabrics` (selected_tcfno=None), `list_fabric_imports`, `view_norm_set` (norm_set_code=None), `list_parameter_sets`,
`list_fabric_factors`, `list_holidays`, `list_exchange_rates`, `list_customers`. Backend đảm bảo chúng trả danh sách rỗng
(không raise) khi DB trống và khi `current_user is None`.
`get_costsheet` chỉ gọi khi đã có `cs.open_id` (người dùng đã bấm Mở / Tạo / chọn phiếu) và luôn trong `try/except AppError`
(BR-52 "Bạn không có quyền xem costsheet này." phải hiện mà trang vẫn vẽ tiếp).
Mọi use case ghi dữ liệu / dựng file chỉ chạy trong `if st.button(...)`, `st.form_submit_button`, hoặc nút xác nhận trong hộp thoại.
`download_norm_template` và `export_costsheets` dùng `download_button(lambda: ..., file_name=...)` (không lỗi với đầu vào hợp lệ).

### 0.8 Trang và menu (manifest)
```python
FEATURE = FeatureManifest(
    key="woven_costing", title="Tính giá vải dệt",
    description=<câu đầu mục 1 / như scaffold>, icon="🧵", group="Kinh doanh Woven", owner="Sales Woven (team FS)",
    pages=(CostsheetListPage, CostsheetPage, MyTasksPage, FabricDataPage, NormParameterPage, ExchangeRatePage, CustomerPage),
    roles=tuple((code.value, ROLE_LABELS[code]) for code in RoleCode),   # SALES, TRUONG_TEAM, TRUONG_DON_VI, SO, PD, FS1, FS2
)
```
| # | Page class | File | slug | title | icon | menu_group |
|---|---|---|---|---|---|---|
| 1 | `CostsheetListPage` | `costsheet_list_page.py` | (landing) | Danh sách costsheet | 📋 | Sales |
| 2 | `CostsheetPage` | `costsheet_page.py` | `costsheet` | Costsheet | 🧾 | Sales |
| 3 | `MyTasksPage` | `my_tasks_page.py` | `viec-cho-toi` | Việc chờ tôi | 📥 | Sales |
| 4 | `FabricDataPage` | `fabric_data_page.py` | `ma-vai` | Dữ liệu mã vải | 🧶 | Phòng SO |
| 5 | `NormParameterPage` | `norm_parameter_page.py` | `dinh-muc` | Định mức và tham số | 📐 | Phòng SO |
| 6 | `ExchangeRatePage` | `exchange_rate_page.py` | `ty-gia` | Tỷ giá | 💱 | Phòng SO |
| 7 | `CustomerPage` | `customer_page.py` | `khach-hang` | Khách hàng | 👥 | Phòng SO |

Quyền mở trang do quản trị viên cấp ở `/admin` (bảng quyền mục 8). Trong trang, nút của vai trò khác bị **ẩn** (mục 8
Screen 2: "nút không được phép thì ẩn"); ở Screen 4/5 các khối chỉ SO dùng được bị ẩn với người không có SO (sales: "chỉ tra
cứu + in nhãn", "chỉ xem").

### 0.9 Mẫu bắt lỗi cục bộ
Nút không mở hộp thoại (Tính lại, Lưu nháp, Lưu OC, Sao chép, Tạo phiên bản mới, Xác nhận giá sợi hôm nay, Kiểm tra file…):
```python
if st.button("Lưu nháp", key=self.key("btn.save"), icon=":material/save:"):
    try:
        result = feature.save_draft(build_input_request(...))
    except AppError as exc:
        show_error_list(exc)  # trang vẫn vẽ, ô nhập giữ nguyên
    else:
        replace_working(result)
        set_flash(self.state, result.message, result.warning_texts)
        st.rerun()
```
(`PydanticValidationError` khi dựng request: bắt như `confirm_dialog` và hiện `InvalidInputError.from_pydantic(exc)`.)

### 0.10 Kiểm tra API Streamlit (bản cài đặt là chuẩn)
Lệnh: `.venv/Scripts/python.exe -X utf8 -c "import inspect, streamlit as st; print(st.__version__, inspect.signature(st.<fn>))"`
(chạy cho từng hàm). Kết quả: `1.64.0`; có đủ và dùng các tham số sau:
- `st.badge(label, *, icon, color, width, help)`; `st.segmented_control(..., default, required, format_func, key, persist_state)`;
  `st.pills(..., selection_mode, persist_state)`; `st.container(*, border, key, horizontal, wrap, gap, ...)`;
  `st.tabs(tabs, *, default, key, on_change)` + `TabContainer.open` (có); `st.expander(label, expanded, *, key, icon, on_change)`
  + `ExpanderContainer.open` (có); `st.dialog(title, *, width, dismissible, icon, on_dismiss)`;
  `st.toggle(..., persist_state)`; `st.date_input(label, value, min_value, max_value, key, *, format, persist_state)`;
  `st.multiselect(..., default, format_func, key, *, placeholder, persist_state)`;
  `st.selectbox(..., index, format_func, key, *, placeholder, accept_new_options, persist_state)`;
  `st.number_input(label, min_value, max_value, value, step, format, key, *, disabled)`; `st.text_input(..., max_chars, key, *, placeholder, disabled)`;
  `st.text_area(..., max_chars, key)`; `st.radio(..., horizontal)`; `st.form(key, clear_on_submit, *, border)`;
  `st.form_submit_button(label, *, type, icon, disabled)`; `st.button(label, key, help, *, type, icon, disabled)`;
  `st.metric(label, value, delta, delta_color, *, help, border, format)`; `st.toast(body, *, icon, duration)`;
  `st.space(size)`; `st.menu_button(...)` (không dùng); `st.popover(...)` (không dùng); `st.warning/info/error(body, *, icon, title)`;
  `st.data_editor(..., column_config, column_order, num_rows, disabled, key)` (qua `editable_table`);
  `st.dataframe(..., on_select, selection_mode, lazy)` (qua `data_table`);
  `st.file_uploader(label, type, accept_multiple_files, key, help)` (trong `multi_upload.py`);
  `st.container(..., vertical_alignment=)` nhận `'top' | 'center' | 'bottom' | 'distribute'`.
- Đã dựng thử: `MultiselectColumn("Trạng thái", options=[...], color=[...])` -> mỗi lựa chọn có màu riêng (OK);
  `NumberColumn(format="v%d")` (OK).
- `st.column_config`: `TextColumn(label, *, width, help, disabled, required, pinned, max_chars)`,
  `NumberColumn(label, *, width, disabled, required, pinned, format, min_value, max_value, step)`,
  `DateColumn(label, *, format, ...)`, `DatetimeColumn(label, *, format, timezone)`,
  `SelectboxColumn(label, *, required, default, options, format_func)`, `CheckboxColumn(label, *, disabled, default)`,
  `MultiselectColumn(label, *, options, color, format_func)` - đều có.
- Không dùng: `st.set_page_config`, `unsafe_allow_html`, `st.html`, `use_container_width`, `st.*_chart`, `st.plotly_chart`.

---

## 1. Screen 1 - Danh sách costsheet (`CostsheetListPage`, landing, menu Sales)
- title `Danh sách costsheet`, icon `📋`, description `"Lọc, xem mọi costsheet được phép xem; tạo mới và xuất Excel."`
- UC: UC-27 (`list_costsheets`), UC-28 (`export_costsheets`), mở Screen 2 cho UC-15 / UC-29. Dùng thêm UC-38 cho danh sách lọc.

Phác thảo:
```
[flash]
┌ 🔎 Bộ lọc ─────────────────────────────────────────────────────────────┐
│ Từ khóa [..............................]  Trạng thái [Nháp × Chờ duyệt ×…] │
│ Team [▾] Sales [▾] Khách hàng [▾] Nhà máy nhuộm [▾] Loại đơn [▾] Loại giá [▾] │
│ Ngày tính giá [01/08/2026 – 20/11/2026]  (o) Chỉ phiên bản mới nhất  ( ) Chỉ dưới ngưỡng GP/OP │
└──────────────────────────────────────────────────────────────────────────┘
[Số phiếu][Chờ duyệt][Đã duyệt][Đã chốt đơn][Dưới ngưỡng GP/OP][Độ co thấp / bằng 0]
┌ bảng (chọn 1 dòng) ─────────────────────────────────────────────────────┐
[➕ Tạo costsheet] [📂 Mở phiếu đã chọn] [⬇ Xuất Excel]
```
Khối từ trên xuống:
1. `show_flash(self.state)`; `feature = gateway.open(WovenCostingController)`;
   `options = feature.get_costsheet_options(EmptyRequest())` (UC-38, không lỗi khi trống).
2. `with panel("Bộ lọc", icon="🔎"):`
   - hàng 1 `c1, c2 = st.columns([2, 3])`:
     - `c1.text_input("Từ khóa", key=self.key("keyword"), placeholder="Số costsheet, mã vải, OC, style", persist_state="session")`;
     - `c2.multiselect("Trạng thái", list(CostsheetStatus), default=[s for s in CostsheetStatus if s != CostsheetStatus.DA_THAY_THE], format_func=lambda s: s.value, key=self.key("statuses"), persist_state="session")`.
   - hàng 2 `st.columns(6)`, mỗi ô `st.selectbox(label, options, index=None, placeholder="Tất cả", key=..., persist_state="session")`:
     - "Team" -> `options.teams` (["FS1","FS2"]) key `team`;
     - "Sales" -> `options.sales_users` (`format_func=lambda u: u.name`, giá trị gửi `u.username`) key `sales`;
     - "Khách hàng" -> `[c.name for c in options.customers]` key `customer`;
     - "Nhà máy nhuộm" -> `list(DyePlant)` key `dye_plant`;
     - "Loại đơn" -> `list(OrderType)` key `order_type`;
     - "Loại giá" -> `list(PriceType)` key `price_type`.
   - hàng 3 `st.columns([2, 1, 1])`:
     - `st.date_input("Ngày tính giá (từ - đến)", value=(date.today() - timedelta(days=90), date.today()), format="DD/MM/YYYY", key=self.key("dates"), persist_state="session")`
       -> tuple; khi người dùng mới chọn 1 đầu (tuple 1 phần tử) thì `date_to = date_from`;
     - `st.toggle("Chỉ phiên bản mới nhất", value=True, key=self.key("latest"), persist_state="session")`;
     - `st.toggle("Chỉ dưới ngưỡng GP/OP", value=False, key=self.key("below"), persist_state="session")`.
3. `request = ListCostsheetsRequest(keyword, statuses, team, sales_username, customer_name, dye_plant, order_type, price_type, date_from, date_to, latest_only, below_threshold_only)`;
   `data = feature.list_costsheets(request)` (UC-27; không cache vì phụ thuộc người dùng).
4. `stat_row([("Số phiếu", k.total), ("Chờ duyệt", k.pending), ("Đã duyệt", k.approved), ("Đã chốt đơn", k.closed), ("Dưới ngưỡng GP/OP", k.below_threshold), ("Độ co thấp / bằng 0", k.low_shrinkage)])`
   với `k = data.kpis`, số qua `format_number`.
5. Bảng: `picked = data_table(rows, column_config=CFG, column_order=ORDER, selection="single", key=self.key("grid"), empty_message="Chưa có costsheet nào phù hợp bộ lọc.")`
   Dòng (từ `CostsheetListRowDTO`), backend trả sẵn đã sắp **Ngày tính giá giảm dần**:

   | Cột (nhãn) | Field | column_config |
   |---|---|---|
   | `id` (ẩn: không có trong `column_order`) | `id` | - |
   | Số costsheet | `costsheet_no` | `TextColumn(pinned=True)` |
   | Phiên bản | `version` | `NumberColumn(format="v%d", width="small")` |
   | Trạng thái | `[status.value]` | `MultiselectColumn` màu (mục 0.3) |
   | Ngày tính giá | `costing_date` | `DateColumn(format="DD/MM/YYYY")` |
   | Sales | `sales_name` | `TextColumn` |
   | Team | `team` | `TextColumn(width="small")` |
   | Khách hàng | `customer_name` | `TextColumn` |
   | Thị trường | `market` | `TextColumn` |
   | Loại đơn | `order_type` | `TextColumn` |
   | OC | `oc_no` | `TextColumn` |
   | Mã vải | `tcfno` | `TextColumn` |
   | Hình thức bán | `sale_form` | `TextColumn` |
   | Nhà máy nhuộm | `dye_plant` | `TextColumn(width="small")` |
   | Loại giá | `price_type` | `TextColumn(width="small")` |
   | Số mét | `order_meters` | `NumberColumn(format="localized")` |
   | Giá bán (VND/m) | `sell_price_vnd` | `NumberColumn(format="localized")` |
   | Giá bán (USD/m) | `sell_price_usd` | `NumberColumn(format="%.4f")` |
   | Giá vốn (VND/m) | `cogs_vnd` | `NumberColumn(format="localized")` |
   | F&I (VND/m) | `freight_insurance` | `NumberColumn(format="localized")` |
   | GP% | `gp_pct` ×100 | `NumberColumn(format="%.2f %%")` |
   | OP% | `op_pct` ×100 | `NumberColumn(format="%.2f %%")` |
   | Cảnh báo | `warning_text` (ví dụ "GP/OP thấp; Độ co thấp") | `TextColumn` |
   | Người duyệt | `approved_by_name` | `TextColumn` |
   | Ngày duyệt | `approved_at` | `DatetimeColumn(format="DD/MM/YYYY HH:mm")` |

   Các giá trị enum chuyển `.value` khi dựng dòng; số `Decimal` -> `float` để bảng định dạng.
6. Thanh nút `with st.container(horizontal=True, gap="small"):`
   - `st.button("Tạo costsheet", type="primary", icon=":material/add:", key=self.key("new"), disabled=not has_any(..., "SALES", "TRUONG_TEAM"), help=...)`
     -> `navigation.new_costsheet(self)` (Screen 2 ở chế độ tạo mới; UC-15 chạy ở Screen 2). Tắt (kèm `help="Chỉ Sales / Trưởng team lập costsheet."`) khi
     tài khoản không có SALES / TRUONG_TEAM (chỉ hiển thị; backend BR-51 vẫn chặn).
   - `st.button("Mở phiếu đã chọn", icon=":material/folder_open:", key=self.key("open"), disabled=not picked)` -> `navigation.open_costsheet(self, picked[0]["id"])`.
   - `download_button(lambda: feature.export_costsheets(request), label="Xuất Excel", key=self.key("export"), file_name=f"danh-sach-costsheet-{date.today():%Y%m%d}.xlsx")` (UC-28, theo bộ lọc đang chọn; `request` là đối tượng mới tạo mỗi lần chạy).
- Lần đầu không có dữ liệu: bộ lọc mặc định, 6 ô = 0, `empty_state("Chưa có costsheet nào phù hợp bộ lọc.")`, nút Mở tắt, Xuất Excel vẫn dùng được (file chỉ có tiêu đề).

---

## 2. Screen 2 - Costsheet (`CostsheetPage`, slug `costsheet`, menu Sales)
- title `Costsheet`, icon `🧾`, description `"Lập, tính, xem và duyệt một costsheet."`
- UC: UC-14..UC-26, UC-29 (+ UC-38 danh mục).

### 2.1 Vòng đời trang (state)
```python
def render(self):
    show_flash(self.state)
    feature = gateway.open(WovenCostingController)
    options = feature.get_costsheet_options(EmptyRequest())
    self._open_picker(feature, options)                 # 2.2 - luôn hiện
    cid = self.state.get("cs.open_id")
    if not cid:
        self._create_panel(feature, options)            # 2.3 - chế độ tạo mới
        return
    working = self._working(feature, cid)               # 2.1.a
    if working is None:
        return
    rev = self.state.get("cs.rev", 0); sfx = f"{working.id}.{rev}"
    editable = working.editable
    self._header(working)                               # 2.4
    self._summary(working)                              # 2.5
    a = self._order_block(working, options, sfx, editable)          # 2.6 khối A
    tabs = st.tabs([...8 thẻ...], key=self.key(f"tabs.{working.id}"))   # 2.7 - KHÔNG lazy (xem lý do)
    ... mỗi thẻ trả các giá trị đã nhập ...
    self._toolbar(feature, working, a, yarn_rows, twist_rows, weaving, dyeing, price, params, sfx)   # 2.8 - cuối trang
```
**2.1.a `_working`**: `w = self.state.get("cs.working")`; nếu `w is None or w.id != cid`:
`try: w = feature.get_costsheet(GetCostsheetRequest(costsheet_id=cid))` `except AppError as exc: show_error_list(exc); self.state.set("cs.open_id", None); return None`;
rồi `replace_working(w)` = `state.set("cs.working", w); state.set("cs.rev", rev+1); state.set("cs.dirty", False)` (không rerun).
Như vậy `get_costsheet` chỉ gọi 1 lần khi mở; các lần chạy lại (gõ ô, sửa bảng) dùng bản trong state, ô nhập giữ nguyên.

**Gieo widget:** mọi widget nhập của Screen 2 có key `self.key(f"<tên>.{sfx}")`. Trước khi vẽ: `seed(key, giá_trị_từ_working)`,
vẽ widget không truyền `value=`/`index=`. Bảng sửa trong ô: `editable_table(rows_từ_working, key=self.key(f"<bảng>.{sfx}"), ...)`.
Khi `cs.working` được thay (mở phiếu, Tính lại, Lưu nháp, mọi thao tác, đổi phiên bản) `rev` tăng -> key mới -> widget gieo
lại đúng số mới (kể cả cột kết quả trong bảng sợi). Ô đang gõ dở giữa 2 lần tính được giữ vì key không đổi.

**Vì sao các thẻ KHÔNG lazy:** thẻ nào không được vẽ trong 1 lần chạy thì Streamlit xoá state widget của thẻ đó -> mất các ô
sửa trong bảng khi chuyển thẻ, và nút "Tính lại" ở cuối trang sẽ không đọc được giá trị các thẻ khác. Mọi thẻ chỉ đọc từ
`cs.working` (không gọi use case), nên vẽ cả 8 thẻ mỗi lần vẫn nhanh. Dùng `st.tabs([...], key=self.key(f"tabs.{working.id}"))`
(có `key` để nhớ thẻ đang mở qua các lần rerun) và KHÔNG truyền `on_change`, không dùng `.open`.

**Tính lại (UC-16) không lưu:** đọc mọi giá trị widget của lần chạy này -> `build_input_request(working, ...)` ->
`feature.calculate_costsheet(req)` -> `replace_working(resp)`, `state.set("cs.dirty", True)`, `st.toast("Đã tính lại.", icon=":material/calculate:")`, `st.rerun()`.
Khi `cs.dirty` = True, dưới tiêu đề hiện `st.caption(":orange[Kết quả đã tính lại nhưng chưa lưu. Bấm \"Lưu nháp\" để lưu.]")`.
Vì response của `calculate_costsheet` mang lại chính các ô nhập (đã chuẩn hóa) + kết quả, gieo lại widget từ response
không làm mất gì người dùng đã nhập.

### 2.2 Ô chọn phiếu đang mở (luôn ở đầu trang)
`with st.container(horizontal=True, gap="small", vertical_alignment="bottom"):`
- `st.selectbox("Phiếu đang mở", options=<số costsheet gần đây>, index=None, accept_new_options=True, placeholder="Gõ hoặc chọn số costsheet", key=self.key("pick_no"))`
  - options = `[r.costsheet_no for r in feature.list_costsheets(ListCostsheetsRequest(latest_only=True, <mặc định 90 ngày>)).rows]`
    (lấy tối đa 200 số đầu; không lỗi khi trống). Khi phiếu đang mở có số không nằm trong list thì thêm vào đầu list.
- `st.selectbox("Phiên bản", options=[v.version for v in working.versions], format_func=lambda v: f"v{v}", key=self.key(f"pick_ver.{working.costsheet_no}"))`
  (chỉ khi có phiếu đang mở; seed = `working.version`).
- `st.button("Mở", icon=":material/folder_open:", key=self.key("pick_go"))`:
  `try: w = feature.get_costsheet(GetCostsheetRequest(costsheet_no=no, version=ver_or_None))` -> `state.set("cs.open_id", w.id)`; `replace_working(w)`; `st.rerun()`
  `except AppError: show_error_list(exc)` (AC-33: "Bạn không có quyền xem costsheet này."). Đổi số costsheet thì `version=None` (= mới nhất).
- `st.button("Tạo costsheet mới", icon=":material/add:", key=self.key("pick_new"))` (chỉ khi đang mở 1 phiếu và có SALES/TRUONG_TEAM)
  -> `navigation.new_costsheet(self)` (đặt open_id None; ở cùng trang thì `st.rerun()`).

### 2.3 Chế độ tạo mới (UC-15), khi chưa mở phiếu nào
`with panel("Tạo costsheet mới", icon="➕", description="Nhập thông tin đơn, app lấy thông số vải, định mức, tham số và tính ngay."):`
1. Ngoài form (vì form không chứa nút thường): hàng `st.container(horizontal=True, vertical_alignment="bottom")`:
   `customer = st.selectbox("Khách hàng", [c.name for c in options.customers], key=self.key("new.customer"), placeholder="Chọn khách hàng")`
   (áp `cs.pending_customer` nếu có: `st.session_state[key] = state.pop("cs.pending_customer")` TRƯỚC khi vẽ; seed None)
   + `st.button("Thêm khách hàng", icon=":material/person_add:", key=self.key("new.add_cust"))` -> hộp thoại 2.9.1.
2. `with st.form(self.key("new.form"), border=False):` 3 cột:
   - "Nhà máy nhuộm" `st.segmented_control(..., list(DyePlant), default=DyePlant.HCM, required=True)`;
   - "Thị trường" `st.selectbox(list(Market), index=0)`; "Loại đơn hàng" `st.selectbox(list(OrderType), index=1)` (Sản Xuất);
   - "Style" `st.text_input(max_chars=100)`; "Hình thức bán" `st.selectbox(list(SaleForm), index=1)` (Vải Thành Phẩm);
   - "Giá mộc mua ngoài (đ/m, khi Vải Nhuộm)" `st.number_input(min_value=0.0, step=100.0, value=None)`;
   - "Ngày giao hàng" `st.date_input(value=None, format="DD/MM/YYYY")`; "Ngày tính giá" `st.date_input(value="today", format="DD/MM/YYYY")`;
   - "Mã vải" `st.text_input(max_chars=15, placeholder="Ví dụ EM35790026")` (gửi `.strip().upper()`);
   - "Số lượng đặt (m)" `st.number_input(min_value=0.0, step=100.0, value=None)`;
   - "Loại giá" `st.selectbox(list(PriceType), index=0)` (FOB); "Số OC (có thể nhập sau)" `st.text_input(max_chars=40)`.
   - `st.form_submit_button("Tạo costsheet", type="primary", icon=":material/add:")` ->
     `try: w = feature.create_costsheet(CreateCostsheetRequest(dye_plant, customer_name=customer, market, order_type, style, sale_form, greige_buy_price, delivery_date, costing_date, tcfno, order_meters, price_type, oc_no))`
     `except AppError: show_error_list(exc)` (BR-03 mã vải chưa có, BR-61 chưa có tỷ giá, BR-51 chưa có team)
     `else: state.set("cs.open_id", w.id); replace_working(w); set_flash(state, w.message or f"Đã tạo costsheet {w.costsheet_no}."); st.rerun()`.
3. Lần đầu không có dữ liệu: ô chọn phiếu trống, panel tạo mới với giá trị mặc định; KHÔNG gọi use case có thể lỗi.
   Nếu `options.customers` rỗng: dưới ô khách hàng `st.caption("Chưa có khách hàng. Bấm \"Thêm khách hàng\" hoặc nhờ SO tải danh sách.")`.

### 2.4 Tiêu đề
```python
with st.container(horizontal=True, gap="small", vertical_alignment="center"):
    st.markdown(f"### {w.costsheet_no} · v{w.version}")
    status_badge(w.status)                                # st.badge (mục 0.3)
    if w.fabric_overridden: st.badge("Thông số vải đã sửa", color="orange", icon=":material/edit:")
st.caption(f"Người lập: {w.sales_name} ({w.team}) · Người duyệt: {w.approved_by_name or '-'} {format_datetime(w.approved_at)} "
           f"· Tỷ giá {format_number(w.exchange_rate)} · Bộ định mức {w.norm_set_code} · Bộ tham số {w.parameter_set_date:%d/%m/%Y}"
           + (f" · Sao chép từ {w.copied_from}" if w.copied_from else ""))
if w.status == TRA_LAI or w.return_reason: st.warning(f"Lý do trả lại: {w.return_reason}", icon=":material/undo:")   # BR-34: vẫn hiện khi đã về Nháp
if w.status == HUY: st.error(f"Đã hủy. Lý do: {w.cancel_reason}", icon=":material/block:")
if not w.editable: st.info("Phiếu đang ở trạng thái <status>, chỉ xem.", icon=":material/visibility:")   # BR-31/BR-38/BR-39; SO luôn chỉ xem
if self.state.get("cs.dirty"): caption cam (2.1)
```

### 2.5 Ô tóm tắt
`st.columns(5)`, mỗi ô `st.metric(label, value, border=True)`:
- "Đơn giá (đ/m)" = `format_number(r.unit_cost_vnd)`; "Giá vốn" = `format_number(r.cogs_vnd)`; "Giá bán" = `format_number(r.sell_price_vnd)`;
- "GP%" = `pct_text(r.gp_pct)`, `delta=f"{pct_text(r.gp_pct - r.gp_threshold)} so với ngưỡng {pct_text(r.gp_threshold)}"`, `delta_color="normal"`
  -> âm hiện **đỏ** (dưới ngưỡng tô đỏ), dương hiện xanh;
- "OP%" tương tự với `op_threshold`.
(`r = w.result`; khi chưa tính được (`r.calculated` = False, ví dụ thiếu giá bán) giá trị "-" và không có delta.)

### 2.6 Khối A - Thông tin đơn (`panel("Thông tin đơn", icon="📝")`)
Các widget (seed từ `w.input`, `disabled=not w.editable`), lưới `st.columns(4)`:

| Nhãn | Widget | Field `w.input` | Ghi chú |
|---|---|---|---|
| Nhà máy nhuộm | `segmented_control(list(DyePlant), required=True)` | `dye_plant` | đổi -> thẻ Nhuộm đổi theo ngay (rerun) |
| Khách hàng | `selectbox([c.name ...], placeholder="Chọn khách hàng")` + nút "Thêm khách hàng" | `customer_name` | nút chỉ khi `ADD_CUSTOMER` trong `allowed_actions`; áp `cs.pending_customer` trước khi vẽ |
| Thị trường | `selectbox(list(Market))` | `market` | |
| Loại đơn hàng | `selectbox(list(OrderType))` | `order_type` | |
| Style | `text_input(max_chars=100)` | `style` | |
| Hình thức bán | `selectbox(list(SaleForm))` | `sale_form` | Mộc -> ẩn thẻ Nhuộm (2.7.4) |
| Giá mộc mua ngoài (đ/m) | `number_input(min_value=0.0, step=100.0)` | `greige_buy_price` | **chỉ vẽ khi Hình thức bán = Vải Nhuộm** |
| Ngày giao hàng | `date_input(format="DD/MM/YYYY")` | `delivery_date` | seed None được |
| Ngày tính giá | `date_input(format="DD/MM/YYYY")` | `costing_date` | |
| Mã vải | `text_input(max_chars=15)` | `tcfno` | đổi mã + Tính lại -> backend lấy lại thông số / sợi |
| Số lượng đặt (m) | `number_input(min_value=0.0, step=100.0)` | `order_meters` | |
| Loại giá | `selectbox(list(PriceType))` | `price_type` | điều khiển ô F&I (2.7.5) |
| Số OC | `text_input(max_chars=40, placeholder="KDV10-SX-LO-0726-6564.1")` | `oc_no` | **sửa được khi** `editable` **hoặc** `SAVE_OC` trong `allowed_actions` (Chờ duyệt / Đã duyệt / Đã chốt đơn, UC-24) |
| Lý do ngoại lệ độ co | `selectbox(list(ShrinkageException))` | `shrinkage_exception` | khi `w.result.low_shrinkage`: nhãn thêm `:orange-badge[Độ co thấp]` |
| Lý do độ co thấp / bằng 0 | `text_input(max_chars=300)` | `shrinkage_reason` | chỉ vẽ khi `w.result.low_shrinkage` hoặc đã có giá trị |
| Ghi chú | `text_area(max_chars=1000, height=68)` | `note` | full width |

### 2.7 Các thẻ
`st.tabs(["Thông số vải", "Sợi", "Ngành Dệt", "Nhuộm", "Giá bán & lợi nhuận", "Tham số", f"Cảnh báo ({len(w.warnings)})", "Lịch sử"], key=self.key(f"tabs.{w.id}"))`
(khi Hình thức bán đang chọn = Mộc, bỏ thẻ "Nhuộm" khỏi danh sách - UI concept "ẩn khi Mộc").

#### 2.7.1 Thông số vải (khối B)
- `st.markdown(f"**{f.fabric_name}**")` + `st.badge(f"Nguồn: {f.source}", color="blue" if Peace/WFX else "orange")`.
- `data_table(rows, column_config=...)` 3 cột: "Thông số" | "Mộc" | "Thành phẩm" | "⚑" (🟠 khi field nằm trong `f.overridden_fields`):
  Khổ (cm), Khổ cắt (cm), g/m2, g/m, Mật độ dọc (sợi/10 cm), Mật độ ngang (sợi/10 cm), m/kg. Số `NumberColumn(format="localized")`
  (m/kg `format="%.4f"`).
- `stat_row([("Độ co", pct_text(r.shrinkage)), ("Độ co mắc", pct_text(f.warping_loss_rate))])`.
- Bảng sợi gốc chỉ đọc (`f.yarns`): Hướng, STT, Tên sợi, Tỷ lệ (%), Loại sợi, Sợi gốc, Tỷ lệ sợi gốc (%), T/M.
- Nút (theo `allowed_actions`), `st.container(horizontal=True)`:
  - "Sửa thông số vải" (`EDIT_FABRIC`, chỉ có khi nguồn "Nhập tay" + Nháp/Trả lại, BR-47; AC-41: mã Peace không có nút) -> hộp thoại 2.9.3;
  - "In nhãn" (`PRINT_LABEL`) -> hộp thoại 2.9.4.
  (Hai nút này cũng nằm trên thanh nút 2.8; ở đây lặp lại cho tiện - **khác key**.) Nếu không muốn lặp, UI-build chỉ để ở 2.8.
- Khi `f.source != "Nhập tay"`: `st.caption("Thông số lấy từ dữ liệu gốc Peace / WFX, chỉ đọc.")`.

#### 2.7.2 Sợi (khối C)
- Ô Hồ cho mọi sợi dọc (BR-09): `st.toggle("Tick Hồ cho tất cả sợi dọc", key=self.key(f"sized.{sfx}"), disabled=not editable)`, seed = mọi dòng WARP có `is_sized`;
  bên cạnh `st.caption(f"Gợi ý: {w.size_suggest_reason}")` khi có lý do gợi ý (ví dụ "Sợi spun không se").
- Bảng `editable_table(rows, key=self.key(f"yarns.{sfx}"), columns=YARN_COLS, column_config=..., disabled=[mọi cột trừ 4 cột nhập])` khi `editable`;
  `data_table(...)` cùng cột khi không sửa được. Dòng = `w.yarn_lines` (`YarnLineViewDTO`), không thêm / xoá dòng:

  | Cột | Field | Sửa | column_config |
  |---|---|---|---|
  | Hướng | `direction` (WARP/WEFT) | - | `TextColumn(width="small", pinned=True)` |
  | STT | `seq` | - | `NumberColumn(width="small")` |
  | Tên sợi | `yarn_name` | - | `TextColumn(width="large")` |
  | T/M | `twist_tpm` | - | `TextColumn(width="small")` |
  | Tỷ lệ (%) | `ratio`×100 | - | `NumberColumn(format="%.2f")` |
  | Đơn vị giá | `price_currency` | ✔ | `SelectboxColumn(options=["USD", "VND"], required=True)` |
  | Giá | `price_input` | ✔ | `NumberColumn(min_value=0, format="%.4f", help="USD/kg hoặc đ/kg")` |
  | Giá (đ/kg) | `price_vnd` | - | `NumberColumn(format="localized")` |
  | Ngày nhập giá | `price_entered_on` | - | `DateColumn(format="DD/MM/YYYY")` |
  | Giá hết hạn | `"🟠"` khi `price_expired` | - | `TextColumn(width="small")` |
  | Sợi cặn (%) | `waste_rate`×100 | ✔ | `NumberColumn(min_value=0, max_value=99.99, format="%.2f")` |
  | Se | `is_twisted` | ✔ | `CheckboxColumn()` |
  | Hồ | `is_sized` | - | `CheckboxColumn(disabled=True)` (theo toggle ở trên; sợi ngang luôn trống) |
  | Lý do gợi ý Hồ | `size_suggest_reason` | - | `TextColumn` |
  | Tiêu hao (%) | `loss_rate`×100 | - | `NumberColumn(format="%.2f")` |
  | Lượng sợi (kg) | `yarn_kg` | - | `NumberColumn(format="%.2f")` |
  | Thành tiền (đ) | `amount` | - | `NumberColumn(format="localized")` |
- Dưới bảng: `stat_row([("Tổng tỷ lệ", pct_text(r.yarn_ratio_total)), ("Tổng chi phí sợi (đ)", format_number(r.yarn_total)), ("Giá thanh lý sợi cặn (đ/kg)", format_number(param yarn_waste_price))])`
  (giá thanh lý sợi cặn sửa ở thẻ Tham số - BR-46; ở đây chỉ hiện).
- Nút "Xác nhận giá sợi hôm nay" (`CONFIRM_YARN_PRICES`) nằm trên thanh nút 2.8.
- Rỗng (mã chưa có sợi): `empty_state("Mã vải chưa có dòng sợi.", "Liên hệ SO / PD bổ sung sợi cho mã này.")`.

#### 2.7.3 Ngành Dệt (khối D)
1. `section_title("Dòng Se")` + `editable_table(rows, key=self.key(f"twist.{sfx}"), columns=TWIST_COLS, allow_add_delete=True)` (không sửa được: `data_table`), dòng = `w.input.twist_lines`:
   | Cột | Field | column_config |
   |---|---|---|
   | Hướng | `direction` | `SelectboxColumn(options=["Dọc", "Ngang"], required=True)` |
   | Hệ sợi | `fiber_system` | `SelectboxColumn(options=["Filament", "Spun"], required=True)` |
   | Chi số | `count` | `SelectboxColumn(options=[c.count for c in options.counts], required=True)` |
   | Độ săn | `twist` | `SelectboxColumn(options=options.twists, required=True)` (số nguyên) |
   | SL yêu cầu (kg) | `quantity_kg` | `NumberColumn(min_value=0, format="%.2f", required=True)` |
   Dưới bảng: `stat_row([("Sản lượng Se ước tính (kg)", r.twist_estimated_kg), ("Tổng SL Se nhập (kg)", r.twist_entered_kg), ("Chênh lệch (kg)", r.twist_estimated_kg - r.twist_entered_kg)])`.
   `st.caption("Tối đa 9 dòng Se dọc và 9 dòng Se ngang.")`. Dòng trống (mọi ô None) được bỏ khi dựng request.
2. `section_title("Hồ, mắc, cone, gia công")`, `st.columns(4)`:
   - "Nguyên liệu hồ" `selectbox(options.size_materials, placeholder="Không hồ")` -> `weaving.size_material`; dưới: `st.caption(f"Nhóm tổng canh: {r.size_band or '-'}")`;
   - "Mắc phân băng" `segmented_control(["Có", "Không"])` -> `weaving.warping_band`;
   - "Chi số cone 1" `selectbox([c.count ...], placeholder="-")`, "SL cone 1 (kg)" `number_input(min_value=0.0)` (help: "Để trống = tổng SL Se ngang");
   - "Chi số cone 2", "SL cone 2 (kg)";
   - "Gia công Se (đ/kg)", "SL gia công Se (kg)", "Gia công Hồ (đ/m)", "Gia công Dệt (đ/m)", "Chi phí gia công khác (đ/m)" `number_input(min_value=0.0, step=100.0)`.
3. `section_title("Chi phí công đoạn")` `data_table(r.weaving_stages)` cột: Công đoạn, SL, Đơn vị, Định mức (đ/đơn vị), Hệ số mã hàng ("🟠" khi có BR-24), Thành tiền (đ).
4. `section_title("Chi phí theo khoản mục (đ/m)")` `data_table(r.cost_items)` cột: Công đoạn, Nhân công, Khấu hao, Điện, Vật tư, Nhiên liệu, Hóa chất, CPQL, Tổng (đ/m) (`format="localized"`).
5. `stat_row([("Hệ số số lượng", format_number(r.quantity_factor, 4)), ("Tổng chi phí ngành Dệt (đ)", ...), ("Đơn giá CM (đ/m)", ...), ("Số mét mộc", ...), ("Kg mộc", ...)])`.
6. Hình thức bán = Vải Nhuộm: `st.info("Vải Nhuộm: chi phí ngành Dệt = 0, dùng giá mộc mua ngoài.")` và ẩn mục 1-2 (vẫn giữ giá trị cũ trong request).

#### 2.7.4 Nhuộm (khối E) - chỉ khi Hình thức bán ≠ Mộc
Theo **Nhà máy nhuộm đang chọn ở khối A** (không phải giá trị đã lưu) vẽ HCM hoặc TCDN; giá trị nhà máy kia giữ nguyên trong request.

**HCM (4.15)** - `w.input.hcm_dyeing`:
- `st.columns(4)`: "Nguyên liệu nhuộm" `selectbox(options.hcm_dye_materials, placeholder="Chọn")`; "Cấp màu" `selectbox(options.hcm_color_levels + Blended)`;
  "Khổ" `segmented_control([1, 2, 3], format_func={1:"Khổ đơn",2:"Khổ đôi",3:"Khổ ba"}, required=True)`; "Tiêu hao quy trình nhuộm (%)" `number_input(min_value=0.0, max_value=99.99, format="%.2f")` (×100 / ÷100).
- Cấp màu = Blended: `st.columns(5)` 5 ô "Trắng (%)", "Nhạt (%)", "Trung bình (%)", "Đậm (%)", "Đặc biệt (%)" `number_input(0..100)` + `st.caption("Tổng tỷ trọng phải = 100%.")`.
- "Công đoạn đặc biệt (tối đa 7)": `editable_table(key="hcm_stages.{sfx}", columns=["Công đoạn"], column_config={"Công đoạn": SelectboxColumn(options=options.hcm_special_stages, required=True)}, allow_add_delete=True)`.
- "Tính năng đặc biệt (tối đa 6)": tương tự, options `options.hcm_special_features`.
- "Chi phí đặc biệt (tối đa 2)": `editable_table(columns=["Tên", "Đơn giá (đ/kg)"], allow_add_delete=True)`.
- `st.expander("Chi phí phát sinh do ngành báo giá", key=..., expanded=<có dữ liệu>)` (KHÔNG `on_change`): "Tên chi phí" text_input; 7 ô `number_input` trong `st.columns(7)`:
  HCTN, Tiền lương, Khấu hao, Điện, Nhiên liệu, Vật tư, Quản lý (đ/kg); "Lý do sửa so với giá ngành báo" text_input (300).
- "Gia công (tối đa 2)": `editable_table(columns=["Tên", "Đơn giá (đ/kg)"], allow_add_delete=True)`.
- Kết quả: `data_table(r.dyeing_lines)` cột: Dòng, HCTN, Tiền lương, Khấu hao, Điện, Nhiên liệu, Vật tư, Quản lý, Tiêu hao (%), Tổng (đ/kg), Ghi chú;
  `stat_row([("Tiêu hao nhuộm", pct), ("Chi phí/kg (đ)", r.dyeing_per_kg), ("Chi phí/m (đ)", r.dyeing_per_m), ("Tổng chi phí nhuộm (đ)", r.dyeing_total)])`.

**TCDN (4.16)** - `w.input.tcdn_dyeing`:
- `st.columns(4)`: "Nguyên liệu nhuộm" (`options.tcdn_dye_materials`), "Cấp màu" (`options.tcdn_color_levels` + Blended), "Phẩm nhuộm đặc biệt" (`options.special_dyes`, placeholder "Không"),
  "Giá hóa chất thuốc nhuộm (đ/m, vải 250 g/m)" `number_input` (chỉ vẽ khi có phẩm nhuộm đặc biệt); "Hóa chất WR" (`options.wr_chemicals`, placeholder "Không").
- Blended: 5 ô "White (%)", "Light (%)", "Medium (%)", "Dark (%)", "Special (%)".
- "Công đoạn ngoài quy trình (tối đa 13)": `editable_table(columns=["Công đoạn", "Giá hóa chất (đ/m)"], column_config={"Công đoạn": SelectboxColumn(options=options.tcdn_stages, required=True), "Giá hóa chất (đ/m)": NumberColumn(min_value=0, help="Bắt buộc với Coating, Santa, Bonding, Soaping")}, allow_add_delete=True)`;
  `st.caption("Công đoạn lặp lại = thêm dòng.")`.
- "Tính năng đặc biệt (tối đa 6)": `editable_table(columns=["Tính năng", "Giá hóa chất (đ/m)"], allow_add_delete=True)` (chưa có giá = liên hệ TCDN, tính 0).
- `st.expander("Chi phí phát sinh do ngành báo giá")`: "Loại quy trình" `segmented_control(["Nhuộm", "Partial"])`, "Tiêu hao quy trình nhuộm (%)", "Tên chi phí", 7 ô (đ/m):
  Hóa chất, Nhân công, Khấu hao, Điện, Nhiên liệu, Vật tư, CPQL; "Lý do sửa so với giá ngành báo".
- "Gia công ngoài (tối đa 2)": `editable_table(columns=["Tên", "Đơn giá (đ/m)", "Tiêu hao (%)"], allow_add_delete=True)`.
- Kết quả: `data_table(r.dyeing_lines)` cột: Dòng, Hóa chất, Nhân công, Khấu hao, Điện, Nhiên liệu, Vật tư, CPQL, Hệ số TCDN, Tiêu hao (%), Chi phí/m (đ), Ghi chú
  (ghi chú "liên hệ TCDN" khi giá 0); `stat_row([("Hệ số TCDN", r.tcdn_factor), ("Tiêu hao nhuộm", pct), ("Chi phí/m (đ)", ...), ("Tổng chi phí nhuộm (đ)", ...)])`.

#### 2.7.5 Giá bán & lợi nhuận (khối F)
- `st.columns(4)`: "Đơn vị giá bán" `segmented_control(["USD", "VND"], required=True)`; "Giá bán chưa VAT (/m)" `number_input(min_value=0.0, format="%.4f")`;
  "Commission (đ/m)" `number_input(min_value=0.0)`; "Lãi vay (đ/m)" `number_input(min_value=0.0)`.
- F&I (BR-29, theo **Loại giá đang chọn** ở khối A): CIF, CIP -> ô "F&I (đ/m)"; CPT -> ô "Phí vận chuyển (đ/m)"; FOB, EXW, FCA -> **không vẽ ô** (gửi 0).
- "Ngày shipment" `date_input(value=None, format="DD/MM/YYYY")`.
- "Chi phí vào giá vốn (tối đa 10)": `editable_table(key="cogs.{sfx}", columns=["Tên", "Đơn giá (đ/m)", "Ghi chú"], allow_add_delete=True)`.
- Bảng kết quả `data_table(r.profit_rows)` cột "Khoản" | "VND/m" (`localized`) | "USD/m" (`%.4f`) | "⚑" (🔴 khi `below_threshold`):
  Giá bán, Giá vốn, GP, GP%, S&A, Commission, F&I, Lãi vay, OP, OP%, Giá có VAT (dòng % hiển thị dạng "19,17%" trong cột VND; USD trống).
- `st.caption(f"Ngưỡng cảnh báo: GP% {pct_text(r.gp_threshold)}, OP% {pct_text(r.op_threshold)} (SO đặt).")`.

#### 2.7.6 Tham số (khối G)
- Bảng sửa được (tham số sales sửa được, BR-46): `editable_table(rows, key=self.key(f"params.{sfx}"), disabled=["Tham số", "Đơn vị", "Mặc định", "Đã sửa"])`
  dòng = `[p for p in w.parameters if not p.so_only]`: "Tham số" (`label`), "Đơn vị" (`unit`), "Mặc định" (`default_value`, ×100 khi `is_percent`),
  "Đang dùng" (`used_value`, ×100 khi `is_percent`, `NumberColumn(min_value=0, format="%.4f")`), "Đã sửa" (`"🟠"` khi `used_value != default_value`).
  `code` ẩn (không có trong `column_order`).
- Bảng chỉ đọc "Tham số chỉ SO đặt": `data_table([p for p in w.parameters if p.so_only])` cùng cột trừ "Đã sửa".
- `st.caption("Ô đã sửa được tô màu cho người duyệt và lưu theo phiếu.")`.

#### 2.7.7 Cảnh báo (khối H)
- Mỗi `w.warnings` (`WarningDTO(code, message, blocking)`): `st.error(message, icon="⛔")` nếu `blocking` (sẽ chặn gửi duyệt) ngược lại `st.warning(message, icon="⚠️")`;
  thứ tự backend trả.
- Rỗng: `st.success("Không có cảnh báo.", icon=":material/check:")`.

#### 2.7.8 Lịch sử (khối H)
- `section_title("Phiên bản")` + `picked = data_table(w.versions, selection="single", key=self.key(f"versions.{w.costsheet_no}"))`
  cột: Phiên bản (`v%d`), Trạng thái (badge màu), Ngày tính giá, Giá bán (VND/m), Giá vốn (VND/m), GP%, Người duyệt, Ngày duyệt; `id` ẩn.
  + `st.button("Mở phiên bản đã chọn", key=..., disabled=not picked or picked[0]["id"] == w.id)` -> như 2.1.a với id đó (`state.set("cs.open_id", id)`, pop working, `st.rerun()`).
- `section_title("Lịch sử thao tác")` + `data_table(w.history)` cột: Phiên bản, Thao tác, Người, Lúc (`DatetimeColumn`), Ghi chú. Rỗng: "Chưa có thao tác."

### 2.8 Thanh nút (cuối trang, chỉ nút có trong `w.allowed_actions`)
`with st.container(horizontal=True, gap="small"):` theo thứ tự UI concept. `A = set(w.allowed_actions)`:

| Nút (nhãn) | Hiện khi | Hỏi lại? | Gọi | Sau đó |
|---|---|---|---|---|
| Tính lại (`:material/calculate:`) | `RECALCULATE` | Không | `calculate_costsheet(build_input_request(...))` | 2.1 "Tính lại": thay working, `cs.dirty=True`, toast "Đã tính lại." |
| Lưu nháp (`:material/save:`, primary) | `SAVE_DRAFT` | Không | `save_draft(build_input_request(..., confirm_yarn_prices=False))` | thay working, `cs.dirty=False`, flash `resp.message` ("Đã lưu nháp costsheet <số> v<n>.") + `resp.warnings` |
| Gửi duyệt (`:material/send:`) | `SUBMIT` | **Có** | trong `action`: `save_draft(req)` rồi `submit_costsheet(CostsheetActionRequest(costsheet_id=w.id))` | flash `resp.message` (gửi duyệt hoặc "…được duyệt tự động.") + cảnh báo GP/OP (`resp.warnings`, BR-28 không chặn); thay working |
| Duyệt (`:material/check:`) | `APPROVE` | **Có** | `approve_costsheet(CostsheetActionRequest(costsheet_id=w.id))` | flash "Đã duyệt costsheet <số> v<n>." |
| Trả lại (`:material/undo:`) | `RETURN` | **Có, có ô lý do** | `return_costsheet(CostsheetActionRequest(costsheet_id=w.id, reason=reason))` | flash "Đã trả lại costsheet <số> v<n>." |
| Sao chép (`:material/content_copy:`) | `COPY` | Không | `copy_costsheet(CostsheetActionRequest(costsheet_id=w.id))` | `state.set("cs.open_id", resp.id)`, thay working, flash "Đã tạo costsheet <số mới> từ <số nguồn> v<n>.", rerun (mở phiếu mới) |
| Tạo phiên bản mới (`:material/add_circle:`) | `NEW_VERSION` | Không | `new_version(CostsheetActionRequest(costsheet_id=w.id))` | mở phiên bản mới (như Sao chép), flash "Đã tạo phiên bản <n+1> của costsheet <số>." |
| Lưu OC (`:material/tag:`) | `SAVE_OC` | Không | `save_oc(SaveOcRequest(costsheet_id=w.id, oc_no=<ô OC khối A>, close_order=False))` | thay working, toast/flash thông báo của UC (OC đã chuẩn hóa hiện lại trong ô nhờ rev) |
| Chốt đơn (`:material/verified:`) | `CLOSE_ORDER` | **Có** (câu hỏi kèm OC) | `save_oc(SaveOcRequest(costsheet_id=w.id, oc_no=<ô OC>, close_order=True))` | flash "Đã chốt đơn costsheet <số> với OC <OC>." |
| Hủy (`:material/block:`) | `CANCEL` | **Có, có ô lý do** | `cancel_costsheet(CostsheetActionRequest(costsheet_id=w.id, reason=reason))` | flash "Đã hủy costsheet <số> v<n>." |
| In nhãn (`:material/print:`) | `PRINT_LABEL` | Không (hộp thoại nhập REMARK) | 2.9.4 | tải file `nhan-<tcfno>.docx` |
| Xác nhận giá sợi hôm nay (`:material/event_available:`) | `CONFIRM_YARN_PRICES` | Không | `save_draft(build_input_request(..., confirm_yarn_prices=True))` | thay working (ngày nhập giá = hôm nay), flash thông báo |
| Sửa thông số vải (`:material/edit:`) | `EDIT_FABRIC` | Không (hộp thoại form) | 2.9.3 | |

Câu hỏi các hộp thoại (title / question / confirm_label):
- Gửi duyệt: `"Gửi duyệt"` / `f"Lưu các thay đổi và gửi duyệt costsheet {no} v{n}?"` / `"Gửi duyệt"`.
- Duyệt: `"Duyệt costsheet"` / `f"Duyệt costsheet {no} v{n}? GP% {gp}, OP% {op}."` (+ `st.warning` các cảnh báo tô màu nếu có) / `"Duyệt"`.
- Trả lại: `"Trả lại costsheet"` / `f"Trả lại costsheet {no} v{n} cho người lập?"` / `"Trả lại"`, `reason_label="Lý do trả lại"`.
- Chốt đơn: `"Chốt đơn"` / `f"Chốt đơn costsheet {no} v{n} với OC {oc}?"` / `"Chốt đơn"`.
- Hủy: `"Hủy costsheet"` / `f"Hủy costsheet {no} v{n}? Phiếu đã hủy chỉ còn xem và sao chép."` / `"Hủy phiếu"`, `reason_label="Lý do hủy"`.
Mọi `action` trả `(resp.message, resp.warning_texts)` và gọi `replace_working(resp)` (+ `state.set("cs.open_id", resp.id)`).

Không có nút nào (ví dụ SO chỉ xem phiếu Đã duyệt): `st.caption("Bạn chỉ được xem phiếu này.")`.
Lỗi khi bấm nút không hộp thoại: `show_error_list(exc)` ngay trên thanh nút (mẫu 0.9); hộp thoại: lỗi trong hộp thoại.

**`build_input_request(working, a, yarn_rows, sized_all, twist_rows, weaving, hcm, tcdn, price, cogs_rows, param_rows, confirm_yarn_prices=False) -> CostsheetInputRequest`**
(trong `components/costsheet_form.py`, chỉ ánh xạ, không tính toán):
- header từ các widget khối A (Decimal qua `dec()`; mã vải `.strip().upper()`; ô không vẽ (Giá mộc mua ngoài khi không phải
  Vải Nhuộm, F&I khi FOB/EXW/FCA) -> lấy giá trị cũ của `working.input` / 0 cho F&I).
- `yarn_lines` = mỗi dòng bảng sợi -> `YarnLineInputDTO(direction, seq, price_currency, price_input, waste_rate=from_pct(...), is_twisted, is_sized=(sized_all and direction == "WARP"))`
  (khóa dòng = `direction` + `seq`; các cột chỉ đọc bỏ qua).
- `twist_lines` = dòng bảng Se có ít nhất 1 ô khác None -> `TwistLineDTO(...)`.
- `weaving` = `WeavingInputDTO(...)`; `hcm_dyeing` / `tcdn_dyeing` = DTO của nhà máy đang chọn từ widget, nhà máy kia = `working.input.<x>` giữ nguyên; Mộc -> cả hai giữ nguyên.
- `price` = `PriceInputDTO(..., cogs_extra_lines=[CogsLineDTO(name, amount, note) cho dòng có tên hoặc số])`.
- `parameter_overrides` = `[ParameterOverrideDTO(code, used_value=from_pct nếu is_percent) for dòng nếu used != default]`.
- `costsheet_id = working.id`, `confirm_yarn_prices`.
Chỉ gọi khi `working.editable` (các nút gọi nó chỉ hiện khi editable).

### 2.9 Hộp thoại riêng của Screen 2
**2.9.1 Thêm khách hàng (UC-18)** `@st.dialog("Thêm khách hàng", icon=":material/person_add:")`:
- "Tên khách hàng" `text_input(max_chars=200)`; "Mã khách hàng (2-8 ký tự)" `text_input(max_chars=8)` (để trống = app gợi ý theo BR-50).
- Nút "Kiểm tra" -> `add_customer(AddCustomerRequest(name, customer_code, confirm_new=False))`:
  - `resp.created` -> xong (trường hợp không có tên tương tự);
  - ngược lại hiện "Tên tương tự:" `data_table(resp.similar)` cột Tên, Mã KH, Team (`selection="single"`) + `st.caption(f"Mã gợi ý: {resp.suggested_code}")`
    + nút "Dùng tên đã chọn" (đặt `cs.pending_customer` = tên đã chọn, rerun) + nút "Xác nhận tạo mới" -> `add_customer(..., confirm_new=True)`.
- Tạo xong: `state.set("cs.pending_customer", resp.customer_name)`, `set_flash(state, resp.message)` ("Đã thêm khách hàng <tên>."), `st.rerun()`.
- Lỗi (AC-31 "Khách hàng Ichimura Sangyo đã có.") hiện trong hộp thoại.

**2.9.2 Gửi duyệt / Duyệt / Trả lại / Chốt đơn / Hủy** - `confirm_dialog` (mục 0.6, câu hỏi ở 2.8).

**2.9.3 Sửa thông số vải (UC-14)** `@st.dialog("Sửa thông số vải", width="large")`:
- `st.columns(2)` "Mộc" / "Thành phẩm": Khổ (cm), Khổ cắt (cm), g/m2, g/m, Mật độ dọc, Mật độ ngang `number_input(min_value=0.0)` (seed từ `w.fabric`); "Độ co mắc (%)".
- Bảng sợi `editable_table(f.yarns, key=..., columns=["Hướng", "Tên sợi", "Tỷ lệ (%)", "Loại sợi", "Sợi gốc", "Tỷ lệ sợi gốc (%)", "T/M"], allow_add_delete=True)`
  (`Hướng` Selectbox WARP/WEFT, `Loại sợi` Selectbox "Sợi đơn"/"Sợi se").
- "Lưu và tính lại" (primary) -> `update_fabric_override(UpdateFabricOverrideRequest(costsheet_id=w.id, specs=FabricSpecsDTO(...), yarns=[FabricYarnDTO(...)]))`
  -> thay working, flash "Đã cập nhật thông số vải cho costsheet <số>.", rerun. Lỗi BR-05 / BR-47 trong hộp thoại.

**2.9.4 In nhãn (UC-26)** `components/label_dialog.py` - `@st.dialog("In nhãn thông số vải")`:
- Screen 2: 1 dòng cố định (mã vải của phiếu) + "REMARK" `text_input(max_chars=200)`.
- Nút "Tạo file nhãn" -> `file = feature.print_label(PrintLabelRequest(labels=[LabelInputDTO(tcfno, remark)]))` (trong try) ->
  `state.set("label_file", file)`; rồi `download_button(file, label="Tải file nhãn", key=..., primary=True)` (file `nhan-<tcfno>.docx`).

### 2.10 Lần đầu không có dữ liệu
`cs.open_id` = None -> ô chọn phiếu (rỗng) + panel tạo mới (2.3). Không gọi `get_costsheet`. Không lỗi.

---

## 3. Screen 3 - Việc chờ tôi (`MyTasksPage`, slug `viec-cho-toi`, menu Sales)
- title `Việc chờ tôi`, icon `📥`, description `"Những costsheet và dữ liệu đang chờ bạn xử lý."` - UC-30 `list_my_tasks`.

```
[flash]
[Chờ tôi duyệt: 3][Bị trả lại: 1][Đã duyệt chưa có OC: 2][Giá sợi hết hiệu lực: 0] (+SO: [Tỷ giá tháng này][Mã vải thiếu sợi])
┌ 📝 Chờ tôi duyệt (3) ┐ bảng chọn 1 dòng  [Mở]
┌ ↩ Bị trả lại (1) ┐ …
```
1. `show_flash`; `data = feature.list_my_tasks(EmptyRequest())` -> `data.groups: list[TaskGroupDTO(code, title, kind, rows)]`
   theo thứ tự: Chờ tôi duyệt, Bị trả lại, Đã duyệt chưa có OC, Giá sợi hết hiệu lực, (SO) Tỷ giá tháng này, Mã vải thiếu sợi.
   Backend chỉ trả nhóm thuộc vai trò của người dùng.
2. `stat_row([(g.title, len(g.rows)) for g in data.groups])` (khi có nhóm).
3. Không nhóm nào có dòng: `empty_state("Không có việc nào đang chờ bạn.")` và dừng.
4. Mỗi nhóm có dòng: `with panel(f"{g.title} ({len(g.rows)})", icon=ICON[g.code]):`
   - `kind == "costsheet"`: `picked = data_table(rows, selection="single", key=self.key(f"grid.{g.code}"))`, cột (mục 8 Screen 3):
     Số costsheet, Phiên bản (`v%d`), Khách hàng, Mã vải, Sales, Ngày tính giá (`DD/MM/YYYY`), GP% (`%.2f %%`), OP%, Lý do; `costsheet_id` ẩn.
     `st.button("Mở", icon=":material/folder_open:", key=self.key(f"open.{g.code}"), disabled=not picked)` -> `navigation.open_costsheet(self, picked[0]["costsheet_id"])`.
   - `kind == "exchange_rate"` (SO): `st.warning(row.reason)` (ví dụ "Chưa có tỷ giá tháng 11/2026.") + `self.link_to(ExchangeRatePage, label="Đi tới Tỷ giá")`.
   - `kind == "fabric"` (SO): `data_table(rows)` cột Mã vải, Lý do + `self.link_to(FabricDataPage, label="Đi tới Dữ liệu mã vải")`.
5. Nhóm rỗng không vẽ panel. Lần đầu (DB trống, chưa đăng nhập): có thể chỉ có nhóm "Tỷ giá tháng này" (dòng cảnh báo vàng) - không phải lỗi.

---

## 4. Screen 4 - Dữ liệu mã vải (`FabricDataPage`, slug `ma-vai`, menu Phòng SO)
- title `Dữ liệu mã vải`, icon `🧶`, description `"Tải dữ liệu vải Peace / WFX, tra cứu, nhập nhanh mã vải và in nhãn."`
- UC-01..UC-04, UC-26, UC-39.
- `is_so = has_any("SO")`, `can_edit = has_any("SO", "PD")`.
- `tabs = ["Tải Peace/WFX", "Tra cứu & nhập tay"]` nếu `is_so` ngược lại `["Tra cứu & nhập tay"]`;
  `st.tabs(tabs, key=self.key("tabs"), on_change="rerun")` **lazy**: `if tab.open:` (thẻ chỉ đọc + upload; kết quả kiểm tra giữ trong state).

### 4.1 Thẻ "Tải Peace/WFX" (SO)
1. `with panel("Chọn file", icon="📤", description="Chọn 1-4 file: Peace Weaving control, Peace TCFNO STANDARD, WFX Weaving_Control_Report, WFX TCFNO_Standard_Report (.xlsx / .xls)."):`
   `files = multi_file_upload("File dữ liệu vải", types=[".xlsx", ".xls"], key=self.key("files"))`
   `st.button("Kiểm tra", type="primary", icon=":material/fact_check:", disabled=not files, key=self.key("check"))` ->
   `try: preview = feature.preview_fabric_import(PreviewFabricImportRequest(files=files))` -> `state.set("fab.preview", preview)` `except AppError: show_error_list(exc)` (AC-03).
   Đổi file -> xoá `fab.preview` (so tên file với `preview.file_names`).
2. Có `preview`:
   - `st.caption` số mã đọc được theo từng file (`preview.file_counts`: "Weaving control.xlsx: 2.832 mã").
   - `stat_row([("Mới", p.new_count), ("Thay đổi", p.changed_count), ("Không đổi", p.unchanged_count), ("Thiếu sợi", p.missing_yarn_count), ("Lỗi", p.error_count)])`.
   - `only = st.toggle("Chỉ hiện mã mới / thay đổi / lỗi", value=True, key=self.key("only_changes"))`; lọc hiển thị `rows` theo `row.result in {Mới, Thay đổi, Lỗi}` (chỉ lọc hiển thị).
   - `data_table(rows)` cột: Mã vải, Tên vải, Nguồn, Kết quả, Lý do (`empty_message="Không có mã mới / thay đổi / lỗi."`).
   - `n = p.new_count + p.changed_count`; `st.button(f"Lưu {n} mã", type="primary", icon=":material/save:", disabled=n == 0, key=self.key("save"))` ->
     `confirm_dialog(..., title="Lưu dữ liệu vải", question=f"Lưu {p.new_count} mã mới và cập nhật {p.changed_count} mã? Mã đang lưu nhưng không có trong file được giữ nguyên.", confirm_label="Lưu", action=lambda _: (feature.save_fabric_import(PreviewFabricImportRequest(files=files)).message, []), on_done=lambda: state.pop("fab.preview"))`
     -> flash "Đã lưu: M mã mới, C mã cập nhật. S mã thiếu sợi cần kiểm tra."
3. `with panel("5 lần cập nhật gần nhất", icon="🕘"):` `data_table(feature.list_fabric_imports(EmptyRequest()).rows)` cột: Thời điểm (`DD/MM/YYYY HH:mm`), Người tải, Tên file,
   Mới, Thay đổi, Không đổi, Thiếu sợi, Lỗi; `empty_message="Chưa có lần cập nhật nào."`.
4. Lần đầu: chưa chọn file -> nút Kiểm tra tắt, không có kết quả, bảng nhật ký rỗng.

### 4.2 Thẻ "Tra cứu & nhập tay"
1. `with panel("Bộ lọc", icon="🔎"):` `st.columns([3, 2, 1])`:
   `st.text_input("Từ khóa", placeholder="Mã vải hoặc tên vải", key=..., persist_state="session")`;
   `st.segmented_control("Nguồn", ["Tất cả", "Peace", "WFX", "Nhập tay"], default="Tất cả", required=True, key=..., persist_state="session")` ("Tất cả" -> `source=None`);
   `st.toggle("Chỉ mã thiếu sợi", key=..., persist_state="session")`.
2. `data = feature.search_fabrics(SearchFabricsRequest(keyword, source, missing_yarn_only, selected_tcfno=None))` (cache).
   `picked = data_table(data.rows, selection="single", key=self.key("grid"), empty_message="Không tìm thấy mã vải.")`, cột:
   Mã vải, Tên vải, Nguồn, Khổ mộc, Mật độ dọc mộc, Mật độ ngang mộc, g/m mộc, Khổ TP, g/m TP, Độ co (%), Độ co mắc (%), Ngày tạo (`DD/MM/YYYY`), Cập nhật lúc (`DD/MM/YYYY HH:mm`).
   `stat_row([("Số mã", data.total)])` phía trên bảng.
3. Thanh nút `st.container(horizontal=True)`:
   - "Thêm mã vải" (`can_edit`) -> `fabric_dialog(feature, None)`;
   - "Sửa" (`can_edit`, `disabled=not picked`) -> `fabric_dialog(feature, detail)`;
   - "In nhãn" (mọi người) -> `label_dialog(feature, [picked tcfno] hoặc [])`.
4. Có `picked`: `detail = feature.search_fabrics(SearchFabricsRequest(..., selected_tcfno=picked[0]["tcfno"])).detail` ->
   `with panel(f"{detail.tcfno} - {detail.fabric_name}", icon="📄"):` bảng thông số Mộc / Thành phẩm (như 2.7.1) + `st.badge(nguồn)` + Độ co mắc + Remark;
   bảng sợi: Hướng, STT, Tên sợi đầy đủ, YCODE, Tên sợi, Tỷ lệ (%), Loại sợi, YCODE gốc, Sợi gốc, Tỷ lệ sợi gốc (%), T/M.
   Không có dòng chọn: `st.caption("Chọn 1 mã vải trong bảng để xem thông số và các dòng sợi.")`.
5. **`fabric_dialog(feature, detail | None)`** `@st.dialog("Thêm mã vải" | f"Sửa mã vải {tcfno}", width="large")`:
   - "Mã vải" text_input (tắt khi sửa), "Tên vải" text_input(300), "Độ co mắc (%)" (mặc định 10), "Ghi chú (Remark)";
   - `st.columns(2)` Mộc / Thành phẩm: Khổ, Khổ cắt, g/m2, g/m, Mật độ dọc, Mật độ ngang `number_input(min_value=0.0, value=None)`;
   - Bảng sợi `editable_table(..., columns=["Hướng", "Tên sợi", "Tỷ lệ (%)", "Loại sợi", "Sợi gốc", "Tỷ lệ sợi gốc (%)", "T/M"], allow_add_delete=True)`;
   - "Lưu mã vải" -> `save_fabric(SaveFabricRequest(is_new, tcfno, fabric_name, ..., yarns=[FabricYarnDTO(...)]))` -> flash "Đã lưu mã vải <tcfno>.", rerun;
     lỗi (BR-02, BR-05, BR-72 "Cần ít nhất 1 sợi dọc và 1 sợi ngang.", "Mã vải … đã có. Hãy dùng chức năng Sửa.") trong hộp thoại.
6. **`label_dialog(feature, tcfnos)`**: `editable_table([{"Mã vải": t, "REMARK": ""} for t in tcfnos] hoặc 1 dòng trống, columns=["Mã vải", "REMARK"], allow_add_delete=True)`
   + `st.caption("Tối đa 4 mã vải, 4 nhãn trên 1 trang.")` + "Tạo file nhãn" -> `print_label(PrintLabelRequest(labels=[LabelInputDTO(tcfno=..., remark=...)]))` ->
   `download_button(file, label="Tải file nhãn", primary=True)`. Lỗi "Mã vải <tcfno> chưa có trong dữ liệu gốc." trong hộp thoại.

---

## 5. Screen 5 - Định mức và tham số (`NormParameterPage`, slug `dinh-muc`, menu Phòng SO)
- title `Định mức và tham số`, icon `📐`, description `"Bộ định mức, bộ tham số chung, hệ số theo mã hàng và ngày lễ."` - UC-06..UC-11, UC-32..UC-34, UC-37.
- `is_so = has_any("SO")`; người khác: chỉ xem (khối tải lên / form / nút ẩn).
- `t1, t2, t3, t4 = st.tabs(["Bộ định mức", "Tham số chung", "Hệ số theo mã hàng", "Ngày lễ"], key=self.key("tabs"), on_change="rerun")`, mỗi thẻ `if tX.open:` (lazy - bảng định mức lớn).

### 5.1 Bộ định mức
1. `data = feature.view_norm_set(ViewNormSetRequest(norm_set_code=state.get("norm.code")))` (cache).
2. `with panel("Danh sách bộ định mức", icon="📚"):` `picked = data_table(data.sets, selection="single", key=self.key("norm.sets"), empty_message="Chưa có bộ định mức.")`
   cột: Mã bộ, Hiệu lực từ (`DD/MM/YYYY`), Ghi chú, Người tải, Lúc tải, Đang hiệu lực (`CheckboxColumn`). Chọn dòng -> `state.set("norm.code", code)` và `st.rerun()` khi khác code cũ
   (không chọn = bộ đang hiệu lực).
3. Có `data.selected`: `with panel(f"Các bảng của bộ {code}", icon="📊"):`
   `sheet = st.selectbox("Bảng", [t.title for t in data.selected.tables], key=self.key("norm.sheet"))` (12 bảng 4.5.1..4.5.12, nhãn ví dụ "Đơn giá theo phút (DonGiaPhut)")
   -> `data_table(table.rows, column_order=table.columns)` (dòng là dict theo tên cột của F-05; số `localized` do UI-build áp chung cho cột số).
4. SO: `with panel("Cập nhật bộ định mức", icon="⬆"):`
   - `download_button(lambda: feature.download_norm_template(EmptyRequest()), label="Tải file mẫu", key=..., file_name=f"bo-dinh-muc-{date.today():%Y%m%d}.xlsx")`;
   - `file = file_upload("Tải lên bộ định mức", types=[".xlsx"], key=...)`; `st.columns(2)`: "Ngày hiệu lực" `date_input(format="DD/MM/YYYY")`, "Ghi chú" `text_input(max_chars=300)`;
   - `st.button("Kiểm tra", disabled=file is None)` -> `preview_norm_set(SaveNormSetRequest(file, effective_from, note))` -> `state.set("norm.preview", p)` (lỗi file BR-70/BR-64 -> `show_error_list`);
   - `p`: `data_table(p.sheet_counts)` (Sheet, Số dòng); `data_table(p.changes)` (Sheet, Khóa, Cột, Giá trị cũ, Giá trị mới; trống "Không có ô thay đổi.");
     lỗi `p.errors` -> mỗi lỗi 1 dòng `st.error` (ví dụ "Sheet DinhMucDet dòng 0: thiếu sheet.", AC-36);
   - `st.button("Lưu bộ định mức", type="primary", disabled=bool(p.errors))` -> `confirm_dialog(title="Lưu bộ định mức", question=f"Lưu bộ định mức mới hiệu lực từ {d:%d/%m/%Y}? Costsheet đã gửi duyệt / đã duyệt không đổi số.", confirm_label="Lưu", action=lambda _: (feature.save_norm_set(SaveNormSetRequest(...)).message, []))`
     -> flash "Đã lưu bộ định mức <mã>, hiệu lực từ dd/mm/yyyy.", pop `norm.preview`.

### 5.2 Tham số chung
1. `data = feature.list_parameter_sets(EmptyRequest())` (cache) -> `data.sets` (Hiệu lực từ, Người lưu, Lúc lưu) và `data.latest: list[ParameterValueDTO]`.
2. `data_table(data.sets, empty_message="Chưa có bộ tham số.")`.
3. Bảng giá trị bộ mới nhất (mọi người xem): `data_table` cột Tham số, Đơn vị, Giá trị (×100 khi `is_percent`), Chỉ SO (Checkbox).
4. SO: `with st.form(self.key("param.form")):` "Ngày hiệu lực" `date_input(format="DD/MM/YYYY")` + một `st.number_input(label=f"{p.label} ({p.unit})", value=float(to_pct(p) ), format="%.4f", key=self.key(f"param.{p.code}"))` cho mỗi `p` trong `data.latest`, xếp `st.columns(3)`;
   `st.form_submit_button("Lưu bộ tham số mới", type="primary")` -> `save_parameter_set(SaveParameterSetRequest(effective_from, values=[ParameterValueInputDTO(code, value=from_pct nếu is_percent)]))`
   -> toast/flash "Đã lưu bộ tham số hiệu lực từ dd/mm/yyyy."; lỗi BR-64 / BR-65 -> `show_error_list`.
   (`data.latest` rỗng -> `empty_state("Chưa có bộ tham số.")`, không vẽ form.)

### 5.3 Hệ số theo mã hàng
1. `rows = feature.list_fabric_factors(EmptyRequest()).rows` (cache); `picked = data_table(rows, selection="single", key=..., empty_message="Chưa có hệ số theo mã hàng.")`
   cột: Mã vải, Công đoạn, Khoản mục, Hệ số nhân (`%.4f`), Cộng thêm (`localized`), Hiệu lực từ, Đang dùng (Checkbox), Ghi chú; `id` ẩn.
2. SO, thanh nút: "Thêm" -> hộp thoại form; "Sửa" (`disabled=not picked`) -> hộp thoại form điền sẵn; "Ngừng dùng" (`disabled=not picked or not picked.active`) ->
   `save_fabric_factor(SaveFabricFactorRequest(id=..., <mọi field cũ>, active=False))` -> flash.
3. Hộp thoại `@st.dialog("Hệ số theo mã hàng")`: "Mã vải" text_input, "Công đoạn" selectbox (Se / Mắc Hồ / Mắc / Cone / Dệt / Kiểm), "Khoản mục" selectbox
   (Nhân công / Khấu hao / Điện / Vật tư / Nhiên liệu / Hóa chất / CPQL), "Hệ số nhân" number_input(value=1.0, min_value=0.0001), "Cộng thêm" (0), "Hiệu lực từ" date_input,
   "Đang dùng" toggle(True), "Ghi chú"; "Lưu" -> `save_fabric_factor(...)` -> flash "Đã lưu hệ số cho mã <tcfno>.".

### 5.4 Ngày lễ
1. `rows = feature.list_holidays(EmptyRequest()).rows` (cache); `picked = data_table(rows, selection="single", key=..., empty_message="Chưa có ngày lễ.")` cột Ngày (`DD/MM/YYYY`), Tên ngày lễ.
2. SO: `with st.form(self.key("holiday.form"), clear_on_submit=True):` `st.columns(2)` "Ngày" date_input, "Tên ngày lễ" text_input(100); `form_submit_button("Thêm")` ->
   `save_holiday(SaveHolidayRequest(action=HolidayAction.ADD, date, name))` -> toast "Đã thêm ngày lễ."
3. SO: `st.button("Xóa", disabled=not picked)` -> `save_holiday(SaveHolidayRequest(action=HolidayAction.DELETE, date=picked date, name=picked name))` -> toast "Đã xóa ngày lễ." (cờ xóa, BR / UC-11).

---

## 6. Screen 6 - Tỷ giá (`ExchangeRatePage`, slug `ty-gia`, menu Phòng SO)
- title `Tỷ giá`, icon `💱`, description `"Tỷ giá VND/USD theo tháng dùng cho costsheet."` - UC-05, UC-31.
1. `show_flash`; `with st.form(self.key("form")):` `st.columns(3)`:
   "Tháng" `st.selectbox(list(range(1, 13)), index=date.today().month - 1, format_func=lambda m: f"{m:02d}")`;
   "Năm" `st.number_input(min_value=2020, max_value=2100, value=date.today().year, step=1)`;
   "Tỷ giá (VND/USD)" `st.number_input(min_value=0.0, value=None, step=10.0, format="%.2f")`;
   `st.form_submit_button("Lưu tỷ giá", type="primary", icon=":material/save:")` ->
   `try: resp = feature.save_exchange_rate(SaveExchangeRateRequest(month, year, rate))` -> `set_flash(state, resp.message)` ("Đã lưu tỷ giá tháng MM/YYYY: <tỷ giá>."), `st.rerun()` `except AppError: show_error_list(exc)` (BR-60 "Tỷ giá phải lớn hơn 0.").
   Rate None -> backend báo lỗi (không kiểm tra ở trang).
2. `with panel("Các tháng đã nhập", icon="📅"):` `data_table(feature.list_exchange_rates(EmptyRequest()).rows, empty_message="Chưa có tỷ giá nào.")`
   cột: Tháng (`%02d`), Năm (`%d`), Tỷ giá (`localized`), Người cập nhật, Lúc cập nhật (`DD/MM/YYYY HH:mm`); backend sắp mới nhất trên cùng.

---

## 7. Screen 7 - Khách hàng (`CustomerPage`, slug `khach-hang`, menu Phòng SO)
- title `Khách hàng`, icon `👥`, description `"Danh sách khách hàng dùng trong costsheet: tìm, sửa, tải danh sách ban đầu."` - UC-12, UC-13, UC-35, UC-36.
1. `show_flash`; `keyword = st.text_input("Tìm kiếm", placeholder="Tên hoặc mã khách hàng", key=..., persist_state="session")`.
2. `data = feature.list_customers(ListCustomersRequest(keyword=keyword))` (cache); `stat_row([("Khách hàng", len(data.rows))])`;
   `picked = data_table(data.rows, selection="single", key=self.key("grid"), empty_message="Chưa có khách hàng.")` cột (mục 8):
   Mã KH, Tên, Team, Người tạo, Ngày tạo (`DD/MM/YYYY`), Đang dùng (`CheckboxColumn`); `id` ẩn.
3. Thanh nút: "Sửa" (`disabled=not picked`) -> `@st.dialog("Sửa khách hàng")`: "Tên khách hàng" (200), "Mã khách hàng" (8), "Team" `segmented_control(["FS1", "FS2", "Chung"], required=True)`,
   "Đang dùng" toggle; "Lưu" -> `update_customer(UpdateCustomerRequest(id, name, customer_code, team, active))` -> flash "Đã cập nhật khách hàng <tên mới>."; lỗi BR-50 trong hộp thoại.
4. `with st.expander("Tải danh sách khách hàng", icon=":material/upload_file:", key=self.key("import"), on_change="rerun")` + `if exp.open:` (lazy):
   - `file = file_upload("File danh sách khách hàng (.xlsx)", types=[".xlsx", ".xls"], key=..., help="Cột bắt buộc: Team, Customer; cột Mã KH không bắt buộc.")`;
   - "Xem trước" (`disabled=file is None`) -> `preview_customer_import(CustomerImportRequest(file=file))` -> `state.set("cust.preview", p)`;
   - `p`: `stat_row([("Sẽ thêm", p.added), ("Bỏ qua (trùng)", p.skipped)])` + `data_table(p.rows)` cột Tên, Mã KH, Team, Kết quả ("Thêm" / "Trùng");
   - "Lưu" (primary, `disabled=p.added == 0`) -> `save_customer_import(CustomerImportRequest(file=file))` -> flash "Đã thêm N khách hàng, bỏ qua M tên trùng.", pop preview.

---

## 8. Bảng đối chiếu mục 8 của tài liệu -> thiết kế
| Mục 8 | Ở đâu |
|---|---|
| 2 nhóm menu Sales (1-3), Phòng SO (4-7) | 0.8 `menu_group` |
| Bảng danh sách chỉ xem, chọn 1 dòng | 1.5, 3.4, 4.2, 5.x, 7.2 (`data_table(selection="single")`) |
| Bảng trong costsheet sửa trong ô rồi Tính lại / Lưu nháp | 2.7.2-2.7.6, 2.8 |
| Không biểu đồ | không dùng `*_chart` |
| Hỏi lại trước Gửi duyệt, Duyệt, Trả lại, Chốt đơn, Hủy, Lưu dữ liệu vải, Lưu bộ định mức; không hỏi với Lưu nháp, Tính lại | 0.6, 2.8, 4.1, 5.1 |
| Thông báo ngắn sau mỗi thao tác | `flash.py`, `st.toast` |
| Screen 1 bộ lọc / 6 ô / bảng / 3 nút | 1 |
| Screen 2 tiêu đề + ô chọn phiếu / ô tóm tắt / form / 8 thẻ / thanh nút theo trạng thái | 2.2-2.8 |
| Screen 2 "ô tô màu cho người duyệt" | 0.4, 2.4 badge, 2.5 delta đỏ, 2.7.1 ⚑, 2.7.5 ⚑, 2.7.6 "Đã sửa", 2.6 badge độ co |
| Screen 2 "lỗi hiện thành danh sách, mỗi lỗi 1 dòng" | `show_error_list` (0.2) |
| Screen 3 các bảng theo nhóm + Mở | 3 |
| Screen 4 2 thẻ | 4 |
| Screen 5 4 thẻ | 5 |
| Screen 6 form + bảng | 6 |
| Screen 7 tìm + bảng + tải danh sách + sửa | 7 |
| Quyền theo vai trò (bảng mục 8) | quyền trang: `/admin`; trong trang: `allowed_actions` (Screen 2), `has_any` (Screen 1, 4, 5) |

---

## 9. Fields the UI expects from the backend
Tên dưới đây là đề xuất; UI-build đọc DTO thật và sửa theo. Lead: nếu backend đặt tên khác, giữ ý nghĩa.

**Enums (re-export ở `dto/common_dto.py`), giá trị = chữ tiếng Việt / mã của tài liệu:**
`RoleCode` (SALES, TRUONG_TEAM, TRUONG_DON_VI, SO, PD, FS1, FS2) + `ROLE_LABELS`;
`CostsheetStatus` (NHAP "Nháp", CHO_DUYET "Chờ duyệt", TRA_LAI "Trả lại", DA_DUYET "Đã duyệt", DA_CHOT_DON "Đã chốt đơn", HUY "Hủy", DA_THAY_THE "Đã thay thế");
`CostsheetAction` (RECALCULATE, SAVE_DRAFT, SUBMIT, APPROVE, RETURN, COPY, NEW_VERSION, SAVE_OC, CLOSE_ORDER, CANCEL, PRINT_LABEL, CONFIRM_YARN_PRICES, EDIT_FABRIC, ADD_CUSTOMER);
`DyePlant` (HCM, TCDN); `Market` (Xuất Khẩu, Nội Địa); `OrderType` (Thí Nghiệm, Sản Xuất, Dự Trữ, Gia Công); `SaleForm` (Mộc, Vải Thành Phẩm, Vải Nhuộm);
`PriceType` (FOB, CIF, EXW, CPT, CIP, FCA); `ShrinkageException` (Không, Mộc khách đã ổn định, Có pre-setting); `Currency` (USD, VND); `YarnDirection` (WARP, WEFT);
`FabricSource` (Peace, WFX, Nhập tay); `HolidayAction` (ADD, DELETE); `CustomerTeam` (FS1, FS2, Chung).

**`CostsheetOptionsResponse` (UC-38):** `customers: list[CustomerOptionDTO(name, customer_code, team)]`, `teams: list[str]`,
`sales_users: list[UserOptionDTO(username, name, team)]`, `counts: list[CountOptionDTO(fiber_system, count)]`, `twists: list[int]`,
`size_materials: list[str]`, `hcm_dye_materials`, `hcm_color_levels`, `hcm_special_stages`, `hcm_special_features`, `tcdn_dye_materials`,
`tcdn_color_levels`, `tcdn_stages`, `special_dyes`, `wr_chemicals` (đều `list[str]`; cấp màu đã gồm "Blended"), `my_roles: list[str]`, `my_team: str | None`.
Trả rỗng (không lỗi) khi DB trống.

**`ListCostsheetsRequest`:** `keyword: str = ""`, `statuses: list[CostsheetStatus] = []` (rỗng = mọi trạng thái), `team`, `sales_username`, `customer_name`,
`dye_plant`, `order_type`, `price_type` (đều optional), `date_from: date | None`, `date_to: date | None`, `latest_only: bool = True`, `below_threshold_only: bool = False`.
**`CostsheetListResponse`:** `rows: list[CostsheetListRowDTO]`, `kpis: CostsheetKpiDTO(total, pending, approved, closed, below_threshold, low_shrinkage)`.
**`CostsheetListRowDTO`:** `id, costsheet_no, version, status, costing_date, sales_name, team, customer_name, market, order_type, oc_no, tcfno, sale_form, dye_plant,
price_type, order_meters, sell_price_vnd, sell_price_usd, cogs_vnd, freight_insurance, gp_pct, op_pct (0..1), warning_text, approved_by_name, approved_at`.

**`CostsheetResponse` (mọi UC-14..UC-25, UC-29):**
- đầu phiếu: `id, costsheet_no, version, status, editable: bool, allowed_actions: list[CostsheetAction], message: str, warnings: list[WarningDTO],
  auto_approved: bool, sales_name, team, approved_by_name, approved_at, return_reason, cancel_reason, copied_from, exchange_rate, norm_set_code,
  parameter_set_date, fabric_overridden, size_suggest_reason`;
- `input: CostsheetInputDTO` - đúng các ô nhập (cùng tên field với `CostsheetInputRequest`, xem dưới) để trang gieo widget;
- `fabric: FabricSnapshotDTO(tcfno, fabric_name, source, greige_width_cm, greige_cut_width_cm, greige_gsm, greige_g_per_m, greige_warp_density,
  greige_weft_density, finished_* (6 field tương ứng), greige_m_per_kg, finished_m_per_kg, warping_loss_rate, overridden_fields: list[str], yarns: list[FabricYarnDTO])`;
- `yarn_lines: list[YarnLineViewDTO(direction, seq, yarn_name, twist_tpm, ratio, price_currency, price_input, price_vnd, price_entered_on, price_expired,
  waste_rate, is_twisted, is_sized, size_suggest_reason, loss_rate, yarn_kg, amount)]`;
- `result: CostsheetResultDTO(calculated: bool, greige_meters, finished_meters_needed, greige_kg, finished_kg, quantity_factor, shrinkage, low_shrinkage: bool,
  dye_loss_rate, yarn_ratio_total, yarn_total, twist_estimated_kg, twist_entered_kg, size_band, weaving_total, weaving_cm_price, tcdn_factor,
  dyeing_per_kg, dyeing_per_m, dyeing_total, total_cost, unit_cost_vnd, unit_cost_usd, cogs_vnd, cogs_usd, sell_price_vnd, sell_price_usd, gp, gp_pct,
  sa, op, op_pct, price_with_vat, gp_threshold, op_threshold, weaving_stages: list[StageCostDTO(stage, quantity, unit, norm, factor_applied, amount)],
  cost_items: list[CostItemRowDTO(stage, labor, depreciation, power, material, fuel, chemical, overhead, total)],
  dyeing_lines: list[DyeingLineDTO(name, chemical, labor, depreciation, power, fuel, material, overhead, factor, loss_rate, per_kg, per_m, note)],
  profit_rows: list[ProfitRowDTO(label, vnd, usd, is_percent, below_threshold)])`;
- `parameters: list[ParameterValueDTO(code, label, unit, is_percent, so_only, default_value, used_value)]` (bảng 4.6 đã trải phẳng: các ô của
  `weft_loss_table`, `quantity_factor_table` thành từng dòng có `code` riêng);
- `versions: list[VersionDTO(id, version, status, costing_date, sell_price_vnd, cogs_vnd, gp_pct, approved_by_name, approved_at)]`;
- `history: list[HistoryDTO(version, action, by_name, at, comment)]`;
- `WarningDTO(code, message, blocking: bool)`; tiện thêm `warning_texts: list[str]` (hoặc trang tự lấy `[w.message for w in resp.warnings]`).
- `similar` không có ở đây (thuộc `AddCustomerResponse`).

**`CostsheetInputRequest` (UC-16, UC-17) = `CostsheetInputDTO` + `costsheet_id: str | None`, `confirm_yarn_prices: bool = False`:**
`dye_plant, customer_name, market, order_type, style, sale_form, greige_buy_price, delivery_date, costing_date, tcfno, order_meters, price_type, oc_no,
shrinkage_exception, shrinkage_reason, note,`
`yarn_lines: list[YarnLineInputDTO(direction, seq, price_currency, price_input, waste_rate, is_twisted, is_sized)]`,
`twist_lines: list[TwistLineDTO(direction, fiber_system, count, twist, quantity_kg)]`,
`weaving: WeavingInputDTO(size_material, warping_band, cone_count_1, cone_qty_1, cone_count_2, cone_qty_2, twist_outsourcing_price, twist_outsourcing_qty,
size_outsourcing_price, weaving_outsourcing_price, other_outsourcing_price)`,
`hcm_dyeing: HcmDyeingInputDTO(dye_material, color_level, blend_ratios: list[Decimal] (5), width_type, dye_loss_rate, special_stages: list[str],
special_features: list[str], special_costs: list[NamedCostDTO(name, amount)], extra_cost: ExtraCostDTO | None, extra_cost_reason, outsourcing_lines: list[NamedCostDTO])`,
`tcdn_dyeing: TcdnDyeingInputDTO(dye_material, color_level, blend_ratios, special_dye, special_dye_chemical_price, wr_chemical,
extra_stages: list[TcdnStageInputDTO(name, chemical_price)], special_features: list[NamedCostDTO], extra_cost_type, extra_cost_loss_rate,
extra_cost: ExtraCostDTO | None, extra_cost_reason, outsourcing_lines: list[TcdnOutsourcingDTO(name, amount, loss_rate)])`,
`ExtraCostDTO(name, chemical, labor, depreciation, power, fuel, material, overhead)` (HCM: HCTN = chemical, Tiền lương = labor, Quản lý = overhead),
`price: PriceInputDTO(sell_price_currency, sell_price_input, cogs_extra_lines: list[CogsLineDTO(name, amount, note)], commission, freight_insurance, interest_cost, ship_date)`,
`parameter_overrides: list[ParameterOverrideDTO(code, used_value)]`.
Mọi số optional (ô trống = None), tỷ lệ gửi 0..1. Đổi `tcfno` -> backend lấy lại thông số + dòng sợi (dòng sợi mới thay dòng cũ).

**`CreateCostsheetRequest` (UC-15):** `dye_plant, customer_name, market, order_type, style, sale_form, greige_buy_price, delivery_date, costing_date, tcfno, order_meters, price_type, oc_no`.
**`GetCostsheetRequest` (UC-29):** `costsheet_id: str | None`, `costsheet_no: str | None`, `version: int | None` (None = mới nhất).
**`CostsheetActionRequest`:** `costsheet_id`, `reason: str | None`. **`SaveOcRequest`:** `costsheet_id, oc_no, close_order`.
**`UpdateFabricOverrideRequest` (UC-14):** `costsheet_id, specs: FabricSpecsDTO(greige_* 6, finished_* 6, warping_loss_rate), yarns: list[FabricYarnDTO]`.
**`AddCustomerRequest` / `AddCustomerResponse` (UC-18):** request `name, customer_code: str | None, confirm_new: bool`; response
`created: bool, customer_name, customer_code, suggested_code, similar: list[CustomerOptionDTO], message`.
**`PrintLabelRequest`:** `labels: list[LabelInputDTO(tcfno, remark)]` -> `FileDownloadDTO`.
**`MyTasksResponse` (UC-30):** `groups: list[TaskGroupDTO(code, title, kind: "costsheet" | "exchange_rate" | "fabric", rows: list[TaskRowDTO])]`;
`TaskRowDTO(costsheet_id, costsheet_no, version, customer_name, tcfno, sales_name, costing_date, gp_pct, op_pct, reason)` (các field không dùng = None).

**Phòng SO:**
- `FabricImportPreviewResponse`: `file_names: list[str]`, `file_counts: list[FileCountDTO(file_name, kind, count)]`, `new_count, changed_count, unchanged_count, missing_yarn_count, error_count`,
  `rows: list[FabricImportRowDTO(tcfno, fabric_name, source, result: "Mới" | "Thay đổi" | "Không đổi" | "Thiếu sợi" | "Lỗi", reason)]`. `FabricImportSaveResponse.message`.
- `FabricImportLogResponse.rows: list[FabricImportLogDTO(imported_at, imported_by, file_names, new_count, changed_count, unchanged_count, missing_yarn_count, error_count)]`.
- `SearchFabricsRequest(keyword="", source: FabricSource | None, missing_yarn_only=False, selected_tcfno: str | None)`; `SearchFabricsResponse(total, rows: list[FabricRowDTO(tcfno, fabric_name, source, greige_width_cm, greige_warp_density, greige_weft_density, greige_g_per_m, finished_width_cm, finished_g_per_m, shrinkage, warping_loss_rate, created_date, updated_at)], detail: FabricDetailDTO | None)`;
  `FabricDetailDTO` = mọi field 4.1 + `yarns: list[FabricYarnDTO(direction, seq, full_yarn_name, yarn_code, yarn_name, rate, yarn_kind, raw_yarn_code, raw_yarn_name, raw_rate, twist_tpm)]`.
- `SaveFabricRequest(is_new, tcfno, fabric_name, remark, warping_loss_rate, greige_* 6, finished_* 6, yarns)`; `SaveFabricResponse(tcfno, message)`.
- `NormSetResponse(sets: list[NormSetRowDTO(norm_set_code, effective_from, note, uploaded_by, uploaded_at, is_current)], selected: NormSetDetailDTO | None(norm_set_code, tables: list[NormTableDTO(sheet, title, columns: list[str], rows: list[dict])]))`.
- `NormSetPreviewResponse(sheet_counts: list[SheetCountDTO(sheet, rows)], changes: list[NormChangeDTO(sheet, key, column, old_value, new_value)], errors: list[str])`; `SaveNormSetResponse.message`.
- `ParameterSetListResponse(sets: list[ParameterSetRowDTO(effective_from, created_by, created_at)], latest: list[ParameterValueDTO])` (latest: `used_value` = `default_value` = giá trị bộ);
  `SaveParameterSetRequest(effective_from, values: list[ParameterValueInputDTO(code, value)])`.
- `FabricFactorListResponse.rows: list[FabricFactorDTO(id, tcfno, stage, cost_item, multiplier, addition, effective_from, active, note)]`; `SaveFabricFactorRequest(id | None, tcfno, stage, cost_item, multiplier, addition, effective_from, active, note)`.
- `HolidayListResponse.rows: list[HolidayDTO(date, name)]`; `SaveHolidayRequest(action, date, name)`.
- `ExchangeRateListResponse.rows: list[ExchangeRateDTO(month, year, rate, updated_by, updated_at)]` (mới nhất trên cùng).
- `CustomerListResponse.rows: list[CustomerDTO(id, customer_code, name, team, created_by, created_at, active)]`;
  `CustomerImportResponse(added, skipped, rows: list[CustomerImportRowDTO(name, customer_code, team, result)], message)`; `UpdateCustomerRequest(id, name, customer_code, team, active)`.
- `MessageResponse.message` cho UC-05, UC-09, UC-10, UC-11, UC-13.

**Hành vi backend mà UI dựa vào:**
1. Các use case ở mục 0.7 không raise khi DB trống / `current_user is None`.
2. `allowed_actions` đã tính theo trạng thái + vai trò + chủ phiếu + BR-47 (EDIT_FABRIC chỉ khi nguồn "Nhập tay"), AC-20/AC-27/AC-41.
3. `calculate_costsheet` không lưu và trả `CostsheetResponse` đầy đủ (input đã chuẩn hóa + kết quả + cảnh báo); khi chưa đủ dữ liệu để tính
   (ví dụ chưa có giá bán) vẫn trả response với `result.calculated=False` và cảnh báo, không raise (chỉ raise với lỗi như BR-61/BR-62).
4. Lỗi có nhiều mục (BR-42, BR-43, BR-44, BR-14 khi gửi duyệt) -> 1 `AppError` với `message` chung và `details` = list các câu.
5. `submit_costsheet` dùng dữ liệu đã lưu, nên trang gọi `save_draft` ngay trước đó trong cùng hộp thoại.

---

## 10. Giả định (thiết kế)
- G1: Thẻ của Screen 2 không lazy (giữ ô sửa trong bảng khi chuyển thẻ; nút ở cuối trang đọc được mọi thẻ). Các thẻ Screen 4, 5 và expander Screen 7 lazy.
- G2: "Gửi duyệt" = lưu nháp các ô đang nhập rồi gửi duyệt, trong 1 hộp thoại (contract `CostsheetActionRequest` chỉ có id). Nếu lead thêm input vào request gửi duyệt thì bỏ bước lưu.
- G3: Tick Hồ trên phiếu là 1 công tắc cho mọi sợi dọc (BR-09: bỏ là bỏ cho mọi sợi dọc); cột Hồ trong bảng chỉ hiển thị.
- G4: Ô "phiếu đang mở" = ô chọn số costsheet (gõ được số bất kỳ, AC-33) + ô chọn phiên bản; danh sách gợi ý lấy từ `list_costsheets` 90 ngày, phiên bản mới nhất.
- G5: "Tạo costsheet" ở Screen 1 mở Screen 2 ở chế độ tạo mới (form Thông tin đơn rút gọn); UC-15 chạy ở Screen 2.
- G6: Tô màu ô (không có CSS): badge, chữ màu, cột cờ 🟠 / 🔴 và delta đỏ ở ô tóm tắt GP% / OP%.
- G7: Tỷ lệ hiển thị theo % (nhân 100) và chia 100 khi gửi; đây là đổi đơn vị hiển thị.
- G8: Nút "Sửa thông số vải" / "In nhãn" có thể xuất hiện cả ở thẻ Thông số vải và thanh nút (khác key); UI-build được giữ 1 chỗ (thanh nút).
- G9: Người không có vai trò SO thấy Screen 4 chỉ thẻ "Tra cứu & nhập tay" (PD vẫn có Thêm / Sửa mã vải), Screen 5 chỉ xem.
- G10: Lọc "Chỉ hiện mã mới / thay đổi / lỗi" ở Screen 4 là lọc hiển thị trên kết quả kiểm tra đã nhận.
