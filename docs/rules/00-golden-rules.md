# 00 - Golden Rules (non-negotiable)

Most rules are enforced automatically by `tests/architecture/` (run by `scripts/check.py`) and by the
Claude Code Stop hook (`.claude/settings.json` -> `scripts/hooks/stop_guard.sh`).

## A. Process
0. **The workflow gate** (full table in `CLAUDE.md`). This repository is LOCKED for writing by default; reading and
   analysing it is always allowed. Phase 0 (default) may write only `docs/business/_sources/*-discovery.md`; phase 1
   (the user pasted `docs/prompt/01-business-analysis.md`) may also write the business document and the analysis plan;
   phase 2 (the user pasted `docs/prompt/02-implement-feature.md` AND `Status: Ready for implementation`) may write the
   feature's own code. You MUST NOT write code, run `scripts/new_feature.py`, start the app or install packages before
   phase 2, and MUST NOT create `.gate-unlock` or change `scripts/hooks/` to get around the guard.
1. You MUST read `docs/README.md`, every file in `docs/rules/` and `docs/capabilities.md` before your first change in
   a session, and MUST NOT promise the user a capability that `docs/capabilities.md` does not list.
2. You MUST work from a business document `docs/business/<feature_key>.md`. If it is missing or incomplete,
   complete it from `_TEMPLATE.md` **with the user** before writing code.
3. You MUST NOT invent business rules. Ambiguities go to section 10 "Open questions" of the business doc,
   with the safe default you chose, and you tell the user.
4. You MUST create features ONLY with `python scripts/new_feature.py <feature_key> --title "..."`.
   Never create feature folders by hand or copy another feature folder.
5. You MUST finish every task with `python scripts/check.py` printing `ALL CHECKS PASSED` **and**
   `python scripts/doctor.py` printing `APP IS HEALTHY` (quality gate + every feature loads + the app really starts).
   Both outputs go into your report; never claim success without them.
5b. When anything fails, you MUST repair it yourself following `10-self-repair.md`: diagnose from evidence (command
   output, `logs/app.log`), fix the smallest thing in the right layer of YOUR feature, re-verify, and write the fix in
   the plan's `## Fix log`. Changing tests, hiding errors, or dropping a requirement to get a green output is
   forbidden.
6. You MUST NOT edit, skip, weaken or delete tests in `tests/architecture/` or `tests/core/`, and MUST NOT add
   `# noqa`, `pytest.skip`, `xfail` or config ignores to pass a check. Fix the code.

## B. Architecture
7. ONE process: `run.ps1` starts Streamlit only. You MUST NOT add an API server, HTTP calls, REST clients,
   FastAPI/Flask, or a second process. Pages run business actions in-process through the gateway:
   `gateway.open(XxxController).use_case(request)`. Never write `XxxController()` in a page.
8. One feature = one key = `backend/features/<key>/` + `frontend/features/<key>/` + `docs/business/<key>.md`.
9. Features are independent: a feature MUST NOT import another feature (backend or frontend).
   Generic reusable code goes to `backend/shared/` or `frontend/core/components/`.
10. You MUST NOT modify framework code (`backend/core/`, `backend/shared/`, `frontend/core/`, `frontend/app.py`,
    `frontend/home/`, `scripts/`, `tests/architecture/`, `tests/core/`, `run.ps1`) to implement a feature.
    Exception: adding a generic helper/component, only if the user agrees.
11. Every class MUST inherit the base class of its layer (see 03).
12. Each feature has exactly ONE controller (its top layer), exported by `backend/features/<key>/__init__.py`.
    One use case (UC-xx) = one controller method = one service class (one file).
13. Controller methods contain ONE line: `return XxxService().handle(request)`.
14. Business rules and decisions live ONLY in `business/`. Pages, controllers, builders make no business decisions.
15. A page imports from the backend ONLY: `backend.core.*`, its feature root `backend.features.<key>`
    (the controller) and `backend.features.<key>.dto.*`.
16. The backend MUST NOT import `streamlit` or anything from `frontend`.
17. Pages MUST NOT read/write files or use openpyxl/python-docx/pypdf: the backend does file work.

## C. Logging (see 09)
18. Never `print()`. Use `self.logger` (services, controllers, pages) or `get_logger(__name__)`.
19. Every feature page MUST keep the log panel (`show_log_panel = True`, the default). Home has no log panel.
20. Every service MUST log its important steps (what was received, counts, decisions) with `self.logger.info`.

## D. Code
21. Python 3.11, full type hints, English identifiers/comments/docstrings/log messages.
22. Language of texts: **framework code** (`backend/core`, `backend/shared`) raises English messages; the texts of a
    **feature** that the user reads (page labels, button labels, BR-xx messages, feature errors) follow the business
    document (Vietnamese). The shared UI chrome in `frontend/core` and Home stays Vietnamese (the end users are
    Vietnamese): do not translate it.
23. Expected failures raise an `AppError` subclass with a clear, actionable message.
24. Dependencies only in `requirements.txt`, exact pins (`==`). `run.ps1` is the only launcher.
25. Never hard-code absolute paths or secrets. Use `get_settings()` and `.env`.

## Definition of Done (all MUST be true)
- [ ] `python scripts/doctor.py` prints `APP IS HEALTHY` (the app starts and every feature loads).
- [ ] `docs/business/<key>.md` is complete and section 11 "Implementation map" is filled.
- [ ] Every BR-xx is implemented in `business/` and has at least one unit test.
- [ ] Every UC-xx is one method of the feature's controller + one service; pages call it via `gateway.open`.
- [ ] Services log their main steps; the page shows the log panel.
- [ ] `python scripts/check.py` prints `ALL CHECKS PASSED`.
- [ ] `run.ps1` starts the app; the feature card is on `/home` and its pages open without errors.
- [ ] You told the user, in Vietnamese and without jargon, what was built, how to use it, and open questions.
