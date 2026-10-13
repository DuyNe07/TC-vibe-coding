# 02 - Backend Architecture

## Decisions
1. **All-in-one**: ONE Streamlit process. The backend is a Python package imported by the pages.
   No API server, no HTTP, no JSON between UI and backend. Do not add one.
2. **One gateway**: every page runs business actions through `backend.core.gateway.gateway`.
   It is the single, uniform calling mechanism (logs every call, and its `PermissionMiddleware` refuses a feature
   the logged-in user may not open; audit/caching are added there as middlewares without touching features).
3. **Each business is packaged**: a feature exposes ONE top layer - its controller - exported by the
   package root `backend/features/<key>/__init__.py`. Everything below it is internal to the feature.

```python
# frontend/features/leave_request/pages/submit_page.py
from backend.core.gateway import gateway
from backend.features.leave_request import LeaveRequestController  # the top layer only
from backend.features.leave_request.dto.submit_dto import SubmitLeaveRequest

leave = gateway.open(LeaveRequestController)
result = leave.submit(SubmitLeaveRequest(days=2, reason="Việc riêng"))  # typed result DTO
```

## Layers (top -> bottom), condensed per business

```
Page (frontend)
  │  gateway.open(XxxController).use_case(request_dto)
  ▼
Gateway (backend/core/gateway.py)          uniform mechanism: middlewares + log "<Controller>.<action> done in N ms"
  ▼
┌─ backend/features/<key>/ ──────────────────────────────────────────────────────────┐
│ 1. controllers/  XxxController       TOP layer, the only public entry of the business │
│        one method per use case:  return XxxService().handle(request)                 │
│ 2. services/     XxxService          one use case: orchestrates the layers below      │
│ 3. business/     rules BR-xx + decisions (pure)                                        │
│    builders/     conversions: file -> models, models -> DTO / Excel / Word             │
│    repositories/ load / save entities (table <developer>__<key>__<name>)              │
│ 4. models/       entities, value objects, enums                                        │
│    dto/          input / output of use cases (shared with the page)                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```
A layer only calls the layers below it. Errors (`AppError`) bubble up; the gateway logs them and
`BasePage` shows the message to the user.

## Layer responsibilities

| Layer | Does | MUST NOT |
|---|---|---|
| `controllers/` | ONE class per feature; one method per use case, one line delegating to one service | Any other logic; be created by pages (use `gateway.open`) |
| `services/` | ONE use case: builder -> business -> repository -> builder; logs main steps | Call other services, contain business rules, touch the UI |
| `business/` | Business rules (BR-xx), decisions, calculations - pure functions of their inputs | Repositories, files, services, Streamlit |
| `builders/` | Conversions: uploaded file -> models, models -> response DTO, models -> files | Business decisions, repositories |
| `repositories/` | Save/load entities of one type, simple queries | Business rules |
| `models/` | Data shape, field constraints, self-contained properties (`total = qty * price`) | I/O, rules involving other objects |
| `dto/` | Input/output of use cases. May re-export model enums | Logic |

## Shared helpers (`backend/shared/`) - use them instead of the raw libraries
| Module | Gives you |
|---|---|
| `file_io` | `ExcelReader/ExcelWriter`, `WordReader/WordWriter/WordContent/WordTemplateRenderer`, `PdfTextReader` |
| `web` | `fetch_page(url)` -> `WebPage` (`.text()`, `.tables()`, `.links()`, `.find_texts(xpath)`), `fetch_file(url)` -> `(bytes, filename)`, `WebFetchError`. Public pages only (no login, no JavaScript); call it from `builders/` or `services/`, never from a page |
| `utils` | `strip_accents`, `normalize_key`, `parse_decimal` |

## Allowed imports inside a feature (enforced by `tests/architecture/test_imports.py`)
`backend.core.*` and `backend.shared.*` are always allowed.

| From \ may import | models | dto | business | builders | repositories | services | constants | exceptions |
|---|---|---|---|---|---|---|---|---|
| models | ✔ | | | | | | | |
| constants | ✔ | | | | | | | |
| dto | ✔ | ✔ | | | | | | |
| business | ✔ | | ✔ | | | | ✔ | ✔ |
| builders | ✔ | ✔ | | ✔ | | | ✔ | ✔ |
| repositories | ✔ | | | | ✔ | | ✔ | ✔ |
| services | ✔ | ✔ | ✔ | ✔ | ✔ | ✘ | ✔ | ✔ |
| controllers | | ✔ | | | | ✔ | | |

Global rules:
- `backend/**` never imports `streamlit` or `frontend`.
- `backend/features/<A>` never imports `backend/features/<B>`.
- `backend/core` imports nothing from `shared` or `features`; `backend/shared` imports only `core`.
- Pages import only: `backend.core.*`, `backend.features.<same key>` (root = controller) and
  `backend.features.<same key>.dto.*`. Pages never write `XxxController()` - always `gateway.open(XxxController)`.

## Use case contract
- Input: one `BaseRequestDTO` subclass (`EmptyRequest` when there is no input).
- Output: one `BaseResponseDTO` subclass; lists are wrapped (`ItemListResponse(items=[...])`);
  generated files return `FileDownloadDTO`.
- Services receive dependencies with defaults so tests can inject them:
  `def __init__(self, repository: ItemRepository | None = None): self.repository = repository or ItemRepository()`

## Extending the calling mechanism (framework owners only)
```python
class AuditMiddleware(GatewayMiddleware):
    def handle(self, call, proceed):
        result = proceed(call)  # call.feature_key, call.name, call.request are available
        ...  # e.g. write an audit record
        return result


gateway.use(AuditMiddleware())  # registered once in the framework, never in a feature
```

## Errors
Raise, never return error codes.

| Situation | Raise |
|---|---|
| Bad input, wrong file type | `InvalidInputError` (automatic for DTO validation) |
| Business rule violated | `BusinessRuleViolation` (via `business.ensure_valid(...)` / `rule.check(...)`) |
| Record not found | `NotFoundError` (automatic in `repository.get_or_raise`) |
| Duplicate | `ConflictError` |
| File unreadable / wrong template | `FileProcessingError` or a subclass in `<feature>/exceptions.py` |
Any other exception is shown as an unexpected error with its traceback, and logged.

## Persistence
Default storage = the app database: `class ItemRepository(SqlRepository[Item]): pass` stores every `Item` as one
JSON document in table `<developer>__<feature_key>__item` (created automatically; `table_name = "..."` replaces `item`).
- ONE PostgreSQL database is shared by every developer and every feature: each feature declares the GitHub username of
  its developer in `backend/features/<key>/__init__.py`: `DEVELOPER = "Xuan2894"` -> tables `xuan2894__<key>__...`
  (lower case, `-` -> `_`, at most 63 characters). Set by `scripts/new_feature.py --developer`; checked by
  `tests/architecture/test_structure.py`. Never change it once data exists (the tables would start empty).
- Database = PostgreSQL from `POSTGRES_IP/PORT/DB/USER/PASSWORD` in `.env`; without them a local SQLite file
  `data/app.db`; `APP_DATABASE_URL` overrides both. Tests always get a throw-away SQLite database (`conftest.py`).
- `backend/core/db.py` runs SQLAlchemy 2 **async** (asyncpg / aiosqlite) on one background event loop; repositories
  keep a plain sync API (`get`, `list_all`, `find`, `add`, `update`, `save`, `save_many`, `delete`, `clear`), so
  services stay synchronous. Features never import `sqlalchemy` or `backend.core.db` directly.
- **RAM cache (automatic).** A repository keeps its whole table in RAM after the first read; this process's writes
  clear it at once, other processes' writes show after `APP_DB_CACHE_SECONDS` (default 30). Entities read are
  shared: change them with `entity.model_copy(update={...})` and save, never in place.
- **Read-only use cases:** decorate the controller method with `@cached_query` (from `backend.core.base`). The gateway
  keeps the result in RAM (LRU, 256 results) until any data is written, so page reruns do not recompute lists, price
  tables or generated files. Never on a use case that writes, reads an uploaded file, or depends on the current user.
- `JsonFileRepository` (files in `data/<key>/`) remains for file-shaped data only; `InMemoryRepository` for tests.

## Users and permissions (framework: `backend/core/access.py`, `backend/core/current_user.py`)
- Login is required for every page. Built-in administrator: `u-admin` (first password `u-admin`), full rights.
  A login survives page reloads (F5): cookie `tc_session` -> table `core__session`, `APP_SESSION_HOURS` (default 12);
  logout or deactivating the user ends it.
- Rights are given **per app** (= feature). Permission keys: `"<feature_key>"` = the whole app (also its future pages),
  `"<feature_key>/<page_slug>"` = one page (landing page without slug: `"<feature_key>/main"`). A user's rights =
  personal keys + keys of all their groups (union). `AccessManager.set_rights_in_app(app_key, users, groups)` replaces
  the rights in ONE app of the given user / group ids and keeps their rights in other apps.
- Enforcement is automatic: the router registers only the pages the user may open (menu, Home and URLs), and the
  gateway refuses any controller call of a feature the user has no key on. Features write NO permission code.
- Administrators grant rights on the page "Người dùng & phân quyền", opened by typing the URL `/admin` (it is not in
  the menu; non-admins get no such page): pick an app, tick the screens per user / group in one grid, save.
  Accounts and groups (members) are managed in the other two tabs.
- `self.current_user` (services and pages) is the logged-in `CurrentUser` (`None` in tests): use it to record
  "who did it", never to re-implement access checks. Finer rules (e.g. "Sales only edits its own requests") are
  business rules BR-xx in `business/`, written in the business document.
- **Roles inside an app.** When the business document gives actors different rights inside one app ("only Phòng SO
  edits master data", "Xưởng S1 only changes S1 data"), declare the actors as roles in the manifest:
  `roles=(("SO", "Phòng SO"), ("XS1", "Xưởng S1"), ...)`. The administrator ticks them per user / group on `/admin`
  (key `"<key>/@<CODE>"`). The business rule reads `self.current_user.roles_in("<key>")` (a set of codes); a `None`
  user is system code / tests (allowed); administrators get no role automatically, the rule decides (usually "admin =
  every role"). NEVER build a login, an access code, a "who are you" picker or a user list inside a feature: who acted
  is `self.current_user` (record `username` + `display_name`).
