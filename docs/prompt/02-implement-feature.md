# TASK: Implement the confirmed business documents -> backend + UI (Prompt 2 of 3)

> GATE KEY: `TC-UNLOCK-IMPLEMENT`. Pasting this prompt is what allows writing code in this repository, and only for a
> business document whose `Status` is `Ready for implementation`. Step 1 creates the file `.gate-unlock` (which opens
> the mechanical guard `scripts/hooks/gate_guard.sh`) and Step 6 deletes it. See the workflow gate in `CLAUDE.md`.

You are the lead engineer (Python/Streamlit) inside this repository, a framework for internal Streamlit apps built by
AI for non-programmers. Implement the confirmed business documents as working features (backend + UI) from start to
finish in THIS session, strictly following the repository rules.

**Mode: ONE question round about the UI, then fully automatic.** The business was settled in Prompt 1. You ask the user
exactly once, at Step 0, how they want to use the screens (application-level, never code), then STOP. After their reply
you never ask again and never wait for approval: plan, build (with sub-agents when your tool has them), test, verify,
then send ONE final report. The only other allowed message: if your tool is in a read-only / plan mode and cannot
write files, tell the user in one Vietnamese sentence to allow editing, then continue.

## 1. Scope (detect it yourself)
Candidate documents: `docs/business/*.md` except `_TEMPLATE.md`, `README.md`, `sample_product_import.md`.
1. **In scope** = every candidate whose header `Status` is `Ready for implementation`, plus every candidate that has a
   plan `docs/plans/<feature_key>-implementation-plan.md` with unchecked steps (an interrupted run: resume it), plus
   an `Implemented` feature that the user explicitly asks in this conversation to change (e.g. "Đổi giao diện chức
   năng X": then only the UI changes, the business stays as documented).
2. If nothing is in scope: reply in Vietnamese which documents exist and their status (e.g. "Tài liệu X đang ở trạng
   thái Draft - hãy hoàn tất Prompt 1 trước") and stop.
3. The feature key is the `Feature key` value in the document header (= the file name without `.md`). The controller
   class is the PascalCase of the key + `Controller` (`leave_request` -> `LeaveRequestController`).
4. Source of truth = the document, including the `### Giao diện đã chốt (UI concept)` block of section 8 written at
   Step 0. Every data field, file column, UC, BR, screen element, UI decision and AC MUST be implemented. Nothing may
   be skipped, simplified or invented.
5. Gaps: if the document is silent or ambiguous on a detail, choose the safest behaviour consistent with the rest of
   the document (validate strictly, never delete data silently, show a clear Vietnamese message), write it in
   section 10 as `Giả định (triển khai): ...`, and list it in the final report. Technical choices are always yours.
6. Real blockers (e.g. the document requires a system that does not exist): implement everything else, make the
   blocked part show a clear Vietnamese message in the UI, and explain it in the final report.
7. Several features in scope: ask the Step 0 questions for all of them in one message, then build them one after
   another (Steps 1-5 per feature).

## 2. Step 0 - UI concept: the ONLY question round -> STOP
**Skip Step 0** only when (a) resuming: the plan has unchecked steps AND section 8 already contains
`### Giao diện đã chốt (UI concept)`, or (b) the user already answered these UI questions earlier in this conversation.
Otherwise, for every in-scope feature:
1. Read the document (sections 4-8 above all), `docs/rules/04-frontend-streamlit.md` (section "Excel-like UI") and the
   reference pages in `frontend/features/sample_product_import/pages/` to know what the app can show.
2. Send ONE message in simple Vietnamese - no technical words, no code, no Streamlit names:
   - One line: what will be built (feature name, number of screens).
   - For each screen of section 8, a proposal with a small text sketch (the users work in Excel every day: prefer one
     clear table per screen, filters above it, totals as tiles, "Xuất Excel" / "Nhập từ Excel" buttons), e.g.
     ```
     ┌ Bộ lọc: [Từ khoá] [Trạng thái ▼] ───────────────────┐
     │ Tổng số: 120      Tổng tiền: 35.000.000 đ           │
     │ Bảng: Mã | Tên | Số lượng | Đơn giá | Trạng thái     │
     │ [Xuất Excel]   [Lưu thay đổi]                        │
     └──────────────────────────────────────────────────────┘
     ```
   - Numbered questions, each with options and the proposed default marked `(đề xuất)`. Ask only what the document
     leaves open, from this list:
     1. Menu: mỗi màn hình là một mục riêng trong menu bên trái, dưới tên chức năng; hoặc gộp thành các thẻ (tab)
        trong một trang.
     2. Bảng dữ liệu (như Excel): (a) chỉ xem - lọc, sắp xếp, tìm kiếm, tải Excel; (b) sửa trực tiếp trong ô rồi bấm
        "Lưu"; (c) chọn một dòng để xem chi tiết / sửa.
     3. Nhập dữ liệu (chỉ những cách tài liệu cho phép): (a) điền form từng bản ghi; (b) nhập nhiều dòng trong bảng
        như Excel; (c) tải file Excel lên.
     4. Bộ lọc phía trên bảng và thứ tự cột của bảng (đề xuất từ mục 4 và 8 của tài liệu).
     5. Ô số liệu tổng hợp và biểu đồ: những số nào, loại biểu đồ nào - hoặc không cần.
     6. Hỏi lại trước khi lưu / xoá (hộp thoại xác nhận): có / không.
   - End with exactly: "Trả lời theo số (ví dụ: 1a, 2b, 5: bỏ biểu đồ), hoặc gõ "ok" để dùng toàn bộ đề xuất. Sau câu
     trả lời này AI sẽ tự làm đến khi xong, không hỏi thêm."
3. **STOP** and wait for the reply.
4. After the reply ("ok", or a point left unanswered = the proposal):
   - Write the decisions at the top of section 8 of the document as `### Giao diện đã chốt (UI concept)` (replace
     the block if it already exists), in Vietnamese, per screen: place (menu item / tab), blocks from top to bottom,
     table type (chỉ xem / sửa trong ô / chọn dòng), columns in order, filters, KPI tiles, charts, buttons,
     confirmations.
   - The UI changes only how things are shown and entered, never the business rules. An impossible wish (another
     library, own colours/logo, login, e-mail...) gets the closest possible option, recorded in section 10 as
     `Giả định (triển khai): ...`.
   - If a UI choice needs an action without a use case (e.g. saving many edited rows at once), add it to section 6 as
     the next `UC-xx` that applies the existing BRs, and note it in section 10.
   - From now on never ask the user anything (sub-agents neither).

## 3. Commands (run from the repository root; they work in PowerShell AND Git Bash - always use forward slashes)
On macOS/Linux replace `.venv/Scripts/python.exe` with `.venv/bin/python`. Copy the commands exactly.

```
# Open the workflow gate (Step 1, after the UI answer) / close it again (Step 6, before the report)
echo <key> > .gate-unlock
rm .gate-unlock

# Create the environment (only if the .venv folder is missing)
py -3.11 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt

# Install packages again (only on "No module named ..." errors)
.venv/Scripts/python.exe -m pip install -r requirements.txt

# Quality gate - MUST end with "ALL CHECKS PASSED" (the --fix variant auto-fixes lint/format first)
.venv/Scripts/python.exe scripts/check.py --fix
.venv/Scripts/python.exe scripts/check.py

# Tests of one feature only (faster while working)
.venv/Scripts/python.exe -X utf8 -m pytest backend/features/<key>/tests -q

# Scaffold a NEW feature (never for an existing one)
.venv/Scripts/python.exe -X utf8 scripts/new_feature.py <key> --title "<VI title>" --description "<VI sentence>" --icon "<emoji>" --group "<VI group>" --owner "<owner>"

# Gateway registration check: lists the use cases the pages can call through the gateway
.venv/Scripts/python.exe -X utf8 -c "from backend.features.<key> import <Pascal>Controller as C; print(sorted(C.actions()))"

# Streamlit API check: the INSTALLED version is the truth (replace data_editor by the function you need)
.venv/Scripts/python.exe -X utf8 -c "import inspect, streamlit as st; print(st.__version__, inspect.signature(st.data_editor))"

# Start the app in the BACKGROUND (this command keeps running until stopped)
powershell -NoProfile -ExecutionPolicy Bypass -File ./run.ps1 -NoBrowser -Port 8599

# Health check (prints b'ok' when the app is up; retry for up to 60 seconds after starting)
.venv/Scripts/python.exe -c "import urllib.request as u; print(u.urlopen('http://127.0.0.1:8599/_stcore/health', timeout=5).read())"

# Stop the app
powershell -NoProfile -Command 'Get-NetTCPConnection -LocalPort 8599 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }'
```
If port 8599 is busy, `run.ps1` picks the next free one: read its line `[run] Starting app at http://localhost:<port>/home`
and use that port in the health check and stop commands.

## 4. Non-negotiable rules (full rules in `docs/rules/` - read them)
1. **One process, no API.** ONE Streamlit process started by `run.ps1`. Pages run business actions IN-PROCESS through
   the gateway. FORBIDDEN: FastAPI/Flask/any web server, REST endpoints, string routes like `"feature/action"`, HTTP
   clients (`requests`, `httpx`, `urllib` to localhost) in app code, JSON between UI and backend, a second process,
   another launcher than `run.ps1`, new libraries (`requirements.txt` is frozen for features).
2. **The ONLY calling flow:**
   ```
   Page.render()                                      frontend/features/<key>/pages/*.py
     -> feature = gateway.open(<Pascal>Controller)    backend/core/gateway.py (uniform mechanism, logs every call)
       -> feature.<use_case>(<UseCase>Request(...))   controllers/<key>_controller.py  (TOP layer, 1 line per method)
         -> <UseCase>Service().handle(request)        services/<use_case>_service.py   (one use case)
              -> builders/      file -> models, models -> DTO / Excel / Word
              -> business/      BR-xx rules + calculations + decisions (pure, no I/O)
              -> repositories/  load/save entities (data/<key>/*.json)
              -> models/        entities, value objects, enums
         <- <UseCase>Response  (DTO)                  dto/*.py
     <- page renders the DTO; an AppError raised anywhere is shown by BasePage and logged by the gateway
   ```
3. **Encapsulation = gateway registration.** Exactly ONE controller class per feature, exported by
   `backend/features/<key>/__init__.py` (`from backend.features.<key>.controllers.<key>_controller import
   <Pascal>Controller` and `__all__ = ["<Pascal>Controller"]`). This export IS the registration with the gateway: there
   is no central list to edit, so features never conflict. Pages import only `backend.core.*`, `backend.features.<key>`
   and `backend.features.<key>.dto.*`, and never write `<Pascal>Controller()`.
4. **Navigation = manifest.** `frontend/features/<key>/manifest.py` (`FEATURE = FeatureManifest(...)`) lists the pages;
   the sidebar menu (feature entry + `↳` sub-pages) and the Home card are generated from it. Never edit the sidebar,
   Home, router or `frontend/app.py`.
5. **Traceability.** One `UC-xx` = one controller method (docstring `"""UC-xx <tên nghiệp vụ>."""`) = one service class
   in its own file. One validation `BR-xx` = one `BaseBusinessRule` subclass with `code = "BR-xx"`; one
   calculation/decision `BR-xx` = a named method of a `BaseBusiness` class whose docstring starts with `BR-xx`.
   One screen = one page class (or one tab, if the UI concept groups screens as tabs).
6. **Tests are law.** Never edit, skip or weaken tests in `tests/`, never add `# noqa`, `pytest.skip`, `xfail` or config
   ignores. Fix YOUR code until `scripts/check.py` prints `ALL CHECKS PASSED`.
7. **Logging.** Never `print()`. Services log main steps with `self.logger.info(...)`. Pages keep the log panel.
8. **Language.** Code, identifiers, comments, docstrings, logs: English. Everything the user sees: Vietnamese, from the
   document.
9. **No conflict with existing work.** Write ONLY in `backend/features/<key>/`, `frontend/features/<key>/`,
   `docs/plans/<key>-*.md` and `docs/business/<key>.md` (only: the UI concept block and new UCs of Step 0, sections
   10 and 11, `Status`). Never modify other features, `sample_product_import`, `backend/core/`, `backend/shared/`,
   `frontend/core/`, `frontend/app.py`, `frontend/home/`, `scripts/`, `tests/`, `run.ps1`, `requirements.txt`,
   `.streamlit/`, `conftest.py`, `pyproject.toml`. If something seems missing in the framework, build it inside the
   feature.
10. **Existing feature** (`backend/features/<key>/` already exists): do NOT scaffold, do NOT delete folders. Update in
    place to match the document. Keep stored data readable: new model fields MUST have defaults; for a removed/renamed
    field add a small conversion in the repository (models use `extra="forbid"`). Never delete `data/<key>/`.
11. Do not `git commit` / `git push`.

## 5. Step 1 - Preflight
0. Open the gate: write the in-scope feature keys into `.gate-unlock` (section 3). Without it every write to code is
   refused by `scripts/hooks/gate_guard.sh`. Do this only now, never before the user's Step 0 answer.
1. If `.venv` is missing, create it (section 3). Run the quality gate once BEFORE changing anything (baseline).
   If it fails because of missing packages, install them and re-run. If it fails in code outside your scope, do not
   touch that code: note it as "pre-existing" for the final report.
2. Read completely: `CLAUDE.md`, `docs/README.md`, every file in `docs/rules/`, `docs/business/README.md`, each
   in-scope business document, and the reference feature (all files of `backend/features/sample_product_import/` and
   `frontend/features/sample_product_import/`). Skim `backend/core/base/*.py`, `backend/core/gateway.py`,
   `frontend/core/base_page.py`, `frontend/core/components/__init__.py`, `backend/shared/file_io/__init__.py`.

## 6. Step 2 - Plan (write it, do not wait)
Create or update `docs/plans/<key>-implementation-plan.md`. If it already exists with checked steps, keep it and
resume from the first unchecked step (verify earlier steps still pass the quality gate). The plan contains:
1. Summary (Vietnamese, 3-5 lines) and the UI concept in one line per screen.
2. Scaffold command (only for a new feature) built from the document header: title = `#` title, description = first
   sentence of section 1, icon, Home group, owner.
3. **Requirement Traceability Matrix** - one row for EVERY data field (section 4), file and column (5), UC (6), BR (7),
   screen element with data or an action and UI concept decision (8), AC (9):
   `| Spec item | Description (VI) | Code element (file :: class/method) | Test (file :: test) | Status ☐/✅ |`
4. **Controller contract** (binding for every role): per UC `def <use_case>(self, request: <X>Request) -> <X>Response`
   with the DTO file name and the main fields. Pages list: page class, slug, screen.
5. Checkboxes, ticked as you go: `☐ Step 0 UI concept recorded`, `☐ Scaffold`, `☐ Backend (section 9) - ALL CHECKS
   PASSED`, `☐ UI design (section 10)`, `☐ UI build (section 11) - ALL CHECKS PASSED`, `☐ Gateway registration
   check`, `☐ Navigation check`, `☐ Scaffold ping removed`, `☐ Document updated`, `☐ Verify (Step 5)`, `☐ Report`;
   plus the implementation assumptions.

## 7. Step 3 - Build with sub-agents (backend and UI)
| Role | Writes ONLY in | Job |
|---|---|---|
| Lead (you) | `docs/business/<key>.md` (rule 9), `docs/plans/<key>-implementation-plan.md` | Steps 0-2, scaffold, start the sub-agents, check their work, Step 4, Step 5, report |
| Backend sub-agent | `backend/features/<key>/` | section 9: the whole business logic, top layer = the controller |
| UI-design sub-agent | `docs/plans/<key>-ui-design.md` | section 10: study the Streamlit docs and design every screen (no Python) |
| UI-build sub-agent | `frontend/features/<key>/` | section 11: pages, feature widgets, manifest (= the feature's navigation) |

Order:
1. Lead: scaffold (new feature only) - creates the BE and FE folders and the doc, with a working `ping` use case.
2. **Phase A, in parallel:** Backend sub-agent + UI-design sub-agent. Wait for both.
3. **Phase B:** UI-build sub-agent (it needs the finished backend and the design). Wait.
4. Lead: Step 4 (integrate), Step 5 (verify), report.
Only one role writes Python at a time (Backend in phase A, UI-build in phase B), so `check.py --fix` never touches
files another agent is editing.

How:
- If your tool can start sub-agents (Claude Code: the Agent tool with the general-purpose agent; other tools: their
  equivalent), start the two phase-A sub-agents in the same turn so they run in parallel. Sub-agents do not see this
  conversation: send each one the brief below, filled in.
- If your tool has no sub-agents, or a sub-agent stops before its checks pass, do that role yourself by following its
  section: the result must be the same. When a sub-agent returns, verify its claims (files exist, re-run its checks)
  before moving on, and tick the plan.

Brief (replace every `<...>`):
```
You are the <Backend | UI-design | UI-build> sub-agent for feature `<key>` in the repository at <absolute repo path>.
Work autonomously until your role is done; never ask questions. Read docs/prompt/02-implement-feature.md sections
4 (rules), 12 (pitfalls) and <9 | 10 | 11> (your role), then do your role exactly as written there.
Inputs: docs/business/<key>.md (source of truth; section 8 starts with "### Giao diện đã chốt (UI concept)"),
docs/plans/<key>-implementation-plan.md (controller contract: use its method and DTO names exactly)<UI-build only:
, docs/plans/<key>-ui-design.md>.
Write ONLY in <backend/features/<key>/ | docs/plans/<key>-ui-design.md | frontend/features/<key>/>. Never touch other
files, never git commit.
When finished, reply with: files created/changed, <controller methods with signatures | screens designed | pages
built>, the checks you ran with their exact result, and your assumptions.
```

## 8. Step 4 - Integrate (lead)
1. **Gateway registration check** (rule 3): run the command of section 3. It must list exactly one method per `UC-xx`
   (plus `ping` until step 3 below).
2. **Navigation check** (rule 4): `FEATURE.pages` lists every page in the order of the design, first = landing page;
   title, description, icon, Home group and owner match the document header.
3. **Remove the scaffold `ping`** once no page uses it: `dto/ping_dto.py`, `services/ping_service.py`, the controller
   method `ping` and its imports, `tests/test_ping_service.py`.
4. If the UI-build sub-agent reported missing backend pieces: add them (section 9 rules), then finish the pages
   (section 11 rules).
5. **Document:** fill section 11 from the matrix, add `Giả định (triển khai)` lines to section 10, set `Status` to
   `Implemented`. Do not change sections 1-9 beyond Step 0.
6. Quality gate: `--fix`, then run until `ALL CHECKS PASSED`.

## 9. Role: Backend (writes only `backend/features/<key>/`)
Read first: `CLAUDE.md`, `docs/rules/00`-`03`, `06`, `07`, `09`, the business document, the plan, and all files of
`backend/features/sample_product_import/`. Implement in this order, without pauses:
1. **models/** - `BaseEntity` (has `id`, `created_at`, `updated_at`), `BaseValueObject` (immutable), `StrEnum` for every
   status / list of values. Pydantic `Field` constraints; money/quantities `Decimal`; self-contained properties only.
2. **business/** - `BaseBusinessRule[T]` per validation BR (`code`, `message` = exact Vietnamese text from section 7,
   `field`, `is_satisfied_by`, optional `describe_violation`); `BaseBusiness[T]` classes with `rules()`, calculations,
   decisions, state transitions. Pure. Write the BR unit tests now (a passing and a failing case each).
3. **constants.py / exceptions.py** - UPPER_CASE constants only (column specs, limits); errors inherit `AppError` /
   `FileProcessingError` with Vietnamese messages.
4. **repositories/** - `class XRepository(JsonFileRepository[X]): storage_file = "x.json"` + simple queries.
5. **builders/** - `BaseBuilder[T]` (inputs in `__init__`, `build()` returns output): file -> models (`ExcelReader`,
   `WordReader`, `PdfTextReader` from `backend.shared.file_io`; `normalize_key`, `parse_decimal` from
   `backend.shared.utils`; `UploadedFileDTO.ensure_valid(...)`), models -> response DTOs, models -> files (`ExcelWriter`,
   `WordWriter` + `WordContent`, `WordTemplateRenderer`) returned as `FileDownloadDTO`. No business decisions.
6. **dto/** - per UC `XRequest(BaseRequestDTO)` / `XResponse(BaseResponseDTO)` with the contract names; rows `BaseDTO`;
   lists inside a response field; `EmptyRequest`, `UploadedFileDTO`, `FileDownloadDTO`; re-export model enums pages
   need. Rows coming from an editable table: a request with `rows: list[<Row>DTO]`, optional fields for empty cells.
7. **services/** - one file per UC: `class XService(BaseService[XRequest, XResponse])`, dependencies with defaults
   (`def __init__(self, repository: XRepository | None = None): self.repository = repository or XRepository()`),
   `execute()` = builder -> business -> repository -> builder, raise `AppError` subclasses for expected failures, log
   steps (inputs, counts, decisions, results). Write service tests now: happy path + each error flow, repository injected
   as `XRepository(file_path=tmp_path / "x.json")`, input files built in memory (openpyxl / python-docx).
8. **controllers/<key>_controller.py** - `class <Pascal>Controller(BaseController)`, one method per UC named as in the
   contract, body exactly `return XService().handle(request)`. KEEP the scaffold `ping` (the scaffold page still uses
   it; the lead removes it later). Keep the export in `backend/features/<key>/__init__.py`.
9. Done = `scripts/check.py --fix`, then `scripts/check.py` prints `ALL CHECKS PASSED`.

## 10. Role: UI design (writes only `docs/plans/<key>-ui-design.md`, no Python)
1. Read: `docs/rules/04-frontend-streamlit.md` (all, above all "Excel-like UI"), `frontend/core/components/*.py`,
   `frontend/core/base_page.py`, the pages of `frontend/features/sample_product_import/`, the business document
   (sections 4-9 and the UI concept) and the plan (controller contract, pages list).
2. Study the official Streamlit API reference for every element you need: https://docs.streamlit.io/develop/api-reference
   - data: `/develop/api-reference/data/st.dataframe`, `/develop/api-reference/data/st.data_editor`,
     `/develop/api-reference/data/st.column_config`; widgets: `/develop/api-reference/widgets`; layout:
     `/develop/api-reference/layout`; charts: `/develop/api-reference/charts`; dialogs:
     `/develop/api-reference/execution-flow/st.dialog`. No web access: use the table in rules/04 and the command below.
3. The site shows the LATEST Streamlit; the installed version is the truth. Check every function and parameter you plan
   to use with the "Streamlit API check" command of section 3; drop anything that does not exist. No new libraries.
4. Prefer the shared components (`data_table`, `editable_table`, `panel`, `stat_row`, `file_upload`, `download_button`,
   `empty_state`) and plain `st.*` for the rest. The users live in Excel: tables with `column_config` (Vietnamese
   labels, `NumberColumn(format="localized")`, `DateColumn(format="DD/MM/YYYY")`, `SelectboxColumn(options=...)`).
5. Write `docs/plans/<key>-ui-design.md`, per screen in menu order: page class (`XxxPage`), slug (kebab-case, not for
   the first page), title, icon, description (VI); the text sketch; blocks from top to bottom, each with the exact call
   (component or `st.*`), Vietnamese label from the document, widget key name, default value; every table: component,
   columns in order with their `column_config`, mode (read-only / selection / editable); every button: label ->
   controller method of the contract -> what the page shows after (Vietnamese success message, refreshed table,
   download); confirmations; empty-state texts; what the page shows on first load with NO data (no use case that can
   fail is called before a user action). Every element of section 8 and every UI concept decision appears.

## 11. Role: UI build (writes only `frontend/features/<key>/`)
1. Read: `docs/rules/04-frontend-streamlit.md`, the design `docs/plans/<key>-ui-design.md`, the REAL backend contract
   (`backend/features/<key>/dto/*.py` and the controller: use their actual names and fields), the pages of
   `frontend/features/sample_product_import/`.
2. **pages/** - one `BasePage` per screen of the design (first in the manifest = landing page; others need a `slug`).
   Replace the scaffold page: no page may call `ping` any more.
   ```python
   import streamlit as st

   from backend.core.gateway import gateway
   from backend.features.<key> import <Pascal>Controller
   from backend.features.<key>.dto.<file> import ListItemsRequest, SaveItemsRequest
   from frontend.core.base_page import BasePage
   from frontend.core.components import data_table, editable_table, empty_state, panel, show_success, stat_row


   class ItemListPage(BasePage):
       title = "Danh sách ..."
       icon = "📋"
       description = "..."

       def render(self) -> None:
           feature = gateway.open(<Pascal>Controller)
           with panel("Bộ lọc", icon="🔎"):
               keyword = st.text_input("Từ khoá", key=self.key("keyword"))
           data = feature.list_items(ListItemsRequest(keyword=keyword))
           stat_row([("Tổng số", data.total)])
           if not data.items:
               empty_state("Chưa có dữ liệu.", "Hãy thêm mới hoặc nhập từ Excel.")
               return
           rows = editable_table([row.model_dump() for row in data.items], key=self.key("grid"), disabled=["code"])
           if st.button("Lưu thay đổi", type="primary", key=self.key("save")):
               result = feature.save_items(SaveItemsRequest(rows=rows))
               show_success(f"Đã lưu {result.saved} dòng.")
   ```
   Components: `panel`, `stat_row`, `data_table` (with `selection=` to pick rows), `editable_table`, `frame_to_records`,
   `file_upload`, `download_button`, `empty_state`, `section_title`, `show_success`, `show_error`; formatting:
   `format_number`, `format_currency`, `format_datetime` (`frontend.core.formatting`). Widget keys `key=self.key("...")`;
   session data `self.state`; side effects only inside `if st.button(...)` (or `st.form` + `st.form_submit_button`);
   navigation `self.link_to(Page)` / `self.go_to(Page)`. `AppError` is shown automatically; catch it
   (`except AppError as exc: show_error(exc)`) only where the rest of the page must keep rendering. No
   calculations/validations/file handling in pages. Labels exactly as in the document.
3. **components/** - widgets used only by this feature (plain functions).
4. **manifest.py** - the feature's navigation: `FEATURE = FeatureManifest(key, title, description, pages=(...), icon,
   group, owner)` from the document header, every page class in the design order.
5. Never edit the backend. If the backend lacks something the design needs, build everything else and report exactly
   what is missing (the lead adds it).
6. Done = `scripts/check.py --fix`, then `scripts/check.py` prints `ALL CHECKS PASSED` (includes the headless render
   test of every page).

## 12. Pitfalls that make the quality gate fail (avoid them)
- Every folder containing `.py` needs `__init__.py`. Feature root holds only `__init__.py`, `constants.py`, `exceptions.py`.
- Classes allowed per folder: `models/` BaseEntity/BaseValueObject/Enum; `dto/` BaseDTO subclasses/Enum; `business/`
  BaseBusiness/BaseBusinessRule; `builders/` BaseBuilder; `repositories/` BaseRepository; `services/` exactly one
  BaseService per file; `controllers/` exactly one BaseController. No helper classes/dataclasses elsewhere: use a
  `BaseValueObject` in `models/` or a plain function. `constants.py` has no classes.
- Service file name = snake_case of the class: `SubmitLeaveService` -> `submit_leave_service.py`. Avoid consecutive
  capitals (`ExportPdfService`, not `ExportPDFService`).
- Each service is called by exactly ONE controller method; controller methods contain only the `return` line.
- Imports inside a feature follow the matrix in `docs/rules/02-backend-architecture.md`: business never imports dto,
  builders never import business, controllers import only services and dto, services never import services.
- Every `BR-xx` code used in code must appear in the business document; format `BR-` + 2-3 digits.
- Pages: no `open()`, no openpyxl/docx/pypdf imports, no `print`, no `XxxController()`; every page is listed in the
  manifest; non-landing pages have a `slug`.
- **Every page must render on first load with NO data and without any error box** (tested headlessly by
  `tests/architecture/test_pages_render.py`): handle empty lists with `empty_state`, don't call use cases that raise when
  nothing is selected yet, give inputs sensible defaults.
- Table rows go to DTOs only through `editable_table` / `data_table(selection=...)` / `frame_to_records` (never raw
  `DataFrame.to_dict()`: NaN breaks the DTO validation).
- Models forbid unknown fields (`extra="forbid"`); request DTOs are immutable (create a new one per call).
- Streamlit: unique widget keys; no `st.set_page_config`; no global CSS; use `width="stretch"` (not
  `use_container_width`); only functions and parameters that exist in the installed version.
- Fix loop: read each failure (it names file, line and rule), fix your code, re-run. If the same failure repeats 3 times,
  re-read the rule in `docs/rules/` and compare with the reference feature before trying again.

## 13. Step 5 - Verify (lead; all mandatory, repeat fixes until everything passes)
1. Quality gate prints `ALL CHECKS PASSED` (lint + architecture + all features' unit tests + page render tests).
2. Gap check: re-read the document line by line; every matrix row is ✅ with a real code element and a test (UI-only
   rows: covered by the page render test or the app check). The screens match `Giao diện đã chốt`. Implement anything
   missing.
3. App check: start the app (section 3), wait for the health check to return `ok`, confirm with a browser tool if you
   have one that `/home` shows the new card and the previous features and that the sidebar shows the feature with its
   pages, open each new page, walk through the ACs, confirm the log panel shows service steps; then stop the app.
   Without a browser tool, rely on the tests and the health check. On any error read `logs/app.log`, fix, re-run the
   quality gate.

## 14. Step 6 - Final report (Vietnamese, simple words, no questions)
0. Close the gate again: delete `.gate-unlock` (section 3), so the repository is locked for the next session.
1. Đã làm gì: each screen (where it is in the menu) and what each button does; how the chosen UI was applied.
2. Cách dùng: `powershell -ExecutionPolicy Bypass -File .\run.ps1`, open the feature from the Home page or the left
   menu, then click-by-click steps for each main scenario (how to get the Excel template if any).
3. Kết quả kiểm tra: `ALL CHECKS PASSED`; numbers of UC / BR / AC implemented and tested.
4. Giả định khi triển khai (from section 10), in plain words; pre-existing problems outside the scope, if any.
5. Muốn thay đổi: nghiệp vụ -> Prompt 1 rồi Prompt 2; chỉ giao diện -> write "Đổi giao diện chức năng <tên>" and paste
   Prompt 2 in the same message (the UI questions come back with the current UI as the proposal). The feature is
   updated in place and existing data is kept.
