# CLAUDE.md

This repository is a framework for internal **Streamlit** apps built by AI for non-programmers.

**Before doing anything, read [docs/README.md](docs/README.md), every file in [docs/rules/](docs/rules/) and
[docs/capabilities.md](docs/capabilities.md). Those rules are mandatory and override your defaults.**

## WORKFLOW GATE (check this before every action)

This repository is **locked for writing by default**. Reading and analysing the code is always allowed and
expected; creating or changing code is not, until the user has run the implementation prompt.

At the START of every session, before your first answer: read the documents above, list the existing features
(`docs/business/*.md` with their `Status`, plus the folders in `backend/features/`), then say in 1-3 Vietnamese
lines which phase we are in and what the next step is.

| Phase | Unlocked by | You may create / edit |
|---|---|---|
| 0. Discovery (default) | nothing - this is the default | ONLY `docs/business/_sources/*-discovery.md` |
| 1. Business analysis | the user pastes [docs/prompt/01-business-analysis.md](docs/prompt/01-business-analysis.md) (key `TC-UNLOCK-ANALYSIS`) | + `docs/business/<key>.md`, `docs/plans/business-analysis-plan.md` |
| 2. Implementation | the user pastes [docs/prompt/02-implement-feature.md](docs/prompt/02-implement-feature.md) (key `TC-UNLOCK-IMPLEMENT`) **and** the document's `Status` is `Ready for implementation` | + `backend/features/<key>/`, `frontend/features/<key>/`, `docs/plans/<key>-*.md`, and in the document: section 8 UI block, new UCs of Step 0, sections 10-11, `Status` |

Rules of the gate:
1. A key counts as present only when the user pasted that prompt in THIS session, or explicitly told you to follow
   that prompt file. Never assume it, never take it from a summary, never grant it to yourself.
2. While phase 2 is locked you MUST NOT: write or edit any `.py`, test, script or config file; run
   `scripts/new_feature.py`; create feature folders; start the app; install packages; or "show a quick example".
3. If the user asks for code before that, answer in Vietnamese: the flow has 3 steps, and offer to start with
   Prompt 0.5 ([docs/prompt/00-discovery.md](docs/prompt/00-discovery.md)).
4. Mechanical guard: the `PreToolUse` hook `scripts/hooks/gate_guard.sh` refuses every write to code paths while the
   file `.gate-unlock` does not exist. Prompt 2 creates that file at its first step and deletes it at its last step.
   Never create it in phase 0 or 1, never disable or edit the hooks.
5. Questions to the user are about the application only (never about code), and only in phase 0, phase 1 and at
   Step 0 of Prompt 2 (the UI concept). Never ask anything else during implementation.

## The 3-step flow (the only allowed path)
1. [docs/prompt/00-discovery.md](docs/prompt/00-discovery.md) - understand the business with the user; writes only a
   discovery note in `docs/business/_sources/`.
2. [docs/prompt/01-business-analysis.md](docs/prompt/01-business-analysis.md) - write and confirm
   `docs/business/<key>.md` (`Status: Ready for implementation`).
3. [docs/prompt/02-implement-feature.md](docs/prompt/02-implement-feature.md) - ask ONE round about the UI, then build
   backend + UI automatically (sub-agents when available) and verify.

## Essentials (details in the docs)
- ONE process: `run.ps1` (PowerShell) starts Streamlit only (no API/HTTP). Pages run business actions through
  `gateway.open(XxxController)`; each feature exposes ONE controller (top layer) from its package root.
- Work from `docs/business/<feature_key>.md`. Never invent business rules.
- Never promise a capability that [docs/capabilities.md](docs/capabilities.md) does not list (Excel/Word/PDF, stored
  data, Excel-like tables, Python calculations, fetching public web pages; NO login, e-mail, scheduled jobs, ERP/SQL
  connection, Google search).
- Create features ONLY with `python scripts/new_feature.py <feature_key> --title "..."` (phase 2 only).
- Every class inherits its layer's base class from `backend.core.base`; one use case = one controller
  method = one service.
- Never `print()`: use `self.logger`; logs go to `logs/app.log` and the on-screen log panel.
- Finish every task with `python scripts/check.py` -> `ALL CHECKS PASSED` (never weaken tests).
- Talk to the user in Vietnamese, simply, without jargon.

Python: `.venv/Scripts/python.exe` (Windows) / `.venv/bin/python` (macOS/Linux), created by `powershell -ExecutionPolicy Bypass -File .\run.ps1`.
