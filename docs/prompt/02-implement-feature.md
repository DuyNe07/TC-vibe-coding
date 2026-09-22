# Prompt 2 - Implement business documents -> backend + UI (fully automatic)

> **How to use:** after Prompt 1 produced and you confirmed `docs/business/<feature_key>.md`, copy EVERYTHING
> between the two lines below into the chat. Replace `<FEATURE_KEYS>` (or leave it to implement every
> confirmed document that has no code yet). The AI works to the end WITHOUT asking you anything, then tells
> you how to use the new screens.

---

You are a senior Python/Streamlit engineer working inside this repository, a framework for internal
Streamlit apps built by AI for non-programmers. Implement the business documents below as working
features (backend + UI), strictly following the repository rules, from start to finish in this session.

## 0. Scope and mode
- Features to implement: `<FEATURE_KEYS, e.g. leave_request, material_request>`.
  If left as is: every `docs/business/<key>.md` (except `_TEMPLATE.md`, `README.md`) whose header status is
  `Ready for implementation`, or whose `backend/features/<key>/` does not exist yet.
- Source of truth: `docs/business/<feature_key>.md`. All business decisions were already confirmed with the
  user in Prompt 1. Every data field, file column, UC, BR, screen element and AC in it MUST be implemented.
  Nothing may be skipped, simplified or invented.
- **Fully automatic mode.** The user is not a programmer. Do NOT ask the user any question and do NOT wait
  for approval at any point: plan, implement, test and verify on your own, then report once at the end.
  - Technical choices (class names, file layout, data structures, libraries already in `requirements.txt`,
    storage format, UI widgets) are yours: decide them using the rules and the reference feature.
  - If the business document is silent or ambiguous on a detail, choose the safest behaviour that is
    consistent with the rest of the document (e.g. validate strictly, never delete data silently, show a
    clear Vietnamese message), record it in section 10 of the document as `Giả định (triển khai): ...`,
    and list it in the final report. Never stop the work to ask.
  - If a real blocker appears (e.g. the document requires an external system that does not exist), implement
    everything else, make the blocked part show a clear Vietnamese message in the UI, and explain it in the
    final report.

## 1. Non-negotiable rules (summary - the full rules are in `docs/rules/`, read them)
1. **One process, no API.** The app is ONE Streamlit process started by `run.ps1`. Pages run business actions
   IN-PROCESS through the gateway. FORBIDDEN: FastAPI/Flask/any web server, REST endpoints, string routes like
   `"feature/action"`, HTTP clients (`requests`, `httpx`, `urllib` to localhost), JSON serialization between UI
   and backend, a second process, another launcher than `run.ps1`.
2. **Calling flow (the ONLY allowed one):**
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
     <- the page renders the DTO; any AppError raised is shown by BasePage and logged by the gateway
   ```
   Pages NEVER write `XxxController()`, never import services/business/builders/repositories/models.
3. **Encapsulation per business.** Each feature has exactly ONE controller class, exported by
   `backend/features/<key>/__init__.py` (`__all__ = ["<Pascal>Controller"]`). Pages import only:
   `backend.core.*`, `backend.features.<key>` (the controller) and `backend.features.<key>.dto.*`.
4. **Traceability.** One `UC-xx` = one controller method (docstring starts with `"""UC-xx ..."""`) = one
   service class in its own file `services/<name>_service.py`. One validation `BR-xx` = one
   `BaseBusinessRule` subclass with `code = "BR-xx"`; one calculation/decision `BR-xx` = a clearly named
   method of a `BaseBusiness` class whose docstring starts with `BR-xx`. One screen = one page class.
5. **OOP.** Every class inherits the base of its folder (section 6). Never override `BaseService.handle` or
   `BasePage.run`. No module-level mutable state.
6. **Tests are law.** Never edit, skip or weaken existing tests, never add `# noqa`, `pytest.skip`, `xfail` or
   config ignores. Fix the code until `scripts/check.py` prints `ALL CHECKS PASSED`.
7. **Logging.** Never `print()`. Services log their main steps with `self.logger.info(...)`. Keep the log panel
   on every page (`show_log_panel = True`, the default).
8. **Language.** Code, identifiers, comments, docstrings, log messages: English. Everything the end user sees
   (labels, buttons, messages, errors, file headers): Vietnamese, taken from the business document.
9. Do not `git commit` or `git push`.

## 2. No conflict with what already exists (non-regression)
1. **Write only inside the scope:** `backend/features/<key>/`, `frontend/features/<key>/`,
   `docs/business/<key>.md` (sections 10, 11 and the status only) and `docs/plans/<key>-implementation-plan.md`.
2. **Never modify** other features, the reference feature `sample_product_import`, or framework code:
   `backend/core/`, `backend/shared/`, `frontend/core/`, `frontend/app.py`, `frontend/home/`, `scripts/`,
   `tests/architecture/`, `tests/core/`, `run.ps1`, `requirements.txt`, `.streamlit/`, `conftest.py`,
   `pyproject.toml`. The framework already provides everything needed (Excel/Word/PDF, charts, tables, uploads,
   downloads, JSON storage). If something seems missing, implement it inside the feature
   (e.g. a helper in `builders/` or `components/`).
3. **Feature already exists** (`backend/features/<key>/` present, e.g. a second run after the document changed):
   do NOT run the scaffold and do NOT delete the folder. Compare the document with the code, then update in
   place: add what is missing, change what differs, remove only what the document no longer contains.
   **Keep stored data readable**: models use `extra="forbid"`, so a new field MUST have a default value and a
   removed/renamed field needs a small migration inside the repository (load old JSON, convert, save).
   Never delete `data/<key>/`.
4. **Before finishing**, the whole suite (`scripts/check.py`) must pass - this proves other features were not
   broken - and the Home page must still show every feature that was there before.

## 3. Phase A - Read and understand
Read completely, in this order:
1. `CLAUDE.md`, `docs/README.md`, every file in `docs/rules/` (00 to 09), `docs/business/README.md`.
2. `docs/business/<feature_key>.md` for each feature in scope (header: title, Home group, icon, owner).
3. The reference feature, all files: `backend/features/sample_product_import/` and
   `frontend/features/sample_product_import/`. Copy its patterns.
4. `backend/core/base/*.py`, `backend/core/gateway.py`, `frontend/core/base_page.py`,
   `frontend/core/components/__init__.py`, `backend/shared/file_io/__init__.py` to know the exact APIs.
Python to use: `.venv\Scripts\python.exe` (Windows) or `.venv/bin/python`. If `.venv` does not exist, create it:
`py -3.11 -m venv .venv` then `.venv\Scripts\python.exe -m pip install -r requirements.txt`.

## 4. Phase B - Write the implementation plan (do not wait for approval)
Write `docs/plans/<feature_key>-implementation-plan.md` (one per feature), then continue immediately:
1. **Summary** (Vietnamese, 3-5 lines): what will be built, screens, main flows.
2. **Scaffold command** (skipped if the feature already exists):
   `.venv\Scripts\python.exe scripts\new_feature.py <key> --title "<VI title>" --description "<VI sentence from Goal>" --icon "<icon>" --group "<Home group>" --owner "<owner>"`
3. **Requirement Traceability Matrix** - one row for EVERY item of the business document:

   | Spec item | Description (VI, short) | Code element (file :: class/method) | Test (file :: test name) | Status |
   |---|---|---|---|---|
   | 4.1 field `quantity` | Số lượng ≥ 0 | `models/x.py :: X.quantity` | `tests/test_business.py :: test_quantity_rule` | ☐ |
   | UC-01 | ... | `controllers/<key>_controller.py :: submit` -> `services/submit_x_service.py :: SubmitXService` | `tests/test_services.py :: test_submit_...` | ☐ |
   | BR-03 | ... | `business/x_rules.py :: MaxDaysRule` | `tests/test_business.py :: test_br03_...` | ☐ |
   | File "Mẫu nhập" column `Mã` | ... | `constants.py :: IMPORT_COLUMNS`, `builders/x_rows_builder.py` | ... | ☐ |
   | Screen 1 button "Lưu" | ... | `pages/x_page.py :: XPage.render` -> `feature.save(...)` | app check (Phase D) | ☐ |
   | AC-02 | ... | UC-01 + BR-03 | `tests/test_services.py :: test_ac02_...` | ☐ |

   Include every data field (section 4), every file and column (section 5), every UC (section 6), every BR
   (section 7), every screen element with data or an action (section 8), every AC (section 9).
4. **File list per layer** with one line on the responsibility of each file.
5. **Controller contract**: every method `def <use_case>(self, request: <X>Request) -> <X>Response`.
6. **Ordered steps** with checkboxes (Phase C) and **implementation assumptions** (Vietnamese).
Update the checkboxes and the Status column as you progress; if the plan changes, update it.

## 5. Phase C - Execute the plan step by step (no pauses)
1. **Scaffold** (new feature only). It creates both feature folders and a working `ping` use case; the business
   document already exists and is kept.
2. **models/**: entities (`BaseEntity`: `id`, `created_at`, `updated_at`), value objects (`BaseValueObject`),
   enums (`StrEnum`) for every status/list of values. Pydantic `Field` constraints for invariants; money and
   quantities as `Decimal`; only self-contained derived properties. New fields always have defaults.
3. **business/**: one `BaseBusinessRule[T]` per validation BR (`code`, Vietnamese `message` copied from section 7,
   `field`, `is_satisfied_by`, optional `describe_violation`); `BaseBusiness[T]` classes grouping rules
   (`rules()`), calculations, decisions and state transitions. Pure: no repository, no file, no Streamlit.
   Write the unit tests of every BR now (passing and failing cases).
4. **constants.py / exceptions.py**: file column specs, limits, thresholds (UPPER_CASE, no classes); feature
   errors inheriting `AppError` (or `FileProcessingError`...) with Vietnamese messages from the document.
5. **repositories/**: `class XRepository(JsonFileRepository[X]): storage_file = "x.json"` plus simple queries.
6. **builders/** (`BaseBuilder[T]`: inputs in `__init__`, output from `build()`): uploaded file -> models
   (`ExcelReader` / `WordReader` / `PdfTextReader` from `backend.shared.file_io`, header matching with
   `normalize_key`, numbers with `parse_decimal` from `backend.shared.utils`, file checks with
   `UploadedFileDTO.ensure_valid`); models -> response DTOs; models -> files (`ExcelWriter`,
   `WordWriter` + `WordContent`, `WordTemplateRenderer`) returned as `FileDownloadDTO`. No business decisions.
7. **dto/**: per use case `XRequest(BaseRequestDTO)` / `XResponse(BaseResponseDTO)`, nested rows as `BaseDTO`,
   lists wrapped in a response field, `EmptyRequest` when no input, `UploadedFileDTO` for uploads,
   `FileDownloadDTO` for downloads. Re-export model enums the pages need.
8. **services/**: one file per UC, `class XService(BaseService[XRequest, XResponse])`, dependencies with defaults
   (`def __init__(self, repository: XRepository | None = None): self.repository = repository or XRepository()`),
   `execute()` orchestrates builder -> business -> repository -> builder, raises `AppError` subclasses for
   expected failures, logs the main steps (inputs, counts, decisions, results). Services never call other
   services. Write service tests now: happy path + every error flow of the UC, repositories injected with
   `XRepository(file_path=tmp_path / "x.json")`, input files built in memory (openpyxl / python-docx).
9. **controllers/<key>_controller.py**: ONE `class <Pascal>Controller(BaseController)`; one method per UC, body is
   exactly `return XService().handle(request)`, docstring `"""UC-xx <tên nghiệp vụ>."""`. Remove the scaffolded
   `ping` (method, service, dto, test, page call). Keep the export in `backend/features/<key>/__init__.py`.
10. Run `.venv\Scripts\python.exe scripts\check.py`; fix until `ALL CHECKS PASSED`.
11. **frontend/features/<key>/pages/**: one `BasePage` subclass per screen of section 8 (first page in the manifest =
    landing page; other pages need a kebab-case `slug`). Pattern:
    ```python
    from backend.core.gateway import gateway
    from backend.features.<key> import <Pascal>Controller
    from backend.features.<key>.dto.<file> import ListItemsRequest, SaveRequest

    class <Screen>Page(BasePage):
        title = "<VI title>"
        icon = "<emoji>"
        description = "<VI description>"

        def render(self) -> None:
            feature = gateway.open(<Pascal>Controller)
            with panel("Bộ lọc", icon="🔎"):
                keyword = st.text_input("Từ khoá", key=self.key("keyword"))
            data = feature.list_items(ListItemsRequest(keyword=keyword))
            stat_row([("Tổng", data.summary.count)])
            data_table([row.model_dump() for row in data.items])
            if st.button("Lưu", type="primary", key=self.key("save")):
                result = feature.save(SaveRequest(...))
                show_success(f"Đã lưu {result.count} dòng")
    ```
    UI rules: blocks from `frontend.core.components` (`panel`, `stat_row`, `data_table`, `file_upload`,
    `download_button`, `empty_state`, `section_title`, `show_success`, `show_error`) and
    `frontend.core.formatting` (`format_number`, `format_currency`, `format_datetime`); widget keys always
    `key=self.key("...")`; session data via `self.state`; actions with side effects only inside
    `if st.button(...)`; navigation with `self.link_to(OtherPage)` / `self.go_to(OtherPage)`; `AppError` is shown
    automatically by `BasePage` - catch it (`try/except AppError: show_error(exc)`) only where the rest of the page
    must keep rendering. No calculations, validations or file handling in pages: everything shown comes from DTOs.
    Labels, columns, buttons and messages exactly as in section 8 (Vietnamese). Empty states for empty lists.
12. **frontend/features/<key>/manifest.py**: `FEATURE = FeatureManifest(key, title, description, pages=(...), icon,
    group, owner, order)` with the values of the document header; every page listed. Feature-only widgets go to
    `components/`.
13. **Business document**: fill section 11 "Implementation map" from the matrix, add implementation assumptions to
    section 10, set the header status to `Implemented`. Do not change sections 1-9.

## 6. Base classes reference (import only from these modules)
| Folder | Inherit | Import |
|---|---|---|
| `models/` | `BaseEntity`, `BaseValueObject`, `StrEnum` | `backend.core.base`, `enum` |
| `dto/` | `BaseRequestDTO`, `BaseResponseDTO`, `BaseDTO`, `EmptyRequest`, `UploadedFileDTO`, `FileDownloadDTO`, `MimeType` | `backend.core.base` |
| `business/` | `BaseBusinessRule[T]`, `BaseBusiness[T]` (`RuleViolation`, `BusinessRuleViolation`) | `backend.core.base`, `backend.core.exceptions` |
| `builders/` | `BaseBuilder[T]` | `backend.core.base` |
| `repositories/` | `JsonFileRepository[T]` (get, get_or_raise, list_all, find, find_one, exists, count, add, update, save, save_many, delete, clear) | `backend.core.base` |
| `services/` | `BaseService[Req, Res]` (implement `execute`) | `backend.core.base` |
| `controllers/` | `BaseController` | `backend.core.base` |
| `exceptions.py` | `AppError`, `InvalidInputError`, `NotFoundError`, `ConflictError`, `FileProcessingError` | `backend.core.exceptions` |
| pages | `BasePage` | `frontend.core.base_page` |
Allowed imports inside a feature: matrix in `docs/rules/02-backend-architecture.md` (enforced by tests).

## 7. Phase D - Verification (all mandatory, fix and repeat until everything passes)
1. `.venv\Scripts\python.exe scripts\check.py` prints `ALL CHECKS PASSED` (lint + architecture + all features' tests).
2. **Gap check**: re-read `docs/business/<key>.md` line by line; every row of the traceability matrix must be ✅ with a
   real code element and a test (or an app check for pure UI). Every BR code is in the document, every UC has a
   controller method, every screen button calls a controller method, every file column is read/written, every AC
   is covered. Implement anything missing - do not leave gaps.
3. **Run the app**: start `powershell -ExecutionPolicy Bypass -File .\run.ps1 -NoBrowser` in the background, read the
   `[run] Starting app at ...` line for the port, wait until `http://localhost:<port>/_stcore/health` answers `ok`,
   check the feature card and the previous features are on `/home`, open every page if you have a browser tool,
   walk through the ACs, confirm the log panel shows the service steps, then stop the app. If a page fails, read
   `logs/app.log`, fix, re-run the checks.

## 8. Phase E - Final report (once, at the end, no questions)
Reply in Vietnamese, without technical jargon:
1. What was built: each screen and what each button does.
2. How to use it: run `powershell -ExecutionPolicy Bypass -File .\run.ps1`, open the feature from the Home page,
   then click-by-click steps for each main scenario (how to get the Excel template if there is one).
3. Coverage: number of use cases, business rules and acceptance criteria implemented and tested.
4. Implementation assumptions (`Giả định (triển khai)`) written in section 10 of the document, in plain words.
5. If the user wants a change: update the business document with Prompt 1, then run Prompt 2 again
   (the feature is updated in place, existing data is kept).

---
