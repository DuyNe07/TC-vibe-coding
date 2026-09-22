# 05 - Feature Workflow (the only allowed path)

## New feature
1. **Read** `docs/README.md` and all `docs/rules/`.
2. **Business doc**: open `docs/business/<key>.md`. If missing or incomplete, write it first with the user
   (procedure: `docs/prompt/01-business-analysis.md`).
   All questions to the user happen at THIS stage, and only about the application (screens, data, rules,
   messages, files) - never about code. The document ends with `Status: Ready for implementation`.
3. **Plan (no waiting)**: write `docs/plans/<key>-implementation-plan.md` (summary, requirement traceability
   matrix with every field/file column/UC/BR/screen element/AC -> code element -> test, file list, ordered steps
   with checkboxes, implementation assumptions), then execute it immediately. During implementation do NOT ask
   the user anything: technical choices are yours; business gaps get the safest behaviour consistent with the
   document, recorded in section 10 as `Giả định (triển khai): ...` and reported at the end.
   Only touch the feature's own folders, its document and its plan; never break other features.
   (Full procedure: `docs/prompt/02-implement-feature.md`.)
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
