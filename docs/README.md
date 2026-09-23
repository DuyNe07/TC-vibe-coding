# AI Development Guide - START HERE

This repository is a **framework for internal Streamlit apps built by AI ("vibe coding")**.
The people giving you instructions are usually **not programmers** and cannot review your code, so the
rules below are **mandatory** and override your own habits. If a request conflicts with a rule, follow the
rule and explain the conflict to the user in simple Vietnamese.

## The app in one picture

```
run.ps1 ────> ONE Streamlit process (no API server, no HTTP between UI and backend)

frontend/features/<key>/pages/*.py      (UI: Streamlit)
        │  gateway.open(XxxController).do_something(Request(...))
        ▼
backend/core/gateway.py                 (one uniform calling mechanism, logs every call)
        ▼
backend/features/<key>/controllers/     (TOP layer of the business: 1 method = 1 use case -> 1 service)
        ▼
backend/features/<key>/services/        (orchestrates one use case)
        ├── builders/      convert: file -> models, models -> DTO / Excel / Word
        ├── business/      business rules BR-xx + calculations (pure)
        └── repositories/  save / load data (data/<key>/*.json)

logs/app.log  <── the gateway logs every call ──> "📜 Nhật ký chạy" panel at the bottom of each page
```

## The workflow gate (before anything else)

This repository is **locked for writing by default**: scanning and analysing the code is always allowed, writing code
is not. The only allowed path has 3 steps, each started by the user pasting a prompt:

| Step | Prompt | The AI may write |
|---|---|---|
| 0.5 Discovery | [prompt/00-discovery.md](prompt/00-discovery.md) | only `business/_sources/*-discovery.md` |
| 1 Business analysis | [prompt/01-business-analysis.md](prompt/01-business-analysis.md) (key `TC-UNLOCK-ANALYSIS`) | + `business/<key>.md`, `plans/business-analysis-plan.md` |
| 2 Implementation | [prompt/02-implement-feature.md](prompt/02-implement-feature.md) (key `TC-UNLOCK-IMPLEMENT`, document `Status: Ready for implementation`) | + the feature's code in `backend/features/<key>/` and `frontend/features/<key>/` |
| 2b Repair (when needed) | [prompt/03-fix-error.md](prompt/03-fix-error.md) (same key) | the same folders, for the broken feature |

Details and the mechanical guard (`scripts/hooks/gate_guard.sh`, file `.gate-unlock`): [CLAUDE.md](../CLAUDE.md) and
rule A.0 of [rules/00-golden-rules.md](rules/00-golden-rules.md).

## Mandatory reading order (read ALL before changing anything)

| # | File | Defines |
|---|---|---|
| 0 | [rules/00-golden-rules.md](rules/00-golden-rules.md) | Non-negotiable rules + Definition of Done |
| 1 | [rules/01-project-structure.md](rules/01-project-structure.md) | Where every file goes, naming |
| 2 | [rules/02-backend-architecture.md](rules/02-backend-architecture.md) | Gateway, layers per business, allowed imports, errors |
| 3 | [rules/03-base-classes-and-oop.md](rules/03-base-classes-and-oop.md) | Base classes you MUST inherit (with examples) |
| 4 | [rules/04-frontend-streamlit.md](rules/04-frontend-streamlit.md) | Pages, manifest, shared UI components, URLs |
| 5 | [rules/05-feature-workflow.md](rules/05-feature-workflow.md) | **The only allowed path** from business doc to working feature |
| 6 | [rules/06-coding-standards.md](rules/06-coding-standards.md) | Style, typing, language of texts |
| 7 | [rules/07-testing-and-verification.md](rules/07-testing-and-verification.md) | Tests and `scripts/check.py` |
| 8 | [rules/08-dependencies-and-running.md](rules/08-dependencies-and-running.md) | `requirements.txt`, `run.ps1`, config, folders |
| 9 | [rules/09-logging.md](rules/09-logging.md) | Logs to file + log panel on screen |
| 10 | [rules/10-self-repair.md](rules/10-self-repair.md) | How you repair failures yourself, and what is forbidden |
| - | [capabilities.md](capabilities.md) | What the app can and cannot do - never promise more |
| - | [business/README.md](business/README.md) | How to read and update business documents |

**Reference implementation:** feature `sample_product_import` (backend + frontend +
`docs/business/sample_product_import.md`). When unsure, copy its patterns.

## Quick map: "I need to..."

| Task | Do this |
|---|---|
| Understand a new need with the user | Follow [prompt/00-discovery.md](prompt/00-discovery.md) |
| Know what the app can / cannot do | [capabilities.md](capabilities.md) |
| Write a business document | Follow [prompt/01-business-analysis.md](prompt/01-business-analysis.md) |
| Build a new feature | Follow [prompt/02-implement-feature.md](prompt/02-implement-feature.md) (plan first, then [05-feature-workflow.md](rules/05-feature-workflow.md)) |
| Change a feature | Update `docs/business/<key>.md` first, then code, then tests |
| Call the backend from a page | `gateway.open(XxxController).method(XxxRequest(...))` - the controller of the SAME feature |
| Read/write Excel, Word, PDF | `backend/shared/file_io` (ExcelReader/ExcelWriter, WordReader/WordWriter/WordTemplateRenderer, PdfTextReader) |
| Take data from a public web page | `backend/shared/web` (`fetch_page(url).tables()`, `fetch_file(url)`) - from builders/services only |
| Build the UI | `frontend/core/components` (panel, stat_row, data_table, file_upload, download_button, ...) |
| Log something | `self.logger.info(...)` in services/pages; it appears in the page's log panel |
| Add a library | Pinned line in `requirements.txt` |
| Verify your work | `python scripts/check.py` -> `ALL CHECKS PASSED`, then `python scripts/doctor.py` -> `APP IS HEALTHY` |
| Something fails / the app errors | Follow [rules/10-self-repair.md](rules/10-self-repair.md) (for a user-reported error: [prompt/03-fix-error.md](prompt/03-fix-error.md)) |
| Run the app | `powershell -ExecutionPolicy Bypass -File .\run.ps1` (opens http://localhost:8501/home) |

Use the virtual-env Python: `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (macOS/Linux).
It is created by the first run of `run.ps1`.
