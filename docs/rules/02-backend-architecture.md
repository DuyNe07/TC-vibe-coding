# 02 - Backend Architecture

## Decisions
1. **All-in-one**: ONE Streamlit process. The backend is a Python package imported by the pages.
   No API server, no HTTP, no JSON between UI and backend. Do not add one.
2. **One gateway**: every page runs business actions through `backend.core.gateway.gateway`.
   It is the single, uniform calling mechanism (logs every call; future permissions/audit/caching are added
   there as middlewares without touching features).
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
│    repositories/ load / save entities (data/<key>/*.json)                              │
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
Default storage = JSON files: `class ItemRepository(JsonFileRepository[Item]): storage_file = "items.json"`
stores `data/<feature_key>/items.json` (atomic, thread-safe). Do not add a database unless the user asks.
