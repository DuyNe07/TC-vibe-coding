# TASK: Update ALL my feature branches to the newest `dev`, adapt my features, push, give Pull Request links (Prompt 4)

> GATE KEY: `TC-UNLOCK-IMPLEMENT`. This prompt allows writing code ONLY inside the features of the user's branches
> (`backend/features/<key>/`, `frontend/features/<key>/`, their line in `backend/app_registry.py`, their
> `docs/plans/<key>-*.md`, sections 10-11 of their `docs/business/<key>.md`). Framework files always come from `dev`
> unchanged. `SUPREME-RULES.md` applies.

You help a NON-programmer bring their work up to date and, if they want it on the company server, send it there.
Each feature lives on its own branch `vibe/...` started from `dev` (`docs/rules/05-feature-workflow.md` rule 2): one
person with 10 apps has 10 branches. In ONE run, for EVERY one of those branches you: save the work, take the newest
`dev` (the team branch = latest framework + everybody's merged apps), replay the branch on top of it (rebase), refactor
its features to the newest framework, prove the app works, push it, and give its Pull Request link. You ask ONE round of
questions, then work automatically until the final report.
Never suggest forking the repository or cloning it again: everything happens on branches of THIS repository.

## 1. Hard rules
1. **Never lose the user's work.** Commit it first, and keep a local safety branch `backup/<branch>-<yyyymmdd>` for
   EVERY branch before rebasing it. Forbidden: `git reset --hard`, `git checkout -- .`, `git clean`, `git stash drop`,
   `git rebase --skip` of a user commit, deleting branches.
2. **Never push to `main` / `dev` / `master`.** Never `--force`; the only allowed rewrite is `--force-with-lease` on
   the user's OWN branches after the rebase (Step 6). `dev` changes only through a Pull Request.
3. **Never commit secrets or runtime data.** Before every commit, `git status --short` must show nothing matching
   `.env` (`.env.example` is fine), `data/`, `logs/`, `.gate-unlock`, `*.pem`, `*.key`, `*token*`, `*secret*`,
   `.venv/`. If one appears: unstage it and tell the user.
4. **A token** the user gives you is used ONLY inside the `git fetch` / `git push` command line. Never write it to a
   file, never to `.git/config`, never repeat it in your messages.
5. **Framework files are never edited here** (the list in `SUPREME-RULES.md` section 2). If a feature needs something
   the framework does not offer, build it inside the feature or write it in the report as a request to the framework
   owner. Never explain or hint how the framework lock works.
6. **The database is shared by every machine.** Never delete or rewrite stored rows to make something pass; stored data
   of the user's features must stay readable (Step 5, item 6).
7. A failing command: show the real error in simple Vietnamese and the ONE thing the user must do (wrong token, no
   permission, no network). Never retry a failed push more than twice. One branch failing never stops the others.
8. **Outside the team** (the user says "tôi làm riêng, không theo nhóm"): the same steps with `main` in place of `dev`.

## 2. Step 1 - Look first (read-only, no questions yet)
```
git rev-parse --is-inside-work-tree
git remote -v
git branch --show-current
git config user.name
git config user.email
git status --short
git fetch origin --prune
git log --oneline -10 origin/dev
git branch --list "vibe/*"
```
The branches to update = every local `vibe/*` branch, plus the current branch if it is not `main`, `dev` or
`backup/*`. For each one: `git log --oneline origin/dev..<branch>` (its own commits; none = already merged, nothing to
send - say so and skip it) and its features: `git diff --stat origin/dev...<branch> -- backend/features frontend/features`.
Read `CLAUDE.md`, `SUPREME-RULES.md`, `docs/README.md`, every file of `docs/rules/`, and each of those features'
`docs/business/<key>.md`.
Uncommitted changes on `main` / `dev`: they belong to a feature - its branch is created in Step 3.

## 3. Step 2 - ONE round of questions -> STOP
Simple Vietnamese, numbered, the proposal marked `(đề xuất)`; ask only what Step 1 did not answer:
1. **Các nhánh sẽ cập nhật:** show the list (nhánh -> chức năng, số thay đổi chưa gửi); proposal: tất cả (đề xuất).
2. **Mô tả ngắn công việc** (1 câu tiếng Việt) - only for a branch that has unsaved changes, e.g. "Thêm màn hình báo
   cáo tồn kho".
3. **Tên và email ghi vào lịch sử** - only if `git config` is empty.
4. **Bạn muốn chức năng chạy ở đâu?**
   (a) **trên server công ty** (đề xuất) - gửi các nhánh lên GitHub, rồi bạn tạo Pull Request theo link;
   (b) chỉ trên máy của tôi - cập nhật và kiểm tra trên máy, không gửi gì lên GitHub, không cần Pull Request.
5. **Đẩy lên GitHub** (only for 4a): (a) dùng đăng nhập GitHub sẵn có trên máy (đề xuất nếu `git push --dry-run` không
   đòi đăng nhập); (b) dán mã truy cập (Personal Access Token): mở `https://github.com/settings/tokens` ->
   *Generate new token* -> *Fine-grained*, chọn đúng repo, *Contents: Read and write*, hạn 7 ngày -> copy dãy
   `github_pat_...`; (c) "tôi tự push": you prepare everything and give one command per branch to run.
   Add one line: "Mã truy cập sẽ nằm trong nội dung chat này; dùng token hạn 7 ngày và xoá trên GitHub khi xong."
**STOP**. After the answer never ask again until the final report.

## 4. Step 3 - Save the work
```
git config user.name "<Tên>"          # only if it was empty
git config user.email "<email>"       # only if it was empty
```
Unsaved changes on the current branch: on `main` / `dev` first `git checkout -b vibe/<prefix>-<key>-<ddmm>`
(the changes move with it); then
```
git add -A
git status --short                    # check rule 3 before committing
git commit -m "<loại>(<key>): <mô tả ngắn>"
```
"nothing to commit" is fine. `<loại>` = `feat` (new), `fix` (repair), `refactor` (no behaviour change).
Then `echo <all feature keys of all branches> > .gate-unlock` and, for EVERY branch to update:
`git branch backup/<branch>-<yyyymmdd> <branch>`.

## 5. Step 4 - Rebase each branch on the newest `dev` (Steps 4-6 run branch by branch)
```
git checkout <branch>
git rebase origin/dev
```
On each conflict (`git status --short` shows `UU`), file by file - during a rebase `--ours` = `dev`, `--theirs` =
the user's commit:
- **Framework files** (`SUPREME-RULES.md` section 2 list, plus `SUPREME-RULES.md`): take `dev`:
  `git checkout --ours -- <file>`.
- **The user's feature files** (`backend/features/<key>/`, `frontend/features/<key>/`, `docs/business/<key>.md`,
  `docs/plans/<key>-*.md`, `docs/business/_sources/*`): take the user's: `git checkout --theirs -- <file>`.
- **`backend/app_registry.py`**: keep EVERY line of both sides (one line per app), remove the markers.
- **A shared document both sides edited** (e.g. `docs/business/README.md`): merge by hand, keep both contents.
- `git add <file>`, then `git rebase --continue`. Never `--skip` a user commit; never `--abort` without telling the user.
Then the baseline: `.venv/Scripts/python.exe scripts/check.py` - keep the output; its failures show what the newest
framework now expects from the features. (Missing packages: `.venv/Scripts/python.exe -m pip install -r requirements.txt`.)

## 6. Step 5 - Refactor the branch's features to the newest framework
Check EVERY item for every feature of the branch and move it to the framework's way (compare with the reference feature
`sample_product_import` and `docs/rules/`):
1. **App registry.** One line `("<prefix>", "<key>")` in `backend/app_registry.py` (prefix = the builder's short name,
   lower-case letters and digits, e.g. `tenban`); URLs become `/<prefix>-<app>`.
2. **Developer prefix.** `backend/features/<key>/__init__.py` declares `DEVELOPER = "<github username>"` (tables
   `<developer>__<key>__*`). Never change it once data exists.
3. **Storage.** Repositories inherit `SqlRepository[Entity]`; lookups by value use `repository.find_by(field=...)`; no
   `sqlalchemy`, no raw SQL, no repository internals (`_save`, `_write`, `_purge`, `_stored`) in the feature. Old
   JSON files in `data/<key>/` are imported once by a small repository base class (keep the file, renamed
   `.imported`), never deleted.
4. **Soft delete.** `repository.delete()` / `clear()` only set the delete flag; reads skip deleted rows;
   `restore()` / `list_deleted()` exist. Re-check every delete in the feature against its business rules.
5. **Big data.** Tables only through `data_table` / `editable_table`, charts only through `bar_chart` / `line_chart` /
   `pie_chart`, Excel only through `ExcelReader` (they cap rows and points). Replace direct `st.dataframe`,
   `st.plotly_chart`, `px.*`, `pd.read_excel` in the feature.
6. **Stored data stays readable** by every app version on the shared database: new model fields get defaults; a
   renamed / removed field or a changed format gets a migration revision
   (`.venv/Scripts/python.exe scripts/migrate.py new <key> "..."`, `backend.core.migration_ops`).
7. **Menu and login.** Pages grouped with `menu_group`; no in-app login, access code or user list (rights are given on
   `/admin`); actors with different rights inside the app = manifest `roles` + a BR reading
   `self.current_user.roles_in(key)`.
8. **Speed.** `@cached_query` on every read-only controller method; nothing heavy on page render.
9. **Anything else** the baseline shows (renamed helper, new base-class argument): fix the feature side.
10. The sample feature `sample_product_import` hides itself: never delete or edit it.
Then update section 11 of each touched business document. Self-repair loop of `docs/rules/10-self-repair.md` until:
`.venv/Scripts/python.exe scripts/check.py` -> `ALL CHECKS PASSED` and `.venv/Scripts/python.exe scripts/doctor.py` ->
`APP IS HEALTHY`. If after 5 attempts something still fails: push anyway (Step 6) and say exactly what is red.

## 7. Step 6 - Commit and push the branch, then the next branch
```
git add -A
git status --short                    # rule 3 again
git commit -m "refactor(<key>): adapt to the current framework (<what changed>)"
git push --force-with-lease -u origin <branch>      # 5a: GitHub login already on the machine
git push --force-with-lease https://<github-user>:<token>@github.com/<owner>/<repo>.git <branch>   # 5b: token
```
- Answer 4b (chỉ trên máy): no push - commit only, go to the next branch.
- `--force-with-lease` is needed because the rebase rewrote the branch; it refuses if somebody else pushed to the same
  branch meanwhile: then do not force, note it for the report, continue with the next branch.
- 5c "tôi tự push": collect one command per branch: `git push --force-with-lease -u origin <branch>` (Windows asks for
  the GitHub login: username + token as password).
Then back to Step 4 with the next branch. At the very end: `git checkout <the branch the user was on>` and
`rm .gate-unlock` (always, even when something failed).

## 8. Step 7 - Report (Vietnamese, short, no jargon)
1. One line per branch: nhánh -> chức năng -> đã lấy bản chung mới nhất của nhóm (`dev`) và đặt công việc lên trên;
   xung đột ở file nào, giữ bên nào; kết quả kiểm tra (dòng cuối của `scripts/check.py` và `scripts/doctor.py`, nếu còn
   đỏ: lỗi gì).
2. Những gì đã sửa trong từng chức năng cho hợp khung sườn mới (một dòng mỗi mục của Step 5 đã đổi); dữ liệu cũ được giữ.
3. **Answer 4a - write this in bold, it is the most important line of the report:**
   "**Để chức năng chạy trên server công ty, bạn PHẢI tạo Pull Request cho từng nhánh: bấm link bên dưới -> bấm nút
   *Create pull request*. Người phụ trách sẽ duyệt và gộp vào `dev`, sau đó chức năng mới có trên server. Chưa tạo Pull
   Request = chức năng chỉ nằm trên GitHub, server chưa có.**"
   Then one link per branch (base `dev`, never the default branch):
   `https://github.com/<owner>/<repo>/compare/dev...<branch>?expand=1`
   Answer 4b: "Bạn chỉ chạy trên máy mình nên không cần tạo Pull Request; khi nào muốn đưa lên server công ty, chạy lại
   prompt 4 và chọn (a)."
4. Bản sao an toàn trên máy: các nhánh `backup/<branch>-<ngày>` (xoá được khi mọi thứ ổn); có thể xoá token trên GitHub.
