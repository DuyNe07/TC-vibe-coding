# TASK: Extend a finished feature - read what exists, ask what to add, then build it in place (Prompt 5)

> GATE KEY: `TC-UNLOCK-IMPLEMENT`, but code stays locked until Step 4 is confirmed. Until then you may write ONLY
> `docs/business/<key>.md` and `docs/plans/<key>-extension-<yyyymmdd>.md`. From Step 5 on: the feature's own folders,
> its line in `backend/app_registry.py`, its plans and its document. `SUPREME-RULES.md` applies.

You are analyst and lead engineer at once. A feature is already built and in use ("tính năng A đã xong"); the user
wants MORE from it. You read everything that exists first, tell the user what the feature does today, ask what they want
to add, settle it with them like Prompt 1 does, then build it like Prompt 2 does - without breaking what works and
without losing a single stored row. The user is NOT a programmer: simple Vietnamese, never technical questions.

## 1. Hard rules
1. **Existing behaviour is a contract.** Every existing `UC-xx`, `BR-xx`, screen, file column and `AC-xx` keeps working
   unless the user explicitly asks to change it (then the document says what changed). Existing tests keep passing;
   never edit a test to accommodate the extension - add new ones.
2. **IDs only grow.** New use cases / rules / criteria take the next free number (`UC-07`, `BR-15`, `AC-21`...). Never
   renumber or reuse an ID; a removed item is marked `(bỏ từ <yyyy-mm-dd>)`, not deleted.
3. **Stored data stays.** The database is shared by every machine and app version: new fields get defaults, a renamed /
   removed field or a changed format needs a migration revision, deleting = the delete flag. Never delete rows, tables,
   `data/<key>/`.
4. **Stay inside the feature and inside `docs/capabilities.md`.** Never edit the framework, another feature or the
   sample. A wish the app cannot do: say so and offer the closest supported way.
5. **Stop points.** At every `STOP` end your message and wait. Questions are about the application only (what users
   do, data, rules, calculations, files, screens), never about code.

## 2. Step 1 - Which feature? (-> STOP only if unclear)
List the features: every `docs/business/*.md` (except `_TEMPLATE.md`, `README.md`, `sample_product_import.md`) with its
`Status`, and the folders of `backend/features/`. If the user already named the feature (name, key or screen), take it.
Otherwise show the `Implemented` ones as a numbered list (Vietnamese name + one line of what it does) and ask
"Bạn muốn phát triển thêm chức năng nào?" -> **STOP**.
If the feature is not `Implemented` yet: say which prompt finishes it first (Prompt 1 or 2) and stop.

## 3. Step 2 - Read EVERYTHING that exists, then tell the user what the feature does today -> STOP
Read completely: `CLAUDE.md`, `SUPREME-RULES.md`, `docs/README.md`, every file of `docs/rules/`, `docs/capabilities.md`,
the feature's `docs/business/<key>.md` (all sections, including `Giao diện đã chốt` and section 10), every
`docs/plans/<key>-*.md` (fix logs too), `docs/business/_sources/` files about it, and the code:
`backend/features/<key>/` (models, rules, services, controller) and `frontend/features/<key>/` (manifest, pages).
Note where the code and the document disagree: the document wins; mention real gaps in the summary.
Then send ONE message in simple Vietnamese:
- **Hiện tại chức năng làm được:** the screens in menu order, and on each: what it shows, the buttons and what they do;
  the files imported / exported; the main rules and calculations; who uses which screen (roles, if any).
- **Bạn muốn phát triển thêm gì?** with 3-5 concrete example directions taken from THIS feature (e.g. "thêm cột ... vào
  bảng ...", "xuất thêm báo cáo ...", "thêm bước duyệt ...", "thêm biểu đồ ...", "nhập thêm từ file ..."), and: "Kể tự
  nhiên, đính kèm file mẫu nếu có."
**STOP**.

## 4. Step 3 - Clarify until nothing important is open (-> STOP, repeat)
Like `docs/prompt/01-business-analysis.md` Steps 4-5, but only for the change: at most 5-7 numbered questions per round,
each with options; after each answer repeat back "Tôi hiểu là..." before the next round. Cover: what the user does and
sees, new / changed data fields (meaning, type, required, validation), rules and formulas (units, rounding), statuses and
transitions, files (exact columns), which screen it lives on, who may use it, AND the impact on what exists: does any
current rule, column, file or screen change? What happens to rows already stored (default value, conversion)?
Check every wish against `docs/capabilities.md` (Làm được / Làm được theo cách khác / Không làm được + thay thế).
**STOP** after each round until everything that affects screens, data, rules, files or existing rows is answered.

## 5. Step 4 - Update the document, confirm ("chốt") -> STOP
1. Write `docs/plans/<key>-extension-<yyyymmdd>.md`: what is added / changed, the impact on existing UC/BR/AC/data,
   the data plan for stored rows (defaults, migration), and the questions answered.
2. Update `docs/business/<key>.md` in place, keeping its format: new fields in section 4 (with the default for existing
   rows), new files / columns in 5, new `UC-xx` in 6, new `BR-xx` in 7 (exact Vietnamese messages), new or changed
   screens in 8, new `AC-xx` in 9 - including at least one AC proving the old behaviour still works where the change
   touches it - and in section 10 a line `Mở rộng <yyyy-mm-dd>: <tóm tắt>` plus the confirmed `Giả định: ...`.
   Changed items say so: `(sửa <yyyy-mm-dd>: trước đây ...)`.
3. Self-review like Prompt 1 Step 6 (every new BR used by a UC, every UC on a screen, every UC has an AC, no vague words).
4. Show the user a readable summary: what is new, what changes in what they use today, what happens to existing data.
   Ask: "Đúng chưa? Trả lời "đồng ý" để tôi bắt đầu làm." -> **STOP**.
   Corrections: update, show again, **STOP**. On "đồng ý": set `Status` = `Ready for implementation`.

## 6. Step 5 - UI of the new / changed screens: ONE round -> STOP
Only when the change adds or changes screen elements: send the questions of `docs/prompt/02-implement-feature.md`
Step 0, for the NEW or CHANGED parts only, with the current UI (`Giao diện đã chốt`) as the proposal, ending with:
"Trả lời theo số, hoặc gõ "ok" để dùng toàn bộ đề xuất. Sau câu trả lời này AI sẽ tự làm đến khi xong, không hỏi thêm."
-> **STOP**. Then update `### Giao diện đã chốt (UI concept)` (keep the existing decisions, add / change only the
touched screens). No screen change: skip this step. From here on never ask anything again.

## 7. Step 6 - Build in place
Open the gate: `echo <key> > .gate-unlock`. Then follow `docs/prompt/02-implement-feature.md` sections 3 (commands),
4 (rules), 7-13 (build, roles, pitfalls, verify) in **existing-feature mode**: never scaffold, never delete folders,
update in place. In the plan of Step 4 add the traceability rows of the NEW / CHANGED items only, plus one row
"regression: existing tests" that must stay green. Order: models (defaults) -> migration revision if stored data
changes -> business (+ tests) -> repositories -> builders -> dto -> services (+ tests) -> controller (`@cached_query` on
read-only) -> pages / manifest. Run the full quality gate early (baseline) and after each layer.
Done = `scripts/check.py` -> `ALL CHECKS PASSED` (old AND new tests), `scripts/migrate.py status` -> up to date,
`scripts/doctor.py` -> `APP IS HEALTHY`, and with a browser tool: the old main scenario still works and every new AC
passes. Then fill section 11, set `Status` = `Implemented`, `rm .gate-unlock`.

## 8. Step 7 - Final report (Vietnamese, simple words, no questions)
1. Đã thêm / thay đổi gì: per screen, where it is and what the new buttons / columns / files do.
2. Những gì giữ nguyên và đã kiểm tra lại (các chức năng cũ vẫn chạy); dữ liệu cũ được xử lý thế nào.
3. Cách dùng phần mới: `powershell -ExecutionPolicy Bypass -File .\run.ps1`, then click-by-click.
4. Kết quả kiểm tra: last lines of `scripts/check.py` and `scripts/doctor.py`; numbers of new UC / BR / AC tested.
5. Giả định khi triển khai, if any. Gửi lên server: `docs/prompt/04-sync-to-server.md`.
