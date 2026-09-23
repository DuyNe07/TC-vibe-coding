# 05 - Feature Workflow (the only allowed path)

The repository is locked for writing until the implementation prompt is used: see the workflow gate in `CLAUDE.md`
and rule A.0 of `00-golden-rules.md`.

## New feature
1. **Read** `docs/README.md`, all `docs/rules/` and `docs/capabilities.md` (never promise more than it lists).
   If the user has not explained the business yet, start with `docs/prompt/00-discovery.md`: talk with them, check
   feasibility against `docs/capabilities.md`, and write the discovery note in `docs/business/_sources/`.
2. **Business doc**: open `docs/business/<key>.md`. If missing or incomplete, write it first with the user
   (procedure: `docs/prompt/01-business-analysis.md`). All business questions happen at THIS stage, only about the
   application (data, rules, use cases, files, what each screen shows and allows) - never about code. The document
   ends with `Status: Ready for implementation`.
3. **UI concept, then plan (no more waiting)** (full procedure: `docs/prompt/02-implement-feature.md`):
   - Ask the user ONE round of questions about how they want to use the screens (menu or tabs, Excel-like table:
     read-only / edit in cells / pick a row, input by form / grid / Excel upload, filters, totals, charts,
     confirmations), with a proposal they can accept with "ok". Record the answer in section 8 as
     `### Giao diện đã chốt (UI concept)`. This is the ONLY question during implementation.
   - Write `docs/plans/<key>-implementation-plan.md` (summary, requirement traceability matrix with every field/file
     column/UC/BR/screen element/AC -> code element -> test, controller contract, ordered steps with checkboxes,
     implementation assumptions), then execute it immediately without asking anything: technical choices are yours;
     business gaps get the safest behaviour consistent with the document, recorded in section 10 as
     `Giả định (triển khai): ...` and reported at the end.
   - Build with sub-agents when the tool has them: backend sub-agent (`backend/features/<key>/`) and UI-design
     sub-agent (studies https://docs.streamlit.io/develop/api-reference, writes `docs/plans/<key>-ui-design.md`) in
     parallel, then UI-build sub-agent (`frontend/features/<key>/`). Without sub-agents, do the same roles in sequence.
   - Only touch the feature's own folders, its document and its plans; never break other features.
4. **Scaffold**: `python scripts/new_feature.py <key> --title "..." --description "..." --icon "..." --owner "..."`.
   It creates backend + frontend + doc stub with a working `ping` use case. Run `run.ps1` to see the card.
5. **Map the doc to code** (write this mapping in section 11 of the doc as you go):

   | Business doc | Code |
   |---|---|
   | 4. Data objects | `models/` (entities, enums) |
   | 5. Input/output files | `constants.py` (columns) + `builders/` |
   | 6. UC-xx | one `services/xxx_service.py` + one controller method + DTOs in `dto/` |
   | 7. BR-xx | one `BaseBusinessRule` class (`code="BR-xx"`) or a method of a `BaseBusiness` class |
   | 8. Screens | one page in `frontend/features/<key>/pages/` |

6. **Implement bottom-up**: models -> business (+ tests) -> repositories -> builders -> dto -> services
   (log main steps) -> controller methods -> pages -> manifest (`pages=(...)`).
   - Registering with the gateway = exporting the ONE controller from `backend/features/<key>/__init__.py`
     (done by the scaffold; no central list to edit, so features never conflict).
   - The feature's navigation = `manifest.py`: its pages appear in the sidebar menu and its card on Home.
7. **Remove the scaffold** `ping` (dto, service, controller method, test, page call) once real use cases exist.
8. **Test**: unit tests for every BR-xx and every service in `backend/features/<key>/tests/`.
9. **Verify**: `python scripts/check.py` -> `ALL CHECKS PASSED`. Fix the code, never the tests.
10. **Run**: `run.ps1`, open the feature from `/home`, try each screen, check the log panel shows the steps.
11. **Gap check**: re-read the business doc line by line; every traceability row must be done and tested.
12. **Report** to the user in Vietnamese: what was built, how to use it, open questions; ask them to test.

## Changing a feature
1. Update the business doc first (rules, use cases, screens), then the code, then the tests.
2. Keep the implementation map (section 11) up to date.
3. `python scripts/check.py`, then `run.ps1`.

## Removing a feature
Delete `backend/features/<key>/`, `frontend/features/<key>/`, `docs/business/<key>.md` (and `data/<key>/` if
the user agrees). Nothing else references it.

## When something does not work
1. Open the page's "📜 Nhật ký chạy (log)" panel (or `logs/app.log`) and read the last ERROR/WARNING.
2. Reproduce with a unit test, fix, `python scripts/check.py`.
3. If the page shows old behaviour after edits, stop the app (Ctrl+C) and run `run.ps1` again.
