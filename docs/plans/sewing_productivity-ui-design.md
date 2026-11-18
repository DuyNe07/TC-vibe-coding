# Thiết kế giao diện: Năng suất xưởng may (`sewing_productivity`)

Nguồn: `docs/business/sewing_productivity.md` (mục 8, khối "Giao diện đã chốt") và hợp đồng điều khiển ở
`docs/plans/sewing_productivity-implementation-plan.md`. Tên phương thức và DTO theo đúng hợp đồng. Tên trường bên trong
DTO hàng (ví dụ `OverviewMetricDTO`) hợp đồng chưa ghi, nên tài liệu này mô tả **thông tin cần có**, người làm UI đọc tên
thật trong `backend/features/sewing_productivity/dto/`.

## 0. Những gì đã kiểm tra trên bản cài đặt

Streamlit cài trong `.venv`: **1.64.0**.

| Điều cần biết | Kết quả kiểm tra | Cách kiểm tra |
|---|---|---|
| `persist_state="session"` | Có ở `date_input`, `multiselect`, `selectbox`, `segmented_control`, `pills`, `number_input`, `text_input`. Không có ở `file_uploader`, `data_editor`. Cần `key`. | `inspect.signature` + docstring |
| `date_input` có `key`, `value=` đổi sau đó | Giữ giá trị người dùng đang có, không nhảy về mặc định mới | AppTest |
| `multiselect` có `persist_state`, danh sách lựa chọn đổi làm mất mục đã chọn | Không lỗi, lựa chọn trở về rỗng | AppTest |
| `st.tabs(..., key=, on_change="rerun")` | Trả về `TabContainer`; `.open` = `[True, False]` ở lần đầu | AppTest |
| `segmented_control(required=True)`, `pills(selection_mode="multi", default=[...])`, `number_input(value=None, step=1)` | Chạy được; `number_input` trả về `None` khi trống | AppTest |
| `st.file_uploader(type=[])` | Python đổi thành `None`, tức nhận mọi loại file, không lỗi | Đọc mã + AppTest |
| `.streamlit/config.toml` `maxUploadSize` | 50 (MB) | Đọc file |
| `TextColumn(alignment=)`, `TextColumn(pinned=)`, `DateColumn(format=)`, `DatetimeColumn(format=)`, `NumberColumn(format=)`, `st.toast(duration=)`, `st.spinner(show_time=)`, `st.container(horizontal=)`, `st.dialog`, `st.space` | Có | `inspect.signature` |
| `pd.to_numeric` với `Decimal` | Ra số thực | Chạy thử |
| Ô số thiếu trong `data_table` | **Hiện chữ "None"**: `data_table` không chuyển tham số `placeholder` của `st.dataframe`, mà khung sườn thì không được sửa | Docstring + trình duyệt |
| `NumberColumn(format="localized")` | Hiện `9.5`, `1,234.5`, `126`: không cố định số lẻ và theo ngôn ngữ trình duyệt, không đạt BR-50 | Trình duyệt |
| Ô chữ căn phải, thêm dấu cách đầu cho bằng độ dài | Bấm tiêu đề sắp đúng thứ tự số, cả bảng thường và bảng `lazy` (trên 1.000 dòng): `-`, `7,25 🔴`, `9,50 🔴`, `26,56`, `30,00`, `84,90 🔴`, `85,00`, `126,00`, `1.000,00`, `1.234,50` | Trình duyệt, bảng thử chạy riêng ngoài repo, đã xoá |

**Không chạy thử:** chưa có trang thật và DTO thật nên chưa chạy `@st.dialog`, tab giữ nguyên sau `st.rerun()`, và việc mất
người dùng trong lần chạy riêng của hộp thoại (mục 1.5 suy ra từ mã `frontend/core/auth.py`). Người làm UI kiểm tra ở bước
chạy app.

## 1. Quy tắc chung (áp cho mọi màn hình)

### 1.1 Manifest
`frontend/features/sewing_productivity/manifest.py`, thay trang mẫu của scaffold:
`FeatureManifest(key="sewing_productivity", title="Năng suất xưởng may", description="Theo dõi và phân tích năng suất các xưởng may theo khoảng thời gian bất kỳ.", icon="🧵", group="Sản xuất", owner="Nhóm PI - SO", roles=(("UPDATER", "Người cập nhật dữ liệu"),), pages=(OverviewPage, LineDetailPage, DailyReportPage, MonthlyReportPage, LineMoPage, ChangeoverPage, DataUpdatePage, GoalsPage, CatalogsPage))`

| # | Lớp trang | Slug | Tiêu đề | Icon | `menu_group` | Mô tả |
|---|---|---|---|---|---|---|
| 1 | `OverviewPage` | (không, trang đầu) | Tổng quan | 📊 | Báo cáo | So sánh 4 xưởng theo khoảng thời gian. |
| 2 | `LineDetailPage` | `line-detail` | Chi tiết chuyền | 🧵 | Báo cáo | Xem từng chuyền theo ngày. |
| 3 | `DailyReportPage` | `daily` | Báo cáo ngày | 📅 | Báo cáo | Xem kết quả một ngày. |
| 4 | `MonthlyReportPage` | `monthly` | Báo cáo tháng | 🗓️ | Báo cáo | Xem từng xưởng theo ngày. |
| 5 | `LineMoPage` | `line-mo` | MO theo chuyền | 💵 | Báo cáo | Xem MO 8h của từng chuyền theo ngày. |
| 6 | `ChangeoverPage` | `changeover` | Đổi mã hàng | 🔄 | Báo cáo | Theo dõi KPI đổi mã hàng và số lần đổi gồm cả lên lại. |
| 7 | `DataUpdatePage` | `data-update` | Cập nhật dữ liệu | 📤 | Quản lý dữ liệu | Tải file dữ liệu và nhập đổi mã hàng tuần. |
| 8 | `GoalsPage` | `goals` | Mục tiêu và ngưỡng | 🎯 | Quản lý dữ liệu | Xem và đổi mục tiêu, ngưỡng theo ngày hiệu lực. |
| 9 | `CatalogsPage` | `catalogs` | Danh mục | 🗂️ | Quản lý dữ liệu | Sửa các danh mục dùng để làm sạch dữ liệu. Sửa xong áp dụng ngay cho toàn bộ dữ liệu. |

### 1.2 Ô số và dấu 🔴 (BR-28, BR-50)
Bảng báo cáo cần đồng thời: hiện `-` khi thiếu số, định dạng Việt Nam với số lẻ cố định, có 🔴 cạnh con số, sắp xếp theo số.
Cột số (`NumberColumn`) không làm được 3 điều đầu (mục 0), nên **mọi cột số của bảng báo cáo là ô chữ căn phải có đệm dấu
cách**. Không dùng cột dấu riêng. Làm như vậy đúng với quyết định "Dấu 🔴 đặt cạnh con số trong bảng", tìm được 🔴 bằng ô tìm kiếm
của bảng, và vẫn sắp theo số.

Hàm dùng chung, đặt ở `frontend/features/sewing_productivity/components/report_cells.py`, là hàm thường, không có lớp:

- `number_cells(values, decimals, suffix="", flags=None) -> list[str]`: định dạng **cả cột** trong một lần.
  1. Mỗi giá trị: `format_number(value, decimals) + suffix` (`frontend.core.formatting`); `None` thành `-` và không có `suffix`.
  2. `rjust` bằng dấu cách thường cho bằng độ dài dài nhất của cột, tính cả dòng Cả kỳ và Tổng. Phải là dấu cách thường
     (U+0020): nó xếp trước chữ số, nên `-` đứng thấp nhất.
  3. Đệm xong mới nối ` 🔴` vào cuối các ô có `flags[i]` đúng. Nối trước khi đệm sẽ làm sai độ dài và sai thứ tự sắp xếp.
- `right_text_columns(names) -> dict`: `{name: st.column_config.TextColumn(alignment="right") for name in names}`, ghép vào `column_config` của `data_table`.

Việc so ngưỡng thuộc backend: trang chỉ đọc cờ "dưới ngưỡng" trong DTO, không tự so sánh (rules/04, quy tắc 1). Giá trị hiển
thị chỉ làm tròn khi định dạng.

| Bảng | 🔴 đặt ở đâu | Cột có 🔴 | Sắp theo số |
|---|---|---|---|
| S1 bảng chỉ số | Trong ô chữ, không đệm | Dòng Hiệu suất A, Hiệu suất B, MO 8h | Không cần: mỗi cột trộn nhiều đơn vị |
| S2 bảng chuyền | Trong ô chữ có đệm | Hiệu suất A, Hiệu suất B, MO 8h | Có |
| S2 bảng xưởng theo ngày | Không có | | Có |
| S3 bảng xưởng | Trong ô chữ, không đệm | Dòng Hiệu suất A, Hiệu suất B, MO 8h | Không cần |
| S3 bảng chuyền | Trong ô chữ có đệm | MO 8h | Có |
| S4 mỗi xưởng | Trong ô chữ có đệm | MO 8h, Hiệu suất B | Có |
| S5 thẻ MO 8h, Hiệu suất B | Trong ô chữ có đệm, từng cột ngày đệm riêng | Mọi cột ngày và Cả kỳ, dòng Tổng | Có |
| S5 thẻ Tiền CM, Giờ làm, Số người | Không có | | Có |
| S6 mọi thẻ | Không có | | Có |

Định dạng số (BR-50). Hai dòng cuối do tài liệu không ghi, xem Giả định.

| Loại | `decimals` | `suffix` |
|---|---|---|
| Sản lượng, Mục tiêu A, Mục tiêu B, Mục tiêu sản lượng, Sản lượng trái sở trường, các số đếm | 0 | |
| Hiệu suất A/B, Mục tiêu hiệu suất, Ngưỡng hiệu suất, % so với mục tiêu, Tỷ lệ đúng sở trường | 1 | `%` |
| Tiền CM, Giá CM, Giá CM trung bình, MO, MO 8h, Target MO 8h, Mục tiêu và Ngưỡng MO 8h, Giờ làm, Giờ làm trung bình | 2 | |
| KPI đổi mã hàng | 3 | |
| Số người, Số thợ (giả định) | 1 | |
| SMV, Đổi mã hàng tuần trên chuyền (giả định) | 2 | |

Nếu DTO trả tỷ lệ dạng `0.918` thì nhân 100 khi hiển thị; nếu trả `91.8` thì giữ nguyên. Đọc DTO thật và đối chiếu AC-20.

Cột ngày:
- Bảng **không có** dòng Cả kỳ/Tổng: giá trị `date` thật, `st.column_config.DateColumn(format="DD/MM/YYYY")`, sắp đúng.
- Bảng **có** dòng Cả kỳ/Tổng (S2 bảng chuyền, S4): ô chữ `DD/MM/YYYY`, vì `None` sẽ hiện "None". Backend đã sắp sẵn.

Giới hạn đã biết: bấm tiêu đề cột `Ngày` của S2, S4 hoặc cột `Chuyền` sẽ sắp theo chữ (`01/11` trước `24/10`, `LINE 10` trước
`LINE 2`), và dòng Cả kỳ/Tổng đi theo thứ tự mới. Không đệm tên chuyền vì tìm "LINE 2" sẽ không ra. Thứ tự mặc định vẫn đúng
theo số chuyền rồi ngày. Khi tải CSV từ biểu tượng của bảng, ô số còn dấu cách đầu; file chính thức là nút "Tải Excel".

Chiều cao: bảng cố định số dòng (S1 17 dòng, S3 11 dòng) đặt `height=(số dòng + 1) * 35 + 3` để không có thanh cuộn. Bảng dài
(S2 bảng chuyền, S4, S5, S6 thẻ Chi tiết) đặt `height=520`. Bảng còn lại để mặc định.

### 1.3 Bộ lọc báo cáo
Đặt ở `components/report_filters.py`. Mọi màn hình báo cáo mở đầu bằng:

1. `options = feature.get_filter_options(EmptyRequest())` (UC-26, không có quyền riêng, không báo lỗi khi chưa có dữ liệu).
2. Nếu `not options.has_data`: `empty_state("Chưa có dữ liệu. Người cập nhật cần tải file ở màn hình Cập nhật dữ liệu.")` rồi `return` (AC-45). Không vẽ bộ lọc, không gọi use case nào khác.
3. `with panel("Bộ lọc", icon="🔎"):` các ô lọc của màn hình.
4. `st.caption(f"Dữ liệu mới nhất: {latest_date:%d/%m/%Y} · Lần tải file gần nhất: {format_datetime(last_upload_at)}")` ngay dưới panel.

Ô lọc, tất cả có `persist_state="session"` và `key=self.key("...")`:

| Ô lọc | Lời gọi | Mặc định |
|---|---|---|
| Từ ngày | `st.date_input("Từ ngày", value=<BR-31>, format="DD/MM/YYYY", key=self.key("from_date"), persist_state="session")` | S1, S2 `default_week_from`; S4, S5, S6 `default_month_from` |
| Đến ngày | `st.date_input("Đến ngày", value=<BR-31>, format="DD/MM/YYYY", key=self.key("to_date"), persist_state="session")` | S1, S2 `default_week_to`; S4, S5, S6 `latest_date` |
| Ngày (S3) | `st.date_input("Ngày", value=options.latest_date, format="DD/MM/YYYY", key=self.key("report_date"), persist_state="session")` | `latest_date` |
| Xưởng, chọn nhiều | `st.pills("Xưởng", options.factories, selection_mode="multi", default=list(options.factories), key=self.key("factories"), persist_state="session")` | Tất cả. Bỏ chọn hết cũng tính là tất cả: gửi `options.factories` |
| Xưởng, một xưởng | `st.segmented_control("Xưởng", options.factories, default="Fac 1", required=True, key=self.key("factory"), persist_state="session")` | Fac 1 |
| Chuyền | `st.multiselect("Chuyền", <danh sách>, placeholder="Tất cả", key=self.key("lines"), persist_state="session")` | Rỗng = tất cả, gửi `[]` |
| Nhóm khách hàng | `st.multiselect("Nhóm khách hàng", options.customer_groups, placeholder="Tất cả", key=self.key("customer_groups"), persist_state="session")` | Rỗng = không lọc, gửi `[]` |
| Nhóm sản phẩm | `st.multiselect("Nhóm sản phẩm", options.product_groups, placeholder="Tất cả", key=self.key("product_groups"), persist_state="session")` | Rỗng = không lọc, gửi `[]` |

Hai nhóm lọc mặc định rỗng chứ không chọn sẵn tất cả, vì BR-29 làm nhiều chỉ số thành `-` khi đang lọc: chọn sẵn tất cả sẽ bị
hiểu là đang lọc. `key` được ghép với `self.key` nên 6 trang không dùng chung giá trị.

Sau khi tải file mới, bộ lọc đã giữ trong phiên vẫn là khoảng cũ, đó là đúng yêu cầu "giữ bộ lọc khi quay lại". AC-46 và AC-52
nói về lần mở đầu của phiên.

### 1.4 BR-30 và nút Tải Excel
Mọi nút xuất dùng `download_button(lambda: feature.export_xxx(request), label=..., key=..., file_name=..., primary=True)`.
Hàm này chạy ngoài màn hình khi người dùng bấm, nên export không được phép báo lỗi (rules/04). Cách bảo đảm:

1. Mọi trang gọi **use case xem báo cáo trước**, ngay trong `render()`, không `try`. Từ ngày sau đến ngày thì use case đó báo BR-30, `BasePage` hiện đúng thông báo (AC-42) và dừng trang; bộ lọc đã vẽ ở trên vẫn còn để sửa.
2. Nút xuất nằm **sau** lời gọi đó trong mã, và chỉ vẽ khi `has_data`. Vì vậy khi khoảng ngày sai, nút không tồn tại. Trang không tự so sánh ngày (BR-30 thuộc backend).
3. `file_name` do trang dựng phải trùng tên backend đặt, vì đường đi này bỏ qua `FileDownloadDTO.filename`. Khi làm trang, đọc `builders/` để lấy đúng dạng ngày (và dạng tên xưởng của file MO).

Tính báo cáo có thể chậm ở lần đầu, nên bọc lời gọi xem báo cáo bằng `with st.spinner("Đang tính báo cáo..."):`. Các lần sau kết quả lấy từ RAM (`@cached_query`).

### 1.5 Phân quyền ở S7, S8, S9 (BR-09)
UC-03, UC-16, UC-18, UC-21 có thể báo BR-09. Quyền mở màn hình và vai trò `UPDATER` được cấp riêng trên `/admin`, nên có thể có người
mở được trang mà chưa có vai trò. Trang **không tự xét vai trò**, backend quyết định:

```
try:
    data = feature.<use case đọc>(EmptyRequest())
except AppError as exc:
    st.warning(exc.message, icon=":material/lock:")
    return
```

Lời gọi này là việc đầu tiên trong `render()`. Khi không có quyền, trang chỉ hiện đúng dòng BR-09 dạng cảnh báo, không có hộp lỗi đỏ
và không có khối nào khác. Các use case này không có lỗi nào khác ngoài BR-09, nên bắt `AppError` là đủ. Khi kiểm thử không có người
dùng (`None`), backend cho phép, trang hiện bình thường với danh sách rỗng.

Hộp thoại: `@st.dialog` chạy lại riêng như một fragment, không qua `AppShell` là nơi đặt người dùng hiện tại, và cũng không nằm trong
`BasePage.run()`. Nên **không gọi use case ghi trong hộp thoại**. Nút xác nhận chỉ ghi cờ vào `self.state` rồi `st.rerun()`; lần chạy đầy đủ
sau đó mới gọi use case ở `render()`. Nhờ vậy `uploaded_by` và BR-09 thấy đúng người, và lỗi được xử lý như mọi nơi khác.

### 1.6 Thông báo sau khi lưu
Lưu xong là `st.rerun()` để bảng ở phía trên form được đọc lại. Thông báo giữ qua lần chạy lại bằng `self.state.set("flash", message)`;
đầu `render()` lấy ra bằng `self.state.pop("flash", None)` và gọi `st.toast(message, icon=":material/check:", duration="long")`.
Riêng lưu file (S7) dùng `show_success` để thông báo nằm yên, xem S7.

Các ô nhập trong form **không đặt `min_value`** và bảng danh mục **không đặt `required`, `validate`**: nếu không, trình duyệt chặn trước và
không bao giờ hiện thông báo BR-39, BR-45, BR-47 (AC-28, AC-32, AC-48).

## 2. Screen 1: Tổng quan (`OverviewPage`)

```
┌ Bộ lọc ───────────────────────────────────────────────────────┐
│ [Từ ngày] [Đến ngày] (Fac 1)(Fac 2)(Fac 3)(Fac 5)              │
│ [Nhóm khách hàng ▼ Tất cả]   [Nhóm sản phẩm ▼ Tất cả]          │
└───────────────────────────────────────────────────────────────┘
Dữ liệu mới nhất: 04/11/2026 · Lần tải file gần nhất: 05/11/2026 08:30
ⓘ Hiệu suất A chỉ tính từ 03/10/2026.            (chỉ khi có ghi chú)
┌ Chỉ số theo xưởng ────────────────────────────────────────────┐
│ Chỉ số        | Fac 1    | Fac 2   | Fac 3  | Fac 5           │
│ Hiệu suất A   | 91,8% 🔴 | 98,8%   | ...                      │
└───────────────────────────────────────────────────────────────┘
[Tải Excel báo cáo tuần]
┌ Hiệu suất A theo ngày ┐ ┌ Hiệu suất B theo ngày ┐
┌ MO 8h theo ngày       ┐ ┌ Sản lượng so với mục tiêu A ┐
Chỉ số xếp hạng: (Hiệu suất B)(Hiệu suất A)(MO 8h)
┌ 10 chuyền cao nhất    ┐ ┌ 10 chuyền thấp nhất   ┐
```

Không có ô số liệu.

1. Mục 1.3: panel Bộ lọc gồm hàng 1 `st.columns([1, 1, 2])`: Từ ngày, Đến ngày, Xưởng (chọn nhiều). Hàng 2 `st.columns(2)`: Nhóm khách hàng, Nhóm sản phẩm. Dòng thời điểm dữ liệu.
2. `data = feature.get_overview(OverviewRequest(from_date, to_date, factories, customer_groups, product_groups))`.
3. `data.has_data` sai: `empty_state("Chưa có dữ liệu trong khoảng thời gian này.")`, `return`.
4. `data.note` có giá trị: `st.info(data.note, icon=":material/info:")`.
5. `with panel("Chỉ số theo xưởng", icon="📋"):` `data_table(rows, column_config=..., height=(17 + 1) * 35 + 3, key=self.key("metrics"))`. Một dòng mỗi chỉ số.
   - Cột: `Chỉ số` (`TextColumn(pinned=True)`), rồi các xưởng đang chọn theo thứ tự Fac 1, Fac 2, Fac 3, Fac 5, căn phải.
   - Thứ tự dòng và định dạng (mục 1.2), ô tạo bằng `format_number`, không đệm:
     Mục tiêu A; Sản lượng; Mục tiêu hiệu suất; Hiệu suất A 🔴; % so với mục tiêu của hiệu suất A; Mục tiêu B; Hiệu suất B 🔴; % so với mục tiêu của hiệu suất B; Tiền CM; Mục tiêu MO 8h; MO 8h 🔴; % so với mục tiêu của MO 8h; Giá CM trung bình; Giờ làm trung bình; Tỷ lệ đúng sở trường; Đổi mã hàng tuần; Đổi mã hàng tuần trên chuyền.
6. `download_button(lambda: feature.export_weekly_report(ExportWeeklyRequest(from_date, to_date, factories, customer_groups, product_groups)), label="Tải Excel báo cáo tuần", key=self.key("export"), primary=True, file_name=<bao-cao-tuan_<từ ngày>_<đến ngày>.xlsx>)`. Tạo request trước, ngoài `lambda`.
7. Biểu đồ. Nút chọn chỉ số nằm dưới 4 biểu đồ nhưng `get_charts` cần giá trị của nó, nên tạo khung trước theo thứ tự nhìn thấy:
   `chart_area = st.container()`, `rank_area = st.container()`. Vẽ theo thứ tự:
   - `with rank_area:` `metric = st.segmented_control("Chỉ số xếp hạng", ["Hiệu suất B", "Hiệu suất A", "MO 8h"], default="Hiệu suất B", required=True, key=self.key("ranking_metric"), persist_state="session")`.
   - `charts = feature.get_charts(ChartsRequest(from_date, to_date, factories, customer_groups, product_groups, ranking_metric=metric))`, đổi nhãn sang giá trị backend cần.
   - `with chart_area:` 2 hàng `st.columns(2)`, mỗi ô một `panel`:
     | Khối | Lời gọi |
     |---|---|
     | Hiệu suất A theo ngày | `line_chart(rows, x="Ngày", y="Hiệu suất A (%)", color="Xưởng", key=self.key("chart_eff_a"), empty_message=...)` |
     | Hiệu suất B theo ngày | `line_chart(rows, x="Ngày", y="Hiệu suất B (%)", color="Xưởng", key=self.key("chart_eff_b"), empty_message=...)` |
     | MO 8h theo ngày | `line_chart(rows, x="Ngày", y="MO 8h", color="Xưởng", key=self.key("chart_mo8h"), empty_message=...)` |
     | Sản lượng so với mục tiêu A giữa các xưởng | `bar_chart(rows, x="Xưởng", y=["Sản lượng", "Mục tiêu A"], stacked=False, key=self.key("chart_output"), empty_message=...)` |
   - `with rank_area:` `st.columns(2)`: `panel("10 chuyền cao nhất")` và `panel("10 chuyền thấp nhất")`, mỗi khối `bar_chart(rows, x="Chuyền", y=<nhãn chỉ số>, stacked=False, key=..., empty_message=...)`.
   - `empty_message` = `"Chưa có dữ liệu trong khoảng thời gian này."`.
   - `charts.not_applicable_message` có giá trị: 3 khối Hiệu suất A, MO 8h, Sản lượng so với mục tiêu A hiện `st.info(message)` thay cho biểu đồ (AC-41). Khi xếp hạng không có dòng nào và có thông báo này: 2 khối xếp hạng cũng hiện thông báo đó.

Lưu ý với `charts.py`, để không vẽ sai số:
- `to_long` đổi ô trống thành **0**. **Bỏ hẳn các điểm `None`** khỏi dòng trước khi vẽ, nếu không đường tụt về 0 ở ngày có `-`.
- `prepare_bars`, `prepare_lines` **cộng dồn theo `x`**. Xếp hạng chuyền trải trên nhiều xưởng, `LINE 1` của Fac 1 và Fac 2 sẽ bị cộng nếu `x` chỉ là tên chuyền. Đặt `x` = `"<xưởng> · <chuyền>"`.
- Đổi sang `float`, làm tròn theo BR-50 cho ô hiện khi rê chuột. Thứ tự cột giữ theo dòng backend trả về. Dùng cột dọc như "Giao diện đã chốt": cột ngang sẽ đẩy hạng 1 xuống dưới cùng.

## 3. Screen 2: Chi tiết chuyền (`LineDetailPage`)

```
┌ Bộ lọc ──────────────────────────────────────────────────┐
│ [Từ ngày] [Đến ngày] (Fac 1|Fac 2|Fac 3|Fac 5)           │
│ [Chuyền ▼ Tất cả] [Nhóm khách hàng ▼] [Nhóm sản phẩm ▼]  │
└──────────────────────────────────────────────────────────┘
Dữ liệu mới nhất: ... · Lần tải file gần nhất: ...
┌ Chuyền theo ngày ────────────────────────────────────────┐
│ Chuyền | Ngày | Mục tiêu A | Sản lượng | Hiệu suất A | ...│
│ LINE 1 | 24/10/2026 | ... | 91,8% 🔴 | ... | 26,56 🔴     │
│ LINE 1 | Cả kỳ ...                                        │
│ Tổng   | Cả kỳ ...                                        │
└──────────────────────────────────────────────────────────┘
┌ Thông tin xưởng theo ngày: Ngày | Số thợ | Giờ làm ──────┐
[Tải Excel báo cáo tuần]
```

1. Mục 1.3. Hàng 1 `st.columns([1, 1, 2])`: Từ ngày, Đến ngày, Xưởng (một xưởng). Hàng 2 `st.columns(3)`: Chuyền (`options.lines_by_factory.get(factory, [])`), Nhóm khách hàng, Nhóm sản phẩm. Đổi xưởng thì lựa chọn Chuyền tự về rỗng (mục 0).
2. `data = feature.get_line_detail(LineDetailRequest(from_date, to_date, factory, lines, customer_groups, product_groups))`.
3. `has_data` sai: `empty_state("Chưa có dữ liệu trong khoảng thời gian này.")`, `return`. `data.note` có: `st.info`.
4. `with panel("Chuyền theo ngày", icon="🧵"):` `data_table(rows, column_config=..., height=520, key=self.key("lines_table"))`, chỉ xem, giữ thứ tự backend (số chuyền rồi ngày, dòng Cả kỳ của từng chuyền, dòng Tổng xưởng).
   | Cột | Ô |
   |---|---|
   | Chuyền | `TextColumn(pinned=True)` |
   | Ngày | chữ `DD/MM/YYYY`, hoặc `Cả kỳ` |
   | Mục tiêu A | đệm, 0 lẻ |
   | Sản lượng | đệm, 0 lẻ |
   | Hiệu suất A | đệm, 1 lẻ, `%`, 🔴 |
   | Mục tiêu B | đệm, 0 lẻ |
   | Hiệu suất B | đệm, 1 lẻ, `%`, 🔴 |
   | Tiền CM | đệm, 2 lẻ |
   | Số người | đệm, 1 lẻ |
   | Giờ làm | đệm, 2 lẻ |
   | MO 8h | đệm, 2 lẻ, 🔴 |
5. `with panel("Thông tin xưởng theo ngày", icon="🏭"):` `data_table(rows, column_config=..., key=self.key("factory_days"))`. Cột: Ngày (`DateColumn(format="DD/MM/YYYY")`), Số thợ (đệm, 1 lẻ), Giờ làm (đệm, 2 lẻ).
6. Nút như S1 bước 6, với `factories=[factory]` và `key=self.key("export")`. Hợp đồng `ExportWeeklyRequest` không có `lines`: khi đang chọn chuyền, thêm `st.caption("File Excel gồm mọi chuyền của xưởng đã chọn.")`.

## 4. Screen 3: Báo cáo ngày (`DailyReportPage`)

```
┌ Bộ lọc: [Ngày] ───────────────────────────┐
Dữ liệu mới nhất: ... · Lần tải file gần nhất: ...
┌ Chỉ số theo xưởng ────────────────────────┐
│ Chỉ số | Fac 1 | Fac 2 | Fac 3 | Fac 5    │
└───────────────────────────────────────────┘
┌ Chuyền trong ngày ────────────────────────┐
│ Xưởng: (Fac 1|Fac 2|Fac 3|Fac 5)          │
│ Chuyền | Sản lượng | Tiền CM | ... | Tổng │
└───────────────────────────────────────────┘
[Tải Excel]
```

1. Mục 1.3: panel Bộ lọc chỉ có ô Ngày. Dòng thời điểm dữ liệu.
2. Ô Xưởng nằm dưới bảng xưởng nhưng `get_daily_report` cần nó: `metrics_area = st.container()`, `lines_area = st.container()`. Vẽ trong `lines_area` trước: `with panel("Chuyền trong ngày", icon="🧵"):` ô Xưởng (một xưởng).
3. `data = feature.get_daily_report(DailyReportRequest(report_date, factory))`.
4. `has_data` sai: `empty_state("Chưa có dữ liệu của ngày này.")`, `return`.
5. `with metrics_area, panel("Chỉ số theo xưởng", icon="📋"):` `data_table(rows, column_config=..., height=(11 + 1) * 35 + 3, key=self.key("metrics"))`. Cột `Chỉ số` (`pinned`), 4 xưởng căn phải. Dòng theo thứ tự: MO; Giờ làm; Target MO 8h; MO 8h 🔴; % so với Target MO 8h; Mục tiêu sản lượng; Sản lượng; Hiệu suất A 🔴; Hiệu suất B 🔴; Tỷ lệ đúng sở trường; Số thợ.
6. Tiếp trong khối Chuyền: `data_table(rows, column_config=..., key=self.key("lines_table"), empty_message="Chưa có dữ liệu của ngày này.")`. Cột: Chuyền; Sản lượng (đệm, 0); Tiền CM (đệm, 2); Giờ làm (đệm, 2); Số người (đệm, 1); MO (đệm, 2); MO 8h (đệm, 2, 🔴); Sản lượng trái sở trường (đệm, 0). Dòng cuối Tổng. Fac 1 hiện chung một bảng.
7. `download_button(lambda: feature.export_daily_report(ExportDailyRequest(report_date)), label="Tải Excel", key=self.key("export"), primary=True, file_name=<bao-cao-ngay_<ngày>.xlsx>)`. Vẽ sau `lines_area`, xuất cho cả 4 xưởng (UC-12).

## 5. Screen 4: Báo cáo tháng (`MonthlyReportPage`)

```
┌ Bộ lọc: [Từ ngày] [Đến ngày] (Fac 1)(Fac 2)(Fac 3)(Fac 5) ┐
Dữ liệu mới nhất: ... · Lần tải file gần nhất: ...
┌ Fac 1 ────────────────────────────────────────────────────┐
│ Ngày | MO | Giờ làm | MO 8h | Mục tiêu B | Sản lượng | ... │
│ Tổng | ...                                                │
└───────────────────────────────────────────────────────────┘
┌ Fac 2 ... ┐
[Tải Excel]
```

1. Mục 1.3: `st.columns([1, 1, 2])`: Từ ngày, Đến ngày, Xưởng (chọn nhiều). Dòng thời điểm dữ liệu.
2. `request = MonthlyReportRequest(from_date, to_date, factories)`; `data = feature.get_monthly_report(request)`.
3. `has_data` sai: `empty_state("Chưa có dữ liệu trong khoảng thời gian này.")`, `return`.
4. Mỗi `MonthlyFactoryDTO`: `with panel(<tên xưởng>, icon="🏭"):` `data_table(rows, column_config=..., height=520, key=self.key(f"table_{factory}"), empty_message="Chưa có dữ liệu trong khoảng thời gian này.")`.
   Cột: Ngày (chữ `DD/MM/YYYY` hoặc `Tổng`); MO (đệm, 2); Giờ làm (đệm, 2); MO 8h (đệm, 2, 🔴); Mục tiêu B (đệm, 0); Sản lượng (đệm, 0); Hiệu suất B (đệm, 1, `%`, 🔴); Tiền CM (đệm, 2); Số thợ (đệm, 1). Dòng cuối Tổng theo BR-48.
5. `download_button(lambda: feature.export_monthly_report(request), label="Tải Excel", key=self.key("export"), primary=True, file_name=<bao-cao-thang_<từ ngày>_<đến ngày>.xlsx>)`.

## 6. Screen 5: MO theo chuyền (`LineMoPage`)

```
┌ Bộ lọc: [Từ ngày] [Đến ngày] (Fac 1|Fac 2|Fac 3|Fac 5) [Chuyền ▼] ┐
Dữ liệu mới nhất: ... · Lần tải file gần nhất: ...
[MO 8h] [Tiền CM] [Giờ làm] [Số người] [Hiệu suất B]
│ Chuyền | 01/11 | 02/11 | 03/11 | Cả kỳ │
│ LINE 1 | 26,56 🔴 | ...                │
│ Tổng   | ...                            │
[Tải Excel]
```

1. Mục 1.3. Hàng 1 `st.columns([1, 1, 2])`: Từ ngày, Đến ngày, Xưởng (một xưởng). Hàng 2: Chuyền (`options.lines_by_factory.get(factory, [])`). Dòng thời điểm dữ liệu.
2. `request = LineMoRequest(from_date, to_date, factory, lines)`; `data = feature.get_line_mo(request)`. Gọi **trước** các thẻ.
3. `has_data` sai: `empty_state("Chưa có dữ liệu trong khoảng thời gian này.")`, `return`.
4. `tabs = st.tabs(["MO 8h", "Tiền CM", "Giờ làm", "Số người", "Hiệu suất B"], key=self.key("tabs"), on_change="rerun")`. Mỗi thẻ: `with tab:` `if tab.open:` `data_table(rows, column_config=..., height=520, key=self.key(f"table_{index}"))`, lấy bảng tương ứng trong `data.tables`.
   - Cột: `Chuyền` (`TextColumn(pinned=True)`), mỗi ngày trong `data.dates` một cột, `Cả kỳ`. Dòng cuối Tổng.
   - Nhãn cột ngày `DD/MM`; khoảng chọn qua hai năm thì `DD/MM/YY` để không trùng tên cột. `right_text_columns` cho mọi cột ngày và Cả kỳ.
   - Mỗi cột gọi `number_cells` riêng: MO 8h (2, 🔴); Tiền CM (2); Giờ làm (2); Số người (1); Hiệu suất B (1, `%`, 🔴).
5. Sau các thẻ: `download_button(lambda: feature.export_line_mo(request), label="Tải Excel", key=self.key("export"), primary=True, file_name=<mo-theo-chuyen_<xưởng>_<từ ngày>_<đến ngày>.xlsx>)`.

## 7. Screen 6: Đổi mã hàng (`ChangeoverPage`)

```
┌ Bộ lọc: [Từ ngày] [Đến ngày] (Fac 1)(Fac 2)(Fac 3)(Fac 5) [Chuyền ▼] ┐
Dữ liệu mới nhất: ... · Lần tải file gần nhất: ...
[Theo xưởng] [Theo tháng] [Theo chuyền] [Chi tiết]
│ Xưởng | Số lần đổi KPI | Số ngày làm việc | Số chuyền | KPI đổi mã hàng | ... │
[Tải Excel]
```

1. Mục 1.3. Hàng 1 `st.columns([1, 1, 2])`: Từ ngày, Đến ngày, Xưởng (chọn nhiều). Hàng 2: Chuyền, danh sách là hợp các chuyền của xưởng đang chọn, không trùng, sắp theo số chuyền. Dòng thời điểm dữ liệu.
2. `request = ChangeoverRequest(from_date, to_date, factories, lines)`; `data = feature.get_changeover(request)`. Gọi **trước** các thẻ.
3. `has_data` sai: `empty_state("Chưa có dữ liệu trong khoảng thời gian này.")`, `return`.
4. `tabs = st.tabs(["Theo xưởng", "Theo tháng", "Theo chuyền", "Chi tiết"], key=self.key("tabs"), on_change="rerun")`, mỗi thẻ `if tab.open:` `data_table(...)`, chỉ xem. Không có 🔴.
   | Thẻ | Dữ liệu | Cột (ô đệm, số lẻ) |
   |---|---|---|
   | Theo xưởng | `by_factory` | Xưởng; Số lần đổi KPI (0); Số ngày làm việc (0); Số chuyền (0); KPI đổi mã hàng (3); Số lần đổi gồm cả lên lại (0); Đổi mã hàng tuần (0). Dòng tổng chỉ cộng số lần, ô khác `-` |
   | Theo tháng | `by_month` | Tháng (`MM/YYYY`); Xưởng; Số lần đổi KPI (0); Số ngày làm việc (0); Số chuyền (0); KPI đổi mã hàng (3); Số lần đổi gồm cả lên lại (0) |
   | Theo chuyền | `by_line` | Xưởng; Chuyền; Số lần đổi KPI (0); Số lần đổi gồm cả lên lại (0) |
   | Chi tiết | `details` | Ngày (`DateColumn(format="DD/MM/YYYY")`); Xưởng; Chuyền; Mã đơn gốc; Style; SMV (2); Giá CM (2). `height=520` |
5. Sau các thẻ: `download_button(lambda: feature.export_changeover(request), label="Tải Excel", key=self.key("export"), primary=True, file_name=<doi-ma-hang_<từ ngày>_<đến ngày>.xlsx>)`.

## 8. Screen 7: Cập nhật dữ liệu (`DataUpdatePage`)

```
┌ Bước 1 · Chọn file dữ liệu ──────────────────────────────┐
│ [Chọn file .xlsx]                     [Kiểm tra file]     │
└──────────────────────────────────────────────────────────┘
┌ Bước 2 · Kết quả kiểm tra ───────────────────────────────┐
│ Đọc được | Hợp lệ | Bị bỏ qua | Ngày đầu | Ngày cuối      │
│ So sánh với dữ liệu đang lưu                              │
│ Dòng bị bỏ qua: Sheet | Dòng | Lý do                      │
│ Cảnh báo: Loại | Ngày | Số lượng                          │
│ [Lưu dữ liệu]  → hỏi lại                                  │
└──────────────────────────────────────────────────────────┘
┌ Đổi mã hàng tuần ────────────────────────────────────────┐
│ [Từ ngày] [Đến ngày]                                      │
│ [Fac 1] [Fac 2] [Fac 3] [Fac 5]   [Lưu số đổi mã hàng]    │
└──────────────────────────────────────────────────────────┘
┌ Số đổi mã hàng đã nhập ──────────────────────────────────┐
│ ☐ Xưởng | Từ ngày | Đến ngày | Số lần | Người lưu         │
│ [Xoá dòng đã chọn]  → hỏi lại                             │
└──────────────────────────────────────────────────────────┘
┌ Lịch sử tải file ────────────────────────────────────────┐
│ Thời điểm | Người tải | Tên file | Từ ngày | Đến ngày ... │
└──────────────────────────────────────────────────────────┘
```

Thứ tự trong `render()`, khác với thứ tự nhìn thấy ở chỗ các bước 1, 2 chạy đầu:

1. `logs = feature.list_upload_logs(EmptyRequest())` trong `try` của mục 1.5. Không có quyền: cảnh báo BR-09 rồi `return`.
2. `self.state.pop("flash", None)`: có thì `st.toast` (mục 1.6).
3. `options = feature.get_filter_options(EmptyRequest())`, chỉ để lấy mặc định của form đổi mã hàng.

### Khối tải file
Trạng thái lưu qua các lần chạy lại, trong `self.state`:

| Tên | Nội dung |
|---|---|
| `upload_version` | Số, mặc định 0, ghép vào `key` của ô chọn file. Tăng lên để xoá file đã chọn |
| `check_result` | `UploadCheckResponse` của lần kiểm tra gần nhất |
| `check_error` | `AppError` khi file bị từ chối (BR-01 đến BR-04, BR-09) |
| `checked_fingerprint` | `(file.filename, len(file.content), hash(file.content))` của file đã kiểm tra |
| `do_save` | Cờ do hộp thoại xác nhận đặt |
| `save_message` | Thông báo của UC-02 |

Khối **Bước 1**, `with panel("Bước 1 · Chọn file dữ liệu", icon="📤", description="File .xlsx, tối đa 50 MB, phải được lưu từ Excel."):`

- `file = file_upload("Chọn file", types=(), key=self.key(f"upload_{version}"))`. Dùng `types=()` để nhận mọi loại file, nhờ đó file `.pdf` đi đến backend và hiện đúng thông báo BR-01 (AC-01). Nếu ghi `.xlsx`, trình duyệt chặn trước bằng câu tiếng Anh. File trên 50 MB bị `maxUploadSize` chặn trước bằng thông báo của ô tải file, không tới BR-01.
- **Đổi hoặc bỏ file:** nếu `file is None` hoặc dấu vân tay khác `checked_fingerprint` thì xoá `check_result`, `check_error`, `checked_fingerprint`. Chỉ tính dấu vân tay khi đang có kết quả, để không tốn thời gian mỗi lần chạy lại.
- `if st.button("Kiểm tra file", type="primary", disabled=file is None, key=self.key("check")):`
  - Xoá `check_result`, `check_error`, `save_message`.
  - `with st.spinner("Đang kiểm tra file, có thể mất khoảng một phút...", show_time=True):` `result = feature.check_upload(CheckUploadRequest(file=file))`.
  - Thành công: lưu `check_result` và `checked_fingerprint`. `except AppError as exc:` lưu `check_error` và `checked_fingerprint`.
- Không gọi `check_upload` ngoài nút này: UC-01 đọc cả file, không đặt ở chế độ tự kiểm tra như trang mẫu.

**Lưu** (sau khi có `file`, trước khi vẽ Bước 2). `if self.state.pop("do_save", False) and file is not None:`
- `with st.spinner("Đang lưu dữ liệu, có thể mất khoảng một phút...", show_time=True):` `saved = feature.save_upload(SaveUploadRequest(file=file))`.
- Thành công: `save_message = saved.message`, xoá `check_result`, `check_error`, `checked_fingerprint`, tăng `upload_version`, `st.rerun()`. Lần chạy sau ô chọn file trống và bảng lịch sử có bản ghi mới.
- `except AppError as exc:` lưu `check_error`, không xoá `check_result`, nên thông báo hiện trong Bước 2 và trang vẫn vẽ tiếp.

**Thông báo đã lưu:** `save_message` có giá trị thì `show_success(save_message)` ngay dưới panel Bước 1. Giữ đến lần bấm "Kiểm tra file" kế tiếp, vì việc chọn dòng ở bảng dưới cũng chạy lại trang.

Khối **Bước 2**, chỉ vẽ khi có `check_result` hoặc `check_error`. `with panel("Bước 2 · Kết quả kiểm tra", icon="🔎"):`
- `check_error`: `show_error(check_error)`. File bị từ chối thì không có `check_result`, nên không có nút Lưu (AC-01 đến AC-04).
- `check_result`:
  - `stat_row([("Số dòng đọc được", read_rows), ("Hợp lệ", valid_rows), ("Bị bỏ qua", skipped_rows), ("Ngày đầu", from_date), ("Ngày cuối", to_date)])`, số qua `format_number`, ngày dạng `DD/MM/YYYY`. Đây không phải màn hình báo cáo nên được dùng ô số liệu.
  - `st.caption(f"Trong khoảng {from_date} đến {to_date}: file có {valid_rows} dòng hợp lệ, dữ liệu đang lưu có {stored_rows_in_range} dòng.")`.
  - `section_title("Dòng bị bỏ qua")`, `data_table(rows, column_config=..., key=self.key("skipped"), empty_message="Không có dòng bị bỏ qua.")`. Cột: Sheet; Dòng (`NumberColumn(format="plain")`); Lý do (`TextColumn(width="large")`).
  - `section_title("Cảnh báo")`, `data_table(rows, column_config=..., key=self.key("warnings"), empty_message="Không có cảnh báo.")`. Cột: Loại; Ngày (chữ `DD/MM/YYYY`, không có ngày thì `-`); Số lượng (`NumberColumn(format="localized")`).
  - `if result.can_save and st.button("Lưu dữ liệu", type="primary", key=self.key("save")):` `confirm_save()`.

Hộp thoại, hàm lồng trong `render()`: `@st.dialog("Xác nhận lưu dữ liệu", icon=":material/save:")`
- Nội dung: `st.write(f"Lưu {valid_rows} dòng từ file {filename}? Dữ liệu đang lưu trong khoảng của file sẽ được thay bằng dữ liệu trong file. Dữ liệu ngoài khoảng giữ nguyên.")`.
- `with st.container(horizontal=True):` nút "Lưu" (`type="primary"`, `key=self.key("save_yes")`) đặt `do_save` rồi `st.rerun()`; nút "Huỷ" (`key=self.key("save_no")`) chỉ `st.rerun()`. Không gọi `save_upload` ở đây (mục 1.5).

### Khối đổi mã hàng tuần
`with panel("Đổi mã hàng tuần", icon="🔄", description="Để trống ô của xưởng nào thì không lưu xưởng đó."):` `with st.form(self.key("weekly_form"), border=False):`
- `st.columns(2)`: `st.date_input("Từ ngày", value=options.default_week_from or date.today(), format="DD/MM/YYYY", key=self.key("weekly_from"))`; `st.date_input("Đến ngày", value=options.default_week_to or date.today(), format="DD/MM/YYYY", key=self.key("weekly_to"))`. Chưa có dữ liệu thì mặc định hôm nay.
- `st.columns(4)`: 4 ô `st.number_input("Fac 1", value=None, step=1, placeholder="Để trống", key=self.key("weekly_fac_1"))`, tương tự Fac 2, Fac 3, Fac 5. Danh sách 4 xưởng cố định theo tài liệu, đặt hằng trong `components/`, vì `options.factories` rỗng khi chưa có dữ liệu.
- `st.form_submit_button("Lưu số đổi mã hàng", type="primary")` → `feature.save_weekly_changeovers(SaveWeeklyChangeoversRequest(from_date, to_date, counts={"Fac 1": ..., "Fac 2": ..., "Fac 3": ..., "Fac 5": ...}))`, **không hỏi lại**.
  - Thành công: `flash = result.message`, tăng `weekly_version`, `st.rerun()`.
  - `except AppError as exc:` `show_error(exc)` dưới form, giữ nguyên số đã nhập (AC-32).

### Danh sách đã nhập
`weekly = feature.list_weekly_changeovers(EmptyRequest())`. Lỗi BR-09 đã được chặn ở bước 1, nhưng vẫn để `BasePage` lo nếu phát sinh.

`with panel("Số đổi mã hàng đã nhập", icon="📋"):`
- `selected = data_table(rows, selection="single", column_order=["Xưởng", "Từ ngày", "Đến ngày", "Số lần", "Người lưu"], column_config=..., key=self.key(f"weekly_table_{weekly_version}"), empty_message="Chưa nhập số đổi mã hàng tuần nào.")`. Dòng có thêm `id` để xoá, ẩn nhờ `column_order`; `selected[0]["id"]` vẫn có.
- Cột: Xưởng; Từ ngày, Đến ngày (`DateColumn(format="DD/MM/YYYY")`); Số lần (`NumberColumn(format="localized")`); Người lưu.
- `if st.button("Xoá dòng đã chọn", disabled=not selected, key=self.key("weekly_delete")):` `confirm_delete(selected[0])`.
- Hộp thoại `@st.dialog("Xác nhận xoá", icon=":material/delete:")`: `st.write(f"Xoá số đổi mã hàng của {xưởng} từ {từ ngày} đến {đến ngày}?")`. Nút "Xoá" (`type="primary"`, `key=self.key("delete_yes")`) đặt `do_delete_id` rồi `st.rerun()`; nút "Huỷ" (`key=self.key("delete_no")`) chỉ `st.rerun()`.
- Đầu khối: `delete_id = self.state.pop("do_delete_id", None)`; có thì `result = feature.delete_weekly_changeover(DeleteWeeklyChangeoverRequest(id=delete_id))`, `flash = result.message` ("Đã xoá."), tăng `weekly_version`, `st.rerun()`. `except AppError as exc:` `show_error(exc)`.
- `weekly_version` ghép vào `key` để bỏ lựa chọn cũ sau khi xoá; nếu không, lựa chọn trỏ sang dòng khác.

### Lịch sử tải file
`with panel("Lịch sử tải file", icon="🕘"):` `data_table(rows, column_config=..., key=self.key("logs"), empty_message="Chưa có lần tải file nào.")`, chỉ xem, dùng `logs` ở bước 1.
Cột: Thời điểm (`DatetimeColumn(format="DD/MM/YYYY HH:mm")`, đổi về giờ địa phương không kèm múi giờ); Người tải; Tên file; Từ ngày, Đến ngày (`DateColumn(format="DD/MM/YYYY")`); Số dòng lưu, Số dòng bỏ qua (`NumberColumn(format="localized")`).

**Lần đầu mở, chưa có dữ liệu:** Bước 1 có nút "Kiểm tra file" bị mờ, không có Bước 2, form có mặc định hôm nay, 2 bảng hiện dòng "Chưa ...". Không có hộp lỗi.

## 9. Screen 8: Mục tiêu và ngưỡng (`GoalsPage`)

```
┌ Mức đang áp dụng ─────────────────────────────────────────┐
│ Xưởng | Ngày hiệu lực | Mục tiêu hiệu suất | Mục tiêu MO 8h | ... │
└───────────────────────────────────────────────────────────┘
┌ Thêm mức mới ─────────────────────────────────────────────┐
│ [Xưởng ▼] [Ngày hiệu lực]                                  │
│ [Mục tiêu HS] [Mục tiêu MO 8h] [Ngưỡng HS] [Ngưỡng MO 8h]  │
│ [Lưu mức mới]                                              │
└───────────────────────────────────────────────────────────┘
┌ Lịch sử: ... | Người lưu ─────────────────────────────────┐
```

1. `goals = feature.list_goals(EmptyRequest())` trong `try` của mục 1.5.
2. `self.state.pop("flash", None)`: có thì `st.toast`.
3. `with panel("Mức đang áp dụng", icon="🎯"):` `data_table(rows, column_config=..., key=self.key("current"), empty_message="Chưa có mức nào.")`, chỉ xem, từ `goals.current`. Cột: Xưởng; Ngày hiệu lực (`DateColumn(format="DD/MM/YYYY")`); Mục tiêu hiệu suất (đệm, 1, `%`); Mục tiêu MO 8h (đệm, 2); Ngưỡng hiệu suất (đệm, 1, `%`); Ngưỡng MO 8h (đệm, 2).
4. `with panel("Thêm mức mới", icon="➕"):` `with st.form(self.key("goal_form"), border=False):`
   - `st.columns(2)`: `st.selectbox("Xưởng", <4 xưởng cố định>, index=None, placeholder="Chọn xưởng", key=self.key("factory"))`; `st.date_input("Ngày hiệu lực", value=date.today(), format="DD/MM/YYYY", key=self.key("effective_from"))`.
   - `st.columns(4)`: `st.number_input("Mục tiêu hiệu suất (%)", value=None, step=0.1, format="%.1f", key=self.key("efficiency_target"))`; `st.number_input("Mục tiêu MO 8h", value=None, step=0.01, format="%.2f", key=self.key("mo8h_target"))`; `st.number_input("Ngưỡng hiệu suất (%)", value=None, step=0.1, format="%.1f", key=self.key("efficiency_threshold"))`; `st.number_input("Ngưỡng MO 8h", value=None, step=0.01, format="%.2f", key=self.key("mo8h_threshold"))`.
   - `st.form_submit_button("Lưu mức mới", type="primary")` → `feature.save_goal(SaveGoalRequest(factory, effective_from, efficiency_target, mo8h_target, efficiency_threshold, mo8h_threshold))`, **không hỏi lại**.
     - Thành công: `flash = result.message`, `st.rerun()`, 2 bảng đọc lại.
     - `except AppError as exc:` `show_error(exc)` dưới form (AC-28).
5. `with panel("Lịch sử", icon="🕘"):` `data_table(rows, column_config=..., key=self.key("history"), empty_message="Chưa có mức nào.")`, chỉ xem, từ `goals.history` (mới nhất lên đầu). Cột như bước 3 và thêm Người lưu.

## 10. Screen 9: Danh mục (`CatalogsPage`)

```
[Nhóm sản phẩm] [Nhóm khách hàng] [Số chuyền Fac 1] [Tên sản phẩm theo style]
┌ Bảng sửa được: Tên sản phẩm | Nhóm sản phẩm  (+ thêm, thùng rác) ┐
[Lưu nhóm sản phẩm]
┌ Tên sản phẩm chưa phân nhóm: Tên sản phẩm | Số dòng ─────────────┐
```

1. `catalogs = feature.get_catalogs(EmptyRequest())` trong `try` của mục 1.5.
2. `self.state.pop("flash", None)`: có thì `st.toast`.
3. `tabs = st.tabs(["Nhóm sản phẩm", "Nhóm khách hàng", "Số chuyền Fac 1", "Tên sản phẩm theo style"], key=self.key("tabs"))`. **Không dùng thẻ lười** (`on_change="rerun"`, `.open`): bảng ở thẻ đóng sẽ không được vẽ, `data_editor` không có `persist_state`, nên mất phần đang sửa khi đổi thẻ. Danh mục nhỏ, cả 4 bảng cùng một `get_catalogs`, nên không chậm thêm.
4. Mỗi thẻ cùng một khuôn:
   - `rows = editable_table(<dòng dump từ DTO>, key=self.key(f"grid_<tên>_{version}"), columns=[<tên trường>], column_config=..., allow_add_delete=True)`. Bảng dùng tên trường DTO làm cột, nên dòng trả về đưa thẳng vào DTO; nhãn tiếng Việt nằm ở `column_config`. Có `id` thì ẩn bằng `column_order`.
   - `TextColumn` thường, **không** `required`, không `validate` (mục 1.6). Nhóm sản phẩm thêm mới được, nên không dùng `SelectboxColumn`.
   - `if st.button(<nhãn nút>, type="primary", key=self.key("save_<tên>")):` gọi use case với `rows`, **không hỏi lại**.
     - Thành công: `flash = result.message`, tăng `grid_<tên>_version`, `st.rerun()`. Phải đổi `key`: nếu không, `data_editor` áp lại các dòng vừa thêm lên dữ liệu mới và nhân đôi dòng.
     - `except AppError as exc:` `show_error(exc)` dưới bảng, giữ phần đang sửa (AC-48).
   - `section_title(...)`, `data_table(...)` danh sách còn thiếu, chỉ xem.

| Thẻ | Cột sửa được (trường → nhãn) | Nút → phương thức | Danh sách còn thiếu | Khi rỗng |
|---|---|---|---|---|
| Nhóm sản phẩm | Tên sản phẩm, Nhóm sản phẩm | "Lưu nhóm sản phẩm" → `save_product_groups(SaveProductGroupsRequest(rows=...))` | "Tên sản phẩm chưa phân nhóm" (`unclassified_products`): Tên sản phẩm, Số dòng | "Không còn tên sản phẩm chưa phân nhóm." |
| Nhóm khách hàng | Tên khách hàng, Nhóm khách hàng | "Lưu nhóm khách hàng" → `save_customer_groups(SaveCustomerGroupsRequest(rows=...))` | "Tên khách hàng đang có" (`customer_names`): Tên khách hàng, Nhóm hiện tại, Số dòng | "Chưa có tên khách hàng nào." |
| Số chuyền Fac 1 | Chuyền cũ, Chuyền mới | "Lưu bảng số chuyền" → `save_line_mappings(SaveLineMappingsRequest(rows=...))` | Không có | |
| Tên sản phẩm theo style | Style, Tên sản phẩm | "Lưu tên sản phẩm" → `save_style_products(SaveStyleProductsRequest(rows=...))` | "Style chưa có tên sản phẩm" (`styles_without_product`): Style, Khách hàng, Số dòng | "Không còn style chưa có tên sản phẩm." |

Cột Số dòng: `NumberColumn(format="localized")`.

Theo dõi khi chạy thử: `get_catalogs` không cache theo hợp đồng và chạy lại sau mỗi ô đã sửa, trong khi nó phải đếm trên toàn bộ dòng sản lượng. Nếu thấy chậm với dữ liệu thật, báo lại cho người điều phối thay vì tự đổi cách cache.

## 11. Thông tin trang cần từ backend

Hợp đồng chưa ghi các trường này. Thiếu thứ nào thì làm phần còn lại và báo lại cho người điều phối.

| DTO | Cần có |
|---|---|
| `OverviewMetricDTO`, dòng `metrics` của S3 | Tên chỉ số (đúng nhãn ở S1, S3), giá trị từng xưởng, **cờ dưới ngưỡng từng xưởng** |
| `LineDetailRowDTO`, `MonthlyFactoryDTO`, `DailyLineRowDTO` | Giá trị từng cột, cờ dưới ngưỡng cho Hiệu suất A, Hiệu suất B, MO 8h (phần áp dụng), loại dòng (ngày / Cả kỳ / Tổng) |
| `LineMoTableDTO` | Tên bảng, từng chuyền có giá trị theo ngày và Cả kỳ, cờ dưới ngưỡng từng ô ở MO 8h và Hiệu suất B, dòng Tổng |
| `ChartsResponse` | Điểm có ngày, xưởng, giá trị; `top_lines`, `bottom_lines` có **xưởng và chuyền** |
| Request có `factories`, `lines`, `customer_groups`, `product_groups` | `[]` nghĩa là không lọc. Riêng `customer_groups`, `product_groups`: chỉ khi không rỗng mới áp BR-29 |
| `SaveGoalRequest` | **Mọi trường nhận được `None`**, để ô trống đi đến BR-45 (AC-28). Nếu bắt buộc, lỗi kiểm tra kiểu sẽ hiện thông báo tiếng Anh trước khi tới BR-45 |
| `SaveWeeklyChangeoversRequest` | `from_date`, `to_date` là ngày; số âm vẫn nhận ở mức DTO, để BR-39 báo (AC-32) |
| Dòng của 4 request lưu danh mục | Trường nhận được `None`, để ô trống đi đến BR-47 |
| `WeeklyChangeoverDTO` | `id` |
| `UploadWarningDTO` | Ngày có thể không có |

## 12. Đối chiếu với "Giao diện đã chốt" và tiêu chí nghiệm thu

| Yêu cầu | Ở đâu |
|---|---|
| Menu 2 nhóm, mỗi màn hình một mục | 1.1 |
| Bảng báo cáo chỉ xem, lọc, sắp xếp, tìm kiếm, tải Excel; bộ lọc trên cùng; không có ô số liệu | 1.2, 1.3, mục 2 đến 7 |
| 🔴 cạnh con số; `-` khi thiếu | 1.2 |
| Mọi báo cáo hiện ngày dữ liệu mới nhất và lần tải gần nhất | 1.3 |
| Biểu đồ 2 cột, hàng cuối xếp hạng | 2 |
| S7 hai bước, Lưu hỏi lại; form không hỏi lại; Xoá hỏi lại; lịch sử chỉ xem | 8 |
| S8 bảng, form không hỏi lại, lịch sử | 9 |
| S9 4 thẻ, sửa trong ô, thêm bớt dòng, không hỏi lại, danh sách còn thiếu | 10 |
| AC-01 (file `.pdf`) | `types=()` ở S7 |
| AC-02, 03, 04 | `check_error` ở S7 |
| AC-05, 06, 07, 11, 13 | Bước 2 và lịch sử ở S7 |
| AC-12, BR-09 | 1.5 |
| AC-28, 32, 48 | 1.6, S7, S8, S9 |
| AC-29, 30 | 1.2 |
| AC-41 | 2 |
| AC-42 | 1.4 |
| AC-45, 46, 52 | 1.3 |

## 13. Giả định

- Giả định (triển khai): Mọi cột số của bảng báo cáo là ô chữ căn phải có đệm dấu cách, vì `data_table` không cho đặt `placeholder` và cột số không đạt BR-28, BR-50. Sắp xếp theo số đã kiểm tra trên trình duyệt. CSV tải từ biểu tượng của bảng còn dấu cách đầu.
- Giả định (triển khai): Bấm tiêu đề cột Ngày ở S2, S4 hoặc cột Chuyền sẽ sắp theo chữ; thứ tự mặc định vẫn đúng.
- Giả định (triển khai): BR-50 không ghi Số người, Số thợ, SMV và Đổi mã hàng tuần trên chuyền: Số người và Số thợ dùng 1 chữ số lẻ, hai số còn lại dùng 2.
- Giả định (triển khai): Ở S1, bảng chỉ số chỉ hiện cột của các xưởng đang chọn.
- Giả định (triển khai): Khoảng ngày đúng nhưng không có dữ liệu thì không hiện nút Tải Excel.
- Giả định (triển khai): Nút Tải Excel ở S2 gửi đúng xưởng đang chọn; bộ lọc Chuyền không vào file vì hợp đồng không có trường này, trang có ghi chú.
- Giả định (triển khai): Bỏ chọn hết Xưởng được tính là tất cả.
- Giả định (triển khai): File trên 50 MB bị ô tải file chặn trước với thông báo của ô đó, không phải câu BR-01. Không sửa được vì `.streamlit/` thuộc khung sườn.
- Giả định (triển khai): Chưa có dữ liệu thì form đổi mã hàng tuần lấy mặc định hôm nay, vì BR-31 chưa tính được.
- Giả định (triển khai): Tên file xuất dùng dạng ngày và tên xưởng do `builders/` quy định; trang dựng lại đúng dạng đó.
- Giả định (triển khai): Danh sách 4 xưởng ở form S7, S8 là hằng cố định theo mục 3 của tài liệu, vì `options.factories` rỗng khi chưa có dữ liệu.
