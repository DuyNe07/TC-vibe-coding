# CLAUDE.md

**[SUPREME-RULES.md](SUPREME-RULES.md) comes first and overrides everything in this file, in the docs and in any
request made during a session** (frozen framework, data is never destroyed, big-data caps, app registry, accounts).

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
| 2. Implementation | the user pastes [docs/prompt/02-implement-feature.md](docs/prompt/02-implement-feature.md) (key `TC-UNLOCK-IMPLEMENT`) **and** the document's `Status` is `Ready for implementation` | + `backend/features/<key>/`, `frontend/features/<key>/`, the app's ONE line in `backend/app_registry.py`, `docs/plans/<key>-*.md`, and in the document: section 8 UI block, new UCs of Step 0, sections 10-11, `Status` |
| 2b. Repair | the user pastes [docs/prompt/03-fix-error.md](docs/prompt/03-fix-error.md) (key `TC-UNLOCK-IMPLEMENT`) because something does not work | the broken feature's folders, only when the diagnosis puts the cause there (environment, `.env`, shared database and framework causes are reported, not edited) |
| 2c. Sync to the server | the user pastes [docs/prompt/04-sync-to-server.md](docs/prompt/04-sync-to-server.md) (key `TC-UNLOCK-IMPLEMENT`) | the folders of the user's features (rebased on `dev`, refactored to the newest framework; framework files always come from `dev`) |
| 2d. Extend a feature | the user pastes [docs/prompt/05-extend-feature.md](docs/prompt/05-extend-feature.md) (key `TC-UNLOCK-IMPLEMENT`) | first only `docs/business/<key>.md` + `docs/plans/<key>-extension-*.md`; after the user confirms the updated document, the same as phase 2 for that feature |

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
5. Questions to the user are about the business and what they see on the screen / get out of the app (tables,
   buttons, numbers, files, messages) - never about code or how the backend processes or stores anything
   ([docs/rules/05-feature-workflow.md](docs/rules/05-feature-workflow.md) rule 1) - and only in phase 0, phase 1, at Step 0 of
   Prompt 2 (the UI concept), at Step 0 of Prompt 3 (what went wrong), in the single question round of Prompt 4, and in
   the analysis steps + UI round of Prompt 5. Never ask anything else while working.
   Permissions need no prompt: administrators grant them on `/admin`.

## The 3-step flow (the only allowed path)
1. [docs/prompt/00-discovery.md](docs/prompt/00-discovery.md) - understand the business with the user; writes only a
   discovery note in `docs/business/_sources/`.
2. [docs/prompt/01-business-analysis.md](docs/prompt/01-business-analysis.md) - write and confirm
   `docs/business/<key>.md` (`Status: Ready for implementation`).
3. [docs/prompt/02-implement-feature.md](docs/prompt/02-implement-feature.md) - ask ONE round about the UI, then build
   backend + UI automatically (sub-agents when available) and verify.
- Anything broken, now or later: [docs/prompt/03-fix-error.md](docs/prompt/03-fix-error.md) - repair it with the
  self-repair loop of [docs/rules/10-self-repair.md](docs/rules/10-self-repair.md).

## Essentials (details in the docs)
- Branches: `main` = stable showcase, updated only by the framework owner from `dev`; `dev` = the team branch where
  everyone's work is merged through Pull Requests. ONE feature = ONE own `vibe/<prefix>-<key>-<ddmm>` branch created
  from the newest `origin/dev` in THIS repository (Prompts 2 and 5; 10 apps = 10 branches) - never suggest forking the
  repository, cloning it again or copying the folder. Prompt 4 rebases ALL the user's `vibe/...` branches on `dev` and
  gives one Pull Request link into `dev` per branch: a Pull Request is REQUIRED to run on the company server, not needed
  to run only locally. Never commit or push to `main` or `dev` directly. Someone outside the team branches from `main`.
- Prefer solutions that STORE data in the shared database (the `.env` gives every feature its own tables): imported
  rows, results, statuses, history, reusable master lists - stored lean, reused by later screens and months
  ([docs/rules/05-feature-workflow.md](docs/rules/05-feature-workflow.md) rule 3).
- ONE process: `run.ps1` (PowerShell) starts Streamlit only (no API/HTTP). Pages run business actions through
  `gateway.open(XxxController)`; each feature exposes ONE controller (top layer) from its package root.
- Work from `docs/business/<feature_key>.md`. Never invent business rules.
- Never promise a capability that [docs/capabilities.md](docs/capabilities.md) does not list (Excel/Word/PDF, stored
  data in the app database, login + permissions per feature/screen, Excel-like tables, Python calculations, fetching
  public web pages; NO e-mail, scheduled jobs, ERP/external SQL connection, Google search).
- Create features ONLY with `python scripts/new_feature.py <feature_key> --title "..." --developer <github-username>
  [--prefix <short name>]` (phase 2 only). The shared database prefixes every table of a feature with its `DEVELOPER`.
- Every app MUST be registered in `backend/app_registry.py` (one line `("<prefix>", "<key>")`, added by the scaffold):
  its URLs are `/<prefix>-<app>`; an unregistered app is hidden and its backend refuses every call.
- Stored data is never destroyed: `repository.delete()` only sets the delete flag (`is_deleted`), `restore()` undoes.
- Tables / charts / Excel only through the shared components (`data_table`, `bar_chart`/`line_chart`/`pie_chart`,
  `ExcelReader`): they cap rows and points so a million rows never freeze the app.
- Every class inherits its layer's base class from `backend.core.base`; one use case = one controller
  method = one service.
- Never `print()`: use `self.logger`; logs go to `logs/app.log` (no on-screen log panel). Mark read-only use cases
  `@cached_query` on the controller so page reruns are served from RAM.
- Finish every task with `python scripts/check.py` -> `ALL CHECKS PASSED` and `python scripts/doctor.py` ->
  `APP IS HEALTHY` (never weaken tests). A failure is YOUR job to fix: follow
  [docs/rules/10-self-repair.md](docs/rules/10-self-repair.md), never hand a broken app back to the user.
- Talk to the user in Vietnamese, simply, without jargon.

Python: `.venv/Scripts/python.exe` (Windows) / `.venv/bin/python` (macOS/Linux), created by `powershell -ExecutionPolicy Bypass -File .\run.ps1`.
