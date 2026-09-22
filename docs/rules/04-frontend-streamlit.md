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
        products = gateway.open(SampleProductImportController)   # top layer of the business
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
| `data_table(rows, column_config=)` | read-only table with empty state |
| `file_upload(label, types=, key=)` | returns `UploadedFileDTO` (bytes) or None |
| `download_button(file_dto, label=, key=)` | download a `FileDownloadDTO` |
| `empty_state(msg, hint)`, `section_title(text)` | helpers |
| `show_error(exc)`, `show_success(msg)` | feedback |
| `log_panel(feature_key, key=)` | log viewer (already added by BasePage) |
| `render_sidebar_nav`, `render_footer` | used by AppShell only |
Formatting helpers: `frontend.core.formatting` (`format_number`, `format_currency`, `format_datetime`).

## Rules
1. A page calls ONLY the controller of its own feature, through `gateway.open(...)`. No business logic, no calculations that belong
   to a rule, no file reading/writing, no openpyxl/docx/pypdf in the frontend.
2. Widget keys: always `key=self.key("name")`. Session data: `self.state.get/set(...)` (namespaced per feature).
3. Never call `st.set_page_config`, never inject global CSS, never edit `frontend/core` for one feature.
4. Keep the log panel (`show_log_panel = True`). Only feature pages show logs; Home does not.
5. Navigation between pages of the feature: `self.link_to(OtherPage)` or `self.go_to(OtherPage)`.
6. Every page listed in `FEATURE.pages`; every class in `pages/` inherits `BasePage`.
7. Layout: header (automatic) -> filters/inputs in panels -> KPIs -> tables/charts -> actions. Keep it simple.
