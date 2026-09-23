# TASK: The app shows an error - find the cause and repair it (Prompt 3, only when needed)

> GATE KEY: `TC-UNLOCK-IMPLEMENT`. Pasting this prompt allows you to write code, but ONLY inside the feature that is
> broken. Step 1 creates the file `.gate-unlock` and Step 6 deletes it. See the workflow gate in `CLAUDE.md`.

You are the lead engineer of this repository (a framework for internal Streamlit apps built for non-programmers).
Something does not work: a page shows an error, a result is wrong, the app does not start, or a check fails. Repair it
yourself, following `docs/rules/10-self-repair.md`, until both `scripts/check.py` and `scripts/doctor.py` are green.
The user is not a programmer: do not ask them to debug and do not ask technical questions.

**Automatic mode.** One single exception: if nothing in this conversation says what went wrong, ask exactly one short
Vietnamese question (Step 0) and STOP. After that, work until it is fixed and send ONE final report in Vietnamese.

## 1. Step 0 - Do you know the symptom?
Evidence you may already have: the user's message, the text they copied from the page's log panel, a screenshot, a
failing command output. If you have none, ask ONE question and **STOP**:
"Lỗi xảy ra ở chức năng nào, bạn bấm gì thì bị lỗi, và màn hình hiện câu gì? Nếu được, mở khung "📜 Nhật ký chạy (log)"
ở cuối trang, bấm biểu tượng copy rồi dán vào đây."
Anything the user answers is enough: never ask a second time.

## 2. Step 1 - Preflight (in this order)
1. Create `.gate-unlock` with the feature key you are about to repair (or `unknown` until you know it):
   `echo <key> > .gate-unlock`. Without it, every write to code is refused by `scripts/hooks/gate_guard.sh`.
2. Read `CLAUDE.md`, `docs/README.md`, `docs/rules/10-self-repair.md`, `docs/rules/00-golden-rules.md` and, once you
   know which feature is broken, its business document `docs/business/<key>.md` and plan `docs/plans/<key>-*.md`.
3. Run the full diagnosis and keep the output:
   ```
   .venv/Scripts/python.exe scripts/check.py
   .venv/Scripts/python.exe scripts/doctor.py
   ```
   (On macOS/Linux use `.venv/bin/python`. If `.venv` is missing: `py -3.13 -m venv .venv` then
   `.venv/Scripts/python.exe -m pip install -r requirements.txt`.)
4. Read the end of `logs/app.log` (or ask nothing and read the text the user pasted):
   ```
   .venv/Scripts/python.exe -X utf8 -c "import pathlib; print('\n'.join(pathlib.Path('logs/app.log').read_text(encoding='utf-8', errors='replace').splitlines()[-80:]))"
   ```

## 3. Step 2 - Locate the cause
1. Decide which feature and which layer is wrong (models / business / builders / repositories / dto / services /
   controllers / pages / manifest / document). The traceback's file and the gateway log line
   (`<Controller>.<action> failed`) point straight at it.
2. Write a unit test in `backend/features/<key>/tests/` that reproduces the failure (it stays as a regression test).
   For a UI-only failure, rely on `tests/architecture/test_pages_render.py` plus the log.
3. If the business document and the code disagree, the document wins - unless the document itself is the problem
   (then keep the code, write `Giả định (triển khai): ...` in section 10 and say it in the report).

## 4. Step 3 - Repair (the loop of `docs/rules/10-self-repair.md`)
Smallest fix, right layer, only inside `backend/features/<key>/` and `frontend/features/<key>/`. Forbidden: changing
tests, `# noqa` / `pytest.skip`, `except: pass`, dropping a validation or a `BR-xx`, deleting `data/<key>/`, touching
`backend/core`, `backend/shared`, `frontend/core`, `scripts/`, `requirements.txt` or another feature. Keep stored data
readable (new model fields get defaults; renamed/removed fields get a conversion in the repository).
Same failure 3 times: change approach. After 5 attempts: implement the simplest supported behaviour that keeps the
business rule, record the assumption, and report it honestly.
If the cause really is in the framework, stop and ask the user in ONE Vietnamese sentence for permission to fix the
framework; only with their "yes" change it and add a test in `tests/core/`.

## 5. Step 4 - Verify
1. `scripts/check.py` -> `ALL CHECKS PASSED` (never weaken a test to get there).
2. `scripts/doctor.py` -> `APP IS HEALTHY`.
3. With a browser tool: open the feature, redo exactly what the user did, confirm the error is gone and the log panel
   shows the normal steps.
4. Check you broke nothing else: the other features still load (`doctor.py` lists them) and their tests pass.

## 6. Step 5 - Record it
Append to `docs/plans/<key>-implementation-plan.md`, section `## Fix log`:
`ngày | triệu chứng | nguyên nhân | cách sửa | test đã thêm | đã kiểm tra bằng gì`.
If the business document needed a clarification, add it to section 10 as `Giả định (triển khai): ...`.

## 7. Step 6 - Final report (Vietnamese, simple words)
0. Delete `.gate-unlock` (`rm .gate-unlock`) so the repository is locked again.
1. **Lỗi là gì:** what the user saw, in one or two sentences.
2. **Nguyên nhân:** in plain words, no jargon (e.g. "file Excel thiếu cột Đơn giá nên phần tính tiền bị dừng").
3. **Đã sửa thế nào:** what now happens instead, and the test that prevents it from coming back.
4. **Kết quả kiểm tra:** the two outputs (`ALL CHECKS PASSED`, `APP IS HEALTHY`).
5. **Cách dùng lại:** `powershell -ExecutionPolicy Bypass -File .\run.ps1`, then the steps to redo what failed.
6. **Nếu còn sót:** exactly what is not fixed, why, and what you propose (only if something remains).
