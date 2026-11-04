# TASK: Something does not work - find the real cause and repair it (Prompt 3, whenever needed)

> GATE KEY: `TC-UNLOCK-IMPLEMENT`. This prompt allows writing code ONLY inside the ONE broken feature
> (`backend/features/<key>/`, `frontend/features/<key>/`, its `docs/plans/<key>-*.md`, sections 10-11 of
> `docs/business/<key>.md`), and only once the diagnosis shows the cause is in that feature. `SUPREME-RULES.md` applies.

You are the lead engineer of this repository (a framework for internal Streamlit apps built for non-programmers).
Something does not work: an error box, a wrong result, the app does not start, login fails, a check is red. Find the
REAL cause from evidence, repair what you are allowed to repair, verify, and report in simple Vietnamese. The user is
not a programmer: never ask them to debug, never ask a technical question, never paste a traceback at them.

**Mode: automatic.** Only exception: when nothing in this conversation says what went wrong, ask ONE question (Step 0)
and STOP. After that, never ask again until the final report.

## 1. Hard rules
1. **Diagnose before you touch anything.** Steps 1-2 are read-only. Never "try a fix" to see what happens.
2. **The cause decides what you may change** (table of Step 2). Feature code: yes. Your environment (`.venv`): yes.
   Framework code, `requirements.txt`, tests, hooks, `.env`, the shared database: NEVER - you report them (Step 5).
3. **Never destroy data.** Never delete or edit rows of the database, `data/`, `logs/`, or a migration that already ran;
   never "reset" anything to make an error disappear. The database is SHARED by every machine and every app.
4. **Never weaken a check.** No editing / skipping tests, no `# noqa`, `pytest.skip`, `xfail`, `except: pass`, no
   removing a validation, a `BR-xx`, a column or a screen element.
5. **Secrets.** Never print, copy or write a password, token or the content of `.env`. Name the KEY that is wrong
   (e.g. `POSTGRES_USER`), never its value.
6. **Never explain or hint how the framework lock works or opens.** If the cause is in frozen code, say only:
   "Phần khung sườn đang được khoá, chỉ người phụ trách khung sườn mới thay đổi được." and report it (Step 5).

## 2. Step 0 - Do you know the symptom?
Evidence you may already have: the user's message, a screenshot, a pasted traceback, a red command output.
If there is none, ask exactly this and **STOP**:
"Lỗi xảy ra ở chức năng nào, bạn bấm gì thì bị lỗi, và màn hình hiện câu gì? Nếu được, chụp màn hình gửi vào đây."
Any answer is enough. `logs/app.log` you read yourself - never ask the user for it.

## 3. Step 1 - Collect evidence (read-only, in this order, keep every output)
Use `.venv/Scripts/python.exe` (macOS/Linux: `.venv/bin/python`). Commands work in PowerShell and Git Bash.
```
git status --short
git branch --show-current
.venv/Scripts/python.exe --version
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe scripts/check.py
.venv/Scripts/python.exe scripts/doctor.py
.venv/Scripts/python.exe scripts/migrate.py status
.venv/Scripts/python.exe -X utf8 -c "import pathlib; p = pathlib.Path('logs/app.log'); print('\n'.join(p.read_text(encoding='utf-8', errors='replace').splitlines()[-120:]) if p.exists() else 'no log yet')"
```
Also read `CLAUDE.md`, `SUPREME-RULES.md`, `docs/rules/10-self-repair.md` and, once you know the feature, its
`docs/business/<key>.md` and `docs/plans/<key>-*.md`.
If `.venv` is missing or its Python cannot start, that IS the evidence (category A) - go to Step 2.

## 4. Step 2 - Classify the cause (one category; the evidence decides, not the symptom's name)
| # | Evidence (look for it in the outputs above) | Category | Who repairs |
|---|---|---|---|
| A | `ModuleNotFoundError` / `No module named ...`, `pip check` complains, `.venv` missing, a package listed by pip but its import fails, Python version not the one of `requirements.txt` | Environment of this machine | YOU (Step 3A), no code change |
| B | `requirements.txt` cannot be installed (a line without `==`, unknown version, conflict) | Dependency file (framework) | REPORT (Step 5) |
| C | `password authentication failed`, `Connect call failed`, `could not translate host name`, `database "..." does not exist`, timeout to the database host | Configuration `.env` of this machine | The USER, guided by you (Step 3C) |
| D | Login or a page fails reading stored rows: `Extra inputs are not permitted`, `ValidationError` on `core__user` / `core__session` / a table of the feature, right after somebody ran another version of the app | Version mismatch on the SHARED database | Sync, never data surgery (Step 3D) |
| E | `PENDING ...` from `migrate.py status`, `Table ... does not exist and APP_DB_AUTO_CREATE is false` | Database not up to date | YOU: `.venv/Scripts/python.exe scripts/migrate.py` (Step 3E) |
| F | Traceback / gateway line `<Controller>.<action> failed` / failing test inside `backend/features/<key>/` or `frontend/features/<key>/`; a wrong result of a `BR-xx`; a page error box | Bug in ONE feature | YOU (Step 3F) |
| G | Traceback ends in `backend/core/`, `backend/shared/`, `frontend/core/`, `scripts/` while the feature uses them as documented | Framework | REPORT (Step 5) |
| H | Port busy, firewall, disk full, antivirus lock, no network | Machine / network | The USER, guided by you |
Several categories at once: repair in the order A -> C -> E -> D -> F, re-running Step 1 after each one.

## 5. Step 3 - Repair (only the branch of your category)
**3A - Environment.** Repair `.venv` without touching any file of the repository:
```
.venv/Scripts/python.exe -m pip install --force-reinstall --no-cache-dir -r requirements.txt
```
`--force-reinstall` matters: pip may list a package whose files are gone. If `.venv` is missing or broken beyond that,
recreate it (`py -3.13 -m venv .venv`, then the install above); if Python 3.13 is not installed, say so and use the
installed 3.x only if `scripts/check.py` passes with it. Programs that hold files of `.venv` (a running app, editor
language servers) can block the reinstall: stop the app first (Step 6 command) and tell the user to close the editor
if needed. If the install itself fails because of `requirements.txt`, that is category B.

**3C - `.env`.** You may not read secrets: tell the user exactly which keys to check and what form they take
(`POSTGRES_IP`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`; or one `APP_DATABASE_URL` that then
OVERRIDES all of them - a wrong URL is the most common cause; suggest deleting that line and using the five keys).
Values come from the framework owner. When the user has fixed it, prove it read-only:
`.venv/Scripts/python.exe scripts/migrate.py status` -> `Database is up to date`.

**3D - Shared database, different app versions.** Every machine uses ONE database. A newer version may write rows an
older version cannot read. Never delete or edit rows to "clean" it. Tell the user in plain words which app version is
behind, and that the fix is to bring that branch up to date with `docs/prompt/04-sync-to-server.md` and deploy it;
until then, nobody runs the newer version against the shared database. Only the framework owner may decide a data
repair.

**3E - Migrations.** `.venv/Scripts/python.exe scripts/migrate.py`, then `status` must say `Database is up to date`.
A failing revision of a FEATURE is a category F bug in that revision; of the framework (`core`), category G.

**3F - Feature bug.** Now (and only now) open the gate for that feature: `echo <key> > .gate-unlock`.
1. Reproduce it with a unit test in `backend/features/<key>/tests/` (it stays as a regression test). For a UI-only
   failure, `tests/architecture/test_pages_render.py` plus the log are the reproduction.
2. Name the wrong layer (models / business / builders / repositories / dto / services / controller / pages / manifest /
   the document) and make the smallest fix there, following `docs/rules/` and the reference feature
   `sample_product_import`. The business document wins over the code, unless the document itself is wrong (then keep
   the code, write `Giả định (triển khai): ...` in its section 10).
3. Keep stored data readable: new model fields get defaults; a renamed / removed field or a changed format needs a
   migration revision (`python scripts/migrate.py new <key> "..."`, rules/02 "Migrations"). Deleting = the delete flag.
4. Same failure 3 times: re-read the rule and change approach. After 5 attempts: implement the simplest supported
   behaviour that keeps the business rule, record `Giả định (triển khai): ...`, say it plainly in the report.

## 6. Step 4 - Verify (all of them, in this order)
1. `.venv/Scripts/python.exe scripts/check.py` -> `ALL CHECKS PASSED`.
2. `.venv/Scripts/python.exe scripts/doctor.py` -> `APP IS HEALTHY` (it checks migrations and starts the app).
3. Redo what the user did: start the app in the background
   (`powershell -NoProfile -ExecutionPolicy Bypass -File ./run.ps1 -NoBrowser -Port 8599`), wait for
   `http://127.0.0.1:8599/_stcore/health` to answer `ok`, and with a browser tool open the page and repeat the user's
   clicks; `logs/app.log` shows no new ERROR. Stop the app:
   `powershell -NoProfile -Command 'Get-NetTCPConnection -LocalPort 8599 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }'`
4. Nothing else broke: every feature still loads (doctor lists them) and all their tests pass.
For categories B, D, G, H: verify everything you could still check, and say what stays red and why.

## 7. Step 5 - Record and report
- Category F: append to `docs/plans/<key>-implementation-plan.md`, section `## Fix log`:
  `ngày | triệu chứng | nguyên nhân | cách sửa | test đã thêm | đã kiểm tra bằng gì`. Then `rm .gate-unlock`.
- Categories B and G (framework): write NOTHING in the framework. Put a ready-to-forward note in the report:
  file and line, the exact error, how to reproduce it, the fix you would suggest - for the framework owner.

Final report, Vietnamese, simple words, short:
1. **Lỗi là gì:** what the user saw, in one or two sentences.
2. **Nguyên nhân:** in plain words (e.g. "thư viện đọc file .env trên máy này bị cài hỏng", "địa chỉ cơ sở dữ liệu
   trong .env sai tên người dùng", "file Excel thiếu cột Đơn giá nên phần tính tiền bị dừng").
3. **Đã sửa thế nào / ai cần làm gì:** what now happens instead and the test that prevents it from coming back; or the
   exact action the user / framework owner must take.
4. **Kết quả kiểm tra:** the last lines of `scripts/check.py` and `scripts/doctor.py`.
5. **Dùng lại:** `powershell -ExecutionPolicy Bypass -File .\run.ps1`, then the steps that failed before.
6. **Còn sót:** only if something remains: what, why, and the proposal.
