# 01 - Project Structure

The layout follows the Node.js / NestJS module style: **one folder per feature**, and inside it one folder
per layer (models, dto, services, controllers...). Adding a feature = adding folders, never editing
another feature -> features grow horizontally without conflicts.

```
TC-vibe-coding/
├── run.ps1                     # the ONLY launcher (PowerShell): venv + install + start Streamlit + open /home
├── requirements.txt            # the ONLY dependency list (exact pins)
├── pyproject.toml              # ruff + pytest config
├── conftest.py                 # tests never write to the real data/ folder
├── .env.example                # copied to .env by run.ps1 (APP_NAME, APP_PORT, ...)
├── .streamlit/config.toml      # Streamlit settings (headless, theme, upload size)
├── .claude/settings.json       # hooks: workflow gate (SessionStart + PreToolUse) + check.py after changes
├── .gate-unlock                # only while implementing (created/removed by Prompt 2); never committed
├── CLAUDE.md / AGENTS.md       # entry point for AI tools -> docs/README.md
│
├── docs/
│   ├── README.md               # START HERE
│   ├── capabilities.md         # what the app can and cannot do (check before promising anything)
│   ├── rules/                  # mandatory rules (this folder)
│   ├── business/               # one business document per feature: <feature_key>.md (+ _sources/ raw material)
│   ├── plans/                  # plans written by the AI before coding: <feature_key>-implementation-plan.md
│   └── prompt/                 # prompts for users: 00 discovery, 01 analysis, 02 implementation, 03 fix an error
│
├── backend/                    # pure Python, no Streamlit
│   ├── core/                   # FRAMEWORK - do not modify for a feature
│   │   ├── base/               # BaseEntity, BaseDTO, BaseRepository, BaseBusiness, BaseBuilder,
│   │   │                       # BaseService, BaseController
│   │   ├── gateway.py          # gateway.open(XxxController): the ONE way pages call a business
│   │   ├── config.py           # get_settings()
│   │   ├── logger.py           # get_logger(), read_log_entries()
│   │   ├── exceptions.py       # AppError hierarchy
│   │   └── naming.py           # naming conventions
│   ├── shared/                 # generic helpers: file_io (Excel/Word/PDF), web (public pages), utils (text, numbers)
│   └── features/
│       └── <feature_key>/
│           ├── __init__.py     # public API: exports the feature's ONE controller (top layer)
│           ├── constants.py    # UPPER_CASE constants only
│           ├── exceptions.py   # feature errors (inherit AppError)
│           ├── models/         # entities, value objects, enums
│           ├── dto/            # input/output of use cases
│           ├── business/       # business rules BR-xx + calculations (pure)
│           ├── builders/       # conversions (file <-> models <-> DTO / generated files)
│           ├── repositories/   # persistence
│           ├── services/       # one file = one use case
│           ├── controllers/    # <feature_key>_controller.py: the ONE top-layer class, opened via the gateway
│           └── tests/          # unit tests of this feature
│
├── frontend/                   # Streamlit UI
│   ├── app.py                  # entry point (never edit to add a feature)
│   ├── core/                   # FRAMEWORK: AppShell, Router, BasePage, FeatureManifest, theme, branding
│   ├── public/                 # static assets: logo.png (browser tab icon), Logo_TC.png (UI logo)
│   │   └── components/         # shared UI: header, panel, sidebar menu, footer, table, files, log panel
│   ├── home/home_page.py       # /home: feature cards (generated)
│   └── features/
│       └── <feature_key>/
│           ├── __init__.py
│           ├── manifest.py     # FEATURE = FeatureManifest(...) -> card on Home + sidebar menu
│           ├── pages/          # BasePage subclasses (first page = landing page)
│           └── components/     # widgets used only by this feature
│
├── scripts/
│   ├── new_feature.py          # scaffold a feature (the only way to create one)
│   ├── check.py                # lint + all tests = Definition of Done
│   ├── doctor.py               # end-to-end self-check: checks + features load + the app really starts
│   └── hooks/                  # Claude Code hooks: session_start.sh + gate_guard.sh (workflow gate),
│                               # stop_guard.sh (runs check.py before finishing)
├── tests/
│   ├── architecture/           # enforces these rules (never edit)
│   └── core/                   # tests of the framework
├── data/                       # runtime data, git-ignored (data/<feature_key>/...)
└── logs/                       # runtime logs, git-ignored (logs/app.log)
```

## Naming
| Item | Convention | Example |
|---|---|---|
| Feature key | snake_case, 3-50 chars, same in backend/frontend/docs | `leave_request` |
| URL | key with `-`; other pages add `-<slug>` | `/leave-request`, `/leave-request-history` |
| Service | class `XxxService` in `services/xxx_service.py`, one per file | `SubmitLeaveService` -> `submit_leave_service.py` |
| Controller | ONE class `XxxController` in `controllers/<key>_controller.py`, exported by the feature `__init__.py` | `LeaveRequestController` |
| Controller method | snake_case verb, = use case | `submit`, `list_mine`, `export_report` |
| DTO | `XxxRequest` / `XxxResponse`, grouped by use case in `dto/xxx_dto.py` | `SubmitLeaveRequest` |
| Business rule | class `XxxRule`, `code = "BR-01"` (same ID as the business doc) | `MaxLeaveDaysRule` |
| Page | class `XxxPage` in `pages/xxx_page.py` | `SubmitLeavePage` |

## Allowed files in a feature root
Backend: `__init__.py`, `constants.py`, `exceptions.py` only (everything else goes in a layer folder).
Frontend: `__init__.py`, `manifest.py` only. No other folders than the ones listed above.
