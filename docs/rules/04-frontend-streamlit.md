# 04 - Frontend (Streamlit)

## How the UI is assembled (never edit these to add a feature)
- `frontend/app.py` -> `AppShell` (page config, theme, **login**, **sidebar**, current page, **footer**).
- Login + permissions are framework features (`frontend/core/auth.py`, `frontend/core/admin_page.py`): a user only
  sees the features/pages granted to them; pages never check permissions themselves. The admin page is reached only
  by URL `/admin` (administrators); it is not in the menu.
- `Router` builds URLs from the manifests found in `frontend/features/*/manifest.py` and the app registry:
  `/` -> `/home`; `/home` = Home (one card per app); `/<prefix>-<feature-key-with-dashes>` = app landing page;
  `/<prefix>-<feature>-<slug>` = other pages.

### App registry (`backend/app_registry.py`) - REQUIRED for every app
Every app is ONE line `("<prefix>", "<feature_key>")` in `APPS`, where `<prefix>` is the builder's short name
(lower-case letters and digits, e.g. `tenban`): all of that person's apps live under `/tenban-...`
(Streamlit 1.64 refuses nested paths such as `/tenban/app`, so the prefix is joined with `-`).
- `scripts/new_feature.py ... --prefix tenban` adds the line (default prefix: the developer name, lower-case).
- The router (URLs, Home card, menu) and the gateway (backend calls) both read it: an app that is not registered is
  reported on Home as not registered, has no URL, and its controller refuses every call.
- `tests/architecture/test_structure.py` fails while an app is missing, listed twice, or listed but deleted.
- Never edit or remove another person's line; never change a prefix once users have bookmarks.
- One feature = one **app**. Home lists the apps as cards (its sidebar shows only who is logged in); opening an app
  shows that app's own menu in the sidebar: "Tất cả ứng dụng" (back to Home), the app name, then its pages under
  their `menu_group` labels. Both are generated from manifests: a new app appears automatically.
- Branding (`frontend/core/branding.py`): `frontend/public/logo.png` = browser-tab icon (padded to a square),
  `frontend/public/Logo_TC.png` = logo at the top of the sidebar (`st.logo`).
  To rebrand, replace the files (same names). Features never add their own logo or page icon.
- A feature that fails to load is reported on Home; the other features keep working.

## A feature's frontend
```
frontend/features/<key>/
├── manifest.py      FEATURE = FeatureManifest(key, title, description, pages=(...), icon, group, owner, order)
├── pages/           one BasePage subclass per screen of the business doc (first = landing page)
└── components/      widgets used only by this feature (plain functions)
```

## Page template
```python
class ProductListPage(BasePage):
    title = "Danh sách sản phẩm"
    icon = "📋"
    slug = "products"  # required for every page except the first one of the feature
    description = "Tra cứu sản phẩm và xuất báo cáo."

    def render(self) -> None:
        products = gateway.open(SampleProductImportController)  # top layer of the business
        with panel("Bộ lọc", icon="🔎"):
            keyword = st.text_input("Từ khoá", key=self.key("keyword"))
        data = products.list_products(ListProductsRequest(keyword=keyword))
        stat_row([("Sản phẩm", data.summary.product_count)])
        data_table([item.model_dump() for item in data.items])
```
`BasePage.run()` (fixed) renders: shared header with breadcrumb -> `render()` inside an error boundary. An `AppError` raised by the backend is shown as a friendly message automatically.
To keep rendering after an error, catch it locally:
```python
try:
    saved = products.commit_import(CommitImportRequest(file=file))
except AppError as exc:
    show_error(exc)
else:
    show_success(f"Đã lưu {saved.created} dòng")
```

## Shared components (`frontend.core.components`) - use them before writing new widgets
| Component | Use |
|---|---|
| `page_header(...)` | page title with breadcrumb and the brand stripe (BasePage/Home already call it) |
| `panel(title, icon=, description=)` | bordered block: `with panel("Bộ lọc"):` - use for every logical block |
| `stat_row([(label, value), ...])` | KPI tiles |
| `data_table(rows, column_config=, selection="single"/"multi", key=)` | read-only Excel-like table (sort, search, fullscreen) with empty state; with `selection` returns the ticked rows (list of dicts). Shows at most `APP_TABLE_MAX_ROWS` rows (200 000; with `selection`: `APP_SELECT_MAX_ROWS`, 10 000) and says so |
| `editable_table(rows, key=, columns=, column_config=, disabled=, allow_add_delete=)` | grid edited like an Excel sheet; returns the edited rows (empty cells = `None`, ready for DTOs). Over `APP_EDIT_MAX_ROWS` (5 000) rows it is shown read-only with a warning and returns the rows unchanged |
| `bar_chart(rows, x=, y=, key=, color=, horizontal=, stacked=)`, `line_chart(rows, x=, y=, key=, color=, area=)`, `pie_chart(rows, names=, values=, key=)` | the ONLY way to draw charts (see Charts below) |
| `frame_to_records(df)` | DataFrame -> list of dicts without NaN/numpy values (always use it before building DTOs) |
| `file_upload(label, types=, key=)` | returns `UploadedFileDTO` (bytes) or None |
| `download_button(file_dto, label=, key=)` | download a `FileDownloadDTO` already built |
| `download_button(lambda: feature.export(req), label=, key=, file_name="x.xlsx")` | build the file only when the user clicks (reruns stay fast). It runs off-screen: only for exports that cannot raise an `AppError` (inputs already checked); otherwise build it inside `if st.button(...)` |
| `empty_state(msg, hint)`, `section_title(text)` | helpers |
| `show_error(exc)`, `show_success(msg)` | feedback |
| `render_sidebar_nav`, `render_footer` | used by AppShell only |
Formatting helpers: `frontend.core.formatting` (`format_number`, `format_currency`, `format_datetime`).

## Excel-like UI (the users work in Excel every day)
Prefer what they know: one clear table per screen, filters above it, totals as KPI tiles, an "Xuất Excel" button,
"Nhập từ Excel" upload with a template download. The feature's `### Giao diện đã chốt (UI concept)` block in section 8
of the business document (agreed with the user at the start of Prompt 2) decides the layout.

| Need | Use (Streamlit 1.64.0, verified) |
|---|---|
| Read-only table | `data_table(rows, column_config={...})` |
| Pick a row to see/edit details | `data_table(rows, selection="single", key=self.key("pick"))` -> selected rows |
| Edit cells like Excel, then save | `editable_table(rows, key=..., disabled=["code"])` + `st.button("Lưu")` -> use case with the rows |
| Column formats | `st.column_config.NumberColumn("Số lượng", format="localized")`, `TextColumn`, `DateColumn(format="DD/MM/YYYY")`, `SelectboxColumn(options=[...])`, `CheckboxColumn`, `ProgressColumn`, `LinkColumn` |
| Group screens of one page | `st.tabs([...])`; related inputs side by side: `st.columns(n)` |
| Form with one submit | `with st.form(self.key("form")): ...; st.form_submit_button("Lưu")` |
| Confirmation / details popup | `@st.dialog("Xác nhận xoá")` function called inside `if st.button(...)` |
| Quick choices / filters | `st.segmented_control`, `st.pills`, `st.selectbox`, `st.multiselect`, `st.date_input`, `st.toggle` |
| Charts | `bar_chart` / `line_chart` / `pie_chart` (`frontend.core.components`) |
| Files | `file_upload(...)` / `download_button(...)` (shared components) |

### Look & feel: native Streamlit 1.64 only (less code, faster, matches the theme)
The brand theme (TC logo colours, font Be Vietnam Pro, radius, table header colour) lives in `.streamlit/config.toml`
`[theme]`; every native element picks it up. So: no HTML, no `unsafe_allow_html`, no CSS, no `st.html` in features.
Pick the newest native element below before writing anything by hand.

| Need | Native element (verified in 1.64) |
|---|---|
| Status / tag next to a value ("Đã duyệt", "Nháp") | `st.badge("Đã duyệt", color="green", icon=":material/check:")`; inside text: `:green-badge[Đã duyệt]` |
| Coloured text, icons | `:red[...]`, `:green[...]`, `:orange[...]`; Material icons `":material/download:"` (in `icon=` of buttons, tabs, expanders, badges) |
| Filter with a few choices | `st.segmented_control(...)` (2-5 choices) / `st.pills(...)` (more, or `selection_mode="multi"`) |
| Buttons in one row, toolbar | `with st.container(horizontal=True, gap="small"):` then the buttons (no `st.columns` for buttons) |
| Space between blocks | `st.space("small" / "medium" / "large")` (never empty `st.write("")`) |
| Several actions in one button | `st.menu_button("Thao tác", ["Sửa", "Xoá"], key=...)` -> the picked option (or None) |
| Heavy tab / expander (big table, chart) | lazy: `tab_a, tab_b = st.tabs([...], key=self.key("tabs"), on_change="rerun")`, then `with tab_a: if tab_a.open: ...` - only the open tab runs its use cases. Same for `st.expander(..., key=, on_change="rerun")` + `.open` |
| Very long table (> 1000 rows) | `data_table` already sends only the visible rows (`lazy`); for paging: `page = st.pagination(n_pages, key=...)` |
| KPI with a trend | `st.metric(label, value, delta, chart_data=[...], chart_type="bar", border=True)` |
| Remember a filter when the user comes back to the page | widget argument `persist_state="session"` |
| Short confirmation after an action | `st.toast("Đã lưu", icon=":material/check:")`; pop-up form: `@st.dialog("Tiêu đề", icon=...)` |
| Placeholder while something slow loads | `st.skeleton(height=200)` |

- Official API reference: https://docs.streamlit.io/develop/api-reference (e.g. `/data/st.dataframe`,
  `/data/st.data_editor`, `/data/st.column_config`, `/widgets`, `/layout`, `/charts`, `/execution-flow/st.dialog`).
  The site describes the LATEST Streamlit; the installed version (see `requirements.txt`) is the truth. Before using a
  function or parameter, check it exists:
  `.venv/Scripts/python.exe -X utf8 -c "import inspect, streamlit as st; print(inspect.signature(st.data_editor))"`.
- Never add UI libraries (AgGrid, custom components, JS): `requirements.txt` is frozen for features.
- Tables send data to the backend only inside `if st.button(...)`; validation stays in the backend (BR-xx).

### Charts (`frontend/core/components/charts.py`)
One call per chart: rows (list of dicts or DataFrame) in, a themed Plotly chart out. Never `st.plotly_chart`,
`st.bar_chart`, `px.*` directly in a feature: the shared component keeps big data fast and every chart consistent.
- Data: let a `@cached_query` use case return the rows already grouped (e.g. one row per month); the component only
  prepares for display: bars / pie are summed per category, the biggest `APP_CHART_MAX_CATEGORIES` (30) are kept and
  the rest become "Khác"; lines keep at most `APP_CHART_MAX_POINTS` (5 000) points per series (WebGL past 1 000);
  at most 6 series (fixed colour order `SERIES_COLORS`, checked for colour-blind separation). A caption says what
  was trimmed.
- Look: one y-axis only (two measures of different scale = two charts), legend only with 2+ series, Vietnamese number
  format (`1.234.567,5`), hover tooltips, empty state when there is no data. Show the same numbers in a
  `data_table` when users need exact values.
- Chart design changes (colours, margins, new chart kinds) go into `charts.py` only - one place for every app.

## Rules
1. A page calls ONLY the controller of its own feature, through `gateway.open(...)`. No business logic, no calculations that belong
   to a rule, no file reading/writing, no openpyxl/docx/pypdf in the frontend.
2. Widget keys: always `key=self.key("name")`. Session data: `self.state.get/set(...)` (namespaced per feature).
3. Never call `st.set_page_config`, never inject global CSS, never edit `frontend/core` for one feature.
4. Every widget interaction reruns the page: call only `@cached_query` use cases on render (they come from RAM);
   anything that writes or builds a file for an action goes inside `if st.button(...)`. Never change a response DTO
   in place (cached results are shared).
5. Navigation between pages of the feature: `self.link_to(OtherPage)` or `self.go_to(OtherPage)`.
6. Every page listed in `FEATURE.pages`; every class in `pages/` inherits `BasePage`.
7. Every page MUST render on first load with NO data and without any error box (checked by
   `tests/architecture/test_pages_render.py`): show `empty_state(...)` for empty lists, give inputs defaults, and only
   call use cases that can fail after the user acted (inside `if st.button(...)`).
8. Layout: header (automatic) -> filters/inputs in panels -> KPIs -> tables/charts -> actions, following the
   feature's `### Giao diện đã chốt (UI concept)`. Keep it simple.
9. A feature's navigation = its manifest: the feature is an app with a card on Home, and the pages listed in
   `FEATURE.pages` are the app's sidebar menu once the user opens it (first page = landing page, `/<feature-key>`).
   Set `menu_group = "Sales"` on a page class to list it under the label "Sales" in that menu (pages of a group must be
   consecutive in `FEATURE.pages`). Only the pages the user may open are shown. Actors with different rights inside
   the app are `roles=((CODE, "Nhãn"), ...)` in the manifest (rules 02 "Roles inside an app"): `/admin` shows one
   column per role; a page may read `self.current_user.roles_in(self.feature_key)` only to disable buttons, the
   backend rule decides. The sample feature (`sample=True` in its manifest) is hidden automatically as soon as one real feature
   exists; never delete or disable it by hand. Never edit the sidebar, Home or router to add a feature.
