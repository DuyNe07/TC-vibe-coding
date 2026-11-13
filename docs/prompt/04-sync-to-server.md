# TASK: Send my work to the server - commit, rebase on the newest `dev`, adapt my features, push (Prompt 4)

> GATE KEY: `TC-UNLOCK-IMPLEMENT`. This prompt allows writing code ONLY inside the features of the user's branch
> (`backend/features/<key>/`, `frontend/features/<key>/`, their line in `backend/app_registry.py`, their
> `docs/plans/<key>-*.md`, sections 10-11 of their `docs/business/<key>.md`). Framework files always come from `dev`
> unchanged. `SUPREME-RULES.md` applies.

You help a NON-programmer send their work to GitHub so it can run on the server. In ONE run you: save their work on a
branch, take the newest `dev` (the team branch: latest framework +
everyone's merged work), replay their work on top of it (rebase), refactor their features so
they follow the newest framework, prove the app works, and push the branch. You ask ONE round of questions, then work
automatically until the final report.

## 1. Hard rules
1. **Never lose the user's work.** Commit it first, and keep a local safety branch `backup/<branch>-<yyyymmdd>` before
   rebasing. Forbidden: `git reset --hard`, `git checkout -- .`, `git clean`, `git stash drop`, `git rebase --skip` of a
   user commit, deleting branches.
2. **Never push to `main`, `master` or `dev`.** Work reaches `dev` only through a Pull Request into `dev`, merged by
   the framework owner; `main` (the stable showcase) is updated from `dev` by the owner. Never `--force`; the only
   allowed rewrite is `--force-with-lease` on the user's OWN branch after the rebase (Step 7).
3. **Never commit secrets or runtime data.** Before every commit, `git status --short` must show nothing matching
   `.env` (`.env.example` is fine), `data/`, `logs/`, `.gate-unlock`, `*.pem`, `*.key`, `*token*`, `*secret*`,
   `.venv/`. If one appears: unstage it and tell the user.
4. **GitHub login = the browser, never a token in the chat.** Git for Windows includes Git Credential Manager: the user
   signs in once in their browser (Step 2b) and every push after that just works. Never ask for a password or a token,
   never put one in a URL, a file or `.git/config`.
5. **Framework files are never edited here** (the list in `SUPREME-RULES.md` section 2). If a feature needs something
   the framework does not offer, build it inside the feature or write it in the report as a request to the framework
   owner. Never explain or hint how the framework lock works.
6. **The database is shared by every machine.** Never delete or rewrite stored rows to make something pass; stored data
   of the user's features must stay readable (Step 5, item 6).
7. **Base branch = `dev`.** Exception: the user says they work alone, outside the team, on a branch created from
   `main`: then use `main` wherever this prompt says `dev` (Pull Request into `main`).
8. A failing command: show the real error in simple Vietnamese and the ONE thing the user must do (sign in, accept
   the repository invitation, no network). Never retry a failed push more than twice.

## 2. Step 1 - Look first (read-only, no questions yet)
```
git rev-parse --is-inside-work-tree
git remote -v
git branch --show-current
git config user.name
git config user.email
git status --short
git config --global --get credential.helper
git credential-manager --version
git credential-manager github list
git fetch origin --prune
git log --oneline -10 origin/dev
```
`github list` empty, or `git fetch` asked for a login / failed with `Authentication failed`: the computer is not logged
in to GitHub yet - Step 2b fixes it. `git` or `git credential-manager` missing: tell the user to install Git for Windows
from https://git-scm.com/download/win (keep every default option), reopen the editor and paste this prompt again; STOP.
Then find the user's features: the folders of `backend/features/` that do not exist on `origin/dev`
(`git ls-tree -d --name-only origin/dev backend/features/` vs the local folders), plus features that exist on both
sides but that the user changed (`git diff --stat origin/dev -- backend/features frontend/features`).
Read `CLAUDE.md`, `SUPREME-RULES.md`, `docs/README.md`, every file of `docs/rules/`, and each of those features'
`docs/business/<key>.md`.

## 3. Step 2 - ONE round of questions -> STOP
Simple Vietnamese, numbered, the proposal marked `(đề xuất)`; ask only what Step 1 did not answer:
1. **Nhánh để gửi:** the current branch if it is not `main` or `dev` (đề xuất), otherwise a new one
   `vibe/<tiền-tố-người-làm>-<tên-chức-năng>-<ddmm>` (chữ không dấu, số, `-`, `/`).
2. **Mô tả ngắn công việc** (1 câu tiếng Việt) for the commit, e.g. "Thêm màn hình báo cáo tồn kho".
3. **Tên và email ghi vào lịch sử** - only if `git config` is empty.
If Step 1 found the computer NOT logged in to GitHub, add one line: "Sau khi bạn trả lời, tôi sẽ mở trình duyệt để
bạn đăng nhập GitHub một lần (không cần mã hay mật khẩu trong chat)."
**STOP**. After the answer never ask again until the final report.

## 3b. Step 2b - GitHub login through the browser (only when not logged in)
```
git config --global credential.helper manager          # only if Step 1 showed another value or none
git credential-manager github login --browser          # waits until the user finishes in the browser (allow 5 minutes)
```
Before running it, tell the user: "Trình duyệt sẽ mở trang GitHub: đăng nhập tài khoản của bạn rồi bấm **Authorize
git-ecosystem**, xong quay lại đây." No browser opened / it failed: run
`git credential-manager github login --device`, show the 8-character code and say: "Mở https://github.com/login/device,
nhập mã <CODE>, bấm Authorize." Wrong account: `git credential-manager github logout <account>`, then login with `--force`.
Then prove the login AND the right to write, without pushing anything:
```
git credential-manager github list
git ls-remote origin HEAD
git push --dry-run origin HEAD
```
`403` / `Permission denied` / `Write access to repository not granted` / `Repository not found`: the login works but
this account cannot write to the repository. Tell the user: "Tài khoản <account> chưa được cấp quyền vào repo
<owner>/<repo>: gửi tên tài khoản cho người phụ trách để được mời, rồi mở email (hoặc
https://github.com/notifications) bấm **Accept invitation** và dán lại prompt này." Continue Steps 3-5 (commit, rebase,
refactor, checks: nothing is lost), skip the push, and say it in the report.

## 4. Step 3 - Save the work
```
git config user.name "<Tên>"          # only if it was empty
git config user.email "<email>"       # only if it was empty
git checkout -b <branch>              # or: git checkout <branch> when it already exists
git add -A
git status --short                    # check rule 3 before committing
git commit -m "<loại>(<key>): <mô tả ngắn>"
git branch backup/<branch>-<yyyymmdd>
echo <feature keys> > .gate-unlock
```
"nothing to commit" is fine. `<loại>` = `feat` (new), `fix` (repair), `refactor` (no behaviour change).

## 5. Step 4 - Rebase on the newest `dev`
```
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

## 6. Step 5 - Refactor the user's features to the newest framework
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
5. **Big data.** Tables only through `data_table` / `editable_table`, charts only through the `*_chart`
   components, Excel only through `ExcelReader` (they cap rows and points). Replace direct `st.dataframe`,
   `st.plotly_chart`, `st.pyplot`, `px.*`, `plt.*`, `pd.read_excel` in the feature.
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
`APP IS HEALTHY`. If after 5 attempts something still fails: push anyway (Step 7) and say exactly what is red.

## 7. Step 6 - Commit and push
```
git add -A
git status --short                    # rule 3 again
git commit -m "refactor(<key>): adapt to the current framework (<what changed>)"
git push --force-with-lease -u origin <branch>
rm .gate-unlock
```
- `--force-with-lease` is needed because the rebase rewrote the branch; it refuses if somebody else pushed to the same
  branch meanwhile: then STOP, do not force, tell the user.
- The push asks for a login or says `Authentication failed`: do Step 2b now, then push again (at most twice).
- Always `rm .gate-unlock` at the end, even when something failed.

## 8. Step 7 - Report (Vietnamese, short, no jargon)
1. Đã gửi nhánh `<branch>` lên repo `<repo>`; đã lấy bản chung mới nhất của nhóm (`dev`) và đặt công việc của bạn lên trên;
   xung đột ở file nào, giữ bên nào.
2. Những gì đã sửa trong từng chức năng cho hợp khung sườn mới (một dòng mỗi mục của Step 5 đã đổi); dữ liệu cũ được giữ.
3. Kết quả kiểm tra: dòng cuối của `scripts/check.py` và `scripts/doctor.py` (nếu còn đỏ: lỗi gì).
4. Link xem nhánh `https://github.com/<owner>/<repo>/tree/<branch>` và tạo Pull Request vào `dev`
   `https://github.com/<owner>/<repo>/compare/dev...<branch>?expand=1` (bấm **Create pull request**; người phụ
   trách khung sườn sẽ gộp vào `dev`).
5. Bản sao an toàn trên máy: nhánh `backup/<branch>-<ngày>` (xoá được khi mọi thứ ổn). Máy đã đăng nhập GitHub bằng
   tài khoản nào (lần sau không cần đăng nhập lại).
