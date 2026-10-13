# TASK: Bring a feature branch up to date with `main` and the current framework (Prompt 6 - pull + rebase + adapt)

> GATE KEY: `TC-UNLOCK-IMPLEMENT`. Pasting this prompt allows writing code, ONLY inside the folders of the features that
> exist on the branch and not on `main` (plus their `docs/business/<key>.md` sections 10-11 and `docs/plans/<key>-*.md`).
> Step 3 creates `.gate-unlock`; the last step deletes it. Framework code (`backend/core`, `backend/shared`,
> `frontend/core`, `frontend/home`, `frontend/app.py`, `scripts/`, `tests/`, `conftest.py`, `requirements.txt`) always
> comes from `main` unchanged.

You are the lead engineer of this repository. A person built one or more features on their own branch (often from an
older version of the framework). Your job: fetch the latest code, rebase the branch onto `main`, adapt the features to
the framework of `main`, prove the app works, and push the branch back - automatically after ONE round of questions.

## 1. Read first (no questions yet)
1. `CLAUDE.md`, `docs/README.md`, every file of `docs/rules/`, `docs/capabilities.md`.
2. `git fetch origin --prune`, then `git status --short`, `git branch --show-current`, `git branch -r`,
   `git log --oneline -15 origin/main`. If the working tree has uncommitted changes, stop and ask the user (one line)
   whether to commit them first.
3. Find the branch to sync: the current branch, or the remote branches `origin/vibe/*` not merged into `origin/main`
   (`git branch -r --no-merged origin/main`).
4. For that branch: `git log --oneline origin/main..<branch>` (its own commits) and
   `git diff --stat origin/main...<branch>` (what it adds). The feature keys = the folders of `backend/features/` that the
   branch adds.

## 2. ONE round of questions -> STOP
Simple Vietnamese, numbered, defaults marked `(đề xuất)`:
1. **Nhánh cần cập nhật:** `<branch>` (đề xuất) - liệt kê các nhánh khác nếu có.
2. **Đẩy lại lên GitHub sau khi xong?** Việc cập nhật (rebase) viết lại lịch sử của nhánh nên phải đẩy đè (an toàn: chỉ đè
   khi trên GitHub không có ai vừa đẩy thêm). (a) Đẩy đè nhánh cũ (đề xuất nếu nhánh của chính bạn); (b) đẩy sang nhánh
   mới `<branch>-rebased`; (c) chỉ làm trên máy, không đẩy.
3. Nếu cần mã truy cập GitHub: như `docs/prompt/04-push-to-github.md` mục 3 câu 5 (hoặc "tôi tự push").
**STOP** and wait. After the answer, never ask again until the final report.

## 3. Rebase
1. `echo unlocked > .gate-unlock`.
2. Keep a safety point: `git branch backup/<branch>-<yyyymmdd> <branch>` (local only, never pushed).
3. `git checkout <branch>` (or `git checkout -b <branch> origin/<branch>`), then `git rebase origin/main`.
   Merge commits of the branch that only brought `main` in are dropped by the rebase: expected.
4. Conflicts (`git status` shows them), file by file:
   - Framework paths (listed in the header): take `main`: `git checkout --ours -- <file>` (during a rebase "ours" = the
     commit being rebased onto = `main`). Never keep the branch's edit of framework code; if the feature needed it, the
     adaptation happens in the feature (step 4) - or, if truly generic, it is written in the final report as a request
     to the framework owner.
   - Feature paths of the branch (`backend/features/<key>/`, `frontend/features/<key>/`, `docs/business/<key>.md`,
     `docs/plans/<key>-*.md`, `docs/business/_sources/*`): take the branch: `git checkout --theirs -- <file>`.
   - Both sides edited a shared document (e.g. `docs/business/README.md`): merge by hand, keep both contents.
   - `git add <file>` then `git rebase --continue`. Never `git rebase --skip` a commit of the branch.
5. Baseline: run `.venv/Scripts/python.exe scripts/check.py` right after the rebase and keep its output: it tells
   which failures come from the new framework.

## 4. Adapt the features to the framework of `main`
Compare what the framework offers now with what the feature built itself, and move to the framework version. A worked
example: branch `origin/vibe/tinh-gia-soi-1210`, commit "refactor(yarn_costing): PostgreSQL storage + collapsible menu"
(`git show --stat <commit>`). Typical changes (check each one for every feature of the branch):
0. **Developer prefix.** `backend/features/<key>/__init__.py` declares `DEVELOPER = "<github username of the branch
   author>"` (from `git log --format=%an` / the branch name / the fork owner; ask in the question round if unclear).
1. **Storage = database.** Every repository inherits `SqlRepository[Entity]` (table `<developer>__<key>__<name>`), never
   `JsonFileRepository`. If the feature already has user data in `data/<key>/*.json` (it ran before), keep it: add a
   small base class in the feature's `repositories/` that imports the old file once when the table is empty:
   ```python
   class <Pascal>SqlRepository(SqlRepository[TEntity]):
       legacy_file: ClassVar[str] = ""  # old file name, e.g. "orders.json"

       def _load(self) -> dict[str, TEntity]:
           items = super()._load()
           if items:
               return items
           path = get_settings().data_dir / "<key>" / self.legacy_file
           if not self.legacy_file or not path.exists():
               return {}
           rows = [self.entity_type.model_validate(r) for r in json.loads(path.read_text(encoding="utf-8") or "[]")]
           self.save_many(rows)
           path.replace(path.with_name(path.name + ".imported"))  # never imported twice, never deleted
           return {r.id: r for r in rows}
   ```
   (full version with old-format conversion, seeds and a clear error for a broken file:
   `git show origin/vibe/tinh-gia-soi-1210:backend/features/yarn_costing/repositories/yarn_sql_repository.py`).
   Seed data that was written "on first read" moves to `_seed()`. Feature tests: `XRepository()` instead
   of `XRepository(file_path=...)` (conftest gives each test an empty database). Never delete `data/`.
2. **Menu.** Remove in-page menus / "↳" workarounds / "[Nhóm] " prefixes in page titles; set `menu_group = "..."` on
   each page class instead and order `FEATURE.pages` by group (rules 04 #9).
3. **Login / permissions.** Pages and services write no permission checks: the framework hides pages and refuses
   features the user may not open. Use `self.current_user` for "who did it". If the feature has its OWN access system
   that is a documented business rule (BR-xx: e.g. access codes, per-factory scope, audit names), do NOT delete it:
   keep it working and add to section 10 of its business document an open question "nối tài khoản đăng nhập với ...",
   to be decided with Prompt 1 / Prompt 5.
4. **Speed.** Put `@cached_query` on every read-only controller method (lists, details, dashboards, exports) and remove
   any `show_log_panel` / log panel code (the framework has none any more).
5. **Any other framework API change** shown by the baseline failures (renamed helper, new base-class argument...): fix
   the feature side, following `docs/rules/`.
6. The sample feature `sample_product_import` hides itself once the branch has a real feature: never delete or edit it.
7. Update section 11 "Implementation map" (and the plan, if it names files) of each touched feature document.
Self-repair loop of `docs/rules/10-self-repair.md` until both commands pass:
`.venv/Scripts/python.exe scripts/check.py` -> `ALL CHECKS PASSED` and `.venv/Scripts/python.exe scripts/doctor.py` ->
`APP IS HEALTHY`. Never weaken tests, never edit framework code to make the feature pass.

## 5. Commit and push
1. `git status --short`: nothing from `.env`, `data/`, `logs/`, `.gate-unlock`, secrets may be staged.
2. One commit: `refactor(<key>): adapt to the current framework (<what changed>)` with a short body.
3. Push according to answer 2: (a) `git fetch origin` then `git push --force-with-lease origin <branch>` - if it is
   refused, someone pushed meanwhile: stop, do NOT force, tell the user; (b) `git push -u origin <branch>-rebased`;
   (c) nothing. Never push to `main`. Token rules of Prompt 4 apply.
4. `rm .gate-unlock`.

## 6. Final report (Vietnamese, no jargon)
- Nhánh nào đã được cập nhật lên phiên bản khung sườn mới nhất; đã đẩy lên đâu (hoặc lệnh để tự đẩy).
- Những gì đã đổi trong từng chức năng (lưu vào cơ sở dữ liệu, menu gấp / mở, đăng nhập...), dữ liệu cũ được giữ thế nào.
- Kết quả hai lệnh kiểm tra (copy dòng cuối).
- Nhắc người dùng: nếu chưa có `.env` thì `Copy-Item .env.example .env`, điền 5 dòng `POSTGRES_*` (giá trị xin người phụ
  trách khung sườn), rồi chạy lại `run.ps1` (thư viện mới được cài tự động).
- Câu hỏi mở còn lại (ví dụ nối hệ thống người thao tác riêng của chức năng với đăng nhập) và bước tiếp theo
  (Prompt 5 để cấp quyền cho người dùng).
- Bản sao an toàn: nhánh `backup/<branch>-<ngày>` trên máy (xoá được khi mọi thứ ổn).
