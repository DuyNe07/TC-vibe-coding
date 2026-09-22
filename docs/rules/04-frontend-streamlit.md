# 04 - Frontend (Streamlit)

## How the UI is assembled (never edit these to add a feature)
- `frontend/app.py` -> `AppShell` (page config, theme, **sidebar menu**, current page, **footer**).
- `Router` builds URLs from the manifests found in `frontend/features/*/manifest.py`:
  `/` -> `/home`; `/home` = Home (feature cards); `/<feature-key-with-dashes>` = feature landing page;
  `/<feature>-<slug>` = other pages.
- Home and the sidebar menu are generated from manifests: a new feature appears automatically.
- Branding (`frontend/core/branding.py`): `frontend/public/logo.png` = browser-tab icon (padded to a square),
  `frontend/public/Logo_TC.png` = logo in the sidebar (fixed height, width keeps the ratio).
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
`BasePage.run()` (fixed) renders: shared header with breadcrumb -> `render()` inside an error boundary ->
**log panel**. An `AppError` raised by the backend is shown as a friendly message automatically.
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
| `page_header(...)`, `hero(...)` | headers (BasePage/Home already call them) |
| `panel(title, icon=, description=)` | bordered block: `with panel("Bộ lọc"):` - use for every logical block |
| `stat_row([(label, value), ...])` | KPI tiles |
| `data_table(rows, column_config=, selection="single"/"multi", key=)` | read-only Excel-like table (sort, search, fullscreen) with empty state; with `selection` returns the ticked rows (list of dicts) |
| `editable_table(rows, key=, columns=, column_config=, disabled=, allow_add_delete=)` | grid edited like an Excel sheet; returns the edited rows (empty cells = `None`, ready for DTOs) |
| `frame_to_records(df)` | DataFrame -> list of dicts without NaN/numpy values (always use it before building DTOs) |
| `file_upload(label, types=, key=)` | returns `UploadedFileDTO` (bytes) or None |
| `download_button(file_dto, label=, key=)` | download a `FileDownloadDTO` |
| `empty_state(msg, hint)`, `section_title(text)` | helpers |
| `show_error(exc)`, `show_success(msg)` | feedback |
| `log_panel(feature_key, key=)` | log viewer (already added by BasePage) |
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
| Charts | `st.bar_chart` / `st.line_chart` (simple), `st.plotly_chart(fig)` (plotly is installed) |
| Files | `file_upload(...)` / `download_button(...)` (shared components) |

- Official API reference: https://docs.streamlit.io/develop/api-reference (e.g. `/data/st.dataframe`,
  `/data/st.data_editor`, `/data/st.column_config`, `/widgets`, `/layout`, `/charts`, `/execution-flow/st.dialog`).
  The site describes the LATEST Streamlit; the installed version (see `requirements.txt`) is the truth. Before using a
  function or parameter, check it exists:
  `.venv/Scripts/python.exe -X utf8 -c "import inspect, streamlit as st; print(inspect.signature(st.data_editor))"`.
- Never add UI libraries (AgGrid, custom components, JS): `requirements.txt` is frozen for features.
- Tables send data to the backend only inside `if st.button(...)`; validation stays in the backend (BR-xx).

## Rules
1. A page calls ONLY the controller of its own feature, through `gateway.open(...)`. No business logic, no calculations that belong
   to a rule, no file reading/writing, no openpyxl/docx/pypdf in the frontend.
2. Widget keys: always `key=self.key("name")`. Session data: `self.state.get/set(...)` (namespaced per feature).
3. Never call `st.set_page_config`, never inject global CSS, never edit `frontend/core` for one feature.
4. Keep the log panel (`show_log_panel = True`). Only feature pages show logs; Home does not.
5. Navigation between pages of the feature: `self.link_to(OtherPage)` or `self.go_to(OtherPage)`.
6. Every page listed in `FEATURE.pages`; every class in `pages/` inherits `BasePage`.
7. Every page MUST render on first load with NO data and without any error box (checked by
   `tests/architecture/test_pages_render.py`): show `empty_state(...)` for empty lists, give inputs defaults, and only
   call use cases that can fail after the user acted (inside `if st.button(...)`).
8. Layout: header (automatic) -> filters/inputs in panels -> KPIs -> tables/charts -> actions, following the
   feature's `### Giao diện đã chốt (UI concept)`. Keep it simple.
9. A feature's navigation = its manifest: the pages listed in `FEATURE.pages` appear automatically in the sidebar
   menu under the feature (first page = the feature entry, others as `↳` sub-items) and the feature card appears on
   Home. Never edit the sidebar, Home or router to add a feature.
