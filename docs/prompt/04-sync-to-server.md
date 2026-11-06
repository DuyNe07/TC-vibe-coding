# TASK: Save my apps on GitHub and bring them up to date - run on my machine or on the company server (Prompt 4)

> GATE KEY: `TC-UNLOCK-IMPLEMENT`. This prompt allows writing code ONLY inside the user's own features
> (`backend/features/<key>/`, `frontend/features/<key>/`, their line in `backend/app_registry.py`, their
> `docs/plans/<key>-*.md`, the `Run mode` row and sections 10-11 of their `docs/business/<key>.md`). Framework files
> always come unchanged from the base branch (`main` for mode 1, `dev` for mode 2). `SUPREME-RULES.md` applies.

You help a NON-programmer keep their apps safe on GitHub and up to date with the newest common core. Every app runs
in ONE of two ways - the user chooses, per app:

| | Mode 1 - **Chỉ chạy trên máy tôi** (local) | Mode 2 - **Chạy trên server công ty** |
|---|---|---|
| For whom | only the user, on their own computer (tắt máy = tắt app) | runs all day, many colleagues open it by link |
| Branch on GitHub | ONE branch per person: `<name>_local`, built on `main`, holding ALL their local apps | one branch per app `vibe/<prefix>-<key>-<ddmm>`, built on `dev` |
| What you do | merge each local app into `<name>_local`, take the newest `main`, push `<name>_local` | rebase each app branch on the newest `dev`, push it, give the Pull Request link |
| Pull Request | **none**, never into `dev` / `main` | the user opens the link and clicks *Create pull request* (never you) |

`<name>` = the user's GitHub username in lower case, only `a-z 0-9` (from `gh config get -h github.com user`, else
`git config user.name`), e.g. `xuan2894_local`. Below `<L>` means that branch. `dev` = everything that runs on the
server; `<name>_local` = one person's apps that never go to the server.

You ask ONE round of questions, then work automatically until the final report.

## 1. Hard rules
1. **Never lose the user's work.** Commit it first, and keep a local safety branch `backup/<branch>-<yyyymmdd>` for
   EVERY branch you rebase or merge (also `<L>`). Forbidden: `git reset --hard`, `git checkout -- .`, `git clean`,
   `git stash drop`, `git rebase --skip` of a user commit, deleting branches.
2. **No fork, no new clone, no copied folder - ever.** Never fork the repository (no `gh repo fork`, no *Fork* button),
   never suggest it, not even as a fallback. Everything happens on branches of THIS repository. A push refused for
   permission (`403`, `Permission denied`, `not allowed`) has ONE answer: "Nhờ người phụ trách khung sườn thêm tài
   khoản GitHub của bạn vào repo, rồi chạy lại prompt 4."
3. **Never create a Pull Request yourself.** No `gh pr create` (also not with `--web`), no `gh api` / `curl` to
   `/pulls`, never open the Pull Request page in a browser or a browser tool, never click *Create pull request*. Your
   output is the LINK as text (Step S3): the user opens it and clicks the button. A Pull Request that already exists
   for the branch updates itself when you push: just say so.
4. **Never push to `main` / `dev` / `master`**, never merge `<L>` into `dev` or `main`, never push to another person's
   `..._local` or `vibe/...` branch. Never `--force`; the only allowed rewrite is `--force-with-lease` on the user's
   OWN `vibe/...` branches after their rebase in mode 2. `<L>` is never rewritten (merge into it, never rebase it).
5. **Never commit secrets or runtime data.** Before every commit, `git status --short` must show nothing matching
   `.env` (`.env.example` is fine), `data/`, `logs/`, `.gate-unlock`, `*.pem`, `*.key`, `*token*`, `*secret*`,
   `.venv/`. If one appears: unstage it and tell the user.
6. **A token** the user gives you is used ONLY inside the `git fetch` / `git push` command line. Never write it to a
   file, never to `.git/config`, never repeat it in your messages.
7. **Framework files are never edited here** (the list in `SUPREME-RULES.md` section 2). If a feature needs something
   the framework does not offer, build it inside the feature or write it in the report as a request to the framework
   owner. Never explain or hint how the framework lock works.
8. **The database is shared by every machine** (local and server). Never delete or rewrite stored rows to make
   something pass; stored data of the user's features must stay readable (Step R, item 6).
9. A failing command: show the real error in simple Vietnamese and the ONE thing the user must do (wrong token, no
   permission, no network). Never retry a failed push more than twice. One branch failing never stops the others.
10. **Outside the team** (the user says "tôi làm riêng, không theo nhóm"): mode 2 with `main` in place of `dev`.

## 2. Step 1 - Look first (read-only, no questions yet)
```
git rev-parse --is-inside-work-tree
git remote -v
git branch --show-current
git config user.name
git config user.email
gh config get -h github.com user
git status --short
git fetch origin --prune
git log --oneline -5 origin/dev
git log --oneline -5 origin/main
git branch --list "vibe/*" "*_local"
git branch -r --list "origin/<name>_local"
```
Work out `<name>` and `<L>` (both commands empty: ask in Step 2). `<owner>/<repo>` comes from `git remote get-url origin`.
The app branches = every local `vibe/*` branch, plus the current branch if it is not `main`, `dev`, `<L>` or
`backup/*`. For each one:
- its OWN commits: `git log --oneline --no-merges <branch> --not origin/dev origin/main <L>` (leave out `<L>` when it
  does not exist yet). None = already in `dev` or in `<L>`: nothing to send, say so and skip it.
- its apps: `git log --no-merges --name-only --format= <branch> --not origin/dev origin/main -- backend/features frontend/features`
  (the folder names = feature keys), and each app's `docs/business/<key>.md` read from that branch
  (`git show <branch>:docs/business/<key>.md`): the header row `Run mode` gives the proposal (`Local` -> 1,
  `Server` or no row -> 2).
- `<L>` with uncommitted changes (a repair made there): those are saved on `<L>` itself in Step 3.
Read `CLAUDE.md`, `SUPREME-RULES.md`, `docs/README.md`, every file of `docs/rules/`, and those business documents.

## 3. Step 2 - ONE round of questions -> STOP
Simple Vietnamese, numbered, the proposal marked `(đề xuất)`; ask only what Step 1 did not answer:
1. **Mỗi ứng dụng chạy ở đâu?** Explain the two ways in two lines each, then a numbered list `ứng dụng -> nhánh ->
   số thay đổi chưa gửi -> đề xuất`:
   - **(1) Chỉ chạy trên máy bạn**: chỉ bạn dùng, mở app trên máy bạn; code được lưu an toàn trên GitHub trong nhánh
     riêng của bạn `<L>` (gom mọi ứng dụng chạy trên máy của bạn). Không cần Pull Request, không cần ai duyệt.
   - **(2) Chạy trên server công ty**: chạy liên tục, nhiều người mở được qua đường link; bạn phải bấm link tạo
     Pull Request, người phụ trách duyệt rồi mới có trên server.
   "Trả lời `1` hoặc `2` cho tất cả, hoặc theo số từng ứng dụng (ví dụ `1:1, 2:2`)."
2. **Mô tả ngắn công việc** (1 câu tiếng Việt) - only for a branch that has unsaved changes, e.g. "Thêm màn hình báo
   cáo tồn kho".
3. **Tên và email ghi vào lịch sử, tên GitHub** - only if Step 1 found them empty.
4. **Đẩy lên GitHub**: (a) dùng đăng nhập GitHub sẵn có trên máy (đề xuất nếu `git push --dry-run origin HEAD` không
   đòi đăng nhập); (b) dán mã truy cập (Personal Access Token): mở `https://github.com/settings/tokens` ->
   *Generate new token* -> *Fine-grained*, chọn đúng repo, *Contents: Read and write*, hạn 7 ngày -> copy dãy
   `github_pat_...`; (c) "tôi tự push": you prepare everything and give the push commands to run.
   Add one line: "Mã truy cập sẽ nằm trong nội dung chat này; dùng token hạn 7 ngày và xoá trên GitHub khi xong."
**STOP**. After the answer never ask again until the final report.

## 4. Step 3 - Save the work
```
git config user.name "<Tên>"          # only if it was empty
git config user.email "<email>"       # only if it was empty
```
Unsaved changes on the current branch: on `main` / `dev` first `git checkout -b vibe/<prefix>-<key>-<ddmm>`
(the changes move with it); on `<L>` or an app branch: commit right there.
```
git add -A
git status --short                    # check rule 5 before committing
git commit -m "<loại>(<key>): <mô tả ngắn>"
```
"nothing to commit" is fine. `<loại>` = `feat` (new), `fix` (repair), `refactor` (no behaviour change).
Then `echo <all feature keys of all branches> > .gate-unlock` and, for EVERY app branch and `<L>` (if it exists):
`git branch backup/<branch>-<yyyymmdd> <branch>`.
Write the chosen mode into each app's business document header (`| Run mode (Chạy ở đâu) | Local |` or `Server`),
committed with that app in the steps below.

## 5. Mode 1 - local apps into `<L>` (skip when no app chose 1)
**Step L1 - Prepare `<L>` and take the newest `main`.**
```
git checkout <L>                      # exists on this machine; then, if origin/<L> exists:
git merge --ff-only origin/<L>        #   refused (both sides changed): git merge --no-edit origin/<L>
git checkout -b <L> origin/<L>        # only on GitHub
git checkout -b <L> origin/main       # nowhere yet: create it from main
git merge --no-edit origin/main       # the newest common core (merge, never rebase <L>)
```
Merge conflicts (`UU`) - during a MERGE `--ours` = `<L>`, `--theirs` = `origin/main`:
- **Framework files** (`SUPREME-RULES.md` section 2 list, plus `SUPREME-RULES.md`): take `main`:
  `git checkout --theirs -- <file>`.
- **The user's feature files** (`backend/features/<key>/`, `frontend/features/<key>/`, `docs/business/<key>.md`,
  `docs/plans/<key>-*.md`, `docs/business/_sources/*`): keep `<L>`'s: `git checkout --ours -- <file>`.
- **`backend/app_registry.py`**: keep EVERY line of both sides (one line per app), remove the markers.
- **A shared document both sides edited** (e.g. `docs/business/README.md`): merge by hand, keep both contents.
- `git add <file>`, then `git commit --no-edit`. Never `git merge --abort` without telling the user.

**Step L2 - Move each local app branch onto `<L>`, then merge it in** (branch by branch):
```
git rev-list --count origin/dev..<branch>
git rev-list --count <L>..<branch>
```
The SMALLER count tells where the branch was born: `<B>` = `origin/dev` or `<L>` (equal: `<L>`).
```
git rebase --onto <L> <B> <branch>    # replays ONLY this app's own commits onto <L>
```
(A plain `git rebase <L>` would copy everybody's `dev` work into `<L>` - never do that.) Conflicts: the rules of
Step S1. Then:
```
git checkout <L>
git merge --no-ff --no-edit <branch>  # the app now lives in <L>
```
An app the user chose 1 for that is ALREADY in `dev` (its own commits are empty): copy it into `<L>` -
`git checkout origin/dev -- backend/features/<key> frontend/features/<key> docs/business/<key>.md`, add its registry
line by hand, `git commit -m "feat(<key>): chuyển sang chạy trên máy"`; tell the user it stays on the server until the
framework owner removes it there.

**Step L3 - Refactor and verify on `<L>`**: Step R below for every app of the user in `<L>`, then
`git add -A`, `git status --short` (rule 5), `git commit -m "refactor(<keys>): adapt to the current framework (<what changed>)"`.

**Step L4 - Push `<L>`** (never force):
```
git push -u origin <L>                                                          # 4a
git push https://<github-user>:<token>@github.com/<owner>/<repo>.git <L>       # 4b
```
Refused as "non-fast-forward" (another machine of the same person pushed): `git pull --no-rebase --no-edit origin <L>`,
re-run Step R's two checks, push again. 4c: collect `git push -u origin <L>` for the report. No Pull Request link.

## 6. Mode 2 - server apps (skip when no app chose 2; Steps S1-S3 run branch by branch)
**Step S1 - Rebase the branch on the newest `dev`.** Where it was born (`<B>`): the smaller of
`git rev-list --count origin/dev..<branch>` and `git rev-list --count <L>..<branch>` (no `<L>`: `origin/dev`).
```
git checkout <branch>
git rebase origin/dev                 # born from dev
git rebase --onto origin/dev <L> <branch>   # born from <L>: only its own commits go to dev
```
On each conflict (`git status --short` shows `UU`), file by file - during a REBASE `--ours` = the base (`dev`),
`--theirs` = the user's commit:
- **Framework files**: take the base: `git checkout --ours -- <file>`.
- **The user's feature files**: take the user's: `git checkout --theirs -- <file>`.
- **`backend/app_registry.py`**: keep EVERY line of both sides, remove the markers.
- **A shared document both sides edited**: merge by hand, keep both contents.
- `git add <file>`, then `git rebase --continue`. Never `--skip` a user commit; never `--abort` without telling the user.
An app that lives ONLY in `<L>` and now goes to the server: `git checkout -b vibe/<prefix>-<key>-<ddmm> origin/dev`,
`git checkout <L> -- backend/features/<key> frontend/features/<key> docs/business/<key>.md`, its registry line by
hand, `git commit -m "feat(<key>): đưa lên server công ty"` (the app also stays in `<L>`).

**Step S2 - Refactor and verify**: Step R below, then `git add -A`, `git status --short` (rule 5),
`git commit -m "refactor(<key>): adapt to the current framework (<what changed>)"`.

**Step S3 - Push the branch, prepare its link**:
```
git push --force-with-lease -u origin <branch>                                              # 4a
git push --force-with-lease https://<github-user>:<token>@github.com/<owner>/<repo>.git <branch>   # 4b
```
- `--force-with-lease` is needed because the rebase rewrote the branch; it refuses if somebody else pushed to the same
  branch meanwhile: then do not force, note it for the report, continue with the next branch.
- 4c "tôi tự push": collect `git push --force-with-lease -u origin <branch>` (Windows asks for the GitHub login:
  username + token as password).
- The Pull Request link (rule 3: text only, never opened, never created by you), base `dev`, never the default branch:
  `https://github.com/<owner>/<repo>/compare/dev...<branch>?expand=1`

## 7. Step R - Refactor the features to the newest framework (used by L3 and S2)
Check EVERY item for every feature of the branch and move it to the framework's way (compare with the reference feature
`sample_product_import` and `docs/rules/`). First the baseline: `.venv/Scripts/python.exe scripts/check.py` - its
failures show what the newest framework expects. (Missing packages: `.venv/Scripts/python.exe -m pip install -r requirements.txt`.)
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
Then update section 11 and the `Run mode` row of each touched business document. Self-repair loop of
`docs/rules/10-self-repair.md` until `.venv/Scripts/python.exe scripts/check.py` -> `ALL CHECKS PASSED` and
`.venv/Scripts/python.exe scripts/doctor.py` -> `APP IS HEALTHY`. If after 5 attempts something still fails: push
anyway and say exactly what is red.

At the very end: `git checkout <L>` when mode 1 was used (all the user's local apps run from it), otherwise back to the
branch the user was on; then `rm .gate-unlock` (always, even when something failed).

## 8. Step 7 - Report (Vietnamese, short, no jargon)
1. One line per app: ứng dụng -> chạy ở đâu (máy bạn / server công ty) -> nhánh -> đã lấy bản chung mới nhất
   (`main` cho máy bạn, `dev` cho server); xung đột ở file nào, giữ bên nào; kết quả kiểm tra (dòng cuối của
   `scripts/check.py` và `scripts/doctor.py`, nếu còn đỏ: lỗi gì).
2. Những gì đã sửa trong từng chức năng cho hợp khung sườn mới (một dòng mỗi mục của Step R đã đổi); dữ liệu cũ được giữ.
3. **Mode 1:** "Code các ứng dụng chạy trên máy của bạn đã được lưu trên GitHub ở nhánh riêng `<L>`:
   `https://github.com/<owner>/<repo>/tree/<L>`. Không cần Pull Request. Để mở app: ở nhánh `<L>` (máy đang ở nhánh
   này), chạy `powershell -ExecutionPolicy Bypass -File .\run.ps1`. Ứng dụng mới chọn "chạy trên máy" sẽ được tạo từ
   nhánh này và gộp lại vào đây. Bản chung (`main`) chỉ đổi khi người phụ trách khung sườn phát hành bản mới; chạy lại
   prompt 4 để nhận."
4. **Mode 2 - write this in bold, it is the most important line of the report:**
   "**Để chức năng chạy trên server công ty, bạn PHẢI tự tạo Pull Request cho từng nhánh: bấm link bên dưới -> trang
   GitHub mở ra -> bấm nút *Create pull request*. Link chỉ mở trang tạo, Pull Request chưa có cho đến khi bạn bấm nút.
   Người phụ trách sẽ duyệt và gộp vào `dev`, sau đó chức năng mới có trên server.**"
   Then one link per branch: `https://github.com/<owner>/<repo>/compare/dev...<branch>?expand=1`
   (a branch that already has a Pull Request: "Pull Request cũ đã tự cập nhật, không cần tạo lại").
5. 4c "tôi tự push": the push commands, one per line, run in PowerShell in the project folder.
6. Bản sao an toàn trên máy: các nhánh `backup/<branch>-<ngày>` (xoá được khi mọi thứ ổn); có thể xoá token trên GitHub.
