# 05 - Feature Workflow (the only allowed path)

The repository is locked for writing until the implementation prompt is used: see the workflow gate in `CLAUDE.md`
and rule A.0 of `00-golden-rules.md`.

## Three rules for every prompt (00-05)
1. **Questions = business + what the user sees.** The user is NOT a programmer. Every question is phrased as the work
   they do, or as what appears on the screen / comes out of the app (bảng hiện cột gì, nút nào, số nào, file Excel
   nào, thông báo gì). Never ask how something is processed, stored or computed inside (backend, database, table,
   service, API, cache, field type...): decide that yourself and describe only its visible result.
   - Sai: "Backend xử lý dữ liệu trùng thế nào?", "Lưu vào bảng riêng hay chung?", "Dùng cache không?"
   - Đúng: "Khi file có 2 dòng trùng mã, màn hình nên (a) báo lỗi dòng đó (b) lấy dòng sau cùng?",
     "Lần sau mở lại, bạn có muốn thấy kết quả lần trước trong bảng không?"
2. **One feature = one own branch from the newest `dev`, in THIS repository.** Never suggest forking the repository on
   GitHub, cloning it again or copying the folder. A new feature: `git fetch origin` then
   `git checkout -b vibe/<prefix>-<key>-<ddmm> origin/dev`. Someone building 10 apps has 10 `vibe/...` branches, each
   started from `dev`; extending an app continues on that app's branch. Prompt 4 brings ALL of them up to date with
   the newest `dev` (rebase) and gives one Pull Request link per branch.
3. **Store data by default (the shared database).** With the `.env` from the framework owner, every feature may create
   its own tables in the company PostgreSQL database (`SqlRepository`, tables prefixed by its `DEVELOPER`). Data kept
   there survives restarts, machines and versions - this is what makes an app worth opening every day. So when you
   design a feature, prefer solutions that save: imported Excel rows, calculation results, statuses, history (ai, lúc
   nào), master lists (danh mục) that later screens and later months reuse instead of uploading the same file again.
   Keep it lean: store the business rows once (not every intermediate step), compute summaries from stored rows,
   archive old periods with a status/period field rather than copying tables, stay under ~200 thousand rows per table
   (see `docs/capabilities.md`). Only a pure one-shot conversion (file in -> file out, nothing to look back at) skips
   storage, and only when the user confirms nobody needs to see it again. Ask about it in business words
   ("có cần xem lại / so sánh với lần trước không?"), never "có lưu vào database không?".

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
4. **Scaffold**: `python scripts/new_feature.py <key> --title "..." --developer <github-username> --description "..." --icon "..." --owner "..."`.
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
     AND the app's line in `backend/app_registry.py` (both done by the scaffold: `--prefix <your short name>`;
     one line per app, so features never conflict). Without the line the app is hidden and its backend refuses calls.
   - The feature's navigation = `manifest.py`: its card appears on Home and its pages in the app's sidebar menu.
7. **Remove the scaffold** `ping` (dto, service, controller method, test, page call) once real use cases exist.
8. **Test**: unit tests for every BR-xx and every service in `backend/features/<key>/tests/`.
9. **Verify**: `python scripts/check.py` -> `ALL CHECKS PASSED`, then `python scripts/doctor.py` ->
   `APP IS HEALTHY`. Fix the code, never the tests. Any failure: the self-repair loop of `10-self-repair.md`.
10. **Run**: `run.ps1`, open the feature from `/home`, try each screen, check `logs/app.log` has no ERROR.
11. **Gap check**: re-read the business doc line by line; every traceability row must be done and tested.
12. **Report** to the user in Vietnamese: what was built, how to use it, open questions; ask them to test.

## Changing a feature
0. Work on the feature's own `vibe/...` branch (rule 2 above); none on this machine: a new one from `origin/dev`.
1. Update the business doc first (rules, use cases, screens), then the code, then the tests.
2. Keep the implementation map (section 11) up to date.
3. `python scripts/check.py`, then `run.ps1`.

## Removing a feature
Delete `backend/features/<key>/`, `frontend/features/<key>/`, `docs/business/<key>.md` (and `data/<key>/` if
the user agrees). Nothing else references it.

## When something does not work
Full procedure: `10-self-repair.md` (for an error reported by a user: `docs/prompt/03-fix-error.md`).
1. Read the last ERROR/WARNING in `logs/app.log`.
2. Reproduce with a unit test, fix, `python scripts/check.py`, then `python scripts/doctor.py`.
3. If the page shows old behaviour after edits, stop the app (Ctrl+C) and run `run.ps1` again.
